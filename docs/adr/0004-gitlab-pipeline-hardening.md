# ADR 0004: GitLab 数据流水线韧性加固方案

**日期**: 2026-04-09
**状态**: 已接受 (Accepted)

## 1. 背景 (Context)

在 DevOps 平台的数据链路中，GitLab 作为核心源码管理源，其数据在 Staging 清洗层面临以下技术挑战：
*   **JSONB 物理陷阱**: GitLab API 返回的 Raw 数据，在 Postgres 中以 JSONB 存储。提取出的文本常带有物理引号（如 `"true"`），直接强转布尔或数值会导致全链路同步中断。
*   **类型不一致 (Cross-Source alignment)**: 提取的业务关联键（如 `zentao_id`）默认为文本，与下游强类型关联时性能低下且易报错。
*   **时区偏差**: 原始记录时间戳未执行 UTC 归一化，导致 Lead Time 等 DORA 指标计算不准。

## 2. 决策 (Decision)

我们决定对所有 GitLab Staging 模型执行以下“防御性编程”标准：

### 2.1 强制防御性 JSONB 提取 (Defensive Extraction)
所有从 `raw_data` 提取并转型的字段，必须遵循“清理 + 判空 + 转型”三部曲：
```sql
cast(nullif(trim(both '"' from (raw_data->>'key')), '') as [target_type])
```

### 2.2 时区归一化 (UTC Normalization)
所有时间戳字段必须统一重命名为 `_at` 后缀，并转换为 UTC 时区：
```sql
cast([field] as timestamp with time zone) at time zone 'UTC' as [field_at]
```

### 2.3 强类型 ID 对齐
所有跨源关联 ID 必须在 Staging 层显式转换为 `integer` 或 `bigint`，严禁在 Intermediate 层保留文本类型进行 Join。

## 3. 影响 (Consequences)

### 正面影响
*   **物理鲁棒性**: 即使上游 API 返回非标格式数据，Staging 层也能通过 `nullif` 优雅降级，防止整个 dbt 工程崩溃。
*   **指标一致性**: 统一时区基准，确保 DORA 模型计算的准确性。
*   **扫描性能**: 消除 Intermediate 层的隐式类型转换，优化索引利用率。

### 负面影响
*   **代码密度**: SQL 代码行数略有增加，需在未来的审计中作为标准审查项。

## 4. 引用 (References)
*   [ADR 0002: ID Normalization](0002-id-normalization.md)
*   [Lessons Learned #69 (JSONB Trap)](../history/lessons-learned.log)
