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
    children: [
      {
        path: 'home',
        name: 'Home',
        component: HomeView,
        meta: { title: '首页总览' },
      },
      {
        path: 'quality',
        name: 'Quality',
        component: QualityView,
        meta: {
          title: '质量监控',
          permissions: ['rpt:quality:view'],
        },
      },
      {
        path: 'radar',
        name: 'Radar',
        component: RadarView,
        meta: {
          title: 'Traceability 雷达',
          permissions: ['rpt:quality:view'],
        },
      },
      {
        path: 'board',
        name: 'Board',
        component: BoardView,
        meta: {
          title: '迭代看板',
          permissions: ['rpt:quality:view'],
        },
      },
      {
        path: 'test-cases',
        name: 'TestCase',
        component: TestCaseView,
        meta: {
          title: '测试用例',
          permissions: ['rpt:quality:view'],
        },
      },
      {
        path: 'service-desk',
        name: 'ServiceDesk',
        component: ServiceDeskView,
        meta: { title: '服务台' },
      },
      {
        path: 'admin',
        name: 'Admin',
        component: AdminView,
        meta: {
          title: '系统管理',
          permissions: ['USER:MANAGE'],
        },
      },
    ],
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
