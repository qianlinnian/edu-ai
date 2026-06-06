from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import AgentInstance, AgentWorkflow


@dataclass(frozen=True)
class CourseAgentCapability:
    course_id: int
    agent_id: int | None
    workflow_id: int | None
    enabled_node_types: tuple[str, ...]
    can_chat: bool
    has_rag: bool
    has_grading: bool
    has_analytics: bool
    has_exercise: bool


def _empty_capability(course_id: int) -> CourseAgentCapability:
    return CourseAgentCapability(
        course_id=course_id,
        agent_id=None,
        workflow_id=None,
        enabled_node_types=(),
        can_chat=False,
        has_rag=False,
        has_grading=False,
        has_analytics=False,
        has_exercise=False,
    )


def _enabled_node_types(workflow_dag: dict[str, Any] | None) -> tuple[str, ...]:
    nodes = workflow_dag.get("nodes") if isinstance(workflow_dag, dict) else []
    ordered: list[str] = []
    seen: set[str] = set()
    for node in nodes if isinstance(nodes, list) else []:
        node_type = str((node or {}).get("data", {}).get("nodeType", "")).strip()
        if node_type and node_type not in seen:
            seen.add(node_type)
            ordered.append(node_type)
    return tuple(ordered)


async def get_published_course_agent_capability(db: AsyncSession, *, course_id: int) -> CourseAgentCapability:
    agent = (
        await db.execute(
            select(AgentInstance)
            .where(
                AgentInstance.course_id == course_id,
                AgentInstance.is_active.is_(True),
            )
            .order_by(desc(AgentInstance.updated_at), desc(AgentInstance.id))
            .limit(1)
        )
    ).scalar_one_or_none()
    if agent is None:
        return _empty_capability(course_id)

    workflow = (
        await db.execute(
            select(AgentWorkflow)
            .where(
                AgentWorkflow.agent_id == agent.id,
                AgentWorkflow.is_active.is_(True),
            )
            .order_by(desc(AgentWorkflow.created_at), desc(AgentWorkflow.id))
            .limit(1)
        )
    ).scalar_one_or_none()
    if workflow is None:
        return _empty_capability(course_id)

    enabled_node_types = _enabled_node_types(workflow.workflow_dag)
    enabled = set(enabled_node_types)
    return CourseAgentCapability(
        course_id=course_id,
        agent_id=agent.id,
        workflow_id=workflow.id,
        enabled_node_types=enabled_node_types,
        can_chat={"input_node", "llm_node", "output_node"}.issubset(enabled),
        has_rag="rag_node" in enabled,
        has_grading="grading_node" in enabled,
        has_analytics="analytics_node" in enabled,
        has_exercise="exercise_node" in enabled,
    )
