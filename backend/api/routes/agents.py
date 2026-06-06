from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from models.agent import (
    AgentInstance,
    AgentTemplate,
    AgentWorkflow,
    build_agent_runtime_config_from_workflow,
    infer_llm_provider_from_model,
    validate_workflow_dag,
)
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


def _validate_workflow_or_400(workflow_dag: dict, *, course_id: int, for_publish: bool) -> dict:
    validation = validate_workflow_dag(workflow_dag, course_id=course_id)
    errors = list(validation["errors"])
    if for_publish:
        errors.extend(validation["publish_errors"])
    if errors:
        raise HTTPException(status_code=400, detail="Workflow validation failed: " + "; ".join(errors))
    return validation


def _apply_workflow_publication(agent: AgentInstance, workflow: AgentWorkflow) -> None:
    runtime_config = build_agent_runtime_config_from_workflow(workflow.workflow_dag, course_id=agent.course_id)
    config = dict(agent.config or {})
    config.update(
        {
            "agent_type": runtime_config["agent_type"],
            "workflow_mode": runtime_config["workflow_mode"],
            "runtime_note": runtime_config["runtime_note"],
            "top_k": runtime_config["top_k"],
            "similarity_threshold": runtime_config["similarity_threshold"],
            "workflow_summary": runtime_config["workflow_summary"],
            "workflow_mapping": runtime_config["workflow_mapping"],
        }
    )
    agent.config = config
    agent.tools = runtime_config["tools"]
    agent.llm_provider = runtime_config["llm_provider"]
    agent.llm_model = runtime_config["llm_model"]
    agent.is_active = True


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


async def _get_agent_by_course(db: AsyncSession, *, course_id: int) -> AgentInstance | None:
    result = await db.execute(
        select(AgentInstance)
        .where(AgentInstance.course_id == course_id)
        .order_by(AgentInstance.is_active.desc(), desc(AgentInstance.updated_at), desc(AgentInstance.id))
        .limit(1)
    )
    return result.scalar_one_or_none()


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


def _normalize_agent_llm_payload(payload: dict) -> dict:
    next_payload = dict(payload)
    model = next_payload.get("llm_model")
    if isinstance(model, str) and model.strip():
        next_payload["llm_provider"] = infer_llm_provider_from_model(model)
    return next_payload


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

    existing_agent = await _get_agent_by_course(db, course_id=data.course_id)
    if existing_agent is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Course {data.course_id} already has an Agent. Reuse and update agent_id={existing_agent.id} instead.",
        )

    payload = _normalize_agent_llm_payload(data.model_dump())
    agent = AgentInstance(**payload, created_by=user.id)
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
    payload = _normalize_agent_llm_payload(payload)
    new_course_id = payload.get("course_id")
    if new_course_id is not None and new_course_id != agent.course_id:
        new_course = await _get_course_or_404(db, new_course_id)
        _ensure_course_manager(course=new_course, user=user)
        existing_agent = await _get_agent_by_course(db, course_id=new_course_id)
        if existing_agent is not None and existing_agent.id != agent.id:
            raise HTTPException(
                status_code=409,
                detail=f"Course {new_course_id} already has an Agent. Reassigning this agent would create duplicates.",
            )

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

    workflow_result = await db.execute(
        select(AgentWorkflow)
        .where(AgentWorkflow.agent_id == agent.id)
        .order_by(AgentWorkflow.is_active.desc(), desc(AgentWorkflow.created_at))
        .limit(1)
    )
    workflow = workflow_result.scalar_one_or_none()
    if workflow is None:
        raise HTTPException(status_code=409, detail="Agent workflow is required before publishing")

    _validate_workflow_or_400(workflow.workflow_dag, course_id=agent.course_id, for_publish=True)
    _apply_workflow_publication(agent, workflow)
    workflow.is_active = True
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
    _validate_workflow_or_400(data.workflow_dag, course_id=agent.course_id, for_publish=False)

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

    payload = data.model_dump(exclude_unset=True)
    if "workflow_dag" in payload:
        _validate_workflow_or_400(payload["workflow_dag"], course_id=agent.course_id, for_publish=False)

    for field, value in payload.items():
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
    _validate_workflow_or_400(workflow.workflow_dag, course_id=agent.course_id, for_publish=True)

    await db.execute(
        update(AgentWorkflow).where(AgentWorkflow.agent_id == agent.id).values(is_active=False)
    )
    workflow.is_active = True
    _apply_workflow_publication(agent, workflow)

    await db.flush()
    await db.commit()
    await db.refresh(workflow)
    return workflow
