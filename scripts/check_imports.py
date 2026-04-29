import os
import sys


def check_imports():
    """核心模块导入依赖检查�?""
    print("=" * 60)
    print("DevOps Platform 依赖导入检�?)
    print("=" * 60)

    # 将当前路径加入系统，模拟运行环境
    sys.path.insert(0, os.getcwd())

    modules = [
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "devops_collector.config",
        "devops_collector.models.base_models",
        "devops_collector.auth.auth_service",
        "devops_collector.core.security",
        "devops_portal.main",
    ]

    success_count = 0
    for mod in modules:
        try:
            print(f"检�?{mod: <40} ", end="")
            __import__(mod)
            print("[  OK  ]")
            success_count += 1
        except ImportError as e:
            print(f"[ FAIL ] - {e}")
        except Exception as e:
            print(f"[  ERR ] - {type(e).__name__}: {e}")

    print("-" * 60)
    print(f"检查完�? {success_count}/{len(modules)} 成功")
    print("=" * 60)


if __name__ == "__main__":
    check_imports()
