from fastapi import FastAPI
from app.api.v1.api_router import api_router
from app.routers import admin, webhooks
from app.db.database import init_db

app = FastAPI(title="ModaMasal AI Backend")

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(api_router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])

from fastapi.responses import HTMLResponse

FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moda Masal AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-pink-50 min-h-screen flex flex-col items-center justify-center p-4">
    <div class="max-w-2xl bg-white p-8 rounded-xl shadow-lg text-center">
        <h1 class="text-4xl font-bold text-pink-600 mb-4">Moda Masal Yapay Zeka Asistanı 🌸</h1>
        <p class="text-gray-700 mb-6 text-lg">Sipariş, mesajlaşma ve yapay zeka altyapımız başarıyla çalışmaktadır.</p>
        
        <div class="flex justify-center gap-4 mb-8">
            <a href="/api/v1/admin/" class="bg-pink-500 hover:bg-pink-600 text-white font-bold py-2 px-6 rounded-full transition shadow-md">
                Yönetim Paneline Git 🛍️
            </a>
        </div>
        
        <div class="text-sm text-gray-500 flex justify-center gap-6 border-t pt-4">
            <a href="/privacy" class="hover:text-pink-500 underline">Gizlilik Politikası</a>
            <a href="/terms" class="hover:text-pink-500 underline">Kullanım Şartları</a>
        </div>
    </div>
</body>
</html>
"""

PRIVACY_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gizlilik Politikası - Moda Masal AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 p-8 font-sans">
    <div class="max-w-3xl mx-auto bg-white p-8 rounded-lg shadow">
        <h1 class="text-3xl font-bold mb-6 border-b pb-2">Gizlilik Politikası (Privacy Policy)</h1>
        <p class="mb-4 text-sm text-gray-500">Son güncellenme: 2026</p>
        
        <h2 class="text-xl font-semibold mt-6 mb-2 text-pink-600">1. Toplanan Veriler</h2>
        <p class="text-gray-700 mb-4">Facebook, Instagram ve WhatsApp üzerinden bizimle iletişime geçtiğinizde; adınız, telefon numaranız, adresiniz ve mesaj içerikleriniz siparişlerinizi işleyebilmek adına yetkili temsilcilerimiz tarafından güvenli bir şekilde toplanır.</p>

        <h2 class="text-xl font-semibold mt-6 mb-2 text-pink-600">2. Verilerin Kullanımı</h2>
        <p class="text-gray-700 mb-4">Toplanan veriler yalnızca e-ticaret siparişlerinizi oluşturma, kargolama süreçlerini yönetme ve müşteri hizmetleri desteği sağlamak amacıyla kullanılır. Üçüncü şahıslarla reklam veya pazarlama amacıyla paylaşılmaz.</p>

        <h2 class="text-xl font-semibold mt-6 mb-2 text-pink-600">3. Verilerin Korunması</h2>
        <p class="text-gray-700 mb-4">Kişisel verileriniz güvenli sunucularımızda korunmaktadır. Verilerinizin silinmesini talep etmek için iletişim kanallarımızdan bize ulaşabilirsiniz.</p>

        <div class="mt-8 pt-4 border-t">
            <a href="/" class="text-blue-500 hover:text-blue-700 font-semibold">← Ana Sayfaya Dön</a>
        </div>
    </div>
</body>
</html>
"""

TERMS_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kullanım Şartları - Moda Masal AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 p-8 font-sans">
    <div class="max-w-3xl mx-auto bg-white p-8 rounded-lg shadow">
        <h1 class="text-3xl font-bold mb-6 border-b pb-2">Kullanım Şartları</h1>
        <p class="text-gray-700 mb-4">Moda Masal yapay zeka asistanını kullanarak, botumuzla yaptığınız görüşmelerin sipariş amaçlı işlendiğini kabul etmiş olursunuz. Sipariş oluşturma esnasında verdiğiniz bilgilerin doğruluğu size aittir.</p>
        <div class="mt-8 pt-4 border-t">
            <a href="/" class="text-blue-500 hover:text-blue-700 font-semibold">← Ana Sayfaya Dön</a>
        </div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=FRONTEND_HTML)

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    return HTMLResponse(content=PRIVACY_HTML)

@app.get("/terms", response_class=HTMLResponse)
async def terms():
    return HTMLResponse(content=TERMS_HTML)
