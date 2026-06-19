/**
 * @file store/notification.ts
 * @description SSE 实时通知流管理（Pinia Store）
 *
 * 职责：
 * 1. 建立并维护 /notifications/stream SSE 长连接
 * 2. 内存缓存最新通知（最多保留 50 条）
 * 3. 触发 Naive UI NNotification 全局通知框
 * 4. 连接断开时指数退避重连（最大 30s）
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { NotificationApi } from 'naive-ui'
import type { Notification } from '@/types/api'

const MAX_NOTIFICATIONS = 50
const INITIAL_RETRY_MS = 1000
const MAX_RETRY_MS = 30_000

export const useNotificationStore = defineStore('notification', () => {
  // ==========================================================================
  // State
  // ==========================================================================
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const isConnected = ref(false)

  // NNotification 实例由 App.vue 注入
  let naiveNotify: NotificationApi | null = null
  let eventSource: EventSource | null = null
  let retryMs = INITIAL_RETRY_MS
  let retryTimer: ReturnType<typeof setTimeout> | null = null

  // ==========================================================================
  // Actions
  // ==========================================================================

  /** 由 App.vue 在挂载后注入 Naive UI notification 实例 */
  function setNotifyInstance(instance: NotificationApi): void {
    naiveNotify = instance
  }

  /** 建立 SSE 连接 */
  function connect(): void {
    if (eventSource) return // 防止重复连接

    const token = localStorage.getItem('access_token')
    if (!token) return

    // SSE 不支持自定义 Header，通过 query 参数传递 token
    // 后端 /notifications/stream 需要支持 ?token= 参数认证
    eventSource = new EventSource(`/notifications/stream?token=${encodeURIComponent(token)}`)

    eventSource.onopen = (): void => {
      isConnected.value = true
      retryMs = INITIAL_RETRY_MS // 连接成功后重置重试间隔
    }

    eventSource.onmessage = (event: MessageEvent): void => {
      try {
        const notification = JSON.parse(event.data as string) as Notification
        addNotification(notification)
      } catch {
        console.warn('[NotificationStore] Failed to parse SSE message:', event.data)
      }
    }

    eventSource.onerror = (): void => {
      isConnected.value = false
      eventSource?.close()
      eventSource = null
      scheduleReconnect()
    }
  }

  /** 断开 SSE 连接 */
  function disconnect(): void {
    if (retryTimer) clearTimeout(retryTimer)
    eventSource?.close()
    eventSource = null
    isConnected.value = false
  }

  /** 指数退避重连 */
  function scheduleReconnect(): void {
    if (retryTimer) clearTimeout(retryTimer)
    retryTimer = setTimeout(() => {
      connect()
      retryMs = Math.min(retryMs * 2, MAX_RETRY_MS)
    }, retryMs)
  }

  /** 添加通知到内存队列，并触发 Naive UI Toast */
  function addNotification(notification: Notification): void {
    // 头部插入，保持最新在前
    notifications.value.unshift(notification)
    if (notifications.value.length > MAX_NOTIFICATIONS) {
      notifications.value.pop()
    }
    if (!notification.read) {
      unreadCount.value++
    }

    // 触发 Naive UI 全局通知
    if (naiveNotify) {
      const notifyFn =
        notification.type === 'error'   ? naiveNotify.error
        : notification.type === 'warning' ? naiveNotify.warning
        : notification.type === 'success' ? naiveNotify.success
        : naiveNotify.info

      notifyFn({
        title: notification.title,
        content: notification.content,
        duration: notification.type === 'error' ? 0 : 5000, // 错误通知不自动消失
        keepAliveOnHover: true,
      })
    }
  }

  /** 标记全部已读 */
  function markAllRead(): void {
    notifications.value.forEach((n) => { n.read = true })
    unreadCount.value = 0
  }

  return {
    notifications,
    unreadCount,
    isConnected,
    setNotifyInstance,
    connect,
    disconnect,
    markAllRead,
  }
})
