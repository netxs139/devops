-- 确保每个 MDM 实体在 SCD2 切片模型中，每个主键最多只有一个 is_current = true 的记录
-- 防止 GetOrCreate 并发更新导致的历史血缘分叉

with

identities as (
    select 
        cast(global_user_id as text) as entity_id, 
        'mdm_identities' as source_table,
        count(*) as current_count
    from {{ source('raw', 'mdm_identities') }}
    where is_current = true
    group by global_user_id
    having count(*) > 1
),

organizations as (
    select 
        cast(id as text) as entity_id, 
        'mdm_organizations' as source_table,
        count(*) as current_count
    from {{ source('raw', 'mdm_organizations') }}
    where is_current = true
    group by id
    having count(*) > 1
),

projects as (
    select 
        cast(id as text) as entity_id, 
        'mdm_projects' as source_table,
        count(*) as current_count
    from {{ source('raw', 'mdm_projects') }}
    where is_current = true
    group by id
    having count(*) > 1
)

select * from identities
union all
select * from organizations
union all
select * from projects
