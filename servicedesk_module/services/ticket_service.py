import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agile_module.services.agile_routing_service import AgileRoutingService
from agile_module.services.gitlab_service import GitLabService
from servicedesk_module.models.sd_models import CustomerIdentity, Ticket
from servicedesk_module.schemas.ticket_schemas import CustomerIdentityCreate, TicketCreateExternal, TicketTriageUpdate


logger = logging.getLogger(__name__)


class TicketService:
    @staticmethod
    async def create_customer_identity(session: AsyncSession, data: CustomerIdentityCreate, tenant_id: str = "default") -> CustomerIdentity:
        """后台创建并分发外部客户身份。"""
        identity = CustomerIdentity(
            tenant_id=tenant_id,
            company_name=data.company_name,
            customer_company_id=data.customer_company_id,
            assigned_department_id=data.assigned_department_id,
            email=data.email,
            phone=data.phone,
            password_hash="fake_hash",  # pragma: allowlist secret
        )
        session.add(identity)
        await session.commit()
        await session.refresh(identity)
        logger.info(f"Created CustomerIdentity: {identity.id} for {identity.email}")
        return identity

    @staticmethod
    async def create_ticket(session: AsyncSession, data: TicketCreateExternal, reporter: CustomerIdentity) -> Ticket:
        """外部客户提交工单 (Bug/Requirement)
        自动从 reporter 中提取其对应的 tenant_id 与 department_id 归属。
        """
        ticket = Ticket(
            tenant_id=reporter.tenant_id,
            reporter_id=reporter.id,
            title=data.title,
            description=data.description,
            # 默认给外部提单的类型为 CONSULTATION，待分诊判定
            ticket_type="CONSULTATION",
            status="NEW",
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        logger.info(f"Customer {reporter.id} created Ticket {ticket.id}")
        return ticket

    @staticmethod
    async def triage_ticket(session: AsyncSession, ticket_id: uuid.UUID, data: TicketTriageUpdate, agent_id: str) -> Ticket | None:
        """内部客服分诊：修改工单类型、绑定产品线。
        如果绑定了产品线，自动路由出目标 GitLab Group 与 Project。
        """
        stmt = select(Ticket).where(Ticket.id == ticket_id)
        result = await session.execute(stmt)
        ticket = result.scalar_one_or_none()

        if not ticket:
            return None

        if data.ticket_type:
            ticket.ticket_type = data.ticket_type

        if data.department_id:
            ticket.department_id = data.department_id

        if data.product_id:
            ticket.product_id = data.product_id
            # 触发 Agile 模块的物理寻址
            group_id = await AgileRoutingService.get_gitlab_group_id(session, data.product_id)
            project_id = await AgileRoutingService.get_reception_project_id(session, data.product_id)

            if group_id:
                ticket.gitlab_group_id = group_id
            if project_id:
                ticket.gitlab_project_id = project_id

        ticket.assignee_id = agent_id
        ticket.status = "ACCEPTED"

        # 如果类型是 BUG 或 REQUIREMENT，且路由到了具体的 GitLab Project，则同步创建 Issue
        if ticket.ticket_type in ("BUG", "REQUIREMENT") and ticket.gitlab_project_id and not ticket.agile_issue_id:
            try:
                # 假设有一个全局或实例化的 GitLabService
                # 这里为了简单直接实例化，实际项目中可能从依赖或单例获取
                gitlab_service = GitLabService()
                issue_data = await gitlab_service.create_issue(
                    project_id=ticket.gitlab_project_id,
                    title=f"[{ticket.ticket_type}] {ticket.title}",
                    description=ticket.description or "No description provided.",
                    labels=[ticket.ticket_type, "ServiceDesk"]
                )
                if issue_data and "iid" in issue_data:
                    ticket.agile_issue_id = str(issue_data["iid"])
                    logger.info(f"Successfully synced Ticket {ticket.id} to GitLab Issue IID {ticket.agile_issue_id}")
            except Exception as e:
                logger.error(f"Failed to sync Ticket {ticket.id} to GitLab: {e}")
                # 根据业务决定是否抛出异常，这里仅记录日志，降级处理允许工单分诊成功但没关联 Issue

        await session.commit()
        await session.refresh(ticket)
        logger.info(f"Agent {agent_id} triaged Ticket {ticket.id} to Product {ticket.product_id}")
        return ticket

    @staticmethod
    async def update_ticket_status_by_agile_issue(
        session: AsyncSession,
        gitlab_project_id: int,
        agile_issue_id: str,
        new_status: str
    ) -> Ticket | None:
        """从 Agile 模块的反向回调更新 SD 工单状态"""
        stmt = select(Ticket).where(
            Ticket.gitlab_project_id == gitlab_project_id,
            Ticket.agile_issue_id == agile_issue_id
        )
        result = await session.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if ticket and ticket.status != new_status:
            logger.info(f"Syncing SD Ticket {ticket.id} status: {ticket.status} -> {new_status}")
            ticket.status = new_status
            await session.commit()
            await session.refresh(ticket)
            
        return ticket
