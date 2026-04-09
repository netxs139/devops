
with source as (
    select * from {{ source('raw', 'gitlab_commits') }}
),

renamed as (
    select
        id as commit_sha,
        project_id,
        short_id,
        title,
        author_email,
        cast(committed_date as timestamp with time zone) at time zone 'UTC' as committed_at,
        message,
        -- 使用正则提取 #123 格式的禅道 ID
        cast(substring(message from '#([0-9]+)') as integer) as zentao_id,
        eloc_score,
        impact_score,
        churn_lines,
        file_count,
        test_lines,
        comment_lines,
        refactor_ratio
    from source
)

select * from renamed
