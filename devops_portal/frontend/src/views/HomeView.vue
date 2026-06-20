<script setup lang="ts">
/**
 * @file HomeView.vue
 * @description 首页导航大厅 (Navigation Hub)
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { NGrid, NGridItem, NCard, NText, NSpace } from 'naive-ui'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

interface NavItem {
  name: string
  path: string
  title: string
  icon: string
}

interface DomainGroup {
  domain: string
  items: NavItem[]
}

const domainGroups = computed<DomainGroup[]>(() => {
  const rootRoute = router.options.routes.find((r) => r.path === '/')
  const children = rootRoute?.children || []

  // 提取需要在菜单显示的路由，并检查权限
  const visibleRoutes = children.filter((route) => {
    if (!route.meta?.showInMenu) return false
    const perms = route.meta.permissions as string[] | undefined
    if (perms && perms.length > 0) {
      return perms.some((p) => auth.hasPermission(p))
    }
    return true
  })

  const groups = new Map<string, NavItem[]>()
  for (const route of visibleRoutes) {
    const domain = (route.meta?.domain as string) || '其他'
    if (domain === '导航') continue // 跳过自己

    if (!groups.has(domain)) {
      groups.set(domain, [])
    }
    groups.get(domain)!.push({
      name: route.name as string,
      path: `/${route.path}`,
      title: (route.meta?.title as string) || (route.name as string),
      icon: (route.meta?.icon as string) || '📌',
    })
  }

  const result: DomainGroup[] = []
  for (const [domain, items] of groups.entries()) {
    result.push({ domain, items })
  }
  return result
})

function navigateTo(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="home-container">
    <div class="header-section">
      <h1 class="page-title">全域导航大厅</h1>
      <p class="page-subtitle">欢迎来到 DevOps Portal，选择下方业务域进入工作。</p>
    </div>

    <div v-for="group in domainGroups" :key="group.domain" class="domain-section">
      <h2 class="domain-title">{{ group.domain }}</h2>
      <NGrid :cols="4" :x-gap="24" :y-gap="24" responsive="screen">
        <NGridItem v-for="item in group.items" :key="item.path">
          <NCard class="nav-card" hoverable @click="navigateTo(item.path)">
            <NSpace vertical align="center" :size="16">
              <div class="icon-wrapper">
                <span class="icon-emoji">{{ item.icon }}</span>
              </div>
              <NText strong class="card-title">{{ item.title }}</NText>
            </NSpace>
          </NCard>
        </NGridItem>
      </NGrid>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  max-width: 1440px;
  margin: 0 auto;
}

.header-section {
  margin-bottom: var(--space-8);
  text-align: center;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 15px;
  color: var(--color-text-secondary);
}

.domain-section {
  margin-bottom: var(--space-8);
}

.domain-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.nav-card {
  cursor: pointer;
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--color-bg-card);
  height: 100%;
}

.nav-card:hover {
  transform: translateY(-4px);
  border-color: var(--color-primary);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.05);
}

.icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--color-bg-base);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
}

.nav-card:hover .icon-wrapper {
  background: rgba(14, 165, 233, 0.1);
}

.icon-emoji {
  font-size: 32px;
}

.card-title {
  font-size: 15px;
  text-align: center;
}
</style>
