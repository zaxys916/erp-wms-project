<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { inventoryAPI, extractError } from '@/api'

const router = useRouter()

const stats = ref({ total_records: 0, total_quantity: 0, last_updated: null as string | null })
const loading = ref(false)

const shortcuts = [
  { title: '仓库与库位', desc: '管理库位容量与启用状态', path: '/zones', icon: 'Location', color: '#409eff' },
  { title: '产品管理', desc: '维护 SKU 与产品档案', path: '/products', icon: 'Goods', color: '#67c23a' },
  { title: '库存查询', desc: '查看各库位实时库存', path: '/inventory/checkpoints', icon: 'Box', color: '#e6a23c' },
  { title: '用户管理', desc: '分配角色与访问权限', path: '/users', icon: 'User', color: '#f56c6c' },
  { title: '采购订单', desc: '采购下单、审核与收货', path: '/purchases', icon: 'ShoppingCart', color: '#409eff' },
  { title: '销售订单', desc: '销售下单、审核与发货', path: '/sales', icon: 'Sell', color: '#67c23a' },
  { title: '供应商档案', desc: '管理供应商信息', path: '/suppliers', icon: 'OfficeBuilding', color: '#e6a23c' },
  { title: '客户档案', desc: '管理客户信息', path: '/customers', icon: 'UserFilled', color: '#f56c6c' },
  { title: '报表统计', desc: '库存、出入库与订单统计', path: '/reports', icon: 'DataAnalysis', color: '#409eff' },
  { title: '库存预警', desc: '低于安全库存的产品清单', path: '/inventory/alerts', icon: 'Warning', color: '#f56c6c' }
]

async function loadStats() {
  loading.value = true
  try {
    const { data } = await inventoryAPI.status()
    stats.value = data
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>

<template>
  <div class="home">
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="hover" v-loading="loading">
          <el-statistic title="库存记录数" :value="stats.total_records" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" v-loading="loading">
          <el-statistic title="库存总数量" :value="stats.total_quantity" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-title">最近更新</div>
          <div class="stat-value">{{ stats.last_updated ?? '--' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="shortcuts">
      <el-col :span="6" v-for="s in shortcuts" :key="s.path">
        <el-card shadow="hover" class="shortcut-card" @click="router.push(s.path)">
          <el-icon :size="28" :color="s.color"><component :is="s.icon" /></el-icon>
          <div class="shortcut-title">{{ s.title }}</div>
          <div class="shortcut-desc">{{ s.desc }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
}

.shortcuts {
  margin-top: 16px;
}

.shortcut-card {
  cursor: pointer;
  text-align: center;
  transition: transform 0.2s;
}

.shortcut-card:hover {
  transform: translateY(-4px);
}

.shortcut-title {
  margin-top: 12px;
  font-size: 16px;
  font-weight: 500;
}

.shortcut-desc {
  margin-top: 6px;
  font-size: 13px;
  color: #909399;
}
</style>
