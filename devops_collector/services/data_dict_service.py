"""数据字典服务 (Data Dictionary Service)。

提供 ORM 模型反射能力，生成 Markdown 或 JSON 格式的数据字典文档。
"""

import inspect
from datetime import datetime

from sqlalchemy import inspect as sa_inspect

from devops_collector import models
from devops_collector.models.base_models import Base


class DataDictService:
    def generate_markdown(self) -> tuple[str, int]:
        """生成 Markdown 格式的数据字典内容。"""
        all_models = self._get_all_models()
        categories = self._categorize_models(all_models)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = "# DevOps 效能平台 - 数据字典\n\n"
        md += f"> **生成时间**: {now}\n"
        md += "> **版本**: v2.2 (Service Level)\n\n---\n\n"

        md += "## 数据表清单\n\n"
        for domain, m_list in categories.items():
            if not m_list:
                continue
            md += f"### {domain}\n"
            for m in m_list:
                md += f"- `{m.__tablename__}` - {m.__name__}\n"

        md += "\n---\n\n"

        for domain, m_list in categories.items():
            if not m_list:
                continue
            md += f"## {domain}\n\n"
            for model in m_list:
                mapper = sa_inspect(model)
                md += f"### {model.__name__} (`{model.__tablename__}`)\n\n"
                md += f"**业务描述**: {self._extract_docstring_description(model)}\n\n"

                md += "| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |\n"
                md += "|:-------|:---------|:-----|:-----|:-------|:-----|\n"
                for col in mapper.columns:
                    constraints = ", ".join(self._get_column_constraints(col)) or "-"
                    nullable = "是" if col.nullable else "否"
                    default_val = str(col.default.arg) if col.default and hasattr(col.default, "arg") else "-"
                    if "function" in default_val or "lambda" in default_val:
                        default_val = "(auto)"
                    comment = getattr(col, "comment", None) or "-"
                    md += f"| `{col.name}` | {self._get_column_type_description(col)} | {constraints} | {nullable} | {default_val} | {comment} |\n"

                md += "\n---\n\n"

        return md, len(all_models)

    def _get_all_models(self):
        all_models = []
        for _name, obj in inspect.getmembers(models):
            if inspect.isclass(obj) and hasattr(obj, "__tablename__") and obj != Base:
                all_models.append(obj)
        all_models.sort(key=lambda m: m.__tablename__)
        return all_models

    def _categorize_models(self, all_models):
        categories = {
            "核心主数据域": [],
            "测试管理域": [],
            "GitLab 集成域": [],
            "认证与授权域": [],
            "分析与洞察域": [],
            "其他辅助域": [],
        }
        for model in all_models:
            table_name = model.__tablename__
            if "mdm_" in table_name or table_name in ["organizations", "products", "services"]:
                categories["核心主数据域"].append(model)
            elif "gitlab_" in table_name or table_name in ["sync_logs"]:
                categories["GitLab 集成域"].append(model)
            elif "test_" in table_name or "requirement" in table_name:
                categories["测试管理域"].append(model)
            elif "auth_" in table_name:
                categories["认证与授权域"].append(model)
            elif "view_" in table_name or "okr_" in table_name:
                categories["分析与洞察域"].append(model)
            else:
                categories["其他辅助域"].append(model)
        return categories

    def _get_column_type_description(self, column) -> str:
        col_type = str(column.type)
        type_mapping = {
            "VARCHAR": "String",
            "INTEGER": "Integer",
            "BOOLEAN": "Boolean",
            "DATETIME": "DateTime",
            "UUID": "UUID",
            "JSONB": "JSONB",
            "JSON": "JSON",
            "FLOAT": "Numeric",
            "NUMERIC": "Numeric",
            "TEXT": "Text",
            "BIGINT": "BigInteger",
            "DATE": "Date",
        }
        for key, value in type_mapping.items():
            if key in col_type:
                if key == "VARCHAR":
                    return col_type.replace("VARCHAR", "String")
                return value
        return col_type

    def _get_column_constraints(self, column) -> list[str]:
        constraints = []
        if column.primary_key:
            constraints.append("PK")
        if column.foreign_keys:
            constraints.append("FK")
        if column.unique:
            constraints.append("UNIQUE")
        if column.index:
            constraints.append("INDEX")
        return constraints

    def _extract_docstring_description(self, model_class) -> str:
        doc = inspect.getdoc(model_class)
        if not doc:
            return "无描述"
        lines = doc.split("\n")
        description = []
        for raw_line in lines:
            line = raw_line.strip()
            if line and not line.startswith("Attributes:") and not line.startswith("Args:"):
                description.append(line)
            elif line.startswith("Attributes:"):
                break
        return " ".join(description) if description else "无描述"
