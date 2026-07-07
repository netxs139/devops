"""PMS 采集插件 Worker"""

import logging
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from uuid6 import uuid7

from devops_collector.models.base_models import ProjectMaster, SystemRegistry
from devops_collector.services.base_worker import BaseWorker


logger = logging.getLogger(__name__)


class PMSProjectSchema(BaseModel):
    """PMS 项目元数据模型验证 Schema。"""

    project_code: str = Field(..., min_length=1)
    project_name: str = Field(..., min_length=1)
    project_type: str | None = None
    status: str = "PLAN"
    plan_start_date: date | None = None
    plan_end_date: date | None = None
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    external_id: str


class PMSWorker(BaseWorker):
    """PMS 数据采集 Worker。"""

    SCHEMA_VERSION = "1.0"

    def __init__(self, session: Session, client: Any = None, correlation_id: str = "unknown-cid", **kwargs) -> None:
        """初始化 PMS Worker。"""
        if client is None:
            raise ValueError("Client must be provided")
        super().__init__(session, client, correlation_id=correlation_id)

    def process_task(self, task: dict) -> dict:
        """PMS 数据同步的核心入口。"""
        # 1. 确保来源系统注册
        sys_reg = self.session.query(SystemRegistry).filter_by(system_code="PMS").first()
        if not sys_reg:
            sys_reg = SystemRegistry(system_code="PMS", system_name="PMS Project Management System")
            self.session.add(sys_reg)
            self.session.flush()

        # 2. 拉取所有项目
        pms_projects = self.client.get_projects()
        self.log_progress("Fetched PMS projects", len(pms_projects), len(pms_projects))

        synced_projects = 0
        synced_milestones = 0

        for p_data in pms_projects:
            try:
                ext_id = p_data.get("id")
                if not ext_id:
                    self.logger.warning(f"Skip PMS project because id is missing: {p_data}")
                    continue

                # 暂存 ODS 层
                self.save_to_staging(source="pms", entity_type="project", external_id=ext_id, payload=p_data)

                # 强校验
                p_validated = PMSProjectSchema(
                    project_code=p_data.get("project_code"),
                    project_name=p_data.get("project_name"),
                    project_type=p_data.get("project_type"),
                    status=p_data.get("status", "PLAN"),
                    plan_start_date=p_data.get("plan_start_date"),
                    plan_end_date=p_data.get("plan_end_date"),
                    actual_start_at=p_data.get("actual_start_at"),
                    actual_end_at=p_data.get("actual_end_at"),
                    external_id=str(ext_id),
                )

                # 入库或更新主数据
                project = self.session.query(ProjectMaster).filter_by(project_code=p_validated.project_code).first()
                if not project:
                    project = ProjectMaster(
                        id=uuid7(),
                        project_code=p_validated.project_code,
                        system_id=sys_reg.id,
                    )
                    self.session.add(project)

                project.project_name = p_validated.project_name
                project.project_type = p_validated.project_type
                project.status = p_validated.status
                project.plan_start_date = p_validated.plan_start_date
                project.plan_end_date = p_validated.plan_end_date
                project.actual_start_at = p_validated.actual_start_at
                project.actual_end_at = p_validated.actual_end_at
                project.external_id = p_validated.external_id

                self.session.flush()
                synced_projects += 1

                # 3. 同步里程碑数据
                milestones = self.client.get_milestones(ext_id)
                for m_data in milestones:
                    m_id = m_data.get("id")
                    if m_id:
                        self.save_to_staging(source="pms", entity_type="milestone", external_id=m_id, payload=m_data)
                        synced_milestones += 1

            except Exception as e:
                self.logger.error(f"Failed to sync PMS project {p_data.get('project_code')}: {e}")
                # 容错处理：单条失败不终止整个同步
                continue

        self.session.commit()
        return {"synced_projects": synced_projects, "synced_milestones": synced_milestones}
