<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { userAPI, extractError, type User } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const user = ref<User | null>(null)

const userId = computed(() => Number(route.params.id))

const roleDesc = computed(() => {
  switch (user.value?.role) {
    case 'admin':
      return '管理员 — 拥有全部权限'
    case 'operator':
      return '操作员 — 可读写库存与库位'
    default:
      return '普通用户 — 仅可查看'
  }
})

async function loadData() {
  loading.value = true
  try {
    const { data } = await userAPI.get(userId.value)
    user.value = data
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div v-loading="loading">
    <el-page-header content="用户详情" @back="router.push('/users')" class="header" />

    <el-descriptions :column="2" border v-if="user">
      <el-descriptions-item label="ID">{{ user.id }}</el-descriptions-item>
      <el-descriptions-item label="用户名">{{ user.username ?? '-' }}</el-descriptions-item>
      <el-descriptions-item label="邮箱">{{ user.email ?? '-' }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="user.is_active ? 'success' : 'danger'">
          {{ user.is_active ? '启用' : '禁用' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="角色">{{ user.role ?? '-' }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ user.created_at ?? '-' }}</el-descriptions-item>
      <el-descriptions-item label="权限说明" :span="2">{{ roleDesc }}</el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<style scoped>
.header {
  margin-bottom: 16px;
}
</style>
