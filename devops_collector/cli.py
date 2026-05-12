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

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


# 禁用 LiteLLM 远程模型价格拉取，消除 CLI 启动延迟
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from devops_collector.config import settings
from devops_collector.core.management import BaseCommand


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
    "import_": "init",
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
    return "run"


def _make_short_name(stem: str) -> str:
    """将文件名转换为简短的子命令名。"""
    for prefix in PREFIX_GROUP_MAP:
        if stem.startswith(prefix):
            short = stem[len(prefix) :]
            return short.replace("_", "-")
    return stem.replace("_", "-")


PLUGINS_DIR = PROJECT_ROOT / "devops_collector" / "plugins"

# ... (前缀和分组映射保持不变)


def _scan_directory(directory: Path, module_prefix: str, registry: dict):
    """扫描指定目录下的 BaseCommand 并存入注册表。"""
    if not directory.exists():
        return

    for py_file in sorted(directory.glob("*.py")):
        print(f"DEBUG: Found file {py_file.stem}")
        if py_file.stem.startswith("__"):
            continue

        try:
            module_path = f"{module_prefix}.{py_file.stem}"
            module = importlib.import_module(module_path)
            if hasattr(module, "Command") and issubclass(module.Command, BaseCommand):
                group = _classify_command(py_file.stem)
                short_name = _make_short_name(py_file.stem)
                module.Command._source_file = str(py_file)
                registry.setdefault(group, {})[short_name] = module.Command
        except Exception as e:
            logger.debug(f"Failed to load command {py_file.stem}: {e}")


def discover_commands() -> dict[str, dict[str, type[BaseCommand]]]:
    """扫描核心目录与所有插件目录，返回 {group: {short_name: CommandClass}} 映射。"""
    registry: dict[str, dict[str, type[BaseCommand]]] = {}

    # 1. 扫描核心命令
    _scan_directory(COMMANDS_DIR, "devops_collector.management.commands", registry)

    # 2. 扫描插件命令
    if PLUGINS_DIR.exists():
        for plugin_dir in PLUGINS_DIR.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith("__"):
                continue

            plugin_cmd_dir = plugin_dir / "management" / "commands"
            if plugin_cmd_dir.exists():
                module_prefix = f"devops_collector.plugins.{plugin_dir.name}.management.commands"
                _scan_directory(plugin_cmd_dir, module_prefix, registry)

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


def _introspect_command_params(cmd_class: type[BaseCommand]) -> tuple[list[dict], bool]:
    """探测命令参数定义。返回 (参数列表, 是否为现代模式)。"""
    import inspect

    handle_method = cmd_class.handle
    sig = inspect.signature(handle_method)

    # 1. 检查是否为“现代”签名：存在除 self, session, args, options 以外的具体命名参数
    modern_params = []
    is_modern = False
    for name, param in sig.parameters.items():
        if name in ("self", "session", "args", "options"):
            continue
        # 只要有一个特定参数，就视为现代模式
        is_modern = True

        # 尝试提取 Annotated 信息
        from typing import Annotated, get_args, get_origin

        annotation = param.annotation
        default = param.default

        param_type = annotation
        typer_info = None

        if get_origin(annotation) is Annotated:
            # 提取 Annotated[type, typer.Option/Argument]
            param_type = get_args(annotation)[0]
            for arg in get_args(annotation)[1:]:
                if isinstance(arg, (typer.models.OptionInfo, typer.models.ArgumentInfo)):
                    typer_info = arg
                    break

        modern_params.append(
            {
                "name": name,
                "type": param_type if param_type is not inspect.Parameter.empty else str,
                "default": default if default is not inspect.Parameter.empty else None,
                "typer_info": typer_info,
                "is_flag": param_type is bool,
            }
        )

    if is_modern:
        return modern_params, True

    # 2. 回退到旧的 argparse 探测模式
    probe_parser = argparse.ArgumentParser(add_help=False)
    try:
        cmd_class().add_arguments(probe_parser)
    except Exception:
        return [], False

    legacy_params = []
    for action in probe_parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue
        opt_strings = action.option_strings
        if not opt_strings:
            continue
        name = max(opt_strings, key=len).lstrip("-").replace("-", "_")
        legacy_params.append(
            {
                "name": name,
                "type": action.type or str,
                "default": action.default,
                "help": action.help or "",
                "is_flag": isinstance(action, argparse._StoreTrueAction),
                "typer_info": None,
            }
        )
    return legacy_params, False


def _run_base_command(cmd_class: type[BaseCommand], original_stem: str, options: dict):
    """统一执行 BaseCommand 的核心逻辑。"""
    cmd = cmd_class()
    session = _get_session()
    try:
        console.print(f"🚀 [bold cyan]正在执行:[/bold cyan] {original_stem}")
        success = cmd.execute(session, **options)
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


def _make_command_callback(cmd_class: type[BaseCommand], original_stem: str):
    """为一个 BaseCommand 子类生成 Typer 回调函数。"""
    import inspect

    params, is_modern = _introspect_command_params(cmd_class)

    def callback(**kwargs):
        _run_base_command(cmd_class, original_stem, kwargs)

    callback.__doc__ = cmd_class.help or f"执行 {original_stem}"
    callback.__name__ = original_stem

    # 注入默认的 skip_checks
    sig_params = [
        inspect.Parameter(
            "skip_checks",
            inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(False, "--skip-checks", help="跳过预飞行检查"),
            annotation=bool,
        )
    ]

    for p in params:
        if is_modern:
            # 现代模式：直接透传原有的默认值（可能是 typer.Option 对象）
            default = p["default"]
            annotation = p["type"]
        else:
            # 旧模式：手动包装
            if p["is_flag"]:
                default = typer.Option(False, help=p["help"])
                annotation = bool
            else:
                default = typer.Option(p["default"], help=p["help"])
                annotation = p["type"]

        sig_params.append(inspect.Parameter(p["name"], inspect.Parameter.KEYWORD_ONLY, default=default, annotation=annotation))

    callback.__signature__ = inspect.Signature(sig_params)
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
            # 获取真实的文件名（去掉 .py 后缀）
            source_path = getattr(cmd_class, "_source_file", "")
            if source_path:
                original_stem = Path(source_path).stem
            else:
                original_stem = short_name.replace("-", "_")

            cb = _make_command_callback(cmd_class, original_stem)
            sub_app.command(name=short_name, help=cmd_class.help)(cb)


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


# 构建应用
_build_app()


def main():
    """CLI 主入口。"""
    app()


if __name__ == "__main__":
    main()
