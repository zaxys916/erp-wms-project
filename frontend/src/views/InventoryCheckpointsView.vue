<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  productAPI,
  stocktakeAPI,
  zoneAPI,
  extractError,
  type Product,
  type Stocktake,
  type StocktakeItem,
  type Zone
} from '@/api'

const loading = ref(false)
const submitting = ref(false)
const saving = ref(false)
const list = ref<Stocktake[]>([])
const products = ref<Product[]>([])
const zones = ref<Zone[]>([])

// ---------- 新建盘点单 ----------
const createRef = ref<FormInstance>()
const createForm = reactive({ zone_id: null as number | null, remark: '' })
const createRules: FormRules = {
  zone_id: [{ required: false }]
}

const pendingCount = computed(() => list.value.filter((x) => x.status === 'pending').length)
const completedCount = computed(() => list.value.filter((x) => x.status === 'completed').length)

async function loadList() {
  loading.value = true
  try {
    const [s, p, z] = await Promise.all([stocktakeAPI.list(), productAPI.list(), zoneAPI.list()])
    list.value = s.data
    products.value = p.data
    zones.value = z.data
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

async function createStocktake() {
  submitting.value = true
  try {
    const { data } = await stocktakeAPI.create({
      zone_id: createForm.zone_id,
      remark: createForm.remark || undefined
    })
    ElMessage.success(`盘点单 ${data.order_no} 已创建，共 ${data.items.length} 条待盘点`)
    createForm.zone_id = null
    createForm.remark = ''
    // 创建后直接打开录入弹窗
    await loadList()
    await openDetail(data.id)
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    submitting.value = false
  }
}

// ---------- 盘点详情/录入 ----------
const detailVisible = ref(false)
const active = ref<{ id: number; order_no: string; zone_id: number | null; status: string; remark: string | null } | null>(null)
const activeItems = ref<StocktakeItem[]>([])

async function openDetail(id: number) {
  try {
    const { data } = await stocktakeAPI.detail(id)
    active.value = {
      id: data.id,
      order_no: data.order_no,
      zone_id: data.zone_id ?? null,
      status: data.status,
      remark: data.remark ?? null
    }
    activeItems.value = data.items.map((it) => ({
      ...it,
      actual_qty: it.actual_qty ?? it.book_qty
    }))
    detailVisible.value = true
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

/** 录入某个产品的实盘数量 */
async function saveItem(item: StocktakeItem) {
  if (item.actual_qty == null || item.actual_qty < 0) {
    ElMessage.warning('请输入有效的实盘数量')
    return
  }
  saving.value = true
  try {
    const { data } = await stocktakeAPI.updateItem(active.value!.id, item.id, item.actual_qty)
    const idx = activeItems.value.findIndex((x) => x.id === item.id)
    if (idx >= 0) activeItems.value[idx] = data
    ElMessage.success(`已保存 ${productName(item.product_id)} 的实盘数量`)
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    saving.value = false
  }
}

/** 完成盘点：后台自动调账并生成差异报告 */
async function finishStocktake() {
  if (!active.value) return
  try {
    await ElMessageBox.confirm(
      `确认完成盘点 ${active.value.order_no}？完成将按实盘数量调整库存并生成差异报告。`,
      '完成盘点',
      { type: 'warning' }
    )
    const { data } = await stocktakeAPI.complete(active.value!.id)
    ElMessageBox.alert(
      `盘点单 ${data.order_no} 已完成\n调整项：${data.adjusted_count} 项\n累计差异：${data.total_diff} 件`,
      '盘点完成',
      { confirmButtonText: '知道了' }
    )
    detailVisible.value = false
    await loadList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(extractError(e))
  }
}

const productName = (id: number) => products.value.find((p) => p.id === id)?.name ?? `#${id}`
const zoneName = (id: number | null) => {
  if (!id) return '全仓'
  return zones.value.find((z) => z.id === id)?.zone_name ?? `#${id}`
}
const statusTag: Record<string, string> = { pending: 'warning', completed: 'success' }
const statusText: Record<string, string> = { pending: '盘点中', completed: '已完成' }

onMounted(loadList)
</script>

<template>
  <div>
    <el-row :gutter="16" class="mb">
      <el-col :span="8">
        <el-card shadow="never">
          <el-statistic title="盘点中" :value="pendingCount" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-statistic title="已完成" :value="completedCount" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <el-statistic title="盘点单总数" :value="list.length" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="mb">
      <template #header><span>新建盘点单</span></template>
      <el-form ref="createRef" :model="createForm" :rules="createRules" inline>
        <el-form-item label="盘点库位">
          <el-select
            v-model="createForm.zone_id"
            placeholder="留空 = 全仓盘点"
            clearable
            style="width: 260px"
          >
            <el-option v-for="z in zones" :key="z.id" :label="z.zone_name" :value="z.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.remark" placeholder="选填" style="width: 200px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="createStocktake">创建并开始盘点</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>盘点单列表</span>
          <el-button @click="loadList" :loading="loading">刷新</el-button>
        </div>
      </template>
      <el-table :data="list" v-loading="loading" border stripe>
        <el-table-column prop="order_no" label="单号" min-width="190" />
        <el-table-column label="盘点范围" width="140">
          <template #default="{ row }">{{ zoneName(row.zone_id) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTag[row.status] as any" size="small">{{ statusText[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="175">
          <template #default="{ row }">{{ row.created_at ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openDetail(row.id)">
              {{ row.status === 'pending' ? '继续盘点' : '查看' }}
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无盘点单，请先新建" />
        </template>
      </el-table>
    </el-card>

    <!-- 盘点录入弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="`盘点录入：${active?.order_no ?? ''}`"
      width="720px"
      destroy-on-close
    >
      <el-alert
        v-if="active?.status === 'pending'"
        type="info"
        :closable="false"
        show-icon
        title="录入每个产品的实盘数量后点「保存」，全部录完点「完成盘点」自动调账并生成差异报告。"
        class="mb"
      />
      <el-table :data="activeItems" border stripe max-height="420">
        <el-table-column label="产品" min-width="150">
          <template #default="{ row }">{{ productName(row.product_id) }}</template>
        </el-table-column>
        <el-table-column label="库位" width="130">
          <template #default="{ row }">{{ zoneName(row.zone_id) }}</template>
        </el-table-column>
        <el-table-column prop="book_qty" label="账面数量" width="100" />
        <el-table-column label="实盘数量" width="190">
          <template #default="{ row }">
            <el-input-number
              v-if="active?.status === 'pending'"
              v-model="row.actual_qty"
              :min="0"
              size="small"
              controls-position="right"
            />
            <span v-else>{{ row.actual_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column label="差异" width="90">
          <template #default="{ row }">
            <el-text :type="row.diff > 0 ? 'danger' : row.diff < 0 ? 'success' : 'info'">
              {{ row.diff > 0 ? `+${row.diff}` : row.diff }}
            </el-text>
          </template>
        </el-table-column>
        <el-table-column v-if="active?.status === 'pending'" label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" :loading="saving" @click="saveItem(row)">保存</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无盘点明细" />
        </template>
      </el-table>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button v-if="active?.status === 'pending'" type="success" @click="finishStocktake">
          完成盘点
        </el-button>
      </template>
    </el-dialog>
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
