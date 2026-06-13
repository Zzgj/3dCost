import axios from 'axios'
import { ElMessage } from 'element-plus'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

const ERROR_MESSAGES: Record<string, string> = {
  INSUFFICIENT_STOCK: '库存不足',
  LOCKED_RESOURCE: '资源已锁定,无法修改',
  BOM_CYCLE_DETECTED: 'BOM 存在循环引用',
  COST_SOURCE_MISSING: '缺少成本数据,请先录入采购',
  NOT_FOUND: '资源不存在',
  VALIDATION_ERROR: '请求参数有误',
}

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const code = error.response?.data?.error?.code
    const message = error.response?.data?.error?.message
    ElMessage.error(ERROR_MESSAGES[code] || message || '操作失败')
    return Promise.reject(error)
  },
)

export default client
