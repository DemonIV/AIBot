import google.generativeai as genai
from google.generativeai.types import content_types
from collections import defaultdict
import json
from app.core.config import settings
from app.services.shopify_service import ShopifyClient

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.shopify_client = ShopifyClient()
        
        self.system_prompt = """Sen Moda Masal mağazasının yapay zeka satış asistanısın.
Görevin: Müşterilerin ürün sorularını yanıtlamak ve sipariş oluşturmak.

ÖNEMLİ PERSONA VE KONUŞMA KURALLARI:
1. NOKTALAMA İŞARETİ KULLANMA: Fiyat ve sayısal değerler için kesinlikle noktalama işareti kullan. Konuşurken nokta virgül vs hiç kullanma sadece dümdüz yaz sanki hızlı yazıyormuşsun gibi
2. SAMİMİ VE NAZİK OL: "Efendim" diye hitap edebilirsin çok nazik ol
3. EMOJİ KULLAN: Cümlelerinde mutlaka en az bir tane emoji olsun 🌸 👗 ✨
4. STOK BİLGİSİ: Asla "5 adet var" gibi sayı verme Sadece "Stoklarımızda mevcuttur" veya "Stoklarımızda mevcut değildir efendim" de
5. ÖNERİ YAP: Eğer istenen ürünün stoğu yoksa ("Durum: Tükendi" ise) ürün açıklamasını (Özellikler kısmını) oku ve kumaşı boyu kategorisi benzer olan başka bir ürün varsa onu öner "Bu tükendi ama dilerseniz şu modelimize bakabilirsiniz" de
6. TÜRKÇE KARAKTERLER: Müşteri "ikra" yazarsa sen "İkra" ürününü anlayacaksın harf uyumuna takılma

SİPARİŞ ALMA SÜRECİ (ÇOK ÖNEMLİ):
Müşteri bir ürünü satın almak istediğinde HEMEN sipariş oluşturma. Sırasıyla şu bilgileri İSTE:
1. "Tabii siparişinizi oluşturmak için hangi beden ve renk istediğinizi öğrenebilir miyim?" (Eğer zaten söylediyse geç)
2. "Sipariş teslimatı için İsim, Soyisim, Açık Adres, Şehir ve Telefon Numaranızı rica edebilir miyim? 🌸" (Mail adresi opsiyonel)
3. Müşteri bilgileri verince HEPSİNİ özetle ve onayla: "Bilgilerinizi şöyle aldım: ... Doğru mudur efendim?"
4. Müşteri "Evet" derse ŞUNU SOR: "Ödemenizi Kredi Kartı ile Web Sitemizden mi yoksa Kapıda Ödeme ile mi yapmak istersiniz?"
5. Müşterinin cevabına göre `create_draft_order` aracını kullan:
   - Kredi Kartı derse: `payment_method="Kredi Kartı"` yap. Link oluşur.
   - Kapıda Ödeme derse: `payment_method="Kapıda Ödeme"` yap. Link oluşmaz, sadece onay mesajı döner.
6. Araca İsim, Soyisim, Adres, Şehir, Tel bilgilerini EKSİKSİZ gir. `product_summary` alanını doldur.
7. Sonuç mesajını müşteriye ilet.

ASLA YAPMA:
- Eksik bilgiyle sipariş oluşturma.
- Fiyat veya stok uydurma `search_products` ne derse o
- Müşteriye "Yapay zekayım" deme satış danışmanı gibi davran
"""
        
        # Tools definition for Gemini
        self.tools_config = [
            {
                "function_declarations": [
                    {
                        "name": "search_products",
                        "description": "Search for products in the store.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search keyword."
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "create_draft_order",
                        "description": "Create a checkout link or confirm order.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "variant_id": {
                                    "type": "integer",
                                    "description": "The Variant ID of the product."
                                },
                                "quantity": {
                                    "type": "integer",
                                    "description": "Quantity to order."
                                },
                                "first_name": {"type": "string"},
                                "last_name": {"type": "string"},
                                "address1": {"type": "string"},
                                "city": {"type": "string"},
                                "phone": {"type": "string"},
                                "product_summary": {"type": "string", "description": "Short summary of product name, color, size requested by user."},
                                "payment_method": {"type": "string", "enum": ["Kredi Kartı", "Kapıda Ödeme"], "description": "Payment method choice."},
                                "email": {"type": "string"}
                            },
                            "required": ["variant_id", "first_name", "last_name", "address1", "city", "phone", "product_summary", "payment_method"]
                        }
                    }
                ]
            }
        ]

        self.model = genai.GenerativeModel(
            model_name='gemini-flash-latest',
            system_instruction=self.system_prompt,
            tools=self.tools_config
        )
        
        # In-memory history: {session_id: ChatSession}
        # Note: We store the chat object itself which manages history
        self.chat_sessions = {}

    async def generate_response(self, user_message: str, session_id: str) -> str:
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = self.model.start_chat(enable_automatic_function_calling=False)
        
        chat = self.chat_sessions[session_id]
        
        try:
            # Send message to model
            response = await chat.send_message_async(user_message)
            
            # Check for function calls
            # Gemini handles function calls via 'parts'
            if not response.parts:
                 return response.text

            part = response.parts[0]
            
            if part.function_call:
                fc = part.function_call
                function_name = fc.name
                function_args = fc.args
                
                tool_result = ""
                
                if function_name == "search_products":
                    query = function_args.get("query")
                    tool_result = await self.shopify_client.search_products(query=query)
                elif function_name == "create_draft_order":
                    # Args come as floats sometimes in JSON parsing, ensure int
                    variant_id = int(function_args.get("variant_id"))
                    quantity = int(function_args.get("quantity", 1))
                    
                    first_name = function_args.get("first_name")
                    last_name = function_args.get("last_name")
                    address1 = function_args.get("address1")
                    city = function_args.get("city")
                    phone = function_args.get("phone")
                    product_summary = function_args.get("product_summary")
                    email = function_args.get("email")
                    payment_method = function_args.get("payment_method")

                    tool_result = await self.shopify_client.create_draft_order(
                        variant_id=variant_id, 
                        quantity=quantity,
                        first_name=first_name,
                        last_name=last_name,
                        address1=address1,
                        city=city,
                        phone=phone,
                        product_summary=product_summary,
                        payment_method=payment_method,
                        email=email
                    )
                
                # Send the tool result back to the model
                function_response_part = genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=function_name,
                        response={'result': tool_result}
                    )
                )
                
                final_response = await chat.send_message_async([function_response_part])
                return final_response.text
            
            return response.text

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Gemini Service Error: {e}")
            print(f"Traceback: {error_details}")
            return f"Teknik Hata Detayı: {str(e)}"
