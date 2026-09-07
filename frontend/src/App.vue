<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/api'

const router = useRouter()
const route = useRoute()

const username = ref(localStorage.getItem('username') || '')
const role = ref('')

interface MenuItem {
  path: string
  title: string
  icon: string
  /** 可见角色；缺省表示所有登录用户可见 */
  roles?: string[]
}

const menuItems: MenuItem[] = [
  { path: '/', title: '首页', icon: 'House' },
  { path: '/zones', title: '仓库与库位', icon: 'Location', roles: ['admin', 'operator'] },
  { path: '/products', title: '产品管理', icon: 'Goods', roles: ['admin', 'operator'] },
  { path: '/inventory/inbound', title: '入库管理', icon: 'Download', roles: ['admin', 'operator'] },
  { path: '/inventory/outbound', title: '出库管理', icon: 'Upload', roles: ['admin', 'operator'] },
  { path: '/inventory/checkpoints', title: '库存盘点', icon: 'Finished', roles: ['admin', 'operator'] },
  { path: '/inventory/discrepancies', title: '差异报告', icon: 'Warning', roles: ['admin', 'operator'] },
  { path: '/users', title: '用户管理', icon: 'User', roles: ['admin'] },
  { path: '/about', title: '关于', icon: 'InfoFilled' }
]

const isLoginPage = computed(() => route.path === '/login')
const pageTitle = computed(
  () => menuItems.find((m) => m.path === route.path)?.title || 'ERP-WMS 系统'
)

/** 按当前用户角色过滤侧边菜单 */
const visibleMenus = computed(() =>
  menuItems.filter((m) => !m.roles || m.roles.includes(role.value || 'user'))
)

onMounted(async () => {
  try {
    const { data } = await authAPI.me()
    role.value = data.role || ''
    username.value = data.username || username.value
  } catch {
    // 认证失败由拦截器统一跳登录页
  }
})

function handleLogout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('username')
  username.value = ''
  role.value = ''
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <!-- 登录页使用独立简洁布局 -->
  <div v-if="isLoginPage" class="login-layout">
    <router-view />
  </div>

  <el-container v-else class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="aside">
      <div class="logo">
        <span class="logo-text">ERP-WMS</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        class="menu"
      >
        <el-menu-item
          v-for="item in visibleMenus"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <span class="page-title">{{ pageTitle }}</span>
        <div class="header-right">
          <el-icon><User /></el-icon>
          <span class="username">{{ username || '未登录' }}</span>
          <el-button text type="primary" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-container {
  height: 100vh;
}

.login-layout {
  min-height: 100vh;
  background: linear-gradient(135deg, #001529 0%, #0a2540 55%, #145388 100%);
  padding: 40px 20px;
  box-sizing: border-box;
}

.aside {
  background-color: #001529;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #002140;
}

.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  letter-spacing: 2px;
}

.menu {
  border-right: none;
  flex: 1;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
}

.username {
  font-size: 14px;
}

.main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
