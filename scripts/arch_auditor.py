import os
import re
import sys


# 定义 ANSI 颜色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# =============================================================================
# 架构规则定义区 (AI 自动登记入口)
# =============================================================================
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
]


def audit():
    errors = 0
    warnings = 0
    project_root = "."

    print(f"{YELLOW}>>> Running Optimized Architecture Audit (v2.1-Performance)...{RESET}")

    for root, _, files in os.walk(project_root):
        if any(x in root for x in [".venv", ".git", "__pycache__", "scripts", "archived", ".agent", "chaos-sentinel-workspace", "tests", "migrations"]):
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

            # 预计算文件级 Context，消除 O(N^2) 隐患
            file_ctx = {
                "path": normalized_path,
                "filename": file,
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

                # Context State Management (基于行首缩进的简易状态机)
                if line.startswith("class "):
                    file_ctx["in_scd_class"] = "SCDMixin" in line
                elif line.startswith(("#", "@")):
                    pass
                elif line[:1].strip() and not line.startswith("class "):
                    file_ctx["in_scd_class"] = False

                # Rule Execution
                for rule in RULES:
                    if rule["check"](line, file_ctx):
                        color = RED if rule["severity"] == "ERROR" else YELLOW
                        print(f"{color}[{rule['severity']}] {rule['id']}: {rule['name']}{RESET}")
                        print(f"  File: {normalized_path}:{line_num}")
                        print(f"  Detail: {stripped_line}")
                        print(f"  Fix: {rule['message']}")

                        if rule["severity"] == "ERROR":
                            errors += 1
                        else:
                            warnings += 1

    if errors > 0:
        print(f"\n{RED}Architecture Audit FAILED: {errors} Errors, {warnings} Warnings.{RESET}")
        return False

    print(f"\n{GREEN}Architecture Audit PASSED with {warnings} Warnings.{RESET}")
    return True


if __name__ == "__main__":
    import time

    start = time.time()
    res = audit()
    print(f"Audit finished in {time.time() - start:.2f}s")
    sys.exit(0 if res else 1)
