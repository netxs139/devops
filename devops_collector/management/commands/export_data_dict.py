from pathlib import Path
from typing import Annotated

import typer

from devops_collector.core.management import BaseCommand
from devops_collector.services.data_dict_service import DataDictService


class Command(BaseCommand):
    help = "导出数据字典：基于 ORM 模型生成 Markdown 格式的数据库结构说明"

    def handle(
        self,
        output_path: Annotated[str, typer.Option("--output", "-o", help="输出路径")] = "docs/api/DATA_DICTIONARY.md",
    ):
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        service = DataDictService()

        self.stdout.write("正在扫描模型并生成数据字典 (via Service)...\n")

        try:
            markdown_content, table_count = service.generate_markdown()

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            self.stdout.write(f"✅ 数据字典已成功导出至: {output_file}\n")
            self.stdout.write(f"📊 共扫描并记录了 {table_count} 个数据表。\n")
            return True
        except Exception as e:
            self.stderr.write(f"❌ 生成失败: {e}\n")
            return False
