"""初始化 SonarQube 项目与 MDM 资产的关联。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from devops_collector.models import Product, ProjectMaster
from devops_collector.plugins.sonarqube.models import SonarProject


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
SONAR_MAP_CSV = SAMPLE_DATA_DIR / "sonarqube_project_map.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化 SonarQube 项目关联。"""
    if not SONAR_MAP_CSV.exists():
        logger.warning(f"找不到 SonarQube 映射文件: {SONAR_MAP_CSV}")
        return True

    try:
        logger.info(f"从 {SONAR_MAP_CSV} 同步 SonarQube 项目关联...")

        # 预加载 MDM 数据
        projects = {p.project_code: p.id for p in session.query(ProjectMaster).filter(ProjectMaster.is_current).all()}
        products = {p.product_code: p.id for p in session.query(Product).filter(Product.is_current).all()}

        with open(SONAR_MAP_CSV, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sonar_key = row.get("sonar_project_key", "").strip()
                mdm_proj_code = row.get("mdm_project_id", "").strip()  # CSV 中通常存的是 Code
                mdm_prod_code = row.get("mdm_product_id", "").strip()

                if not sonar_key:
                    continue

                # 1. 查找或创建 Sonar 项目占位符
                project = session.query(SonarProject).filter_by(key=sonar_key).first()
                if not project:
                    project = SonarProject(key=sonar_key, name=sonar_key.split(":")[-1], qualifier="TRK")
                    session.add(project)
                    session.flush()

                # 2. 关联 MDM 项目
                if mdm_proj_code:
                    p_id = projects.get(mdm_proj_code) or projects.get(f"PROJ-{mdm_proj_code}")
                    if p_id:
                        project.mdm_project_id = p_id
                    # 尝试通过 ID 匹配 (如果 CSV 存的是数字)
                    elif mdm_proj_code.isdigit():
                        project.mdm_project_id = int(mdm_proj_code)

                # 3. 关联 MDM 产品
                if mdm_prod_code:
                    prod_id = products.get(mdm_prod_code) or products.get(f"PRD-{mdm_prod_code}")
                    if prod_id:
                        project.mdm_product_id = prod_id
                    elif mdm_prod_code.isdigit():
                        project.mdm_product_id = int(mdm_prod_code)

                logger.debug(f"已关联 SonarQube '{sonar_key}' -> Proj:{mdm_proj_code}, Prod:{mdm_prod_code}")

        session.flush()
        logger.info("✅ SonarQube 项目关联初始化完成。")
        return True
    except Exception as e:
        logger.error(f"SonarQube 关联初始化失败: {e}")
        return False


def main():
    from sqlalchemy import create_engine

    from devops_collector.config import settings

    engine = create_engine(settings.database.uri)
    with Session(engine) as session:
        if execute_command(session):
            session.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
