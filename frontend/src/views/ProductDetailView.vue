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
const product = ref<Product | null>(null)
const records = ref<Inventory[]>([])
const zones = ref<Zone[]>([])

const productId = computed(() => Number(route.params.id))
const productRecords = computed(() => records.value.filter((r) => r.product_id === productId.value))
const totalQty = computed(() => productRecords.value.reduce((s, r) => s + r.quantity, 0))
const zoneName = (id: number) => zones.value.find((z) => z.id === id)?.zone_name ?? `#${id}`

async function loadData() {
  loading.value = true
  try {
    const [p, i, z] = await Promise.all([productAPI.get(productId.value), inventoryAPI.list(), zoneAPI.list()])
    product.value = p.data
    records.value = i.data.items
    zones.value = z.data.items
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
    <el-page-header content="产品详情" @back="router.push('/products')" class="header" />

    <el-descriptions :column="3" border v-if="product">
      <el-descriptions-item label="产品名称">{{ product.name }}</el-descriptions-item>
      <el-descriptions-item label="SKU">{{ product.sku ?? '-' }}</el-descriptions-item>
      <el-descriptions-item label="当前总库存">
        <el-text type="primary">{{ totalQty }}</el-text>
      </el-descriptions-item>
      <el-descriptions-item label="分布库位数">{{ productRecords.length }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ product.created_at ?? '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-card shadow="never">
      <template #header><span>库存分布</span></template>
      <el-table :data="productRecords" border stripe>
        <el-table-column label="库位" min-width="160">
          <template #default="{ row }">{{ zoneName(row.zone_id) }}</template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="120" />
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">{{ row.last_updated ?? '-' }}</template>
        </el-table-column>
        <template #empty>
          <el-empty description="该产品暂无库位库存记录" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.header {
  margin-bottom: 16px;
}

.mb {
  margin-bottom: 16px;
}
</style>
