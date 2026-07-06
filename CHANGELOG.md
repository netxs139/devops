# 修订记录 (Changelog)

所有对 DevOps Data Application Platform 的重要更改都将记录在此文件中。

## [Unreleased]

- **v3.0 阶段三与阶段四：BI 度量中心大屏与 Vue 前端重构闭环 (2026-07-06)**:

  - **Zero-Sync Direct Query**: 摒弃 Python 层统计，纯利用 Pydantic + FastAPI 提供透明数据通道，由 dbt-postgres 计算 marts 宽表。
  - **只读模型**: 在 `devops_collector/models/marts.py` 中建立针对 DORA 及项目级指标宽表的视图级 SQLAlchemy 映射 (`viewonly=True`)。
  - **Vue 3 独立渲染**: 彻底废弃 Streamlit Iframes，基于 Naive UI 与 ECharts 构建 `DoraMetricsView.vue` 和 `GitprimeView.vue`，实现数据和视图的双向解耦。
  - **防穿透屏障与卸载治理 (BI 4大防线)**:
    - **后端 TTLCache**: 在 `bi_metrics_router.py` 中应用了 `cachetools.TTLCache` 建立 15 秒微级内存屏障，保护底层 DB 免受轮询穿透。
    - **前端 Visibility 探测**: 利用 VueUse `useDocumentVisibility` 实现页面处于后台时的自动轮询挂起，节约带宽与性能。
    - **组件资源卸载**: 通过 `onBeforeUnmount` 强制释放 ECharts 实例并清空 `setInterval` 句柄，消除内存泄漏风险。
    - **渐进式骨架屏**: 前置骨架渲染提升 LCP 体验。
  - **依赖瘦身与构建优化 (Gold Triangle)**:
    - 移除了冗余的 `streamlit`、`plotly` 等重依赖。
    - **构建提速**: 在 Vite 生产模式下完全剥离 `vue-tsc`，开启 TS 增量编译 `incremental: true`，结合 `vite-plugin-checker` 异步校验类型错误。
  - **架构加固**: 修复 `docker-compose.yml` 跨库模块 (`identity_module`) 卷挂载路径缺失的 Bug，消除 API 容器重启死锁；缩减 Worker 冗余副本数为 1。

- **Vue 3 前端重构阶段六：分析仪表盘与全地图路由注册 (2026-06-20)**:

  - **HomeView.vue**: 实现全域导航大厅，读取路由元数据 `meta.domain` 对所有可用业务域模块进行自动归类与卡片化展示，支持 hoverable 交互、300ms cubic-bezier 平滑过渡及 Naive UI 动态响应式栅格布局（NGrid 4列自适应）。

  - **QualityView.vue**: 交付质量监控大屏组件，包含 3 张核心度量卡片（同步成功率、审计异常数、数据新鲜度），右侧展示最新审计异常 Alert 告警列表（警告级别 NAlert）。

  - **PlaceholderView.vue**: 新建通用模块占位组件，从路由元数据 `meta.title` 和 `meta.domain` 动态拉取所处业务域和模块名称，显示优雅的“此模块正在建设中...” NEmpty 状态，并提供一键返回导航大厅的交互按钮。

  - **全地图路由注册**: 在 `router/index.ts` 中注册全量 24 模块路由（Index 0 - 23），将各占位页面无缝挂载为 `PlaceholderView`，并将 `QualityView` 和 `RadarView` 正式对齐至底座质量和效能溯源域，同时配置精细的 RBAC `meta.permissions` 校验数组与 `meta.domain` 侧边栏分组元数据。

  - **DashboardLayout.vue**: 重构侧边菜单动态生成逻辑，在 computed `menuOptions` 中根据路由配置和当前用户的权限过滤出可用页面，按 `meta.domain` 进行 Map 分组，构造 `type: 'group'` nested menu 结构进行侧边折叠渲染；同时实现顶部 Header 用户信息 department / location 物理数据作用域展示标签。

  - **工程门禁**: frontend-lint / typecheck / build 全量成功，`just frontend-build` 33s 完成 3487 modules 编译并合并静态制品输出；pytest 398passed。commit: `3dcb1a6`。

- **Vue 3 前端重构阶段五：服务台域 SFC + 手动容灾工具 (2026-06-20)**:

  - **ServiceDeskView.vue**: 双 Tab 工单列表（我的工单/全量反馈），3 张统计 NStatistic 卡片（累计/待处理/已解决），状态点徽章（CSS `::before` 彩点 + 脉冲光晕），工单行内状态流转按钮（待处理→处理中→解决→关闭 四段 PATCH），驳回 Modal（拉取 `/service-desk/track/{id}` 获取 gitlab_issue_iid → POST `/service-desk/tickets/{iid}/reject`），视图切换（列表 ↔ 表单）。

  - **TicketForm.vue**: 三层 MDM 联动面板（业务产品 → 归属项目 → 受理仓库 `lead_repo_id` 实时解析），Bug/需求双段式切换（iOS-style Segmented Control），Naive UI `NUpload` 自定义上传（`UploadCustomRequestOptions` 原生类型对齐，`file.file` null 守卫），Query 参数预填（从 `TestCaseView.vue` 缺陷跳转自动回填标题/步骤/关联用例）。

  - **TestCaseView.vue**: 打通 `@report-bug` handler，通过 `router.push` 携带 `type/title/steps/ref_case_iid/product_id` 跳转至服务台自动填充创建工单。

  - **容灾工具**: `.agent/scripts/recovery.py` 实现 `save`（保存 `git diff` 补丁、`progress.txt`、`task.md`）与 `restore`（重放补丁还原工作区）；`justfile` 新增 `checkpoint` / `recover` 入口。

  - **类型治理**: `api.d.ts` 补全 `TicketStatus`（加入 `'opened'`）、`TicketType`、`Ticket`、`ServiceDeskBugSubmit`、`ServiceDeskRequirementSubmit` 与后端 Pydantic Schema 全字段对齐；ESLint 配置 Vue SFC 块启用 `@typescript-eslint/no-unused-vars`（`argsIgnorePattern: '^_'`），禁用冲突的基础 `no-unused-vars` 规则。

  - **Bug 修复**: `</Card>` → `</NCard>` 模板闭合错误（Vite 编译 `Invalid end tag` 崩溃）；`catch (err: any)` → `catch (err: unknown)` 全面替换。

  - **工程门禁**: ESLint 0 errors，TypeScript 0 errors，`just frontend-build` 3482 modules，`pytest tests/unit/test_portal/test_service_desk_router.py` 8 passed。commit: `feab822`。

  - **HTML5 原生 Drag/Drop 看板**: `Board.vue` 实现 4 列看板（待办/进行中/测试中/已完成），支持跨列原生拖拽，WIP 超限动态闪烁警告，优先级彩条（P0=红/P1=橙/P2=蓝），Story Points 及 Assignee Avatar Chip。

  - **团队心情反馈 Pulse**: `Pulse.vue` 提供 5 种 Emoji 心情投票（🚀🔥😊😐😔），单次点击投票、再次点击撤回，localStorage 持久化（key: `pulse_<date>_<userId>`），弹跳动效，今日分布进度条，Mock 历史数据可视化。

  - **BoardView 页面组装**: Sprint 信息栏（名称/目标/日期区间）、线性进度条（完成率/剩余天数/待完成SP 三联统计），Board 主区 + Pulse 右侧面板响应式布局（>1280px 双栏，移动端堆叠）。

  - **类型补全**: `api.d.ts` 新增 `PulseEntry` 接口（localStorage 专用，含 `userId/emoji/date/ts` 字段）。

  - **工程门禁**: typecheck/ESLint 100% 通过，`just frontend-build` 2278 模块编译成功（`BoardView-CMIPCWia.js 10.12 kB`）。commit: `6042b9f`。

  - **测试用例管理控制台**: `TestCaseView.vue` 完整实现用例总览、多维度筛选（按状态、优先级、关键字）、用例新建入口及侧边执行控制台抽屉。

  - **用例详情与执行控制台**: `TestCaseDetail.vue` 与 `TestCaseForm.vue` 补全用例执行与录入组件，打通关联项目 GitLab ID 解析逻辑；`ProductSelector.vue` 提供按产品与组织部门的双轴上下文联动。

  - **Traceability 雷达与 VSM 看板**: `RadarView.vue` 支持按项目/天数筛选、度量指标卡片（平均评审等待时间、秒批率、漏洞数）下钻明细展示；`Radar.vue` 配合 ECharts 5 渲染协作雷达及 VSM 流水线耗时时序图。

  - **类型与规范治理**: 补全 `api.d.ts` 中的 `TestCase`, `TestSummary`, `RadarResponse` 等核心接口契约；修复所有 Vue 3 SFC 文件的 TS 类型报错与 ESLint/Stylelint 违规，成功通过 `just frontend-build` 生产环境制品打包。commit: `6d42799`。

- **Vue 3 前端重构阶段二：登录与鉴权体系 SFC 完全迁移 (2026-06-20)**:

  - **登录页 SFC 迁移**: `LoginView.vue` 实现密码登录（`URLSearchParams` 表单体）与 GitLab OAuth 跳转两种方式，错误信息模糊化符合等保三级要求。
  - **OAuth 回调处理**: `LoginCallback.vue` 截获后端重定向携带的 `access_token` query 参数，写入 Auth Store 后跳转至目标页。
  - **主壳与路由守卫**: `DashboardLayout.vue` 实现权限动态菜单过滤；`router/index.ts` 落地三段 `beforeEach` 守卫（未登录跳转、已登录回跳首页、`meta.permissions` OR 语义权限校验）。
  - **JWT 状态机**: `store/auth.ts` Pinia Composition Store 完整实现 JWT 解析、RBAC 判定、数据隔离作用域（department/location）及 `setToken`/`logout` 行为方法。
  - **Bug 修复**: 修复 import 语句断行错误与 `\3c` HTML 实体泄漏至 Vue 源码问题；补充 `api.d.ts` 缺失的 `AuthToken` 接口；落地 axios 合法豁免合约注释。commits: `d82e589`, `997c508`。

- **Vue 3 前端重构阶段一：工程脚手架与规范初始化 (2026-06-20)**:

  - **Vue 3 SFC 脚手架底座**: 在 `devops_portal/frontend/` 建立了以 Vue 3 + Vite + TypeScript + Naive UI + ECharts 5 为技术栈的前端开发底座，支持 Composition API（`<script setup>`）及严格类型校验。
  - **等保三级安全防线**: 配置 `index.html` 强制 CSP 声明与 `X-Frame-Options: SAMEORIGIN` 阻断点击劫持；启用 Flat ESLint 配置中的 `vue/no-v-html` 以禁止 `v-html` 输出，防范 XSS 注入。
  - **网络与权限链路规范**: 统一封装 `request.ts`，自动处理 JWT 校验与每次请求重新生成并随 Header 携带的随机 `Correlation-ID` 以追踪全链路日志；实现 `v-permission` 自定义指令物理移除无权限 DOM 以阻止展示层伪造。
  - **Vite 自动化集成构建**: 配置 `justfile` 新增 `frontend-dev/build/lint` 全套工作流命令，支持将构建的静态资源与 HTML 模板自动输出并挂载到后端的静态托管层 `devops_portal/static/`。

- **CI 流水线原生化与高阶安全审计重构 (2026-06-15)**:

  - **原生并行与缓存加速**: 重构 `.gitlab-ci.yml`，彻底剥离 `gatekeeper.py` 调度，引入 Stage 原生并行。设定 `${CI_COMMIT_REF_SLUG}` 分支级全局缓存，并全面绑定内网 Nexus (`$PIP_INDEX_URL`, `$NEXUS_DOCKER_REGISTRY`, `$NPM_CONFIG_REGISTRY`) 实现构建提速。
  - **全量度量制品留存**: 将所有的测试与扫描动作强制输出并捕获为标准制品 (Artifacts)，包含 `coverage.xml`, `junit.xml` 等，打通 GitLab MR 可视化。
  - **高阶审计接入**: 集成 Trivy 实体镜像扫描 (`trivy image`) 与文件级 CVE/IaC 扫描，集成 CycloneDX SBOM (含 License/PURL)，集成 Radon 代码复杂度与维护性指数提取，全面输出标准 JSON 报告供下游 DDAP 消费。

- **工程严谨性规则演进与教训归档 (2026-06-08)**:

  - **技能文档演进**: 演进了 `engineering-rigor-arbiter` 技能文档，补充了脚本路径依赖防御 (Explicit PYTHONPATH Injection) 与清场指令精确打击与容错原则 (Clean Target Precision & Tolerance) 等两项核心红线规范。
  - **教训沉淀归档**: 主动回顾终端中有关 scripts 模块 ModuleNotFoundError 及 pytest 缓存权限不足 clean 卡死的错误，并在 `lessons-learned.log` 完成归档。

- **Docker Compose 兼容性修复 (2026-06-01)**:

  - **动态命令探测**: 在 `justfile` 中引入动态 `COMPOSE_BIN` 探测机制，优先使用旧版 `docker-compose`，若不存在则降级为新版插件化 `docker compose`。修复了云端 GitHub Actions 等现代 CI/CD 容器运行时因缺少 `docker-compose` 独立二进制导致 fullgate 执行失败的问题。

- **Git Hooks 体系标准化升级 (A+B) (2026-05-31)**:

  - **Ruff 原生 Pydocstyle**: 淘汰脆弱的 AST 内联脚本 `check-docstrings`，启用 Ruff `D101/D102/D103/D105` 规则，执行速度提升百倍，同时引入格式校验能力。
  - **标准防呆护栏**: 新增 `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`, `check-merge-conflict` 五项官方 pre-commit-hooks 防止低级错误入库。
  - **Layer 1 本地类型门禁**: 在 pre-commit 中接入 `mypy` 静态类型检查，确保 AI 生成的代码在 `git commit` 时即被类型防线拦截。
  - **Commit 规范强拦截**: 接入 `commitizen`，物理强制 Conventional Commits 格式（`feat/fix/docs: ...`），与 `AGENTS.md §3.3` 契约对齐。
  - **Layer 2 CI/CD 类型验收门禁**: 在 `.gitlab-ci.yml` 新增独立 `static-analysis` stage，在 MR 和 `main` 分支触发 `mypy` 全局扫描，作为组织级验收防线（当前 `allow_failure: true` 观测模式，待 Tech-Debt 清零后切换为强制拦截）。

- **FastAPI 路由与 Service 层深度集成 (Phase 1)**:

  - **解耦中转层**: 完成了 `admin`, `iteration`, `plugin`, `security`, `devex_pulse`, `service_desk` 等 7+ 个核心路由的重构，由 `devops_collector.core` 映射切换为直接引用 `devops_collector.services`。
  - **双轨调用对齐**: 确保 Web 端与 CLI 端共享同一套重构后的业务逻辑服务，通过了全量单元测试 (`tests/unit/test_portal/`)。

- **诊断总线事务安全性修复 (Bug Fix)**:

  - **原子回滚保护**: 在 `DiagHelper.run_check` 中注入了 Session 回滚机制，确保单项诊断 SQL 失败时能及时释放锁并清理状态，彻底解决了审计日志写入时的“事务锁定”崩溃。
  - **状态传播修复**: 修正了 `sys_diagnose` 的返回逻辑，使其能正确透传子诊断项的聚合状态。

- **管理命令现代化迁移 (Progressing)**:

  - **签名即文档**: 已完成 `realign_org_managers`, `init_organizations`, `init_products`, `export_sonar_report`, `export_project_map`, `export_data_dict`, `init_okrs`, `init_locations`, `init_mdm_location`，插件映射类命令（`init_gitlab_mappings`, `init_zentao_mappings`, `init_sonarqube_links`, `init_jenkins_links`, `init_nexus_links`），基础主数据类命令（`init_catalog`, `init_calendar`, `init_cost_codes`, `init_labor_rates`, `init_purchase_contracts`, `init_revenue_contracts`），以及数据诊断类命令（`check_data_dict_freshness`, `check_identity_alignment`）等核心命令的现代化重构，采用 `Annotated` 类型提示实现参数的自动解析与 Rich 进度条集成。同时移除了所有过时的 `add_arguments` 定义。

### 新增 (Added)

- **Agent Skill 体系初始化 (v5.7.0)**:
  - **Skill 物理注入**: 初始化并提交了 16+ 个核心 Agent Skill，覆盖了任务启动、故障分诊、代码审查及离场交接等全生命周期。
  - **意图锚点加固**: 建立了「安全锁」机制，强化了 AI 在执行物理写操作前的方案呈报与 A/B/C 决策对齐流程。
- **AI 效能归因 (v5.6.0)**: 引入 LiteLLM 作为统一模型网关，开发 `analyze_efficacy` 诊断命令实现异常指标的自动化诊断。
- **UI 视觉提升 (v5.5.0)**: 注入 Apple HIG 深色模式全套 Design Tokens，并将卡片与侧边栏的玻璃拟态通透度升级为 blur(20px)。
- **CLI 插件增强 (v5.4.0)**: 重构了 `BaseCommand` 与 `DiagHelper`，全局集成 `rich` 组件，支持面板渲染与动态进度条。
- **MyPy 治理 (Phase 4) (v5.3.0)**: 完成 Auth 模块 26 项报错修复，解除了 pyproject.toml 中的鉴权模块隔离。

## [5.2.0] - 2026-05-12

### 新增 (Added) - v5.2.0

- **CLI 现代化与去中心化发现 (Decentralized CLI Discovery)**:
  - **Typer 引擎集成**: 交付了基于 `typer` 的现代化命令行入口 `cli.py`，支持多级命令分组、Rich 渲染与参数自动反射。
  - **插件自动挂载**: 实现了 `plugins/*/management/commands` 的动态扫描机制，支持插件命令的零配置、无感扩展。
  - **全局审计总线 (Audit Trail)**: 在 `BaseCommand` 注入审计钩子，物理追踪所有 CLI 操作（Who/When/What/Changes/Result）。
- **业务逻辑层标准化 (Service-Oriented Refactoring)**:
  - **Service/Command 严格分离**: 完成了全量核心命令（OKR, Org, Calendar, DataDict, Products 等）的逻辑下沉，建立了统一的 `services/` 包。
  - **预飞行检查钩子 (Pre-flight Checks)**: 为所有命令集成了环境连通性、DB 连通性及运行时架构审计。

### 优化 (Improved) - v5.2.0

- **架构红线确立**: 在 `AGENTS.md` 中固化了“服务/命令分离”与“去中心化发现”的强制性契约。

### 新增 (Added) - v5.1.0

- **管理总线架构收敛 (Management CLI Convergence)**:
  - **BaseCommand 框架**: 交付了标准化、插件化的管理命令框架，支持统一的数据库 Session 管理、异常处理与日志审计。
  - **核心脚本迁移 (28+)**: 完成了包括 RBAC 初始化、组织对齐、架构审计、系统体检等 28 个分散脚本的“类化”重构，彻底终结了“脚本乱战”状态。
  - **Python 化依赖同步**: 交付了 `sync_deps` 命令，内建 Nexus/清华源自动切换与重试逻辑，显著提升了环境稳定性。
  - **混合调度 v3**: `cli.py` 支持混合模式，强制新功能必须以 `BaseCommand` 插件形式实现。
- **基础设施织网 (Infrastructure & SSOT)**:
  - **API 网关集成 (Traefik)**: 引入 Traefik 统筹流量，实现路径级路由、消灭跨域并落地集中鉴权。
  - **SSOT 配置治理**: 确立 `.env.example` 为全局唯一事实源，消除了容器编排与环境管理中的硬编码配置。
  - **Justfile 全面重构**: 确立 `just` 为环境管理的绝对权威，统一了质检、构建与部署的调度入口。
  - **Dockerfile 极致瘦身**: 引入 Builder/Final 双阶段构建模式，镜像体积缩减约 40%。
- **质量与效能下钻 (Analytics & QA)**:
  - **MyPy 深度治理 (Phase 1-3)**: 完成核心域与插件层的强类型重构，MyPy 报错清零，启用严格模式。
  - **Traceability Radar (溯源雷达)**: 交付了工业赛博朋克风格的效能雷达图，支持 VSM、协作质量与安全多维指标可视化。
  - **GitLab 效能分析增强**: 实现秒批 (Rubber Stamp) 识别机制、VSM 瓶颈分析及 Shift-Left 漏洞追溯逻辑。
  - **TDD 2.0 工作流**: 落地意图驱动测试 (TDD 2.0) 与 pytest-mock 存根标准。

### 优化 (Improved) - v5.1.0

- **运维协议标准化**: 更新了 `AGENTS.md` 和 `contexts.md`，确立了“管理命令总线”为系统运维的唯一路径。
- **事务安全性**: 将所有初始化脚本纳入 CLI 顶层事务守卫，支持跨多表操作的原子性回滚。

## [5.0.0] - 2026-04-29

### 新增 (Added) - v5.0.0

- **文档基建 2.0 (Documentation Infrastructure)**:
  - **SSOT 治理**: 确立了以 `DOC_INDEX.md` 为核心的“单一事实来源”索引体系，将 27+ 份文档重构为 Architecture, Features, Analytics, Guides, History 五大模块。
  - **架构白皮书收官**: 交付了 `SYSTEM_DESIGN.md`，深度定义了 MDS + SDA 分层逻辑。
  - **资产血缘对齐**: 完成了全量初始化脚本对 `docs/assets/sample_data/` 物理路径的重连。
- **质量红线突破**:
  - **100% 核心覆盖率**: 核心调度层与注册表模块通过深度单元测试，正式达成 100% 物理分支覆盖率目标。
- **合规与安全**:
  - **开源协议落地**: 根目录新增 Apache 2.0 License，完成项目法律合规性闭环。
  - **安全扫描实操指南**: 交付了 `SECURITY_SCAN.md`，指导 OWASP Dependency-Check 的深度应用。

### 优化 (Improved) - v5.0.0

- **AI 协作协议 (AGENTS.md V2.0)**: 固化了“凭据-意图防火墙”和“物理取证原则”，确保人机协同的安全边界。
- **目录结构精简**: 根目录执行“控制平面”清理，仅保留 5 个元文档，大幅降低认知负荷。
