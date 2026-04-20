"""RabbitMQ 消息队列封装模块

提供任务发布和消费的统一接口，支持持久化消息。

队列名称: gitlab_tasks
"""

import json
import logging
import uuid

import pika

from .config import Config


logger = logging.getLogger(__name__)


class MessageQueue:
    """RabbitMQ 消息队列客户端。

    提供任务发布和消费方法，自动管理连接状态。

    Attributes:
        url: RabbitMQ 连接 URL
        channel: AMQP 通道

    Example:
        mq = MessageQueue()
        mq.publish_task({'project_id': 123, 'job_type': 'full'})
    """

    def __init__(self):
        """初始化 MQ 客户端，增加心跳以维持长任务连接。"""
        self.url = Config.RABBITMQ_URL
        # 增加 heartbeat 以防止长任务处理期间连接被 RabbitMQ 断开 (默认 60s)
        if "?" in self.url:
            self.url += "&heartbeat=600"
        else:
            self.url += "?heartbeat=600"

        self.params = pika.URLParameters(self.url)
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        try:
            self.connection = pika.BlockingConnection(self.params)
            self.channel = self.connection.channel()
            for q in ["gitlab_tasks", "zentao_tasks", "sonarqube_tasks", "nexus_tasks", "sys_audit_tasks"]:
                self.channel.queue_declare(queue=q, durable=True)
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise e

    def publish_task(self, task: dict) -> None:
        """发布同步任务到队列。

        Args:
            task: 任务字典，包含 project_id 和 job_type
        """
        if not self.channel or self.connection.is_closed:
            self.connect()
        source = task.get("source", "gitlab")
        queue_name = f"{source}_tasks"

        # 注入 Correlation ID
        correlation_id = task.get("correlation_id")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            task["correlation_id"] = correlation_id

        self.channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=json.dumps(task),
            properties=pika.BasicProperties(delivery_mode=2, correlation_id=correlation_id),
        )
        logger.info(f"Published task to {queue_name} [CorrelationID: {correlation_id}]: {task}")

    def consume_tasks(self, callback) -> None:
        """开始消费任务队列 (阻塞式)。

        Args:
            callback: 消息处理回调函数，签名为 (ch, method, properties, body)
        """
        if not self.channel or self.connection.is_closed:
            self.connect()
        self.channel.basic_qos(prefetch_count=1)
        for q in ["gitlab_tasks", "zentao_tasks", "sonarqube_tasks", "nexus_tasks"]:
            self.channel.basic_consume(queue=q, on_message_callback=callback)
        logger.info("Waiting for tasks on all queues...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise e

    def consume_batches(self, queue_name: str, batch_callback, batch_size: int = 100, timeout: float = 1.0) -> None:
        """开始批处理消费任务队列 (阻塞式)。

        Args:
            queue_name: 要消费的队列名称。
            batch_callback: 批处理回调函数，签名为 (batch_data_list, delivery_tags, channel)
            batch_size: 每批最大消息数量
            timeout: 空闲超时时间，超时后若缓存中有数据则立即触发回调
        """
        if not self.channel or self.connection.is_closed:
            self.connect()
        self.channel.basic_qos(prefetch_count=batch_size)

        batch = []
        delivery_tags = []

        logger.info(f"Waiting for tasks in batches on {queue_name}...")
        try:
            for method, _properties, body in self.channel.consume(queue_name, inactivity_timeout=timeout):
                if method is None:
                    # Timeout reached
                    if batch:
                        batch_callback(batch, delivery_tags, self.channel)
                        batch.clear()
                        delivery_tags.clear()
                    continue

                batch.append(json.loads(body))
                delivery_tags.append(method.delivery_tag)

                if len(batch) >= batch_size:
                    batch_callback(batch, delivery_tags, self.channel)
                    batch.clear()
                    delivery_tags.clear()
        except KeyboardInterrupt:
            self.channel.cancel()
        except Exception as e:
            logger.error(f"Batch Consumer error: {e}")
            raise e
