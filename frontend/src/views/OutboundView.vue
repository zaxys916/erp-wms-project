<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  inventoryAPI,
  productAPI,
  stockOrderAPI,
  zoneAPI,
  extractError,
  type Inventory,
  type Product,
  type StockOrder,
  type Zone
} from '@/api'

const loading = ref(false)
const submitting = ref(false)
const products = ref<Product[]>([])
const zones = ref<Zone[]>([])
const orders = ref<StockOrder[]>([])
const inventoryRows = ref<Inventory[]>([])

const formRef = ref<FormInstance>()
const form = reactive({
  product_id: null as number | null,
  zone_id: null as number | null,
  quantity: 1,
  remark: ''
})

const rules: FormRules = {
  product_id: [{ required: true, message: '请选择产品', trigger: 'change' }],
  zone_id: [{ required: true, message: '请选择库位', trigger: 'change' }],
  quantity: [{ required: true, type: 'number', min: 1, message: '数量须大于 0', trigger: 'blur' }]
}

const statusTag: Record<string, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  cancelled: 'info'
}
const statusText: Record<string, string> = {
  pending: '待审核',
  approved: '已审核',
  rejected: '已驳回',
  cancelled: '已取消'
}

async function loadData() {
  loading.value = true
  try {
    const [p, z, o, i] = await Promise.all([
      productAPI.list(),
      zoneAPI.list(),
      stockOrderAPI.list(),
      inventoryAPI.list()
    ])
    products.value = p.data.items
    zones.value = z.data.items
    orders.value = o.data.items.filter((x) => x.order_type === 'out')
    inventoryRows.value = i.data.items
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

/** 创建出库单（待审核） */
async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await stockOrderAPI.create({
      order_type: 'out',
      product_id: form.product_id!,
      zone_id: form.zone_id!,
      quantity: form.quantity,
      remark: form.remark || undefined
    })
    ElMessage.success('出库单已创建，待审核')
    formRef.value?.resetFields()
    form.quantity = 1
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    submitting.value = false
  }
}

/** 审核通过（库存才真正扣减并写入流水） */
async function approve(row: StockOrder) {
  try {
    await ElMessageBox.confirm(`确认审核通过出库单 ${row.order_no}？审核后库存将扣减 ${row.quantity}。`, '审核出库单', {
      type: 'warning'
    })
    await stockOrderAPI.approve(row.id)
    ElMessage.success('已审核通过，库存已更新')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(extractError(e))
  }
}

async function reject(row: StockOrder) {
  try {
    await ElMessageBox.confirm(`确认驳回出库单 ${row.order_no}？`, '驳回出库单', { type: 'warning' })
    await stockOrderAPI.reject(row.id)
    ElMessage.success('已驳回')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(extractError(e))
  }
}

async function cancelOrder(row: StockOrder) {
  try {
    await ElMessageBox.confirm(`确认取消出库单 ${row.order_no}？`, '取消出库单', { type: 'warning' })
    await stockOrderAPI.cancel(row.id)
    ElMessage.success('已取消')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(extractError(e))
  }
}

const productName = (id: number) => products.value.find((p) => p.id === id)?.name ?? `#${id}`
const zoneName = (id: number) => zones.value.find((z) => z.id === id)?.zone_name ?? `#${id}`

onMounted(loadData)
</script>

<template>
  <div>
    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="出库流程：创建出库单 → 审核通过后库存自动扣减，并记录库存流水；库存不足时审核会失败。"
      class="mb"
    />

    <el-card shadow="never" class="mb">
      <template #header><span>创建出库单</span></template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" style="max-width: 560px">
        <el-form-item label="产品" prop="product_id">
          <el-select v-model="form.product_id" placeholder="请选择产品" style="width: 100%">
            <el-option v-for="p in products" :key="p.id" :label="`${p.name}（${p.sku}）`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="出库库位" prop="zone_id">
          <el-select v-model="form.zone_id" placeholder="请选择库位" style="width: 100%">
            <el-option v-for="z in zones" :key="z.id" :label="z.zone_name" :value="z.id" :disabled="!z.status" />
          </el-select>
        </el-form-item>
        <el-form-item label="出库数量" prop="quantity">
          <el-input-number v-model="form.quantity" :min="1" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" placeholder="选填" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="danger" plain :loading="submitting" @click="submit">提交出库单</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="mb">
      <template #header>
        <div class="card-header">
          <span>出库单列表</span>
          <el-button @click="loadData" :loading="loading">刷新</el-button>
        </div>
      </template>
      <el-table :data="orders" v-loading="loading" border stripe>
        <el-table-column prop="order_no" label="单号" min-width="180" />
        <el-table-column label="产品" min-width="140">
          <template #default="{ row }">{{ productName(row.product_id) }}</template>
        </el-table-column>
        <el-table-column label="库位" min-width="120">
          <template #default="{ row }">{{ zoneName(row.zone_id) }}</template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="90" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag[row.status] as any" size="small">{{ statusText[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ row.created_at ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button size="small" type="success" @click="approve(row)">审核通过</el-button>
              <el-button size="small" type="warning" @click="reject(row)">驳回</el-button>
              <el-button size="small" type="info" @click="cancelOrder(row)">取消</el-button>
            </template>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无出库单" />
        </template>
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header><span>当前库存</span></template>
      <el-table :data="inventoryRows" border stripe size="small">
        <el-table-column label="产品" min-width="160">
          <template #default="{ row }">{{ productName(row.product_id) }}</template>
        </el-table-column>
        <el-table-column label="库位" min-width="140">
          <template #default="{ row }">{{ zoneName(row.zone_id) }}</template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="110" />
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">{{ row.last_updated ?? '-' }}</template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无库存数据" />
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

.muted {
  color: #c0c4cc;
}
</style>
