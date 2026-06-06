from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import analytics, exercises
from core.database import get_db
from core.security import get_current_user
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
        self.execute_calls = []

    async def execute(self, statement):
        self.execute_calls.append(statement)
        if self.results:
            return self.results.pop(0)
        return FakeResult()


def make_app(*, db, user=...):
    app = FastAPI()
    app.include_router(exercises.router, prefix="/api/v1/exercises")
    app.include_router(analytics.router, prefix="/api/v1/analytics")

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    if user is not ...:
        app.dependency_overrides[get_current_user] = lambda: user
    return app


def make_user(*, user_id: int, role: UserRole):
    return SimpleNamespace(id=user_id, role=role)


def make_course(*, course_id: int = 1, teacher_id: int = 7):
    return SimpleNamespace(id=course_id, teacher_id=teacher_id)


def make_pool_exercise(*, exercise_id: int = 5, course_id: int = 1):
    return SimpleNamespace(id=exercise_id, course_id=course_id)


def make_generated_exercise(*, exercise_id: int = 9, course_id: int = 1, student_id: int = 42):
    return SimpleNamespace(id=exercise_id, course_id=course_id, student_id=student_id)


def make_alert(*, alert_id: int, student_id: int, course_id: int):
    return SimpleNamespace(
        id=alert_id,
        student_id=student_id,
        course_id=course_id,
        alert_type="knowledge_weak",
        severity="high",
        message="Weak mastery detected",
        details={"source": "unit-test"},
        created_at=datetime(2026, 6, 5, tzinfo=timezone.utc),
    )


def test_exercise_pool_requires_authentication():
    client = TestClient(make_app(db=FakeDB()))

    response = client.get("/api/v1/exercises/pool", params={"course_id": 1})

    assert response.status_code == 401


def test_exercise_pool_rejects_teacher_outside_course():
    db = FakeDB(results=[FakeResult(scalar=make_course(course_id=1, teacher_id=99))])
    client = TestClient(make_app(db=db, user=make_user(user_id=7, role=UserRole.TEACHER)))

    response = client.get("/api/v1/exercises/pool", params={"course_id": 1})

    assert response.status_code == 403


def test_exercise_pool_rejects_unenrolled_student():
    db = FakeDB(
        results=[
            FakeResult(scalar=make_course(course_id=1, teacher_id=7)),
            FakeResult(scalar=None),
        ]
    )
    client = TestClient(make_app(db=db, user=make_user(user_id=42, role=UserRole.STUDENT)))

    response = client.get("/api/v1/exercises/pool", params={"course_id": 1})

    assert response.status_code == 403


def test_exercise_pool_returns_pool_for_enrolled_student():
    db = FakeDB(
        results=[
            FakeResult(scalar=make_course(course_id=1, teacher_id=7)),
            FakeResult(scalar=123),
            FakeResult(
                scalars=[
                    {
                        "id": 5,
                        "course_id": 1,
                        "question": "What is a binary tree?",
                        "created_at": datetime(2026, 6, 5, tzinfo=timezone.utc),
                    }
                ]
            ),
        ]
    )
    client = TestClient(make_app(db=db, user=make_user(user_id=42, role=UserRole.STUDENT)))

    response = client.get("/api/v1/exercises/pool", params={"course_id": 1})

    assert response.status_code == 200
    assert response.json()[0]["id"] == 5


def test_exercise_attempt_rejects_teacher():
    client = TestClient(make_app(db=FakeDB(), user=make_user(user_id=7, role=UserRole.TEACHER)))

    response = client.post("/api/v1/exercises/attempt", json={"exercise_id": 5, "student_answer": "A"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Only students can submit exercise attempts"


def test_exercise_attempt_rejects_unenrolled_student():
    db = FakeDB(
        results=[
            FakeResult(scalar=make_pool_exercise(exercise_id=5, course_id=1)),
            FakeResult(scalar=make_course(course_id=1, teacher_id=7)),
            FakeResult(scalar=None),
        ]
    )
    client = TestClient(make_app(db=db, user=make_user(user_id=42, role=UserRole.STUDENT)))

    response = client.post("/api/v1/exercises/attempt", json={"exercise_id": 5, "student_answer": "A"})

    assert response.status_code == 403


def test_exercise_attempt_rejects_foreign_generated_exercise():
    db = FakeDB(
        results=[
            FakeResult(scalar=make_generated_exercise(exercise_id=9, course_id=1, student_id=999)),
        ]
    )
    client = TestClient(make_app(db=db, user=make_user(user_id=42, role=UserRole.STUDENT)))

    response = client.post("/api/v1/exercises/attempt", json={"generated_exercise_id": 9, "student_answer": "A"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed to submit attempts for another student's exercise"


def test_alerts_teacher_requires_course_id():
    client = TestClient(make_app(db=FakeDB(), user=make_user(user_id=7, role=UserRole.TEACHER)))

    response = client.get("/api/v1/analytics/alerts")

    assert response.status_code == 400
    assert response.json()["detail"] == "course_id is required for teacher alert queries"


def test_alerts_teacher_supports_course_and_student_filter():
    db = FakeDB(
        results=[
            FakeResult(scalar=make_course(course_id=3, teacher_id=7)),
            FakeResult(scalars=[make_alert(alert_id=1, student_id=11, course_id=3)]),
        ]
    )
    client = TestClient(make_app(db=db, user=make_user(user_id=7, role=UserRole.TEACHER)))

    response = client.get("/api/v1/analytics/alerts", params={"course_id": 3, "student_id": 11})

    assert response.status_code == 200
    assert response.json()[0]["student_id"] == 11
    compiled = db.execute_calls[-1].compile()
    assert compiled.params["course_id_1"] == 3
    assert compiled.params["student_id_1"] == 11


def test_alerts_student_forces_own_student_id_and_checks_course_access():
    db = FakeDB(
        results=[
            FakeResult(scalar=make_course(course_id=5, teacher_id=7)),
            FakeResult(scalar=321),
            FakeResult(scalars=[make_alert(alert_id=2, student_id=42, course_id=5)]),
        ]
    )
    client = TestClient(make_app(db=db, user=make_user(user_id=42, role=UserRole.STUDENT)))

    response = client.get("/api/v1/analytics/alerts", params={"course_id": 5, "student_id": 999})

    assert response.status_code == 200
    assert response.json()[0]["student_id"] == 42
    compiled = db.execute_calls[-1].compile()
    assert compiled.params["course_id_1"] == 5
    assert compiled.params["student_id_1"] == 42


def test_alerts_student_rejects_unenrolled_course():
    db = FakeDB(
        results=[
            FakeResult(scalar=make_course(course_id=5, teacher_id=7)),
            FakeResult(scalar=None),
        ]
    )
    client = TestClient(make_app(db=db, user=make_user(user_id=42, role=UserRole.STUDENT)))

    response = client.get("/api/v1/analytics/alerts", params={"course_id": 5})

    assert response.status_code == 403
