import asyncio
import time
from types import SimpleNamespace

import pytest

from api.routes import chat
from education import analytics_engine, exercise_engine
from models.agent import AgentInstance
from models.user import UserRole
from models.course import KnowledgeUnit
from models.exercise import ExercisePool, ExerciseType
from models.learning import StudentKnowledgeMastery


class FakeResult:
    def __init__(self, *, scalar=None, scalars=None, rows=None):
        self._scalar = scalar
        self._scalars = scalars or []
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return self

    def all(self):
        return self._rows or self._scalars


class FakeDB:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def execute(self, statement):
        if self.results:
            return self.results.pop(0)
        return FakeResult()

    async def flush(self):
        for index, obj in enumerate(self.added, start=1):
            if getattr(obj, "id", None) is None:
                obj.id = index

    async def refresh(self, obj):
        return None


def make_user(user_id: int = 21):
    return SimpleNamespace(id=user_id, role=UserRole.ADMIN)


def make_agent(course_id: int = 3) -> AgentInstance:
    agent = AgentInstance(
        course_id=course_id,
        name="Chat Agent",
        description="demo",
        config={},
        system_prompt="You are helpful.",
        tools=[],
        llm_provider="dashscope",
        llm_model="qwen-max",
        created_by=1,
    )
    agent.id = 8
    agent.is_active = True
    return agent


def make_choice_exercise() -> ExercisePool:
    exercise = ExercisePool(
        course_id=3,
        exercise_type=ExerciseType.CHOICE,
        difficulty=2,
        question="Which option is correct?",
        options=[{"key": "A", "label": "Right"}, {"key": "B", "label": "Wrong"}],
        answer="B",
        explanation="B is correct.",
        knowledge_point_ids=[301],
        is_generated=False,
    )
    exercise.id = 51
    return exercise


def make_knowledge_unit() -> KnowledgeUnit:
    ku = KnowledgeUnit(
        course_id=3,
        name="Functions",
        description="desc",
        domain="cs",
        difficulty=2,
        tags=None,
        parent_id=None,
        order_index=1,
    )
    ku.id = 301
    return ku


@pytest.mark.asyncio
async def test_learning_loop_smoke_from_attempt_to_alert_to_next_exercise(monkeypatch):
    attempt_db = FakeDB(
        results=[
            FakeResult(scalar=make_choice_exercise()),
            FakeResult(scalars=[301]),
            FakeResult(scalar=None),
        ]
    )
    attempt = await exercise_engine.create_attempt_and_update_mastery(
        attempt_db,
        student_id=21,
        exercise_id=51,
        generated_exercise_id=None,
        student_answer="A",
    )
    mastery = next(item for item in attempt_db.added if isinstance(item, StudentKnowledgeMastery))

    alert_db = FakeDB(
        results=[
            FakeResult(rows=[(mastery, make_knowledge_unit())]),
            FakeResult(scalars=[]),
            FakeResult(scalar=None),
        ]
    )
    created_alerts = await analytics_engine.refresh_learning_alerts(alert_db, course_id=3, student_id=21)

    next_exercise_db = FakeDB(results=[FakeResult(scalars=[make_choice_exercise()])])

    async def fake_knowledge_context(*args, **kwargs):
        return [
            {
                "id": 301,
                "name": "Functions",
                "description": "desc",
                "difficulty": 2,
                "mastery_score": mastery.mastery_score,
                "attempt_count": mastery.attempt_count,
                "correct_count": mastery.correct_count,
            }
        ]

    monkeypatch.setattr(exercise_engine, "_get_knowledge_context", fake_knowledge_context)

    generated = await exercise_engine.generate_targeted_exercises(
        next_exercise_db,
        student_id=21,
        course_id=3,
        knowledge_point_ids=[],
        exercise_type=ExerciseType.CHOICE,
        difficulty=2,
        count=1,
        use_llm=False,
    )

    assert attempt.is_correct is False
    assert mastery.mastery_score == 0.35
    assert created_alerts == 1
    assert generated["target_knowledge_points"][0]["knowledge_unit_id"] == 301
    assert generated["exercises"][0]["source"] == "pool"


@pytest.mark.asyncio
async def test_chat_stream_small_concurrency_baseline(monkeypatch):
    async def fake_chat_stream(self, query, history=None, context=None):
        yield "hello"

    monkeypatch.setattr(chat.QAAgent, "chat_stream", fake_chat_stream)

    async def run_once(index: int) -> str:
        agent = make_agent()
        course = SimpleNamespace(id=agent.course_id, teacher_id=7)
        db = FakeDB(results=[FakeResult(scalar=course), FakeResult(scalar=agent), FakeResult(scalars=[])])
        response = await chat.send_message_stream(
            data=chat.ChatRequest(agent_id=agent.id, course_id=agent.course_id, message=f"q-{index}"),
            db=db,
            user=make_user(index + 1),
        )
        parts: list[str] = []
        async for chunk in response.body_iterator:
            parts.append(chunk if isinstance(chunk, str) else chunk.decode("utf-8"))
        return "".join(parts)

    started = time.perf_counter()
    outputs = await asyncio.gather(*(run_once(index) for index in range(5)))
    elapsed = time.perf_counter() - started

    assert all('"type": "done"' in output for output in outputs)
    assert elapsed < 2.0
