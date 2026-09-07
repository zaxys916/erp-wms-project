<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { userAPI, extractError, type User } from '@/api'

const loading = ref(false)
const users = ref<User[]>([])

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({ username: '', email: '', password: '', role: 'user' })

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }]
}

async function loadData() {
  loading.value = true
  try {
    const { data } = await userAPI.list()
    users.value = data
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, { username: '', email: '', password: '', role: 'user' })
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  try {
    await userAPI.create({ ...form })
    ElMessage.success('用户已创建')
    dialogVisible.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

async function toggleActive(row: User) {
  try {
    if (row.is_active) {
      await userAPI.disable(row.id)
      ElMessage.success(`用户 ${row.username} 已禁用`)
    } else {
      await userAPI.enable(row.id)
      ElMessage.success(`用户 ${row.username} 已启用`)
    }
    await loadData()
  } catch (e) {
    ElMessage.error(extractError(e))
  }
}

const roleTagType = (role?: string | null) =>
  role === 'admin' ? 'danger' : role === 'operator' ? 'warning' : 'info'

onMounted(loadData)
</script>

<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>用户列表</span>
          <div>
            <el-button @click="loadData" :loading="loading">刷新</el-button>
            <el-button type="primary" @click="openCreate">新增用户</el-button>
          </div>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="160" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)">{{ row.role ?? '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ row.created_at ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggleActive(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无用户数据" />
        </template>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新增用户" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="普通用户 (user)" value="user" />
            <el-option label="操作员 (operator)" value="operator" />
            <el-option label="管理员 (admin)" value="admin" />
          </el-select>
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
