import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 1. Ortam degiskenlerini WSGI veya yerel ortamdan garanti okuma
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 2. SADECE PostgreSQL! SQLite veya MySQL tamamen yasaklandi.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("KRITIK HATA: DATABASE_URL ayarlari bulunamadi. Proje sadece PostgreSQL ile calismaya ayarlidir!")

DATABASE_URL = DATABASE_URL.strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

print(f"PRODUCTION DB URL: {DATABASE_URL.split('://')[0]}")

# echo=False yaparak console kirliligini engelliyoruz (Production)
try:
    engine = create_async_engine(DATABASE_URL, echo=False)
except Exception as e:
    print(f"CRITICAL DB ENGINE ERROR: {e}")
    raise e

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session

async def init_db():
    try:
        # Tablolari otomatik kur (varsa dokunmaz)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # Admin kullanicisi yoksa yarat
        from app.db.models import User
        from app.services.auth_service import AuthService
        from sqlalchemy.future import select
        
        async with SessionLocal() as db:
            result = await db.execute(select(User).filter(User.username == "admin"))
            admin_user = result.scalars().first()
            if not admin_user:
                auth = AuthService()
                hashed_pw = auth.get_password_hash("admin")
                new_admin = User(username="admin", hashed_password=hashed_pw)
                db.add(new_admin)
                await db.commit()
                print("==> VERICIKARISI YAPILDI: Tablolar ve VIP (admin) kullanicisi kuruldu.")
    except Exception as e:
        print(f"Normal Arkaplan Kurulum Hatasi: {e}")
