<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { authAPI, extractError } from '@/api'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const { data } = await authAPI.login(form.username, form.password)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('username', form.username)
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e) {
    ElMessage.error(extractError(e))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card" shadow="always">
      <div class="title">
        <h2>ERP-WMS 系统</h2>
        <p>企业资源计划 · 仓库管理系统</p>
      </div>
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="默认管理员账号：admin / admin123"
        class="mb"
      />
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="handleLogin">
          登 录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  min-height: calc(100vh - 200px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 420px;
  padding: 8px 12px;
}

.title {
  text-align: center;
  margin-bottom: 18px;
}

.title h2 {
  margin: 0 0 6px;
  color: #001529;
  letter-spacing: 2px;
}

.title p {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.mb {
  margin-bottom: 18px;
}

.submit-btn {
  width: 100%;
  margin-top: 6px;
}
</style>
