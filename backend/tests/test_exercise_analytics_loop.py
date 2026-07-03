from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from api.routes import exercises
from education import analytics_engine, exercise_engine
from models.course import KnowledgeUnit
from models.exercise import ExercisePool, ExerciseType, GeneratedExercise
from models.learning import LearningAlert, StudentKnowledgeMastery
from models.user import UserRole


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
        self.refreshed = []

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
        self.refreshed.append(obj)


def make_user(user_id: int = 11, role: UserRole = UserRole.STUDENT):
    return SimpleNamespace(id=user_id, role=role)


def make_pool_exercise(*, kp_ids=None):
    item = ExercisePool(
        course_id=3,
        exercise_type=ExerciseType.CHOICE,
        difficulty=2,
        question="Which option is correct?",
        options=[{"key": "A", "label": "Right"}, {"key": "B", "label": "Wrong"}],
        answer="A",
        explanation="Because A is correct.",
        knowledge_point_ids=kp_ids or [101],
        is_generated=False,
    )
    item.id = 99
    return item


def make_generated_exercise(*, kp_ids=None):
    item = GeneratedExercise(
        student_id=11,
        course_id=3,
        exercise_type=ExerciseType.CHOICE,
        question="Generated question",
        options=[{"key": "A", "label": "Right"}, {"key": "B", "label": "Wrong"}],
        answer="A",
        explanation="Because A is correct.",
        target_knowledge_points=kp_ids or [101, 999],
        difficulty=2,
    )
    item.id = 199
    return item


def make_mastery(*, student_id=11, knowledge_unit_id=101, mastery_score=0.2):
    mastery = StudentKnowledgeMastery(
        student_id=student_id,
        knowledge_unit_id=knowledge_unit_id,
        mastery_score=mastery_score,
        attempt_count=1,
        correct_count=0,
    )
    mastery.id = 1
    return mastery


def make_knowledge_unit(*, knowledge_unit_id=101, course_id=3, name="Loops"):
    unit = KnowledgeUnit(
        course_id=course_id,
        name=name,
        description="desc",
        domain="cs",
        difficulty=2,
        tags=None,
        parent_id=None,
        order_index=1,
    )
    unit.id = knowledge_unit_id
    return unit


@pytest.mark.asyncio
async def test_create_attempt_updates_mastery_after_successful_answer():
    exercise = make_pool_exercise()
    db = FakeDB(
        results=[
            FakeResult(scalar=exercise),
            FakeResult(scalars=[101]),
            FakeResult(scalar=None),
        ]
    )

    attempt = await exercise_engine.create_attempt_and_update_mastery(
        db,
        student_id=11,
        exercise_id=exercise.id,
        generated_exercise_id=None,
        student_answer="A",
    )

    mastery = next(item for item in db.added if isinstance(item, StudentKnowledgeMastery))

    assert attempt.is_correct is True
    assert attempt.score == 100.0
    assert mastery.attempt_count == 1
    assert mastery.correct_count == 1
    assert mastery.mastery_score == 0.65


@pytest.mark.asyncio
async def test_refresh_learning_alerts_creates_weak_alert_and_resolves_recovered_one():
    weak_mastery = make_mastery(knowledge_unit_id=101, mastery_score=0.2)
    weak_unit = make_knowledge_unit(knowledge_unit_id=101, name="Loops")
    stale_alert = LearningAlert(
        student_id=11,
        course_id=3,
        alert_type="knowledge_weak",
        severity="medium",
        message="old",
        details={"knowledge_unit_id": 999, "knowledge_unit_name": "Old"},
        is_resolved=False,
    )
    stale_alert.id = 7

    db = FakeDB(
        results=[
            FakeResult(rows=[(weak_mastery, weak_unit)]),
            FakeResult(scalars=[stale_alert]),
            FakeResult(scalar=None),
        ]
    )

    created = await analytics_engine.refresh_learning_alerts(db, course_id=3, student_id=11)

    new_alert = next(item for item in db.added if isinstance(item, LearningAlert))
    assert created == 1
    assert stale_alert.is_resolved is True
    assert new_alert.severity == "high"
    assert new_alert.details["knowledge_unit_id"] == 101


@pytest.mark.asyncio
async def test_generate_targeted_exercises_uses_weak_points_metadata(monkeypatch):
    exercise = make_pool_exercise(kp_ids=[101])
    db = FakeDB(results=[FakeResult(scalars=[exercise])])

    async def fake_knowledge_context(*args, **kwargs):
        return [
            {
                "id": 101,
                "name": "Loops",
                "description": "desc",
                "difficulty": 2,
                "mastery_score": 0.18,
                "attempt_count": 3,
                "correct_count": 0,
            }
        ]

    monkeypatch.setattr(exercise_engine, "_get_knowledge_context", fake_knowledge_context)

    result = await exercise_engine.generate_targeted_exercises(
        db,
        student_id=11,
        course_id=3,
        knowledge_point_ids=[],
        exercise_type=ExerciseType.CHOICE,
        difficulty=2,
        count=1,
        use_llm=False,
    )

    assert result["source"] == "pool"
    assert result["generation_method"] == "pool_recommendation"
    assert result["target_knowledge_points"][0]["knowledge_unit_id"] == 101
    assert result["target_knowledge_points"][0]["mastery_score"] == 0.18
    assert result["exercises"][0]["knowledge_point_ids"] == [101]


@pytest.mark.asyncio
async def test_submit_attempt_returns_alert_refresh_metadata(monkeypatch):
    attempt = SimpleNamespace(
        id=5,
        exercise_id=99,
        generated_exercise_id=None,
        is_correct=False,
        score=0.0,
        feedback="retry",
    )
    exercise = make_pool_exercise()
    db = FakeDB(
        results=[
            FakeResult(scalar=exercise),
            FakeResult(scalar=SimpleNamespace(id=3, teacher_id=7)),
            FakeResult(scalar=123),
            FakeResult(scalar=exercise),
        ]
    )

    monkeypatch.setattr(exercises, "create_attempt_and_update_mastery", AsyncMock(return_value=attempt))
    monkeypatch.setattr(exercises, "refresh_learning_alerts", AsyncMock(return_value=2))

    result = await exercises.submit_attempt(
        data=exercises.ExerciseAttemptRequest(exercise_id=99, student_answer="B"),
        db=db,
        user=make_user(),
    )

    assert result["mastery_updated"] is True
    assert result["alerts_refreshed"] == 2
    assert result["course_id"] == 3


@pytest.mark.asyncio
async def test_generated_attempt_skips_missing_knowledge_points():
    exercise = make_generated_exercise()
    db = FakeDB(
        results=[
            FakeResult(scalar=exercise),
            FakeResult(scalars=[101]),
            FakeResult(scalar=None),
        ]
    )

    attempt = await exercise_engine.create_attempt_and_update_mastery(
        db,
        student_id=11,
        exercise_id=None,
        generated_exercise_id=exercise.id,
        student_answer="A",
    )

    mastery_rows = [item for item in db.added if isinstance(item, StudentKnowledgeMastery)]

    assert attempt.is_correct is True
    assert len(mastery_rows) == 1
    assert mastery_rows[0].knowledge_unit_id == 101


@pytest.mark.asyncio
async def test_generate_targeted_exercises_prefers_course_agent_llm_config(monkeypatch):
    db = FakeDB(
        results=[
            FakeResult(scalar=SimpleNamespace(name="Data Structure", domain="cs")),
            FakeResult(scalars=[]),
            FakeResult(
                scalar=SimpleNamespace(
                    llm_provider="zhipu",
                    llm_model="",
                    system_prompt="course exercise prompt",
                )
            ),
        ]
    )
    captured: dict = {}

    class FakeProvider:
        async def chat(self, messages, temperature=0.3):
            captured["messages"] = messages
            captured["temperature"] = temperature
            return "ignored"

    async def fake_knowledge_context(*args, **kwargs):
        return [
            {
                "id": 101,
                "name": "Loops",
                "description": "desc",
                "difficulty": 2,
                "mastery_score": 0.18,
                "attempt_count": 3,
                "correct_count": 0,
            }
        ]

    monkeypatch.setattr(exercise_engine, "_get_knowledge_context", fake_knowledge_context)
    monkeypatch.setattr(
        exercise_engine,
        "get_llm_provider",
        lambda provider, model: captured.update({"provider": provider, "model": model}) or FakeProvider(),
    )
    monkeypatch.setattr(
        exercise_engine,
        "_safe_json_loads",
        lambda raw: {
            "exercises": [
                {
                    "question": "Generated question",
                    "options": [{"key": "A", "label": "Right"}, {"key": "B", "label": "Wrong"}],
                    "answer": "A",
                    "explanation": "Because A is correct.",
                    "knowledge_point_ids": [101],
                    "difficulty": 2,
                }
            ]
        },
    )

    result = await exercise_engine.generate_targeted_exercises(
        db,
        student_id=11,
        course_id=3,
        knowledge_point_ids=[],
        exercise_type=ExerciseType.CHOICE,
        difficulty=2,
        count=1,
        use_llm=True,
    )

    assert captured["provider"] == "zhipu"
    assert captured["model"] == "glm-4"
    assert "course exercise prompt" in captured["messages"][0]["content"]
    assert result["source"] == "generated"
    assert result["generation_method"] == "llm"


@pytest.mark.asyncio
async def test_learning_loop_smoke_from_attempt_to_alert_to_next_exercise(monkeypatch):
    attempt_exercise = make_pool_exercise(kp_ids=[301])
    attempt_exercise.id = 51
    attempt_exercise.answer = "B"
    attempt_exercise.explanation = "B is correct."

    attempt_db = FakeDB(
        results=[
            FakeResult(scalar=attempt_exercise),
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
            FakeResult(rows=[(mastery, make_knowledge_unit(knowledge_unit_id=301, name="Functions"))]),
            FakeResult(scalars=[]),
            FakeResult(scalar=None),
        ]
    )
    created_alerts = await analytics_engine.refresh_learning_alerts(alert_db, course_id=3, student_id=21)

    next_exercise = make_pool_exercise(kp_ids=[301])
    next_exercise.id = 52
    next_exercise.answer = "B"
    next_exercise.explanation = "B is correct."
    next_exercise_db = FakeDB(results=[FakeResult(scalars=[next_exercise])])

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
