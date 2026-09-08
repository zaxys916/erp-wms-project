<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { supplierAPI, extractError, type Supplier } from '@/api'

const loading = ref(false)
const rows = ref<Supplier[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({ name: '', contact: '', phone: '', address: '' })

const rules: FormRules = {
  name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    const { data } = await supplierAPI.list()
    rows.value = data.items
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { name: '', contact: '', phone: '', address: '' })
  dialogVisible.value = true
}

function openEdit(row: Supplier) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    contact: row.contact ?? '',
    phone: row.phone ?? '',
    address: row.address ?? ''
  })
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  try {
    if (isEdit.value && editingId.value != null) {
      await supplierAPI.update(editingId.value, { ...form })
      ElMessage.success('供应商已更新')
    } else {
      await supplierAPI.create({ ...form })
      ElMessage.success('供应商已创建')
    }
    dialogVisible.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

async function remove(row: Supplier) {
  try {
    await ElMessageBox.confirm(`确认删除供应商「${row.name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await supplierAPI.remove(row.id)
    ElMessage.success('供应商已删除')
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
          <span>供应商档案</span>
          <div class="header-actions">
            <el-button @click="loadData" :loading="loading">刷新</el-button>
            <el-button type="primary" @click="openCreate">新增供应商</el-button>
          </div>
        </div>
      </template>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="contact" label="联系人" width="120">
          <template #default="{ row }">{{ row.contact ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" width="140">
          <template #default="{ row }">{{ row.phone ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="address" label="地址" min-width="180">
          <template #default="{ row }">{{ row.address ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无供应商数据" />
        </template>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑供应商' : '新增供应商'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="供应商名称" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
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