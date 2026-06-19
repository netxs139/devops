/**
 * @file directives/permission.ts
 * @description v-permission 按钮级鉴权指令
 *
 * 用法：
 *   <NButton v-permission="'USER:MANAGE'">审批</NButton>
 *   <NButton v-permission="['rpt:quality:view', 'USER:MANAGE']">批量操作</NButton>
 *
 * 策略：无权限时直接从 DOM 移除元素（非 disable），防止通过 CSS 绕过的 UI 欺骗攻击。
 * 注意：按钮级鉴权是展示层防御，真正的权限校验在后端 API 层。
 */

import type { Directive, DirectiveBinding } from 'vue'
import { useAuthStore } from '@/store/auth'

function checkPermission(el: HTMLElement, binding: DirectiveBinding<string | string[]>): void {
  const auth = useAuthStore()
  const requiredPerms = Array.isArray(binding.value) ? binding.value : [binding.value]

  // OR 语义：满足任一权限即可见
  const hasAccess = requiredPerms.some((perm) => auth.hasPermission(perm))

  if (!hasAccess) {
    // 直接移除 DOM 元素，而非仅隐藏（防止 CSS 绕过）
    el.parentNode?.removeChild(el)
  }
}

export const vPermission: Directive<HTMLElement, string | string[]> = {
  mounted(el, binding) {
    checkPermission(el, binding)
  },
  updated(el, binding) {
    checkPermission(el, binding)
  },
}
