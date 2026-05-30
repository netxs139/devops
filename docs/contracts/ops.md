# 运维、架构与插件集成契约 (DevOps, Architecture & Plugins)

> **定位**: 本文档是 `contexts.md` 的领域扩展，涵盖平台核心架构、运维生命周期、RabbitMQ 调度隔离及第三方插件（GitLab、ZenTao 等）集成规范。当涉及插件开发或平台部署时，必须严格遵守。

## 1. 核心架构与插件拓扑 (Architecture & Plugins)

### 1.1 业务逻辑拓扑地图 (Logical Directory Topology)

- **`devops_collector/` (采集引擎与领域内核)**：平台的后方心脏，掌握基础规则与数据拉取逻辑。
  - `auth/` (认证网关层)：处理 JWT Token 发放、权限声明注入及 RBAC 混合校验。
  - `core/` (底层基建层)：单例配置加载、多端安全防线、以及唯一的数据库引擎池 (Engine/Session)。
  - `models/` (MDM 实体定义层)：所有组织架构等跨域主数据 Schema 的最终拼图与 SSOT。
  - `plugins/` (开放生态插件组)：按系统源严格物理隔离。每个目录自给自足，包含 `client.py` 与 `worker.py`。
- **`devops_portal/` (交互管控前端 API)**：直接面向人类的大屏/系统报表拉取请求。路由定义层坚守“薄逻辑”规则。
- **`scripts/` (自动化与管理总线)**：全量运维脚本的单一收口地。核心入口为 `cli.py`。

### 1.2 Plugin Factory 结构

插件位于 `devops_collector/plugins/`，结构必须遵循以下标准：
```text
plugins/{plugin_name}/
    __init__.py      # 必须包含 register() 函数
    client.py        # API 客户端，继承 BaseClient
    worker.py        # 任务处理器，继承 BaseWorker
    models.py        # SQLAlchemy 模型定义
    schemas.py       # Pydantic 请求/响应模型 (可选)
```

- **Router-Service 模式**:
  - **Router 层**: 仅负责路由定义、参数校验、权限控制及调用 Service。严禁在 Router 中编写业务逻辑或直接操作多表数据库。
  - **Service 层**: 承载核心业务逻辑。多表操作强制使用 `with db.begin():` 包裹。

### 1.3 CLI 调度总线架构 (CLI Command Bus Architecture) [MANDATORY]

- **1. 命令总线 (Command Bus)**: `scripts/cli.py` 是整个系统运维能力的唯一物理入口。
- **2. 混合调度机制 (Hybrid Dispatching v3)**:
  - **框架模式 (Command Framework) [NEW/PRIORITY]**: 基于 `BaseCommand` 基类的插件化架构。存放于 `devops_collector/management/commands/`。
  - **原生兼容模式 (Native Legacy)**: 支持遗留接口脚本。
  - **子进程模式 (Subprocess Fallback)**: 自动降级为 `subprocess.run` 调用。
- **3. 开发契约**: 任何**新**运维逻辑**必须**以 `BaseCommand` 子类形式实现。

### 1.4 数据采集管道性能规范 (Data Pipeline Performance) [MANDATORY]

- **Staging 写入分级 (Tiered Staging Write)**:
  - **批量实体 (Commit, Issue, MR 等)**: 必须调用 `bulk_save_to_staging()` (使用 PostgreSQL 原生 `COPY FROM`)。
  - **单条低频实体 (Product, Project, Group)**: 允许使用 `save_to_staging()`。判断标准：单次同步超 10 条必须走批量。
- **Transform 层批处理 (Batch Transform)**:
  - **预加载模式**: 严禁在循环内逐条执行 N+1 查询。必须在循环前一次性加载为 Map。
  - **延迟 Flush**: 严禁在循环内逐条 `session.flush()`。必须在循环结束后统一执行。

## 2. 运维流程与生命周期 (DevOps Ops)

### 2.1 部署模式与镜像加速

- **部署命令**: `just deploy`, `just package`, `just deploy-offline`。
- **内网/私服构建规范 (Private Registry Compatibility) [MANDATORY]**:
  - 为适配离线或受限网络，Dockerfile 严禁硬编码外部公共镜像地址。核心工具必须从 NEXUS 镜像仓库提取。
  - **依赖拉取优先级 (Mirror Priority)**: 内网 Nexus > 互联网镜像 > 官方 PyPI。
  - 镜像构建阶段必须通过 `ARG` 支持 `UV_IMAGE` 和 `PIP_INDEX_URL` 注入。

### 2.2 健康检查 (Healthcheck Resilience) [MANDATORY]

- 所有容器必须定义 `healthcheck`。对于基础服务，`retries` 必须设为不少于 **60** 次，且配置 `start_period`。
- 针对低配环境，必须显式限制内存/磁盘水位（如 RabbitMQ VM Watermark），防止误报重启。

### 2.3 异步任务 (RabbitMQ) 规范

- **队列分离 (Queue Isolation) [MANDATORY]**: 每个数据源 (Plugin) 必须拥有独立的 RabbitMQ 队列（如 `gitlab_tasks`）。**严禁**混入同一队列防止任务饿死。
- **动态路由与 SSOT**: 队列名称列表应从 `PluginRegistry.list_sources()` 动态生成，严禁硬编码。
- **公平消费 (Fair Dispatch)**: Worker 使用 `prefetch_count=1` 轮询监听所有队列。
- **失败补偿与调度纪律**:
  - Scheduler 在推送任务前必须校验实体的 `sync_status`，处于 `SYNCING` 或 `QUEUED` 的严禁重复入队。
  - 调度必须设置**上限**（限流），防止灌满队列。

### 2.4 调度器陷阱与运维手册 [MANDATORY]

- **状态死锁模式**: 若数据库大量项目处于 `QUEUED` 状态但队列为空，说明调度器跳过。恢复：执行 `just sync-all`（含 `--force-all --once`）。
- **Worker 韧性**:
  - MQ 断线时必须实现指数退避重连。
  - 必须捕获 `SIGTERM` 信号优雅停机，严禁中断处理中的任务。

## 3. 插件集成特异性规范

### 3.1 禅道集成防护规范 (ZenTao Guardrails) [MANDATORY]

- **认证防御**: 必须实现 401 异常拦截与 Token 自动刷新，重试逻辑必须包含 `is_retry` 状态位防止死循环。MQ 连接心跳 `heartbeat=600`。
- **数据一致性陷阱**: 
  - 禅道 `0` 表示空值，入库前必须转为 `NULL`。
  - **子资源韧性**: Detail API 报 404 时，必须降级为空集合处理，严禁中断全量任务。人员降级失败则保留原始字符串。
- **状态归一化**: 必须通过 Transformer 将不同业务状态映射为标准 5 状态 (Backlog, InProgress, Testing, Completed, Cancelled)。

### 3.2 GitLab 集成性能守卫

- **同步深度守卫 (Sync Depth Limit)**: 首次同步必须显式传递 `since` 参数（默认近 365 天），严禁无限制全量抓取。
- **借用字段映射**: "借用"非标字段时，必须在 `schemas.py` 通过 `Field(alias=...)` 集中管理。

### 3.3 SonarQube & Jenkins 集成

- **SonarQube 推拉结合**: 基础数据周期拉取，扫描结果由 CI 主动推送（Webhook Receiver）。
- **Jenkins 门禁**: 接入前必须产出 ADR。严禁全量拉取 Console Log 存库，改为 Webhook 推送关键状态。

## 4. 全链路可观测性与告警体系

- **轻量级监控**: 优先通过结构化日志输出关键健康指标（延迟、死信率），未来流量爬坡再切入 Prometheus (`/metrics`)。
- **容灾熔断锁**: 若插件连续 10 次遭遇 5xx 或连接耗尽，必须进入冷却休眠，防止算力过载。
- **呼救闭环网**: P0/Blocker 灾难发生时，必须向外围（企微/邮件）实施突发告警推送。

## 5. 开放网关与 Webhook 契约 (Open API Gateway)

- **接收器解耦**: 被动接收接口首要义务是瞬时落单（如入队 MQ），必须在 `200ms` 内响应第三方。
- **强鉴权与限流**: `/webhook` 端点一律执行 Token 准入、HMAC 验签或限速机制，封堵 DDoS 及重放攻击。
