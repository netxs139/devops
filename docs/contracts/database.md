# 数据库与数据治理契约 (Database & Data Governance)

> **定位**: 本文档是 `contexts.md` 的领域扩展，涵盖数据库 Schema 设计、主数据管理 (MDM)、查询优化、数据脱敏等强制规范。当进行数据库模型变更、关联查询或设计数据同步逻辑时，必须严格遵守。

## 1. 数据库开发规范 (Database & SCD)

### 1.1 Surrogate PK 准则 (Surrogate PK Principle) [MANDATORY]

- **物理主键 (Physical PK)**: **所有**数据库表（除部分 N:N 关联表外）必须强制包含一个名为 `id` 的物理主键，严禁使用业务编码作为物理 PK。
- **主键类型 (PK Types)**:
  - `User` (mdm_identities): 使用 `UUID` (字段名为 `global_user_id` 并别名为 `id`)，以支持多源身份归一。
  - **其它表**: 统一使用 **BigInteger** 自增主键。
- **关联解耦 (Relationship Decoupling)**: 所有的 `ForeignKey` 必须指向父表的物理 `id`。严禁跨表透传业务编码（如 `project_id`, `org_id`）作为关联手段，防止业务重命名时触发级联故障。
- **业务标识 (Logical Keys)**: 原有的 `org_id`, `project_id`, `product_id` 等业务键已完全解耦，重命名为 `org_code`, `project_code`, `product_code` 等字符串字段。
- **API 响应对齐 (API Alignment) [MANDATORY]**: 所有的接口响应（Router 层）在处理业务 ID 时，必须将外部可见的 `project_id` 键映射到模型中的 `project_code` 字段，将 `product_id` 键映射到 `product_code` 字段。严禁在 API 响应中透传自增的物理 `id`。
- **命名公约 (Naming Convention)**:
  - 后缀 `_id`: 专指指向物理 PK 的外键（BigInt/UUID）。
  - 后缀 `_code`: 专指业务逻辑编码（String），如 `cost_center_code`。
- **MDM 重构同步规程 (Schema Evolution Protocol) [MANDATORY]**:
  - 任何涉及到 MDM 核心表（`mdm_*`）物理主键或逻辑主键（`code` vs `id`）的重构，**必须同步审计并更新**所有相关的测试用例与导入脚本。
  - 脚本中严禁直接将业务编码（String）赋值给整数型外键字段。必须实现先查询（Resolve）业务码获取物理 ID（Integer），再执行赋值的闭环逻辑。

### 1.2 权限建模协议 (Permission & RBAC Protocol) [MANDATORY]

> **背景**：为了降低认知负载并实现 UI 与 API 的强一致性，系统采用「菜单即权限」的联合建模范式。

- **1. 菜单-角色模型 (Menu-as-Permission)**:
  - 系统不设独立的 `Permission` 实体类。权限标识符（`perms`）直接作为属性挂载在 `SysMenu` 模型上。
  - **逻辑路径**: 用户 (User) -> 分配角色 (SysRole) -> 关联菜单 (SysMenu) -> 获得权限标识 (`perms`)。
- **2. 权限声明规范**:
  - 权限标识符必须遵循 `{业务域}:{资源}:{操作}` 的命名公约（如 `rpt:quality:view`, `pm:project:edit`）。
- **3. 测试注入规程**:
  - 在集成测试中模擬权限时，**严禁猜测**名为 `SysPermission` 的类。
  - **正确做法**: 必须通过创建 `SysMenu(perms="...")` 实例并关联至角色菜单集来实现权限注入。

### 1.3 审计与安全性 (分层要求)

- **MDM 层 (`mdm_*`)**: 强制继承 `TimestampMixin`（`created_at`, `updated_at`）+ `SCDMixin`（`is_deleted`, `is_current`, `effective_from/to`）。SCD 机制已覆盖软删除与版本追踪。
- **系统层 (`sys_*`)**: 强制继承 `TimestampMixin`。RBAC 关联表（如 `sys_user_roles`, `sys_role_menu`）应至少包含 `created_at`，以支持安全审计。
- **插件层 (`{source}_*`)**: 不强制继承 `TimestampMixin`。插件模型的 `created_at`/`updated_at` 保留**源系统 API 返回的时间语义**（如 MR 在 GitLab 的创建时间），不与系统入库时间混淆。生命周期由 `sync_status` 管理。
- **`created_by` (操作人)**: 不全局强制。仅在**存在用户交互**的业务模块（如 Service Desk `sd_*`）按需添加。自动化同步写入的数据通过 `correlation_id` 和 `sys_sync_logs` 追踪来源。
- **`correlation_id` (追踪标识) [MANDATORY]**: 所有后台同步相关的 Staging 表 (`stg_raw_data`) 和日志表 (`sys_sync_logs`) 必须包含此字段，以便在 1000+ 项目并行时进行全链路链路还原。
- **软删除**: 严禁物理删除生产数据。MDM 层通过 `SCDMixin.is_deleted` 实现；插件层通过 `sync_status='DELETED'` 标记源端已消失的实体。
- **SCD Type 2**: 组织、产品、团队主数据采用慢变维，追踪“历史时刻的负责人”及“当时的组织归属”。
- **唯一键与 SCD 冲突处理 [MANDATORY]**:
  - 若表内存在业务主键的 `Unique` 约束（如 `mdm_organizations.org_id`），在执行 GetOrCreate 或 SCD 更新前，**必须**去除 `is_current=True` 的过滤条件进行全局查询。
  - 否则，INSERT 操作将由于“看不见”历史记录 (`is_current=False`) 而触发物理唯一冲突。
- **组织架构模式**:
  - **层级 (Hierarchy)**: 公司(Root) -> 中心(Center) -> 部门(Dept)，不再使用 `SYS-` 体系节点。
  - **属性 (Attribute)**: 体系 (Business Line) 作为 `Organization` 的 `business_line` 字段存储，支持跨体系的部门归属。

### 1.4 外键循环与测试隔离规范 (Foreign Key Cycles & Testing Isolation) [NEW/MANDATORY]

> **背景**: MDM 核心实体间存在天然的业务循环。例如：用户归属于地点 (`User.location_id`), 而地点负责人又是该用户 (`Location.manager_user_id`)。这种“鸡生蛋，蛋生鸡”的逻辑在数据库物理层面会引发删表顺序死锁。

- **1. ORM 层面声明 (ORM-Level Declaration)**:
  - 针对所有已知的循环外键（如：User \<-> Organization, User \<-> Location），**必须**在 `ForeignKey` 定义中显式指定 `use_alter=True` 并通过 `name` 参数给出全局唯一的约束名称。
  - 示例：`ForeignKey("mdm_identities.global_user_id", use_alter=True, name="fk_location_manager")`。
- **2. 同步逻辑的两阶段协议 (Two-Phase Alignment Protocol)** \[MANDATORY\]:
  - **第一阶段 (Ingestion)**: Worker 在同步带外键循环的实体时，仅入库基础非空字段。如果关联的目标对象（如负责人）尚未入库，**严禁**触发递归查询或报错。
  - **暂存标识**: 将外部源提供的原始标识（如 LDAP ID）存入专门的 `manager_raw_id` 字符串字段。
  - **第二阶段 (Self-Healing)**: 在全量同步任务结束时，由应用级 Service 触发 `realign_all_managers()`。该方法统一将 `manager_raw_id` 解析为真正的 `manager_user_id` (UUID) 物理外键，实现最终一致性。
- **3. 测试环境隔离 (Testing Isolation)**:
  - 在 SQLite 内存数据库环境下，`Base.metadata.drop_all` 会因为无法静态计算删表顺序而失败。
  - **DoD 标准**: 集成测试夹具必须实现环境感知，在测试结束时采取「连接自动关闭销毁」或显式执行 `PRAGMA foreign_keys=OFF`，确保清理过程不因外键循环而报错。

### 1.5 模型实现完整性规范 (Model Implementation Integrity) [NEW/MANDATORY]

> **背景**: AI 在快速生成 ORM 模型时，极易漏掉 Python 基础导入（如 `uuid`, `datetime`）或通用的审计 Mixins，导致运行时出现 NameError 或数据链路断裂。

- **1. 物理导入清单 (Physical Import Checklist)**:
  - 凡是使用 `UUID(as_uuid=True)` 或 `default=uuid.uuid4` 的文件，**必须**包含 `import uuid`。
  - 凡是包含日期时间字段的文件，**必须**包含 `from datetime import datetime`。
  - 严禁依赖级联导入（即假设父模块已导入）。
- **2. 强制审计头 (Mandatory Audit Headers)**:
  - **Staging/插件表**: 必须继承 `TimestampMixin` 和 `TraceabilityMixin`。
  - **MDM 核心表**: 必须继承 `TimestampMixin` 和 `SCDMixin`。
  - 审计工具 `arch_auditor` 将强制校验类的继承列表，若发现 `Column` 定义但缺失审计 Mixin 则视为阻断级错误。
- **3. 冒烟验证协议 (Smoke Test Protocol)**:
  - AI 在修改 `models.py` 后，执行 TDD 循环前，**必须**执行一步“冒烟导入”：`python -c "from devops_collector.plugins.xxx.models import *"`。
  - 只有冒烟导入通过（证明无 NameError），方可启动 `pytest`。

### 1.6 数据入库幂等性与外键顺序规范 (Data Ingestion & Idempotency) [NEW/MANDATORY]

> **背景**: 在抓取插件硬化过程中发现，直接使用 `session.add()` 在重试场景下极易触发唯一键冲突，且子实体早于父实体持久化会触发外键约束失效。

- **1. 强制 Merge 范式 (Mandatory Merge Pattern)**:
  - 凡是涉及插件采集实体的 Transform/Save 逻辑，**必须**优先使用 `session.merge(obj)`。
  - **原因**: `merge` 会自动处理“已存在则更新，不存在则插入”的逻辑，是保证采集任务天然幂等的最高效手段。
- **2. 外键前置持久化协议 (FK-Safe Persistence Order)**:
  - 涉及父子关系的实体同步（如：Pipeline -> Job, Issue -> Note），**必须**先对父实体执行 `session.merge()`。
  - **逻辑**: 必须确保父实体的 ID 在 Session 中已处于 Persistent 状态（或已 Flush 到数据库），方可处理子实体的外键赋值，严禁依赖级联自动处理复杂的分布式外键。
- **3. 测试种子完备性 (Test Data Seeding)**:
  - 任何涉及外键字段的集成测试，**必须**在测试 Setup 阶段预先同步/创建其依赖的父级记录。
  - **严禁**在 Mock 环境下通过伪造不存在的外键 ID 来进行“跳步测试”，这会导致生产环境下的物理约束崩溃。

## 2. 数据性能与查询优化

- **连接池管理 (Connection Pool) [MANDATORY]**:
  - 数据库连接必须通过**应用级连接池** (`create_engine` 的 `pool_size` + `max_overflow`) 管理。Worker / Scheduler 进程启动时创建**唯一的** `engine` 实例，每个任务从池中借用 Session，处理完归还。
  - **严禁**在循环或回调函数中反复调用 `create_engine()`，否则将导致 PostgreSQL 连接耗尽。
  - 推荐配置：`pool_size=5, max_overflow=10, pool_pre_ping=True`（自动检测断连并重建）。
- **插件层索引策略 (Plugin Index Policy)**:
  - **外键字段必建索引**: PostgreSQL 不会自动为 FK 创建索引。所有 `ForeignKey` 列必须显式添加 `index=True`，否则 JOIN 和 CASCADE DELETE 会触发全表扫描。
  - **高频查询字段建索引**: `state`/`status`（列表筛选）、`created_at`/`merged_at`/`committed_date`（时间范围聚合、DORA 指标计算）等高频 WHERE/ORDER BY 字段。
  - **不盲目加索引**: 枚举值极少的字段（如 `environment` 仅 prod/staging，选择性差）或查询频率低的字段不加索引，避免无收益的写入代价。
- **N+1 问题**: 查询关联对象时必须显式使用 `.options(joinedload(...))`。
- **批量处理**:
  - **读**: 大数据集查询必须使用 `yield_per(1000)` 或分页游标。
  - **写**: 插件同步逻辑强制使用 `bulk_insert_mappings`，严禁循环单条 `db.add()`。

## 3. 全局身份与成本归因规范 (Global Identity & Attribution)

### 3.1 身份对齐优先 (Identity First) [MANDATORY]

- **主键转换原则**: 任何数据源采集到的人员标识，入库前**禁止**直接使用原始账号作为最终业务关联键。
- **强制转换链**: 采集原始账号 -> 调用 `IdentityManager.get_global_id()` -> 映射为统一的 UUID `global_user_id` -> 存入业务表。
- **成本归因**: 只有完成 `global_user_id` 转换的工时或提交记录，方可参与效能度量与成本中心分摊计算。对于无法对齐的“流浪账号”，系统必须通过 `sys_unknown_identities` 表进行挂起并在看板显著提醒。

### 3.2 企业级主数据管理 (Enterprise MDM) 六大金科玉律 [MANDATORY]

1. **黄金记录与幸存者规则 (Golden Record & Survivorship)**：多路数据对齐时，必须基于权威优先级配置（如 HR > WeCom > GitLab）判定合并写入权。
1. **全局身份解耦 (OneID Cross-Reference)**：外部账户标识必须统一存入 `mdm_identity_mappings`，`User` 表主键仅保留平台生成的 `global_user_id`。
1. **隔离暂存区 (Staging Area & Promotion)**：源系统原始数据必须先落入 `mdm_staging`，由 `PromotionService` 清洗合并后再直写主数据表。
1. **数据血缘 (Data Lineage)**：`User` 或 `Organization` 创建/更新时必须强制记录 `source_system` 与 `correlation_id`，支持按批次回滚。
1. **慢变维追踪 (SCD Type 2)**：属性变更严禁 `UPDATE` 覆盖，必须置位 `is_current=False` 并 `INSERT` 新行。
1. **异步对齐与自愈 (Async Auto-Alignment)**：同步带循环引用的对象时执行两阶段对齐协议（第一阶段暂存，第二阶段通过 `realign_org_managers` 合并）。

## 4. 数据隐私与合规治理 (Data Privacy & Governance)

### 4.1 数据脱敏 (PII Masking)

- **敏感字段拦截**: 所有包含个人身份信息 (PII)、薪酬、私密联系方式等敏感数据的字段，严禁在未经脱敏的情况下直接透传给前端 API 或记录在普通业务日志中。
- **动态脱敏策略**: 必须在 Service 层或 Pydantic 响应模型中实现字段级别的动态脱敏拦截（例如：仅展示邮箱的前缀首字符与域名掩码）。

### 4.2 行级权限过滤 (Row-Level Security)

- **物理隔离网机制**: 对于带有强归属属性的绩效与度量数据，必须基于查询发起方的 `global_user_id` 与 RBAC 权限栈，在 ORM 层（而非内存层）追加强行级过滤子句。
- **拦截越权 (Zero Trust)**: 严禁仅靠前端“隐藏菜单项”来实现伪权限控制。底层 Router 与 Service 均需确保对非管辖范围内的数据访问请求，实施无条件鉴权熔断 (抛弃请求并返回 HTTP 403)。

## 5. 数据生命周期与归档策略 (Data Lifecycle & Archiving)

### 5.1 TTL 与冷热分层架构

- **追踪日志 (Sync Logs / Worker Dumps)**: 此类过程验证数据仅在热库保留最多 90 天，超过周期的数据必须定期配置清理或通过脚本转储至冷存储器进行物理标记清理。
- **业务明细快照**: 针对单点频繁落库的数据对象（如 `gitlab_commits`），针对不同颗粒度应当依据活跃日阈值建立历史分区策略，保障主工作流表的体积可控。

### 5.2 磁盘真空化要求 (Vacuum Policy)

- 考虑到数据采集过程中带来的极高频的 Upsert 操作，必须针对涉事关联大表开启严格的 PostgreSQL 定期 `autovacuum` 并调校触发频次。
- **严惩膨胀 (Table Bloat)**: 禁止忽略物理表的自发膨胀问题，以防全表扫描导致 I/O 阻塞。

## 6. 查询性能降级与原生加速策略 (Query Degradation & Native Caching)

### 6.1 Dashboard 负载分离与结果物化

- **防击穿屏障**: 因驾驶舱 Dashboard 存在极庞大的高维 SQL 时序运算量。前台高频重算展示绝对不可直接无防避地砸穿到底层 Postgres 单表上。
- **轻量替代方案 (Postgres Native)**: 鉴于当前系统不引入 Redis 组件，必须大量运用**底层数据库级的预计算表** 或 **物化视图 (Materialized Views)**。利用 dbt 或后台 Scheduler (任务处理器) 定点发起数据降维与前置刷新。

### 6.2 内存拦截与防御性后退 (Degradation)

- **应用级缓存**: Python 后端对高频只读请求，按需应用 `@lru_cache` 等内部空间作防洪拦截，阻挡对库的击穿式拉取。演进路线上 `[Planned]` 待多实例扩容时再切为外部 Redis 集群。
- **优雅降级展现能力**: 如果面临计算卡死或数据库长查询超时，API 结构必须能在应用层捕获异常，并且有能力降级（如向前端回传特定的“当前不可用但请您参考上期快照数据”的信标）。绝对避让抛出 500 导致带崩全网白屏（White Screen of Death）的低容忍态势。
