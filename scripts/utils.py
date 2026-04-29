"""初始化脚本共享工具函数�?""

import logging
from collections import defaultdict

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


def build_user_indexes(session: Session):
    """构建用户双索�?(邮箱 + 姓名)，用于灵活匹�?CSV 中的人员字段�?

    Returns:
        tuple: (email_idx, name_idx)
            - email_idx: {email_lower: global_user_id}
            - name_idx: {full_name: [global_user_id, ...]}
    """
    from devops_collector.models import User

    all_users = session.query(User).filter_by(is_current=True).all()
    email_idx = {u.primary_email.lower(): u.global_user_id for u in all_users if u.primary_email}
    name_idx = defaultdict(list)
    for u in all_users:
        if u.full_name:
            name_idx[u.full_name].append(u.global_user_id)
    return email_idx, name_idx


def resolve_user(value, email_idx, name_idx, field_label=""):
    """尝试�?CSV 值解析为 global_user_id。优先邮箱匹配，降级姓名唯一匹配�?

    Args:
        value: CSV 单元格�?(邮箱或中文姓�?
        email_idx: 邮箱索引字典
        name_idx: 姓名索引字典
        field_label: 字段标签，用于日志输�?

    Returns:
        global_user_id �?None
    """
    if not value:
        return None
    # 策略1: 邮箱精确匹配
    val_lower = value.lower()
    if val_lower in email_idx:
        return email_idx[val_lower]
    # 策略2: 姓名唯一匹配 (仅当不含 @ 时尝�?
    if "@" not in value and value in name_idx:
        candidates = name_idx[value]
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            logger.warning(f"[{field_label}] 姓名 '{value}' 存在 {len(candidates)} 个重名，跳过")
    return None
