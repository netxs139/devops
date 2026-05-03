"""devops_collector.core.services

业务服务层公共工具，提供 SCD Type2（慢变维）更新的统一实现。

本文件遵循 **Google Python Style Guide**，所有注释采用中文的 Google Docstring 风格。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import inspect
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from devops_collector.models.base_models import Base


log = logging.getLogger(__name__)


class ConcurrencyError(RuntimeError):
    """乐观锁冲突异常。

    当更新时发现记录已被其他事务修改（sync_version 不匹配）或
    未能找到当前有效记录时抛出。业务层可捕获后决定重试或返回错误信息。
    """


def close_current_and_insert_new(session: Session, model_cls: type[Base], natural_key: dict[str, Any], new_data: dict[str, Any]) -> Base:
    """统一的 SCD Type2 更新函数。

    该函数在同一个事务中完成以下步骤：

    1. 根据 ``natural_key``（业务唯一键）查询当前有效记录（``is_current=True``）。
       若未找到则抛出 ``ConcurrencyError``。
    2. 检查 ``sync_version`` 是否与 ``new_data`` 中提供的 ``sync_version`` 相同（乐观锁）。
       不匹配则抛出 ``ConcurrencyError``。
    3. 将当前记录标记为失效：``is_current=False``、``effective_to=now()``。
    4. 基于 ``natural_key`` 与 ``new_data`` 创建一条新记录：
       - ``sync_version`` + 1
       - ``effective_from=now()``
       - ``is_current=True``
       - 其它业务字段使用 ``new_data`` 中的值（若未提供则保留原值）。
    5. 提交事务并返回新创建的对象。

    参数:
        session: 已打开的 SQLAlchemy ``Session``（事务会话）。
        model_cls: 需要更新的模型类，例如 ``Organization``、``User``。
        natural_key: 业务唯一键的字典，例如 ``{"org_id": "ORG_001"}``。
        new_data: 需要写入的新字段字典，**必须包含** ``sync_version`` 键，
                  其值为当前记录的 ``sync_version``（用于乐观锁校验）。

    返回:
        新插入的模型实例（已持久化）。

    Raises:
        ConcurrencyError: 当记录不存在或乐观锁冲突时抛出。
    """
    try:
        current: Any = session.query(model_cls).filter_by(**natural_key, is_current=True).one()
    except NoResultFound as exc:
        raise ConcurrencyError(f"未找到 {model_cls.__name__}（键 {natural_key}）的当前有效记录") from exc
    expected_version = new_data.get("sync_version")
    if expected_version is None:
        raise ConcurrencyError("new_data 必须包含 sync_version 用于乐观锁校验")
    if cast(Any, current).sync_version != expected_version:
        raise ConcurrencyError(f"乐观锁冲突：当前版本 {cast(Any, current).sync_version} 与期望 {expected_version} 不匹配")
    now = datetime.now(UTC)
    current.is_current = False
    current.effective_to = now
    session.add(current)
    insert_kwargs: dict[str, Any] = {**natural_key}
    new_data_clean = {k: v for k, v in new_data.items() if k != "sync_version"}
    insert_kwargs.update(new_data_clean)
    insert_kwargs.update(
        {
            "sync_version": cast(Any, current).sync_version + 1,
            "effective_from": now,
            "effective_to": None,
            "is_current": True,
            "is_deleted": False,
        }
    )
    new_obj = model_cls(**insert_kwargs)
    session.add(new_obj)
    session.flush()
    log.info(
        "SCD Type2 更新 %s: %s -> %s (version %s→%s)",
        model_cls.__name__,
        natural_key,
        insert_kwargs,
        cast(Any, current).sync_version,
        cast(Any, new_obj).sync_version,
    )
    return new_obj


def batch_upsert_scd2(session: Session, model_cls: type[Base], natural_key_names: list[str], batch_data: list[dict[str, Any]]) -> int:
    """批量高效处理 SCD Type2 更新。

    该函数适用于同步大量主数据，通过减少数据库交互次数来提升性能。

    算法流程：
    1. 一次性查询 batch 中所有自然键对应的当前记录。
    2. 过滤出需要更新的记录（版本匹配且内容有变，或新增记录）。
    3. 批量将旧记录标记为 is_current=False。
    4. 批量插入新记录。

    参数:
        session: SQLAlchemy 会话。
        model_cls: 模型类。
        natural_key_names: 构成自然键的字段名列表（如 ['employee_id']）。
        batch_data: 待处理的数据字典列表，每项必须包含 natural_key 字段和 sync_version。

    返回:
        成功处理（更新或新增）的记录总数。
    """
    if not batch_data:
        return 0

    now = datetime.now(UTC)

    # 1. 提取所有自然键用于批量查询
    # 注意：这里假设自然键是单字段，如果是复合键需要更复杂的 Tuple 过滤
    if len(natural_key_names) != 1:
        raise NotImplementedError("batch_upsert_scd2 目前仅支持单字段自然键")

    key_name = natural_key_names[0]
    keys = [d[key_name] for d in batch_data]

    # 2. 批量拉取数据库中的当前版本
    existing_records = session.query(model_cls).filter(getattr(model_cls, key_name).in_(keys), cast(Any, model_cls).is_current).all()

    current_map = {getattr(r, key_name): r for r in existing_records}

    # 动态获取主键名称 (处理 User.global_user_id 与 其他模型 .id 的差异)
    mapper = inspect(model_cls)
    pk_name = mapper.primary_key[0].name

    updates_to_close = []
    new_inserts = []

    for item in batch_data:
        key_val = item[key_name]
        current = current_map.get(key_val)

        if current:
            # 乐观锁校验
            expected_version = item.get("sync_version")
            if expected_version is not None and cast(Any, current).sync_version != expected_version:
                log.warning("跳过记录 %s: 乐观锁冲突 (DB:%s, Batch:%s)", key_val, cast(Any, current).sync_version, expected_version)
                continue

            # 标记旧记录失效
            updates_to_close.append({pk_name: getattr(current, pk_name), "is_current": False, "effective_to": now})

            # 准备新记录数据
            new_record_data = {**item}
            new_record_data.update(
                {"sync_version": cast(Any, current).sync_version + 1, "effective_from": now, "effective_to": None, "is_current": True, "is_deleted": False}
            )
            new_inserts.append(new_record_data)
        else:
            # 全新记录插入
            new_record_data = {**item}
            new_record_data.update({"sync_version": 1, "effective_from": now, "effective_to": None, "is_current": True, "is_deleted": False})
            new_inserts.append(new_record_data)

    # 3. 批量执行
    if updates_to_close:
        session.bulk_update_mappings(cast(Any, model_cls), updates_to_close)

    if new_inserts:
        session.bulk_insert_mappings(cast(Any, model_cls), new_inserts)

    session.flush()
    log.info("SCD2 批量更新完成: %s (关闭 %d, 插入 %d)", model_cls.__name__, len(updates_to_close), len(new_inserts))
    return len(new_inserts)
