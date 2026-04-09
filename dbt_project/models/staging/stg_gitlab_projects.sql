
with source as (
    select * from {{ source('raw', 'gitlab_projects') }}
),

renamed as (
    select
        id as gitlab_project_id,
        name as project_name,
        path_with_namespace,
        description,
        cast(created_at as timestamp with time zone) at time zone 'UTC' as created_at,
        cast(last_activity_at as timestamp with time zone) at time zone 'UTC' as last_activity_at,
        coalesce(cast(nullif(trim(both '"' from (raw_data->>'archived')), '') as boolean), false) as is_archived
    from source
)

select * from renamed
