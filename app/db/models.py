from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from datetime import datetime
import enum
from .database import Base

class OrderStatus(str, enum.Enum):
    PENDING = "Beklemede"
    SENT = "Gönderildi/Kargolandı"
    COMPLETED = "Tamamlandı"
    CANCELLED = "İptal Edildi"

class OrderSource(str, enum.Enum):
    WEB = "Web"
    WHATSAPP = "WhatsApp"
    INSTAGRAM = "Instagram"

class PaymentMethod(str, enum.Enum):
    CREDIT_CARD = "Kredi Kartı"
    COD = "Kapıda Ödeme"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    
    # Customer Info
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    phone = Column(String, index=True)
    email = Column(String, nullable=True)
    
    # Address Info
    address = Column(Text) # Full address
    city = Column(String)
    
    # Order Details
    product_summary = Column(Text) # E.g., "İkra Elbise (Kırmızı, 38)"
    amount = Column(String, nullable=True) # Optional price
    shopify_invoice_url = Column(String, nullable=True)
    
    # Meta
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    source = Column(Enum(OrderSource), default=OrderSource.WEB)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CREDIT_CARD)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
