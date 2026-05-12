"""Nexus 资产生命周期分析命令。

抽样分析 Nexus 仓库中的组件下载活跃度、存储占用及从公网拉取的频率。
"""

from datetime import UTC, datetime, timedelta

from devops_collector.core.management import BaseCommand
from devops_collector.plugins.nexus.client import NexusClient
from devops_collector.plugins.nexus.config import get_config


class Command(BaseCommand):
    help = "分析 Nexus 资产生命周期：统计各仓库的组件活跃度与存储分布"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="每个仓库的抽样组件上限 (默认: 100)")

    def handle(self, *args, **options):
        limit = options.get("limit", 100)

        config = get_config()["client"]
        client = NexusClient(url=config["url"], user=config["user"], password=config["password"], rate_limit=50)

        now = datetime.now(UTC)
        periods = {
            "7_days": timedelta(days=7),
            "30_days": timedelta(days=30),
            "90_days": timedelta(days=90),
            "180_days": timedelta(days=180),
        }

        try:
            self.stdout.write(f"正在获取 Nexus 仓库列表 (抽样上限: {limit})...\n")
            repos = client.list_repositories()

            report = {}
            for repo in repos:
                repo_name = repo["name"]
                if repo["type"] == "group":
                    continue

                self.stdout.write(f"  分析 [{repo['type']}] {repo_name} ({repo['format']})...\n")

                stats = {
                    "format": repo["format"],
                    "type": repo["type"],
                    "count": 0,
                    "size_mb": 0.0,
                    "never_dl": 0,
                    "dl_7d": 0,
                    "dl_30d": 0,
                    "dl_90d": 0,
                    "dl_old": 0,
                }

                for comp in client.list_components(repo_name):
                    stats["count"] += 1
                    comp_size = 0
                    last_dl = None

                    for asset in comp.get("assets", []):
                        comp_size += asset.get("fileSize", 0)
                        dl_str = asset.get("lastDownloaded")
                        if dl_str:
                            try:
                                dt = datetime.fromisoformat(dl_str.replace("Z", "+00:00"))
                                if last_dl is None or dt > last_dl:
                                    last_dl = dt
                            except:
                                pass

                    stats["size_mb"] += comp_size / (1024 * 1024)

                    if not last_dl:
                        stats["never_dl"] += 1
                    else:
                        age = now - last_dl
                        if age <= periods["7_days"]:
                            stats["dl_7d"] += 1
                        elif age <= periods["30_days"]:
                            stats["dl_30d"] += 1
                        elif age <= periods["90_days"]:
                            stats["dl_90d"] += 1
                        else:
                            stats["dl_old"] += 1

                    if stats["count"] >= limit:
                        break

                report[repo_name] = stats

            # 输出报表
            self.stdout.write("\n" + "=" * 60 + "\n")
            self.stdout.write("      NEXUS ASSET LIFECYCLE REPORT (SAMPLING)\n")
            self.stdout.write("=" * 60 + "\n")

            for name, s in report.items():
                self.stdout.write(f"\n[{s['type'].upper()} / {s['format'].upper()}] {name}\n")
                self.stdout.write(f"  • 总大小: {s['size_mb']:.2f} MB | 抽样数: {s['count']}\n")
                self.stdout.write("  • 下载活跃度:\n")
                self.stdout.write(f"    - 最近 7 天  : {s['dl_7d']}\n")
                self.stdout.write(f"    - 最近 30 天 : {s['dl_30d']}\n")
                self.stdout.write(f"    - 最近 90 天 : {s['dl_90d']}\n")
                self.stdout.write(f"    - 沉寂(>90d) : {s['dl_old']}\n")
                self.stdout.write(f"    - 从未下载   : {s['never_dl']}\n")

            return True

        except Exception as e:
            self.stderr.write(f"❌ 分析失败: {e}\n")
            return False
