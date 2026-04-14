import pandas as pd
import streamlit as st
from sqlalchemy.sql import text

from dashboard.common.db import get_db_engine


# --- 页面基础配置 ---
st.set_page_config(page_title="代码血缘雷达", page_icon="🧬", layout="wide")

# --- 样式美化 ---
st.markdown(
    """
<style>
    .trace-card {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .trace-title { font-weight: bold; font-size: 1.1rem; color: #e2e8f0; }
    .trace-meta { font-size: 0.9rem; color: #94a3b8; }
    .status-badge {
        display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;
    }
    .status-merged { background: #10b981; color: white; }
    .status-open { background: #3b82f6; color: white; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🧬 血缘雷达 (Traceability Radar)")
st.markdown("### 端到端溯源：从禅道需求/Bug 到 GitLab 源码提交的完整生命周期")
st.info("💡 **用途**：输入禅道单号，即可一键追溯修复该问题的全部 **代码 Commit**、是谁写的、以及最终被哪次 **Merge Request** 合并。")

# --- 搜索输入 ---
st.header("1. 开始溯源")
col1, col2 = st.columns([1, 2])
with col1:
    issue_id = st.text_input("📝 输入禅道单号 (例如: 1024)", placeholder="仅输入数字字母...")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_btn = st.button("🚀 追溯渲染 (Trace)", type="primary")


# --- 数据拉取与渲染 ---
@st.cache_data(ttl=60)
def fetch_traceability(issue_id: str):
    engine = get_db_engine()
    query = text("""
        SELECT 
            l.target_type, 
            l.target_id, 
            c.title as commit_title, 
            c.author_name as commit_author, 
            c.committed_date,
            c.raw_data->>'web_url' as commit_url,
            m.title as mr_title,
            m.state as mr_state,
            m.merged_at,
            m.raw_data->>'web_url' as mr_url
        FROM mdm_traceability_links l
        LEFT JOIN gitlab_commits c ON l.target_type = 'commit' AND l.target_id = c.id
        LEFT JOIN gitlab_merge_requests m ON l.target_type = 'mr' AND l.target_id = m.id::text
        WHERE l.source_system = 'zentao' AND l.source_id = :issue_id
    """)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"issue_id": issue_id.strip()})
        return df
    except Exception as e:
        st.error(f"查询失败: {e}")
        return pd.DataFrame()


if search_btn and issue_id:
    with st.spinner("🕵️‍♂️ 正在潜入数据湖中穿透血缘..."):
        df = fetch_traceability(issue_id)

    if df.empty:
        st.warning(f"⚠️ 未找到单号 `#{issue_id}` 的任何关联代码记录。原因可能是：\n1. 开发提交代码时未在注释中填写 `#{issue_id}`\n2. 爬虫任务暂未同步该记录")
    else:
        st.success(f"✅ 成功命中 **{len(df)}** 条追溯记录！")

        # 分离 Commit 和 MR
        commits_df = df[df["target_type"] == "commit"].dropna(subset=["commit_title"])
        mrs_df = df[df["target_type"] == "mr"].dropna(subset=["mr_title"])

        st.divider()
        st.header(f"🔗 血缘图谱: 禅道单 `#{issue_id}`")

        c1, c2 = st.columns(2)

        # 左侧展示代码提交
        with c1:
            st.subheader("💻 源码提交 (Commits)")
            if commits_df.empty:
                st.write("暂无关联提交")
            else:
                for idx, row in commits_df.iterrows():
                    commit_hash = row["target_id"][:8]
                    commit_author = row["commit_author"] or "未知"
                    date_str = str(row["committed_date"])[:16] if pd.notnull(row["committed_date"]) else "未知时间"

                    st.markdown(
                        f"""
                    <div class="trace-card">
                        <div class="trace-title">{row["commit_title"]}</div>
                        <div class="trace-meta">
                            🏷️ Hash: <code>{commit_hash}</code> | 👤 作者: {commit_author} <br>
                            🕒 提交于: {date_str}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # 右侧展示合并请求
        with c2:
            st.subheader("🔀 合并请求 (Merge Requests)")
            if mrs_df.empty:
                st.write("暂无关联的合并请求 (可能通过 Commit 关联但未主动挂载 MR)")
            else:
                for idx, row in mrs_df.iterrows():
                    mr_state = row["mr_state"]
                    badge_class = "status-merged" if mr_state == "merged" else "status-open"
                    mr_state_zh = "已合并" if mr_state == "merged" else str(mr_state).capitalize()

                    date_str = str(row["merged_at"])[:16] if pd.notnull(row["merged_at"]) else "待合并"

                    st.markdown(
                        f"""
                    <div class="trace-card" style="border-left-color: #8b5cf6;">
                        <div class="trace-title">{row["mr_title"]}</div>
                        <div class="trace-meta">
                            <span class="status-badge {badge_class}">{mr_state_zh}</span> | 🆔 IID: {row["target_id"]} <br>
                            🚩 合并时间: {date_str}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # 底盘血缘
        st.divider()
        st.caption(
            "🔍 **血缘链提示**: 这些关系是通过自动化审计机器人解析 GitLab 提交信息中的 `#单号` 格式自动建立的。如果遗漏，请督促开发团队遵守 commit message 规范。"
        )
