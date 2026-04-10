import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dashboard.utils import run_query

# Page Configuration
st.set_page_config(page_title="Data Quality Monitor", page_icon="🛡️", layout="wide")

# Custom CSS for Apple Style Glassmorphism
st.markdown("""
<style>
    :root {
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
        --primary-color: #0A84FF;
        --success-color: #30D158;
        --warning-color: #FF9F0A;
        --error-color: #FF453A;
    }
    
    .stApp {
        background: linear-gradient(135deg, #000000 0%, #1c1c1e 100%);
    }
    
    .metric-card {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        min-height: 180px;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 10px 0;
        font-family: 'Outfit', sans-serif;
    }
    
    .metric-label {
        color: #8E8E93;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .status-safe { background: rgba(48, 209, 88, 0.2); color: #30D158; border: 1px solid #30D158; }
    .status-warn { background: rgba(255, 159, 10, 0.2); color: #FF9F0A; border: 1px solid #FF9F0A; }
    .status-danger { background: rgba(255, 69, 58, 0.2); color: #FF453A; border: 1px solid #FF453A; }
    
    /* Animation */
    .fade-in {
        animation: fadeIn 0.8s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# Data Fetching
@st.cache_data(ttl=60)
def fetch_quality_metrics():
    try:
        # 强制查询 Marts 层 (符合 contexts.md#7.4.2)
        df = run_query("SELECT * FROM public_marts.rpt_system_data_quality")
        return df
    except Exception as e:
        st.error(f"Failed to fetch metrics: {e}")
        return pd.DataFrame()

df_metrics = fetch_quality_metrics()

# Title Section
st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
st.title("🛡️ Data Quality Monitor")
st.markdown("Automated data integrity audit and synchronization health dashboard.")
st.markdown("</div>", unsafe_allow_html=True)

if df_metrics.empty:
    st.warning("⚠️ No quality metrics found. Please ensure dbt models are manifested and sources are synchronized.")
    # Show how to sync
    with st.expander("How to sync data?"):
        st.code("make sync-all && make dbt-build")
else:
    # Ensure datetime format
    df_metrics['last_sync_time'] = pd.to_datetime(df_metrics['last_sync_time'])
    
    # Aggregated KPIs
    avg_success_rate = df_metrics['success_rate_pct'].mean()
    total_anomalies = df_metrics['total_anomalies'].max()
    latest_sync = df_metrics['last_sync_time'].max()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        color = "var(--success-color)" if avg_success_rate > 95 else "var(--warning-color)"
        st.markdown(f"""
        <div class='metric-card fade-in'>
            <div class='metric-label'>Avg Sync Success</div>
            <div class='metric-value' style='color: {color}'>{avg_success_rate:.1f}%</div>
            <span class='status-badge status-{"safe" if avg_success_rate > 95 else "warn"}'>{'Healthy' if avg_success_rate > 95 else 'Attention'}</span>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        color = "var(--error-color)" if total_anomalies > 5 else "var(--success-color)"
        st.markdown(f"""
        <div class='metric-card fade-in'>
            <div class='metric-label'>Detected Anomalies</div>
            <div class='metric-value' style='color: {color}'>{total_anomalies}</div>
            <span class='status-badge status-{"danger" if total_anomalies > 5 else "safe"}'>{'Audit Guarded' if total_anomalies == 0 else 'Review Needed'}</span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        sync_str = latest_sync.strftime('%H:%M:%S') if pd.notnull(latest_sync) else "N/A"
        date_str = latest_sync.strftime('%Y-%m-%d') if pd.notnull(latest_sync) else "N/A"
        st.markdown(f"""
        <div class='metric-card fade-in'>
            <div class='metric-label'>Latest Sync</div>
            <div class='metric-value' style='font-size: 1.25rem; margin-top: 25px;'>{sync_str}</div>
            <div style='color: #8E8E93; font-size: 0.8rem; margin-bottom: 10px;'>{date_str}</div>
            <span class='status-badge status-safe'>Live</span>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class='metric-card fade-in'>
            <div class='metric-label'>Data Tier</div>
            <div class='metric-value'>MARTS</div>
            <span class='status-badge status-safe'>ISO Verified</span>
        </div>
        """, unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)

    # Detailed Table
    st.subheader("System Synchronicity Breakdown")
    display_df = df_metrics[['source_system', 'total_sync_tasks', 'success_count', 'failure_count', 'success_rate_pct', 'last_sync_time']]
    st.dataframe(display_df, use_container_width=True)

    # Trend Chart
    st.subheader("Sync Success Rates by Source")
    st.bar_chart(df_metrics.set_index('source_system')['success_rate_pct'])

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data Source: ISO Marts Layer")
