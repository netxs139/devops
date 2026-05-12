"""架构审计核心引擎 (Architecture Audit Engine)。

定义项目核心架构红线，并提供文件级审计能力。
"""

import re
from pathlib import Path


# 架构规则定义
ARCH_RULES = [
    {
        "id": "ARCH-001",
        "name": "Deprecated Typing.Type",
        "severity": "WARNING",
        "check": lambda line, ctx: "from typing import" in line and "Type" in line,
        "message": "使用原生的 'type' 代替 'typing.Type' (Python 3.10+)。",
    },
    {
        "id": "ARCH-003",
        "name": "Plugin Side-effect Import",
        "severity": "ERROR",
        "check": lambda line, ctx: ctx["is_plugin_init"] and (line.startswith("from .worker import") or line.startswith("from .client import")),
        "message": "插件 __init__.py 仅应导出元数据。请使用延迟加载以避免循环依赖。",
    },
    {
        "id": "ARCH-006",
        "name": "Weak Contract (Bare Dict Response)",
        "severity": "ERROR",
        "check": lambda line, ctx: ctx["is_router"] and "-> dict" in line,
        "message": "路由必须返回 Pydantic 模型或 ResponseSchema，禁止使用裸 dict。",
    },
    {
        "id": "ARCH-009",
        "name": "Unsafe ORM String Reference",
        "severity": "ERROR",
        "check": lambda line, ctx: "relationship(" in line and ('primaryjoin="' in line or 'foreign_keys="' in line) and "lambda" not in line,
        "message": "使用 lambda 形式定义 primaryjoin/foreign_keys，防止 Mock 污染。",
    },
    {
        "id": "ARCH-011",
        "name": "Silent Exception Swallowing",
        "severity": "ERROR",
        "check": lambda line, ctx: re.search(r"except\s*(\w+)?\s*:\s*pass", line) is not None,
        "message": "严禁静默吞掉异常。请使用 logger 记录上下文。",
    },
]


class ArchAuditor:
    """架构审计执行器。"""

    @staticmethod
    def audit_file(file_path: Path) -> list[tuple[str, str]]:
        """审计单个文件是否符合架构规范。"""
        if not file_path.exists() or not file_path.suffix == ".py":
            return []

        results = []
        normalized_path = str(file_path).replace("\\", "/")

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()
        except Exception:
            return []

        file_ctx = {
            "path": normalized_path,
            "filename": file_path.name,
            "content": content,
            "is_router": "/routers/" in normalized_path,
            "is_plugin_init": "/plugins/" in normalized_path and file_path.name == "__init__.py",
        }

        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#"):
                continue

            for rule in ARCH_RULES:
                if rule["check"](line, file_ctx):
                    results.append((rule["severity"], f"[{rule['id']}] {rule['message']} (Line {i + 1})"))

        return results
