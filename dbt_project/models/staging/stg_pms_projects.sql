{{
    config(
        materialized='view',
        tags=['staging', 'pms']
    )
}}

with source as (
    select * from {{ source('raw', 'pms_projects') }}
    where source = 'pms' and entity_type = 'project'
),

renamed as (
    select
        external_id as pms_project_id,
        (payload->>'project_name')::varchar as project_name,
        (payload->>'project_code')::varchar as project_code,
        (payload->>'pm_user_id')::varchar as pm_user_id,
        (payload->>'plan_start_date')::date as plan_start_date,
        (payload->>'plan_end_date')::date as plan_end_date,
        (payload->>'actual_start_at')::timestamp as actual_start_at,
        (payload->>'actual_end_at')::timestamp as actual_end_at,
        (payload->>'status')::varchar as status,
        collected_at as created_at,
        collected_at as updated_at
    from source
)

select * from renamed
