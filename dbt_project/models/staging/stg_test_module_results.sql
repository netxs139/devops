
{{
    config(
        materialized='view',
        tags=['staging', 'test_module', 'gtm']
    )
}}

/*
    GTM 测试执行结果 Staging 层
    源表: gtm_test_execution_records (test_module 物理包)
    作用: 标准化列名，供 int_unified_test_results 使用
*/

with source as (
    select * from {{ source('raw', 'gtm_test_execution_records') }}
),

renamed as (
    select
        execution_id,
        test_case_id,
        execution_status,       -- Passed / Failed / Blocked / Skipped
        executed_by_user_id,
        gitlab_pipeline_id,     -- 关联的 CI 流水线 (可为空)
        executed_at,
        duration_seconds,
        failure_reason,
        environment,
        created_at,
        updated_at
    from source
)

select * from renamed
