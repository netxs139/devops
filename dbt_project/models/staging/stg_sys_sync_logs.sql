-- stg_sys_sync_logs.sql
-- 插件同步日志 Staging 层

with source as (
    select * from {{ source('raw', 'sys_sync_logs') }}
),

renamed as (
    select
        id as sync_log_id,
        project_id as master_project_id,
        external_id as source_entity_id,
        source as source_system,
        status as sync_status,
        message as sync_message,
        correlation_id,
        created_at as sync_started_at,
        updated_at as sync_finished_at
    from source
)

select * from renamed
