from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.order_service import OrderService
from app.db.models import Order, OrderStatus
from typing import List

router = APIRouter()

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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
</head>
<body class="bg-gray-100 font-sans text-sm">
    <div id="app" class="container mx-auto p-4">
        <header class="mb-6 flex justify-between items-center bg-white p-4 rounded shadow">
            <h1 class="text-2xl font-bold text-gray-800 flex items-center gap-2">
                🛍️ ModaMasal Yönetim Paneli
            </h1>
            <div class="flex gap-2">
                <button @click="fetchOrders" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition">
                    <i class="fas fa-sync-alt mr-1"></i> Yenile
                </button>
            </div>
        </header>

        <div class="bg-white rounded-lg shadow overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Durum</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tarih</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ödeme</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Müşteri</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Detaylar (Adres/Ürün)</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Onay</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="order in orders" :key="order.id" class="hover:bg-gray-50 transition">
                        <!-- Status Badge -->
                        <td class="px-4 py-4 whitespace-nowrap">
                            <span :class="statusClass(order.status)" class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full">
                                {{ order.status }}
                            </span>
                        </td>
                        
                        <!-- Date -->
                        <td class="px-4 py-4 whitespace-nowrap text-gray-500">
                            {{ formatDate(order.created_at) }}
                        </td>

                        <!-- Payment Method -->
                        <td class="px-4 py-4 whitespace-nowrap">
                            <span class="text-gray-700 font-medium">{{ order.payment_method }}</span>
                             <div v-if="order.payment_method === 'Kapıda Ödeme'" class="text-xs text-orange-600 font-bold mt-1">
                                ⚠️ Manuel Onay
                            </div>
                        </td>

                        <!-- Customer Info -->
                        <td class="px-4 py-4">
                            <div class="text-sm font-medium text-gray-900">{{ order.first_name }} {{ order.last_name }}</div>
                            <div class="text-sm text-gray-500">
                                <i class="fas fa-phone text-xs mr-1"></i>{{ order.phone }}
                            </div>
                            <div v-if="order.email" class="text-sm text-gray-500">
                                <i class="fas fa-envelope text-xs mr-1"></i>{{ order.email }}
                            </div>
                        </td>

                        <!-- Details (Address & Product) -->
                        <td class="px-4 py-4">
                            <div class="mb-2">
                                <span class="text-xs font-bold text-gray-500 uppercase">Ürün:</span>
                                <span class="text-gray-800">{{ order.product_summary }}</span>
                            </div>
                            <div>
                                <span class="text-xs font-bold text-gray-500 uppercase">Adres:</span>
                                <span class="text-gray-600 text-xs block mt-1 leading-tight">
                                    {{ order.address }} <br>
                                    <span class="font-bold text-gray-700">{{ order.city }} / Türkiye</span>
                                </span>
                            </div>
                        </td>

                        <!-- Actions (Tick / Cross) -->
                        <td class="px-4 py-4 whitespace-nowrap text-sm font-medium">
                            <div class="flex items-center gap-2">
                                <button title="Onayla / Gönderildi" @click="updateStatus(order.id, 'Gönderildi/Kargolandı')" 
                                        class="text-green-600 hover:text-green-900 bg-green-100 hover:bg-green-200 p-2 rounded-full transition">
                                    <i class="fas fa-check"></i>
                                </button>
                                <button title="İptal Et" @click="updateStatus(order.id, 'İptal Edildi')" 
                                        class="text-red-600 hover:text-red-900 bg-red-100 hover:bg-red-200 p-2 rounded-full transition">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                            <div v-if="order.shopify_invoice_url" class="mt-2">
                                <a :href="order.shopify_invoice_url" target="_blank" class="text-blue-600 hover:underline text-xs">
                                     Ödeme Linki ↗
                                </a>
                            </div>
                        </td>
                    </tr>
                     <tr v-if="orders.length === 0">
                        <td colspan="6" class="text-center py-10 text-gray-500">
                            <i class="fas fa-inbox text-4xl mb-3 block text-gray-300"></i>
                            Henüz sipariş bulunmamaktadır.
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const { createApp } = Vue

        createApp({
            data() {
                return {
                    orders: []
                }
            },
            methods: {
                async fetchOrders() {
                    try {
                        const response = await axios.get('/api/v1/admin/orders');
                        this.orders = response.data;
                    } catch (error) {
                        alert('Siparişler çekilemedi!');
                        console.error(error);
                    }
                },
                formatDate(dateString) {
                    if (!dateString) return '';
                    const date = new Date(dateString);
                    return date.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' }) + ' ' + 
                           date.toLocaleTimeString('tr-TR', {hour: '2-digit', minute:'2-digit'});
                },
                statusClass(status) {
                    const map = {
                        'Beklemede': 'bg-yellow-100 text-yellow-800 border border-yellow-200',
                        'Gönderildi/Kargolandı': 'bg-green-100 text-green-800 border border-green-200',
                        'Tamamlandı': 'bg-blue-100 text-blue-800 border border-blue-200',
                        'İptal Edildi': 'bg-red-100 text-red-800 border border-red-200'
                    };
                    return map[status] || 'bg-gray-100 text-gray-800';
                },
                async updateStatus(id, newStatus) {
                    if(!confirm(`Bu siparişi '${newStatus}' olarak işaretlemek istediğinize emin misiniz?`)) return;
                    
                    try {
                        await axios.put(`/api/v1/admin/orders/${id}/status?status=${newStatus}`);
                        // Update local state
                        const order = this.orders.find(o => o.id === id);
                        if(order) order.status = newStatus;
                    } catch (error) {
                        alert('Güncelleme başarısız!');
                    }
                }
            },
            mounted() {
                this.fetchOrders();
                // Auto refresh every 30s
                setInterval(this.fetchOrders, 30000);
            }
        }).mount('#app')
    </script>
</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    return HTMLResponse(content=ADMIN_HTML)

@router.get("/orders")
async def get_orders(db: AsyncSession = Depends(get_db)):
    service = OrderService(db)
    return await service.get_orders()

@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, status: OrderStatus, db: AsyncSession = Depends(get_db)):
    service = OrderService(db)
    updated_order = await service.update_status(order_id, status)
    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated_order
