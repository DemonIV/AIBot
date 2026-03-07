from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.db.database import get_db
from app.services.order_service import OrderService
from app.services.auth_service import AuthService
from app.db.models import Order, OrderStatus, User, CustomerInteraction, InteractionPlatform
from typing import List

router = APIRouter()
auth_service = AuthService()

# Bağımlılık (Dependency): Oturum Kontrolü
def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # "Bearer " kısmını at
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ModaMasal Yönetim Paneli</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Poppins', sans-serif; }
        .tab-active { border-bottom: 2px solid #ec4899; color: #db2777; }
        .tab-inactive { color: #6b7280; }
        .tab-inactive:hover { color: #ec4899; }
    </style>
</head>
<body class="bg-gray-50 font-sans text-sm text-gray-800">
    <div id="app" class="container mx-auto p-4 md:p-6 lg:p-8">
        
        <!-- HEADER & NAVIGATION -->
        <header class="mb-8">
            <div class="flex flex-col md:flex-row justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-pink-50 gap-4">
                <h1 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-500 to-rose-400 flex items-center gap-2">
                    🛍️ ModaMasal AI Panel
                </h1>
                <div class="flex gap-4 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
                    <button @click="currentTab = 'dashboard'" :class="currentTab === 'dashboard' ? 'tab-active' : 'tab-inactive'" class="px-4 py-2 font-semibold whitespace-nowrap transition-colors">
                        <i class="fas fa-chart-line mr-2"></i>İstatistikler
                    </button>
                    <button @click="currentTab = 'orders'" :class="currentTab === 'orders' ? 'tab-active' : 'tab-inactive'" class="px-4 py-2 font-semibold whitespace-nowrap transition-colors">
                        <i class="fas fa-box-open mr-2"></i>Siparişler
                    </button>
                    <button @click="currentTab = 'returns'" :class="currentTab === 'returns' ? 'tab-active' : 'tab-inactive'" class="px-4 py-2 font-semibold whitespace-nowrap transition-colors">
                        <i class="fas fa-undo mr-2"></i>İptal & İadeler
                    </button>
                </div>
                <div class="flex gap-2 items-center">
                    <button @click="fetchOrders" class="text-pink-500 hover:text-pink-600 bg-pink-50 hover:bg-pink-100 p-2 rounded-full transition" title="Yenile">
                        <i class="fas fa-sync-alt" :class="{'fa-spin': isLoading}"></i>
                    </button>
                    <a href="/api/v1/admin/logout" class="text-gray-500 hover:text-red-500 bg-gray-100 hover:bg-red-50 p-2 rounded-full transition" title="Çıkış Yap">
                        <i class="fas fa-sign-out-alt"></i>
                    </a>
                </div>
            </div>
        </header>

        <!-- TAB 1: DASHBOARD (İSTATİSTİKLER) -->
        <div v-show="currentTab === 'dashboard'" class="space-y-6">
            <!-- Summary Cards -->
            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-purple-50">
                    <div class="text-purple-500 mb-2"><i class="fas fa-users text-2xl"></i></div>
                    <div class="text-2xl font-bold text-gray-800">{{ adminStats.total_unique_customers }}</div>
                    <div class="text-sm text-gray-500">Görüşülen Müşteri</div>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-blue-50">
                    <div class="text-blue-500 mb-2"><i class="fas fa-shopping-bag text-2xl"></i></div>
                    <div class="text-2xl font-bold text-gray-800">{{ stats.totalOrders }}</div>
                    <div class="text-sm text-gray-500">Toplam Sipariş</div>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-green-50">
                    <div class="text-green-500 mb-2"><i class="fas fa-check-circle text-2xl"></i></div>
                    <div class="text-2xl font-bold text-gray-800">{{ stats.completedOrders }}</div>
                    <div class="text-sm text-gray-500">Tamamlanan</div>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-yellow-50">
                    <div class="text-yellow-500 mb-2"><i class="fas fa-clock text-2xl"></i></div>
                    <div class="text-2xl font-bold text-gray-800">{{ stats.pendingOrders }}</div>
                    <div class="text-sm text-gray-500">Bekleyenler</div>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-red-50">
                    <div class="text-red-500 mb-2"><i class="fas fa-times-circle text-2xl"></i></div>
                    <div class="text-2xl font-bold text-gray-800">{{ stats.lossOrders }}</div>
                    <div class="text-sm text-gray-500">İptal / İade</div>
                </div>
            </div>

            <!-- Charts -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Line Chart -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 class="font-bold text-gray-700 mb-4 border-b pb-2">Son 7 Günlük Sipariş Trendi</h3>
                    <canvas id="trendChart" height="250"></canvas>
                </div>
                <!-- Doughnut Chart -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 class="font-bold text-gray-700 mb-4 border-b pb-2">Sipariş Durum Dağılımı</h3>
                    <div class="flex justify-center h-[250px]">
                        <canvas id="statusChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: ALL ORDERS -->
        <div v-show="currentTab === 'orders'" class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                <div class="relative w-full max-w-md">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <i class="fas fa-search text-gray-400"></i>
                    </div>
                    <input v-model="searchQuery" type="text" class="block w-full pl-10 pr-3 py-2 border border-gray-200 rounded-xl bg-white focus:border-pink-300 focus:ring-2 focus:ring-pink-100 transition shadow-inner" placeholder="Satışlarda ara...">
                </div>
            </div>
            
            <!-- Shared Table Component -->
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <!-- Table Header -->
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Durum</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Tarih</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Müşteri</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Detaylar</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">İşlem</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-100">
                        <tr v-for="order in activeOrders" :key="order.id" class="hover:bg-pink-50/30 transition">
                            <td class="px-6 py-4 whitespace-nowrap"><span :class="statusClass(order.status)" class="px-3 py-1 text-xs font-semibold rounded-full border">{{ order.status }}</span></td>
                            <td class="px-6 py-4 whitespace-nowrap text-gray-500 text-xs">{{ formatDate(order.created_at) }}</td>
                            <td class="px-6 py-4">
                                <div class="font-medium text-gray-900">{{ order.first_name }} {{ order.last_name }}</div>
                                <div v-if="order.social_username" class="text-xs text-pink-500 font-bold mt-1 tracking-wide">
                                    <i class="fab fa-instagram mr-1"></i>@{{ order.social_username }}
                                </div>
                                <div class="text-xs text-gray-500 mt-1"><i class="fas fa-phone mr-1"></i>{{ order.phone }}</div>
                            </td>
                            <td class="px-6 py-4">
                                <div class="text-sm text-gray-800 font-medium mb-1">{{ order.product_summary }}</div>
                                <div class="text-xs text-gray-600 bg-gray-50 p-2 rounded border border-gray-100 line-clamp-2" :title="order.address + ' ' + order.city">{{ order.address }} - {{ order.city }}</div>
                                <div class="mt-1"><span class="text-xs font-bold text-blue-600">{{ order.payment_method }}</span></div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm">
                                <select @change="updateStatus(order.id, $event.target.value)" class="bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg focus:ring-pink-500 focus:border-pink-500 block w-full p-2">
                                    <option :selected="order.status === 'Beklemede'" value="Beklemede">Beklemede</option>
                                    <option :selected="order.status === 'Gönderildi/Kargolandı'" value="Gönderildi/Kargolandı">Gönderildi</option>
                                    <option :selected="order.status === 'Tamamlandı'" value="Tamamlandı">Tamamlandı</option>
                                    <option :selected="order.status === 'İptal Edildi'" value="İptal Edildi">İptal Edildi</option>
                                    <option :selected="order.status === 'İade Edildi'" value="İade Edildi">İade Edildi</option>
                                </select>
                            </td>
                        </tr>
                        <tr v-if="activeOrders.length === 0">
                            <td colspan="5" class="text-center py-12 text-gray-400"><i class="fas fa-box-open text-4xl mb-2 block opacity-50"></i>Kayıt bulunamadı.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- TAB 3: RETURNS & CANCELLATIONS -->
        <div v-show="currentTab === 'returns'" class="bg-white rounded-2xl shadow-sm border border-red-50 overflow-hidden">
             <div class="p-4 border-b border-red-100 bg-red-50/30 flex justify-between items-center">
                <h2 class="font-bold text-red-700"><i class="fas fa-exclamation-triangle mr-2"></i>Sorunlu Siparişler (İptal & İade)</h2>
                <div class="relative w-full max-w-sm">
                    <input v-model="returnSearchQuery" type="text" class="block w-full pl-3 pr-3 py-2 border border-red-200 rounded-xl bg-white focus:border-red-400 focus:ring-2 focus:ring-red-100 shadow-inner text-sm" placeholder="İadelerde ara...">
                </div>
            </div>
            
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Durum</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Tarih</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Ayrıntılar</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">İşlem</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-100">
                        <tr v-for="order in returnOrders" :key="order.id" class="hover:bg-red-50/50 transition">
                            <td class="px-6 py-4 whitespace-nowrap"><span :class="statusClass(order.status)" class="px-3 py-1 text-xs font-bold rounded-full border">{{ order.status }}</span></td>
                            <td class="px-6 py-4 whitespace-nowrap text-gray-500 text-xs">{{ formatDate(order.created_at) }}</td>
                            <td class="px-6 py-4">
                                <div class="font-bold text-gray-800">{{ order.first_name }} {{ order.last_name }} - {{ order.phone }}</div>
                                <div class="text-sm text-gray-600 mt-1">{{ order.product_summary }}</div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm">
                                <button @click="updateStatus(order.id, 'Beklemede')" class="text-blue-600 hover:text-blue-800 underline text-xs font-semibold">Talebi Geri Al (Bekleyenlere Taşı)</button>
                            </td>
                        </tr>
                        <tr v-if="returnOrders.length === 0">
                            <td colspan="4" class="text-center py-12 text-gray-400"><i class="fas fa-check-circle text-4xl mb-2 block opacity-50 text-green-400"></i>Sorunlu sipariş yok!</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </div>

    <script>
        const { createApp } = Vue;

        createApp({
            data() {
                return {
                    currentTab: 'dashboard',
                    orders: [],
                    adminStats: { total_unique_customers: 0, whatsapp_customers: 0, instagram_customers: 0 },
                    searchQuery: '',
                    returnSearchQuery: '',
                    isLoading: false,
                    chartInstances: {}
                }
            },
            computed: {
                stats() {
                    const total = this.orders.length;
                    const completed = this.orders.filter(o => o.status === 'Tamamlandı' || o.status === 'Gönderildi/Kargolandı').length;
                    const pending = this.orders.filter(o => o.status === 'Beklemede').length;
                    const lost = this.orders.filter(o => ['İptal Edildi', 'İade Edildi'].includes(o.status)).length;
                    return { totalOrders: total, completedOrders: completed, pendingOrders: pending, lossOrders: lost };
                },
                activeOrders() {
                    const normalOrders = this.orders.filter(o => !['İptal Edildi', 'İade Edildi'].includes(o.status));
                    return this.filterArray(normalOrders, this.searchQuery);
                },
                returnOrders() {
                    const badOrders = this.orders.filter(o => ['İptal Edildi', 'İade Edildi'].includes(o.status));
                    return this.filterArray(badOrders, this.returnSearchQuery);
                }
            },
            methods: {
                filterArray(arr, query) {
                    if (!query) return arr;
                    const q = query.toLowerCase().trim();
                    return arr.filter(o => {
                        const str = `${o.id} ${o.first_name} ${o.last_name} ${o.phone} ${o.city} ${o.product_summary} ${o.social_username || ''}`.toLowerCase();
                        return str.includes(q);
                    });
                },
                async fetchOrders() {
                    this.isLoading = true;
                    try {
                        const response = await axios.get('/api/v1/admin/orders');
                        this.orders = response.data;
                        
                        const statsResponse = await axios.get('/api/v1/admin/stats');
                        this.adminStats = statsResponse.data;
                        
                        this.$nextTick(() => { this.updateCharts(); }); // Update graphs after DOM
                    } catch (error) {
                        if (error.response && error.response.status === 401) window.location.href = '/api/v1/admin/login';
                        else console.error('Data pull failed', error);
                    } finally {
                        this.isLoading = false;
                    }
                },
                async updateStatus(id, newStatus) {
                    if(!confirm(`Statüyü '${newStatus}' olarak değiştirmek istiyor musunuz?`)) return;
                    try {
                        await axios.put(`/api/v1/admin/orders/${id}/status?status=${newStatus}`);
                        const index = this.orders.findIndex(o => o.id === id);
                        if(index !== -1) this.orders[index].status = newStatus;
                        this.$nextTick(() => { this.updateCharts(); });
                    } catch (error) {
                        if (error.response?.status === 401) window.location.href = '/api/v1/admin/login';
                        else alert('Güncelleme başarısız!');
                    }
                },
                formatDate(dateStr) {
                    if (!dateStr) return '';
                    return new Date(dateStr).toLocaleString('tr-TR', { day: 'numeric', month: 'short', hour:'2-digit', minute:'2-digit' });
                },
                statusClass(status) {
                    const map = {
                        'Beklemede': 'bg-yellow-100 text-yellow-700 border-yellow-200',
                        'Gönderildi/Kargolandı': 'bg-blue-100 text-blue-700 border-blue-200',
                        'Tamamlandı': 'bg-green-100 text-green-700 border-green-200',
                        'İptal Edildi': 'bg-orange-100 text-orange-700 border-orange-200',
                        'İade Edildi': 'bg-red-100 text-red-700 border-red-200'
                    };
                    return map[status] || 'bg-gray-100 text-gray-700';
                },
                updateCharts() {
                    // Destroy old charts to prevent overlapping
                    if(this.chartInstances.trend) this.chartInstances.trend.destroy();
                    if(this.chartInstances.status) this.chartInstances.status.destroy();

                    // 1. Data Prep for Trend Chart (Last 7 Days)
                    const last7Days = [...Array(7)].map((_, i) => {
                        const d = new Date(); d.setDate(d.getDate() - i);
                        return d.toISOString().split('T')[0];
                    }).reverse();

                    const countsByDay = last7Days.reduce((acc, date) => ({...acc, [date]: 0}), {});
                    this.orders.forEach(o => {
                        const dateOnly = o.created_at.split('T')[0];
                        if(countsByDay[dateOnly] !== undefined) countsByDay[dateOnly]++;
                    });

                    // Render Trend Chart
                    const ctxTrend = document.getElementById('trendChart');
                    if (ctxTrend) {
                        this.chartInstances.trend = new Chart(ctxTrend, {
                            type: 'line',
                            data: {
                                labels: last7Days.map(d => d.substring(5)), // MM-DD format
                                datasets: [{
                                    label: 'Günlük Sipariş/İstek',
                                    data: Object.values(countsByDay),
                                    borderColor: '#ec4899', backgroundColor: 'rgba(236, 72, 153, 0.1)',
                                    borderWidth: 2, fill: true, tension: 0.4
                                }]
                            },
                        });
                    }

                    // Render Status Doughnut Chart
                    const ctxStatus = document.getElementById('statusChart');
                    if (ctxStatus) {
                        this.chartInstances.status = new Chart(ctxStatus, {
                            type: 'doughnut',
                            data: {
                                labels: ['Başarılı/Gönderildi', 'Bekliyor', 'İptal/İade'],
                                datasets: [{
                                    data: [
                                        this.stats.completedOrders,
                                        this.stats.pendingOrders,
                                        this.stats.lossOrders
                                    ],
                                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                                    borderWidth: 0
                                }]
                            },
                            options: { maintainAspectRatio: false, cutout: '70%'}
                        });
                    }
                }
            },
            mounted() {
                this.fetchOrders();
                setInterval(this.fetchOrders, 60000); // 1 minute auto refresh
            }
        }).mount('#app');
    </script>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Giriş Yap - Moda Masal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Poppins', sans-serif; }
    </style>
</head>
<body class="bg-gradient-to-br from-pink-50 to-pink-100 flex items-center justify-center min-h-screen p-4">
    <div class="bg-white/80 backdrop-blur-md p-10 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-pink-100 w-full max-w-md transition-all">
        
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-500 to-rose-400 mb-2">Moda Masal 🌸</h1>
            <h2 class="text-lg text-gray-500 font-medium">Yönetim Paneli</h2>
        </div>
        
        <form action="/api/v1/admin/login" method="POST" class="space-y-6">
            <div>
                <label class="block text-gray-700 text-sm font-semibold mb-2" for="username">Kullanıcı Adı</label>
                <input class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-pink-400 focus:ring-2 focus:ring-pink-100 outline-none transition-all text-gray-700 bg-white/50" id="username" name="username" type="text" placeholder="admin" required>
            </div>
            
            <div>
                <label class="block text-gray-700 text-sm font-semibold mb-2" for="password">Şifre</label>
                <input class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-pink-400 focus:ring-2 focus:ring-pink-100 outline-none transition-all text-gray-700 bg-white/50" id="password" name="password" type="password" placeholder="••••••••" required>
            </div>
            
            <div class="pt-2">
                <button class="w-full bg-gradient-to-r from-pink-500 to-rose-400 hover:from-pink-600 hover:to-rose-500 text-white font-bold py-3 px-4 rounded-xl shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5 focus:outline-none focus:ring-4 focus:ring-pink-200" type="submit">
                    Giriş Yap
                </button>
            </div>
        </form>
        
        <div class="mt-8 text-center text-sm text-gray-400">
            <p>Admin erişimi yetkilendirilen hesaplarla sınırlıdır.</p>
        </div>
    </div>
</body>
</html>
"""

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(content=LOGIN_HTML)

@router.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    # Hata durumunda (yanlış şifre vb.)
    if not user or not auth_service.verify_password(password, user.hashed_password):
        return HTMLResponse(content="<script>alert('Hatalı kullanıcı adı veya şifre!'); window.location.href='/api/v1/admin/login';</script>", status_code=401)
    
    # Token oluştur ve Cookie'ye yerleştir (Aynı Alan adı güvenliği)
    access_token = auth_service.create_access_token(data={"sub": user.username, "role": user.role})
    response = RedirectResponse(url="/api/v1/admin/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=86400, samesite="lax")
    return response

@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/api/v1/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    try:
        get_current_user(request)
        return HTMLResponse(content=ADMIN_HTML)
    except HTTPException:
        return RedirectResponse(url="/api/v1/admin/login")

@router.get("/orders")
async def get_orders(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = OrderService(db)
    return await service.get_orders()

@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, status: OrderStatus, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = OrderService(db)
    updated_order = await service.update_status(order_id, status)
    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated_order

@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Total unique customers
    total_result = await db.execute(select(func.count(CustomerInteraction.id)))
    total_customers = total_result.scalar() or 0
    
    # WhatsApp
    wa_result = await db.execute(select(func.count(CustomerInteraction.id)).where(CustomerInteraction.platform == InteractionPlatform.WHATSAPP))
    wa_customers = wa_result.scalar() or 0
    
    # Instagram
    ig_result = await db.execute(select(func.count(CustomerInteraction.id)).where(CustomerInteraction.platform == InteractionPlatform.INSTAGRAM))
    ig_customers = ig_result.scalar() or 0
    
    return {
        "total_unique_customers": total_customers,
        "whatsapp_customers": wa_customers,
        "instagram_customers": ig_customers
    }
