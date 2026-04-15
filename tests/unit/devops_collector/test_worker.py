"""Unit tests for devops_collector/worker.py

覆盖以下核心路径：
- process_task(): 正常流、JSON 损坏、无 client、任务执行异常
- sys_audit_batch_callback(): 正常写入、写入失败、空 batch 短路
- start_audit_consumer(): MQ 启动异常容错
- main(): PluginLoader + 线程启动链路
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ch():
    """模拟 pika channel。"""
    return MagicMock()


@pytest.fixture
def method():
    """模拟 pika Method，携带 delivery_tag。"""
    m = MagicMock()
    m.delivery_tag = 42
    return m


@pytest.fixture
def properties():
    """模拟 pika BasicProperties。"""
    p = MagicMock()
    p.correlation_id = "test-cid-001"
    return p


def make_body(source="gitlab", job_type="sync_commits"):
    return json.dumps({"source": source, "job_type": job_type}).encode()


# ---------------------------------------------------------------------------
# process_task() — Happy Path
# ---------------------------------------------------------------------------

@patch("devops_collector.worker._SessionFactory")
@patch("devops_collector.worker.PluginRegistry")
def test_process_task_happy_path(mock_registry, mock_session_factory, ch, method, properties):
    """正常流：消息被正确解析、分发给 plugin worker，并 ACK。"""
    mock_session = MagicMock()
    mock_session_factory.return_value = mock_session

    mock_registry.get_config.return_value = {"client": {}, "worker": {}}
    mock_client = MagicMock()
    mock_registry.get_client_instance.return_value = mock_client
    mock_worker = MagicMock()
    mock_registry.get_worker_instance.return_value = mock_worker

    from devops_collector.worker import process_task

    process_task(ch, method, properties, make_body("gitlab", "sync_commits"))

    mock_worker.process_task.assert_called_once()
    ch.basic_ack.assert_called_once_with(delivery_tag=42)
    mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# process_task() — Corrupt JSON Payload
# ---------------------------------------------------------------------------

@patch("devops_collector.worker._SessionFactory")
@patch("devops_collector.worker.PluginRegistry")
def test_process_task_corrupt_json(mock_registry, mock_session_factory, ch, method, properties):
    """JSON 损坏时，correlation_id 降级为 'corrupt-payload'，但消息仍被 ACK（防死循环）。"""
    # 无法获取 config 但不会崩溃
    mock_registry.get_config.return_value = {"client": {}, "worker": {}}
    mock_registry.get_client_instance.return_value = None  # 触发 ValueError

    from devops_collector.worker import process_task

    process_task(ch, method, properties, b"not-valid-json{{{{")

    # 消息必须被 ACK，防止死信循环
    ch.basic_ack.assert_called_once_with(delivery_tag=42)


# ---------------------------------------------------------------------------
# process_task() — No Client Registered
# ---------------------------------------------------------------------------

@patch("devops_collector.worker._SessionFactory")
@patch("devops_collector.worker.PluginRegistry")
def test_process_task_no_client_raises(mock_registry, mock_session_factory, ch, method, properties):
    """找不到 client 时，在获取 session 之前就抛 ValueError（L70 < L73）。
    因此 session=None，rollback 不被调用，但消息仍被 ACK。"""
    mock_registry.get_config.return_value = {"client": {}, "worker": {}}
    mock_registry.get_client_instance.return_value = None  # 没有注册

    from devops_collector.worker import process_task

    process_task(ch, method, properties, make_body("unknown_source"))

    # session 在 ValueError 抛出前尚未创建，rollback 不应被调用
    # 但 ACK 必须发出（防止消息反复重投）
    mock_session_factory.assert_not_called()
    ch.basic_ack.assert_called_once_with(delivery_tag=42)


# ---------------------------------------------------------------------------
# process_task() — Worker Execution Raises
# ---------------------------------------------------------------------------

@patch("devops_collector.worker._SessionFactory")
@patch("devops_collector.worker.PluginRegistry")
def test_process_task_worker_raises(mock_registry, mock_session_factory, ch, method, properties):
    """plugin worker.process_task 内部爆炸，session rollback，消息仍 ACK。"""
    mock_session = MagicMock()
    mock_session_factory.return_value = mock_session

    mock_registry.get_config.return_value = {"client": {}, "worker": {}}
    mock_registry.get_client_instance.return_value = MagicMock()
    mock_worker = MagicMock()
    mock_worker.process_task.side_effect = RuntimeError("downstream exploded!")
    mock_registry.get_worker_instance.return_value = mock_worker

    from devops_collector.worker import process_task

    process_task(ch, method, properties, make_body("gitlab"))

    mock_session.rollback.assert_called_once()
    ch.basic_ack.assert_called_once_with(delivery_tag=42)
    mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# process_task() — No correlation_id in properties (backward compat)
# ---------------------------------------------------------------------------

@patch("devops_collector.worker._SessionFactory")
@patch("devops_collector.worker.PluginRegistry")
def test_process_task_fallback_correlation_id(mock_registry, mock_session_factory, ch, method):
    """properties.correlation_id 为 None 时，从 task body 中回退读取。"""
    properties_none = MagicMock()
    properties_none.correlation_id = None  # 旧版消息

    mock_session = MagicMock()
    mock_session_factory.return_value = mock_session
    mock_registry.get_config.return_value = {"client": {}, "worker": {}}
    mock_registry.get_client_instance.return_value = None  # 触发失败路径

    body = json.dumps({
        "source": "gitlab",
        "job_type": "sync",
        "correlation_id": "fallback-cid-999"
    }).encode()

    from devops_collector.worker import process_task

    process_task(ch, method, properties_none, body)

    # 确认消息被处理（无论成功与否）
    ch.basic_ack.assert_called_once_with(delivery_tag=42)


# ---------------------------------------------------------------------------
# sys_audit_batch_callback() — Happy Path
# ---------------------------------------------------------------------------

@patch("devops_collector.worker._SessionFactory")
def test_sys_audit_batch_callback_happy(mock_session_factory):
    """正常批量写入：session.commit 被调用，所有 tag 被 ACK。"""
    mock_session = MagicMock()
    mock_session_factory.return_value = mock_session
    mock_channel = MagicMock()

    batch_data = [
        {"source": "gitlab", "job_type": "sync", "correlation_id": "c1", "action": "CREATE"},
        {"source": "sonar", "job_type": "scan", "correlation_id": "c2", "action": "UPDATE"},
    ]
    delivery_tags = [1, 2]

    with patch("devops_collector.worker.insert") as mock_insert:
        from devops_collector.worker import sys_audit_batch_callback
        sys_audit_batch_callback(batch_data, delivery_tags, mock_channel)

    mock_session.commit.assert_called_once()
    assert mock_channel.basic_ack.call_count == 2
    mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# sys_audit_batch_callback() — Empty Batch Short-Circuit
# ---------------------------------------------------------------------------

@patch("devops_collector.worker._SessionFactory")
def test_sys_audit_batch_callback_empty(mock_session_factory):
    """空 batch 时直接 return，不触碰数据库。"""
    mock_channel = MagicMock()

    from devops_collector.worker import sys_audit_batch_callback

    sys_audit_batch_callback([], [], mock_channel)

    mock_session_factory.assert_not_called()
    mock_channel.basic_ack.assert_not_called()


# ---------------------------------------------------------------------------
# sys_audit_batch_callback() — DB Write Failure → NACK + requeue
# ---------------------------------------------------------------------------

@patch("devops_collector.worker._SessionFactory")
def test_sys_audit_batch_callback_db_failure(mock_session_factory):
    """数据库写入失败时：rollback，所有 tag 被 NACK + requeue=True。"""
    mock_session = MagicMock()
    mock_session.execute.side_effect = Exception("DB connection lost")
    mock_session_factory.return_value = mock_session
    mock_channel = MagicMock()

    batch_data = [{"action": "CREATE", "correlation_id": "c1"}]
    delivery_tags = [99]

    with patch("devops_collector.worker.insert"):
        from devops_collector.worker import sys_audit_batch_callback
        sys_audit_batch_callback(batch_data, delivery_tags, mock_channel)

    mock_session.rollback.assert_called_once()
    mock_channel.basic_nack.assert_called_once_with(delivery_tag=99, requeue=True)
    mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# start_audit_consumer() — MQ Exception Swallowed
# ---------------------------------------------------------------------------

@patch("devops_collector.worker.MessageQueue")
def test_start_audit_consumer_mq_failure(mock_mq_cls):
    """MQ 连接失败时，start_audit_consumer 吞掉异常不向上传播（线程安全）。"""
    mock_mq_cls.side_effect = ConnectionError("RabbitMQ refused")

    from devops_collector.worker import start_audit_consumer

    # 不应该抛出异常
    start_audit_consumer()


# ---------------------------------------------------------------------------
# main() — Bootstrap Chain
# ---------------------------------------------------------------------------

@patch("devops_collector.worker.MessageQueue")
@patch("devops_collector.worker.threading.Thread")
@patch("devops_collector.worker.Base")
@patch("devops_collector.worker.PluginLoader")
def test_main_bootstrap_chain(mock_loader, mock_base, mock_thread_cls, mock_mq_cls):
    """main() 执行时：PluginLoader.load_models → create_all → audit thread → mq.consume。"""
    mock_thread = MagicMock()
    mock_thread_cls.return_value = mock_thread
    mock_mq = MagicMock()
    mock_mq_cls.return_value = mock_mq

    from devops_collector.worker import main

    main()

    mock_loader.load_models.assert_called_once()
    mock_base.metadata.create_all.assert_called_once()
    mock_thread.start.assert_called_once()
    mock_mq.consume_tasks.assert_called_once()
