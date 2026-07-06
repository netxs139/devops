# 前端开发完整契约 (Frontend Development Contract)

> **SSOT (Single Source of Truth)**: 本文档是前端开发的**唯一权威规范**，覆盖技术栈、设计原则、工程规范、Vue 3 SFC 契约和组件目录。
>
> - 当进行任何 `devops_portal/frontend/` 相关的变更时，**必须**以本文档为准。
> - 旧版原生 JS 代码位于 `devops_portal/static/`，维护期间仍遵循本文档 §10（遗留层）的规定。
>
> *优先级*: 本文档 (业务真相) > `AGENTS.md` (AI调度) > 全局配置。

> [!IMPORTANT]
> **架构迁移状态**: 2026-06-20 起，前端正式启动从 Native JS + Web Components 向 **Vue 3 + Vite + TypeScript** 的渐进式重构。新功能**必须**在 `devops_portal/frontend/` 目录下开发，禁止向旧版 `static/js/` 新增功能页面。

______________________________________________________________________

## 1. 核心技术栈 (Technology Stack) [CANONICAL]

| 层级 | 技术选型 | 版本锚定 |
| :--- | :--- | :--- |
| **前端框架** | Vue 3（Composition API + `<script setup>`） | `^3.5.x` |
| **构建工具** | Vite | `^6.0.x` |
| **开发语言** | TypeScript（`strict: true`） | `^5.7.x` |
| **UI 组件库** | Naive UI（Light Theme，企业品牌色定制） | `^2.39.x` |
| **图表引擎** | ECharts 5 + vue-echarts | `^5.5.x` |
| **状态管理** | Pinia（Composition Store 风格） | `^2.2.x` |
| **客户端路由** | Vue Router 4（History Mode） | `^4.4.x` |
| **包管理器** | pnpm | `^9.0.x` |
| **图标库** | @vicons/ionicons5（按需导入） | `^0.12.x` |
| **HTTP 客户端** | Axios（封装于 `utils/request.ts`） | `^1.7.x` |
| **代码规范** | ESLint v9 Flat Config + Prettier + Stylelint | 见 §6 |
| **组合式 API** | VueUse | `^10.9.x` |
| **日期时间** | Day.js | `^1.11.x` |
| **请求缓存** | TanStack Query (Vue Query) | `^5.0.x` |
| **测试框架** | Vitest (单元/组件) + Playwright (E2E) | `^1.0.x` |

### 1.1 目录布局

```
devops_portal/frontend/
├── index.html                  # Vite 入口 HTML（含 CSP Meta）
├── vite.config.ts              # Vite 配置：Proxy + 别名 + 构建输出
├── tsconfig.json               # TypeScript strict 模式
├── eslint.config.js            # ESLint Flat Config (v9)
├── .stylelintrc.json           # Stylelint 规范
├── package.json
└── src/
    ├── main.ts                 # 应用入口（注册 Pinia/Router/指令）
    ├── App.vue                 # 根组件（Naive UI 全局配置）
    ├── types/
    │   └── api.d.ts            # 后端 Pydantic Schema 强类型镜像
    ├── store/
    │   ├── auth.ts             # JWT 解析、权限判定、数据隔离作用域
    │   └── notification.ts     # SSE 实时通知流管理
    ├── utils/
    │   └── request.ts          # Axios 封装（Correlation-ID + 401 拦截）
    ├── router/
    │   └── index.ts            # 路由表 + beforeEach RBAC 守卫
    ├── directives/
    │   └── permission.ts       # v-permission 按钮级鉴权指令
    ├── layouts/
    │   └── DashboardLayout.vue # 主应用布局（侧边栏 + 顶部栏 + 内容区）
    ├── views/                  # 页面级视图（路由节点）
    └── components/             # 共享业务组件
```

### 1.2 强制依赖约束 (Dependency Mandates)

为防止自造轮子或引入冗余依赖，前端开发过程中必须严格遵循以下约束：

1. **包管理器约束**：必须通过 **pnpm** 进行依赖管理（利用其硬链接与严格的扁平化隔离机制消除依赖幽灵），且禁止在 Vue 3 核心工程中使用 `npm` 安装依赖。
1. **工具库收敛**：防抖、节流、ResizeObserver、LocalStorage 读写等通用功能，**必须**使用 [VueUse](https://vueuse.org/)，严禁在 `utils/` 目录下自行封装低效冗余代码。
1. **日期处理**：统一使用 [Day.js](https://day.js.org/) 处理时间格式化与解析。**严禁**引入臃肿的 `moment.js` 以控制打包体积。
1. **请求缓存管理**：对于高频轮询、请求重试、缓存失效处理等场景，强烈推荐采用 **TanStack Query (Vue Query)**，将 API 请求相关的 isLoading/isError 状态从 Pinia 中彻底剥离，使 Pinia 仅专注于纯粹的全局业务状态（如 Auth、Notification）。
1. **自动化测试**：核心业务逻辑的单元测试必须基于 **Vitest**，端到端 (E2E) 测试基于 **Playwright**。

______________________________________________________________________

## 2. 视觉设计原则 (Design Directives)

### 2.1 主题：企业级白底黑字

**严禁引入暗黑模式。** Naive UI 主题固定为 Light Theme，配合企业品牌色系。

| 角色 | 色值 | CSS Token | 说明 |
| :--- | :--- | :--- | :--- |
| 主色 | `#1A56DB` | `--color-primary` | 企业深蓝 |
| 主色 Hover | `#1E4DB7` | `--color-primary-hover` | |
| 主色浅背景 | `#EFF6FF` | `--color-primary-light` | 选中态底色 |
| 成功 | `#10B981` | `--color-success` | |
| 警告 | `#F59E0B` | `--color-warning` | |
| 错误 | `#EF4444` | `--color-error` | |
| 信息 | `#0EA5E9` | `--color-info` | |
| 文字主色 | `#111827` | `--color-text-primary` | |
| 文字次色 | `#6B7280` | `--color-text-secondary` | |
| 文字三级 | `#9CA3AF` | `--color-text-tertiary` | |
| 边框 | `#E5E7EB` | `--color-border` | |
| 页面背景 | `#F9FAFB` | `--color-bg-base` | |
| 卡片背景 | `#FFFFFF` | `--color-bg-card` | |

> ⚠️ **绝对红线**：组件内部 CSS **严禁**硬编码 Hex 颜色值，必须使用 `var(--...)` 引用上表中的 Design Tokens。

### 2.2 字体与间距

- **字体栈**：`'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`（已在 `App.vue` 全局注入）
- **间距体系**：`--space-1(4px)` / `--space-2(8px)` / `--space-3(12px)` / `--space-4(16px)` / `--space-6(24px)` / `--space-8(32px)`
- **圆角**：`--radius-sm(4px)` / `--radius-md(6px)` / `--radius-lg(8px)` / `--radius-xl(12px)`

### 2.3 动效规范

- **过渡时长**：`--transition-fast(150ms)` / `--transition-base(200ms)` / `--transition-slow(300ms)`
- **降级强制**：所有核心动画必须添加 `@media (prefers-reduced-motion: reduce)` 降级
- **禁止**：`transition: all` 全量过渡；纯装饰性 `keyframes` 无降级方案

______________________________________________________________________

## 3. Vue 3 SFC 开发规范 (SFC Laws)

### 3.1 文件结构规范

- **强制使用 `<script setup>`**：禁止使用 Options API 或无 `setup` 的 `<script>` 块
- **块顺序**：`<script setup>` → `<template>` → `<style scoped>`
- **单文件大小**：单个 `.vue` 文件不超过 **300 行**。超出必须拆分为子组件

```vue
<!-- ✅ 正确示例 -->
<script setup lang="ts">
import { ref } from 'vue'
const count = ref(0)
</script>

<template>
  <div>{{ count }}</div>
</template>

<style scoped>
div { color: var(--color-text-primary); }
</style>
```

### 3.2 TypeScript 规范

- **零 `any`**：ESLint 规则 `@typescript-eslint/no-explicit-any: error`，无例外
- **Props 强类型**：必须使用 `defineProps<{ ... }>()` 泛型语法，不得使用 Runtime Props
- **Emits 强类型**：必须使用 `defineEmits<{ ... }>()` 泛型语法
- **类型导入**：使用 `import type { ... }` 区分类型导入与值导入

```typescript
// ✅ 正确
const props = defineProps<{ title: string; count?: number }>()
const emit = defineEmits<{ change: [value: string]; close: [] }>()

// ❌ 禁止
const props = defineProps({ title: String })
```

### 3.3 Pinia Store 规范

- **风格**：强制使用 **Composition Store** 风格（`setup()` 函数）
- **禁止**：Options Store 风格（`state: () => ({...})`）
- **命名**：`use{Feature}Store`，文件路径 `src/store/{feature}.ts`

### 3.4 路由守卫与权限

- **路由级鉴权**：通过 `meta.permissions: string[]` 声明路由所需权限，由 `router/index.ts` 的 `beforeEach` 统一拦截
- **按钮级鉴权**：使用 `v-permission` 指令，无权限时**直接从 DOM 移除**（非 CSS `display:none`）
- **数据隔离**：组件从 `authStore.dataScopeDepartment` / `authStore.dataScopeLocation` 读取作用域，动态过滤下拉选项或隐藏按钮

### 3.5 性能与内存安全 (Performance & Memory Safety) [MANDATORY]

- **虚拟滚动**：所有可能超过 200 条数据的表格 (`n-data-table`) 与树形组件 (`n-tree`)，必须开启 `virtual-scroll`。
- **销毁机制**：ECharts 图表实例、定时器 (`setInterval`)、自定义原生事件监听器，必须在 `onBeforeUnmount` 中显式释放，严防内存泄漏。
- **逻辑抽离**：单个 `.vue` 文件的 `<script setup>` 严禁超过 400 行，复杂业务状态机（如分发链路、License 校验）必须抽离至 `composables/` 中纯 TS 实现。
- **样式覆盖**：修改 Naive UI 默认样式必须优先使用 `theme-overrides`，严禁滥用 `:deep()` 强行修改底层内置 class。

### 3.6 前端 UX 的异步感知 (UX Asynchronous Awareness)

- **AI 降级适配**：为配合 LLM 降级，前端 Vue 组件的开发规范必须同步更新：对于含有 AI 模块的页面，**绝对禁止**使用全屏 Loading，应采用局部骨架屏 (Skeleton) 或内联加载提示，确保用户在等待期间仍可浏览其他内容。

______________________________________________________________________

## 4. 安全开发规范 (Security Laws) [等保三级]

### 4.1 请求安全

| 要求 | 实现位置 | 说明 |
| :--- | :--- | :--- |
| Correlation-ID 注入 | `utils/request.ts` 请求拦截器 | UUID v4，每次请求自动生成 |
| JWT 自动携带 | `utils/request.ts` 请求拦截器 | `Authorization: Bearer <token>` |
| 401 自动跳转 | `utils/request.ts` 响应拦截器 | 清除 Token 并跳转 `/login` |
| CSP 声明 | `index.html` meta 标签 | 限制外部资源加载来源 |
| X-Frame-Options | `index.html` meta 标签 | 防止 iframe 嵌入攻击 |

### 4.2 XSS 防御

- **禁止 `v-html`**：ESLint 规则 `vue/no-v-html: error` 全局启用
- **动态内容渲染**：一律通过 Vue 模板插值 `{{ }}` 或 `v-text`，框架自动转义

### 4.3 权限穿透防御

- `v-permission` 指令采用 **DOM 物理移除**而非 CSS 隐藏，防止前端 UI 欺骗
- **申明**：前端权限控制为**展示层防御**，所有敏感操作的最终权限校验在**后端 API 层**完成

______________________________________________________________________

## 5. API 接口契约对齐 (API Contract Alignment)

1. **类型定义唯一入口**：所有前后端共享类型定义于 `src/types/api.d.ts`，与后端 `devops_portal/schemas.py` 字段名**完全镜像对齐**（`snake_case`）
1. **禁止字面量硬编码**：严禁在组件/服务层直接硬编码 API 响应结构
1. **HTTP 客户端统一入口**：所有 API 调用必须通过 `src/utils/request.ts` 导出的 `http` 对象，严禁直接使用 `axios` 或 `fetch`
   - **合法豁免端点**：`POST /auth/login`。该接口是 Bearer Token 的唯一来源，调用时尚无 token 可注入。`LoginView.vue` 允许直接使用 `axios` 并须在导入处注明 `[CONTRACT EXEMPTION]` 标注。
1. **响应类型声明**：调用 API 时必须声明返回类型泛型：`http.get<TestSummary>('/test-summary')`

______________________________________________________________________

## 6. 工程化与代码规范 (Tooling & Linting)

### 6.1 Lint 工具链

| 目标 | 工具 | 配置文件 | 运维指令 |
| :--- | :--- | :--- | :--- |
| TypeScript / Vue | ESLint v9 Flat Config | `eslint.config.js` | `just frontend-lint` |
| CSS / `<style>` | Stylelint | `.stylelintrc.json` | `npm run lint:style` |
| 代码格式化 | Prettier（通过 ESLint 集成） | `eslint.config.js` | `npm run lint` |
| 类型检查 | `vue-tsc --noEmit` | `tsconfig.json` | `npm run typecheck` |

### 6.2 门禁集成

- `just verify` 已集成 `frontend-lint`（`npm run lint && npm run typecheck`）
- 所有 CI 合并请求必须通过 `frontend-lint` 门禁才可合并

### 6.3 开发工作流

```bash
# 启动热更新开发服务器（联调 FastAPI:8000）
just frontend-dev

# 构建产物到 devops_portal/static/vue-assets/
just frontend-build

# 全量 Lint + 类型检查
just frontend-lint
```

______________________________________________________________________

## 7. 前端功能全景地图 (Frontend Dashboard Map) [MANDATORY PRE-CHECK]

任何涉及前端视图（`src/views/` 或旧版 `dashboard/pages`）的新增或修改任务，**必须首先**在该地图中确认 Index 与 Domain 的唯一性，严禁索引冲突。

| Index | Page Module | Domain | Key Indicators |
| :--- | :--- | :--- | :--- |
| **0** | **Quality_Monitor** | **底座/质量** | **同步成功率, 审计异常, 数据新鲜度** |
| 1 | Gitprime | 效能/代码 | 提交频率, 活跃开发人数, 影响度 |
| 2 | DORA_Metrics | 效能/标准 | 部署频率, MTTR, 变更为失效率 (V1) |
| 3 | Project_Health | 项目/全景 | 进度偏差, 资源饱和度, 里程碑风险 |
| 4 | Compliance_Audit | 安全/合规 | 密钥泄露, 仓库权限违规, 依赖漏洞 |
| 5 | ABI_Analysis | 技术/二进制 | 接口兼容性突破, 符号导出变化 |
| 6 | User_Profile | 人员/画像 | 技能雷达, 贡献分布, 异常加班预警 |
| 7 | Capitalization_Audit | 财经/资本化 | 研发/资本化投入比例, 工时对齐 |
| 8 | Shadow_IT | 治理/发现 | 未注册系统探测, 资产黑户统计 |
| 9 | Talent_Radar | 人员/储备 | 骨干流失风险, 关键路径依赖 (Bus Factor) |
| 10 | Metrics_Guard | 质量/拦截 | 指标 3-Sigma 离群值标记 |
| 11 | Unified_Activities | 研发/全踪 | 跨源动态流 (MR, Issue, Commit) |
| 12 | Work_Items | 协作/任务 | 迭代进度, 燃尽图, 前置周期时间 |
| 13 | Entity_Alignment | MDM/对齐 | 跨系统实体映射完整度 (MDM Bridge) |
| 14 | Delivery_Costs | 成本/FinOps | 单次交付成本, 资源账单分摊 |
| 15 | Metadata_Governance | 治理/标准 | 元数据覆盖率, 字典完整性 |
| 16 | Michael_Feathers_Code_Hotspots | 技术/重构 | 变更频率 vs 复杂度散点图 |
| 17 | SPACE_Framework | 人员/体验 | 开发者满意度, 研发心流, 专注时长 |
| 18 | Value_Stream | 价值/过程 | 价值周转率, 瓶颈探测, 触点损耗 |
| 19 | Strategic_Executive_Cockpit | 决策/大屏 | 集团级核心指标聚合 (Executive Only) |
| 20 | Nexus_FinOps | 治理/资产 | 制品库存储分布, 僵尸包回收建议 |
| 21 | DORA_Refined | 效能/标准 | 变更前置时间 (分段), 部署频率 (V2) |
| 22 | Code_Traceability | 效能/溯源 | 单项 Issue->Commit->MR 血缘追踪 |
| 23 | Radar_Intelligence | 效能/聚合 | 流动效率, 协同质量, 安全态势雷达 |
| 24 | Service_Desk | 服务/工单 | 客户满意度, MTTR |

**强制开发规程**：

1. **查表**：开发前必须核查上表，确保 Index 不冲突
1. **更新**：若新增页面，必须同步在此表中注册占位，并在 `router/index.ts` 增加对应路由
1. **视觉**：必须引用 `--color-*` Design Tokens，保持企业白色主题归一化

______________________________________________________________________

## 8. Vue 3 核心组件目录 (Component Registry)

> **SSOT**：本节定义 `src/components/` 及 `src/views/` 下核心组件的行为契约。

### 8.1 路由视图（`src/views/`）

| 视图文件 | 路由路径 | 权限要求 |
| :--- | :--- | :--- |
| `LoginView.vue` | `/login` | 公开 |
| `LoginCallback.vue` | `/login/callback` | 公开（OAuth 回调） |
| `HomeView.vue` | `/home` | 已登录 |
| `QualityView.vue` | `/quality` | `rpt:quality:view` |
| `RadarView.vue` | `/radar` | `rpt:quality:view` |
| `BoardView.vue` | `/board` | 已登录 |
| `TestCaseView.vue` | `/test-cases` | 已登录 |
| `ServiceDeskView.vue` | `/service-desk` | 已登录 |
| `AdminView.vue` | `/admin` | `USER:MANAGE` |

### 8.2 核心 SFC 组件

| 组件文件 | 旧版 Web Component | 核心改动 |
| :--- | :--- | :--- |
| `Pulse.vue` | `sys_pulse.component.js` | 心情反馈 + PulseStatus 校验 |
| `Board.vue` | `pm_iteration_board.component.js` | NGrid + HTML5 Drag/Drop |
| `TestCaseDetail.vue` | `qa_test_case_detail.component.js` | NDrawer 承载，完全解耦 DOM |
| `TestCaseForm.vue` | `qa_test_case_form.component.js` | Naive UI 动态表单 + 强校验 |
| `TicketForm.vue` | `sd_request_form.component.js` | 三层映射：产品 ID 联动表单 |
| `Radar.vue` | `radar-viz.js` + `qa_radar.js` | ECharts 5 全量重写，下钻路由 |

______________________________________________________________________

## 9. 交付前检查清单 (Pre-Delivery Checklist) [MANDATORY]

### 合规性

- [ ] Dashboard Map 已查阅，Index 无冲突（或已完成注册）
- [ ] `src/types/api.d.ts` 中已定义本次涉及的所有 API 响应类型
- [ ] API 字段命名与 Python ResponseSchema 镜像对齐（`snake_case`）
- [ ] `just frontend-lint` 零报错、零 TS 类型错误

### 安全性（等保三级）

- [ ] 无 `v-html` 使用（ESLint 自动拦截）
- [ ] 无 `any` 类型（ESLint 自动拦截）
- [ ] 无硬编码 Hex 颜色（Stylelint 自动拦截）
- [ ] 敏感操作按钮已加 `v-permission` 指令

### 视觉质量

- [ ] 无暗黑模式相关代码（`prefers-color-scheme: dark` 等）
- [ ] 所有 ECharts 容器高度明确（非零），用 `getBoundingClientRect().height > 0` 验证
- [ ] Hover 状态有清晰视觉反馈，过渡时长 150-300ms
- [ ] 响应式在 375px / 768px / 1440px 均正常

### 可访问性

- [ ] 所有图片有 `alt` 属性
- [ ] 色彩不是唯一信息载体（辅以文字或图标）
- [ ] `prefers-reduced-motion` 媒体查询已考虑

______________________________________________________________________

## 10. 遗留层维护规范 (Legacy: Native JS / Web Components)

> 旧版代码位于 `devops_portal/static/js/`，**仅接受 Bug 修复，禁止新增功能页面**。

- 旧版 CSS 规范（Apple Style 变量、BEM 命名）继续有效，详见本文档历史版本
- 旧版 Web Components 规范（Shadow DOM、CustomEvent）继续有效，仅用于现有组件维护
- 格式化工具：`djhtml`（HTML/Jinja2）+ `mdformat`（Markdown），不引入 Node.js Prettier

______________________________________________________________________

*最后更新：2026-06-20（Vue 3 + Vite + TypeScript 技术栈迁移）*
*由 Antigravity-AI 生成并维护*
