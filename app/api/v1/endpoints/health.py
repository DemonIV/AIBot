from fastapi import APIRouter, HTTPException
from app.services.shopify_service import ShopifyClient

router = APIRouter()

@router.get("/health")
async def health_check():
    client = ShopifyClient()
    try:
        shop_data = await client.check_connection()
        return {
            "status": "active",
            "shop_name": shop_data.get("shop", {}).get("name", "Unknown"),
            "myshopify_domain": shop_data.get("shop", {}).get("myshopify_domain", "Unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
