"""Quality Core Service.

封装代码质量、安全扫描与架构防腐相关的统一查询层。
"""

from sqlalchemy.orm import Session

from devops_collector.core import security
from devops_collector.models.base_models import User
from devops_collector.models.dependency import DependencyScan
from devops_collector.plugins.gitlab.models import GitLabProject
from devops_collector.plugins.sonarqube.models import SonarProject


class QualityService:
    """处理安全扫描报告与质量指标的查询。"""

    def __init__(self, session: Session):
        """Magic method."""
        self.session = session

    def get_scan(self, scan_id: int):
        """按 ID 查询依赖扫描报告。"""
        return self.session.query(DependencyScan).get(scan_id)

    def list_dependency_scans(self, current_user: User):
        """获取 Dependency Check 扫描结果（支持组织隔离）。"""
        query = self.session.query(DependencyScan).join(GitLabProject)

        # 应用安全策略 (RLS)
        if current_user.role != security.ADMIN_ROLE_KEY:
            # 获取用户所属组织范围
            scope_ids = security.get_user_org_scope_ids(self.session, current_user)
            # 仅显示该组织下的项目扫描记录
            query = query.filter(GitLabProject.organization_id.in_(scope_ids))

        return query.all()

    def export_sonar_quality_report(self) -> str:
        """导出 SonarQube 全量度量数据的 CSV 字符串。"""
        import csv
        import io

        projects = self.session.query(SonarProject).all()
        if not projects:
            return ""

        headers = [
            "Project Key",
            "Project Name",
            "总行数",
            "代码行数",
            "类数量",
            "方法数量",
            "语句数量",
            "文件数",
            "Bugs",
            "安全漏洞",
            "安全热点",
            "注释率%",
            "覆盖率%",
            "圈复杂度",
            "认知复杂度",
            "重复行率%",
            "债务率%",
            "开发总工时(人月)",
            "阻塞级Bugs",
            "严重级Bugs",
            "主要级Bugs",
            "次要级Bugs",
            "信息级Bugs",
            "阻塞级漏洞",
            "严重级漏洞",
            "MAJOR级漏洞",
            "MINOR级漏洞",
            "INFO级漏洞",
            "质量门禁状态",
        ]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)

        for p in projects:
            m = p.latest_measure
            if not m:
                continue

            row = [
                p.key,
                p.name,
                m.lines,
                m.ncloc,
                m.classes,
                m.functions,
                m.statements,
                m.files,
                m.bugs,
                m.vulnerabilities,
                m.security_hotspots,
                f"{m.comment_lines_density or 0:.1f}",
                f"{m.coverage or 0:.1f}",
                m.complexity,
                m.cognitive_complexity,
                f"{m.duplicated_lines_density or 0:.1f}",
                f"{m.sqale_debt_ratio or 0:.1f}",
                m.dev_cost,
                m.bugs_blocker,
                m.bugs_critical,
                m.bugs_major,
                m.bugs_minor,
                m.bugs_info,
                m.vulnerabilities_blocker,
                m.vulnerabilities_critical,
                m.vulnerabilities_major,
                m.vulnerabilities_minor,
                m.vulnerabilities_info,
                m.quality_gate_status or "UNKNOWN",
            ]
            writer.writerow(row)

        return output.getvalue()
