import asyncio
import logging

import httpx
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand, DiagHelper, call_command


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "系统综合诊断主调度脚本。"

    def handle(self, session: Session):
        DiagHelper.print_header("DevOps 平台全项体检")

        # 1. 基础 API 检查 (异步)
        self.stdout.write("\n[1/4] 正在检查 API 服务状态...\n")
        try:
            asyncio.run(self._check_api_health())
        except Exception as e:
            logger.error(f"API 检查过程异常: {e}")

        # 2. 调用数据库专项诊断
        self.stdout.write("\n[2/4] 启动数据库专项检查...\n")
        db_ok = call_command("diag_db", self.session)

        # 3. 调用消息队列专项诊断
        self.stdout.write("\n[3/4] 启动消息队列专项检查...\n")
        mq_ok = call_command("diag_mq", self.session)

        # 4. 调用集成插件专项诊断 (以禅道为例)
        self.stdout.write("\n[4/4] 启动三方集成专项检查 (ZenTao)...\n")
        plugins_ok = call_command("diag_zentao", self.session)

        DiagHelper.print_header("体检报告汇总")

        overall_success = db_ok and mq_ok and plugins_ok
        if overall_success:
            DiagHelper.log_success("所有核心链路均已接通。")
        else:
            DiagHelper.log_warning("部分链路存在异常，请查看上方详细日志。")

        DiagHelper.print_footer()
        return True

    async def _check_api_health(self):
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
