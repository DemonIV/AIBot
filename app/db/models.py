from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class OrderStatus(str, enum.Enum):
    PENDING = "Beklemede"
    SENT = "Gönderildi/Kargolandı"
    COMPLETED = "Tamamlandı"
    CANCELLED = "İptal Edildi"
    RETURNED = "İade Edildi"

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
    # Mağazaya ait Ürünler
    products = relationship("Product", back_populates="store")
    # Müşteri Etkileşimleri
    interactions = relationship("CustomerInteraction", back_populates="store")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    store = relationship("Store", back_populates="products")
    
    name = Column(String, index=True, nullable=False)
    sku = Column(String, unique=True, index=True, nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    
    # İade Talebi ile İlişki
    return_request = relationship("ReturnRequest", back_populates="order", uselist=False)

class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)
    order = relationship("Order", back_populates="return_request")
    
    reason = Column(Text, nullable=False)
    status = Column(String, default="İnceleniyor") # İnceleniyor, Onaylandı, Reddedildi
    created_at = Column(DateTime, default=datetime.utcnow)

class CustomerInteraction(Base):
    __tablename__ = "customer_interactions"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    store = relationship("Store", back_populates="interactions")
    
    sender_id = Column(String, index=True, nullable=False) # WhatsApp phone number or IG platform ID
    platform = Column(String, nullable=False) # "WhatsApp" veya "Instagram"
    message_count = Column(Integer, default=1)
    last_interaction = Column(DateTime, default=datetime.utcnow)
