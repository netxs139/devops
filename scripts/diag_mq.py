"""RabbitMQ 专项诊断脚本。

支持 CLI Phase 2 (Native Mode) 协议。
"""

import logging
import os
import sys
from pathlib import Path

import pika
from sqlalchemy.orm import Session


# 将项目根目录添加到 python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from devops_collector.config import settings
from scripts.utils import DiagHelper


logger = logging.getLogger(__name__)


def execute_command(session: Session = None, **kwargs) -> bool:
    """[Phase 2 改造] 诊断 RabbitMQ 连接和队列状态。"""
    DiagHelper.print_header("RabbitMQ 专项诊断")

    # 尝试从环境变量获取，如果 settings 没对齐
    host = os.getenv("RABBITMQ_HOST") or os.getenv("RABBITMQ__HOST") or settings.rabbitmq.host
    user = os.getenv("RABBITMQ_USER") or os.getenv("RABBITMQ__USER") or settings.rabbitmq.user
    password = os.getenv("RABBITMQ_PASSWORD") or os.getenv("RABBITMQ__PASSWORD") or settings.rabbitmq.password
    port = 5672

    def check_mq_conn():
        print(f"   诊断参数: {host}:{port} (User: {user})")
        credentials = pika.PlainCredentials(user, password)
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port, credentials=credentials, connection_attempts=3, retry_delay=1))
            connection.channel()
            connection.close()
            DiagHelper.log_success("RabbitMQ 连接及认证成功")
            return True
        except Exception as e:
            DiagHelper.log_failure(f"RabbitMQ 连接失败: {e}")
            return False

    res, _ = DiagHelper.run_check("连通性测试", check_mq_conn)

    DiagHelper.print_footer()
    return res is True


def main():
    execute_command()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
