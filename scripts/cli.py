import argparse
import importlib
import logging
import subprocess
import sys
from pathlib import Path


# 添加项目根目录以确保模块能被正确 import
sys.path.insert(0, str(Path(__file__).parent.parent))

# 引入数据库上下文
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from devops_collector.config import settings


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


def run_script(script_name: str, scripts_dir: Path, global_session: Session) -> bool:
    script_path = scripts_dir / script_name
    if not script_path.exists():
        logger.warning(f"脚本不存在，跳过: {script_name}")
        return True

    # ---------- Phase 2 混合调度探针 ----------
    module_name = script_name.replace(".py", "")
    try:
        # 尝试动态加载模块 (scripts.xxx)
        module = importlib.import_module(f"scripts.{module_name}")
        if hasattr(module, "execute_command"):
            logger.info(f"⚡ [Native 模式] 正在执行: {script_name}")
            try:
                success = module.execute_command(session=global_session)
                # 只有原生模式可以享受到事务整合，由调度器决定 commit 还是保持
                if success is False:
                    global_session.rollback()
                    logger.error(f"❌ 脚本逻辑执行失败: {script_name}")
                    return False
                else:
                    global_session.flush()  # 刷入缓存但不 commit，留给顶层或者内部自己控制
                    return True
            except Exception as e:
                global_session.rollback()
                logger.error(f"❌ 脚本原生调用异常: {script_name} ({e})")
                return False
    except ImportError:
        # 找不到模块或里面有绝对路径依赖导致的导入失败，静默降级
        pass
    except Exception as e:
        # 其他解析期错误，记录但不中断，降级到 subprocess 尝试
        logger.debug(f"加载 {script_name} 时未命中 Phase2 规范: {e}")

    # ---------- 降级: Phase 1 子进程模式 ----------
    logger.info(f"🐌 [Subprocess 模式] 正在执行: {script_name}")
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 子进程脚本失败: {script_name} (退出码: {e.returncode})")
        return False
    except Exception as ex:
        logger.error(f"❌ 脚本调用发生异常: {script_name} ({ex})")
        return False


def execute_group(group_name: str, args, scripts_dir: Path, global_session: Session):
    target_scripts = COMMAND_GROUPS.get(group_name, [])

    if hasattr(args, "module") and args.module:
        target = args.module
        if not target.endswith(".py"):
            matches = [s for s in target_scripts if target in s]
            if not matches:
                target = f"{group_name}_{target}.py" if group_name in ["init", "diag", "check", "verify"] else f"{target}.py"
            else:
                target = matches[0]

        logger.info(f"🎯 单独触发: {target}")
        success = run_script(target, scripts_dir, global_session)
        if success:
            global_session.commit()
        return

    if hasattr(args, "all") and args.all:
        logger.info(f"🚀 开始全量执行 [{group_name}] 任务组...")
        success_count = 0
        executed = set()

        try:
            for script in target_scripts:
                if run_script(script, scripts_dir, global_session):
                    success_count += 1
                executed.add(script)

            prefix = f"{group_name}_"
            all_matched_scripts = [f.name for f in scripts_dir.glob(f"{prefix}*.py")]
            for script in all_matched_scripts:
                if script not in executed:
                    if run_script(script, scripts_dir, global_session):
                        success_count += 1

            global_session.commit()
            logger.info(f"🎉 [{group_name}] 任务组执行完成！成功: {success_count} 项。已全局提交。")
        except Exception as e:
            global_session.rollback()
            logger.error(f"⚠️ [{group_name}] 执行中断，发生严重异常已全局回滚。详情: {e}")
    else:
        logger.warning(f"未指定执行范围。请使用 `uv run scripts/cli.py {group_name} --all` 或 `--module <name>`")


def main():
    parser = argparse.ArgumentParser(description="DevOps 平台统一管理调度工具 (Command Bus)")
    subparsers = parser.add_subparsers(dest="command", help="可用命令组")

    for group, scripts in COMMAND_GROUPS.items():
        sp = subparsers.add_parser(group, help=f"调度 {group} 相关的任务 (共 {len(scripts)} 个)")
        sp.add_argument("--all", action="store_true", help=f"按顺序执行所有的 {group} 脚本")
        sp.add_argument("--module", type=str, help="仅执行指定的模块 (如输入文件名的关键词)")

    args = parser.parse_args()
    scripts_dir = Path(__file__).parent.resolve()

    if args.command in COMMAND_GROUPS:
        # Phase 2 顶层统一拉起数据库引擎
        engine = create_engine(settings.database.uri)
        with Session(engine) as session:
            execute_group(args.command, args, scripts_dir, session)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
