"""数据补偿同步 (Reprocess) 命令。

读取 raw_data_staging 表中的原始 JSON，并调用对应插件的业务转换逻辑。
"""

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import RawDataStaging
from devops_collector.services.registry import PluginRegistry


class MockClient:
    """Mock Client 用于 Worker 实例化，防止触发网络请求。"""

    def __init__(self, *args, **kwargs):
        pass


HANDLER_MAPPING = {
    "gitlab": {
        "merge_request": "_transform_mrs_batch",
        "issue": "_transform_issues_batch",
        "pipeline": "_transform_pipelines_batch",
        "deployment": "_transform_deployments_batch",
    },
    "sonarqube": {"measure": "_transform_measures_snapshot", "issue": "_transform_issue"},
    "zentao": {
        "issue_feature": "_transform_issue",
        "issue_bug": "_transform_issue",
        "build": "_transform_build",
        "release": "_transform_release",
    },
}


class Command(BaseCommand):
    help = "数据补偿同步：从 Staging 原始数据重新生成业务表"

    def add_arguments(self, parser):
        parser.add_argument("source", help="数据源名称 (如: gitlab, sonarqube, zentao)")
        parser.add_argument("--type", help="限制实体类型 (如: merge_request)")
        parser.add_argument("--batch-size", type=int, default=50, help="批处理大小 (默认: 50)")

    def handle(self, *args, **options):
        source_name = options["source"]
        entity_type = options.get("type")
        batch_size = options.get("batch_size", 50)

        # 动态导入所有插件以注册 Worker
        self._ensure_plugins_loaded()

        worker_cls = PluginRegistry.get_worker(source_name)
        if not worker_cls:
            self.stderr.write(f"❌ 找不到数据源 {source_name} 的处理类。\n")
            return False

        worker = worker_cls(self.session, client=MockClient())
        query = self.session.query(RawDataStaging).filter(RawDataStaging.source == source_name)
        if entity_type:
            query = query.filter(RawDataStaging.entity_type == entity_type)

        total_records = query.count()
        self.stdout.write(f"开始重处理 {source_name} 的数据，共 {total_records} 条...\n")

        processed_count = 0
        batch_buffer = {}
        source_handlers = HANDLER_MAPPING.get(source_name, {})

        with self.get_progress() as progress:
            task = progress.add_task(f"[cyan]重处理 {source_name} 数据...", total=total_records)

            for rec in query.yield_per(100):
                method_name = source_handlers.get(rec.entity_type)
                if not method_name:
                    progress.advance(task)
                    continue

                handler = getattr(worker, method_name, None)
                if not handler:
                    progress.advance(task)
                    continue

                context_obj = self._resolve_context(source_name, rec.payload)
                if not context_obj:
                    progress.advance(task)
                    continue

                try:
                    if source_name == "gitlab":
                        key = f"{rec.entity_type}:{context_obj.id}"
                        if key not in batch_buffer:
                            batch_buffer[key] = []
                        batch_buffer[key].append(rec.payload)
                        if len(batch_buffer[key]) >= batch_size:
                            handler(context_obj, batch_buffer[key])
                            batch_buffer[key] = []
                    # Sonarqube / Zentao 逻辑
                    elif source_name == "zentao":
                        if rec.entity_type == "build":
                            handler(context_obj.id, rec.payload.get("execution"), rec.payload)
                        elif rec.entity_type == "release":
                            handler(context_obj.id, rec.payload)
                        elif rec.entity_type.startswith("issue_"):
                            handler(context_obj.id, rec.payload, rec.entity_type.split("_")[1])
                    else:
                        handler(context_obj, rec.payload)
                except Exception as e:
                    self.stderr.write(f"\n❌ 处理记录 {rec.id} 失败: {e}\n")

                processed_count += 1
                if processed_count % 100 == 0:
                    self.session.flush()
                progress.advance(task)

            # 清理最后的批次
            for key, payloads in batch_buffer.items():
                if payloads:
                    etype, pid = key.split(":")
                    ctx = self._resolve_context_by_id(source_name, int(pid))
                    if ctx:
                        getattr(worker, source_handlers.get(etype))(ctx, payloads)

        self.session.flush()
        self.stdout.write(f"✅ 完成！共重处理 {processed_count} 条记录。\n")
        return True

    def _ensure_plugins_loaded(self):
        """确保所有 Worker 已注册。"""
        try:
            import devops_collector.plugins.gitlab.worker
            import devops_collector.plugins.jenkins.worker
            import devops_collector.plugins.nexus.worker
            import devops_collector.plugins.sonarqube.worker
            import devops_collector.plugins.zentao.worker
        except ImportError:
            pass

    def _resolve_context(self, source, payload):
        if source == "gitlab":
            from devops_collector.plugins.gitlab.models import GitLabProject

            pid = payload.get("project_id")
            return self.session.query(GitLabProject).get(pid) if pid else None
        elif source == "sonarqube":
            from devops_collector.plugins.sonarqube.models import SonarProject

            pkey = payload.get("project")
            return self.session.query(SonarProject).filter_by(key=pkey).first() if pkey else None
        elif source == "zentao":
            from devops_collector.plugins.zentao.models import ZenTaoProduct

            pid = payload.get("product")
            return self.session.query(ZenTaoProduct).get(pid) if pid else None
        return None

    def _resolve_context_by_id(self, source, pid):
        if source == "gitlab":
            from devops_collector.plugins.gitlab.models import GitLabProject

            return self.session.query(GitLabProject).get(pid)
        return None
