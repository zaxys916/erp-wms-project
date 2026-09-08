<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { reportAPI, extractError, type StockAlert } from '@/api'

const loading = ref(false)
const rows = ref<StockAlert[]>([])

async function loadData() {
  loading.value = true
  try {
    const { data } = await reportAPI.stockAlerts()
    rows.value = data
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>安全库存预警</span>
          <el-button @click="loadData" :loading="loading">刷新</el-button>
        </div>
      </template>
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="以下产品的当前库存总量低于其安全库存阈值，需要及时补货"
        style="margin-bottom: 16px"
      />
      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="product_id" label="产品ID" width="90" />
        <el-table-column prop="name" label="产品名称" min-width="160" />
        <el-table-column prop="sku" label="SKU" width="140" />
        <el-table-column prop="total_qty" label="当前库存" width="110" />
        <el-table-column prop="safety_stock" label="安全库存" width="110" />
        <el-table-column label="缺口" min-width="120">
          <template #default="{ row }">
            <el-tag type="danger">{{ row.deficit }}</el-tag>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无库存预警，库存健康" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>