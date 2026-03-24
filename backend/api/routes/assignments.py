from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.assignment import Assignment, Submission, GradingResult, SubmissionAnnotation, SubmissionStatus

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

    model_config = {"from_attributes": True}


class AnnotationResponse(BaseModel):
    id: int
    annotation_type: str
    position: dict
    content: str
    severity: str
    knowledge_point_id: int | None

    model_config = {"from_attributes": True}


@router.post("", response_model=AssignmentResponse)
async def create_assignment(
    data: AssignmentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    assignment = Assignment(**data.model_dump(), created_by=user.id)
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.get("", response_model=list[AssignmentResponse])
async def list_assignments(course_id: int, db: AsyncSession = Depends(get_db)):
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
    file_path = None
    if file:
        # TODO: 上传到MinIO
        file_path = f"submissions/{assignment_id}/{user.id}/{file.filename}"

    submission = Submission(
        assignment_id=assignment_id,
        student_id=user.id,
        content=content,
        file_path=file_path,
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)

    # TODO: 触发异步批改任务
    # from workers.grading_task import grade_submission
    # grade_submission.delay(submission.id)

    return {"id": submission.id, "status": submission.status, "message": "提交成功，正在批改中"}


@router.get("/{assignment_id}/submissions")
async def list_submissions(assignment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Submission).where(Submission.assignment_id == assignment_id).order_by(Submission.submitted_at.desc())
    )
    return result.scalars().all()


@router.get("/submissions/{submission_id}/result", response_model=GradingResultResponse)
async def get_grading_result(submission_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GradingResult).where(GradingResult.submission_id == submission_id))
    grading = result.scalar_one_or_none()
    if not grading:
        raise HTTPException(status_code=404, detail="批改结果尚未生成")
    return grading


@router.get("/submissions/{submission_id}/annotations", response_model=list[AnnotationResponse])
async def get_annotations(submission_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SubmissionAnnotation)
        .where(SubmissionAnnotation.submission_id == submission_id)
        .order_by(SubmissionAnnotation.id)
    )
    return result.scalars().all()
