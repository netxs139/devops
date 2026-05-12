import argparse
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from devops_collector.config import settings


logger = logging.getLogger("management")


class CommandError(Exception):
    """Exception class indicating a problem while executing a management command."""

    pass


class BaseCommand(ABC):
    """
    The base class from which all management commands derive.

    Management commands should extend this class and implement the ``handle()`` method.
    If you want to add arguments to the command, override ``add_arguments()``.
    """

    help = ""

    def __init__(self, stdout=None, stderr=None):
        from rich.console import Console

        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.session: Session = None  # Will be injected by the runner
        self.settings = settings
        self.console = Console()

    def get_progress(self):
        """返回一个配置好的 Rich Progress 上下文管理器，支持进度条和耗时统计。"""
        from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

        return Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=self.console,
        )

    def add_arguments(self, parser: argparse.ArgumentParser):  # noqa: B027
        """
        Entry point for subclassed commands to add custom arguments.
        """
        pass

    @abstractmethod
    def handle(self, *args, **options) -> bool | None:
        """
        The actual logic of the command. Subclasses must implement this method.
        If it returns True, the transaction will be committed by the runner.
        """
        pass

    def execute(self, session: Session, *args, **options):
        """
        Executes the command. This is usually called by the management runner.
        """
        self.session = session
        try:
            return self.handle(*args, **options)
        except CommandError as e:
            self.stderr.write(f"Error: {e}\n")
            sys.exit(1)
        except Exception as e:
            logger.exception("Unexpected error during command execution")
            self.stderr.write(f"Unexpected error: {e}\n")
            sys.exit(1)


class CommandContext:
    """
    Context manager to provide common resources to commands,
    such as database sessions.
    """

    def __init__(self, session: Session):
        self.session = session
        self.settings = settings


class DiagHelper:
    """诊断助手类，用于标准化诊断输出 (已升级为 Rich)。"""

    from rich.console import Console

    _console = Console()

    @classmethod
    def print_header(cls, title: str, width: int = 60):
        from rich.panel import Panel

        cls._console.print(Panel(f"[bold cyan]{title}[/bold cyan]", width=width, expand=False))

    @classmethod
    def print_footer(cls, width: int = 60):
        cls._console.print(f"[dim]{'=' * width}[/dim]\n")

    @classmethod
    def log_success(cls, msg: str):
        cls._console.print(f"   [green]✓[/green] {msg}")

    @classmethod
    def log_failure(cls, msg: str):
        cls._console.print(f"   [red]✗[/red] {msg}")

    @classmethod
    def log_warning(cls, msg: str):
        cls._console.print(f"   [yellow]⚠[/yellow] {msg}")

    @classmethod
    def run_check(cls, label: str, check_func: Any):
        """运行一个检查项并带有等待动画。"""
        import time

        start_time = time.time()
        try:
            with cls._console.status(f"[cyan][{label}][/cyan] 正在检查..."):
                result = check_func()
            elapsed = time.time() - start_time
            return result, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            cls.log_failure(f"{label} 失败: {e}")
            return None, elapsed


def call_command(command_name: str, session: Session, **options):
    """
    Programmatically call a management command.
    """
    import importlib

    try:
        module_path = f"devops_collector.management.commands.{command_name}"
        module = importlib.import_module(module_path)
        if hasattr(module, "Command"):
            cmd = module.Command()
            return cmd.execute(session, **options)
    except Exception as e:
        import logging

        logging.getLogger("management").error(f"Failed to call command {command_name}: {e}")
        return False
    return False


def build_user_indexes(session: Session):
    """构建用户双索引 (邮箱 + 姓名)，用于灵活匹配 CSV 中的人员字段。"""
    from collections import defaultdict

    from devops_collector.models.base_models import User

    all_users = session.query(User).filter_by(is_current=True).all()
    email_idx = {u.primary_email.lower(): u.global_user_id for u in all_users if u.primary_email}
    name_idx = defaultdict(list)
    for u in all_users:
        if u.full_name:
            name_idx[u.full_name].append(u.global_user_id)
    return email_idx, name_idx


def resolve_user(value, email_idx, name_idx, field_label=""):
    """尝试将 CSV 值解析为 global_user_id。优先邮箱匹配，降级姓名唯一匹配。"""
    if not value:
        return None
    # 策略1: 邮箱精确匹配
    val_lower = value.lower()
    if val_lower in email_idx:
        return email_idx[val_lower]
    # 策略2: 姓名唯一匹配 (仅当不含 @ 时尝试)
    if "@" not in value and value in name_idx:
        candidates = name_idx[value]
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            import logging

            logging.getLogger("management").warning(f"[{field_label}] 姓名 '{value}' 存在 {len(candidates)} 个重名，跳过")
    return None
