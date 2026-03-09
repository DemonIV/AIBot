from fastapi import FastAPI
from app.api.v1.api_router import api_router
from app.routers import admin, webhooks
from app.db.database import init_db

app = FastAPI(title="ModaMasal AI Backend")

# init_db is handled manually via seed_db.py now
# startup hook removed to prevent WSGI deadlocks

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
    <title>Moda Masal | Yapay Zeka Destekli Otomasyon Sistemi</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Poppins', 'sans-serif'],
                        serif: ['Playfair Display', 'serif'],
                    },
                    colors: {
                        brand: {
                            50: '#fdf2f8',
                            100: '#fce7f3',
                            500: '#ec4899',
                            600: '#db2777',
                            900: '#831843',
                        }
                    }
                }
            }
        }
    </script>
    <style>
        .glass-card {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
        }
        .hero-bg {
            background-color: #fdf2f8;
            background-image: 
                radial-gradient(at 0% 0%, hsla(340,100%,76%,0.15) 0px, transparent 50%),
                radial-gradient(at 100% 0%, hsla(340,100%,76%,0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, hsla(380,100%,76%,0.15) 0px, transparent 50%),
                radial-gradient(at 0% 100%, hsla(340,100%,76%,0.15) 0px, transparent 50%);
        }
    </style>
</head>
<body class="hero-bg min-h-screen flex flex-col font-sans text-gray-800 antialiased selection:bg-brand-500 selection:text-white">

    <!-- Navigation -->
    <nav class="absolute top-0 w-full p-6 flex justify-between items-center z-10">
        <div class="text-2xl font-serif font-bold text-brand-900 tracking-tight">
            Moda<span class="text-brand-500">Masal</span>
        </div>
        <div class="space-x-6 text-sm font-medium text-gray-600 hidden md:block">
            <a href="/privacy" class="hover:text-brand-500 transition-colors">Gizlilik Politikası</a>
            <a href="/terms" class="hover:text-brand-500 transition-colors">Kullanım Şartları</a>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow flex items-center justify-center p-6 relative">
        <div class="absolute inset-0 z-0 overflow-hidden pointer-events-none">
            <div class="absolute -top-24 -left-24 w-96 h-96 bg-brand-100/50 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob"></div>
            <div class="absolute top-0 -right-4 w-96 h-96 bg-purple-100/50 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-2000"></div>
            <div class="absolute -bottom-8 left-20 w-96 h-96 bg-pink-100/50 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-4000"></div>
        </div>

        <div class="max-w-4xl w-full z-10 text-center">
            
            <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/60 border border-brand-100 text-brand-600 text-sm font-medium mb-8 shadow-sm">
                <span class="relative flex h-2 w-2">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-brand-500"></span>
                </span>
                Sistem Aktif & Çalışıyor
            </div>

            <h1 class="text-5xl md:text-7xl font-serif font-bold text-gray-900 mb-6 leading-tight">
                Yeni Nesil <br />
                <span class="text-transparent bg-clip-text bg-gradient-to-r from-brand-500 to-purple-500">Yönetim Paneli</span>
            </h1>
            
            <p class="text-lg md:text-xl text-gray-600 mb-12 max-w-2xl mx-auto leading-relaxed">
                Moda Masal'ın yapay zeka destekli altyapısına hoş geldiniz. WhatsApp ve Instagram siparişlerinizi, iadelerinizi ve müşteri etkileşimlerinizi tek bir merkezden yönetin.
            </p>
            
            <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
                <a href="/api/v1/admin/login" class="group relative inline-flex items-center justify-center px-8 py-4 text-base font-bold text-white transition-all duration-200 bg-brand-600 border border-transparent rounded-full hover:bg-brand-500 hover:shadow-lg hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-600 w-full sm:w-auto">
                    Yönetim Paneline Giriş Yap
                    <svg class="w-5 h-5 ml-2 -mr-1 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path></svg>
                </a>
            </div>

        </div>
    </main>

    <!-- Footer Mobile Links -->
    <footer class="p-6 text-center text-sm font-medium text-gray-500 md:hidden z-10">
        <a href="/privacy" class="mx-2 hover:text-brand-500">Gizlilik</a>
        <a href="/terms" class="mx-2 hover:text-brand-500">Şartlar</a>
    </footer>

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
