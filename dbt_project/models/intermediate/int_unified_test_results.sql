
{{
    config(
        materialized='table',
        tags=['intermediate', 'test_results']
    )
}}

/*
    统一测试结果引擎 (Unified Test Results Engine)

    双轨合流：GTM (内部测试管理模块) + 禅道 (ZenTao) 历史测试数据
    统一输出 5 态执行状态: Passed / Failed / Blocked / Skipped / Running
    所有结果绑定至标准 gitlab_project_id 以支持 DORA 度量关联。
*/

with

-- 轨道 A: GTM 内部测试模块
gtm_results as (
    select
        r.execution_id::text as unified_execution_id,
        r.test_case_id::text as unified_case_id,
        c.case_title,
        c.case_type,
        c.priority,
        -- 执行状态归一 (GTM 原生 4 态 -> 统一 5 态)
        case r.execution_status
            when 'Passed'  then 'Passed'
            when 'Failed'  then 'Failed'
            when 'Blocked' then 'Blocked'
            when 'Skipped' then 'Skipped'
            else 'Running'
        end as unified_status,
        r.executed_by_user_id,
        r.gitlab_pipeline_id,
        c.gitlab_project_id,
        r.executed_at,
        r.duration_seconds,
        r.failure_reason,
        r.environment,
        'GTM' as source_system
    from {{ ref('stg_test_module_results') }} r
    left join {{ ref('stg_test_module_cases') }} c
        on r.test_case_id = c.test_case_id
),

-- 轨道 B: 禅道历史测试数据 (过渡期并存)
zentao_results as (
    select
        tr.id::text as unified_execution_id,
        tr.case_id::text as unified_case_id,
        tc.title as case_title,
        'functional' as case_type,
        'P2' as priority,
        -- 执行状态归一 (禅道状态 -> 统一 5 态)
        case
            when tr.status in ('pass', 'passed')   then 'Passed'
            when tr.status in ('fail', 'failed')   then 'Failed'
            when tr.status = 'blocked'             then 'Blocked'
            when tr.status = 'skip'                then 'Skipped'
            else 'Running'
        end as unified_status,
        null::uuid as executed_by_user_id,
        null::bigint as gitlab_pipeline_id,
        null::bigint as gitlab_project_id,
        tr.created_at as executed_at,
        null::integer as duration_seconds,
        null::text as failure_reason,
        'zentao' as environment,
        'ZENTAO' as source_system
    from {{ ref('stg_zentao_test_results') }} tr
    left join {{ ref('stg_zentao_test_cases') }} tc
        on tr.case_id = tc.id
)

-- 双轨合流输出
select * from gtm_results
union all
select * from zentao_results
