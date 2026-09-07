import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import AboutView from '@/views/AboutView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView
    },
    // 仓库与库位管理
    {
      path: '/zones',
      name: 'zones',
      component: () => import('@/views/ZonesView.vue')
    },
    {
      path: '/zones/:id',
      name: 'zone-detail',
      component: () => import('@/views/ZoneDetailView.vue')
    },
    // 产品管理
    {
      path: '/products',
      name: 'products',
      component: () => import('@/views/ProductsView.vue')
    },
    {
      path: '/products/:id',
      name: 'product-detail',
      component: () => import('@/views/ProductDetailView.vue')
    },
    // 入库与出库
    {
      path: '/inventory/inbound',
      name: 'inbound',
      component: () => import('@/views/InboundView.vue')
    },
    {
      path: '/inventory/outbound',
      name: 'outbound',
      component: () => import('@/views/OutboundView.vue')
    },
    // 库存盘点
    {
      path: '/inventory/checkpoints',
      name: 'checkpoints',
      component: () => import('@/views/InventoryCheckpointsView.vue')
    },
    {
      path: '/inventory/discrepancies',
      name: 'discrepancies',
      component: () => import('@/views/DiscrepancyView.vue')
    },
    // 用户管理
    {
      path: '/users',
      name: 'users',
      component: () => import('@/views/UsersView.vue')
    },
    {
      path: '/users/:id',
      name: 'user-detail',
      component: () => import('@/views/UserDetailView.vue')
    }
  ]
})

// 全局登录守卫：除 /login 外均需携带 token，否则跳转登录页
router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  const isPublic = to.meta.public === true
  if (!isPublic && !token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (isPublic && token) {
    return { path: '/' }
  }
  return true
})

export default router
