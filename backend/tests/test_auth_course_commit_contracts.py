from types import SimpleNamespace

import pytest

from api.routes import auth, courses
from models.user import UserRole


class FakeResult:
    def __init__(self, scalar=None):
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar


class FakeDB:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.added = []
        self.deleted = []
        self.flushed = False
        self.committed = False
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

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)


def make_teacher(user_id: int = 7):
    return SimpleNamespace(id=user_id, role=UserRole.TEACHER)


def make_student(user_id: int = 21):
    return SimpleNamespace(id=user_id, role=UserRole.STUDENT)


@pytest.mark.asyncio
async def test_register_commits_before_returning():
    db = FakeDB(results=[FakeResult(scalar=None)])
    payload = auth.UserRegister(
        username="commit_user",
        email="commit_user@test.com",
        password="password123",
        full_name="Commit User",
        role=UserRole.STUDENT,
    )

    result = await auth.register(data=payload, db=db)

    assert db.flushed is True
    assert db.committed is True
    assert db.refreshed
    assert result.username == "commit_user"


@pytest.mark.asyncio
async def test_create_course_commits_before_returning():
    db = FakeDB()
    payload = courses.CourseCreate(
        name="Integration Course",
        code="INT-101",
        description="integration",
        domain="testing",
    )

    result = await courses.create_course(data=payload, db=db, user=make_teacher())

    assert db.flushed is True
    assert db.committed is True
    assert db.refreshed
    assert result.name == "Integration Course"


@pytest.mark.asyncio
async def test_enroll_course_commits_before_returning(monkeypatch):
    db = FakeDB(results=[FakeResult(scalar=None), FakeResult(scalar=None)])
    
    async def fake_get_course_or_404(*args, **kwargs):
        return SimpleNamespace(id=9)
    
    monkeypatch.setattr(courses, "get_course_or_404", fake_get_course_or_404)

    result = await courses.enroll_course(course_id=9, db=db, user=make_student())

    assert db.flushed is True
    assert db.committed is True
    assert result == {"message": "enrolled"}


@pytest.mark.asyncio
async def test_unenroll_course_commits_before_returning(monkeypatch):
    enrollment = SimpleNamespace(student_id=21, course_id=9)
    db = FakeDB(results=[FakeResult(scalar=enrollment)])
    
    async def fake_get_course_or_404(*args, **kwargs):
        return SimpleNamespace(id=9)
    
    monkeypatch.setattr(courses, "get_course_or_404", fake_get_course_or_404)

    result = await courses.unenroll_course(course_id=9, db=db, user=make_student())

    assert db.deleted == [enrollment]
    assert db.flushed is True
    assert db.committed is True
    assert result == {"message": "unenrolled"}
