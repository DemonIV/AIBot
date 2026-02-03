from pydantic import BaseModel
from typing import List, Optional

class ProductVariant(BaseModel):
    id: int
    title: str
    price: str
    inventory_quantity: int
    inventory_policy: Optional[str] = "deny"
    inventory_management: Optional[str] = None
    sku: Optional[str] = None

class ProductImage(BaseModel):
    src: str
    alt: Optional[str] = None

class Product(BaseModel):
    id: int
    title: str
    body_html: Optional[str] = None
    handle: str
    product_type: Optional[str] = None
    vendor: Optional[str] = None
    variants: List[ProductVariant] = []
    images: List[ProductImage] = []
    
    @property
    def price_range(self) -> str:
        """Returns a string representation of the price or price range."""
        prices = [float(v.price) for v in self.variants]
        if not prices:
            return "N/A"
        min_p, max_p = min(prices), max(prices)
        if min_p == max_p:
            return f"{min_p:.2f}"
        return f"{min_p:.2f} - {max_p:.2f}"

    @property
    def total_inventory(self) -> int:
        return sum(v.inventory_quantity for v in self.variants)
