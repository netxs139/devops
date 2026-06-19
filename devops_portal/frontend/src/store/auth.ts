/**
 * @file store/auth.ts
 * @description 用户认证状态机（Pinia Store）
 *
 * 职责：
 * 1. 存储 JWT Token，解析 Payload（roles, permissions, department, location）
 * 2. 提供 hasPermission(perm) / hasRole(role) 权限判定方法
 * 3. 实现数据隔离作用域（department / location）供组件按需读取
 * 4. 封装 GitLab OAuth 回调处理（截获 query 参数写入 Store）
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { JwtPayload, UserProfile } from '@/types/api'

// JWT Base64 解码，兼容 Unicode
function parseJwtPayload(token: string): JwtPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const jsonStr = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
        .join(''),
    )
    return JSON.parse(jsonStr) as JwtPayload
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  // ==========================================================================
  // State
  // ==========================================================================
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const payload = ref<JwtPayload | null>(
    token.value ? parseJwtPayload(token.value) : null,
  )

  // ==========================================================================
  // Getters（计算属性）
  // ==========================================================================
  const isAuthenticated = computed(() => {
    if (!token.value || !payload.value) return false
    // 检查 JWT 是否过期
    return payload.value.exp * 1000 > Date.now()
  })

  const currentUser = computed<UserProfile | null>(() => {
    if (!payload.value) return null
    return {
      id: 0, // 由 /api/users/me 补充
      username: payload.value.username,
      email: payload.value.sub,
      department: payload.value.department,
      location: payload.value.location,
      roles: payload.value.roles,
      permissions: payload.value.permissions,
    }
  })

  /** 数据隔离作用域：部门 */
  const dataScopeDepartment = computed(() => payload.value?.department ?? null)

  /** 数据隔离作用域：省份（location） */
  const dataScopeLocation = computed(() => payload.value?.location ?? null)

  // ==========================================================================
  // Actions
  // ==========================================================================

  /** 权限判定：精确匹配，区分大小写（与后端 RBAC 树镜像对齐） */
  function hasPermission(perm: string): boolean {
    if (!payload.value) return false
    return payload.value.permissions.includes(perm)
  }

  /** 角色判定 */
  function hasRole(role: string): boolean {
    if (!payload.value) return false
    return payload.value.roles.includes(role)
  }

  /** 多权限判定（OR 语义：满足任一即可） */
  function hasAnyPermission(...perms: string[]): boolean {
    return perms.some((p) => hasPermission(p))
  }

  /** 写入 Token（GitLab OAuth 回调 & 普通登录均调用此方法） */
  function setToken(newToken: string): void {
    const parsed = parseJwtPayload(newToken)
    if (!parsed) {
      console.error('[AuthStore] Invalid JWT token format')
      return
    }
    token.value = newToken
    payload.value = parsed
    localStorage.setItem('access_token', newToken)
  }

  /** 登出：清除所有认证状态 */
  function logout(): void {
    token.value = null
    payload.value = null
    localStorage.removeItem('access_token')
  }

  return {
    token,
    payload,
    isAuthenticated,
    currentUser,
    dataScopeDepartment,
    dataScopeLocation,
    hasPermission,
    hasRole,
    hasAnyPermission,
    setToken,
    logout,
  }
})
