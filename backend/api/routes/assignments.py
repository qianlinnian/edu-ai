from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from core.storage import remove_object, upload_bytes
from models.assignment import Assignment, GradingResult, Submission, SubmissionAnnotation, SubmissionStatus
from models.course import Course, Enrollment
from models.user import User, UserRole
from workers.grading_task import grade_submission

router = APIRouter()


class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    description: str | None = None
    assignment_type: str = "text"
    max_score: float = 100.0
    rubric: dict | None = None
    reference_answer: str | None = None
    knowledge_points: list[int] | None = None


class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: str | None
    assignment_type: str
    max_score: float

    model_config = {"from_attributes": True}


class GradingResultResponse(BaseModel):
    id: int
    submission_id: int
    score: float
    max_score: float
    overall_comment: str | None
    strengths: list | None
    weaknesses: list | None
    knowledge_point_scores: dict | None

    model_config = {"from_attributes": True}


class AnnotationResponse(BaseModel):
    id: int
    annotation_type: str
    position: dict
    content: str
    severity: str
    knowledge_point_id: int | None

    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    content: str | None
    file_path: str | None
    status: SubmissionStatus
    submitted_at: datetime

    model_config = {"from_attributes": True}


async def _get_course_for_assignment(db: AsyncSession, assignment_id: int) -> tuple[Assignment, Course]:
    result = await db.execute(
        select(Assignment, Course).join(Course, Course.id == Assignment.course_id).where(Assignment.id == assignment_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return row


async def _get_submission_context(db: AsyncSession, submission_id: int) -> tuple[Submission, Assignment, Course]:
    result = await db.execute(
        select(Submission, Assignment, Course)
        .join(Assignment, Assignment.id == Submission.assignment_id)
        .join(Course, Course.id == Assignment.course_id)
        .where(Submission.id == submission_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return row


async def _ensure_course_access(db: AsyncSession, *, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    if user.role == UserRole.STUDENT:
        enrollment_result = await db.execute(
            select(Enrollment.id).where(Enrollment.course_id == course.id, Enrollment.student_id == user.id)
        )
        if enrollment_result.scalar_one_or_none() is not None:
            return
    raise HTTPException(status_code=403, detail="Not allowed to access this course")


def _ensure_teacher_or_admin_for_course(*, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Teacher or admin access required")


def _ensure_submission_access(*, submission: Submission, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    if user.role == UserRole.STUDENT and submission.student_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Not allowed to access this submission")


@router.post("", response_model=AssignmentResponse)
async def create_assignment(
    data: AssignmentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    if user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Teacher or admin access required")

    course_result = await db.execute(select(Course).where(Course.id == data.course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    _ensure_teacher_or_admin_for_course(course=course, user=user)

    assignment = Assignment(**data.model_dump(), created_by=user.id)
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.get("", response_model=list[AssignmentResponse])
async def list_assignments(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    await _ensure_course_access(db, course=course, user=user)

    result = await db.execute(
        select(Assignment).where(Assignment.course_id == course_id).order_by(Assignment.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    content: str = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not content and not file:
        raise HTTPException(status_code=400, detail="Submission content cannot be empty")

    assignment, course = await _get_course_for_assignment(db, assignment_id)
    await _ensure_course_access(db, course=course, user=user)
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit assignments")

    file_path = None
    if file:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Uploaded file name cannot be empty")
        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="Uploaded file cannot be empty")
        file_path = f"submissions/{assignment.id}/{user.id}/{uuid4().hex}_{file.filename}"
        try:
            upload_bytes(
                object_name=file_path,
                data=payload,
                content_type=file.content_type or "application/octet-stream",
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to upload submission file: {exc}") from exc

    submission = Submission(
        assignment_id=assignment.id,
        student_id=user.id,
        content=content,
        file_path=file_path,
    )

    try:
        db.add(submission)
        await db.flush()
        await db.commit()
        await db.refresh(submission)
    except Exception:
        await db.rollback()
        if file_path:
            try:
                remove_object(object_name=file_path)
            except Exception:
                pass
        raise

    grade_submission.apply_async(args=[submission.id], countdown=1)

    return {
        "id": submission.id,
        "status": submission.status.value,
        "message": "Submission accepted and grading queued",
    }


@router.get("/{assignment_id}/submissions", response_model=list[SubmissionResponse])
async def list_submissions(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    assignment, course = await _get_course_for_assignment(db, assignment_id)

    query = select(Submission).where(Submission.assignment_id == assignment.id)
    if user.role == UserRole.ADMIN or (user.role == UserRole.TEACHER and course.teacher_id == user.id):
        pass
    elif user.role == UserRole.STUDENT:
        query = query.where(Submission.student_id == user.id)
    else:
        raise HTTPException(status_code=403, detail="Not allowed to access this assignment")

    result = await db.execute(query.order_by(Submission.submitted_at.desc()))
    return result.scalars().all()


@router.get("/submissions/{submission_id}/result", response_model=GradingResultResponse)
async def get_grading_result(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    submission, _assignment, course = await _get_submission_context(db, submission_id)
    _ensure_submission_access(submission=submission, course=course, user=user)

    if submission.status == SubmissionStatus.FAILED:
        raise HTTPException(status_code=409, detail="Grading failed")
    if submission.status != SubmissionStatus.GRADED:
        raise HTTPException(status_code=404, detail="AI grading in progress")

    result = await db.execute(select(GradingResult).where(GradingResult.submission_id == submission_id))
    grading = result.scalar_one_or_none()
    if not grading:
        raise HTTPException(status_code=404, detail="Grading result not found")
    return grading


@router.get("/submissions/{submission_id}/annotations", response_model=list[AnnotationResponse])
async def get_annotations(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    submission, _assignment, course = await _get_submission_context(db, submission_id)
    _ensure_submission_access(submission=submission, course=course, user=user)

    if submission.status == SubmissionStatus.FAILED:
        raise HTTPException(status_code=409, detail="Grading failed")
    if submission.status != SubmissionStatus.GRADED:
        raise HTTPException(status_code=404, detail="AI grading in progress")

    result = await db.execute(
        select(SubmissionAnnotation)
        .where(SubmissionAnnotation.submission_id == submission_id)
        .order_by(SubmissionAnnotation.id)
    )
    return result.scalars().all()
