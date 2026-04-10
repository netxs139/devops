"""DevOps Collector Worker

主要的 Worker 进程，负责：
1. 监听 RabbitMQ 任务队列
2. 解析任务消息
3. 将任务分发给对应的插件 Worker
"""

import json
import logging
import threading
import time

from sqlalchemy import create_engine, insert
from sqlalchemy.orm import sessionmaker

# 触发插件自动发现
from .config import Config
from .core.plugin_loader import PluginLoader
from .core.registry import PluginRegistry
from .models.base_models import Base
from .mq import MessageQueue


logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger("Worker")

# 模块级数据库连接池 (全局唯一，多任务共享)
_engine = create_engine(
    Config.DB_URI,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)
_SessionFactory = sessionmaker(bind=_engine)


def process_task(ch, method, properties, body):
    """处理 MQ 消息的回调函数。"""
    task = {}
    session = None

    # 获取 Correlation ID (优先从 properties 获取，兼容旧版本从 task 获取)
    correlation_id = properties.correlation_id
    try:
        task = json.loads(body)
        if not correlation_id:
            correlation_id = task.get("correlation_id", "unknown-cid")
    except Exception:
        correlation_id = correlation_id or "corrupt-payload"

    adapter = logging.LoggerAdapter(logger, {"correlation_id": correlation_id})

    start_time = time.perf_counter()
    try:
        source = task.get("source", "unknown")
        job_type = task.get("job_type", "unknown")
        adapter.info(f"Received task for {source} [CID: {correlation_id}]")

        # 1. 获取插件配置 (动态)
        plugin_cfg = PluginRegistry.get_config(source)
        if not plugin_cfg:
            adapter.warning(f"No config registered for source: {source}, using defaults.")
            plugin_cfg = {"client": {}, "worker": {}}

        # 2. 获取并实例化客户端
        client_kwargs = plugin_cfg.get("client", {})
        client = PluginRegistry.get_client_instance(source, **client_kwargs)
        if not client:
            raise ValueError(f"No client registered for source: {source}")

        # 3. 从连接池获取数据库会话
        session = _SessionFactory()

        # 4. 获取并实例化 Worker
        worker_kwargs = plugin_cfg.get("worker", {})
        worker = PluginRegistry.get_worker_instance(source, session, client, correlation_id=correlation_id, **worker_kwargs)
        if not worker:
            raise ValueError(f"No worker registered for source: {source}")

        # 5. 执行任务
        worker.process_task(task)
        ch.basic_ack(delivery_tag=method.delivery_tag)

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        adapter.info(
            f"Task for {source} processed successfully.",
            extra={"metric_type": "sync_task", "status": "success", "source": source, "job_type": job_type, "duration_ms": duration_ms},
        )

    except Exception as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        adapter.error(
            f"Error processing task: {e}",
            exc_info=True,
            extra={"metric_type": "sync_task", "status": "failure", "error_type": type(e).__name__, "source": source, "duration_ms": duration_ms},
        )
        if session:
            session.rollback()
        # 即使失败也确认消息，防止死循环 (或者根据需求放入死信队列)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    finally:
        if session:
            session.close()

def sys_audit_batch_callback(batch_data: list, delivery_tags: list, channel):
    """处理 AuditLog 的批量异步写入"""
    if not batch_data:
        return

    from devops_collector.models.audit import AuditLog

    session = _SessionFactory()
    try:
        # 清理由 mq.publish_task 产生的副作用 source 和 job_type (只取表中有的列)
        clean_batch = []
        for item in batch_data:
            d = dict(item)
            d.pop("source", None)
            d.pop("job_type", None)
            d.pop("correlation_id", None) # Worker 自己的框架注入，但是表里也要
            if "correlation_id" not in d and "correlation_id" in item:
                d["correlation_id"] = item["correlation_id"]
            clean_batch.append(d)

        session.execute(insert(AuditLog).values(clean_batch))
        session.commit()

        # 批量 ACK
        for tag in delivery_tags:
            channel.basic_ack(delivery_tag=tag)

        logger.info(f"[sys_audit] Successfully saved batch of {len(clean_batch)} audit logs.")
    except Exception as e:
        session.rollback()
        logger.error(f"[sys_audit] Failed to save audit batch: {e}")
        # 重试补偿放入队列或直接拒绝 (取决于容错重试配置)
        for tag in delivery_tags:
            channel.basic_nack(delivery_tag=tag, requeue=True)
    finally:
        session.close()

def start_audit_consumer():
    """独占线程进行高吞吐批量审计消费。"""
    try:
        mq = MessageQueue()
        # 最多攒 100 条或者挂起 3 秒就存库
        mq.consume_batches("sys_audit_tasks", sys_audit_batch_callback, batch_size=100, timeout=3.0)
    except Exception as e:
        logger.error(f"Audit Consumer thread failed: {e}")


def main():
    """Worker 主循环。"""
    # 显式加载所有插件模型，确保 Base.metadata 包含完整的表结构
    PluginLoader.load_models()

    Base.metadata.create_all(_engine)
    # 启动审计专用消费者线程
    threading.Thread(target=start_audit_consumer, daemon=True, name="AuditConsumerThread").start()

    mq = MessageQueue()
    mq.consume_tasks(process_task)


if __name__ == "__main__":
    main()
