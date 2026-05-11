import logging
import os
import re

from devops_collector.core.management import BaseCommand


logger = logging.getLogger(__name__)

# 定义 ANSI 颜色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

RULES = [
    {
        "id": "ARCH-001",
        "name": "Deprecated Typing.Type",
        "severity": "WARNING",
        "check": lambda line, ctx: "from typing import" in line and "Type" in line,
        "message": "Use native 'type' instead of 'typing.Type' (Python 3.10+).",
    },
    {
        "id": "ARCH-002",
        "name": "SCD2 Unique Constraint Conflict",
        "severity": "ERROR",
        "check": lambda line, ctx: ctx["in_scd_class"] and "unique=True" in line and "postgresql_where" not in line,
        "message": "Physical unique=True conflicts with SCD2 history. Use Partial Index (postgresql_where) instead.",
    },
    {
        "id": "ARCH-003",
        "name": "Plugin Side-effect Import",
        "severity": "ERROR",
        "check": lambda line, ctx: ctx["is_plugin_init"] and (line.startswith("from .worker import") or line.startswith("from .client import")),
        "message": "Plugin __init__.py should only export metadata. Use lazy loading for classes.",
    },
    {
        "id": "ARCH-004",
        "name": "Silent ABC Hook",
        "severity": "WARNING",
        "check": lambda line, ctx: (
            "def " in line and "):" in line and "pass" in line and "# noqa: B027" not in line and re.search(r"def .*\(\w*\):\s*pass", line)
        ),
        "message": "Empty hooks in ABC should use '# noqa: B027' to declare intent.",
    },
    {
        "id": "ARCH-005",
        "name": "Missing Observability",
        "severity": "WARNING",
        "check": lambda line, ctx: ctx["is_service"] and "def " in line and not ctx["file_has_logging"],
        "message": "Service methods should include structured logging (logger.info/error).",
    },
    {
        "id": "ARCH-006",
        "name": "Weak Contract (Bare Dict Response)",
        "severity": "ERROR",
        "check": lambda line, ctx: ctx["is_router"] and "-> dict" in line,
        "message": "Routers must return Pydantic models or ResponseSchema, not bare dicts.",
    },
    {
        "id": "ARCH-007",
        "name": "Missing Traceability Metadata",
        "severity": "ERROR",
        "check": lambda line, ctx: ctx["in_scd_class"] and "Column" in line and not ctx["file_has_traceability"],
        "message": "MDM/SCD2 models must include traceability fields (source_system, correlation_id).",
    },
    {
        "id": "ARCH-008",
        "name": "Fuzzy Error Contract (Bare Exception)",
        "severity": "ERROR",
        "check": lambda line, ctx: (ctx["is_service"] or ctx["is_router"]) and ("raise Exception(" in line or "raise ValueError(" in line),
        "message": "Use domain-specific ErrorSchema or ErrorCode instead of bare Exception.",
    },
    {
        "id": "ARCH-010",
        "name": "Missing Observability Contract",
        "severity": "WARNING",
        "check": lambda line, ctx: ctx["is_service"] and "class " in line and "__metrics__" not in line,
        "message": "Service classes should define '__metrics__' contract for predictable observability.",
    },
    {
        "id": "ARCH-009",
        "name": "Unsafe ORM String Reference",
        "severity": "ERROR",
        "check": lambda line, ctx: "relationship(" in line and ('primaryjoin="' in line or 'foreign_keys="' in line) and "lambda" not in line,
        "message": "Use lambda-based primaryjoin/foreign_keys to prevent Mock pollution during ORM discovery.",
    },
    {
        "id": "ARCH-011",
        "name": "Silent Exception Swallowing",
        "severity": "ERROR",
        "check": lambda line, ctx: re.search(r"except\s*(\w+)?\s*:\s*pass", line) is not None,
        "message": "Do not silently swallow exceptions. Use logger.warning/error to record context.",
    },
    {
        "id": "ARCH-012",
        "name": "Unsafe SQLite Duration Calculation",
        "severity": "WARNING",
        "check": lambda line, ctx: "/workers/" in ctx["path"] and re.search(r"\w+_at\s*-\s*\w+_at", line),
        "message": "Direct datetime subtraction is unsafe in SQLite. Use 'CAST((JULIANDAY(end) - JULIANDAY(start)) * 86400 AS INTEGER)' for cross-dialect compatibility.",
    },
    {
        "id": "ARCH-013",
        "name": "Missing UUID Import",
        "severity": "ERROR",
        "check": lambda line, ctx: ("uuid.uuid4" in line or "UUID(" in line) and "import uuid" not in ctx["content"],
        "message": "File uses UUID/uuid4 but 'import uuid' is missing.",
    },
    {
        "id": "ARCH-014",
        "name": "Missing Audit Mixins",
        "severity": "ERROR",
        "check": lambda line, ctx: (
            line.startswith("class ") and "Base" in line and "Mixin" not in line and ctx["file_has_tablename"] and "class Base(" not in line
        ),
        "message": "ORM models with __tablename__ must inherit from TimestampMixin and either TraceabilityMixin (Plugins) or SCDMixin (MDM).",
    },
    {
        "id": "ARCH-015",
        "name": "Stale Data Dictionary",
        "severity": "ERROR",
        "check": lambda line, ctx: False,
        "message": "DATA_DICTIONARY.md is older than some model files. Run 'just docs' to update.",
    },
]


class Command(BaseCommand):
    help = "架构守卫：运行全量架构规则审计。"

    def handle(self, *args, **options):
        errors = 0
        warnings = 0
        project_root = "."

        self.stdout.write(f"{YELLOW}>>> Running Optimized Architecture Audit (v2.2-Management)...{RESET}\n")

        for root, _, files in os.walk(project_root):
            if any(
                x in root
                for x in [".venv", ".git", "__pycache__", "scripts", "archived", ".agent", "chaos-sentinel-workspace", "tests", "migrations", "alembic"]
            ):
                continue

            for file in files:
                if not file.endswith(".py"):
                    continue

                file_path = os.path.join(root, file)
                normalized_path = file_path.replace("\\", "/")

                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        lines = content.splitlines()
                except Exception:
                    continue

                file_ctx = {
                    "path": normalized_path,
                    "filename": file,
                    "content": content,
                    "file_has_tablename": "__tablename__ =" in content,
                    "file_has_logging": "logger." in content or "get_logger" in content,
                    "file_has_traceability": "source_system" in content or "TraceabilityMixin" in content or "SCDMixin" in content,
                    "is_router": "/routers/" in normalized_path,
                    "is_service": "/services/" in normalized_path or "/workers/" in normalized_path,
                    "is_plugin_init": "/plugins/" in normalized_path and file == "__init__.py",
                    "in_scd_class": False,
                }

                for i, line in enumerate(lines):
                    line_num = i + 1
                    stripped_line = line.strip()
                    if not stripped_line:
                        continue

                    if line.startswith("class "):
                        file_ctx["in_scd_class"] = "SCDMixin" in line
                    elif not line[:1].strip() and not line.startswith(("#", "@", "class ")):
                        pass
                    elif line[:1].strip() and not line.startswith("class "):
                        file_ctx["in_scd_class"] = False

                    for rule in RULES:
                        if rule["check"](line, file_ctx):
                            color = RED if rule["severity"] == "ERROR" else YELLOW
                            self.stdout.write(f"{color}[{rule['severity']}] {rule['id']}: {rule['name']}{RESET}\n")
                            self.stdout.write(f"  File: {normalized_path}:{line_num}\n")
                            self.stdout.write(f"  Detail: {stripped_line}\n")
                            self.stdout.write(f"  Fix: {rule['message']}\n")

                            if rule["severity"] == "ERROR":
                                errors += 1
                            else:
                                warnings += 1

        # --- Global Check: ARCH-015 ---
        dict_path = os.path.join(project_root, "docs", "api", "DATA_DICTIONARY.md")
        if os.path.exists(dict_path):
            dict_mtime = os.path.getmtime(dict_path)
            stale_models = []
            for root, _, files in os.walk(project_root):
                if any(x in root for x in [".venv", ".git", "__pycache__", "scripts", ".agent", "tests"]):
                    continue
                for file in files:
                    if file.endswith(".py") and ("models" in root or "plugins" in root):
                        m_path = os.path.join(root, file)
                        if os.path.getmtime(m_path) > dict_mtime + 2:
                            stale_models.append(m_path.replace("\\", "/"))

            if stale_models:
                self.stdout.write(f"{RED}[ERROR] ARCH-015: Stale Data Dictionary{RESET}\n")
                self.stdout.write(f"  Fix: DATA_DICTIONARY.md is older than {len(stale_models)} model files. Run 'just docs'.\n")
                errors += 1

        if errors > 0:
            self.stdout.write(f"\n{RED}Architecture Audit FAILED: {errors} Errors, {warnings} Warnings.{RESET}\n")
            return False

        self.stdout.write(f"\n{GREEN}Architecture Audit PASSED with {warnings} Warnings.{RESET}\n")
        return True
