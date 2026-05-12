import logging

from sqlalchemy.orm import configure_mappers

from devops_collector.core.management import BaseCommand
from devops_collector.plugins.zentao.client import ZenTaoClient
from devops_collector.plugins.zentao.models import ZenTaoProduct
from devops_collector.plugins.zentao.worker import ZenTaoWorker
from devops_collector.services.plugin_loader import PluginLoader


logger = logging.getLogger("SyncZenTao")


class Command(BaseCommand):
    help = "手动触发禅道数据同步脚本 (支持 Task 与 Effort)"

    def add_arguments(self, parser):
        parser.add_argument("--product-id", type=int, help="只同步特定产品 ID")

    def check(self, **options) -> list[tuple[str, str]]:
        results = []
        conn_err = self.check_url_connectivity(self.settings.zentao.url, label="ZenTao API")
        if conn_err:
            results.append(conn_err)
        return results

    def handle(self, *args, **options):
        # 强制加载所有插件模型
        PluginLoader.load_models()
        try:
            configure_mappers()
        except Exception:
            pass

        try:
            # 初始化客户端
            client = ZenTaoClient(
                url=self.settings.zentao.url,
                token=self.settings.zentao.token,
                account=self.settings.zentao.account,
                password=self.settings.zentao.password,
            )
            worker = ZenTaoWorker(self.session, client)

            product_id = options.get("product_id")
            if product_id:
                self.stdout.write(f"手动触发产品 ID 同步: {product_id}\n")
                worker.process_task({"product_id": product_id})
                self.stdout.write("✅ 同步成功！\n")
                return True

            # 全量同步模式
            products = self.session.query(ZenTaoProduct).all()

            if not products:
                self.stdout.write("数据库中未发现禅道产品，正在从 API 自动发现...\n")
                try:
                    remote_products = client.get_products()
                    for p_data in remote_products:
                        try:
                            self.stdout.write(f"发现远程产品: {p_data['name']} (ID: {p_data['id']})\n")
                            worker._sync_product(p_data["id"])
                            self.session.flush()
                        except Exception as pe:
                            logger.warning(f"同步产品元数据失败 (ID: {p_data['id']}): {pe}")
                    products = self.session.query(ZenTaoProduct).all()
                except Exception as e:
                    logger.error(f"从 API 获取产品列表失败: {e}")
                    return False

            if not products:
                self.stdout.write("未找到任何禅道产品。\n")
                return True

            with self.get_progress() as progress:
                task = progress.add_task("[cyan]同步禅道产品...", total=len(products))

                for p in products:
                    progress.update(task, description=f"[cyan]同步产品: {p.name} (ID: {p.id})...")
                    task_dict = {"product_id": p.id}
                    worker.process_task(task_dict)
                    self.session.flush()
                    progress.advance(task)

            self.console.print("  [green]✓[/green] 全量产品同步完成！")

            return True

        except Exception as e:
            logger.error(f"同步失败: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False
