"""身份自动治理引擎 — 服务层 (Identity Resolver Service).

将外部帐号对齐到 HR 金数据用户。业务逻辑从 Command 层下沉至此，
保证同一核心算法可被 CLI、API、测试无差异调用。
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import or_
from sqlalchemy.orm import Session

from devops_collector.models.base_models import IdentityMapping, User


class IdentityResolver:
    """身份治理引擎服务。

    Args:
        session: SQLAlchemy ORM Session，由调用方传入管理生命周期。
        min_score: 最低匹配置信度阈值，默认 0.6。
    """

    def __init__(self, session: Session, min_score: float = 0.6) -> None:
        self.session = session
        self.min_score = min_score

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, *, dry_run: bool = True) -> dict[str, int]:
        """执行身份治理。

        Args:
            dry_run: 若为 True，仅预览不写库；False 则实际更新。

        Returns:
            包含 ``total`` (扫描总数) 与 ``updated`` (变更数) 的统计字典。
        """
        mdm_users: Sequence[User] = (
            self.session.query(User)
            .filter(
                User.is_current,
                User.employee_id.isnot(None),
            )
            .all()
        )

        mappings: Sequence[IdentityMapping] = (
            self.session.query(IdentityMapping)
            .filter(
                or_(
                    IdentityMapping.mapping_status == "PENDING",
                    IdentityMapping.mapping_status == "AUTO",
                    IdentityMapping.confidence_score < 1.0,
                )
            )
            .all()
        )

        updated_count = 0

        for mapping in mappings:
            best_user, score = self._find_best_match(mapping, list(mdm_users))

            if best_user and score >= self.min_score:
                if mapping.global_user_id != best_user.global_user_id or mapping.confidence_score != score:
                    if not dry_run:
                        mapping.global_user_id = best_user.global_user_id
                        mapping.confidence_score = score
                        mapping.mapping_status = "AUTO" if score < 0.9 else "VERIFIED"
                    updated_count += 1

        if not dry_run:
            self.session.flush()

        return {"total": len(mappings), "updated": updated_count}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_best_match(
        self,
        mapping: IdentityMapping,
        mdm_users: list[User],
    ) -> tuple[User | None, float]:
        """计算外部帐号与 MDM 用户的最佳匹配。"""
        email = (mapping.external_email or "").lower()
        ext_username = (mapping.external_username or "").lower()
        ext_uid = (mapping.external_user_id or "").lower()
        email_prefix = email.split("@")[0] if "@" in email else None

        best_user: User | None = None
        max_score: float = 0.0

        for user in mdm_users:
            current_score: float = 0.0
            u_email = user.primary_email.lower() if user.primary_email else ""
            u_emp_id = user.employee_id.lower() if user.employee_id else ""
            u_username = user.username.lower() if user.username else ""

            if email and email == u_email:
                current_score = 1.0
            elif ext_uid == u_emp_id:
                current_score = 1.0
            elif email_prefix and email_prefix in {u_emp_id, u_username}:
                current_score = 0.8
            elif ext_username == (user.full_name.lower() if user.full_name else ""):
                current_score = 0.7 if (email and "@" in email) else 0.4

            if current_score > max_score:
                max_score = current_score
                best_user = user

            if max_score == 1.0:
                break

        return best_user, max_score
