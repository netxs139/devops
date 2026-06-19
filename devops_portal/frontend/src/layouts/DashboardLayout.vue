<script setup lang="ts">
/**
 * @file DashboardLayout.vue
 * @description 主应用布局：侧边导航 + 顶部栏 + 内容区
 * 数据隔离作用域展示：顶部右侧显示当前用户的 department / location
 */
import { computed, h } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import {
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NAvatar,
  NDropdown,
  NSpace,
  NTag,
  NBadge,
  NButton,
  NText,
} from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { useAuthStore } from '@/store/auth'
import { useNotificationStore } from '@/store/notification'

const router = useRouter()
const auth = useAuthStore()
const notifyStore = useNotificationStore()

const user = computed(() => auth.currentUser)

// 侧边导航菜单（根据权限动态过滤）
const menuOptions = computed<MenuOption[]>(() => {
  const all: MenuOption[] = [
    { label: '首页总览', key: '/home', icon: () => h('span', '📊') },
    { label: '质量监控', key: '/quality', icon: () => h('span', '🛡️'),
      show: auth.hasPermission('rpt:quality:view') },
    { label: 'Traceability 雷达', key: '/radar', icon: () => h('span', '📡'),
      show: auth.hasPermission('rpt:quality:view') },
    { label: '迭代看板', key: '/board', icon: () => h('span', '🗂️') },
    { label: '测试用例', key: '/test-cases', icon: () => h('span', '✅') },
    { label: '服务台', key: '/service-desk', icon: () => h('span', '💁') },
    { label: '系统管理', key: '/admin', icon: () => h('span', '⚙️'),
      show: auth.hasPermission('USER:MANAGE') },
  ]
  return all.filter((item) => item['show'] !== false)
})

function handleMenuSelect(key: string): void {
  router.push(key)
}

const userDropdownOptions = [
  { label: '退出登录', key: 'logout' },
]

function handleUserAction(key: string): void {
  if (key === 'logout') {
    notifyStore.disconnect()
    auth.logout()
    router.push('/login')
  }
}
</script>

<template>
  <NLayout has-sider style="height: 100vh;">
    <!-- 侧边栏 -->
    <NLayoutSider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      show-trigger
      style="background: var(--color-bg-card);"
    >
      <!-- Logo 区域 -->
      <div class="logo-area">
        <div class="logo-icon">D</div>
        <NText strong class="logo-text">DevOps Portal</NText>
      </div>

      <NMenu
        :options="menuOptions"
        :indent="18"
        @update:value="handleMenuSelect"
      />
    </NLayoutSider>

    <NLayout>
      <!-- 顶部栏 -->
      <NLayoutHeader bordered class="header">
        <NSpace align="center" justify="end" style="height: 100%; padding: 0 24px;">
          <!-- 数据隔离作用域标签 -->
          <NTag v-if="user?.department" type="info" size="small">
            {{ user.department }}
          </NTag>
          <NTag v-if="user?.location" size="small">
            {{ user.location }}
          </NTag>

          <!-- 通知 -->
          <NBadge :value="notifyStore.unreadCount" :max="99">
            <NButton quaternary circle size="small">
              <template #icon>🔔</template>
            </NButton>
          </NBadge>

          <!-- 用户头像 -->
          <NDropdown :options="userDropdownOptions" @select="handleUserAction">
            <NSpace align="center" style="cursor: pointer;">
              <NAvatar round size="small" style="background: var(--color-primary); color: #fff;">
                {{ user?.username?.charAt(0)?.toUpperCase() ?? 'U' }}
              </NAvatar>
              <NText>{{ user?.username }}</NText>
            </NSpace>
          </NDropdown>
        </NSpace>
      </NLayoutHeader>

      <!-- 内容区 -->
      <NLayoutContent
        content-style="padding: 24px; background: var(--color-bg-base);"
        :native-scrollbar="false"
      >
        <RouterView />
      </NLayoutContent>
    </NLayout>
  </NLayout>
</template>

<style scoped>
.logo-area {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  height: 64px;
  overflow: hidden;
}

.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-text {
  font-size: 15px;
  white-space: nowrap;
}

.header {
  height: 64px;
  background: var(--color-bg-card);
  display: flex;
  align-items: center;
}
</style>
