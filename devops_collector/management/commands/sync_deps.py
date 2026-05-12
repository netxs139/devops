import logging
import socket
import subprocess
import time
from urllib.parse import urlparse

from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand

logger = logging.getLogger("SyncDeps")


class Command(BaseCommand):
    help = "依赖同步工具：实现 uv sync 的多级重试与镜像切换逻辑 (Nexus -> Tsinghua)。"

    def check(self, **options) -> list[tuple[str, str]]:
        results = []
        nexus_url = (
            self.settings.pypi.nexus_url
            if hasattr(self.settings.pypi, "nexus_url")
            else "http://192.168.5.64:8081/repository/pypi-all/simple"
        )
        tsinghua_url = "https://pypi.tuna.tsinghua.edu.cn/simple"

        # 检查主镜像
        nexus_err = self.check_url_connectivity(nexus_url, label="Nexus PyPI")
        if nexus_err:
            results.append(nexus_err)

        # 检查备选镜像 (仅作为警告)
        tsinghua_err = self.check_url_connectivity(tsinghua_url, label="Tsinghua PyPI")
        if tsinghua_err:
            results.append(("WARNING", f"备选镜像无法访问: {tsinghua_url}"))

        return results

    def handle(
        self,
        session: Session,
        frozen: Annotated[bool, typer.Option("--frozen", help="Use --frozen flag for uv sync")] = False,
        attempts: Annotated[int, typer.Option("--attempts", help="Number of attempts for primary index")] = 3,
        dev: Annotated[bool, typer.Option("--dev", help="Include dev dependencies and extras")] = False,
    ):
        nexus_url = (
            self.settings.pypi.nexus_url
            if hasattr(self.settings.pypi, "nexus_url")
            else "http://192.168.5.64:8081/repository/pypi-all/simple"
        )
        tsinghua_url = "https://pypi.tuna.tsinghua.edu.cn/simple"

        # 构建基础命令
        base_cmd = ["uv", "sync"]
        if frozen:
            base_cmd.append("--frozen")

        if dev:
            base_cmd.extend(["--all-groups", "--all-extras"])
        else:
            base_cmd.append("--all-groups")

        # 1. 尝试主镜像 (Nexus)
        nexus_host = urlparse(nexus_url).hostname
        self.stdout.write(f"🚀 开始同步依赖 (主镜像: {nexus_url})...\n")

        success = False
        for i in range(1, attempts + 1):
            self.stdout.write(f"   [尝试 {i}/{attempts}] 正在连接 Nexus...\n")

            # 预检：检查 Nexus 端口是否通畅
            if not self._check_port(nexus_host, urlparse(nexus_url).port or 80):
                self.stdout.write(f"   ⚠️ Nexus ({nexus_host}) 端口不可达，跳过重试。\n")
                break

            cmd = base_cmd + ["--index-url", nexus_url, "--trusted-host", nexus_host]
            if self._run_sync(cmd):
                success = True
                break

            if i < attempts:
                time.sleep(1)

        # 2. 备选镜像 (清华源)
        if not success:
            self.stdout.write("⚠️ Nexus 镜像同步失败，正在切换至备选镜像 (Tsinghua)...\n")
            cmd = base_cmd + ["--extra-index-url", tsinghua_url]
            if self._run_sync(cmd):
                success = True

        if success:
            self.stdout.write("✅ 依赖同步完成！\n")
        else:
            self.stdout.write("❌ 依赖同步失败。\n")

        return success

    def _check_port(self, host, port, timeout=2):
        try:
            socket.setdefaulttimeout(timeout)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, int(port)))
            return True
        except Exception:
            return False

    def _run_sync(self, cmd):
        self.stdout.write(f"   执行命令: {' '.join(cmd)}\n")
        try:
            # 使用 Popen 实时捕获输出并转发到 self.stdout
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            for line in process.stdout:
                self.stdout.write(f"      {line}")

            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.stdout.write(f"   ❌ 命令执行异常: {e}\n")
            return False
