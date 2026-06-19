/**
 * @file request.ts
 * @description Axios HTTP 客户端封装。
 *
 * 等保三级安全要求：
 * 1. 请求拦截器自动注入 Authorization Bearer Token
 * 2. 请求拦截器自动注入 X-Correlation-ID（UUID v4），供 AuditMiddleware 捕获
 * 3. 响应拦截器捕获 401 自动重定向 /login
 * 4. 响应拦截器解析后端 BusinessException 并抛出结构化错误
 */

import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'
import { v4 as uuidv4 } from 'uuid'
import type { BusinessException } from '@/types/api'

// 创建独立实例，避免污染全局 axios
const request: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// =============================================================================
// 请求拦截器
// =============================================================================
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 1. 注入 JWT Token（从 localStorage 读取，由 auth store 写入）
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }

    // 2. 注入 Correlation-ID（等保三级审计追踪链路）
    config.headers['X-Correlation-ID'] = uuidv4()

    return config
  },
  (error: unknown) => Promise.reject(error),
)

// =============================================================================
// 响应拦截器
// =============================================================================
request.interceptors.response.use(
  (response) => response.data,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) {
      return Promise.reject(error)
    }

    const status = error.response?.status
    const responseData = error.response?.data as BusinessException | undefined

    // 401 — Token 过期或未登录，强制重定向到登录页
    if (status === 401) {
      localStorage.removeItem('access_token')
      // 避免循环重定向：仅在非登录页时跳转
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
      }
      return Promise.reject(error)
    }

    // 403 — 权限不足，抛出结构化错误，由组件层捕获展示 Toast
    if (status === 403) {
      const businessError: BusinessException = {
        code: 'PERMISSION_DENIED',
        message: responseData?.message ?? '您没有权限执行此操作',
        correlation_id: responseData?.correlation_id ?? '',
      }
      return Promise.reject(businessError)
    }

    // 422 — 参数校验失败（FastAPI ValidationError）
    if (status === 422) {
      const businessError: BusinessException = {
        code: 'VALIDATION_ERROR',
        message: responseData?.message ?? '请求参数校验失败，请检查输入',
        detail: responseData?.detail,
        correlation_id: responseData?.correlation_id ?? '',
      }
      return Promise.reject(businessError)
    }

    // 其他业务错误 — 透传后端 BusinessException
    if (responseData?.code) {
      return Promise.reject(responseData as BusinessException)
    }

    // 网络错误兜底
    const networkError: BusinessException = {
      code: 'NETWORK_ERROR',
      message: error.message ?? '网络连接异常，请稍后重试',
      correlation_id: '',
    }
    return Promise.reject(networkError)
  },
)

// =============================================================================
// 类型安全的请求方法封装
// =============================================================================
export const http = {
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return request.get<T, T>(url, config)
  },
  post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return request.post<T, T>(url, data, config)
  },
  patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return request.patch<T, T>(url, data, config)
  },
  put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return request.put<T, T>(url, data, config)
  },
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return request.delete<T, T>(url, config)
  },
}

export default request
