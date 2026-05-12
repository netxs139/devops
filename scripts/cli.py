"""DevOps 平台统一管理调度工具 (Command Bus v4 - Typer Edition)。

基于 Typer 的现代化 CLI 入口。自动发现 management/commands/ 下的
BaseCommand 子类并按前缀归组注册为子命令。
"""

import argparse
import importlib
import logging
import os
import sys
from pathlib import Path


# 禁用 LiteLLM 远程模型价格拉取，消除 CLI 启动延迟
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


# 添加项目根目录以确保模块能被正确 import
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devops_collector.config import settings  # noqa: E402
from devops_collector.core.management import BaseCommand  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("CLI")
console = Console()

# ============================================================
# 1. 命令自动发现引擎
# ============================================================

COMMANDS_DIR = PROJECT_ROOT / "devops_collector" / "management" / "commands"

# 前缀 → 子应用分组映射
PREFIX_GROUP_MAP: dict[str, str] = {
    "init_": "init",
    "seed_": "init",
    "link_": "init",
    "reset_": "init",
    "diag_": "diag",
    "sys_": "diag",
    "analyze_": "diag",
    "check_": "check",
    "dependency_": "check",
    "lint_": "check",
    "verify_": "verify",
    "arch_": "verify",
    "smoke_": "verify",
    "test_": "verify",
    "sync_": "sync",
    "mini_sync_": "sync",
    "run_": "run",
    "refresh_": "run",
    "reprocess_": "run",
    "import_": "run",
    "cleanup_": "run",
    "fetch_": "run",
    "get_": "run",
    "realign_": "run",
    "export_": "export",
    "executive_": "export",
    "generate_": "export",
}

GROUP_HELP: dict[str, str] = {
    "init": "初始化与主数据灌库",
    "diag": "系统诊断与 AI 归因",
    "check": "数据校验与合规检查",
    "verify": "架构审计与冒烟测试",
    "sync": "外部系统数据同步",
    "run": "运维与数据处理任务",
    "export": "报告导出与数据字典生成",
}


def _classify_command(stem: str) -> str:
    """根据文件名前缀确定其所属分组。"""
    for prefix, group in PREFIX_GROUP_MAP.items():
        if stem.startswith(prefix):
            return group
    return "run"  # 默认兜底


def _make_short_name(stem: str) -> str:
    """将文件名转换为简短的子命令名。

    Examples:
        init_employees   → employees
        diag_db          → db
        sync_zentao      → zentao
        analyze_efficacy → efficacy
        seed_base_data   → base-data
    """
    for prefix in PREFIX_GROUP_MAP:
        if stem.startswith(prefix):
            short = stem[len(prefix) :]
            return short.replace("_", "-")
    return stem.replace("_", "-")


def discover_commands() -> dict[str, dict[str, type[BaseCommand]]]:
    """扫描 commands 目录，返回 {group: {short_name: CommandClass}} 映射。"""
    registry: dict[str, dict[str, type[BaseCommand]]] = {}

    for py_file in sorted(COMMANDS_DIR.glob("*.py")):
        if py_file.stem.startswith("__"):
            continue

        try:
            module_path = f"devops_collector.management.commands.{py_file.stem}"
            module = importlib.import_module(module_path)
            if hasattr(module, "Command") and issubclass(module.Command, BaseCommand):
                group = _classify_command(py_file.stem)
                short_name = _make_short_name(py_file.stem)
                registry.setdefault(group, {})[short_name] = module.Command
        except Exception as e:
            logger.debug(f"跳过 {py_file.stem}: {e}")

    return registry


# ============================================================
# 2. 数据库 Session 工厂
# ============================================================


def _get_session() -> Session:
    """创建数据库 Session。"""
    engine = create_engine(settings.database.uri)
    return Session(engine)


# ============================================================
# 3. Typer 应用构建
# ============================================================

app = typer.Typer(
    name="devops",
    help="DevOps 平台统一管理调度工具 (Command Bus v4)",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _make_command_callback(cmd_class: type[BaseCommand], original_stem: str):
    """为一个 BaseCommand 子类生成 Typer 回调函数。"""

    def callback(
        args: list[str] = typer.Argument(None, help="传递给命令的额外参数"),
    ):
        """桥接函数：将 Typer 调用委托给 BaseCommand.execute()。"""
        cmd = cmd_class()

        # 解析 BaseCommand 自身声明的参数
        parser = argparse.ArgumentParser(prog=original_stem)
        cmd.add_arguments(parser)
        options, _ = parser.parse_known_args(args or [])

        session = _get_session()
        try:
            console.print(f"🚀 [bold cyan]正在执行:[/bold cyan] {original_stem}")
            success = cmd.execute(session, **vars(options))
            if success:
                session.commit()
            else:
                session.rollback()
        except Exception as e:
            session.rollback()
            console.print(f"[red]❌ 执行异常:[/red] {original_stem} ({e})")
            raise typer.Exit(code=1)
        finally:
            session.close()

    # 设置函数的文档字符串为命令的 help 文本
    callback.__doc__ = cmd_class.help or f"执行 {original_stem}"
    callback.__name__ = original_stem
    return callback


def _build_app():
    """动态构建所有子应用和命令。"""
    registry = discover_commands()

    # 为每个分组创建子应用
    sub_apps: dict[str, typer.Typer] = {}
    for group_name, help_text in GROUP_HELP.items():
        sub_app = typer.Typer(help=help_text, no_args_is_help=True, rich_markup_mode="rich")
        sub_apps[group_name] = sub_app
        app.add_typer(sub_app, name=group_name)

    # 将发现的命令注册到对应的子应用
    for group_name, commands in registry.items():
        sub_app = sub_apps.get(group_name)
        if not sub_app:
            sub_app = typer.Typer(help=group_name, no_args_is_help=True)
            sub_apps[group_name] = sub_app
            app.add_typer(sub_app, name=group_name)

        for short_name, cmd_class in commands.items():
            # 还原原始文件名用于 execute
            original_stem = None
            for py_file in COMMANDS_DIR.glob("*.py"):
                if _make_short_name(py_file.stem) == short_name and _classify_command(py_file.stem) == group_name:
                    original_stem = py_file.stem
                    break
            original_stem = original_stem or short_name

            cb = _make_command_callback(cmd_class, original_stem)
            sub_app.command(name=short_name, help=cmd_class.help)(cb)


# ============================================================
# 4. 特殊命令：list
# ============================================================


@app.command("list")
def list_commands():
    """列出所有自动发现的管理命令。"""
    registry = discover_commands()
    table = Table(title="📋 已注册管理命令", show_lines=False)
    table.add_column("分组", style="cyan", no_wrap=True)
    table.add_column("命令", style="green")
    table.add_column("说明", style="dim")

    for group_name in sorted(registry.keys()):
        commands = registry[group_name]
        for short_name, cmd_class in sorted(commands.items()):
            table.add_row(group_name, short_name, cmd_class.help or "-")

    console.print(table)


# ============================================================
# 5. 向下兼容：保留旧的 --module 调用方式
# ============================================================


@app.command("legacy", hidden=True)
def legacy_dispatch(
    group: str = typer.Argument(..., help="命令组名"),
    module: str = typer.Option(..., "--module", help="模块名"),
):
    """向下兼容旧的 cli.py group --module name 调用方式。"""
    registry = discover_commands()
    commands = registry.get(group, {})

    # 尝试匹配短名或原始文件名
    cmd_class = commands.get(module.replace("_", "-"))
    if not cmd_class:
        # 尝试用原始文件名匹配
        for py_file in COMMANDS_DIR.glob("*.py"):
            if py_file.stem == module:
                group_for = _classify_command(py_file.stem)
                short = _make_short_name(py_file.stem)
                cmd_class = registry.get(group_for, {}).get(short)
                break

    if not cmd_class:
        console.print(f"[red]未找到命令:[/red] {group} → {module}")
        raise typer.Exit(code=1)

    cb = _make_command_callback(cmd_class, module)
    cb(args=None)


# 构建应用
_build_app()


def main():
    app()


if __name__ == "__main__":
    main()
