# 前端开发完整契约 (Frontend Development Contract)

> **SSOT (Single Source of Truth)**: 本文档是前端开发的**唯一权威规范**，覆盖设计原则、样式规范、脚本规范、Web Components 规范和组件契约。
>
> - 当进行任何 `devops_portal/static/` 相关的变更时，**必须**以本文档为准。
>
> *优先级*: 本文档 (业务真相) > `AGENTS.md` (AI调度) > 全局配置。

______________________________________________________________________

## 1. 核心设计理念 (Core Design Directives)

1. **去框架化工程化**：不使用 React/Vue，但通过模块化、服务层分层等手段达到同等代码复用与维护能力。
1. **Apple Style Premium UI**：视觉效果必须对齐苹果公司（Apple Inc.）设计语言。优先采用浅色系、高通透感、大幅留白的视觉体验。
1. **逻辑与样式解耦**：CSS 只负责视觉，JS 只负责逻辑，两者通过 `js-` 类名和 `dataset` 桥接，严禁混用。
1. **设计令牌驱动**：所有审美标准必须通过 Design Tokens 实现，禁止硬编码视觉参数。
1. **组件工程**：优先使用 Web Components (Shadow DOM) 实现高内聚组件。
1. **通信机制**：跨组件通信通过 `CustomEvent` 实现，严禁随意污染全局 `window` 命名空间。

______________________________________________________________________

## 2. 苹果设计专项规范 (Apple-Style HIG for Web)

### 2.1 材质与通透感 (Material & Transparency)

- **玻璃拟态 (Glassmorphism)**：核心卡片和导航组件优先使用玻璃质感。
  - **规范**：`backdrop-filter: blur(20px) saturate(180%);`
  - **背景**：半透明白色 `rgba(255, 255, 255, 0.72)`
  - **变量引用**：`var(--glass-bg)` — 严禁硬编码上述 Hex/rgba 值。
- **连续圆角 (Continuous Curves)**：
  - 小组件/按钮：`8px - 12px`
  - 内容卡片：`16px - 24px`
  - 模态框/认证卡：`24px` 以上

### 2.2 精准色阶 (Neutral Grayscale)

| 角色 | 值 | 变量 |
| :--- | :--- | :--- |
| 全局背景 (Base) | `#F5F5F7` (Apple Gray) | `var(--bg-base)` |
| 文字 Primary | `#1D1D1F` | `var(--text-primary)` |
| 文字 Secondary | `#86868B` | `var(--text-secondary)` |
| 行动项 (CTA) | `#0071E3` (Apple Blue) | `var(--primary-color)` |

> ⚠️ **严禁**在新文件中硬编码上述 Hex 颜色值，必须使用对应的 CSS 变量。

### 2.3 空间与呼吸感 (Space & Air)

- **8px 栅格**：所有 Padding 和 Margin 必须是 8 的倍数（8, 16, 24, 32, 48, 64）。
- **底部安全区**：所有独立内容页面底部强制增加 `120px` 透明占位，确保滚动体验从容感。
- **视口缓冲区**：页面顶部内容距离 Header 必须保持至少 `40px - 60px` 的视觉缓冲区。

### 2.4 排版与动效

- **字体栈**：`-apple-system, BlinkMacSystemFont, "Inter", "Outfit", sans-serif`
- **阴影层级**：
  - Soft（基础边界）：`0 4px 6px -1px rgba(0,0,0,0.01)`
  - Deep（悬浮/弹出）：`0 20px 40px rgba(0,0,0,0.04)`
- **滚动条**：必须同步 `main.css` 中的极细圆角 Apple 风格滚动条，禁止使用系统默认宽度。
- **动效曲线**：`cubic-bezier(0.4, 0, 0.2, 1)` 或弹性 `cubic-bezier(0.175, 0.885, 0.32, 1.275)`。

______________________________________________________________________

## 3. 样式规范 (CSS & Visuals)

### 3.1 样式管理红线

- **严禁内联**：禁止在 HTML 标签中编写超过 2 项属性的内联样式。
- **样式回收**：凡在 3 处以上重复使用的布局，必须在 `css/main.css` 中提取为 `.u-` 原子类或 `.g-` 全局类。

### 3.2 Prefix-BEM 命名体系

所有类名遵循：`.前缀-组件名__子元素--修饰符`

**业务域前缀 (Business Prefixes)**：

| 前缀 | 业务域 |
| :--- | :--- |
| `sd-` | Service Desk |
| `adm-` | Administration |
| `pm-` | Project Management |
| `qa-` | Quality Assurance |
| `rpt-` | Report |
| `sys-` | System |

**功能性前缀 (Functional Prefixes)**：

| 前缀 | 用途 | 示例 |
| :--- | :--- | :--- |
| `u-` | Utility 原子类 | `.u-mt-20` |
| `g-` | Global 全局组件/材质 | `.g-glass-panel` |
| `is-` / `has-` | State 状态 | `.is-active`, `.is-loading` |

### 3.3 命名速查表（前端特有）

| 维度 | 规范格式 | 示例 |
| :--- | :--- | :--- |
| JS 脚本文件名 | `{prefix}_{resource}.js` | `sd_ticket_service.js` |
| 组件文件名 | `{prefix}_{name}.component.js` | `sd_ticket_card.component.js` |
| 自定义 HTML 标签 | `<{prefix}-{name}>` | `<sd-priority-badge>` |
| CSS 类名 | `.prefix-component__element` | `.sd-table__cell` |
| DOM 逻辑钩子 | `.js-{action}-{resource}` | `.js-delete-ticket` |
| 数据属性 | `data-{key}="{value}"` | `data-ticket-id="123"` |

> 全链路命名规范（含数据库、API、后端文件）参见 `contexts.md §11.2`。

______________________________________________________________________

## 4. 脚本规范 (JavaScript)

### 4.1 模块架构 (Service-UI Pattern)

- **ES6 Modules**：强制使用 `type="module"`。
- **分层设计**：`*_service.js`（Fetch 数据）↔ `*_handler.js`（DOM/UI 交互）。

### 4.2 DOM 操作规范

- **逻辑钩子**：使用以 `js-` 开头的类名作为 JS 选择器，严禁用样式类做钩子。
- **状态驱动**：通过操作 `dataset` 或 `classList` 切换 UI，禁止修改 `.style.xxx`。
- **事件委派**：动态生成的元素必须在父容器上联合 `e.target.closest()` 监听。

### 4.3 安全与性能

- **XSS 防御**：渲染动态内容严禁 `innerHTML`，强制使用 `textContent` 或 `<template>`。
- **异步体感**：必须提供骨架屏或 `is-loading` 状态。

### 4.4 文件大小与拆分

- **300 行定律**：单个 JS/CSS/HTML 文件严禁超过 300 行，超出必须拆分。可通过 `scripts/lint_frontend.py` 自动检查。
- **拆分策略**：Service 层与 Handler 层必须分离；单个 Handler 超过 200 行时按功能区域拆分。

### 4.5 错误处理规范

- **Fetch 统一处理**：所有 `fetch()` 调用必须包含 `try-catch`，并检查 `response.ok`，严禁忽略网络错误。
- **用户反馈**：错误发生时必须通过 Toast 或内联提示告知用户，严禁静默失败。
- **控制台日志**：`catch` 块必须 `console.error()` 记录完整上下文（URL、参数、错误对象），严禁空 `catch`。

______________________________________________________________________

## 5. Web Component 开发规约

### 5.1 核心标准

- **命名规范**：
  - **强制前缀**：必须使用业务域前缀或全局前缀（如 `<sd-card>`, `<g-button>`）。
  - **横杠原则**：组件名必须包含至少一个连字符 `-`（浏览器原生要求）。
- **Shadow DOM 封装**（强制）：
  - 所有组件必须使用 `this.attachShadow({mode: 'open'})` 开启隔离罩。
  - 组件内部样式不应受外部影响，内部装饰优先使用宿主选择器 `:host`。
- **样式集成**：
  - **禁止硬编码颜色**：组件内部 CSS 必须使用 `var(--...)` 引用 `main.css` 中定义的 Design Tokens。
  - **通透感适配**：若组件包含背景，需支持 `glassmorphism` 样式变量。

### 5.2 数据与交互 (Props & Events)

- **属性传入 (Attributes)**：配置信息（状态、大小、颜色主题）通过 HTML 属性传入。
- **事件驱动 (Events)**：组件内部状态变化必须通过 `new CustomEvent()` 向上冒泡，严禁在组件内部直接修改外部变量。
- **反应式更新**：利用 `attributeChangedCallback` 监听属性变化并按需局部更新 DOM。

### 5.3 文件组织

- **存储路径**：`devops_portal/static/js/components/`
- **命名格式**：`{prefix}_{name}.component.js`
- **单文件组件**：每个文件包含一个完整类定义和 `customElements.define` 注册逻辑。

### 5.4 开发规范 (Laws)

1. **事件解耦**：禁止在组件内部直接修改全局 `state` 或调用 `Api`（自取数据的全局组件如 `adm-product-selector` 除外）。
1. **属性映射**：`attributeChangedCallback` 必须能实时反映 `_state` 的变化。
1. **命名空间**：事件名称使用 kebab-case（如 `select-case`），避免与原生事件冲突。
1. **影子穿透**：组件内部样式尽量使用 CSS Variables 以支持主题切换。

______________________________________________________________________

## 6. 核心 Web Components 目录 (Component Registry)

> **SSOT**：本节定义 `devops_portal/static/js/components/` 下核心组件的行为契约，包括输入属性、数据属性及外发事件。

### 6.1 `adm-product-selector` — 产品/部门切换器

- **选择器**: `<adm-product-selector>`
- **输入属性**:
  - `selected-type`: `'product'` | `'org'`
  - `selected-id`: 选中项的物理 ID
- **外发事件**:
  - `change`: 切换类型或选择项时触发。`detail: { type: string, id: string }`

### 6.2 `qa-test-case-card` — 测试用例行

- **选择器**: `<qa-test-case-card>`
- **数据属性**: `data` — 传入完整测试用例对象
- **视觉反馈**: `[active]` 属性存在时显示选中高亮
- **外发事件**:
  - `select-case`: 点击整行时触发。`detail: { item: Object }`

### 6.3 `qa-test-case-detail` — 测试用例详情面板

- **选择器**: `<qa-test-case-detail>`
- **数据属性**: `data` — 传入测试用例详情
- **外发事件**:
  - `execute`: 点击执行按钮时触发。`detail: { iid: number, result: string, report: string }`
  - `report-bug`: 点击提单按钮时触发。`detail: { iid: number }`

### 6.4 `sys-pulse` — 系统监控波形图

- **选择器**: `<sys-pulse>`
- **输入属性**:
  - `type`: 监控类型（`cpu`, `memory`, `disk`）
  - `color`: 曲线颜色
- **数据注入**: `pushData(value)` — 实例方法，用于推入实时监测值

### 6.5 `qa-radar-drawer` — 效能详情抽屉

- **选择器**: `<qa-radar-drawer>`
- **数据属性**: `data` — 传入列表数据 `list[RadarDetailItem]`
- **输入属性**:
  - `title`: 抽屉标题（如 "秒批 MR 详情"）
  - `opened`: 布尔值，控制抽屉开关
- **外发事件**:
  - `close`: 点击遮罩或关闭按钮时触发

______________________________________________________________________

## 7. 前端工具与格式化 (Tooling & Formatting)

本项目拒绝引入 Node.js/Prettier 体系，采用纯 Python 生态工具：

| 目标文件 | 工具 | 参数 |
| :--- | :--- | :--- |
| HTML/Jinja2 | `djhtml` | `--tabwidth 2` |
| Markdown | `mdformat` | — |
| JS/CSS | IDE 内置 + AI 样式自律 | Apple Style 规范 |

上述工具已集成至 `pre-commit` 门禁，确保入库代码 100% 物理对齐。

______________________________________________________________________

## 8. 前端功能全景地图 (Frontend Dashboard Map) [MANDATORY PRE-CHECK]

任何涉及前端 `dashboard/pages` 的新增或修改任务，**必须首先**在该地图中确认 Index 与 Domain 的唯一性，严禁索引冲突。

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

**强制开发规程**：

1. **查表**：开发前必须核查上表，确保 Index 不冲突。
1. **更新**：若新增页面，必须同步在此表中注册占位。
1. **视觉**：必须引用 `--glass-bg` 等 Apple Style 变量，保持视觉归一化。

______________________________________________________________________

## 9. API 接口契约对齐 (API Contract Alignment)

如果新页面需要调用后端 API（`fetch()`），则：

1. **先查阅或创建**对应的 Pydantic `ResponseSchema`（位于 `devops_portal/schemas.py` 或独立 `schemas_*.py`）。
1. 前端 JS 中的字段名**必须**与 Python Schema 字段名**镜像对齐**（同名、同含义）。
1. 禁止在 JS 中用字面量硬编码 API 响应结构，必须有 Python 侧 Schema 作为"物理契约"。

______________________________________________________________________

## 10. 交付前检查清单 (Pre-Delivery Checklist) [MANDATORY]

### 合规性

- [ ] Dashboard Map 已查阅，Index 无冲突（或已完成注册）
- [ ] CSS 颜色全部通过变量定义，无硬编码 Hex 泄漏
- [ ] API 字段命名与 Python ResponseSchema 镜像对齐

### 可视容器验证 (DOM Smoke Test)

- [ ] 所有图表容器（`canvas`、`svg`、`div`）在 CSS 中已明确设置高度
- [ ] Chart.js / SVG / Canvas 容器高度不为零（用 DevTools 验证 `getBoundingClientRect().height > 0`）
- [ ] 若容器的 `height` 依赖父级 `flex`，父级已明确设置 `min-height`

### 视觉质量

- [ ] 无 emoji 作为 UI 图标（使用 SVG 替代）
- [ ] 所有可点击元素有 `cursor: pointer`
- [ ] Hover 状态有清晰视觉反馈，过渡时长 150-300ms
- [ ] 响应式在 375px / 768px / 1440px 均正常

### 可访问性

- [ ] 所有图片有 `alt` 属性
- [ ] 色彩不是唯一的信息载体（辅以文字或图标）
- [ ] `prefers-reduced-motion` 已考虑（核心动画添加媒体查询降级）
