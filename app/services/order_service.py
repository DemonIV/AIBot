from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import Order, OrderStatus, OrderSource, PaymentMethod
from typing import List, Optional

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        address: str,
        city: str,
        product_summary: str,
        source: OrderSource = OrderSource.WEB,
        payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD,
        email: str = None,
        shopify_invoice_url: str = None
    ) -> Order:
        new_order = Order(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address,
            city=city,
            product_summary=product_summary,
            source=source,
            payment_method=payment_method,
            email=email,
            shopify_invoice_url=shopify_invoice_url,
            status=OrderStatus.PENDING
        )
        self.db.add(new_order)
        await self.db.commit()
        await self.db.refresh(new_order)
        return new_order

    async def get_orders(self, skip: int = 0, limit: int = 100) -> List[Order]:
        result = await self.db.execute(select(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit))
        return result.scalars().all()

    async def update_status(self, order_id: int, status: OrderStatus) -> Optional[Order]:
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order:
            order.status = status
            await self.db.commit()
            await self.db.refresh(order)
        return order
