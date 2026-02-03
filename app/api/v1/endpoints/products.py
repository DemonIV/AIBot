from fastapi import APIRouter, Query
from typing import List
from app.services.shopify_service import ShopifyClient
from app.schemas.product import Product

router = APIRouter()

@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=2, description="Search query for product title")
):
    """
    Search for products by title.
    """
    client = ShopifyClient()
    products_str = await client.search_products(query=q)
    return {"result": products_str}
