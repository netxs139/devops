import pytest
import pandas as pd
from sqlalchemy.sql import text
import uuid

def test_fetch_traceability_query(db_session):
    """验证血缘雷达后端的 SQL 查询语法及实体链接打通情况 (事务隔离版)"""
    
    # [HARDENING] 1. 种子数据注入：确保测试环境具有确定性的数据
    # 构造一个 1024 号 Issue 的链路
    issue_id = "1024"
    commit_id = str(uuid.uuid4())
    mr_id = "55"

    # 注入基础数据 (Raw SQL 注入以验证物理链路)
    db_session.execute(text("INSERT INTO gitlab_commits (id, title, author_name) VALUES (:id, :title, :author)"),
                       {"id": commit_id, "title": "feat: traceability fix", "author": "Antigravity"})
    
    db_session.execute(text("INSERT INTO gitlab_merge_requests (id, iid, title, state) VALUES (:id, :iid, :title, :state)"),
                       {"id": 55, "iid": 55, "title": "MR 55", "state": "merged"})

    db_session.execute(text("INSERT INTO mdm_traceability_links (source_system, source_id, target_type, target_id) VALUES (:sys, :sid, :tt, :tid)"),
                       {"sys": "zentao", "sid": issue_id, "tt": "commit", "tid": commit_id})

    db_session.execute(text("INSERT INTO mdm_traceability_links (source_system, source_id, target_type, target_id) VALUES (:sys, :sid, :tt, :tid)"),
                       {"sys": "zentao", "sid": issue_id, "tt": "mr", "tid": "55"})
    
    db_session.flush()

    # [HARDENING] 2. 锁定表：防止全量测试时的并发干扰 (Postgres 独占模式)
    try:
        db_session.execute(text("LOCK TABLE mdm_traceability_links IN EXCLUSIVE MODE"))
    except Exception:
        # SQLite 不支持此语法，静默跳过（SQLite 已通过静态池保证隔离）
        pass

    # 3. 执行核心 SQL 逻辑
    query = text("""
        SELECT
            l.target_type,
            l.target_id,
            c.title as commit_title,
            c.author_name as commit_author,
            c.committed_date,
            m.iid as mr_iid,
            m.state as mr_state
        FROM mdm_traceability_links l
        LEFT JOIN gitlab_commits c ON l.target_type = 'commit' AND l.target_id = c.id
        LEFT JOIN gitlab_merge_requests m ON l.target_type = 'mr' AND l.target_id = CAST(m.id AS TEXT)
        WHERE l.source_system = 'zentao' AND l.source_id = :issue_id
    """)

    # 使用 db_session 的 connection 执行查询以保持事务一致性
    conn = db_session.connection()
    df = pd.read_sql(query, conn, params={"issue_id": issue_id})

    # 4. 严格断言
    print(f"✅ SQL 查询执行成功！返回结果行数: {len(df)}")
    assert len(df) == 2, f"应返回 2 条链路，实际返回 {len(df)}"
    assert "target_type" in df.columns
    assert "commit_title" in df.columns
    
    # 验证数据准确性
    commits_df = df[df["target_type"] == "commit"]
    assert commits_df.iloc[0]["commit_title"] == "feat: traceability fix"
    
    mrs_df = df[df["target_type"] == "mr"]
    assert mrs_df.iloc[0]["mr_state"] == "merged"
    
    print("✅ 逻辑隔离校验与引擎穿透全部通过。")
