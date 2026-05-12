"""数据对齐审计报告 (Orphan Alignment Audit) 生成命令。

扫描目前未关联到 MDM 项目主数据的 GitLab 仓库和禅道迭代，生成 Markdown 格式的审计报告。
"""

from sqlalchemy import text

from devops_collector.core.management import BaseCommand


class Command(BaseCommand):
    help = "导出对齐审计报告：识别未对齐的项目资产并生成修复建议"

    def add_arguments(self, parser):
        parser.add_argument("-o", "--output", default="alignment_audit_report.md", help="输出路径 (默认: alignment_audit_report.md)")

    def handle(self, *args, **options):
        output_path = options["output"]

        self.stdout.write("正在分析跨系统资产对齐情况...\n")

        try:
            # 1. 未对齐的 GitLab 仓库
            query_gitlab = text("""
                SELECT project_name, path_with_namespace
                FROM int_entity_alignment
                WHERE master_entity_id IS NULL
                ORDER BY path_with_namespace
            """)
            rows_gitlab = self.session.execute(query_gitlab).fetchall()

            # 2. 未对齐的禅道执行/迭代
            query_zentao = text("""
                SELECT execution_id, execution_name
                FROM stg_zentao_executions
                WHERE mdm_project_id IS NULL
                ORDER BY execution_name
            """)
            rows_zentao = self.session.execute(query_zentao).fetchall()

            # 3. MDM 项目参考
            query_mdm = text("""
                SELECT project_code, project_name
                FROM dim_projects
            """)
            rows_mdm = self.session.execute(query_mdm).fetchall()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# 数据对齐审计报告 (Orphan Alignment Audit)\n\n")
                f.write(f"> **生成时间**: {self.now_str}\n")
                f.write("> **说明**：以下资产目前未关联到 MDM 项目主数据，导致其指标无法汇总到报表大屏。\n\n")

                f.write(f"## 1. 未对齐的 GitLab 仓库 ({len(rows_gitlab)} 个)\n\n")
                f.write("| 仓库路径 (path_with_namespace) | 建议对齐方式 |\n")
                f.write("| :--- | :--- |\n")
                for row in rows_gitlab[:100]:  # 增加显示上限
                    f.write(f"| {row[1]} | 在 `projects.csv` 中添加此路径 |\n")
                if len(rows_gitlab) > 100:
                    f.write(f"| ... | 还有 {len(rows_gitlab) - 100} 条未显示 |\n")

                f.write(f"\n## 2. 未对齐的禅道执行/迭代 ({len(rows_zentao)} 个)\n\n")
                f.write("| 禅道执行名称 | 禅道 ID | 建议对齐方式 |\n")
                f.write("| :--- | :--- | :--- |\n")
                for row in rows_zentao:
                    f.write(f"| {row[1]} | {row[0]} | 在 `zentao_project_map.csv` 中添加此 ID |\n")

                f.write("\n## 3. 可用的 MDM 项目参考\n\n")
                f.write("| MDM 项目代码 | 项目名称 |\n")
                f.write("| :--- | :--- |\n")
                for row in rows_mdm:
                    f.write(f"| {row[0]} | {row[1]} |\n")

            self.stdout.write(f"✅ 审计报告已生成: {output_path}\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 报告生成失败: {e}\n")
            # 如果是因为视图不存在导致，给出提示
            if "int_entity_alignment" in str(e) or "stg_zentao_executions" in str(e):
                self.stdout.write("💡 提示：此报表依赖分析视图，请确保已执行同步和建模流程。\n")
            return False
