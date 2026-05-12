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

    def check_url_connectivity(self, url: str, label: str = "API", timeout: int = 5) -> tuple[str, str] | None:
        """
        Helper to check if a URL is reachable.
        Returns (level, message) or None if successful.
        """
        import requests

        if not url:
            return ("ERROR", f"[{label}] 未配置 URL，请检查配置文件。")

        try:
            # 仅做 HEAD 请求以节省流量和时间
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code >= 500:
                return ("WARNING", f"[{label}] 目标服务器响应异常 (HTTP {response.status_code})。")
            return None
        except requests.exceptions.RequestException as e:
            return ("ERROR", f"[{label}] 网络无法连接: {url} (原因: {e})")

    def check(self, **options) -> list[tuple[str, str]]:
        """
        Subclasses should override this to provide custom pre-flight checks.
        Returns a list of (level, message) tuples where level is 'ERROR' or 'WARNING'.
        """
        return []

    def _base_checks(self) -> list[tuple[str, str]]:
        """
        Internal global checks for infrastructure (DB connectivity, etc.)
        and runtime architecture compliance.
        """
        import sys
        from pathlib import Path

        from sqlalchemy import text

        from devops_collector.services.audit_service import ArchAuditor

        results = []

        # 1. 基础设施检查 (Database)
        try:
            self.session.execute(text("SELECT 1"))
        except Exception as e:
            results.append(("ERROR", f"Database connectivity check failed: {e}"))

        # 2. 运行时架构审计 (Self-Audit)
        try:
            # 获取当前子类命令的文件路径
            cmd_module = sys.modules[self.__class__.__module__]
            if hasattr(cmd_module, "__file__") and cmd_module.__file__:
                cmd_path = Path(cmd_module.__file__)
                audit_results = ArchAuditor.audit_file(cmd_path)
                results.extend(audit_results)
        except Exception as e:
            # 审计器出错不应阻断业务，仅记录警告
            results.append(("WARNING", f"Self-architecture audit failed to run: {e}"))

        return results

    def run_checks(self, **options) -> bool:
        """
        Run all pre-flight checks. Returns True if execution can proceed.
        """
        skip_checks = options.get("skip_checks", False)
        if skip_checks:
            return True

        from rich.console import Group
        from rich.panel import Panel
        from rich.text import Text

        self.stdout.write("🔍 [dim]执行系统预检 (Pre-flight Checks)...[/dim]\n")

        results = self._base_checks() + self.check(**options)

        if not results:
            return True

        has_error = False
        messages = []
        for level, msg in results:
            if level == "ERROR":
                has_error = True
                messages.append(Text.from_markup(f"[bold red]❌ ERROR:[/bold red] {msg}"))
            else:
                messages.append(Text.from_markup(f"[bold yellow]⚠️ WARNING:[/bold yellow] {msg}"))

        if messages:
            self.console.print(Panel(Group(*messages), title="[bold]系统检查报告[/bold]", border_style="red" if has_error else "yellow"))

        if has_error:
            self.stderr.write("\n🚨 [bold red]预检失败，操作已终止。[/bold red] 请修复上述问题后重试。\n")
            return False

        return True

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

        # 1. 运行预检
        if not self.run_checks(**options):
            return False

        # 2. 执行核心逻辑
        success = False
        try:
            # 动态解析 handle 签名，实现参数智能映射
            import inspect

            sig = inspect.signature(self.handle)

            # 如果 handle 需要 session，则注入到 options 中供后续匹配
            if "session" in sig.parameters:
                options["session"] = session

            # 检查 handle 是否接受 **kwargs
            has_var_kwargs = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())

            if has_var_kwargs:
                # 兼容旧模式：handle(self, *args, **options)
                success = self.handle(*args, **options)
            else:
                # 现代模式：handle(self, force: bool, ...) 仅传递匹配的参数
                # 注意：第一个参数通常是 self，不需要在 options 中查找
                filtered_options = {k: v for k, v in options.items() if k in sig.parameters}
                success = self.handle(*args, **filtered_options)

            return success
        except Exception as e:
            session.rollback()  # 修复：确保异常时回滚事务，防止事务污染
            logger.exception("Unexpected error during command execution")
            self.stderr.write(f"Unexpected error: {e}\n")
            raise e  # 修复：抛出异常由调用方处理，不要在 execute 中直接 sys.exit
        finally:
            # 3. 记录自动化审计日志 (Command Audit Trail)
            try:
                import getpass

                from devops_collector.models.audit import AuditLog

                # 如果命令执行失败，先回滚以获得干净的事务状态
                if not success:
                    try:
                        session.rollback()
                    except Exception:
                        pass

                # 序列化参数，过滤掉下划线开头的私有选项
                safe_options = {k: str(v) for k, v in options.items() if not k.startswith("_")}

                # 确定命令标识 (从模块名提取)
                cmd_id = self.__class__.__module__.split(".")[-1]

                AuditLog.create_log(
                    session,
                    action="MANAGEMENT_COMMAND",
                    resource_type="cli_command",
                    resource_id=cmd_id,
                    status="SUCCESS" if success else "FAILURE",
                    changes=safe_options,
                    remark=f"CLI exec: {self.help or '-'}",
                    actor_name=f"{getpass.getuser()}@{sys.platform}",
                )
                # 审计日志随业务事务同步 commit/flush，session 管理由外层 cli.py 负责
            except Exception as audit_err:
                # 审计日志写入失败（如表不存在）不应影响命令本身的执行结果
                try:
                    session.rollback()
                except Exception:
                    pass
                logger.warning(f"Failed to record command audit log: {audit_err}")


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
