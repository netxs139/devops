# 🕵️ dbt Pipeline Audit Report: int_zentao_story_costs.sql

## 🟢 阻断级风险 (Blockers)
- **[JSONB Safe Extraction]** 致命风险：代码中直接使用 `cast(data->>'cost' as numeric)`。
    - **原因**：Postgres 从 JSONB 提取字符串时可能带物理双引号（如 `"123.0"`），直接强转会报 `invalid input syntax for type numeric`。
    - **风险**：此外，如果原始字段为空字符串，强转会报语法错误。

## 💡 修正建议与重构 SQL
```sql
with raw as (
    select * from {{ source('zentao', 'raw_stories') }}
),
final as (
    select
        id,
        -- 使用防御性路径：清理双引号 + 处理空值
        cast(nullif(trim(both '"' from (data->>'cost')), '') as numeric) as accrued_cost,
        cast(nullif(trim(both '"' from (data->>'hours')), '') as numeric) as estimated_hours
    from raw
)
select * from final
```
