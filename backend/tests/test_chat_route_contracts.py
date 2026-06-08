import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.routes import chat
from models.agent import AgentInstance
from models.chat import ChatMessage, ChatSession


class FakeResult:
    def __init__(self, *, scalar=None, scalars=None):
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
        self.deleted = []
        self.flushed = False
        self.refreshed = []

    def add(self, obj):
        self.added.append(obj)

    async def execute(self, statement):
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

    async def delete(self, obj):
        self.deleted.append(obj)


def make_user(user_id: int = 42):
    return SimpleNamespace(id=user_id)


def make_agent(*, agent_id: int = 7, course_id: int = 3, is_active: bool = True):
    agent = AgentInstance(
        course_id=course_id,
        name="QA Agent",
        description="demo",
        config={},
        system_prompt="You are helpful.",
        tools=[],
        llm_provider="dashscope",
        llm_model="qwen-max",
        created_by=1,
    )
    agent.id = agent_id
    agent.is_active = is_active
    return agent


def make_session(*, session_id: int = 8, user_id: int = 42, course_id: int = 3, agent_id: int = 7):
    session = ChatSession(
        user_id=user_id,
        agent_id=agent_id,
        course_id=course_id,
        title="existing",
    )
    session.id = session_id
    return session


def parse_sse_events(payload: bytes) -> list[dict]:
    events = []
    for block in payload.decode("utf-8").strip().split("\n\n"):
        if not block.startswith("data: "):
            continue
        events.append(json.loads(block[6:]))
    return events


@pytest.fixture(autouse=True)
def patch_course_access(monkeypatch):
    async def fake_resolve_course(*, data, db):
        return SimpleNamespace(id=data.course_id, teacher_id=1)

    async def fake_ensure_course_access(db, *, course, user):
        return None

    monkeypatch.setattr(chat, "_resolve_course", fake_resolve_course)
    monkeypatch.setattr(chat, "ensure_course_access", fake_ensure_course_access)


def test_chat_router_has_single_send_stream_route():
    send_stream_routes = [
        route
        for route in chat.router.routes
        if getattr(route, "path", "") == "/send-stream" and "POST" in getattr(route, "methods", set())
    ]
    assert len(send_stream_routes) == 1


def test_agent_config_uses_published_runtime_mapping():
    agent = make_agent()
    agent.tools = ["rag"]
    agent.config = {
        "workflow_mode": "mapped_qa_pipeline",
        "top_k": 8,
        "similarity_threshold": 0.75,
    }

    config = chat._agent_config(agent, course_id=agent.course_id)

    assert config.llm_model == "qwen-max"
    assert config.tools == ["rag"]
    assert config.top_k == 8
    assert config.similarity_threshold == 0.75


@pytest.mark.asyncio
async def test_send_message_success(monkeypatch):
    agent = make_agent()
    db = FakeDB(results=[FakeResult(scalar=agent), FakeResult(scalars=[])])
    data = chat.ChatRequest(agent_id=agent.id, course_id=agent.course_id, message="hello")

    async def fake_chat(self, query, history=None, context=None):
        assert history == []
        assert query == "hello"
        return "assistant reply"

    monkeypatch.setattr(chat.QAAgent, "chat", fake_chat)

    result = await chat.send_message(data=data, db=db, user=make_user())

    assert result["session_id"] == 1
    assert result["message"].content == "assistant reply"
    assert [item.role for item in db.added if isinstance(item, ChatMessage)] == ["user", "assistant"]


@pytest.mark.asyncio
async def test_send_message_stream_success(monkeypatch):
    agent = make_agent()
    db = FakeDB(results=[FakeResult(scalar=agent), FakeResult(scalars=[])])
    data = chat.ChatRequest(agent_id=agent.id, course_id=agent.course_id, message="hello")

    async def fake_chat_stream(self, query, history=None, context=None):
        assert history == []
        yield "part-1"
        yield "part-2"

    monkeypatch.setattr(chat.QAAgent, "chat_stream", fake_chat_stream)

    response = await chat.send_message_stream(data=data, db=db, user=make_user())
    payload = b""
    async for chunk in response.body_iterator:
        payload += chunk.encode("utf-8") if isinstance(chunk, str) else chunk

    events = parse_sse_events(payload)

    assert events[:2] == [
        {"type": "chunk", "content": "part-1"},
        {"type": "chunk", "content": "part-2"},
    ]
    assert events[2]["type"] == "done"
    assert events[2]["session_id"] == 1
    assert events[2]["message_id"] == 3
    assert db.added[-1].content == "part-1part-2"


@pytest.mark.asyncio
async def test_send_message_rejects_missing_session():
    agent = make_agent()
    db = FakeDB(results=[FakeResult(scalar=agent), FakeResult(scalar=None)])
    data = chat.ChatRequest(agent_id=agent.id, course_id=agent.course_id, session_id=99, message="hello")

    with pytest.raises(HTTPException) as exc:
        await chat.send_message(data=data, db=db, user=make_user())

    assert exc.value.status_code == 404
    assert exc.value.detail == "Session not found"


@pytest.mark.asyncio
async def test_send_message_rejects_session_course_mismatch():
    agent = make_agent()
    session = make_session(course_id=999, agent_id=agent.id)
    db = FakeDB(results=[FakeResult(scalar=agent), FakeResult(scalar=session)])
    data = chat.ChatRequest(agent_id=agent.id, course_id=agent.course_id, session_id=session.id, message="hello")

    with pytest.raises(HTTPException) as exc:
        await chat.send_message(data=data, db=db, user=make_user())

    assert exc.value.status_code == 400
    assert exc.value.detail == "Session course mismatch"


@pytest.mark.asyncio
async def test_send_message_rejects_session_agent_mismatch():
    agent = make_agent()
    session = make_session(agent_id=999)
    db = FakeDB(results=[FakeResult(scalar=agent), FakeResult(scalar=session)])
    data = chat.ChatRequest(agent_id=agent.id, course_id=agent.course_id, session_id=session.id, message="hello")

    with pytest.raises(HTTPException) as exc:
        await chat.send_message(data=data, db=db, user=make_user())

    assert exc.value.status_code == 400
    assert exc.value.detail == "Session agent mismatch"


@pytest.mark.asyncio
async def test_send_message_rejects_agent_course_mismatch():
    agent = make_agent(course_id=5)
    db = FakeDB(results=[FakeResult(scalar=agent)])
    data = chat.ChatRequest(agent_id=agent.id, course_id=3, message="hello")

    with pytest.raises(HTTPException) as exc:
        await chat.send_message(data=data, db=db, user=make_user())

    assert exc.value.status_code == 400
    assert exc.value.detail == "Agent does not belong to this course"


@pytest.mark.asyncio
async def test_send_message_rejects_inactive_agent():
    agent = make_agent(is_active=False)
    db = FakeDB(results=[FakeResult(scalar=agent)])
    data = chat.ChatRequest(agent_id=agent.id, course_id=agent.course_id, message="hello")

    with pytest.raises(HTTPException) as exc:
        await chat.send_message(data=data, db=db, user=make_user())

    assert exc.value.status_code == 409
    assert exc.value.detail == "Agent is not active"


@pytest.mark.asyncio
async def test_send_message_rejects_forbidden_course_access(monkeypatch):
    agent = make_agent()
    db = FakeDB()
    data = chat.ChatRequest(agent_id=agent.id, course_id=agent.course_id, message="hello")

    async def fake_ensure_course_access(db, *, course, user):
        raise HTTPException(status_code=403, detail="Not allowed to access this course")

    monkeypatch.setattr(chat, "ensure_course_access", fake_ensure_course_access)

    with pytest.raises(HTTPException) as exc:
        await chat.send_message(data=data, db=db, user=make_user())

    assert exc.value.status_code == 403
    assert exc.value.detail == "Not allowed to access this course"
