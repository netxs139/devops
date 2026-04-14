import os
import sys

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.sql import text
from dashboard.common.db import get_db_engine
import pandas as pd

def test_fetch_traceability_query():
    """验证血缘雷达后端的 SQL 查询语法及实体链接打通情况"""
    engine = get_db_engine()
    
    # 抽取出来的和 22_Code_Traceability.py 同样的数据查询引擎
    query = text("""
        SELECT 
            l.target_type, 
            l.target_id, 
            c.title as commit_title, 
            c.author_name as commit_author, 
            c.committed_date,
            c.web_url as commit_url,
            m.title as mr_title,
            m.state as mr_state,
            m.merged_at,
            m.web_url as mr_url
        FROM mdm_traceability_links l
        LEFT JOIN gitlab_commits c ON l.target_type = 'commit' AND l.target_id = c.id
        LEFT JOIN gitlab_merge_requests m ON l.target_type = 'mr' AND l.target_id = m.id::text
        WHERE l.source_system = 'zentao' AND l.source_id = :issue_id
    """)
    
    try:
        with engine.connect() as conn:
            # 模拟用户输入单个 Issue ID (假设 1024)
            df = pd.read_sql(query, conn, params={"issue_id": "1024"})
            
        print(f"✅ SQL 查询执行成功！返回结果行数: {len(df)}")
        print(f"📊 列映射验证: {list(df.columns)}")
        assert 'target_type' in df.columns, "缺少 target_type 列"
        assert 'commit_title' in df.columns, "缺少 commit_title 列"
        assert 'mr_state' in df.columns, "缺少 mr_state 列"
        
        # 验证分离逻辑边界 (空集状态下的防御能力)
        commits_df = df[df['target_type'] == 'commit'].dropna(subset=['commit_title'])
        mrs_df = df[df['target_type'] == 'mr'].dropna(subset=['mr_title'])
        print(f"🔍 解析分离: 包含 {len(commits_df)} 个 Commit，{len(mrs_df)} 个 MR。")
        print("✅ 逻辑隔离校验与引擎穿透全部通过。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_fetch_traceability_query()
