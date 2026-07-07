
{{
    config(
        materialized='view',
        tags=['staging', 'test_module', 'gtm']
    )
}}

/*
    GTM 测试用例 Staging 层
    源表: gtm_test_cases (test_module 物理包)
    作用: 标准化列名，供 int_unified_test_results 使用
*/

with source as (
    select * from {{ source('raw', 'gtm_test_cases') }}
),

renamed as (
    select
        test_case_id,
        case_title,
        case_description,
        case_type,              -- functional / performance / security
        priority,               -- P0 / P1 / P2 / P3
        status,                 -- Draft / Active / Deprecated
        gitlab_project_id,
        linked_work_item_id,    -- 关联的需求/缺陷 ID (软引用)
        created_by_user_id,
        created_at,
        updated_at
    from source
)

select * from renamed
