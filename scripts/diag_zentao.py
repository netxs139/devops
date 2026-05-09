"""禅道 (ZenTao) 连接与模型诊断脚本。

支持 CLI Phase 2 (Native Mode) 协议。
"""

import logging
import sys
from pathlib import Path

import requests
from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from devops_collector.config import settings
from devops_collector.plugins.zentao.models import ZenTaoProduct
from scripts.utils import DiagHelper


logger = logging.getLogger(__name__)


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 诊断禅道 API 与数据库映射。"""
    DiagHelper.print_header("禅道专项诊断")

    # 1. 配置检查
    print(f"   URL: {settings.zentao.url}")
    print(f"   Token: {settings.zentao.token[:5]}***")

    # 2. API 连通性
    def check_api():
        # 针对不同版本的禅道尝试不同的 Header
        token_headers = [{"Token": settings.zentao.token}, {"x-zentao-token": settings.zentao.token}, {"Authorization": f"Bearer {settings.zentao.token}"}]

        last_err = None
        for h in token_headers:
            try:
                resp = requests.get(f"{settings.zentao.url}/products", headers=h, verify=False, timeout=5)
                if resp.status_code == 200:
                    count = len(resp.json().get("products", []))
                    DiagHelper.log_success(f"API 连通成功 (Header: {list(h.keys())[0]}), 发现 {count} 个产品")
                    return True
                last_err = f"HTTP {resp.status_code}"
            except Exception as e:
                last_err = str(e)

        DiagHelper.log_failure(f"API 所有认证方式均失败: {last_err}")
        return False

    api_ok, _ = DiagHelper.run_check("API 连通性", check_api)

    # 3. 数据库映射
    def check_db():
        p_count = session.query(ZenTaoProduct).count()
        DiagHelper.log_success(f"数据库映射正常, 本地缓存 ZenTaoProduct 记录数: {p_count}")
        return True

    db_ok, _ = DiagHelper.run_check("数据库映射", check_db)

    DiagHelper.print_footer()
    return (api_ok and db_ok) is True


def main():
    from sqlalchemy import create_engine

    from devops_collector.config import settings

    engine = create_engine(settings.database.uri)
    with Session(engine) as session:
        execute_command(session)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
