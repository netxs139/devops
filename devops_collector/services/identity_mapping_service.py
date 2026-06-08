"""身份映射同步服务。"""

import csv
from collections import defaultdict
from pathlib import Path

from sqlalchemy.orm import Session

from devops_collector.models import IdentityMapping, User


class IdentityMappingService:
    """管理从 CSV 或外部系统同步身份映射数据。"""

    def __init__(self, session: Session):
        """Magic method."""
        self.session = session

    def sync_gitlab_mappings(self, csv_path: Path, progress_callback=None) -> dict[str, int]:
        """从 CSV 初始化 GitLab 身份映射（Email 优先策略）。"""
        stats: dict[str, int] = defaultdict(int)

        # 预加载员工主数据，按 Email 和姓名建立索引
        all_users = self.session.query(User).filter(User.is_current).all()
        email_index = {u.primary_email.lower(): u for u in all_users if u.primary_email}
        name_index: dict[str, list] = defaultdict(list)
        for u in all_users:
            if u.full_name:
                name_index[u.full_name].append(u)

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            gitlab_id = (row.get("GitLab用户ID", "") or row.get("GITLAB ID", "")).strip()
            username = (row.get("用户名", "") or row.get("username", "")).strip()
            full_name = (row.get("全名", "") or row.get("Full name", "")).strip()
            email = (row.get("Email", "")).strip().lower()

            if not gitlab_id or not username:
                stats["skipped_invalid"] += 1
                if progress_callback:
                    progress_callback()
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
                    if progress_callback:
                        progress_callback()
                    continue

            if not user:
                stats["skipped_no_match"] += 1
                if progress_callback:
                    progress_callback()
                continue

            # 检查是否已绑定其他 gitlab_id
            mapping = self.session.query(IdentityMapping).filter_by(source_system="gitlab", external_user_id=str(gitlab_id)).first()
            confidence = 1.0 if match_method == "EMAIL" else 0.8
            other_mapping = self.session.query(IdentityMapping).filter_by(source_system="gitlab", global_user_id=user.global_user_id).first()

            if other_mapping and (not mapping or other_mapping.id != mapping.id):
                stats["skipped_duplicate_user"] += 1
                if progress_callback:
                    progress_callback()
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
                self.session.add(mapping)
                stats["created"] += 1
            else:
                mapping.global_user_id = user.global_user_id
                mapping.external_username = username
                mapping.external_email = email if email else mapping.external_email
                mapping.mapping_status = "VERIFIED"
                mapping.confidence_score = confidence
                stats["updated"] += 1

            if progress_callback:
                progress_callback()

        self.session.flush()
        return stats

    def sync_zentao_mappings(self, csv_path: Path, progress_callback=None) -> int:
        """从 CSV 初始化禅道身份映射（工号/Email 优先策略）。"""
        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        count = 0
        for row in rows:
            employee_id = row.get("工号", "").strip()
            full_name = row.get("姓名", "").strip()
            email = row.get("邮箱", "").strip()
            account = email.split("@")[0] if email else None

            if not employee_id and not email:
                if progress_callback:
                    progress_callback()
                continue

            user = None

            # 策略 1: 优先通过工号匹配
            if employee_id:
                user = self.session.query(User).filter(User.employee_id == employee_id, User.is_current).first()

            # 策略 2: 其次通过 Email 匹配
            if not user and email:
                user = self.session.query(User).filter(User.primary_email == email.lower(), User.is_current).first()

            if not user:
                if progress_callback:
                    progress_callback()
                continue

            external_id = account or email.lower()
            mapping = self.session.query(IdentityMapping).filter_by(source_system="zentao", external_user_id=external_id).first()

            if not mapping:
                mapping = IdentityMapping(
                    global_user_id=user.global_user_id,
                    source_system="zentao",
                    external_user_id=external_id,
                    external_username=full_name,
                    external_email=email.lower() if email else None,
                    mapping_status="VERIFIED",
                    confidence_score=1.0,
                )
                self.session.add(mapping)
                count += 1
            else:
                mapping.global_user_id = user.global_user_id
                mapping.mapping_status = "VERIFIED"
                mapping.confidence_score = 1.0

            if progress_callback:
                progress_callback()

        self.session.flush()
        return count
