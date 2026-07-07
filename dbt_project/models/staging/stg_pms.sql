{{
    config(
        materialized='view',
        tags=['staging', 'pms']
    )
}}

select * from {{ ref('stg_pms_projects') }}
