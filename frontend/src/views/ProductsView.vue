<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { inventoryAPI, productAPI, extractError, type Inventory, type Product } from '@/api'

const loading = ref(false)
const products = ref<Product[]>([])
const inventoryRows = ref<Inventory[]>([])
const keyword = ref('')

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({ name: '', sku: '' })

const rules: FormRules = {
  name: [{ required: true, min: 3, message: '产品名称至少 3 个字符', trigger: 'blur' }],
  sku: [{ required: true, pattern: /^[A-Z0-9]{8}$/, message: 'SKU 须为 8 位大写字母或数字', trigger: 'blur' }]
}

/** 产品库存总量 = inventory 台账按产品聚合（唯一数据来源） */
const qtyByProduct = computed(() => {
  const map = new Map<number, number>()
  for (const r of inventoryRows.value) {
    map.set(r.product_id, (map.get(r.product_id) ?? 0) + r.quantity)
  }
  return map
})
const stockOf = (productId: number) => qtyByProduct.value.get(productId) ?? 0

async function loadData() {
  loading.value = true
  try {
    const [p, i] = await Promise.all([productAPI.list(), inventoryAPI.list()])
    products.value = p.data.items
    inventoryRows.value = i.data.items
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  const k = keyword.value.trim().toLowerCase()
  if (!k) return products.value
  return products.value.filter(
    (p) => p.name.toLowerCase().includes(k) || (p.sku ?? '').toLowerCase().includes(k)
  )
})

function openCreate() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { name: '', sku: '' })
  dialogVisible.value = true
}

function openEdit(row: Product) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, { name: row.name, sku: row.sku ?? '' })
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  try {
    if (isEdit.value && editingId.value != null) {
      await productAPI.update(editingId.value, { name: form.name, sku: form.sku })
      ElMessage.success('产品已更新')
    } else {
      await productAPI.create({ name: form.name, sku: form.sku })
      ElMessage.success('产品已创建')
    }
    dialogVisible.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

async function remove(row: Product) {
  try {
    await ElMessageBox.confirm(`确认删除产品「${row.name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await productAPI.remove(row.id)
    ElMessage.success('产品已删除')
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>产品列表</span>
          <div class="header-actions">
            <el-input
              v-model="keyword"
              placeholder="搜索名称 / SKU"
              clearable
              style="width: 200px"
            />
            <el-button @click="loadData" :loading="loading">刷新</el-button>
            <el-button type="primary" @click="openCreate">新增产品</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filtered" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="产品名称" min-width="160" />
        <el-table-column prop="sku" label="SKU" width="140" />
        <el-table-column label="库存总量" width="110">
          <template #default="{ row }">{{ stockOf(row.id) }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ row.created_at ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无产品数据" />
        </template>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑产品' : '新增产品'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="产品名称" prop="name">
          <el-input v-model="form.name" placeholder="至少 3 个字符" />
        </el-form-item>
        <el-form-item label="SKU" prop="sku">
          <el-input v-model="form.sku" placeholder="8 位大写字母或数字，如 TEST0001" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
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
</style>
