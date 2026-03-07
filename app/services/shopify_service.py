import httpx
from typing import List, Optional
import re
from app.core.config import settings
from app.schemas.product import Product

from app.db.database import SessionLocal
from app.services.order_service import OrderService

class ShopifyClient:
    def __init__(self):
        self.base_url = f"https://{settings.SHOPIFY_STORE_URL}/admin/api/{settings.SHOPIFY_API_VERSION}"
        self.headers = {
            "X-Shopify-Access-Token": settings.SHOPIFY_ACCESS_TOKEN,
            "Content-Type": "application/json"
        }

    async def check_connection(self) -> dict:
        """
        Verifies connection to Shopify by fetching shop details.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/shop.json",
                    headers=self.headers
                )
                response.raise_for_status() 
                return response.json()
            except httpx.HTTPStatusError as e:
                raise Exception(f"Shopify API Error: {e.response.status_code} - {e.response.text}") from e
            except httpx.RequestError as e:
                raise Exception(f"Network Error during Shopify connection check: {str(e)}") from e
            except Exception as e:
                raise Exception(f"Unexpected error connecting to Shopify: {str(e)}") from e

    def normalize_turkish(self, text: str) -> str:
        """
        Turkish compliant normalization.
        Maps İ -> i and ı -> i to handle case-insensitive matching correctly.
        """
        if not text:
            return ""
        return text.replace('İ', 'i').replace('ı', 'i').lower()

    async def search_products(self, query: str = None, limit: int = 10) -> str:
        """
        Searches for products in Shopify and returns a human-readable string.
        Uses a scoring system for fuzzy matching (best effort).
        """
        print(f"DEBUG: Searching Shopify for: {query}")
        
        request_params = {"limit": 250, "status": "active"}
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"DEBUG: Shopify'dan ürünler çekiliyor... (Limit: 250)")
                
                response = await client.get(
                    f"{self.base_url}/products.json",
                    headers=self.headers,
                    params=request_params 
                )
                response.raise_for_status()
                data = response.json()
        
                all_products = []
                for p_data in data.get("products", []):
                    try:
                        all_products.append(Product(**p_data))
                    except Exception as e:
                        print(f"UYARI: Bir ürün verisi işlenemedi: {p_data.get('title', 'Bilinmiyor')} - Hata: {e}")
                        continue
        
                print(f"DEBUG: Toplam {len(all_products)} ürün hafızaya alındı.")

                # Fuzzy / Scoring Search Algorithm
                scored_results = []
                
                if query:
                    # Normalize query using custom Turkish logic
                    query_lower = self.normalize_turkish(query)
                    query_parts = query_lower.split() 
                    
                    for p in all_products:
                        title_lower = self.normalize_turkish(p.title)
                        score = 0
                        
                        # Check matches for each word
                        for part in query_parts:
                            if part in title_lower:
                                score += 1
                        
                        # Bonus for exact sequence
                        if query_lower in title_lower:
                            score += 2
                            
                        if score > 0:
                            scored_results.append((score, p))
                    
                    # Sort: Highest Score first, then shortest title
                    scored_results.sort(key=lambda x: (-x[0], len(x[1].title)))
                    results = [item[1] for item in scored_results]
                else:
                    results = all_products

                results = results[:limit]
                count = len(results)
                
                top_score = scored_results[0][0] if scored_results else 0
                print(f"DEBUG: Found {count} products. Top Score: {top_score}")

                if count == 0:
                    return "Aradığınız kriterde ürün bulunamadı. Lütfen ürün adını veya rengini değiştirip tekrar deneyiniz."

                # Format Output
                output_lines = []
                if query:
                    output_lines.append(f"🔍 '{query}' için arama sonuçları:\n")

                for p in results:
                    variant_info = []
                    for v in p.variants:
                        # Logic for stock display
                        is_available = False
                        
                        if v.inventory_management is None:
                            is_available = True
                        elif v.inventory_quantity > 0:
                            is_available = True
                        elif v.inventory_policy == "continue":
                            is_available = True
                        
                        status_text = "Mevcut" if is_available else "Tükendi"
                        
                        variant_line = f"   - Varyant ID: {v.id}, Seçenek: {v.title}, Fiyat: {v.price} TL, Durum: {status_text}"
                        variant_info.append(variant_line)
                    
                    # Description Snippet
                    desc_snippet = "Açıklama Yok"
                    if p.body_html:
                        clean_desc = re.sub('<[^<]+?>', '', p.body_html)
                        desc_snippet = clean_desc[:300] + "..." if len(clean_desc) > 300 else clean_desc

                    variants_str = "\n".join(variant_info)
                    output_lines.append(f"Ürün: {p.title}\nÖzellikler: {desc_snippet}\n{variants_str}")
                
                return "\n".join(output_lines)

            except Exception as e:
                print(f"Error searching products: {e}")
                return "Ürün aranırken bir hata oluştu."

    async def create_draft_order(
        self, 
        variant_id: int, 
        quantity: int, 
        first_name: str, 
        last_name: str, 
        address1: str, 
        city: str, 
        phone: str, 
        product_summary: str,
        payment_method: str = "Kredi Kartı", # "Kredi Kartı" or "Kapıda Ödeme"
        email: str = None
    ) -> str:
        """
        Creates a draft order in Shopify with customer details AND saves to local DB. Returns invoice URL or success message.
        """
        from app.db.models import PaymentMethod
        
        # Decide if we need to create a Shopify Draft Order (Only for Credit Card to get Invoice URL)
        # For COD, we might just save to DB, OR create a draft order without invoice link.
        # User requested: "eğer kapıda ödeme yapmak isiiyorum derse ... admin panele kayıtı düş gönderilecek şeklinde not düş"
        
        invoice_url = None
        
        if payment_method == "Kredi Kartı":
            payload = {
                "draft_order": {
                    "line_items": [
                        {
                            "variant_id": variant_id,
                            "quantity": quantity
                        }
                    ],
                    "customer": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email or f"{phone}@example.com", 
                        "phone": phone
                    },
                    "shipping_address": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "address1": address1,
                        "city": city,
                        "phone": phone,
                        "country": "Turkey"
                    },
                    "use_customer_default_address": False
                }
            }
            
            async with httpx.AsyncClient() as client:
                try:
                    print(f"DEBUG: Creating Shopify Draft Order for {first_name} {last_name}")
                    response = await client.post(
                        f"{self.base_url}/draft_orders.json",
                        headers=self.headers,
                        json=payload
                    )
                    response.raise_for_status()
                    data = response.json()
                    invoice_url = data.get("draft_order", {}).get("invoice_url")
                
                except Exception as e:
                    return f"Sipariş oluşturulurken hata oluştu: {str(e)}"

        # 2. Save Order to Local Database (Always)
        try:
            async with SessionLocal() as session:
                order_service = OrderService(session)
                
                # Map string payment method to Enum
                pm_enum = PaymentMethod.COD if payment_method == "Kapıda Ödeme" else PaymentMethod.CREDIT_CARD
                
                await order_service.create_order(
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    email=email,
                    address=f"{address1} {city}",
                    city=city,
                    product_summary=product_summary,
                    payment_method=pm_enum,
                    shopify_invoice_url=invoice_url
                )
                print(f"DEBUG: Order saved to database successfully.")
                
            if payment_method == "Kapıda Ödeme":
                return "✅ Siparişiniz KAPIDA ÖDEME seçeneğiyle alınmıştır! Hazırlanıp en kısa sürede kargoya verilecektir. 📦"
            elif invoice_url:
                return f"✅ Siparişiniz oluşturuldu! Ödeme yapmak için tıklayın: {invoice_url}"
            else:
                return "Sipariş oluşturuldu ancak ödeme linki alınamadı."
                
        except Exception as e:
            print(f"ERROR: Could not save order to DB: {e}")
            return f"Sipariş kaydı sırasında hata oluştu: {str(e)}"
