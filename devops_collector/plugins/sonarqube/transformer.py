"""SonarQube 数据转换模块。

负责将 SonarQube API 返回的原始 JSON 数据转换为数据库模型对象。
遵循单一职责原则，将数据转换逻辑从 Worker 中剥离。
"""

import logging
from datetime import UTC, datetime

from devops_collector.core.identity_manager import IdentityManager
from devops_collector.core.utils import parse_iso8601, safe_float, safe_int

from .client import SonarQubeClient
from .models import SonarIssue, SonarMeasure, SonarProject


logger = logging.getLogger(__name__)


class SonarDataTransformer:
    """SonarQube 数据转换器。

    Attributes:
        session: SQLAlchemy 数据库会话，用于查询关联数据。
        schema_version: 数据 Schema 版本。
    """

    def __init__(self, session):
        '''"""TODO: Add description.

        Args:
            self: TODO
            session: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        self.session = session

    def transform_measures_snapshot(
        self,
        project: SonarProject,
        measures_data: dict,
        gate_status: dict = None,
        issue_dist: dict = None,
        hotspot_dist: dict = None,
    ) -> SonarMeasure:
        """解析并创建 Sonar 指标快照模型。

        Args:
            project: 关联的 SonarProject 对象。
            measures_data: 原始指标数据字典。
            gate_status: 质量门禁状态字典。
            issue_dist: 问题严重分布字典。
            hotspot_dist: 安全热点分布字典。

        Returns:
            SonarMeasure: 填充好的指标快照对象 (尚未提交到数据库)。
        """
        gate_status = gate_status or {}
        issue_dist = issue_dist or {}
        hotspot_dist = hotspot_dist or {}
        bug_dist = issue_dist.get("BUG", {})
        vul_dist = issue_dist.get("VULNERABILITY", {})
        measure = SonarMeasure(
            project_id=project.id,
            analysis_date=project.last_analysis_date or datetime.now(UTC),
            files=safe_int(measures_data.get("files")),
            lines=safe_int(measures_data.get("lines")),
            ncloc=safe_int(measures_data.get("ncloc")),
            classes=safe_int(measures_data.get("classes")),
            functions=safe_int(measures_data.get("functions")),
            statements=safe_int(measures_data.get("statements")),
            coverage=safe_float(measures_data.get("coverage")),
            bugs=safe_int(measures_data.get("bugs")),
            bugs_blocker=bug_dist.get("BLOCKER", 0),
            bugs_critical=bug_dist.get("CRITICAL", 0),
            bugs_major=bug_dist.get("MAJOR", 0),
            bugs_minor=bug_dist.get("MINOR", 0),
            bugs_info=bug_dist.get("INFO", 0),
            vulnerabilities=safe_int(measures_data.get("vulnerabilities")),
            vulnerabilities_blocker=vul_dist.get("BLOCKER", 0),
            vulnerabilities_critical=vul_dist.get("CRITICAL", 0),
            vulnerabilities_major=vul_dist.get("MAJOR", 0),
            vulnerabilities_minor=vul_dist.get("MINOR", 0),
            vulnerabilities_info=vul_dist.get("INFO", 0),
            security_hotspots=safe_int(measures_data.get("security_hotspots")),
            security_hotspots_high=hotspot_dist.get("HIGH", 0),
            security_hotspots_medium=hotspot_dist.get("MEDIUM", 0),
            security_hotspots_low=hotspot_dist.get("LOW", 0),
            code_smells=safe_int(measures_data.get("code_smells")),
            comment_lines_density=safe_float(measures_data.get("comment_lines_density")),
            duplicated_lines_density=safe_float(measures_data.get("duplicated_lines_density")),
            sqale_index=safe_int(measures_data.get("sqale_index")),
            sqale_debt_ratio=safe_float(measures_data.get("sqale_debt_ratio")),
            complexity=safe_int(measures_data.get("complexity")),
            cognitive_complexity=safe_int(measures_data.get("cognitive_complexity")),
            reliability_rating=SonarQubeClient.rating_to_letter(measures_data.get("reliability_rating")),
            security_rating=SonarQubeClient.rating_to_letter(measures_data.get("security_rating")),
            sqale_rating=SonarQubeClient.rating_to_letter(measures_data.get("sqale_rating")),
            # 新增代码指标
            new_coverage=safe_float(measures_data.get("new_coverage")),
            new_bugs=safe_int(measures_data.get("new_bugs")),
            new_vulnerabilities=safe_int(measures_data.get("new_vulnerabilities")),
            new_reliability_rating=SonarQubeClient.rating_to_letter(measures_data.get("new_reliability_rating")),
            new_security_rating=SonarQubeClient.rating_to_letter(measures_data.get("new_security_rating")),
            quality_gate_status=gate_status.get("status"),
        )
        return measure

    def transform_issue(self, project: SonarProject, i_data: dict) -> SonarIssue:
        """单条 Issue 转换（委托给批量方法以保持逻辑统一）。"""
        results = self.transform_issues_batch(project, [i_data])
        return results[0]

    def transform_issues_batch(self, project: SonarProject, issues_data: list[dict]) -> list[SonarIssue]:
        """批量解析并创建/更新 SonarIssue 模型。

        采用内存 Map 预加载 (Map Load) 模式彻底解决 N+1 查询瓶颈。 (LL #56)
        """
        if not issues_data:
            return []

        # 1. 提取所有 Key 并预加载现有记录
        issue_keys = [i_data["key"] for i_data in issues_data if "key" in i_data]
        existing_issues = {issue.issue_key: issue for issue in self.session.query(SonarIssue).filter(SonarIssue.issue_key.in_(issue_keys)).all()}

        results = []
        for i_data in issues_data:
            key = i_data.get("key")
            if not key:
                continue

            issue = existing_issues.get(key)
            if not issue:
                issue = SonarIssue(issue_key=key, project_id=project.id)
                self.session.add(issue)
                existing_issues[key] = issue  # 加入缓存映射

            # 更新属性
            issue.type = i_data.get("type")
            issue.severity = i_data.get("severity")
            issue.status = i_data.get("status")
            issue.resolution = i_data.get("resolution")
            issue.rule = i_data.get("rule")
            issue.message = i_data.get("message")
            issue.component = i_data.get("component")
            issue.line = i_data.get("line")
            issue.effort = i_data.get("effort")
            issue.debt = i_data.get("debt")

            # 身份关联
            issue.assignee = i_data.get("assignee")
            if issue.assignee:
                u = IdentityManager.get_or_create_user(self.session, "sonarqube", issue.assignee)
                if u:  # LL #72: 身份安全访问规程
                    issue.assignee_user_id = u.global_user_id

            issue.author = i_data.get("author")
            if issue.author:
                u = IdentityManager.get_or_create_user(self.session, "sonarqube", issue.author)
                if u:
                    issue.author_user_id = u.global_user_id

            issue.raw_data = i_data
            issue.creation_date = parse_iso8601(i_data.get("creationDate"))
            issue.update_date = parse_iso8601(i_data.get("updateDate"))
            issue.close_date = parse_iso8601(i_data.get("closeDate"))
            results.append(issue)

        return results
