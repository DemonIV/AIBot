import os
import sys
from dotenv import load_dotenv

# .env dosyasını zorla okut
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, '.env'))

import asyncio
from app.db.database import engine, Base, SessionLocal
from app.db.models import User, Store
from app.services.auth_service import AuthService

async def kur():
    async with engine.begin() as conn:
        print("Mevcut uyduruk tablolar (varsa) siliniyor...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Devasa PostgreSQL tablolariniz kuruluyor...")
        await conn.run_sync(Base.metadata.create_all)
    
    async with SessionLocal() as db:
        print("Yonetici (Admin) ekleniyor...")
        
        # Sifreleme motorunu baslat ve sifreyi olusur
        auth = AuthService()
        hashed_pw = auth.get_password_hash("admin")
        
        admin_user = User(username="admin", hashed_password=hashed_pw)
        db.add(admin_user)
        try:
            await db.commit()
            print("========================================")
            print("BINGO! HER SEY KUSURSUZ SEKILDE KURULDU!")
            print("Giris ID: admin | Sifre: admin")
            print("========================================")
        except Exception as e:
            print("Hata:", e)

asyncio.run(kur())
