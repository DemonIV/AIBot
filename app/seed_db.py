import asyncio

from sqlalchemy.future import select

from app.db.database import Base, SessionLocal, engine
from app.db.models import Store, User, UserRole
from app.services.auth_service import AuthService


async def seed_database() -> None:
    # Ana veritabanı konfigürasyonunu kullanır (DATABASE_URL -> PostgreSQL + asyncpg)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    auth_service = AuthService()

    async with SessionLocal() as db:
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
