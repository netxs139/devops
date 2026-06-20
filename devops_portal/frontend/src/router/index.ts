/**
 * @file router/index.ts
 * @description Vue Router 配置
 *
 * 路由守卫策略：
 * 1. 未登录 → 重定向 /login（保留 redirect 参数，登录后回跳）
 * 2. 已登录访问 /login → 重定向首页
 * 3. meta.permissions 非空 → 校验 hasPermission，无权限 → /403
 * 4. GitLab OAuth 回调：/login/callback 路由解析 query.access_token → 写入 Auth Store
 */

/* eslint-disable @typescript-eslint/explicit-function-return-type */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/store/auth'

// 懒加载视图（减少首屏包体积）
const LoginView        = () => import('@/views/LoginView.vue')
const LoginCallback    = () => import('@/views/LoginCallback.vue')
const DashboardLayout  = () => import('@/layouts/DashboardLayout.vue')
const HomeView         = () => import('@/views/HomeView.vue')
const QualityView      = () => import('@/views/QualityView.vue')
const RadarView        = () => import('@/views/RadarView.vue')
const BoardView        = () => import('@/views/BoardView.vue')
const TestCaseView     = () => import('@/views/TestCaseView.vue')
const ServiceDeskView  = () => import('@/views/ServiceDeskView.vue')
const AdminView        = () => import('@/views/AdminView.vue')
const ForbiddenView    = () => import('@/views/ForbiddenView.vue')
const NotFoundView     = () => import('@/views/NotFoundView.vue')
const PlaceholderView  = () => import('@/views/PlaceholderView.vue')

// --- Dashboard Map 定义 (Index 0 - 23) ---
const dashboardModules = [
  { path: 'quality', name: 'Quality', title: 'Quality Monitor', domain: '底座/质量', icon: '🛡️', component: QualityView, perms: ['rpt:quality:view'] },
  { path: 'gitprime', name: 'Gitprime', title: 'Gitprime', domain: '效能/代码', icon: '📈', component: PlaceholderView },
  { path: 'dora-metrics', name: 'DORAMetrics', title: 'DORA Metrics', domain: '效能/标准', icon: '⏱️', component: PlaceholderView },
  { path: 'project-health', name: 'ProjectHealth', title: 'Project Health', domain: '项目/全景', icon: '🗺️', component: PlaceholderView },
  { path: 'compliance-audit', name: 'ComplianceAudit', title: 'Compliance Audit', domain: '安全/合规', icon: '🔒', component: PlaceholderView },
  { path: 'abi-analysis', name: 'ABIAnalysis', title: 'ABI Analysis', domain: '技术/二进制', icon: '📦', component: PlaceholderView },
  { path: 'user-profile', name: 'UserProfile', title: 'User Profile', domain: '人员/画像', icon: '👤', component: PlaceholderView },
  { path: 'capitalization-audit', name: 'CapitalizationAudit', title: 'Capitalization Audit', domain: '财经/资本化', icon: '💰', component: PlaceholderView },
  { path: 'shadow-it', name: 'ShadowIT', title: 'Shadow IT', domain: '治理/发现', icon: '🕵️', component: PlaceholderView },
  { path: 'talent-radar', name: 'TalentRadar', title: 'Talent Radar', domain: '人员/储备', icon: '🎯', component: PlaceholderView },
  { path: 'metrics-guard', name: 'MetricsGuard', title: 'Metrics Guard', domain: '质量/拦截', icon: '🛑', component: PlaceholderView },
  { path: 'unified-activities', name: 'UnifiedActivities', title: 'Unified Activities', domain: '研发/全踪', icon: '🌊', component: PlaceholderView },
  { path: 'work-items', name: 'WorkItems', title: 'Work Items', domain: '协作/任务', icon: '📋', component: PlaceholderView },
  { path: 'entity-alignment', name: 'EntityAlignment', title: 'Entity Alignment', domain: 'MDM/对齐', icon: '🔗', component: PlaceholderView },
  { path: 'delivery-costs', name: 'DeliveryCosts', title: 'Delivery Costs', domain: '成本/FinOps', icon: '💸', component: PlaceholderView },
  { path: 'metadata-governance', name: 'MetadataGovernance', title: 'Metadata Governance', domain: '治理/标准', icon: '📚', component: PlaceholderView },
  { path: 'code-hotspots', name: 'CodeHotspots', title: 'Code Hotspots', domain: '技术/重构', icon: '🔥', component: PlaceholderView },
  { path: 'space-framework', name: 'SPACEFramework', title: 'SPACE Framework', domain: '人员/体验', icon: '🧘', component: PlaceholderView },
  { path: 'value-stream', name: 'ValueStream', title: 'Value Stream', domain: '价值/过程', icon: '🔄', component: PlaceholderView },
  { path: 'executive-cockpit', name: 'ExecutiveCockpit', title: 'Executive Cockpit', domain: '决策/大屏', icon: '👑', component: PlaceholderView, perms: ['rpt:executive:view'] },
  { path: 'nexus-finops', name: 'NexusFinOps', title: 'Nexus FinOps', domain: '治理/资产', icon: '🗄️', component: PlaceholderView },
  { path: 'dora-refined', name: 'DORARefined', title: 'DORA Refined', domain: '效能/标准', icon: '⏱️', component: PlaceholderView },
  { path: 'code-traceability', name: 'CodeTraceability', title: 'Code Traceability', domain: '效能/溯源', icon: '📡', component: RadarView, perms: ['rpt:quality:view'] },
  { path: 'radar-intelligence', name: 'RadarIntelligence', title: 'Radar Intelligence', domain: '效能/聚合', icon: '👁️', component: PlaceholderView },
]

// 核心功能路由
const coreModules = [
  { path: 'board', name: 'Board', title: '迭代看板', domain: '日常作业', icon: '🗂️', component: BoardView, perms: ['rpt:quality:view'] },
  { path: 'test-cases', name: 'TestCase', title: '测试用例', domain: '日常作业', icon: '✅', component: TestCaseView, perms: ['rpt:quality:view'] },
  { path: 'service-desk', name: 'ServiceDesk', title: '服务台', domain: '支持与治理', icon: '💁', component: ServiceDeskView },
  { path: 'admin', name: 'Admin', title: '系统管理', domain: '支持与治理', icon: '⚙️', component: AdminView, perms: ['USER:MANAGE'] },
]

const mainChildren: RouteRecordRaw[] = [
  {
    path: 'home',
    name: 'Home',
    component: HomeView,
    meta: { title: '首页导航大厅', domain: '导航', icon: '📊', showInMenu: true },
  },
  ...dashboardModules.map(m => ({
    path: m.path,
    name: m.name,
    component: m.component,
    meta: { title: m.title, domain: m.domain, icon: m.icon, showInMenu: true, permissions: m.perms }
  })),
  ...coreModules.map(m => ({
    path: m.path,
    name: m.name,
    component: m.component,
    meta: { title: m.title, domain: m.domain, icon: m.icon, showInMenu: true, permissions: m.perms }
  }))
]

const routes: RouteRecordRaw[] = [
  // ——— 公开路由 ———
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { public: true },
  },
  {
    path: '/login/callback',
    name: 'LoginCallback',
    component: LoginCallback,
    meta: { public: true },
  },

  // ——— 需要登录的主应用路由 ———
  {
    path: '/',
    component: DashboardLayout,
    redirect: '/home',
    children: mainChildren,
  },

  // ——— 错误页面 ———
  {
    path: '/403',
    name: 'Forbidden',
    component: ForbiddenView,
    meta: { public: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFoundView,
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// =============================================================================
// 全局路由守卫
// =============================================================================
router.beforeEach((to, _from) => {
  // 注意：Pinia 必须在 createApp 之后才可用，这里通过直接调用 useAuthStore() 是安全的
  // 因为 router 是在 createApp 之后才调用 router.beforeEach
  const auth = useAuthStore()

  // 1. 公开路由直接放行
  if (to.meta.public) {
    // 已登录用户访问 /login → 直接跳首页
    if (to.name === 'Login' && auth.isAuthenticated) {
      return { name: 'Home' }
    }
    return true
  }

  // 2. 未登录 → 跳转 /login，携带 redirect 参数
  if (!auth.isAuthenticated) {
    return {
      name: 'Login',
      query: { redirect: to.fullPath },
    }
  }

  // 3. 权限校验（meta.permissions 数组，OR 语义）
  const requiredPerms = to.meta.permissions as string[] | undefined
  if (requiredPerms && requiredPerms.length > 0) {
    const hasPerm = requiredPerms.some((p) => auth.hasPermission(p))
    if (!hasPerm) {
      return { name: 'Forbidden' }
    }
  }

  return true
})

export default router
