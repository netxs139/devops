"""初始化 GitLab 身份映射 (Identity Mapping) 数据。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.append(os.getcwd())
from devops_collector.models import IdentityMapping, User


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "gitlab-user.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化 GitLab 身份映射数据。"""
    if not CSV_FILE.exists():
        logger.error(f"找不到 GitLab 用户 CSV 文件: {CSV_FILE}")
        return False

    stats = defaultdict(int)
    try:
        logger.info("=" * 60)
        logger.info("开始 GitLab 身份映射初始化 (Email 优先策略)")
        logger.info("=" * 60)

        # 预加载所有员工主数据，按 Email 和姓名建立索引
        all_users = session.query(User).filter(User.is_current).all()
        email_index = {u.primary_email.lower(): u for u in all_users if u.primary_email}
        name_index = defaultdict(list)
        for u in all_users:
            if u.full_name:
                name_index[u.full_name].append(u)

        logger.info(f"已加载 {len(email_index)} 条员工邮箱索引")
        logger.info(f"已加载 {len(name_index)} 个不同姓名")

        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                gitlab_id = row.get("GitLab用户ID", "").strip() or row.get("GITLAB ID", "").strip()
                username = row.get("用户名", "").strip() or row.get("username", "").strip()
                full_name = row.get("全名", "").strip() or row.get("Full name", "").strip()
                email = row.get("Email", "").strip().lower()

                if not gitlab_id or not username:
                    stats["skipped_invalid"] += 1
                    continue

                stats["total"] += 1
                user = None
                match_method = None

                # 策略 1: Email 精确匹配
                if email and email in email_index:
                    user = email_index[email]
                    match_method = "EMAIL"
                    stats["matched_by_email"] += 1

                # 策略 2: 姓名唯一匹配
                if not user and full_name:
                    candidates = name_index.get(full_name, [])
                    if len(candidates) == 1:
                        user = candidates[0]
                        match_method = "NAME"
                        stats["matched_by_name"] += 1
                    elif len(candidates) > 1:
                        stats["skipped_duplicate_name"] += 1
                        continue

                # 策略 3: 无法匹配
                if not user:
                    stats["skipped_no_match"] += 1
                    continue

                # 创建或更新 IdentityMapping
                mapping = session.query(IdentityMapping).filter_by(source_system="gitlab", external_user_id=str(gitlab_id)).first()
                confidence = 1.0 if match_method == "EMAIL" else 0.8

                # 检查此 global_user_id 是否已经绑定了其他的 gitlab_id
                other_mapping = session.query(IdentityMapping).filter_by(source_system="gitlab", global_user_id=user.global_user_id).first()

                if other_mapping and (not mapping or other_mapping.id != mapping.id):
                    stats["skipped_duplicate_user"] += 1
                    continue

                if not mapping:
                    mapping = IdentityMapping(
                        global_user_id=user.global_user_id,
                        source_system="gitlab",
                        external_user_id=str(gitlab_id),
                        external_username=username,
                        external_email=email if email else None,
                        mapping_status="VERIFIED",
                        confidence_score=confidence,
                    )
                    session.add(mapping)
                    stats["created"] += 1
                else:
                    mapping.global_user_id = user.global_user_id
                    mapping.external_username = username
                    mapping.external_email = email if email else mapping.external_email
                    mapping.mapping_status = "VERIFIED"
                    mapping.confidence_score = confidence
                    stats["updated"] += 1

        session.flush()

        # 输出统计报告
        logger.info("=" * 60)
        logger.info("GitLab 身份映射初始化完成!")
        logger.info("=" * 60)
        logger.info(f"总处理记录: {stats['total']}")
        logger.info(f"  - Email匹配: {stats['matched_by_email']}")
        logger.info(f"  - 姓名匹配: {stats['matched_by_name']}")
        logger.info(f"  - 新建映射: {stats['created']}")
        logger.info(f"  - 更新映射: {stats['updated']}")
        logger.info("跳过记录:")
        logger.info(f"  - 无法匹配: {stats['skipped_no_match']}")
        logger.info(f"  - 重名冲突: {stats['skipped_duplicate_name']}")
        logger.info(f"  - 账号冲突: {stats['skipped_duplicate_user']}")
        logger.info(f"  - 无效数据: {stats['skipped_invalid']}")

        return True
    except Exception as e:
        logger.error(f"GitLab 映射初始化失败: {e}")
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
