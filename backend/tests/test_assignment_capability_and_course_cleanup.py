from types import SimpleNamespace

import pytest

from api.routes import assignments, courses
from core.agent_capability import CourseAgentCapability
from models.assignment import Submission, SubmissionStatus
from models.user import UserRole


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
        self.executed = []
        self.rolled_back = False

    def add(self, obj):
        self.added.append(obj)

    async def execute(self, statement):
        self.executed.append(statement)
        if self.results:
            return self.results.pop(0)
        return FakeResult()

    async def flush(self):
        for index, obj in enumerate(self.added, start=1):
            if getattr(obj, "id", None) is None:
                obj.id = index

    async def commit(self):
        return None

    async def refresh(self, obj):
        if isinstance(obj, Submission) and getattr(obj, "status", None) is None:
            obj.status = SubmissionStatus.PENDING
        return None

    async def rollback(self):
        self.rolled_back = True


def make_student(user_id: int = 42):
    return SimpleNamespace(id=user_id, role=UserRole.STUDENT)


def make_teacher(user_id: int = 7):
    return SimpleNamespace(id=user_id, role=UserRole.TEACHER)


def make_assignment(*, assignment_id: int = 5, course_id: int = 3):
    return SimpleNamespace(id=assignment_id, course_id=course_id)


def make_course(*, course_id: int = 3, teacher_id: int = 7):
    return SimpleNamespace(id=course_id, teacher_id=teacher_id)


def make_capability(*, course_id: int, has_grading: bool):
    return CourseAgentCapability(
        course_id=course_id,
        agent_id=1,
        workflow_id=2,
        enabled_node_types=("input_node", "llm_node", "output_node"),
        can_chat=True,
        has_rag=False,
        has_grading=has_grading,
        has_analytics=False,
        has_exercise=False,
    )


@pytest.mark.asyncio
async def test_submit_assignment_skips_grading_when_capability_disabled(monkeypatch):
    db = FakeDB()
    assignment = make_assignment()
    course = make_course(course_id=assignment.course_id)

    async def fake_get_assignment_course(db, assignment_id):
        return assignment, course

    async def fake_ensure_course_access(db, *, course, user):
        return None

    async def fake_capability(db, *, course_id: int):
        return make_capability(course_id=course_id, has_grading=False)

    queued = {"called": False}

    class FakeGradeTask:
        @staticmethod
        def apply_async(*args, **kwargs):
            queued["called"] = True

    monkeypatch.setattr(assignments, "_get_course_for_assignment", fake_get_assignment_course)
    monkeypatch.setattr(assignments, "ensure_course_access", fake_ensure_course_access)
    monkeypatch.setattr(assignments, "get_published_course_agent_capability", fake_capability)
    monkeypatch.setattr(assignments, "grade_submission", FakeGradeTask)

    result = await assignments.submit_assignment(
        assignment_id=assignment.id,
        content="answer",
        file=None,
        db=db,
        user=make_student(),
    )

    assert result["grading_enabled"] is False
    assert result["status"] == SubmissionStatus.SUBMITTED.value
    assert result["message"] == "Submission accepted; AI grading is disabled for this course"
    assert queued["called"] is False
    assert isinstance(db.added[0], Submission)
    assert db.added[0].status == SubmissionStatus.SUBMITTED


@pytest.mark.asyncio
async def test_submit_assignment_queues_grading_when_capability_enabled(monkeypatch):
    db = FakeDB()
    assignment = make_assignment()
    course = make_course(course_id=assignment.course_id)

    async def fake_get_assignment_course(db, assignment_id):
        return assignment, course

    async def fake_ensure_course_access(db, *, course, user):
        return None

    async def fake_capability(db, *, course_id: int):
        return make_capability(course_id=course_id, has_grading=True)

    queued = {"called": False, "submission_id": None}

    class FakeGradeTask:
        @staticmethod
        def apply_async(*, args, countdown):
            queued["called"] = True
            queued["submission_id"] = args[0]

    monkeypatch.setattr(assignments, "_get_course_for_assignment", fake_get_assignment_course)
    monkeypatch.setattr(assignments, "ensure_course_access", fake_ensure_course_access)
    monkeypatch.setattr(assignments, "get_published_course_agent_capability", fake_capability)
    monkeypatch.setattr(assignments, "grade_submission", FakeGradeTask)

    result = await assignments.submit_assignment(
        assignment_id=assignment.id,
        content="answer",
        file=None,
        db=db,
        user=make_student(),
    )

    assert result["grading_enabled"] is True
    assert result["status"] == SubmissionStatus.PENDING.value
    assert result["message"] == "Submission accepted and grading queued"
    assert queued["called"] is True
    assert queued["submission_id"] == db.added[0].id
    assert db.added[0].status == SubmissionStatus.PENDING


@pytest.mark.asyncio
async def test_delete_course_removes_chat_records_before_agents(monkeypatch):
    db = FakeDB(
        results=[
            FakeResult(scalar=make_course(course_id=3, teacher_id=7)),
            FakeResult(scalars=[]),    # resources
            FakeResult(scalars=[]),    # assignment ids
            FakeResult(scalars=[]),    # pool ids
            FakeResult(scalars=[]),    # generated ids
            FakeResult(scalars=[]),    # knowledge ids
            FakeResult(scalars=[91]),  # agent ids
            FakeResult(scalars=[201]), # session ids
        ]
    )

    async def fake_get_course(db, course_id):
        return make_course(course_id=course_id, teacher_id=7)

    monkeypatch.setattr(courses, "_get_course_or_404", fake_get_course)
    monkeypatch.setattr(courses, "ensure_course_manager", lambda *, course, user: None)
    monkeypatch.setattr(courses, "remove_object", lambda object_name: None)

    result = await courses.delete_course(course_id=3, db=db, user=make_teacher())

    sql = [str(statement) for statement in db.executed]
    chat_message_index = next(i for i, item in enumerate(sql) if "DELETE FROM chat_messages" in item)
    chat_session_index = next(i for i, item in enumerate(sql) if "DELETE FROM chat_sessions" in item)
    agent_index = next(i for i, item in enumerate(sql) if "DELETE FROM agent_instances" in item)

    assert chat_message_index < chat_session_index < agent_index
    assert result["message"] == "deleted"


@pytest.mark.asyncio
async def test_enqueue_submission_grading_requeues_submitted_submission(monkeypatch):
    db = FakeDB()
    assignment = make_assignment()
    course = make_course(course_id=assignment.course_id, teacher_id=7)
    submission = Submission(
        id=33,
        assignment_id=assignment.id,
        student_id=42,
        content="answer",
        status=SubmissionStatus.SUBMITTED,
    )

    async def fake_get_submission_context(db, submission_id):
        return submission, assignment, course

    async def fake_capability(db, *, course_id: int):
        return make_capability(course_id=course_id, has_grading=True)

    queued = {"called": False, "submission_id": None}

    class FakeGradeTask:
        @staticmethod
        def apply_async(*, args, countdown):
            queued["called"] = True
            queued["submission_id"] = args[0]

    monkeypatch.setattr(assignments, "_get_submission_context", fake_get_submission_context)
    monkeypatch.setattr(assignments, "get_published_course_agent_capability", fake_capability)
    monkeypatch.setattr(assignments, "grade_submission", FakeGradeTask)

    result = await assignments.enqueue_submission_grading(
        submission_id=submission.id,
        db=db,
        user=make_teacher(),
    )

    assert result["status"] == SubmissionStatus.PENDING.value
    assert submission.status == SubmissionStatus.PENDING
    assert queued["called"] is True
    assert queued["submission_id"] == submission.id
