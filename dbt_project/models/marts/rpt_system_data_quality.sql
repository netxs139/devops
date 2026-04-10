-- rpt_system_data_quality.sql
-- 数据同步质量大屏模型 (System Data Quality Dashboard)

{{ config(
    materialized='table'
) }}

with sync_stats as (
    select
        source_system,
        count(*) as total_sync_tasks,
        sum(case when sync_status = 'SUCCESS' then 1 else 0 end) as success_count,
        sum(case when sync_status = 'FAILED' then 1 else 0 end) as failure_count,
        max(sync_finished_at) as last_sync_time
    from {{ ref('stg_sys_sync_logs') }}
    group by 1
),

audit_stats as (
    select
        'Audit Guard Anomalies' as indicator_name,
        count(*) as total_records,
        sum(case when is_anomaly = true then 1 else 0 end) as anomaly_count
    from {{ ref('fct_metrics_audit_guard') }}
),

final as (
    select
        s.source_system,
        s.total_sync_tasks,
        s.success_count,
        s.failure_count,
        round((s.success_count::numeric / nullif(s.total_sync_tasks, 0)) * 100, 2) as success_rate_pct,
        s.last_sync_time,
        now() - s.last_sync_time as freshness_gap,
        
        -- 组合审计指标 (模拟)
        a.anomaly_count as total_anomalies,
        a.total_records as audit_total
        
    from sync_stats s
    cross join audit_stats a
)

select * from final
