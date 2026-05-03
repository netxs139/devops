"""GitLab Worker Pipeline Mixin.

提供 Pipeline 和 Deployment 的同步逻辑。
"""

import logging

from devops_collector.core.utils import parse_iso8601

from ..models import GitLabDeployment, GitLabJob, GitLabPipeline, GitLabProject


logger = logging.getLogger(__name__)


class PipelineMixin:
    """提供流水线与部署相关的同步逻辑。

    负责同步 CI/CD 流水线 (Pipeline) 和 部署记录 (Deployment) 的数据。
    """

    def _sync_pipelines(self, project: GitLabProject) -> int:
        """从项目同步流水线记录。

        Args:
            project (GitLabProject): 关联的项目实体。

        Returns:
            int: 处理的流水线总数。
        """
        return self._process_generator(self.client.get_project_pipelines(project.id), lambda batch: self._save_pipelines_batch(project, batch))

    def _save_pipelines_batch(self, project: GitLabProject, batch: list[dict]) -> None:
        """批量保存流水线及其基本指标。

        此方法包含两个步骤：
        1. 将原始数据保存到 Staging 表 (COPY FROM 批量)。
        2. 将数据转换并保存到业务模型表 (Pipeline)。

        Args:
            project (GitLabProject): 关联的项目实体。
            batch (List[dict]): 流水线原始数据列表。
        """
        self.bulk_save_to_staging("gitlab", "pipeline", batch)
        self._transform_pipelines_batch(project, batch)

    def _transform_pipelines_batch(self, project: GitLabProject, batch: list[dict]) -> None:
        """从原始数据转换并加载 Pipeline 实体。

        Args:
            project (GitLabProject): 关联的项目实体。
            batch (List[dict]): 流水线原始数据列表。
        """
        for data in batch:
            p = GitLabPipeline(id=data["id"])
            p.project_id = project.id
            p.status = data["status"]
            p.ref = data.get("ref")
            p.sha = data.get("sha")
            p.source = data.get("source")
            p.created_at = parse_iso8601(data.get("created_at"))
            p.updated_at = parse_iso8601(data.get("updated_at"))
            p.coverage = data.get("coverage")

            # 必须先 merge 确保 Pipeline 存在，以便后续同步 Job 时满足外键约束
            p = self.session.merge(p)

            # FinOps 深度数据补充
            if data["status"] in ["success", "failed", "canceled"]:
                # 如果是列表 API 返回的精简数据，则拉取详情以获取 duration 等核心指标
                if "duration" not in data or data.get("duration") is None:
                    try:
                        full_data = self.client.get_pipeline_details(project.id, p.id)
                        data.update(full_data)
                    except Exception as e:
                        logger.warning(f"Failed to fetch pipeline details for {p.id}: {e}")

                p.duration = data.get("duration")
                p.queued_duration = data.get("queued_duration")
                p.started_at = parse_iso8601(data.get("started_at"))
                p.finished_at = parse_iso8601(data.get("finished_at"))
                p.web_url = data.get("web_url")

                # 关联触发者
                if data.get("user") and "id" in data["user"]:
                    p.user_id = self.user_resolver.resolve(data["user"]["id"])

                # 同步颗粒度 Job 数据
                self._sync_pipeline_jobs(project, p)

    def _sync_deployments(self, project: GitLabProject) -> int:
        """同步部署记录。

        Args:
            project (GitLabProject): 关联的项目实体。

        Returns:
            int: 处理的部署记录总数。
        """
        return self._process_generator(self.client.get_project_deployments(project.id), lambda batch: self._save_deployments_batch(project, batch))

    def _save_deployments_batch(self, project: GitLabProject, batch: list[dict]) -> None:
        """批量保存部署信息。

        包含 Staging (COPY FROM 批量) 和 Transform 两个阶段。

        Args:
            project (GitLabProject): 关联的项目实体。
            batch (List[dict]): 部署记录原始数据列表。
        """
        self.bulk_save_to_staging("gitlab", "deployment", batch)
        self._transform_deployments_batch(project, batch)

    def _transform_deployments_batch(self, project: GitLabProject, batch: list[dict]) -> None:
        """从原始数据转换并加载 Deployment 实体。

        Args:
            project (GitLabProject): 关联的项目实体。
            batch (List[dict]): 部署记录原始数据列表。
        """
        from devops_collector.config import settings

        ids = [item["id"] for item in batch]
        existing = self.session.query(GitLabDeployment).filter(GitLabDeployment.id.in_(ids)).all()
        existing_map = {d.id: d for d in existing}

        # 获取生产环境关键词配置
        prod_envs = settings.analysis.production_env_mapping
        if isinstance(prod_envs, str):
            prod_envs = [i.strip() for i in prod_envs.split(",")]

        for data in batch:
            d = existing_map.get(data["id"])
            if not d:
                d = GitLabDeployment(id=data["id"])
                self.session.add(d)

            d.project_id = project.id
            d.mdm_project_id = project.mdm_project_id
            d.iid = data["iid"]
            d.status = data["status"]
            d.environment = data.get("environment", {}).get("name")
            d.created_at = parse_iso8601(data.get("created_at"))
            d.updated_at = parse_iso8601(data.get("updated_at"))
            d.ref = data.get("ref")
            d.sha = data.get("sha")

            # 识别是否为生产环境部署
            if d.environment:
                d.is_production = any(p.lower() in d.environment.lower() for p in prod_envs)

            # 标记为可见 (Option A), 部署数据通常直接用于分析，这里设为当前转正
            if d.status == "success":
                from datetime import datetime

                d.promoted_at = datetime.now()

    def _sync_pipeline_jobs(self, project: GitLabProject, pipeline: GitLabPipeline) -> int:
        """同步流水线关联的所有 Job 记录。

        Args:
            project (GitLabProject): 关联的项目实体。
            pipeline (GitLabPipeline): 关联的流水线实体。

        Returns:
            int: 处理的 Job 总数。
        """
        return self._process_generator(self.client.get_pipeline_jobs(project.id, pipeline.id), lambda batch: self._save_jobs_batch(pipeline, batch))

    def _save_jobs_batch(self, pipeline: GitLabPipeline, batch: list[dict]) -> None:
        """批量保存 Job 数据。"""
        self.bulk_save_to_staging("gitlab", "job", batch)
        self._transform_jobs_batch(pipeline, batch)

    def _transform_jobs_batch(self, pipeline: GitLabPipeline, batch: list[dict]) -> None:
        """转换并加载 Job 实体。"""
        ids = [item["id"] for item in batch]
        existing = self.session.query(GitLabJob).filter(GitLabJob.id.in_(ids)).all()
        existing_map = {j.id: j for j in existing}

        for data in batch:
            j = existing_map.get(data["id"])
            if not j:
                j = GitLabJob(id=data["id"])
                self.session.add(j)

            j.pipeline_id = pipeline.id
            j.name = data.get("name")
            j.stage = data.get("stage")
            j.status = data.get("status")
            j.created_at = parse_iso8601(data.get("created_at"))
            j.started_at = parse_iso8601(data.get("started_at"))
            j.finished_at = parse_iso8601(data.get("finished_at"))
            j.duration = data.get("duration")
            j.queued_duration = data.get("queued_duration")

            runner = data.get("runner")
            if runner:
                j.runner_id = runner.get("id")
                j.runner_description = runner.get("description")
                # GitLab Job API 响应中 runner 对象通常不直接包含 type，
                # 这里根据 description 或其他启发式方法简单填充，后续可根据需要增强
                j.runner_type = "shared" if runner.get("is_shared") else "specific"
