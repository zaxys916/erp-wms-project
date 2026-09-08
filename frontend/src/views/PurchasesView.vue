<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  purchaseAPI,
  supplierAPI,
  productAPI,
  zoneAPI,
  extractError,
  type PurchaseOrder,
  type PurchaseOrderDetail,
  type Supplier,
  type Product,
  type Zone
} from '@/api'

interface ItemRow {
  product_id: number | null
  zone_id: number | null
  quantity: number
  unit_price: number
}

const loading = ref(false)
const rows = ref<PurchaseOrder[]>([])
const suppliers = ref<Supplier[]>([])
const products = ref<Product[]>([])
const zones = ref<Zone[]>([])

const dialogVisible = ref(false)
const detailVisible = ref(false)
const current = ref<PurchaseOrderDetail | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({ supplier_id: null as number | null, remark: '' })
const items = ref<ItemRow[]>([{ product_id: null, zone_id: null, quantity: 1, unit_price: 0 }])

const rules: FormRules = {
  supplier_id: [{ required: true, message: '请选择供应商', trigger: 'change' }]
}

const statusMap: Record<string, string> = {
  pending: '待审核',
  approved: '已审核',
  received: '已收货',
  cancelled: '已取消'
}
const statusType: Record<string, string> = {
  pending: 'warning',
  approved: 'primary',
  received: 'success',
  cancelled: 'info'
}

async function loadBase() {
  const [sup, prod, zone] = await Promise.all([supplierAPI.list(), productAPI.list(), zoneAPI.list()])
  suppliers.value = sup.data.items
  products.value = prod.data.items
  zones.value = zone.data.items
}

async function loadData() {
  loading.value = true
  try {
    const { data } = await purchaseAPI.list()
    rows.value = data.items
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

function supplierName(id: number) {
  return suppliers.value.find((s) => s.id === id)?.name ?? `#${id}`
}
function productName(id: number) {
  return products.value.find((p) => p.id === id)?.name ?? `#${id}`
}
function zoneName(id: number) {
  return zones.value.find((z) => z.id === id)?.zone_name ?? `#${id}`
}

function openCreate() {
  Object.assign(form, { supplier_id: null, remark: '' })
  items.value = [{ product_id: null, zone_id: null, quantity: 1, unit_price: 0 }]
  dialogVisible.value = true
}

function addItem() {
  items.value.push({ product_id: null, zone_id: null, quantity: 1, unit_price: 0 })
}
function removeItem(idx: number) {
  items.value.splice(idx, 1)
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  const payload = items.value.map((it) => ({
    product_id: it.product_id!,
    zone_id: it.zone_id!,
    quantity: it.quantity,
    unit_price: it.unit_price
  }))
  if (!payload.every((p) => p.product_id && p.zone_id)) {
    ElMessage.warning('请完整填写每行明细的产品与库位')
    return
  }
  try {
    await purchaseAPI.create({ supplier_id: form.supplier_id!, remark: form.remark, items: payload })
    ElMessage.success('采购订单已创建')
    dialogVisible.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

async function approve(row: PurchaseOrder) {
  try {
    await purchaseAPI.approve(row.id)
    ElMessage.success('采购订单已审核')
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

async function receive(row: PurchaseOrder) {
  try {
    await ElMessageBox.confirm(`确认对采购单「${row.order_no}」收货入库？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await purchaseAPI.receive(row.id)
    ElMessage.success('已收货并入账库存')
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

async function cancel(row: PurchaseOrder) {
  try {
    await purchaseAPI.cancel(row.id)
    ElMessage.success('采购订单已取消')
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

async function showDetail(row: PurchaseOrder) {
  try {
    current.value = await purchaseAPI.get(row.id).then((r) => r.data)
    detailVisible.value = true
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

const detailAmount = computed(() =>
  (current.value?.items ?? []).reduce((s, it) => s + Number(it.amount), 0)
)

onMounted(async () => {
  try {
    await loadBase()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
  await loadData()
})
</script>

<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>采购订单</span>
          <div class="header-actions">
            <el-button @click="loadData" :loading="loading">刷新</el-button>
            <el-button type="primary" @click="openCreate">新建采购订单</el-button>
          </div>
        </div>
      </template>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="order_no" label="订单号" min-width="160" />
        <el-table-column label="供应商" min-width="130">
          <template #default="{ row }">{{ supplierName(row.supplier_id) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType[row.status]">{{ statusMap[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="总金额" width="120">
          <template #default="{ row }">¥{{ Number(row.total_amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="showDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'pending'" size="small" @click="approve(row)">审核</el-button>
            <el-button v-if="row.status === 'approved'" size="small" type="success" @click="receive(row)">收货</el-button>
            <el-button v-if="row.status === 'pending'" size="small" type="danger" plain @click="cancel(row)">取消</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无采购订单" />
        </template>
      </el-table>
    </el-card>

    <!-- 新建采购订单 -->
    <el-dialog v-model="dialogVisible" title="新建采购订单" width="720px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="供应商" prop="supplier_id">
          <el-select v-model="form.supplier_id" placeholder="选择供应商" style="width: 100%">
            <el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" />
        </el-form-item>
      </el-form>
      <el-divider content-position="left">明细</el-divider>
      <div v-for="(it, idx) in items" :key="idx" class="item-row">
        <el-select v-model="it.product_id" placeholder="产品" style="flex: 2">
          <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-select v-model="it.zone_id" placeholder="库位" style="flex: 1.5">
          <el-option v-for="z in zones" :key="z.id" :label="z.zone_name" :value="z.id" />
        </el-select>
        <el-input-number v-model="it.quantity" :min="1" style="width: 110px" />
        <el-input-number v-model="it.unit_price" :min="0" :precision="2" style="width: 130px" />
        <el-button type="danger" text :disabled="items.length === 1" @click="removeItem(idx)">删</el-button>
      </div>
      <el-button style="margin-top: 8px" @click="addItem">添加明细</el-button>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">创建</el-button>
      </template>
    </el-dialog>

    <!-- 详情 -->
    <el-dialog v-model="detailVisible" title="采购订单明细" width="640px">
      <template v-if="current">
        <p class="detail-head">
          <strong>{{ current.order_no }}</strong>
          <el-tag :type="statusType[current.status]">{{ statusMap[current.status] }}</el-tag>
        </p>
        <el-table :data="current.items" border size="small">
          <el-table-column label="产品" min-width="140">
            <template #default="{ row }">{{ productName(row.product_id) }}</template>
          </el-table-column>
          <el-table-column label="库位" width="120">
            <template #default="{ row }">{{ zoneName(row.zone_id) }}</template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="90" />
          <el-table-column label="单价" width="110">
            <template #default="{ row }">¥{{ Number(row.unit_price).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="金额" width="120">
            <template #default="{ row }">¥{{ Number(row.amount).toFixed(2) }}</template>
          </el-table-column>
        </el-table>
        <p class="detail-total">合计：¥{{ detailAmount.toFixed(2) }}</p>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.item-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-total {
  text-align: right;
  font-weight: bold;
  margin-top: 8px;
}
</style>