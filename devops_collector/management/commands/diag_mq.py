import logging
import os

import pika

from devops_collector.config import settings
from devops_collector.core.management import BaseCommand, DiagHelper


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "RabbitMQ 专项诊断脚本。"

    def handle(self, *args, **options):
        DiagHelper.print_header("RabbitMQ 专项诊断")

        # 尝试从环境变量获取，如果 settings 没对齐
        host = os.getenv("RABBITMQ_HOST") or os.getenv("RABBITMQ__HOST") or settings.rabbitmq.host
        user = os.getenv("RABBITMQ_USER") or os.getenv("RABBITMQ__USER") or settings.rabbitmq.user
        password = os.getenv("RABBITMQ_PASSWORD") or os.getenv("RABBITMQ__PASSWORD") or settings.rabbitmq.password
        port = 5672

        def check_mq_conn():
            self.stdout.write(f"   诊断参数: {host}:{port} (User: {user})\n")
            credentials = pika.PlainCredentials(user, password)
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=host, port=port, credentials=credentials, connection_attempts=3, retry_delay=1)
                )
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
