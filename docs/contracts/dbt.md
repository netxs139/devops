# dbt 建模与可视化平台契约 (dbt Modeling & BI)

> **定位**: 本文档是 `contexts.md` 的领域扩展，涵盖 dbt 分层模型设计、JSONB 类型安全、看板数据访问约定及 BI 可视化架构。当进行 `dbt_project/` 开发或数据展现时，必须严格遵守。

## 1. dbt 数据建模与分层 (Data Transformation)

> 📘 **开发指南**: 详细的模型开发手册及代码模式请参见 `docs/guides/DBT_MODELING_GUIDE.md`。

### 1.1 分层逻辑

| 层级 | 前缀 | 说明 |
| :--- | :--- | :--- |
| **Staging** | `stg_` | 原始数据清洗，1:1 映射源表。**强制性规则**：严禁在 Staging 层执行业务过滤（如 `where is_current=true`），必须完整保留源表历史快照以支撑 SCD Type 2。 |
| **Intermediate** | `int_` | 中间转换，跨源关联与过滤。 |
| **Marts (维度)** | `dim_` | 业务维度表，描述性属性。 |
| **Marts (事实)** | `fct_` | 业务事实表，度量指标，直接对接报表层。 |

### 1.2 ID 归一化与自愈协议 (Normalization & Self-Healing) [MANDATORY]

- **名称对齐优先**: 在 `int_` 层必须建立 `int_org_normalization` 模型。对于 `zentao_dept_xxx` 等非标 ID，必须通过名称（Name）对齐回填为 HR 规范 ID 或业务中文术语，严禁在报表层暴露原始源系统 ID。
- **SCD2 历史自愈**: 身份主数据 (`int_golden_identity`) 必须实现基于 SCD2 历史版本的字段回溯逻辑。当当前记录属性（部门/工号）缺失时，自动回滚寻找历史版本中的最近非空值填充。
- **置信度溯源**: 合并后的记录必须包含 `attribution_source`，标注数据是来自“HR官网”、“归一化映射”还是“历史自愈”。

### 1.3 源表与元数据管理

- **源表管理**: 所有原始表必须在 `sources.yml` 中声明，包含 database, schema, table 完整路径。
  - **新鲜度 (Freshness)**: 核心 Source 表必须配置 `freshness` 检查（如:warn_after: {count: 24, period: hour}）。
- **元数据 (Metadata)**: 核心 Marts 模型必须在 `meta` 字段中标记 `owner` 和 `domain`，以便 DataHub 采集。
- **质量哨兵**: 所有模型在 `schema.yml` 必须定义 `unique` 和 `not_null` 测试，关键指标使用 Singular SQL Tests 校验。

## 2. dbt 性能与类型守卫 (Performance & Type Safety) [NEW]

- **JSONB 强类型转换 (Defensive JSONB)** [MANDATORY]:
  - 从 `JSONB` 提取字段进行转型时，必须执行 `nullif(trim(both '"' from field), '')`。
  - **逻辑原因**: 防止 Postgres 解析带物理引号的 JSON 字符串（如 `"true"`, `"123"`) 时触发语法错误导致流水线熔断。
- **时区归一化 (UTC Sync)**: 所有 Staging 层的时间戳必须显式执行 `at time zone 'UTC'`，并统一使用 `_at` 后缀（如 `committed_at`, `closed_at`）。
- **ID 语义一致性 (String IDs)**: 所有跨源关联的业务主键在 dbt 语义层强制统一为 `String (character varying)` 类型。严禁在中间层混用 `Integer` 与 `String` 导致关联报错。
- **Staging 透明度**: Staging 模型必须完成所有字段语义对齐（如 `ncloc` -> `lines_of_code`）。严禁在 `int_` 或 `fct_` 层继续直接使用源系统的非标缩写。
- **并发控制**: 在资源受限环境执行 `dbt build` 时，必须通过 `--threads 1` 或环境变量限制并发，防止数据库锁冲突 (Deadlock) 或内存溢出导致的挂起。

## 3. dbt 构建顺序与 Seed 依赖规范 (Build Order) [MANDATORY]

> **背景**：全量部署或 Schema 变更后，若跳过 `dbt seed` 直接执行 `dbt run`，会因维度映射表（如 Nexus 存储成本映射）不存在而导致 Mart 层模型崩溃。

- **标准构建顺序**（首次部署 / CI 全量）：
  ```bash
  dbt seed          # 1. 载入静态维度数据（成本映射、状态映射等）
  dbt run           # 2. 执行模型转换（stg → int → fct）
  dbt test          # 3. 质量哨兵验证
  ```
  或直接使用：`dbt build`（等价于上述三步串联，推荐 CI 环境使用）。
- **增量构建**（日常开发）：允许仅执行 `dbt run --select <model>`，但前提是 seed 数据已存在。
- **seed 文件变更触发条件**：新增映射条目、修改维度值、首次部署新环境——任意一种情况**必须**重新执行 `dbt seed`。
- **并发控制**：资源受限环境（如开发机）必须加 `--threads 1`，防止锁冲突导致挂起。

## 4. BI 与可视化平台 (BI & Visualization)

- **平台选型 (Platform Selection)**:
  - **Streamlit (已集成 ✅)**: 核心 BI 交互平台。用于轻量级、交互式数据应用开发，特别是涉及 Python 逻辑的动态看板。
  - **Superset**: 企业级可视化大盘，用于处理大规模 SQL 聚合报表。
  - **Metabase**: 用于业务侧自服务查询 (Self-service BI) 与快速简单看板搭建。
- **数据源接入 (Data Source Access)** [MANDATORY]:
  - **逻辑层对齐**: 所有的看板查询必须严格区分底层。
  - **ORM/物理表优先**: Streamlit 看板连接 PostgreSQL 业务库时，**必须**直接使用 ORM 定义的物理表名（如 `gitlab_commits`），严禁使用 dbt 专属的 `stg_` 前缀，除非该视图已被显式物化。
  - **隔离性**: 严禁在看板 SQL 中硬编码 schema 名称，统一直连 public schema。

## 5. 看板数据访问协议 (Dashboard Data Access Protocol) [NEW]

> **背景**: 为了防止开发者混淆 dbt 的 stg(Staging) 层视图与 PostgreSQL 业务物理表，特制定此强制对齐协议。

- **1. 命名空间禁令 (Naming Prohibition)** [MANDATORY]:
  - 在 `dashboard/pages/` 下的所有 Python 脚本中，SQL 查询语句中**严禁出现**以 `stg_` 开头的表名（这些是 dbt 的临时/中间视图，属于 Analytics 层，对 Dashboard 往往不可见或不稳定）。
- **2. 物理表对齐清单 (Physical Table Mapping)**:
  - 凡是查询 GitLab 数据，必须对应表：`gitlab_commits`, `gitlab_merge_requests`, `gitlab_projects`。
  - 凡是查询禅道数据，必须对应表：`zentao_issues`, `zentao_executions`。
  - 关联追踪表对应：`mdm_traceability_links`。
- **3. ID 与 Hash 关联规程**:
  - 在 dashboard SQL 中，关联 commit 请使用 `id` (即 full SHA)；关联 MR 请使用 `id` (BigInt)。严禁混淆 `raw_id` 与物理 `id`。
- **4. 性能与安全**:
  - 看板 SQL 必须包含 `LIMIT`（如果是在列表显示中）。
  - 必须使用 `sqlalchemy.sql.text` 并通过 `params` 传参，严禁 f-string 拼接 SQL。
