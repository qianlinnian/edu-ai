from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from models.agent import AgentInstance, AgentTemplate, AgentWorkflow
from models.course import Course, Enrollment
from models.user import User, UserRole

router = APIRouter()


class AgentInstanceCreate(BaseModel):
    template_id: int | None = Field(default=None, ge=1)
    course_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    system_prompt: str = Field(min_length=1)
    config: dict = Field(default_factory=dict)
    tools: list[str] = Field(default_factory=list)
    llm_provider: str = Field(default="dashscope", min_length=1, max_length=50)
    llm_model: str = Field(default="qwen-max", min_length=1, max_length=100)


class AgentInstanceUpdate(BaseModel):
    template_id: int | None = Field(default=None, ge=1)
    course_id: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    system_prompt: str | None = Field(default=None, min_length=1)
    config: dict | None = None
    tools: list[str] | None = None
    llm_provider: str | None = Field(default=None, min_length=1, max_length=50)
    llm_model: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class AgentInstanceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    course_id: int
    llm_provider: str
    llm_model: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AgentWorkflowCreate(BaseModel):
    agent_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    workflow_dag: dict = Field(default_factory=dict)


class AgentWorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    workflow_dag: dict | None = None
    is_active: bool | None = None


class AgentWorkflowResponse(BaseModel):
    id: int
    agent_id: int
    name: str
    description: str | None
    workflow_dag: dict
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


async def _get_course_or_404(db: AsyncSession, course_id: int) -> Course:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


async def _get_template_or_404(db: AsyncSession, template_id: int) -> AgentTemplate:
    result = await db.execute(select(AgentTemplate).where(AgentTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Agent template not found")
    return template


async def _get_agent_or_404(db: AsyncSession, agent_id: int) -> AgentInstance:
    result = await db.execute(select(AgentInstance).where(AgentInstance.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


async def _get_workflow_or_404(db: AsyncSession, workflow_id: int) -> AgentWorkflow:
    result = await db.execute(select(AgentWorkflow).where(AgentWorkflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Agent workflow not found")
    return workflow


async def _ensure_course_access(db: AsyncSession, *, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    if user.role == UserRole.STUDENT:
        result = await db.execute(
            select(Enrollment.id).where(Enrollment.course_id == course.id, Enrollment.student_id == user.id)
        )
        if result.scalar_one_or_none() is not None:
            return
    raise HTTPException(status_code=403, detail="Not allowed to access this course")


def _ensure_course_manager(*, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Teacher or admin access required")


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Teacher or admin access required")
    result = await db.execute(select(AgentTemplate).order_by(AgentTemplate.created_at.desc()))
    return result.scalars().all()


@router.post("/instances", response_model=AgentInstanceResponse)
async def create_agent(
    data: AgentInstanceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, data.course_id)
    _ensure_course_manager(course=course, user=user)

    if data.template_id is not None:
        await _get_template_or_404(db, data.template_id)

    agent = AgentInstance(**data.model_dump(), created_by=user.id)
    db.add(agent)
    await db.flush()
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/instances", response_model=list[AgentInstanceResponse])
async def list_agents(
    course_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(AgentInstance)
    if course_id is not None:
        course = await _get_course_or_404(db, course_id)
        await _ensure_course_access(db, course=course, user=user)
        query = query.where(AgentInstance.course_id == course_id)
    elif user.role == UserRole.TEACHER:
        query = query.join(Course, AgentInstance.course_id == Course.id).where(Course.teacher_id == user.id)
    elif user.role == UserRole.STUDENT:
        query = query.join(Enrollment, Enrollment.course_id == AgentInstance.course_id).where(
            Enrollment.student_id == user.id
        )

    result = await db.execute(query.order_by(AgentInstance.created_at.desc()))
    return result.scalars().all()


@router.get("/instances/{agent_id}", response_model=AgentInstanceResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = await _get_agent_or_404(db, agent_id)
    course = await _get_course_or_404(db, agent.course_id)
    await _ensure_course_access(db, course=course, user=user)
    return agent


@router.put("/instances/{agent_id}", response_model=AgentInstanceResponse)
async def update_agent(
    agent_id: int,
    data: AgentInstanceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = await _get_agent_or_404(db, agent_id)
    current_course = await _get_course_or_404(db, agent.course_id)
    _ensure_course_manager(course=current_course, user=user)

    payload = data.model_dump(exclude_unset=True)
    new_course_id = payload.get("course_id")
    if new_course_id is not None and new_course_id != agent.course_id:
        new_course = await _get_course_or_404(db, new_course_id)
        _ensure_course_manager(course=new_course, user=user)

    template_id = payload.get("template_id")
    if template_id is not None:
        await _get_template_or_404(db, template_id)

    for field, value in payload.items():
        setattr(agent, field, value)

    await db.flush()
    await db.commit()
    await db.refresh(agent)
    return agent


@router.post("/instances/{agent_id}/publish", response_model=AgentInstanceResponse)
async def publish_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = await _get_agent_or_404(db, agent_id)
    course = await _get_course_or_404(db, agent.course_id)
    _ensure_course_manager(course=course, user=user)

    workflow_result = await db.execute(select(AgentWorkflow.id).where(AgentWorkflow.agent_id == agent.id).limit(1))
    if workflow_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=409, detail="Agent workflow is required before publishing")

    agent.is_active = True
    await db.flush()
    await db.commit()
    await db.refresh(agent)
    return agent


@router.post("/workflows", response_model=AgentWorkflowResponse)
async def create_workflow(
    data: AgentWorkflowCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = await _get_agent_or_404(db, data.agent_id)
    course = await _get_course_or_404(db, agent.course_id)
    _ensure_course_manager(course=course, user=user)

    existing_workflow = await db.execute(select(AgentWorkflow.id).where(AgentWorkflow.agent_id == agent.id).limit(1))
    workflow = AgentWorkflow(**data.model_dump(), is_active=existing_workflow.scalar_one_or_none() is None)
    db.add(workflow)
    await db.flush()
    await db.commit()
    await db.refresh(workflow)
    return workflow


@router.get("/workflows", response_model=list[AgentWorkflowResponse])
async def list_workflows(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = await _get_agent_or_404(db, agent_id)
    course = await _get_course_or_404(db, agent.course_id)
    await _ensure_course_access(db, course=course, user=user)

    result = await db.execute(
        select(AgentWorkflow).where(AgentWorkflow.agent_id == agent_id).order_by(AgentWorkflow.created_at.desc())
    )
    return result.scalars().all()


@router.get("/workflows/{workflow_id}", response_model=AgentWorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workflow = await _get_workflow_or_404(db, workflow_id)
    agent = await _get_agent_or_404(db, workflow.agent_id)
    course = await _get_course_or_404(db, agent.course_id)
    await _ensure_course_access(db, course=course, user=user)
    return workflow


@router.put("/workflows/{workflow_id}", response_model=AgentWorkflowResponse)
async def update_workflow(
    workflow_id: int,
    data: AgentWorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workflow = await _get_workflow_or_404(db, workflow_id)
    agent = await _get_agent_or_404(db, workflow.agent_id)
    course = await _get_course_or_404(db, agent.course_id)
    _ensure_course_manager(course=course, user=user)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(workflow, field, value)

    await db.flush()
    await db.commit()
    await db.refresh(workflow)
    return workflow


@router.post("/workflows/{workflow_id}/publish", response_model=AgentWorkflowResponse)
async def publish_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workflow = await _get_workflow_or_404(db, workflow_id)
    agent = await _get_agent_or_404(db, workflow.agent_id)
    course = await _get_course_or_404(db, agent.course_id)
    _ensure_course_manager(course=course, user=user)

    await db.execute(
        update(AgentWorkflow).where(AgentWorkflow.agent_id == agent.id).values(is_active=False)
    )
    workflow.is_active = True
    agent.is_active = True

    await db.flush()
    await db.commit()
    await db.refresh(workflow)
    return workflow
