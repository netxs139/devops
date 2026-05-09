"""系统综合诊断主调度脚本。

作为“仪表盘”，协调并调用各专项诊断脚本。
支持 CLI Phase 2 (Native Mode) 协议。
"""

import asyncio
import logging
import sys
from pathlib import Path

import httpx
from sqlalchemy.orm import Session


# 将项目根目录添加到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入各专项诊断模块
from scripts import diag_db, diag_mq, diag_zentao
from scripts.utils import DiagHelper


logger = logging.getLogger(__name__)


async def check_api_health():
    """检查 API 服务是否在线。"""
    base_url = "http://localhost:8000"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{base_url}/health", timeout=3)
            if resp.status_code == 200:
                DiagHelper.log_success(f"后端 API 服务运行正常: {resp.json()}")
                return True
            DiagHelper.log_failure(f"后端 API 返回异常状态: {resp.status_code}")
            return False
        except Exception as e:
            DiagHelper.log_warning(f"无法连接到后端 API (可能未启动): {e}")
            return False


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 系统综合诊断主入口。"""
    DiagHelper.print_header("DevOps 平台全项体检")

    # 1. 基础 API 检查 (异步)
    print("\n[1/4] 正在检查 API 服务状态...")
    try:
        asyncio.run(check_api_health())
    except Exception as e:
        logger.error(f"API 检查过程异常: {e}")

    # 2. 调用数据库专项诊断
    print("\n[2/4] 启动数据库专项检查...")
    db_ok = diag_db.execute_command(session)

    # 3. 调用消息队列专项诊断
    print("\n[3/4] 启动消息队列专项检查...")
    mq_ok = diag_mq.execute_command()

    # 4. 调用集成插件专项诊断 (以禅道为例)
    print("\n[4/4] 启动三方集成专项检查 (ZenTao)...")
    plugins_ok = diag_zentao.execute_command(session)

    DiagHelper.print_header("体检报告汇总")

    overall_success = db_ok and mq_ok and plugins_ok
    if overall_success:
        DiagHelper.log_success("所有核心链路均已接通。")
    else:
        DiagHelper.log_warning("部分链路存在异常，请查看上方详细日志。")

    DiagHelper.print_footer()
    return True


def main():
    from sqlalchemy import create_engine

    from devops_collector.config import settings

    engine = create_engine(settings.database.uri)
    with Session(engine) as session:
        execute_command(session)


if __name__ == "__main__":
    # 强制将日志级别设置为 INFO 以确保输出可见
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
