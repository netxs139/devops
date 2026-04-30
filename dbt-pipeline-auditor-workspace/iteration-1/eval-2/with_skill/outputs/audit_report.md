# 🕵️ dbt Pipeline Audit Report: stg_gitlab_projects.sql

## 🟢 阻断级风险 (Blockers)

- **[Staging Purity]** 架构违规：在 `stg_gitlab_projects` 模型中使用了 `JOIN`。依据《Staging 纯洁度法则》，`stg_` 模型应为 1:1 源表映射，严禁跨表关联。
- **[SCD2 Preservation]** 数据完整性风险：关联 `mdm_organizations` 时未过滤 `is_current = true`。由于该表为 SCD Type 2 快照表，直接 Join 会导致一个项目关联到该组织的所有历史版本，造成结果集翻倍。

## 💡 修正建议

1. **移除 JOIN**：将 `org_name` 的关联逻辑移动到 `int_` (Intermediate) 层执行。
1. **强制过滤**：在 Intermediate 层关联时，必须增加 `where is_current = true`。

### 建议重构 (int_gitlab_projects.sql)

```sql
with projects as (
    select * from {{ ref('stg_gitlab_projects') }}
),
orgs as (
    select * from {{ ref('stg_mdm_organizations') }}
    where is_current = true  -- 必须锁定当前版本
)
select 
    p.*,
    o.full_name as org_name
from projects p
left join orgs o on p.org_id = o.org_id
```
