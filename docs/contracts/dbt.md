# dbt 建模与可视化平台契约 (dbt Modeling & BI)

> **定位**: 本文档是 `contexts.md` 的领域扩展，涵盖 dbt 分层模型设计、JSONB 类型安全、看板数据访问约定及 BI 可视化架构。当进行 `dbt_project/` 开发或数据展现时，必须严格遵守。

## 1. dbt 数据建模与分层 (Data Transformation)



### 1.1 分层逻辑

| 层级 | 前缀 | 说明 | 数据形态 |
| :--- | :--- | :--- | :--- |
| **Staging** | `stg_` | 原始数据清洗，1:1 映射源表。**强制性规则**：严禁在 Staging 层执行业务过滤（如 `where is_current=true`），必须完整保留源表历史快照以支撑 SCD Type 2。 | 扁平模型，与源系统同构 |
| **Intermediate** | `int_` | 中间转换，跨源关联、身份/组织归一化、复杂业务逻辑组合与过滤。 | 归一化后的业务实体片段 |
| **Marts (维度)** | `dim_` | 业务维度表，描述性属性。 | 星型/雪花型建模 |
| **Marts (事实)** | `fct_` | 业务事实表，度量指标，直接对接报表层。 | 星型/雪花型建模 |

### 1.4 命名契约 (Naming Convention) [NEW]

#### 1.4.1 模型文件命名
- **Staging**: `stg_{source}_{resource}.sql` （例：`stg_gitlab_commits.sql`）
- **Intermediate**: `int_{domain}_{logic}.sql` （例：`int_org_normalization.sql`）
- **Marts**: `dim_{entity}.sql` 或 `fct_{metric_event}.sql` （例：`fct_dora_metrics_v2.sql`）

#### 1.4.2 字段命名
- **布尔值**: 强制使用 `is_` 或 `has_` 前缀（如 `is_deleted`, `has_incident`）。
- **时间戳**: 统一使用 `_at` 后缀（如 `created_at`）。日期（不含时间）使用 `_date`。
- **ID 标识符**:
  - 主键统一命名为 `{resource}_id`。
  - 跨系统主键在 `int_` 层必须归一化为 `global_user_id` 或 `master_project_id`。

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
  - 针对从源系统 `raw_data` (JSONB) 提取的字段进行转型时，必须执行以下“三板斧”清理：
    ```sql
    -- 推荐模板
    coalesce(
        nullif(trim(both '"' from raw_data->>'resolvedDate'), ''),
        '1970-01-01'::text
    )::timestamp as resolved_at
    ```
    1. **`trim(both '"' from field)`**: 清除 JSON 字面量中可能残留的物理引号，防止触发语法错误导致流水线熔断。
    2. **`nullif(..., '')`**: 将空字符串转换为真正的 `NULL`。
    3. **`coalesce`**: 为关键计算字段提供默认值。
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

## 6. 数据生命周期与清理 (Data Lifecycle)

### 6.1 软删除与存续性检查
- **僵尸数据过滤**: 所有 Marts 层模型必须基于 `mdm_systems_registry` 或拓扑表的存续性标志。
- **一致性**: 严禁在报表中展示已在源系统物理删除的“幽灵记录”，除非该记录被明确标注为 `is_historical_archive`。

### 6.2 主数据刷新规范
- **定向重置**: 主数据（组织/产品/项目）变更时，必须使用标准工具 `scripts/refresh_master_data.py` 进行定向重置，严禁手动 `TRUNCATE` 导致外键引用崩溃。

## 7. 测试分级与 CI 门禁 (Testing & CI/CD)

### 7.1 测试严重性 (Severity)
- **Error (阻断)**: 主键冲突、关键 ID 为空、数据类型溢出。必须中断 CI 流水线，禁止物化下游模型。
- **Warn (预警)**: 业务逻辑异常（如单次工时 > 24h）。允许执行完毕，但必须在大屏展示数据风险警告。

### 7.2 单元测试强制化
- 针对涉及 DORA MTTR 计算、资本化 ROI 逻辑的 `int_` 层模型，必须编写 `singular tests` 或使用模拟数据的 `unit tests` 覆盖边界场景。

## 8. 数据治理与 Schema 监控 (Governance)

### 8.1 Schema Drift 防御
- 核心 Source 必须配置 `freshness` 检查。
- 关键 Staging 模型应包含字段存续性审计，防止源端 API 结构变更导致数据静默丢失（Silent Failure）。

## 9. 高阶业务语义标准 (Advanced Semantics)

### 9.1 SCD2 冲突处理标准
- 身份与组织关联必须统一遵循：`优先查找 is_current=True` -> `失败则回溯最近历史版本` -> `仍失败则回填业务桩记录(Stub)` 的流水线逻辑。
