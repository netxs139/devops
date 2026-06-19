<script setup lang="ts">
/**
 * @file App.vue
 * @description 根组件：Naive UI 全局配置（Light Theme + 企业品牌色系）
 * 注入 NNotificationProvider 实例到 Notification Store，供 SSE 触发全局通知。
 */
import { onMounted, onUnmounted } from 'vue'
import {
  NConfigProvider,
  NNotificationProvider,
  NMessageProvider,
  NDialogProvider,
  useNotification,
  type GlobalThemeOverrides,
} from 'naive-ui'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useNotificationStore } from '@/store/notification'

// ——— 企业品牌色系（白底黑字，Light Theme 定制）———
const themeOverrides: GlobalThemeOverrides = {
  common: {
    // 主色：企业深蓝（专业感）
    primaryColor: '#1A56DB',
    primaryColorHover: '#1E4DB7',
    primaryColorPressed: '#1E40AF',
    primaryColorSuppl: '#3B82F6',
    // 辅助色
    infoColor: '#0EA5E9',
    successColor: '#10B981',
    warningColor: '#F59E0B',
    errorColor: '#EF4444',
    // 字体
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSize: '14px',
    borderRadius: '6px',
  },
  Button: {
    borderRadius: '6px',
  },
  Card: {
    borderRadius: '8px',
  },
  DataTable: {
    thColor: '#F8FAFC',
    thTextColor: '#374151',
  },
}

const authStore = useAuthStore()
const notifyStore = useNotificationStore()

onMounted(() => {
  // 已登录则启动 SSE 连接
  if (authStore.isAuthenticated) {
    notifyStore.connect()
  }
})

onUnmounted(() => {
  notifyStore.disconnect()
})

// 内部组件：用于注入 NNotification 实例到 Store
const NotificationInjector = {
  name: 'NotificationInjector',
  setup() {
    const notifyApi = useNotification()
    const notifyStore = useNotificationStore()
    notifyStore.setNotifyInstance(notifyApi)
    return () => null // 纯逻辑组件，不渲染任何 DOM
  },
}
</script>

<template>
  <NConfigProvider :theme-overrides="themeOverrides">
    <NNotificationProvider placement="top-right" :max="5">
      <NMessageProvider>
        <NDialogProvider>
          \3c !-- 注入 Notification 实例到 Store，必须在 NNotificationProvider 内部 -->
          <NotificationInjector />
          <RouterView />
        </NDialogProvider>
      </NMessageProvider>
    </NNotificationProvider>
  </NConfigProvider>
</template>

\3c style>
/* 全局重置 */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body, #app {
  height: 100%;
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: #111827;
  background-color: #F9FAFB;
}

/* 企业级 CSS Design Tokens */
:root {
  /* 主色调 */
  --color-primary: #1A56DB;
  --color-primary-hover: #1E4DB7;
  --color-primary-light: #EFF6FF;

  /* 语义色 */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-info: #0EA5E9;

  /* 中性色 */
  --color-text-primary: #111827;
  --color-text-secondary: #6B7280;
  --color-text-tertiary: #9CA3AF;
  --color-border: #E5E7EB;
  --color-bg-base: #F9FAFB;
  --color-bg-card: #FFF;
  --color-bg-hover: #F3F4F6;

  /* 阴影 */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 5%);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 10%), 0 2px 4px -2px rgb(0 0 0 / 10%);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 10%), 0 4px 6px -4px rgb(0 0 0 / 10%);

  /* 间距 */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;

  /* 过渡 */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
  --transition-slow: 300ms ease;
}

/* 滚动条美化（企业白色主题） */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-base);
}

::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

/* 全局过渡动画（prefers-reduced-motion 降级） */
@media (prefers-reduced-motion: no-preference) {
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity var(--transition-base);
  }

  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
  }
}
\3c /style>
