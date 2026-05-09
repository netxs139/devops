"""初始化脚本共享工具函数。"""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


def build_user_indexes(session: Session):
    """构建用户双索引 (邮箱 + 姓名)，用于灵活匹配 CSV 中的人员字段。

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
    """尝试将 CSV 值解析为 global_user_id。优先邮箱匹配，降级姓名唯一匹配。

    Args:
        value: CSV 单元格值 (邮箱或中文姓名)
        email_idx: 邮箱索引字典
        name_idx: 姓名索引字典
        field_label: 字段标签，用于日志输出

    Returns:
        global_user_id 或 None
    """
    if not value:
        return None
    # 策略1: 邮箱精确匹配
    val_lower = value.lower()
    if val_lower in email_idx:
        return email_idx[val_lower]
    # 策略2: 姓名唯一匹配 (仅当不含 @ 时尝试)
    if "@" not in value and value in name_idx:
        candidates = name_idx[value]
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            logger.warning(f"[{field_label}] 姓名 '{value}' 存在 {len(candidates)} 个重名，跳过")
    return None


class DiagHelper:
    """诊断助手类，用于标准化诊断输出。"""

    @staticmethod
    def print_header(title: str):
        print("=" * 60)
        print(f"{title:^60}")
        print("=" * 60)

    @staticmethod
    def print_footer():
        print("=" * 60)
        print("\n")

    @staticmethod
    def log_success(msg: str):
        print(f"   ✓ {msg}")

    @staticmethod
    def log_failure(msg: str):
        print(f"   ✗ {msg}")

    @staticmethod
    def log_warning(msg: str):
        print(f"   ⚠ {msg}")

    @staticmethod
    def run_check(label: str, check_func: Callable[[], Any]):
        """运行一个检查项并打印结果。"""
        print(f"\n[{label}] 正在检查...")
        start_time = time.time()
        try:
            result = check_func()
            elapsed = time.time() - start_time
            return result, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            DiagHelper.log_failure(f"{label} 失败: {e}")
            return None, elapsed
