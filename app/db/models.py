from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
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

class UserRole(str, enum.Enum):
    ADMIN = "admin" # Super Admin
    STORE_OWNER = "owner" # Müşteri mağaza sahibi

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STORE_OWNER)
    
    # Bir kullanıcının yönettği mağazalar
    stores = relationship("Store", back_populates="owner")

class Store(Base):
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Mağaza Sahibi (Kullanıcı)
    owner = relationship("User", back_populates="stores")
    # Mağazaya ait Siparişler
    orders = relationship("Order", back_populates="store")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    
    # Bağlı olduğu mağaza
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True) # Şimdilik Nullable, göç kolaylığı için
    store = relationship("Store", back_populates="orders")
    
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
