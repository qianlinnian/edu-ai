from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

SUPPORTED_WORKFLOW_NODE_TYPES = {
    "input_node": {
        "label": "User Input",
        "semantic": "Workflow entrypoint. Accepts the incoming learner request.",
        "runtime_supported": True,
    },
    "rag_node": {
        "label": "Knowledge Retrieval",
        "semantic": "Retrieves course context before the LLM step.",
        "runtime_supported": True,
    },
    "llm_node": {
        "label": "LLM",
        "semantic": "Generates the final answer for the current QA workflow.",
        "runtime_supported": True,
    },
    "output_node": {
        "label": "Output",
        "semantic": "Marks the final response returned to chat clients.",
        "runtime_supported": True,
    },
    "grading_node": {
        "label": "Grading",
        "semantic": "UI-only prototype node. Not executed by the current runtime.",
        "runtime_supported": False,
    },
    "analytics_node": {
        "label": "Analytics",
        "semantic": "UI-only prototype node. Not executed by the current runtime.",
        "runtime_supported": False,
    },
    "exercise_node": {
        "label": "Exercise",
        "semantic": "UI-only prototype node. Not executed by the current runtime.",
        "runtime_supported": False,
    },
    "condition_node": {
        "label": "Condition",
        "semantic": "UI-only prototype node. Branching is not executed by the current runtime.",
        "runtime_supported": False,
    },
}
RUNTIME_WORKFLOW_NODE_TYPES = {name for name, meta in SUPPORTED_WORKFLOW_NODE_TYPES.items() if meta["runtime_supported"]}


def _normalize_nodes(workflow_dag: dict[str, Any] | None) -> list[dict[str, Any]]:
    raw_nodes = workflow_dag.get("nodes") if isinstance(workflow_dag, dict) else []
    return [node for node in raw_nodes if isinstance(node, dict)]


def _normalize_edges(workflow_dag: dict[str, Any] | None) -> list[dict[str, Any]]:
    raw_edges = workflow_dag.get("edges") if isinstance(workflow_dag, dict) else []
    return [edge for edge in raw_edges if isinstance(edge, dict)]


def validate_workflow_dag(
    workflow_dag: dict[str, Any] | None,
    *,
    course_id: int | None = None,
) -> dict[str, Any]:
    nodes = _normalize_nodes(workflow_dag)
    edges = _normalize_edges(workflow_dag)
    errors: list[str] = []
    publish_errors: list[str] = []

    if not isinstance(workflow_dag, dict):
        errors.append("workflow_dag must be an object")
        return {"errors": errors, "publish_errors": publish_errors, "warnings": [], "summary": {}}

    if not isinstance(workflow_dag.get("nodes"), list):
        errors.append("workflow_dag.nodes must be a list")
    if not isinstance(workflow_dag.get("edges"), list):
        errors.append("workflow_dag.edges must be a list")
    if errors:
        return {"errors": errors, "publish_errors": publish_errors, "warnings": [], "summary": {}}

    node_ids: set[str] = set()
    node_types: dict[str, str] = {}
    incoming: dict[str, int] = {}
    outgoing: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    ui_only_node_ids: list[str] = []

    for index, node in enumerate(nodes, start=1):
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            errors.append(f"Node #{index} is missing id")
            continue
        if node_id in node_ids:
            errors.append(f"Duplicate node id: {node_id}")
            continue
        node_ids.add(node_id)

        data = node.get("data") if isinstance(node.get("data"), dict) else {}
        node_type = str(data.get("nodeType") or "").strip()
        if node_type not in SUPPORTED_WORKFLOW_NODE_TYPES:
            errors.append(f"Node {node_id} has unsupported nodeType: {node_type or 'missing'}")
            continue

        node_types[node_id] = node_type
        incoming[node_id] = 0
        outgoing[node_id] = 0
        type_counts[node_type] = type_counts.get(node_type, 0) + 1

        if node_type == "rag_node":
            top_k = data.get("topK")
            similarity = data.get("similarity")
            rag_course_id = data.get("course", course_id)
            if not isinstance(top_k, int) or top_k <= 0:
                errors.append(f"RAG node {node_id} requires a positive integer topK")
            if not isinstance(similarity, (int, float)) or not 0 <= float(similarity) <= 1:
                errors.append(f"RAG node {node_id} requires similarity between 0 and 1")
            if course_id is not None and rag_course_id != course_id:
                errors.append(f"RAG node {node_id} course must match the workflow course")
        elif node_type == "llm_node":
            model = str(data.get("model") or "").strip()
            if not model:
                errors.append(f"LLM node {node_id} requires model")
        elif not SUPPORTED_WORKFLOW_NODE_TYPES[node_type]["runtime_supported"]:
            ui_only_node_ids.append(node_id)

    for index, edge in enumerate(edges, start=1):
        edge_id = str(edge.get("id") or f"edge-{index}").strip()
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        if not source or not target:
            errors.append(f"Edge {edge_id} must include source and target")
            continue
        if source not in node_ids or target not in node_ids:
            errors.append(f"Edge {edge_id} references unknown nodes")
            continue
        if source == target:
            errors.append(f"Edge {edge_id} cannot connect a node to itself")
            continue
        outgoing[source] = outgoing.get(source, 0) + 1
        incoming[target] = incoming.get(target, 0) + 1

    required_types = ("input_node", "llm_node", "output_node")
    for required_type in required_types:
        count = type_counts.get(required_type, 0)
        if count == 0:
            errors.append(f"Workflow requires {required_type}")
        elif count > 1:
            errors.append(f"Workflow supports only one {required_type}")

    start_node_ids = sorted(node_id for node_id, count in incoming.items() if count == 0)
    end_node_ids = sorted(node_id for node_id, count in outgoing.items() if count == 0)
    if not start_node_ids:
        errors.append("Workflow must have at least one start node")
    if not end_node_ids:
        errors.append("Workflow must have at least one end node")

    input_node_ids = [node_id for node_id, node_type in node_types.items() if node_type == "input_node"]
    output_node_ids = [node_id for node_id, node_type in node_types.items() if node_type == "output_node"]
    if input_node_ids and input_node_ids[0] not in start_node_ids:
        errors.append("Input node must be a start node")
    if output_node_ids and output_node_ids[0] not in end_node_ids:
        errors.append("Output node must be an end node")

    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        if source in adjacency and target in node_ids and source != target:
            adjacency[source].append(target)

    def has_path(source: str, target: str) -> bool:
        seen = set()
        stack = [source]
        while stack:
            current = stack.pop()
            if current == target:
                return True
            if current in seen:
                continue
            seen.add(current)
            stack.extend(adjacency.get(current, []))
        return False

    if input_node_ids and output_node_ids and not has_path(input_node_ids[0], output_node_ids[0]):
        errors.append("Workflow must contain a path from input_node to output_node")

    llm_node_ids = [node_id for node_id, node_type in node_types.items() if node_type == "llm_node"]
    if input_node_ids and llm_node_ids and not has_path(input_node_ids[0], llm_node_ids[0]):
        errors.append("Workflow must contain a path from input_node to llm_node")
    if llm_node_ids and output_node_ids and not has_path(llm_node_ids[0], output_node_ids[0]):
        errors.append("Workflow must contain a path from llm_node to output_node")

    rag_node_ids = [node_id for node_id, node_type in node_types.items() if node_type == "rag_node"]
    if len(rag_node_ids) > 1:
        publish_errors.append("Current runtime supports at most one rag_node")
    if ui_only_node_ids:
        publish_errors.append(
            "Current runtime cannot publish workflows containing UI-only nodes: "
            + ", ".join(sorted(node_types[node_id] for node_id in ui_only_node_ids))
        )

    summary = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": type_counts,
        "start_node_ids": start_node_ids,
        "end_node_ids": end_node_ids,
        "ui_only_node_ids": sorted(ui_only_node_ids),
        "runtime_supported_node_types": sorted(RUNTIME_WORKFLOW_NODE_TYPES),
    }
    warnings = []
    if ui_only_node_ids:
        warnings.append("Some nodes are UI-only and can be saved but not published.")

    return {
        "errors": errors,
        "publish_errors": publish_errors,
        "warnings": warnings,
        "summary": summary,
    }


def build_agent_runtime_config_from_workflow(
    workflow_dag: dict[str, Any],
    *,
    course_id: int,
) -> dict[str, Any]:
    validation = validate_workflow_dag(workflow_dag, course_id=course_id)
    combined_errors = [*validation["errors"], *validation["publish_errors"]]
    if combined_errors:
        raise ValueError("; ".join(combined_errors))

    nodes = _normalize_nodes(workflow_dag)
    nodes_by_type = {
        node["data"]["nodeType"]: node
        for node in nodes
        if isinstance(node.get("data"), dict) and node["data"].get("nodeType") in RUNTIME_WORKFLOW_NODE_TYPES
    }
    rag_node = nodes_by_type.get("rag_node")
    llm_node = nodes_by_type["llm_node"]

    return {
        "agent_type": "qa",
        "workflow_mode": "mapped_qa_pipeline",
        "runtime_note": (
            "Published workflows are currently mapped into the QA agent config. "
            "The platform does not execute arbitrary workflow nodes as a general runtime engine."
        ),
        "course_id": course_id,
        "top_k": rag_node["data"].get("topK", 5) if rag_node else 5,
        "similarity_threshold": rag_node["data"].get("similarity", 0.7) if rag_node else 0.7,
        "llm_model": llm_node["data"].get("model", "qwen-max"),
        "tools": ["rag"] if rag_node else [],
        "workflow_summary": validation["summary"],
        "workflow_mapping": {
            "input_node_id": nodes_by_type["input_node"]["id"],
            "rag_node_id": rag_node["id"] if rag_node else None,
            "llm_node_id": llm_node["id"],
            "output_node_id": nodes_by_type["output_node"]["id"],
        },
    }


class AgentTemplate(Base):
    __tablename__ = "agent_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_type: Mapped[str] = mapped_column(String(50))  # qa, grading, exercise, custom
    config: Mapped[dict] = mapped_column(JSON)  # 默认配置模板
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    tools: Mapped[list | None] = mapped_column(JSON, nullable=True)  # 工具列表
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AgentInstance(Base):
    __tablename__ = "agent_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("agent_templates.id"), nullable=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSON)  # Agent配置（覆盖模板）
    system_prompt: Mapped[str] = mapped_column(Text)
    tools: Mapped[list | None] = mapped_column(JSON, nullable=True)
    llm_provider: Mapped[str] = mapped_column(String(50), default="dashscope")
    llm_model: Mapped[str] = mapped_column(String(100), default="qwen-max")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class AgentWorkflow(Base):
    __tablename__ = "agent_workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agent_instances.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_dag: Mapped[dict] = mapped_column(JSON)  # DAG结构定义
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
