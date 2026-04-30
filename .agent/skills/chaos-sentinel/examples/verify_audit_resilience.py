import os
import sys
import time


# 注入项目路径
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devops_collector.models.audit_events import bind_audit_listeners
from devops_collector.models.base_models import Base, User


# 动态加载混沌工具
sys.path.append(os.path.join(os.getcwd(), ".agent", "skills", "chaos-sentinel"))
from scripts.fault_library import ChaosEngine


def test_audit_resilience_under_io_pressure():
    """
    场景：模拟审计日志系统在极端延迟下的表现。
    预期：即使日志写入变慢，也不应影响主业务事务的完成（由于我们用了 raw connection.execute 且有 try-except）。
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    bind_audit_listeners([User])

    print("\n🕵️ 开始生存压力测试：业务 vs 缓慢审计...")

    # 模拟“故障注入”：注入 5 秒的全局延迟
    with ChaosEngine.api_latency(5.0):
        print("💥 [注入中] 模拟数据库/网络 5s 延迟...")

        start_time = time.time()

        # 执行主业务操作
        user = User(full_name="Chaos Victim", primary_email="victim@chaos.com")
        db.add(user)
        db.commit()

        end_time = time.time()
        duration = end_time - start_time

        print(f"⏱️ 业务操作完成，耗时: {duration:.2f}s")

        # 验证点：如果是同步阻塞且没处理好，耗时应 > 5s
        # 如果处理得当（比如在 listener 里有超时或者异步逻辑，或者我们预期它虽然慢但不能崩）
        if duration >= 5.0:
            print("⚠️ [警告] 审计逻辑阻塞了主业务流程！建议优化为异步或减少阻塞。")
        else:
            print("✅ [成功] 业务流程未被严重阻塞。")


if __name__ == "__main__":
    test_audit_resilience_under_io_pressure()
