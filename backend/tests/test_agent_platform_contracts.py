from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from api.routes import agents, platform
from models.agent import AgentInstance, AgentWorkflow
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
        self.refreshed = []

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

    async def refresh(self, obj):
        self.refreshed.append(obj)


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


def make_workflow(agent_id: int = 3, is_active: bool = False) -> AgentWorkflow:
    workflow = AgentWorkflow(
        agent_id=agent_id,
        name="Demo Workflow",
        description="demo",
        workflow_dag={"nodes": [], "edges": []},
        is_active=is_active,
    )
    workflow.id = 5
    return workflow


@pytest.mark.asyncio
async def test_create_workflow_preserves_workflow_dag(monkeypatch):
    agent = make_agent()
    course = SimpleNamespace(id=agent.course_id, teacher_id=7)
    db = FakeDB(results=[FakeResult(scalar=123)])
    payload = agents.AgentWorkflowCreate(
        agent_id=agent.id,
        name="Saved Workflow",
        description="persist dag",
        workflow_dag={"nodes": [{"id": "n1"}], "edges": [{"id": "e1"}]},
    )

    monkeypatch.setattr(agents, "_get_agent_or_404", AsyncMock(return_value=agent))
    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(return_value=course))

    result = await agents.create_workflow(data=payload, db=db, user=make_teacher())

    assert db.flushed is True
    assert db.added[0].workflow_dag == payload.workflow_dag
    assert db.added[0].is_active is False
    assert result.workflow_dag == payload.workflow_dag


@pytest.mark.asyncio
async def test_publish_workflow_marks_agent_and_workflow_active(monkeypatch):
    agent = make_agent()
    workflow = make_workflow(agent_id=agent.id, is_active=False)
    course = SimpleNamespace(id=agent.course_id, teacher_id=7)
    db = FakeDB()

    monkeypatch.setattr(agents, "_get_workflow_or_404", AsyncMock(return_value=workflow))
    monkeypatch.setattr(agents, "_get_agent_or_404", AsyncMock(return_value=agent))
    monkeypatch.setattr(agents, "_get_course_or_404", AsyncMock(return_value=course))

    result = await agents.publish_workflow(workflow_id=workflow.id, db=db, user=make_teacher())

    assert len(db.execute_calls) == 1
    assert workflow.is_active is True
    assert agent.is_active is True
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
        platform.ChaoxingLaunchRequest(course=1, token="TOKEN", role="student")
    )
    dingtalk_result = await platform.dingtalk_auth(code="demo-code", course_id=2)

    assert chaoxing_result == {
        "platform": "chaoxing",
        "status": "ok",
        "message": "超星LTI对接端点",
        "widget_url": "/widget/chat?course=1&token=TOKEN",
        "course": 1,
        "role": "student",
    }
    assert dingtalk_result == {
        "platform": "dingtalk",
        "status": "ok",
        "message": "钉钉认证端点",
        "code": "demo-code",
        "course_id": 2,
        "widget_url": "/widget/chat?course=2&token=YOUR_TOKEN",
    }
