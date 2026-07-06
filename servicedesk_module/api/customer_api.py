import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from identity_module.deps import get_db
from servicedesk_module.models.sd_models import CustomerIdentity
from servicedesk_module.schemas.ticket_schemas import TicketCreateExternal, TicketResponse
from servicedesk_module.services.ticket_service import TicketService


router = APIRouter(prefix="/customer", tags=["ServiceDesk - Customer"])


# 伪造一个鉴权依赖获取当前外部客户身份
# 实际业务中应从 JWT 或 Session 中解析出客户 ID，并查询数据库
async def get_current_customer(session: AsyncSession = Depends(get_db)) -> CustomerIdentity:
    """Mock authentication dependency for external customers."""
    # 这里为了演示，假设直接查出一个存在的身份 (或者需要在测试中注入)
    # 在生产中应为: user_id = extract_jwt(request)
    # return await session.get(CustomerIdentity, user_id)
    raise NotImplementedError("Authentication logic is pending")


@router.post("/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket(
    data: TicketCreateExternal,
    session: AsyncSession = Depends(get_db),
    # customer: CustomerIdentity = Depends(get_current_customer)
) -> TicketResponse:
    """外部客户提报工单 (Bug/Requirement)"""
    # 模拟一个客户身份（仅用于编译预检通过，实际应由Depends注入）
    mock_reporter = CustomerIdentity(
        id=uuid.uuid4(),  # type: ignore
        tenant_id="default",
        email="mock@example.com",
    )

    ticket = await TicketService.create_ticket(session, data, mock_reporter)
    return ticket  # type: ignore
