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

// 侧边导航菜单（根据权限与路由配置动态生成，按 Domain 分组）
const menuOptions = computed<MenuOption[]>(() => {
  const rootRoute = router.options.routes.find((r) => r.path === '/')
  const children = rootRoute?.children || []

  // 提取所有需要在菜单显示的路由，并检查权限
  const visibleRoutes = children.filter((route) => {
    if (!route.meta?.showInMenu) return false
    const perms = route.meta.permissions as string[] | undefined
    if (perms && perms.length > 0) {
      return perms.some((p) => auth.hasPermission(p))
    }
    return true
  })

  // 按 Domain 分组
  const domainGroups = new Map<string, MenuOption[]>()
  for (const route of visibleRoutes) {
    const domain = (route.meta?.domain as string) || '其他'
    if (!domainGroups.has(domain)) {
      domainGroups.set(domain, [])
    }
    domainGroups.get(domain)!.push({
      label: (route.meta?.title as string) || route.name,
      key: `/${route.path}`,
      icon: route.meta?.icon ? () => h('span', route.meta!.icon as string) : undefined,
    })
  }

  // 构造分组菜单结构
  const groupedMenu: MenuOption[] = []

  // 首页导航直接提升，不作为折叠组
  const navGroup = domainGroups.get('导航')
  if (navGroup) {
    groupedMenu.push(...navGroup)
  }

  // 其他组作为 MenuGroup 渲染（这里为了侧边栏清晰，使用 type: 'group' 或者带 children 的节点）
  for (const [domain, items] of domainGroups.entries()) {
    if (domain === '导航') continue
    groupedMenu.push({
      type: 'group',
      label: domain,
      key: `group-${domain}`,
      children: items,
    })
  }

  return groupedMenu
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
