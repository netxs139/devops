import argparse
import importlib
import logging
import subprocess
import sys
from pathlib import Path


# 添加项目根目录以确保模块能被正确 import
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from devops_collector.config import settings
from devops_collector.core.management import BaseCommand


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("CLI")

COMMAND_GROUPS = {
    "init": [
        "seed_base_data.py",
        "init_organizations.py",
        "init_rbac.py",
        "init_locations.py",
        "init_mdm_location.py",
        "init_cost_codes.py",
        "init_labor_rates.py",
        "init_products.py",
        "init_products_projects.py",
        "link_users_to_entities.py",
        "init_gitlab_mappings.py",
        "init_zentao_mappings.py",
        "init_revenue_contracts.py",
        "init_purchase_contracts.py",
        "init_okrs.py",
        "init_catalog.py",
        "init_calendar.py",
        "init_discovery.py",
        "init_jenkins_links.py",
        "init_nexus_links.py",
        "init_sonarqube_links.py",
        "init_zentao_links.py",
        "seed_e2e_admin.py",
        "reset_database.py",
    ],
    "diag": ["diag_db.py", "diag_mq.py", "diag_zentao.py", "sys_diagnose.py"],
    "check": [
        "check_imports.py",
        "check_data_dict_freshness.py",
        "check_issue_labels.py",
        "check_issue_resolution.py",
        "check_identity_alignment.py",
        "dependency_check.py",
        "lint_frontend.py",
    ],
    "verify": [
        "verify_orm_integrity.py",
        "verify_plugins.py",
        "verify_okr_preview.py",
        "arch_auditor.py",
        "smoke_test_report.py",
        "test_dashboard_pages.py",
        "test_wecom_alignment.py",
    ],
    "run": [
        "sync_zentao.py",
        "mini_sync_gitlab.py",
        "run_gitlab_direct.py",
        "run_identity_resolver.py",
        "refresh_master_data.py",
        "reprocess_staging_data.py",
        "import_employees.py",
        "cleanup_stale_data.py",
        "analyze_nexus_lifecycle.py",
        "fetch_api_doc.py",
        "get_zt_token.py",
    ],
    "export": [
        "export_sonarqube_report.py",
        "export_zentao_data.py",
        "executive_audit_report.py",
        "generate_alignment_report.py",
        "generate_data_dictionary.py",
        "generate_project_map.py",
    ],
}


def get_command_class(command_name: str) -> type[BaseCommand] | None:
    """尝试获取类命令。"""
    try:
        module_path = f"devops_collector.management.commands.{command_name}"
        module = importlib.import_module(module_path)
        if hasattr(module, "Command") and issubclass(module.Command, BaseCommand):
            return module.Command
    except (ImportError, AttributeError):
        pass
    return None


def run_command(command_name: str, session: Session, scripts_dir: Path, args_list: list[str] = None) -> bool:
    """
    统一执行入口：类命令优先 -> 模块 execute_command 其次 -> 子进程兜底。
    """
    # 1. 尝试类命令 (New Framework)
    cmd_class = get_command_class(command_name)
    if cmd_class:
        logger.info(f"🚀 [Command Framework] 正在执行: {command_name}")
        cmd = cmd_class()
        # 处理参数
        parser = argparse.ArgumentParser(prog=f"cli.py ... --module {command_name}")
        cmd.add_arguments(parser)
        options, _ = parser.parse_known_args(args_list or [])
        try:
            success = cmd.execute(session, **vars(options))
            if success:
                session.flush()
                return True
            else:
                session.rollback()
                return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ 类命令执行异常: {command_name} ({e})")
            return False

    # 2. 尝试旧的原生模式 (Phase 2 Legacy)
    script_file = f"{command_name}.py" if not command_name.endswith(".py") else command_name
    script_path = scripts_dir / script_file
    module_name = command_name.replace(".py", "")

    try:
        module = importlib.import_module(f"scripts.{module_name}")
        if hasattr(module, "execute_command"):
            logger.info(f"⚡ [Native Legacy] 正在执行: {script_file}")
            success = module.execute_command(session=session)
            if success:
                session.flush()
                return True
            else:
                session.rollback()
                return False
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"加载脚本 {script_file} 时出错: {e}")

    # 3. 子进程模式 (Phase 1 Fallback)
    if script_path.exists():
        logger.info(f"🐌 [Subprocess Fallback] 正在执行: {script_file}")
        try:
            result = subprocess.run([sys.executable, str(script_path)], check=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ 子进程执行失败: {script_file} ({e})")
            return False

    logger.warning(f"⚠️ 未找到任何匹配的命令或脚本: {command_name}")
    return False


def execute_group(group_name: str, args, scripts_dir: Path, session: Session, unknown_args: list[str]):
    target_scripts = COMMAND_GROUPS.get(group_name, [])

    if hasattr(args, "module") and args.module:
        target = args.module
        # 去掉 .py 后缀统一逻辑
        cmd_name = target.replace(".py", "")

        # 如果在硬编码列表里，尝试补全
        if cmd_name not in target_scripts and target not in target_scripts:
            matches = [s for s in target_scripts if cmd_name in s]
            if matches:
                cmd_name = matches[0].replace(".py", "")

        success = run_command(cmd_name, session, scripts_dir, unknown_args)
        if success:
            session.commit()
        return

    if hasattr(args, "all") and args.all:
        logger.info(f"🚀 开始全量执行 [{group_name}] 任务组...")
        success_count = 0
        for script in target_scripts:
            cmd_name = script.replace(".py", "")
            if run_command(cmd_name, session, scripts_dir):
                success_count += 1
        session.commit()
        logger.info(f"🎉 [{group_name}] 执行完成，成功 {success_count} 项。")
    else:
        logger.warning("请指定 --all 或 --module <name>")


def main():
    parser = argparse.ArgumentParser(description="DevOps 平台统一管理调度工具 (Command Bus v3)")
    subparsers = parser.add_subparsers(dest="command", help="可用命令组")

    for group in COMMAND_GROUPS:
        sp = subparsers.add_parser(group, help=f"调度 {group} 相关的任务")
        sp.add_argument("--all", action="store_true", help="全量执行")
        sp.add_argument("--module", type=str, help="执行指定模块")

    # 特殊的管理命令：列出所有发现的类命令
    subparsers.add_parser("list", help="列出所有可用的类命令")

    args, unknown = parser.parse_known_args()
    scripts_dir = Path(__file__).parent.resolve()

    if args.command == "list":
        cmd_dir = PROJECT_ROOT / "devops_collector/management/commands"
        print("\n发现的类命令 (Management Commands):")
        for f in cmd_dir.glob("*.py"):
            if f.stem != "__init__":
                cmd_class = get_command_class(f.stem)
                help_text = cmd_class.help if cmd_class else "No help available."
                print(f"  - {f.stem:<20} : {help_text}")
        print()
        return

    if args.command in COMMAND_GROUPS:
        engine = create_engine(settings.database.uri)
        with Session(engine) as session:
            execute_group(args.command, args, scripts_dir, session, unknown)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
