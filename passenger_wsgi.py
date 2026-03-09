import os
import sys

# Application root directory'sini path'e ekliyoruz
sys.path.insert(0, os.path.dirname(__file__))

# .env (ortam degiskenlerini) WSGI uyanirken okumasi icin en basa ekliyoruz
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ASGI olan FastAPI'yi Namecheap'in (WSGI) anlayacagi dile ceviren kopru
from a2wsgi import ASGIMiddleware
from app.main import app

# cPanel/Passenger'in calistiracagi asil obje 'application'
application = ASGIMiddleware(app)
