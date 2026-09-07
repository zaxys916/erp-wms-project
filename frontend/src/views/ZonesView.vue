<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  warehouseAPI,
  zoneAPI,
  extractError,
  type Warehouse,
  type Zone
} from '@/api'

const loading = ref(false)
const zones = ref<Zone[]>([])
const warehouses = ref<Warehouse[]>([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  zone_name: '',
  capacity: 0,
  status: true,
  warehouse_id: null as number | null
})

const rules: FormRules = {
  zone_name: [{ required: true, message: '请输入库位名称', trigger: 'blur' }],
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    const [zoneRes, whRes] = await Promise.all([zoneAPI.list(), warehouseAPI.list()])
    zones.value = zoneRes.data
    warehouses.value = whRes.data
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

function warehouseName(id?: number | null) {
  if (id == null) return '-'
  return warehouses.value.find((w) => w.id === id)?.name ?? `#${id}`
}

function openCreate() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { zone_name: '', capacity: 0, status: true, warehouse_id: null })
  dialogVisible.value = true
}

function openEdit(row: Zone) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    zone_name: row.zone_name,
    capacity: row.capacity,
    status: row.status,
    warehouse_id: row.warehouse_id
  })
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (isEdit.value && editingId.value != null) {
      await zoneAPI.update(editingId.value, { ...form })
      ElMessage.success('库位已更新')
    } else {
      await zoneAPI.create({ ...form })
      ElMessage.success('库位已创建')
    }
    dialogVisible.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

async function toggleStatus(row: Zone) {
  try {
    if (row.status) {
      await zoneAPI.disable(row.id)
      ElMessage.success(`库位 ${row.zone_name} 已禁用`)
    } else {
      await zoneAPI.enable(row.id)
      ElMessage.success(`库位 ${row.zone_name} 已启用`)
    }
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

async function remove(row: Zone) {
  try {
    await ElMessageBox.confirm(`确认删除库位「${row.zone_name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await zoneAPI.remove(row.id)
    ElMessage.success('库位已删除')
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>库位列表</span>
          <div>
            <el-button @click="loadData" :loading="loading">刷新</el-button>
            <el-button type="primary" @click="openCreate">新增库位</el-button>
          </div>
        </div>
      </template>

      <el-table :data="zones" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="zone_name" label="库位名称" min-width="140" />
        <el-table-column prop="capacity" label="容量" width="100" />
        <el-table-column label="所属仓库" min-width="120">
          <template #default="{ row }">{{ warehouseName(row.warehouse_id) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'">
              {{ row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ row.created_at ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" :type="row.status ? 'warning' : 'success'" @click="toggleStatus(row)">
              {{ row.status ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无库位数据" />
        </template>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑库位' : '新增库位'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="库位名称" prop="zone_name">
          <el-input v-model="form.zone_name" placeholder="如 A-01-01" />
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="form.capacity" :min="0" :max="1000000" />
        </el-form-item>
        <el-form-item label="所属仓库">
          <el-select v-model="form.warehouse_id" placeholder="请选择仓库" clearable style="width: 100%">
            <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" active-text="启用" inactive-text="禁用" />
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
</style>
