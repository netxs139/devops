from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

from dashboard.common.api_client import api_client
from dashboard.common.db import get_db_engine


# --- Page Configuration ---
st.set_page_config(page_title="Radar Intelligence | DevOps Decision Hub", page_icon="🎯", layout="wide")

# --- Custom Styling ---
st.markdown(
    """
<style>
    .metric-card {
        background: #1e1e1e;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #333;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #66FCF1;
        margin-bottom: 8px;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- Data Fetching ---
@st.cache_data(ttl=300)
def fetch_radar_data(project_id=None, days=30):
    """Fetch radar metrics from the FastAPI backend using standard client."""
    params = {"days": days}
    if project_id:
        params["project_id"] = project_id

    return api_client.get("/api/traceability/radar", params=params)


def get_projects():
    """Get project list for filter."""
    engine = get_db_engine()
    query = text("SELECT product_id, product_name FROM mdm_products ORDER BY product_name")
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn)
    except Exception:
        return pd.DataFrame(columns=["product_id", "product_name"])


# --- UI Layout ---
st.title("🎯 效能雷达分析 (Engineering Radar Intelligence)")
st.markdown("### 研发价值流、协同质量与安全态势的深度深度度量")

# Sidebar Filters
with st.sidebar:
    st.header("🎛️ 过滤器")
    projects_df = get_projects()
    project_options = {"全局汇总": None}
    for _, row in projects_df.iterrows():
        project_options[row["product_name"]] = row["product_id"]

    selected_project_name = st.selectbox("选择产品/项目", options=list(project_options.keys()))
    selected_project_id = project_options[selected_project_name]

    days = st.slider("统计周期 (天)", 7, 180, 30)

    st.divider()
    if st.button("🔄 刷新数据"):
        st.cache_data.clear()
        st.rerun()

data = fetch_radar_data(selected_project_id, days)

if not data:
    st.warning("⚠️ 无法获取雷达数据。请确保后端 API 服务已启动。")
    st.stop()

# --- Main Dashboard ---
vsm = data.get("vsm", {})
collab = data.get("collaboration", {})
security = data.get("security", {})
eloc_data = data.get("eloc", {"labels": [], "values": []})

# 1. Top Metrics Grid
m1, m2, m3, m4 = st.columns(4)


def set_drilldown(m_type):
    st.session_state.drilldown_type = m_type


if "drilldown_type" not in st.session_state:
    st.session_state.drilldown_type = None

with m1:
    val = f"{vsm.get('avg_wait_minutes', 0):.0f}m"
    st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">平均等待响应</div></div>', unsafe_allow_html=True)
    if st.button("查看瓶颈 MR", key="btn_vsm"):
        set_drilldown("VSM_WAITING")

with m2:
    val = f"{collab.get('effective_review_rate', 0) * 100:.1f}%"
    st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">有效评审率</div></div>', unsafe_allow_html=True)

with m3:
    val = f"{collab.get('rubber_stamp_rate', 0) * 100:.1f}%"
    color = "#ff4b4b" if collab.get("rubber_stamp_rate", 0) > 0.2 else "#66FCF1"
    st.markdown(
        f'<div class="metric-card"><div class="metric-value" style="color:{color}">{val}</div><div class="metric-label">秒批率 (风险)</div></div>',
        unsafe_allow_html=True,
    )
    if st.button("查看风险 MR", key="btn_rs"):
        set_drilldown("RUBBER_STAMP")

with m4:
    val = f"{security.get('total_active', 0)}"
    st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">活跃漏洞数</div></div>', unsafe_allow_html=True)
    if st.button("查看漏洞详情", key="btn_sec"):
        set_drilldown("VULNERABILITY")

# --- Drill-down Detail Section ---
if st.session_state.drilldown_type:
    st.markdown("---")
    st.subheader(f"🔍 详情下钻: {st.session_state.drilldown_type}")

    detail_data = api_client.get(
        "/api/traceability/detail", params={"metric_type": st.session_state.drilldown_type, "project_id": selected_project_id, "days": days}
    )

    if detail_data and detail_data.get("items"):
        df_detail = pd.DataFrame(detail_data["items"])
        st.dataframe(
            df_detail,
            column_config={"url": st.column_config.LinkColumn("链接"), "timestamp": st.column_config.DatetimeColumn("发生时间"), "value": "度量值"},
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("暂无该维度的异常记录。")

    if st.button("关闭下钻"):
        st.session_state.drilldown_type = None
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# 2. Charts Row
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("🕸️ 研发协同雷达 (Collaboration Radar)")

    categories = ["流动效率", "评审深度", "非秒批率", "响应时效", "代码复杂度控制"]
    # 归一化得分逻辑
    scores = [
        vsm.get("flow_efficiency", 0.5),
        collab.get("effective_review_rate", 0.5),
        1 - collab.get("rubber_stamp_rate", 0),
        max(0, 1 - (vsm.get("avg_wait_minutes", 0) / 480)),  # 8h 阈值
        0.7,  # 预留
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(r=scores + [scores[0]], theta=categories + [categories[0]], fill="toself", line_color="#66FCF1", fillcolor="rgba(102, 252, 241, 0.2)")
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], color="#444"), bgcolor="rgba(0,0,0,0)"),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=30, l=30, r=30),
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📊 代码当量分布 (ELOC Distribution)")
    if eloc_data["labels"]:
        eloc_df = pd.DataFrame({"Contributor": eloc_data["labels"], "ELOC": eloc_data["values"]}).sort_values("ELOC", ascending=True)

        fig_eloc = px.bar(eloc_df, x="ELOC", y="Contributor", orientation="h", color="ELOC", color_continuous_scale="Viridis")
        fig_eloc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        )
        st.plotly_chart(fig_eloc, use_container_width=True)
    else:
        st.info("暂无代码当量数据")

# 3. VSM Timeline Table
st.divider()
st.subheader("🛤️ 价值流关键路径 (Value Stream Lifecycle)")
timeline = data.get("vsm_timeline", [])

if timeline:
    tm_df = pd.DataFrame(timeline)
    # 转换列名增强可读性
    tm_df.rename(
        columns={
            "id": "MR IID",
            "title": "标题",
            "draft_minutes": "准备耗时(m)",
            "wait_minutes": "等待耗时(m)",
            "review_minutes": "评审耗时(m)",
            "total_minutes": "总时长(m)",
        },
        inplace=True,
    )

    st.dataframe(
        tm_df,
        column_config={
            "MR IID": st.column_config.NumberColumn("ID"),
            "总时长(m)": st.column_config.ProgressColumn("生命周期时长", format="%d m", min_value=0, max_value=tm_df["总时长(m)"].max()),
        },
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("所选周期内无 MR 价值流数据")

# 4. Security Breakdown
st.divider()
st.subheader("🛡️ 安全漏洞态势 (Security Posture)")
sec_col1, sec_col2 = st.columns([1, 2])

with sec_col1:
    labels = ["Critical", "High", "Medium", "Low"]
    values = [security.get("critical", 0), security.get("high", 0), security.get("medium", 0), security.get("low", 0)]

    fig_sec = px.pie(
        names=labels,
        values=values,
        hole=0.4,
        color=labels,
        color_discrete_map={"Critical": "#ff4b4b", "High": "#ffa500", "Medium": "#ffff00", "Low": "#00ff00"},
    )
    st.plotly_chart(fig_sec, use_container_width=True)

with sec_col2:
    st.info(
        """
    **安全建议**:
    - 当前存在 {crit} 个 **Critical** 漏洞，建议在 24 小时内修复。
    - 漏洞响应时效：平均发现到修复时长 {sla}h (Mock数据)。
    - 建议开启 GitLab Security Scan 的自动阻塞功能。
    """.format(crit=security.get("critical", 0), sla=12.5)
    )

st.caption(f"数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 数据源: DevOps Platform API")
