# 修订记录 (Changelog)

所有对 DevOps Data Application Platform 的重要更改都将记录在此文件中。

## [Unreleased]

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
