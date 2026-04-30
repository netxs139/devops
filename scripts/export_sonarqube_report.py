"""SonarQube 质量中心导出脚本。

导出截图样式的 CSV 质量报告。
"""

import csv
import os
import sys


# 注入项目根目录以支持导入 (LL #28)
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devops_collector.config import settings
from devops_collector.core.plugin_loader import PluginLoader
from devops_collector.plugins.sonarqube.models import SonarProject


def export_report(output_path: str = "sonarqube_quality_report.csv"):
    """执行报表导出。"""
    # 1. 强制加载全量模型 Registry (LL #13)
    PluginLoader.load_models()

    # 2. 初始化数据库会话
    engine = create_engine(settings.database.uri)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 3. 获取所有项目及其最新指标 (Latest Snapshot)
        projects = session.query(SonarProject).all()

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

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
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
                    m.dev_cost,  # 使用我们在 Model 中定义的 hybrid_property
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

        print(f"✅ Export completed: {output_path} ({len(projects)} projects)")

    finally:
        session.close()


if __name__ == "__main__":
    export_report()
