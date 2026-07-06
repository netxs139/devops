import uuid

from fastapi import APIRouter, Depends, HTTPException
from identity_module.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from servicedesk_module.schemas.ticket_schemas import CustomerIdentityCreate, CustomerIdentityResponse, TicketResponse, TicketTriageUpdate
from servicedesk_module.services.ticket_service import TicketService


router = APIRouter(prefix="/agent", tags=["ServiceDesk - Internal Agent"])


# Mock dependencies
async def get_current_agent_id() -> str:
    """Mock authentication dependency for internal staff."""
    return "agent_internal_123"


@router.post("/customers", response_model=CustomerIdentityResponse, status_code=201)
async def create_customer(data: CustomerIdentityCreate, session: AsyncSession = Depends(get_db)) -> CustomerIdentityResponse:
    """内部分诊/管理人员创建客户账号"""
    identity = await TicketService.create_customer_identity(session, data)
    return identity  # type: ignore


@router.patch("/tickets/{ticket_id}/triage", response_model=TicketResponse)
async def triage_ticket(
    ticket_id: uuid.UUID, data: TicketTriageUpdate, session: AsyncSession = Depends(get_db), agent_id: str = Depends(get_current_agent_id)
) -> TicketResponse:
    """内部客服分诊：修改工单类型、绑定产品线并触发 Agile 路由。"""
    ticket = await TicketService.triage_ticket(session, ticket_id, data, agent_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket  # type: ignore
