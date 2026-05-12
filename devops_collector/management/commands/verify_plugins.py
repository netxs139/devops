import logging

from devops_collector.core.management import BaseCommand
from devops_collector.plugins import load_all_plugins
from devops_collector.services.registry import PluginRegistry


logger = logging.getLogger("PluginVerifier")


class Command(BaseCommand):
    help = "验证插件架构去中心化是否成功。"

    def handle(self, *args, **options):
        self.stdout.write("Starting Plugin Architecture Verification...\n")

        # 1. 触发自动发现
        self.stdout.write("1. Triggering Plugin Autodiscovery...\n")
        loaded_plugins = load_all_plugins()
        self.stdout.write(f"   Autodiscovered plugins: {loaded_plugins}\n")

        expected_plugins = ["gitlab", "sonarqube", "jenkins", "jira", "zentao", "jfrog", "nexus", "dependency_check"]

        # 2. 验证插件注册状态
        self.stdout.write("\n2. Verifying Plugin Registration Status...\n")
        all_passed = True

        for name in expected_plugins:
            self.stdout.write(f"   Checking plugin: [{name}]\n")

            # 检查加载状态
            if name not in loaded_plugins:
                self.stdout.write(f"   [X] Plugin module '{name}' was not loaded by PluginLoader!\n")
                all_passed = False
                continue

            # 检查组件注册
            client_cls = PluginRegistry.get_client(name)
            worker_cls = PluginRegistry.get_worker(name)
            config_dict = PluginRegistry.get_config(name)

            status = []
            if client_cls:
                status.append("Client [OK]")
            elif name == "dependency_check":
                status.append("Client [SKIPPED]")
            else:
                status.append("Client [MISSING]")

            if worker_cls:
                status.append("Worker [OK]")
            else:
                status.append("Worker [MISSING]")

            if config_dict:
                status.append("Config [OK]")
            else:
                status.append("Config [MISSING]")

            self.stdout.write(f"      Status: {', '.join(status)}\n")

            is_client_ok = bool(client_cls) or (name == "dependency_check")

            if not (is_client_ok and worker_cls and config_dict):
                self.stdout.write(f"      [X] Incomplete registration for {name}\n")
                all_passed = False
            else:
                # 打印配置键值概览
                keys = list(config_dict.keys())
                self.stdout.write(f"      Config Keys: {keys}\n")

        # 3. 结果汇总
        self.stdout.write("\n3. Verification Summary\n")
        if all_passed:
            self.stdout.write("   [SUCCESS] All plugins are correctly decentralized and registered!\n")
            return True
        else:
            self.stdout.write("   [FAILURE] Some plugins failed verification.\n")
            return False
