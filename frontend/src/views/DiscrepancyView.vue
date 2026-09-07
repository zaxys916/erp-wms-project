<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  productAPI,
  stocktakeAPI,
  zoneAPI,
  extractError,
  type Discrepancy,
  type Product,
  type Zone
} from '@/api'

const loading = ref(false)
const rows = ref<Discrepancy[]>([])
const products = ref<Product[]>([])
const zones = ref<Zone[]>([])

const openCount = computed(() => rows.value.filter((r) => r.status === 'open').length)
const totalDiff = computed(() => rows.value.reduce((s, r) => s + (r.difference ?? 0), 0))

async function loadData() {
  loading.value = true
  try {
    const [d, p, z] = await Promise.all([
      stocktakeAPI.discrepancies(),
      productAPI.list(),
      zoneAPI.list()
    ])
    rows.value = d.data.items
    products.value = p.data.items
    zones.value = z.data.items
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

const productName = (id: number) => products.value.find((p) => p.id === id)?.name ?? `#${id}`
const zoneName = (id: number | null | undefined) => {
  if (!id) return '-'
  return zones.value.find((z) => z.id === id)?.zone_name ?? `#${id}`
}

onMounted(loadData)
</script>

<template>
  <div>
    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="差异报告"
      description="盘点单完成后，实盘与账面不一致的记录会自动进入本报告；差异已按实盘数量调整库存并写入 adjust 流水。"
      class="mb"
    />

    <el-row :gutter="16" class="mb">
      <el-col :span="8">
        <el-card shadow="never">
          <el-statistic title="差异记录数" :value="rows.length" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-statistic title="待关注（open）" :value="openCount" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-statistic title="累计差异量" :value="totalDiff" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>盘点差异明细</span>
          <el-button @click="loadData" :loading="loading">刷新</el-button>
        </div>
      </template>
      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column label="产品" min-width="150">
          <template #default="{ row }">{{ productName(row.product_id) }}</template>
        </el-table-column>
        <el-table-column label="库位" width="130">
          <template #default="{ row }">{{ zoneName(row.zone_id) }}</template>
        </el-table-column>
        <el-table-column prop="book_qty" label="账面数量" width="100" />
        <el-table-column prop="actual_qty" label="实盘数量" width="100" />
        <el-table-column label="差异" width="100">
          <template #default="{ row }">
            <el-text :type="row.difference > 0 ? 'danger' : row.difference < 0 ? 'success' : 'info'">
              {{ row.difference > 0 ? `+${row.difference}` : row.difference }}
            </el-text>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'open' ? 'danger' : 'success'" size="small">
              {{ row.status === 'open' ? '待关注' : '已处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="产生时间" width="180">
          <template #default="{ row }">{{ row.created_at ?? '-' }}</template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无差异记录，盘点完成后差异会自动显示在这里" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.mb {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
