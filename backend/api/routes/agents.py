from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.agent import AgentTemplate, AgentInstance, AgentWorkflow

router = APIRouter()


class AgentInstanceCreate(BaseModel):
    template_id: int | None = None
    course_id: int
    name: str
    description: str | None = None
    system_prompt: str
    config: dict = {}
    tools: list[str] | None = None
    llm_provider: str = "dashscope"
    llm_model: str = "qwen-max"


class AgentInstanceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    course_id: int
    llm_provider: str
    llm_model: str
    is_active: bool

    model_config = {"from_attributes": True}


class AgentWorkflowCreate(BaseModel):
    agent_id: int
    name: str
    description: str | None = None
    workflow_dag: dict


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentTemplate).order_by(AgentTemplate.created_at.desc()))
    return result.scalars().all()


@router.post("/instances", response_model=AgentInstanceResponse)
async def create_agent(
    data: AgentInstanceCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    agent = AgentInstance(**data.model_dump(), created_by=user.id)
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


@router.get("/instances", response_model=list[AgentInstanceResponse])
async def list_agents(course_id: int | None = None, db: AsyncSession = Depends(get_db)):
    query = select(AgentInstance)
    if course_id:
        query = query.where(AgentInstance.course_id == course_id)
    result = await db.execute(query.order_by(AgentInstance.created_at.desc()))
    return result.scalars().all()


@router.get("/instances/{agent_id}", response_model=AgentInstanceResponse)
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentInstance).where(AgentInstance.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")
    return agent


@router.post("/workflows")
async def create_workflow(data: AgentWorkflowCreate, db: AsyncSession = Depends(get_db)):
    workflow = AgentWorkflow(**data.model_dump())
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    return {"id": workflow.id, "name": workflow.name}
