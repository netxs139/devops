{{
    config(
        materialized='table',
        tags=['intermediate', 'ci']
    )
}}

/*
    GitLab & Jenkins 联合 CI 调度分析模型 (Union CI Engine)

    统一不同 CI 工具的执行状态、持续时长及关联的提交 SHA，用于构建全平台 CI 效能指标。
*/

with

gitlab_ci as (
    select
        'gitlab_' || pipeline_id::text as ci_id,
        'GITLAB' as ci_type,
        project_id::text as project_key,
        case lower(status)
            when 'success' then 'SUCCESS'
            when 'failed' then 'FAILURE'
            when 'canceled' then 'ABORTED'
            when 'running' then 'RUNNING'
            else 'UNKNOWN'
        end as status,
        coalesce(duration, 0)::numeric as duration_seconds,
        sha as commit_sha,
        created_at,
        null::text as triggered_by
    from {{ ref('stg_gitlab_pipelines') }}
),

jenkins_ci as (
    select
        'jenkins_' || build_internal_id::text as ci_id,
        'JENKINS' as ci_type,
        job_id::text as project_key,
        case upper(build_result)
            when 'SUCCESS' then 'SUCCESS'
            when 'FAILURE' then 'FAILURE'
            when 'ABORTED' then 'ABORTED'
            when 'UNSTABLE' then 'FAILURE'
            else 'UNKNOWN'
        end as status,
        coalesce(duration_ms, 0)::numeric / 1000.0 as duration_seconds,
        commit_sha,
        start_time as created_at,
        trigger_user_id::text as triggered_by
    from {{ ref('stg_jenkins_builds') }}
)

select * from gitlab_ci
union all
select * from jenkins_ci
