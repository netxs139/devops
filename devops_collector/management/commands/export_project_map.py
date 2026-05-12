"""项目资源拓扑图 (Project Map) 生成命令。

生成项目核心目录拓扑图，并标注 Client, Worker, Service 等核心职责，辅助开发者快速定位资源。
"""

import os
from pathlib import Path

from devops_collector.core.management import BaseCommand


class Command(BaseCommand):
    help = "导出项目地图：生成项目核心目录的职责拓扑图 (Markdown)"

    def add_arguments(self, parser):
        parser.add_argument("-o", "--output", default="docs/PROJECT_MAP.md", help="输出路径 (默认: docs/PROJECT_MAP.md)")

    def handle(self, *args, **options):
        output_file = Path(options["output"])
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 核心文件夹扫描白名单
        scan_dirs = ["devops_collector", "tests/unit/devops_collector", "devops_portal", "infrastructure/scripts"]

        self.stdout.write("正在扫描项目结构并标记职责...\n")

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# DevOps Platform 系统资源清单 (PROJECT_MAP.md)\n\n")
                f.write("> **定位**：本文件为 AI 助手（及开发者）提供全局资源导航。在寻找 Client, Worker, Test, Model 时优先读取本图谱。\n\n")

                for base_dir in scan_dirs:
                    if not os.path.exists(base_dir):
                        continue

                    f.write(f"## {base_dir}\n")
                    f.write("```text\n")

                    for root, dirs, files in os.walk(base_dir):
                        # 排除缓存和内部目录
                        dirs[:] = [d for d in dirs if d not in ["__pycache__", ".venv", ".pytest_cache", ".git"]]

                        level = root.replace(base_dir, "").count(os.sep)
                        indent = "  " * level
                        folder_name = os.path.basename(root)
                        f.write(f"{indent}{folder_name}/\n")

                        sub_indent = "  " * (level + 1)
                        for file in files:
                            if file.endswith((".py", ".sh", ".sql", ".md")) and "__init__" not in file:
                                role = self._get_role_label(file)
                                f.write(f"{sub_indent}{file}{role}\n")

                    f.write("```\n\n")

            self.stdout.write(f"✅ 项目地图已成功导出至: {output_file}\n")
            return True
        except Exception as e:
            self.stderr.write(f"❌ 导出失败: {e}\n")
            return False

    def _get_role_label(self, filename):
        """标注核心职责标识。"""
        if "client" in filename:
            return " [⚡ CLIENT: API Connection]"
        if "worker" in filename:
            return " [⚙️ WORKER: Business Orchestration]"
        if "service" in filename:
            return " [🛠️ SERVICE: Data Logic]"
        if "models" in filename:
            return " [📄 MODELS: Schema]"
        if "test_" in filename:
            return " [🚀 TEST: Unit Protection]"
        return ""
