
{{
    config(
        materialized='table',
        tags=['intermediate', 'work_items']
    )
}}

/*
    统一工作项引擎 (Unified Work Items Engine) v2

    该模型整合了来自 GitLab 和禅道的所有任务、需求和缺陷。
    Jira 数据源已于 2026-07 迁移至 PMS (自研项目管理系统)；
    历史 Jira 数据通过存量数据归档保留，不再实时同步。
*/

with

-- 1. 来自 GitLab 的工作项
gitlab_items as (
    select
        issue_id::text as work_item_id,
        iid::text as work_item_key,
        project_id::text as source_project_id,
        title,
        state as current_status,
        'Issue' as work_item_type,
        created_at,
        updated_at,
        closed_at,
        author_user_id,
        'GITLAB' as source_system,
        time_estimate as estimate_seconds,
        total_time_spent as spent_seconds
    from {{ ref('stg_gitlab_issues') }}
),

-- 2. 来自禅道的工作项 (双轨过渡期并存)
zentao_items as (
    select
        issue_unique_id as work_item_id,
        raw_id::text as work_item_key,
        coalesce(execution_id::text, product_id::text) as source_project_id,
        issue_title as title,
        issue_status as current_status,
        case
            when issue_type = 'story' then 'Story'
            when issue_type = 'bug'   then 'Bug'
            when issue_type = 'task'  then 'Task'
            else issue_type
        end as work_item_type,
        created_at,
        updated_at,
        closed_at,
        assigned_to_user_id as author_user_id,
        'ZENTAO' as source_system,
        coalesce(nullif(trim(both '"' from estimate#>>'{}'  ), ''), '0')::numeric * 3600 as estimate_seconds,
        coalesce(nullif(trim(both '"' from consumed#>>'{}'  ), ''), '0')::numeric * 3600 as spent_seconds
    from {{ ref('stg_zentao_issues') }}
)

-- 3. 最终汇总 (GitLab + ZenTao 双轨)
select * from gitlab_items
union all
select * from zentao_items
