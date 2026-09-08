<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { reportAPI, extractError, type InventorySummary, type OrderStat } from '@/api'

const loading = ref(false)
const summary = ref<InventorySummary | null>(null)
const trend = ref<{ date: string; in_qty: number; out_qty: number }[]>([])
const orderStats = ref<{ purchase: OrderStat[]; sale: OrderStat[] } | null>(null)

async function loadData() {
  loading.value = true
  try {
    const [s, t, o] = await Promise.all([
      reportAPI.inventorySummary(),
      reportAPI.movementTrend(30),
      reportAPI.orderStats()
    ])
    summary.value = s.data
    trend.value = t.data
    orderStats.value = o.data
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

function statLabel(key: string) {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已审核',
    received: '已收货',
    shipped: '已发货',
    cancelled: '已取消'
  }
  return map[key] ?? key
}

function totalAmount(list: OrderStat[] | undefined) {
  return list?.reduce((s, x) => s + Number(x.amount), 0) ?? 0
}

function maxQty() {
  return Math.max(1, ...trend.value.map((t) => Math.max(t.in_qty, t.out_qty)))
}

onMounted(loadData)
</script>

<template>
  <div class="page" v-loading="loading">
    <!-- 库存汇总 -->
    <el-row :gutter="16" v-if="summary">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-num">{{ summary.total_quantity }}</div>
          <div class="stat-label">库存总数量</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-num">{{ summary.product_count }}</div>
          <div class="stat-label">产品种类</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-num">¥{{ summary.inventory_value.toFixed(2) }}</div>
          <div class="stat-label">库存总价值（按成本价）</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-num">{{ summary.total_records }}</div>
          <div class="stat-label">库位台账记录数</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 出入库趋势 -->
    <el-card shadow="never" class="block">
      <template #header>
        <div class="card-header">
          <span>近 30 天出入库趋势</span>
          <el-button @click="loadData" :loading="loading">刷新</el-button>
        </div>
      </template>
      <el-empty v-if="!trend.length" description="暂无出入库流水" />
      <el-table v-else :data="trend" border size="small">
        <el-table-column prop="date" label="日期" min-width="120" />
        <el-table-column label="入库数量" min-width="180">
          <template #default="{ row }">
            <div class="bar-row">
              <span>{{ row.in_qty }}</span>
              <div class="bar"><div class="bar-in" :style="{ width: ((Number(row.in_qty) / maxQty()) * 100) + '%' }"></div></div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="出库数量" min-width="180">
          <template #default="{ row }">
            <div class="bar-row">
              <span>{{ row.out_qty }}</span>
              <div class="bar"><div class="bar-out" :style="{ width: ((Number(row.out_qty) / maxQty()) * 100) + '%' }"></div></div>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 订单统计 -->
    <el-row :gutter="16" class="block">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>采购订单统计</span></template>
          <el-table :data="orderStats?.purchase ?? []" border size="small">
            <el-table-column label="状态" width="120">
              <template #default="{ row }">{{ statLabel(row.status) }}</template>
            </el-table-column>
            <el-table-column prop="count" label="订单数" width="100" />
            <el-table-column label="金额合计">
              <template #default="{ row }">¥{{ Number(row.amount).toFixed(2) }}</template>
            </el-table-column>
          </el-table>
          <p class="total">采购总额：¥{{ totalAmount(orderStats?.purchase).toFixed(2) }}</p>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><span>销售订单统计</span></template>
          <el-table :data="orderStats?.sale ?? []" border size="small">
            <el-table-column label="状态" width="120">
              <template #default="{ row }">{{ statLabel(row.status) }}</template>
            </el-table-column>
            <el-table-column prop="count" label="订单数" width="100" />
            <el-table-column label="金额合计">
              <template #default="{ row }">¥{{ Number(row.amount).toFixed(2) }}</template>
            </el-table-column>
          </el-table>
          <p class="total">销售总额：¥{{ totalAmount(orderStats?.sale).toFixed(2) }}</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stat-card {
  text-align: center;
  padding: 12px 0;
}

.stat-num {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  color: #909399;
  margin-top: 6px;
}

.block {
  margin-top: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bar {
  flex: 1;
  height: 14px;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
}

.bar-in {
  height: 100%;
  background: #67c23a;
}

.bar-out {
  height: 100%;
  background: #e6a23c;
}

.total {
  text-align: right;
  font-weight: bold;
  margin-top: 8px;
}
</style>