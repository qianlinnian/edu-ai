from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from api.routes import agents, platform
from models.agent import AgentInstance, AgentWorkflow, build_agent_runtime_config_from_workflow, validate_workflow_dag
from models.user import UserRole


class FakeResult:
    def __init__(self, scalar=None, scalars=None):
        self._scalar = scalar
        self._scalars = scalars or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return self

    def all(self):
        return self._scalars


class FakeDB:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.added = []
        self.execute_calls = []
        self.flushed = False
        self.committed = False
        self.refreshed = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    async def execute(self, statement):
        self.execute_calls.append(statement)
        if self.results:
            return self.results.pop(0)
        return FakeResult()

    async def flush(self):
        self.flushed = True
        for index, obj in enumerate(self.added, start=1):
            if getattr(obj, "id", None) is None:
                obj.id = index

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed.append(obj)

    async def commit(self):
        self.committed = True


def make_teacher():
    return SimpleNamespace(id=7, role=UserRole.TEACHER)


def make_agent(course_id: int = 9) -> AgentInstance:
    agent = AgentInstance(
        course_id=course_id,
        name="Demo Agent",
        description="demo",
        config={"agent_type": "qa"},
        system_prompt="You are helpful.",
        tools=["rag"],
        llm_provider="dashscope",
        llm_model="qwen-max",
        created_by=7,
    )
    agent.id = 3
    agent.is_active = False
    return agent


def valid_workflow_dag(course_id: int = 9, *, include_rag: bool = True, include_ui_only: bool = False) -> dict:
    nodes = [
        {
            "id": "n1",
            "type": "custom",
            "position": {"x": 0, "y": 0},
            "data": {"label": "用户输入", "nodeType": "input_node"},
        },
        {
            "id": "n3",
            "type": "custom",
            "position": {"x": 0, "y": 160},
            "data": {"label": "LLM", "nodeType": "llm_node", "model": "qwen-max"},
        },
        {
            "id": "n4",
            "type": "custom",
            "position": {"x": 0, "y": 240},
            "data": {"label": "输出", "nodeType": "output_node"},
        },
    ]
    edges = [
        {"id": "e2", "source": "n3", "target": "n4"},
    ]

    if include_rag:
        nodes.insert(
            1,
            {
                "id": "n2",
                "type": "custom",
                "position": {"x": 0, "y": 80},
                "data": {
                    "label": "知识检索",
                    "nodeType": "rag_node",
                    "course": course_id,
                    "topK": 5,
                    "similarity": 0.7,
                },
            },
        )
        edges.insert(0, {"id": "e1", "source": "n1", "target": "n2"})
        edges.insert(1, {"id": "e1b", "source": "n2", "target": "n3"})
    else:
        edges.insert(0, {"id": "e1", "source": "n1", "target": "n3"})

    if include_ui_only:
        nodes.append(
            {
                "id": "n5",
                "type": "custom",
                "position": {"x": 200, "y": 120},
                "data": {"label": "作业批改", "nodeType": "grading_node"},
            }
        )

    return {"nodes": nodes, "edges": edges}


def make_workflow(agent_id: int = 3, is_active: bool = False, *, workflow_dag: dict | None = None) -> AgentWorkflow:
    workflow = AgentWorkflow(
        agent_id=agent_id,
        name="Demo Workflow",
        description="demo",
        workflow_dag=workflow_dag or valid_workflow_dag(),
        is_active=is_active,
    )
    workflow.id = 5
    return workflow


def test_validate_workflow_dag_reports_missing_required_nodes():
    result = validate_workflow_dag({"nodes": [], "edges": []}, course_id=9)

    assert "Workflow requires input_node" in result["errors"]
    assert "Workflow requires llm_node" in result["errors"]
    assert "Workflow requires output_node" in result["errors"]


def test_build_agent_runtime_config_from_workflow_maps_supported_nodes():
    runtime = build_agent_runtime_config_from_workflow(valid_workflow_dag(course_id=9), course_id=9)

    assert runtime["workflow_mode"] == "mapped_qa_pipeline"
    assert runtime["llm_provider"] == "dashscope"
    assert runtime["llm_model"] == "qwen-max"
    assert runtime["tools"] == ["rag"]
    assert runtime["workflow_mapping"]["rag_node_id"] == "n2"


def test_build_agent_runtime_config_infers_provider_from_llm_model():
    workflow = valid_workflow_dag(course_id=9)
    workflow["nodes"][2]["data"]["model"] = "deepseek-chat"

    runtime = build_agent_runtime_config_from_workflow(workflow, course_id=9)

    assert runtime["llm_provider"] == "deepseek"
    assert runtime["llm_model"] == "deepseek-chat"


def test_build_agent_runtime_config_uses_explicit_model_provider_mapping():
    workflow = valid_workflow_dag(course_id=9)
    workflow["nodes"][2]["data"]["model"] = "qwen-vl-max"

    runtime = build_agent_runtime_config_from_workflow(workflow, course_id=9)

    assert runtime["llm_provider"] == "dashscope"
    assert runtime["llm_model"] == "qwen-vl-max"


@pytest.mark.asyncio
async def test_create_workflow_preserves_validated_workflow_dag(monkeypatch):
    agent = make_agent()
    course = SimpleNamespace(id=agent.course_id, teacher_id=7)
    db = FakeDB(results=[FakeResult(scalar=123)])
    payload = agents.AgentWorkflowCreate(
        agent_id=agent.id,
        name="Saved Workflow",
        description="persist dag",
        workflow_dag=valid_workflow_dag(course_id=agent.course_id),
    )

    monkeypatch.setattr(agents, "_get_agent_or_404", AsyncMock(return_value=agent))
    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(return_value=course))

    result = await agents.create_workflow(data=payload, db=db, user=make_teacher())

    assert db.flushed is True
    assert db.committed is True
    assert db.added[0].workflow_dag == payload.workflow_dag
    assert db.added[0].is_active is False
    assert result.workflow_dag == payload.workflow_dag


@pytest.mark.asyncio
async def test_create_agent_rejects_duplicate_agent_for_same_course(monkeypatch):
    course = SimpleNamespace(id=9, teacher_id=7)
    existing_agent = make_agent(course_id=9)
    db = FakeDB()
    payload = agents.AgentInstanceCreate(
        course_id=9,
        name="Another Agent",
        description="dup",
        config={},
        system_prompt="You are helpful.",
        tools=[],
        llm_provider="dashscope",
        llm_model="qwen-max",
    )

    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(return_value=course))
    monkeypatch.setattr(agents, "_get_agent_by_course", AsyncMock(return_value=existing_agent))

    with pytest.raises(HTTPException) as exc:
        await agents.create_agent(data=payload, db=db, user=make_teacher())

    assert exc.value.status_code == 409
    assert "already has an Agent" in exc.value.detail


@pytest.mark.asyncio
async def test_create_agent_normalizes_provider_from_model(monkeypatch):
    course = SimpleNamespace(id=9, teacher_id=7)
    db = FakeDB()
    payload = agents.AgentInstanceCreate(
        course_id=9,
        name="DeepSeek Agent",
        description="provider normalization",
        config={},
        system_prompt="You are helpful.",
        tools=[],
        llm_provider="dashscope",
        llm_model="deepseek-chat",
    )

    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(return_value=course))
    monkeypatch.setattr(agents, "_get_agent_by_course", AsyncMock(return_value=None))

    result = await agents.create_agent(data=payload, db=db, user=make_teacher())

    assert db.added[0].llm_model == "deepseek-chat"
    assert db.added[0].llm_provider == "deepseek"
    assert result.llm_provider == "deepseek"


@pytest.mark.asyncio
async def test_update_agent_rejects_reassigning_to_course_with_existing_agent(monkeypatch):
    agent = make_agent(course_id=9)
    existing_agent = make_agent(course_id=11)
    existing_agent.id = 88
    current_course = SimpleNamespace(id=9, teacher_id=7)
    new_course = SimpleNamespace(id=11, teacher_id=7)
    db = FakeDB()
    payload = agents.AgentInstanceUpdate(course_id=11)

    monkeypatch.setattr(agents, "_get_agent_or_404", AsyncMock(return_value=agent))
    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(side_effect=[current_course, new_course]))
    monkeypatch.setattr(agents, "_get_agent_by_course", AsyncMock(return_value=existing_agent))

    with pytest.raises(HTTPException) as exc:
        await agents.update_agent(agent_id=agent.id, data=payload, db=db, user=make_teacher())

    assert exc.value.status_code == 409
    assert "would create duplicates" in exc.value.detail


@pytest.mark.asyncio
async def test_update_agent_normalizes_provider_from_model(monkeypatch):
    agent = make_agent(course_id=9)
    current_course = SimpleNamespace(id=9, teacher_id=7)
    db = FakeDB()
    payload = agents.AgentInstanceUpdate(llm_provider="dashscope", llm_model="deepseek-chat")

    monkeypatch.setattr(agents, "_get_agent_or_404", AsyncMock(return_value=agent))
    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(return_value=current_course))

    result = await agents.update_agent(agent_id=agent.id, data=payload, db=db, user=make_teacher())

    assert agent.llm_model == "deepseek-chat"
    assert agent.llm_provider == "deepseek"
    assert result.llm_provider == "deepseek"


@pytest.mark.asyncio
async def test_create_workflow_rejects_invalid_dag(monkeypatch):
    agent = make_agent()
    course = SimpleNamespace(id=agent.course_id, teacher_id=7)
    db = FakeDB()
    payload = agents.AgentWorkflowCreate(
        agent_id=agent.id,
        name="Invalid Workflow",
        workflow_dag={"nodes": [{"id": "n1", "data": {"nodeType": "input_node"}}], "edges": []},
    )

    monkeypatch.setattr(agents, "_get_agent_or_404", AsyncMock(return_value=agent))
    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(return_value=course))

    with pytest.raises(HTTPException) as exc:
        await agents.create_workflow(data=payload, db=db, user=make_teacher())

    assert exc.value.status_code == 400
    assert "Workflow validation failed" in exc.value.detail


@pytest.mark.asyncio
async def test_publish_workflow_marks_agent_active_and_applies_runtime_mapping(monkeypatch):
    agent = make_agent()
    workflow = make_workflow(agent_id=agent.id, is_active=False, workflow_dag=valid_workflow_dag(course_id=agent.course_id))
    course = SimpleNamespace(id=agent.course_id, teacher_id=7)
    db = FakeDB()

    monkeypatch.setattr(agents, "_get_workflow_or_404", AsyncMock(return_value=workflow))
    monkeypatch.setattr(agents, "_get_agent_or_404", AsyncMock(return_value=agent))
    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(return_value=course))

    result = await agents.publish_workflow(workflow_id=workflow.id, db=db, user=make_teacher())

    assert len(db.execute_calls) == 1
    assert workflow.is_active is True
    assert agent.is_active is True
    assert agent.config["workflow_mode"] == "mapped_qa_pipeline"
    assert agent.llm_provider == "dashscope"
    assert agent.config["workflow_mapping"]["llm_node_id"] == "n3"
    assert agent.llm_model == "qwen-max"
    assert agent.tools == ["rag"]
    assert result.is_active is True


@pytest.mark.asyncio
async def test_publish_workflow_allows_ui_only_nodes_as_capability_switches(monkeypatch):
    agent = make_agent()
    workflow = make_workflow(
        agent_id=agent.id,
        workflow_dag=valid_workflow_dag(course_id=agent.course_id, include_ui_only=True),
    )
    course = SimpleNamespace(id=agent.course_id, teacher_id=7)
    db = FakeDB()

    monkeypatch.setattr(agents, "_get_workflow_or_404", AsyncMock(return_value=workflow))
    monkeypatch.setattr(agents, "_get_agent_or_404", AsyncMock(return_value=agent))
    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(return_value=course))

    result = await agents.publish_workflow(workflow_id=workflow.id, db=db, user=make_teacher())

    assert workflow.is_active is True
    assert agent.is_active is True
    assert agent.config["workflow_mode"] == "mapped_qa_pipeline"
    assert result.is_active is True


def test_platform_connection_requires_platform_specific_config():
    platform.PlatformConnectionCreate(
        platform_type="chaoxing",
        name="Chaoxing Demo",
        config={
            "lti_key": "demo-lti-key",
            "lti_secret": "demo-lti-secret",
            "callback_url": "https://example.com/lti/chaoxing",
        },
    )

    with pytest.raises(ValidationError):
        platform.PlatformConnectionCreate(
            platform_type="dingtalk",
            name="DingTalk Demo",
            config={"app_key": "demo-app-key"},
        )


@pytest.mark.asyncio
async def test_platform_mock_endpoints_return_stable_payloads():
    chaoxing_result = await platform.chaoxing_lti_launch(
        platform.ChaoxingLaunchRequest(course_id=1, launch_ticket="launch-ticket-001", role="student"),
        request=SimpleNamespace(headers={"origin": "https://demo.eduai.example"}),
        user=make_teacher(),
    )
    dingtalk_result = await platform.dingtalk_auth(
        request=SimpleNamespace(headers={"referer": "https://portal.example.com/platform"}),
        code="auth-code-001",
        course_id=2,
        role="teacher",
        user=make_teacher(),
    )
    chaoxing_payload = chaoxing_result.model_dump()
    dingtalk_payload = dingtalk_result.model_dump()

    assert chaoxing_payload["platform"] == "chaoxing"
    assert chaoxing_payload["mode"] == "simulated"
    assert chaoxing_payload["status"] == "ok"
    assert chaoxing_payload["message"] == "Simulated chaoxing launch prepared"
    assert chaoxing_payload["course_id"] == 1
    assert chaoxing_payload["role"] == "student"
    assert chaoxing_payload["token"]
    assert chaoxing_payload["token_source"] == "issued_by_edu_ai_backend"
    assert chaoxing_payload["course_id_source"] == "provided_by_upstream_platform_payload"
    assert chaoxing_payload["role_source"] == "provided_by_upstream_platform_payload"
    assert chaoxing_payload["upstream_reference"] == "launch-ticket-001"
    assert chaoxing_payload["upstream_reference_type"] == "launch_ticket"
    assert chaoxing_payload["widget_url"].startswith("https://demo.eduai.example/widget/chat?course=1&token=")
    assert "simulated platform integration" in chaoxing_payload["integration_boundary"].lower()

    assert dingtalk_payload["platform"] == "dingtalk"
    assert dingtalk_payload["mode"] == "simulated"
    assert dingtalk_payload["status"] == "ok"
    assert dingtalk_payload["message"] == "Simulated dingtalk launch prepared"
    assert dingtalk_payload["course_id"] == 2
    assert dingtalk_payload["role"] == "teacher"
    assert dingtalk_payload["token"]
    assert dingtalk_payload["token_source"] == "issued_by_edu_ai_backend"
    assert dingtalk_payload["course_id_source"] == "provided_by_upstream_platform_payload"
    assert dingtalk_payload["role_source"] == "provided_by_upstream_platform_payload"
    assert dingtalk_payload["upstream_reference"] == "auth-code-001"
    assert dingtalk_payload["upstream_reference_type"] == "auth_code"
    assert dingtalk_payload["widget_url"].startswith("https://portal.example.com/widget/chat?course=2&token=")
