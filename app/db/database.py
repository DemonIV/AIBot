import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Check for DATABASE_URL (Cloud) or use local SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"DEBUGGING STARTUP: Raw DATABASE_URL found: {bool(DATABASE_URL)}")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if not DATABASE_URL:
    # Fallback to local SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./modamasal.db"
    print("DEBUGGING STARTUP: Using Local SQLite")

print(f"DEBUGGING STARTUP: Final URL Scheme: {DATABASE_URL.split('://')[0]}")

try:
    engine = create_async_engine(DATABASE_URL, echo=True)
except Exception as e:
    print(f"CRITICAL DB ENGINE ERROR: {e}")
    raise e
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
