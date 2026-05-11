# 修订记录 (Changelog)

所有对 DevOps Data Application Platform 的重要更改都将记录在此文件中。

## [5.1.0] - 2026-05-11

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
