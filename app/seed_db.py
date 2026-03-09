import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from app.db.models import Base, User, Store, UserRole
from app.services.auth_service import AuthService
from app.core.config import settings
import os

DATABASE_URL = "sqlite+aiosqlite:///./modamasal.db"

async def seed_database():
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    # Yeni tabloları oluştur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    auth_service = AuthService()

    async with SessionLocal() as db:
        # Kontrol et, admin var mı?
        result = await db.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalars().first()
        
        if not admin_user:
            print("Creating default admin user...")
            hashed_pw = auth_service.get_password_hash("admin")
            admin_user = User(username="admin", hashed_password=hashed_pw, role=UserRole.ADMIN)
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            print("Admin user created (username: admin, password: admin)")
        else:
            print("Admin user already exists.")
            
        # Default Store oluştur (Eğer yoksa)
        store_result = await db.execute(select(Store).where(Store.name == "ModaMasal Default"))
        default_store = store_result.scalars().first()
        
        if not default_store:
            print("Creating default store...")
            default_store = Store(name="ModaMasal Default", owner_id=admin_user.id)
            db.add(default_store)
            await db.commit()
            print("Default store created.")
        else:
            print("Default store already exists.")

if __name__ == "__main__":
    asyncio.run(seed_database())
