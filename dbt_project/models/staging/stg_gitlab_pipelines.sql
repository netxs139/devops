
{{
    config(
        materialized='incremental',
        unique_key='pipeline_id',
        on_schema_change='sync_all_columns',
        tags=['staging', 'gitlab', 'incremental']
    )
}}

with source as (
    select * from {{ source('raw', 'gitlab_pipelines') }}
    {% if is_incremental() %}
        where updated_at > (select max(updated_at) from {{ this }})
    {% endif %}
),

renamed as (
    select
        id as pipeline_id,
        project_id,
        status,
        ref,
        sha,
        created_at,
        updated_at,
        duration
        -- started_at and finished_at are missing in DB schema
    from source
)

select * from renamed
