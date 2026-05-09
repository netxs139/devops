"""数据库专项诊断脚本。

支持 CLI Phase 2 (Native Mode) 协议。
"""

import logging
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session


# 将项目根目录添加到 python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils import DiagHelper


logger = logging.getLogger(__name__)


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 诊断数据库连接及核心数据表。"""
    DiagHelper.print_header("数据库专项诊断")

    success = True

    # 1. 检查连接与版本
    def check_version():
        result = session.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        DiagHelper.log_success(f"数据库连接成功: {version}")
        return True

    _, _ = DiagHelper.run_check("连接测试", check_version)

    # 2. 检查核心表内容
    tables = ["mdm_identities", "mdm_organizations", "mdm_products", "mdm_projects", "sys_role", "sys_menu"]

    print("\n[数据统计] 核心表记录数:")
    for table in tables:
        try:
            count_result = session.execute(text(f"SELECT count(*) FROM {table}")).fetchone()[0]
            print(f"   - {table:22}: {count_result} 条记录")
        except Exception:
            DiagHelper.log_warning(f"{table:22}: ✗ 查询失败 (可能表不存在)")
            success = False

    DiagHelper.print_footer()
    return success


def main():
    from sqlalchemy import create_engine

    from devops_collector.config import settings

    engine = create_engine(settings.database.uri)
    with Session(engine) as session:
        execute_command(session)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
