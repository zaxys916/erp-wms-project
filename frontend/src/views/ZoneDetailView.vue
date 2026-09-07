<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  inventoryAPI,
  productAPI,
  zoneAPI,
  extractError,
  type Inventory,
  type Product,
  type Zone
} from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const zone = ref<Zone | null>(null)
const records = ref<Inventory[]>([])
const products = ref<Product[]>([])

const zoneId = computed(() => Number(route.params.id))

const zoneRecords = computed(() => records.value.filter((r) => r.zone_id === zoneId.value))
const used = computed(() => zoneRecords.value.reduce((s, r) => s + r.quantity, 0))
const rate = computed(() =>
  zone.value && zone.value.capacity > 0 ? Math.round((used.value / zone.value.capacity) * 100) : 0
)
const productName = (id: number) => products.value.find((p) => p.id === id)?.name ?? `#${id}`

async function loadData() {
  loading.value = true
  try {
    const [z, i, p] = await Promise.all([zoneAPI.get(zoneId.value), inventoryAPI.list(), productAPI.list()])
    zone.value = z.data
    records.value = i.data.items
    products.value = p.data.items
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div v-loading="loading">
    <el-page-header content="库位详情" @back="router.push('/zones')" class="header" />

    <el-descriptions :column="3" border v-if="zone">
      <el-descriptions-item label="库位名称">{{ zone.zone_name }}</el-descriptions-item>
      <el-descriptions-item label="容量">{{ zone.capacity }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="zone.status ? 'success' : 'danger'">{{ zone.status ? '启用' : '禁用' }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="已用">{{ used }}</el-descriptions-item>
      <el-descriptions-item label="剩余">{{ zone.capacity - used }}</el-descriptions-item>
      <el-descriptions-item label="占用率">{{ rate }}%</el-descriptions-item>
    </el-descriptions>

    <el-card shadow="never" class="mt">
      <template #header><span>存放产品</span></template>
      <el-table :data="zoneRecords" border stripe>
        <el-table-column label="产品" min-width="180">
          <template #default="{ row }">{{ productName(row.product_id) }}</template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="120" />
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">{{ row.last_updated ?? '-' }}</template>
        </el-table-column>
        <template #empty>
          <el-empty description="该库位暂无库存" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.header {
  margin-bottom: 16px;
}

.mt {
  margin-top: 16px;
}
</style>
