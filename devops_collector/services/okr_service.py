"""DevOps Collector OKR 自动化服务类

本模块负责根据 Key Result 的配置，自动从各插件数据中提取指标并更新 OKR 进度。
实现“数据驱动战略”的闭环逻辑。
"""

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from devops_collector.models.base_models import OKRKeyResult, OKRObjective
from devops_collector.plugins.gitlab.models import GitLabCommit as Commit
from devops_collector.plugins.gitlab.models import GitLabIssue as Issue
from devops_collector.plugins.sonarqube.models import SonarMeasure, SonarProject


logger = logging.getLogger(__name__)


class OKRService:
    """OKR 自动化更新服务。

    负责定期扫描 Key Result 配置，自动从各插件数据中提取指标并更新进度。
    支持 SonarQube 度量、Git 提交数及 Issue 解决数等多种动态指标。

    Attributes:
        session (Session): 数据库会话对象，用于持久化 OKR 进度。

    Example:
        service = OKRService(db_session)
        service.update_all_active_okrs()
    """

    def __init__(self, session: Session):
        """初始化 OKR 服务。

        Args:
            session (Session): SQLAlchemy 数据库会话。
        """
        self.session = session

    def update_all_active_okrs(self):
        """更新所有活跃状态目标的 KR 值。

        查询所有状态为 'active' 的 OKRObjective 关联的 Key Result，
        并逐一调用 update_key_result 进行数据同步。

        Returns:
            None
        """
        active_krs = self.session.query(OKRKeyResult).join(OKRObjective).filter(OKRObjective.status == "active").all()
        logger.info(f"Starting automatic OKR update for {len(active_krs)} Key Results")
        for kr in active_krs:
            try:
                self.update_key_result(kr)
            except Exception as e:
                logger.error(f"Failed to update KR {kr.id} ({kr.title}): {e}")
        self.session.commit()

    def update_key_result(self, kr: OKRKeyResult):
        """根据配置更新单个 KR 的当前值和进度。

        解析 KR 的 linked_metrics_config，调用相应的私有提取方法。

        Args:
            kr (OKRKeyResult): 待更新的 Key Result 实体对象。

        Returns:
            None
        """
        config = kr.linked_metrics_config
        if not config or not isinstance(config, dict):
            return
        metric_type = config.get("type")
        new_value = None
        if metric_type == "sonar":
            new_value = self._get_sonar_metric(config)
        elif metric_type == "git_commit_count":
            new_value = self._get_git_commit_count(config)
        elif metric_type == "issue_resolved_count":
            new_value = self._get_issue_resolved_count(config)
        if new_value is not None:
            kr.current_value = float(new_value)
            kr.progress = self._calculate_progress(kr)
            logger.debug(f"Updated KR {kr.id}: new_value={new_value}, progress={kr.progress}%")

    def _calculate_progress(self, kr: OKRKeyResult) -> int:
        """计算进度百分比 (0-100)。

        计算公式: (当前值 - 初始值) / (目标值 - 初始值)

        Args:
            kr (OKRKeyResult): 包含当前值、初始值和目标值的 KR 对象。

        Returns:
            int: 0 到 100 之间的整数进度百分比。返回 0 说明计算异常或未开始。
        """
        try:
            curr = float(kr.current_value or 0)
            target = float(kr.target_value or 0)
            initial = float(kr.initial_value or 0)
            if target == initial:
                return 100 if curr >= target else 0
            progress = int((curr - initial) / (target - initial) * 100)
            return max(0, min(100, progress))
        except (ValueError, TypeError, ZeroDivisionError):
            return 0

    def _get_sonar_metric(self, config: dict) -> float | None:
        """从 SonarQube 度量值中获取最新指标。

        Args:
            config (dict): 配置字典，需包含 'project_key' 和 'metric_name'。
                示例: {"project_key": "xxx", "metric_name": "coverage"}

        Returns:
            Optional[float]: 获取到的指标数值，若未找到则返回 None。
        """
        project_key = config.get("project_key")
        metric_name = config.get("metric_name")
        if not project_key or not metric_name:
            return None
        latest_measure = (
            self.session.query(SonarMeasure).join(SonarProject).filter(SonarProject.key == project_key).order_by(SonarMeasure.analysis_date.desc()).first()
        )
        if latest_measure:
            value = getattr(latest_measure, metric_name, None)
            if value is not None:
                return float(value)
        return None

    def _get_git_commit_count(self, config: dict) -> int:
        """从 Git 提交记录中统计提交数。

        Args:
            config (dict): 配置字典，需包含 'project_id'。
                示例: {"project_id": 123}

        Returns:
            int: 提交总数。
        """
        project_id = config.get("project_id")
        if not project_id:
            return 0
        count = self.session.query(func.count(Commit.id)).filter_by(project_id=project_id).scalar()
        return count or 0

    def _get_issue_resolved_count(self, config: dict) -> int:
        """从 Issue 记录中统计已解决数量。

        Args:
            config (dict): 配置字典，需包含 'project_id'，可选 'state'。
                示例: {"project_id": 123, "state": "closed"}

        Returns:
            int: 已解决数量。
        """
        project_id = config.get("project_id")
        state = config.get("state", "closed")
        if not project_id:
            return 0
        count = self.session.query(func.count(Issue.id)).filter_by(project_id=project_id, state=state).scalar()
        return count or 0

    def sync_okrs_from_csv(self, csv_path, progress_callback=None):
        """从 CSV 文件同步 OKR 主数据（Objective + Key Results）。

        该方法实现了 Command 层的业务逻辑下沉，确保 CLI 和 Web 端共用一套同步逻辑。
        """
        import csv
        import uuid

        from devops_collector.core.management import build_user_indexes, resolve_user
        from devops_collector.models.base_models import Organization

        email_idx, name_idx = build_user_indexes(self.session)
        processed_objectives = {}

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            o_title = row.get("目标标题", "").strip()
            o_desc = row.get("目标描述", "").strip()
            org_name = row.get("组织名称", "").strip()
            owner_val = row.get("负责人", row.get("负责人邮箱", "")).strip()
            period = row.get("周期", "").strip()
            kr_title = row.get("关键结果标题", "").strip()
            target_str = row.get("目标值", "0")
            current_str = row.get("当前值", "0")
            unit = row.get("单位", "").strip()

            if not o_title or not period:
                if progress_callback:
                    progress_callback()
                continue

            target = float(target_str) if target_str else 0.0
            current = float(current_str) if current_str else 0.0

            org = self.session.query(Organization).filter(Organization.org_name == org_name).first()
            owner_id = resolve_user(owner_val, email_idx, name_idx, "负责人")

            if not org or not owner_id:
                if progress_callback:
                    progress_callback()
                continue

            # 获取或创建 Objective
            obj_key = (o_title, period, org.id)
            if obj_key not in processed_objectives:
                obj = self.session.query(OKRObjective).filter_by(title=o_title, period=period, org_id=org.id).first()
                if not obj:
                    obj = OKRObjective(
                        objective_id=f"OBJ-{period}-{uuid.uuid5(uuid.NAMESPACE_DNS, o_title).hex[:8].upper()}",
                        title=o_title,
                        description=o_desc,
                        period=period,
                        owner_id=owner_id,
                        org_id=org.id,
                        status="ACTIVE",
                    )
                    self.session.add(obj)
                    self.session.flush()
                processed_objectives[obj_key] = obj
            else:
                obj = processed_objectives[obj_key]

            # 创建/更新 Key Result
            if kr_title:
                progress_val = round(current / target, 4) if target > 0 else 0.0
                kr = self.session.query(OKRKeyResult).filter_by(objective_id=obj.id, title=kr_title).first()
                if not kr:
                    self.session.add(
                        OKRKeyResult(
                            objective_id=obj.id,
                            title=kr_title,
                            target_value=target,
                            current_value=current,
                            unit=unit,
                            owner_id=owner_id,
                            progress=progress_val,
                        )
                    )
                else:
                    kr.current_value = current
                    kr.progress = progress_val

            if progress_callback:
                progress_callback()

        self.session.flush()
        return len(rows)
