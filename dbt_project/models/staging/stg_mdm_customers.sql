
{{
    config(
        materialized='view',
        tags=['staging', 'mdm', 'customers']
    )
}}

with source as (
    select * from {{ source('raw', 'mdm_customers') }}
),

renamed as (
    select
        customer_id,
        customer_name,
        customer_short_name,
        usci,                   -- 统一社会信用代码
        industry_code,
        industry_name,
        customer_tier,          -- S / A / B / C
        sales_owner_user_id,
        is_active,
        created_at,
        updated_at
    from source
)

select * from renamed
