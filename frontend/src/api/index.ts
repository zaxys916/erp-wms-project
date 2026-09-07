import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

/**
 * 统一走 /api 前缀，由 Vite dev server 代理到后端 8000 端口，
 * 避免浏览器跨域与硬编码后端地址。
 */
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('username')
      // 登录接口本身的 401 由页面提示，不做跳转
      const url = error.config?.url ?? ''
      if (!url.includes('/auth/token')) {
        const redirect = encodeURIComponent(window.location.pathname + window.location.search)
        window.location.href = `/login?redirect=${redirect}`
      }
    }
    return Promise.reject(error)
  }
)

/** 从 AxiosError 中提取后端返回的错误信息（统一错误信封 {code,message,errors}） */
export function extractError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as {
      message?: unknown
      detail?: unknown
      errors?: unknown
    } | null
    if (data) {
      if (typeof data.message === 'string' && data.message) return data.message
      if (typeof data.detail === 'string') return data.detail
      if (Array.isArray(data.detail) && data.detail.length) return '数据校验失败'
      if (Array.isArray(data.errors) && data.errors.length) return String(data.errors[0])
    }
    return error.message
  }
  return error instanceof Error ? error.message : '未知错误'
}

/** 后端统一分页结构 */
export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ---------- 类型定义（与后端 schemas 对应）----------
export interface Warehouse {
  id: number
  name: string
  location?: string | null
  created_at?: string | null
}

export interface Zone {
  id: number
  zone_name: string
  capacity: number
  status: boolean
  warehouse_id?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export interface Product {
  id: number
  name: string
  sku?: string | null
  created_at?: string | null
}

export interface Inventory {
  id: number
  product_id: number
  zone_id: number
  quantity: number
  last_updated?: string | null
}

export interface User {
  id: number
  username?: string | null
  email?: string | null
  is_active?: boolean | null
  role?: string | null
  created_at?: string | null
}

/** 出入库单据（后端 stock_orders） */
export interface StockOrder {
  id: number
  order_no: string
  order_type: 'in' | 'out'
  product_id: number
  zone_id: number
  quantity: number
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  remark?: string | null
  created_by?: number | null
  approved_by?: number | null
  created_at?: string | null
  approved_at?: string | null
}

/** 库存流水（后端 inventory_movement） */
export interface InventoryMovement {
  id: number
  product_id: number
  zone_id: number
  movement_type: 'in' | 'out' | 'adjust'
  quantity: number
  balance_after: number
  ref_no?: string | null
  remark?: string | null
  created_by?: number | null
  created_at?: string | null
}

/** 盘点单 */
export interface Stocktake {
  id: number
  order_no: string
  zone_id?: number | null
  status: 'pending' | 'completed'
  remark?: string | null
  created_by?: number | null
  created_at?: string | null
  completed_at?: string | null
}

export interface StocktakeItem {
  id: number
  stocktaking_id: number
  product_id: number
  zone_id: number
  book_qty: number
  actual_qty?: number | null
  diff: number
}

export interface Discrepancy {
  id: number
  stocktaking_id?: number | null
  product_id: number
  zone_id?: number | null
  book_qty: number
  actual_qty: number
  difference: number
  status: 'open' | 'adjusted'
  handled_by?: number | null
  created_at?: string | null
}

// ---------- 认证 ----------
export const authAPI = {
  /** 登录使用 OAuth2 表单格式 */
  login: (username: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    return apiClient.post<{ access_token: string; token_type: string }>('/auth/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  register: (data: { username: string; email: string; password: string; role?: string }) =>
    apiClient.post<User>('/auth/register', data),
  me: () => apiClient.get<User>('/auth/users/me'),
  logout: () => apiClient.post('/auth/logout')
}

// ---------- 仓库 ----------
export const warehouseAPI = {
  list: () => apiClient.get<Page<Warehouse>>('/warehouses'),
  get: (id: number) => apiClient.get<Warehouse>(`/warehouses/${id}`),
  create: (data: { name: string; location?: string }) => apiClient.post<Warehouse>('/warehouses', data),
  update: (id: number, data: { name: string; location?: string }) =>
    apiClient.put<Warehouse>(`/warehouses/${id}`, data),
  remove: (id: number) => apiClient.delete(`/warehouses/${id}`)
}

// ---------- 库位 ----------
export const zoneAPI = {
  list: () => apiClient.get<Page<Zone>>('/zones'),
  get: (id: number) => apiClient.get<Zone>(`/zones/${id}`),
  create: (data: { zone_name: string; capacity: number; status?: boolean; warehouse_id?: number | null }) =>
    apiClient.post<Zone>('/zones', data),
  update: (id: number, data: { zone_name: string; capacity: number; status?: boolean; warehouse_id?: number | null }) =>
    apiClient.put<Zone>(`/zones/${id}`, data),
  enable: (id: number) => apiClient.put<Zone>(`/zones/${id}/enable`),
  disable: (id: number) => apiClient.put<Zone>(`/zones/${id}/disable`),
  remove: (id: number) => apiClient.delete(`/zones/${id}`)
}

// ---------- 产品 ----------
export const productAPI = {
  list: () => apiClient.get<Page<Product>>('/products'),
  get: (id: number) => apiClient.get<Product>(`/products/${id}`),
  create: (data: { name: string; sku: string }) => apiClient.post<Product>('/products', data),
  update: (id: number, data: { name: string; sku: string }) =>
    apiClient.put<Product>(`/products/${id}`, data),
  remove: (id: number) => apiClient.delete(`/products/${id}`)
}

// ---------- 库存 ----------
export const inventoryAPI = {
  list: () => apiClient.get<Page<Inventory>>('/inventory'),
  get: (id: number) => apiClient.get<Inventory>(`/inventory/${id}`),
  status: () =>
    apiClient.get<{ total_records: number; total_quantity: number; last_updated: string | null }>(
      '/inventory/status'
    ),
  movements: () => apiClient.get<Page<InventoryMovement>>('/inventory/movements'),
  create: (data: { product_id: number; zone_id: number; quantity: number }) =>
    apiClient.post<Inventory>('/inventory', data),
  update: (id: number, data: { product_id: number; zone_id: number; quantity: number }) =>
    apiClient.put<Inventory>(`/inventory/${id}`, data),
  remove: (id: number) => apiClient.delete(`/inventory/${id}`)
}

// ---------- 出入库单据（先建单、审核后生效）----------
export const stockOrderAPI = {
  list: () => apiClient.get<Page<StockOrder>>('/movements'),
  create: (data: {
    order_type: 'in' | 'out'
    product_id: number
    zone_id: number
    quantity: number
    remark?: string
  }) => apiClient.post<StockOrder>('/movements', data),
  approve: (id: number) => apiClient.post<StockOrder>(`/movements/${id}/approve`),
  reject: (id: number) => apiClient.post<StockOrder>(`/movements/${id}/reject`),
  cancel: (id: number) => apiClient.post<StockOrder>(`/movements/${id}/cancel`)
}

// ---------- 库存盘点 ----------
export const stocktakeAPI = {
  list: () => apiClient.get<Page<Stocktake>>('/stocktakes'),
  create: (data: { zone_id?: number | null; remark?: string }) =>
    apiClient.post<{ id: number; order_no: string; status: string; items: StocktakeItem[] }>(
      '/stocktakes',
      data
    ),
  detail: (id: number) =>
    apiClient.get<Stocktake & { items: StocktakeItem[] }>(`/stocktakes/${id}`),
  updateItem: (id: number, itemId: number, actualQty: number) =>
    apiClient.put<StocktakeItem>(`/stocktakes/${id}/items/${itemId}`, { actual_qty: actualQty }),
  complete: (id: number) =>
    apiClient.post<{
      id: number
      order_no: string
      status: string
      item_count: number
      adjusted_count: number
      total_diff: number
    }>(`/stocktakes/${id}/complete`),
  discrepancies: () => apiClient.get<Page<Discrepancy>>('/stocktakes/discrepancies')
}

// ---------- 用户 ----------
export const userAPI = {
  list: () => apiClient.get<Page<User>>('/users'),
  get: (id: number) => apiClient.get<User>(`/users/${id}`),
  create: (data: { username: string; email: string; password: string; role?: string }) =>
    apiClient.post<User>('/users', data),
  enable: (id: number) => apiClient.put<User>(`/users/${id}/enable`),
  disable: (id: number) => apiClient.put<User>(`/users/${id}/disable`),
  updatePassword: (id: number, newPassword: string) =>
    apiClient.put(`/users/${id}/password`, null, { params: { new_password: newPassword } })
}

export default apiClient
