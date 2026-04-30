import os
import socket
import time
from contextlib import contextmanager


class ChaosEngine:
    """混沌故障注入引擎核心类"""

    @staticmethod
    @contextmanager
    def api_latency(seconds: float = 30.0):
        """模拟全局网络延迟 (Monkeypatch requests)"""
        import requests

        original_send = requests.Session.send

        def delayed_send(*args, **kwargs):
            time.sleep(seconds)
            return original_send(*args, **kwargs)

        requests.Session.send = delayed_send
        print(f"🔥 [Chaos] Injected {seconds}s latency into requests.Session")
        try:
            yield
        finally:
            requests.Session.send = original_send
            print("🛡️ [Chaos] Latency injection removed")

    @staticmethod
    @contextmanager
    def mock_service_unreachable(port: int = 6379):
        """模拟端口不可达 (仅针对本地 mock 或基建)"""
        # 这里使用一个简单的 socket 占用方案
        print(f"🔥 [Chaos] Simulating Port {port} unreachable...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            s.listen(1)
            yield
        except Exception as e:
            print(f"⚠️ [Chaos] Failed to bind port {port}: {e}")
            yield
        finally:
            s.close()
            print(f"🛡️ [Chaos] Port {port} is now free")

    @staticmethod
    @contextmanager
    def disk_full_simulation(path: str):
        """模拟目录不可写 (Permission Denied)"""
        original_mode = os.stat(path).st_mode
        print(f"🔥 [Chaos] Locking path {path} as Read-Only")
        os.chmod(path, 0o444)
        try:
            yield
        finally:
            os.chmod(path, original_mode)
            print(f"🛡️ [Chaos] Restored path {path} permissions")

    @staticmethod
    def kill_process_by_name(name: str):
        """模拟进程意外崩溃"""
        print(f"🔥 [Chaos] Killing process matching: {name}")
        # Windows 兼容方案
        os.system(f"taskkill /f /im {name}.exe")

    @staticmethod
    @contextmanager
    def db_pool_starvation(engine, count: int = 15):
        """模拟数据库连接池耗尽 (LL #102, #71)"""
        print(f"🔥 [Chaos] Starving DB connection pool with {count} ghost connections...")
        connections = []
        try:
            for i in range(count):
                connections.append(engine.connect())
            yield
        finally:
            for conn in connections:
                conn.close()
            print("🛡️ [Chaos] DB connections released")

    @staticmethod
    @contextmanager
    def auth_token_poisoning(client, failure_after: int = 5):
        """模拟中途身份过期 (LL #91, #104)"""
        original_request = client.session.request
        call_count = [0]  # 闭包

        def mock_request(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > failure_after:
                # 注入 401
                from requests.models import Response

                res = Response()
                res.status_code = 401
                res._content = b'{"error": "Unauthorized"}'
                print(f"🔥 [Chaos] Injected 401 Unauthorized at call #{call_count[0]}")
                return res
            return original_request(*args, **kwargs)

        client.session.request = mock_request
        try:
            yield
        finally:
            client.session.request = original_request
            print("🛡️ [Chaos] Auth poisoning removed")


if __name__ == "__main__":
    # 自测逻辑
    with ChaosEngine.api_latency(2):
        print("Test: Waiting for logic...")
