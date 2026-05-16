from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from core.storage import remove_object, get_minio_client, upload_bytes
from models.agent import AgentInstance, AgentWorkflow
from models.assignment import Assignment, GradingResult, Submission, SubmissionAnnotation
from models.course import Course, CourseResource, Enrollment, KnowledgeRelation, KnowledgeUnit, ResourceChunk
from core.config import get_settings
from models.exercise import ExerciseAttempt, ExercisePool, GeneratedExercise
from models.learning import LearningAlert, StudentKnowledgeMastery
from models.user import User, UserRole
from workers.embedding_task import process_resource

router = APIRouter()
settings = get_settings()


class CourseCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    domain: str


class CourseResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None
    domain: str
    teacher_id: int

    model_config = {"from_attributes": True}


class KnowledgeUnitCreate(BaseModel):
    name: str
    description: str | None = None
    domain: str
    difficulty: int = 1
    tags: list[str] | None = None
    parent_id: int | None = None


class KnowledgeUnitResponse(BaseModel):
    id: int
    name: str
    description: str | None
    domain: str
    difficulty: int
    tags: dict | None
    course_id: int

    model_config = {"from_attributes": True}


class CourseResourceResponse(BaseModel):
    id: int
    name: str
    file_type: str
    file_size: int
    chunk_count: int
    processing_status: str
    processing_error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeGenerateResponse(BaseModel):
    created: int
    items: list[KnowledgeUnitResponse]


async def _get_course_or_404(db: AsyncSession, course_id: int) -> Course:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


async def _ensure_course_access(db: AsyncSession, *, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    if user.role == UserRole.STUDENT:
        result = await db.execute(
            select(Enrollment.id).where(Enrollment.course_id == course.id, Enrollment.student_id == user.id)
        )
        if result.scalar_one_or_none() is not None:
            return
    raise HTTPException(status_code=403, detail="Not allowed to access this course")


def _ensure_course_manager(*, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Teacher or admin access required")


def _knowledge_name_from_text(text: str, index: int) -> str:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return f"课程知识点 {index}"
    for prefix in ("一、", "二、", "三、", "四、", "五、", "1.", "2.", "3.", "#", "##"):
        normalized = normalized.removeprefix(prefix).strip()
    return normalized[:28] or f"课程知识点 {index}"


@router.post("", response_model=CourseResponse)
async def create_course(data: CourseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in {UserRole.TEACHER, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Teacher or admin access required")
    course = Course(**data.model_dump(), teacher_id=user.id)
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


@router.get("", response_model=list[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(Course).where(Course.is_active.is_(True))
    if user.role == UserRole.TEACHER:
        query = query.where(Course.teacher_id == user.id)
    elif user.role == UserRole.STUDENT:
        query = query.join(Enrollment, Enrollment.course_id == Course.id).where(Enrollment.student_id == user.id)
    result = await db.execute(query.order_by(Course.created_at.desc()))
    return result.scalars().all()


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    await _ensure_course_access(db, course=course, user=user)
    return course


@router.post("/{course_id}/enroll")
async def enroll_course(course_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can enroll in courses")
    await _get_course_or_404(db, course_id)
    existing = await db.execute(
        select(Enrollment).where(Enrollment.student_id == user.id, Enrollment.course_id == course_id)
    )
    if existing.scalar_one_or_none() is not None:
        return {"message": "already_enrolled"}
    enrollment = Enrollment(student_id=user.id, course_id=course_id)
    db.add(enrollment)
    await db.flush()
    return {"message": "enrolled"}


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_course_manager(course=course, user=user)
    course.name = data.name
    course.code = data.code
    course.description = data.description
    course.domain = data.domain
    await db.flush()
    await db.refresh(course)
    return course


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_course_manager(course=course, user=user)

    resources = (
        await db.execute(select(CourseResource).where(CourseResource.course_id == course_id))
    ).scalars().all()
    resource_ids = [resource.id for resource in resources]
    resource_paths = [resource.file_path for resource in resources]

    assignment_ids = (
        await db.execute(select(Assignment.id).where(Assignment.course_id == course_id))
    ).scalars().all()
    submission_ids: list[int] = []
    if assignment_ids:
        submission_ids = (
            await db.execute(select(Submission.id).where(Submission.assignment_id.in_(assignment_ids)))
        ).scalars().all()

    if submission_ids:
        await db.execute(delete(SubmissionAnnotation).where(SubmissionAnnotation.submission_id.in_(submission_ids)))
        await db.execute(delete(GradingResult).where(GradingResult.submission_id.in_(submission_ids)))
        await db.execute(delete(Submission).where(Submission.id.in_(submission_ids)))
    if assignment_ids:
        await db.execute(delete(Assignment).where(Assignment.id.in_(assignment_ids)))
    if resource_ids:
        await db.execute(delete(ResourceChunk).where(ResourceChunk.resource_id.in_(resource_ids)))
        await db.execute(delete(CourseResource).where(CourseResource.id.in_(resource_ids)))

    pool_ids = (
        await db.execute(select(ExercisePool.id).where(ExercisePool.course_id == course_id))
    ).scalars().all()
    generated_ids = (
        await db.execute(select(GeneratedExercise.id).where(GeneratedExercise.course_id == course_id))
    ).scalars().all()
    if pool_ids:
        await db.execute(delete(ExerciseAttempt).where(ExerciseAttempt.exercise_id.in_(pool_ids)))
        await db.execute(delete(ExercisePool).where(ExercisePool.id.in_(pool_ids)))
    if generated_ids:
        await db.execute(delete(ExerciseAttempt).where(ExerciseAttempt.generated_exercise_id.in_(generated_ids)))
        await db.execute(delete(GeneratedExercise).where(GeneratedExercise.id.in_(generated_ids)))

    knowledge_ids = (
        await db.execute(select(KnowledgeUnit.id).where(KnowledgeUnit.course_id == course_id))
    ).scalars().all()
    if knowledge_ids:
        await db.execute(delete(StudentKnowledgeMastery).where(StudentKnowledgeMastery.knowledge_unit_id.in_(knowledge_ids)))
        await db.execute(
            delete(KnowledgeRelation).where(
                KnowledgeRelation.source_id.in_(knowledge_ids) | KnowledgeRelation.target_id.in_(knowledge_ids)
            )
        )
        await db.execute(update(KnowledgeUnit).where(KnowledgeUnit.id.in_(knowledge_ids)).values(parent_id=None))
        await db.execute(delete(KnowledgeUnit).where(KnowledgeUnit.id.in_(knowledge_ids)))

    await db.execute(delete(LearningAlert).where(LearningAlert.course_id == course_id))
    agent_ids = (
        await db.execute(select(AgentInstance.id).where(AgentInstance.course_id == course_id))
    ).scalars().all()
    if agent_ids:
        await db.execute(delete(AgentWorkflow).where(AgentWorkflow.agent_id.in_(agent_ids)))
        await db.execute(delete(AgentInstance).where(AgentInstance.id.in_(agent_ids)))
    await db.execute(delete(Enrollment).where(Enrollment.course_id == course_id))
    await db.execute(delete(Course).where(Course.id == course_id))

    minio_deleted = 0
    for path in resource_paths:
        try:
            remove_object(object_name=path)
            minio_deleted += 1
        except Exception:
            pass

    await db.commit()
    return {"message": "deleted", "minio_deleted": minio_deleted}


@router.post("/{course_id}/knowledge-units", response_model=KnowledgeUnitResponse)
async def create_knowledge_unit(
    course_id: int,
    data: KnowledgeUnitCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_course_manager(course=course, user=user)
    payload = data.model_dump()
    tags = payload.pop("tags", None)
    ku = KnowledgeUnit(**payload, tags={"values": tags} if tags else None, course_id=course_id)
    db.add(ku)
    await db.flush()
    await db.refresh(ku)
    return ku


@router.get("/{course_id}/knowledge-units", response_model=list[KnowledgeUnitResponse])
async def list_knowledge_units(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    await _ensure_course_access(db, course=course, user=user)
    result = await db.execute(
        select(KnowledgeUnit).where(KnowledgeUnit.course_id == course_id).order_by(KnowledgeUnit.order_index)
    )
    return result.scalars().all()


@router.post("/{course_id}/knowledge-units/generate", response_model=KnowledgeGenerateResponse)
async def generate_knowledge_units(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_course_manager(course=course, user=user)

    existing_names = set(
        (
            await db.execute(select(KnowledgeUnit.name).where(KnowledgeUnit.course_id == course_id))
        ).scalars().all()
    )
    chunks = (
        await db.execute(
            select(ResourceChunk.content)
            .where(ResourceChunk.course_id == course_id)
            .order_by(ResourceChunk.id)
            .limit(5)
        )
    ).scalars().all()
    source_texts = chunks or [
        f"{course.name} 课程概览",
        f"{course.domain} 基础概念",
        f"{course.name} 重点知识与练习",
    ]

    created_items: list[KnowledgeUnit] = []
    for index, text in enumerate(source_texts, start=1):
        name = _knowledge_name_from_text(text, index)
        if name in existing_names:
            continue
        unit = KnowledgeUnit(
            course_id=course_id,
            name=name,
            description=text[:300],
            domain=course.domain,
            difficulty=min(max(index, 1), 5),
            tags={"source": "auto_generated"},
            order_index=len(existing_names) + len(created_items),
        )
        db.add(unit)
        created_items.append(unit)
        existing_names.add(name)

    await db.flush()
    for unit in created_items:
        await db.refresh(unit)

    return {"created": len(created_items), "items": created_items}


@router.get("/{course_id}/resources", response_model=list[CourseResourceResponse])
async def list_resources(course_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    course = await _get_course_or_404(db, course_id)
    await _ensure_course_access(db, course=course, user=user)

    result = await db.execute(
        select(CourseResource).where(CourseResource.course_id == course_id).order_by(CourseResource.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{course_id}/resources/{resource_id}/download")
async def download_resource(
    course_id: int,
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    await _ensure_course_access(db, course=course, user=user)
    resource_result = await db.execute(
        select(CourseResource).where(
            CourseResource.id == resource_id,
            CourseResource.course_id == course_id,
        )
    )
    resource = resource_result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    client = get_minio_client()
    response = None
    try:
        response = client.get_object(settings.MINIO_BUCKET, resource.file_path)
        payload = response.read()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to download resource: {exc}") from exc
    finally:
        if response is not None:
            try:
                response.close()
                response.release_conn()
            except Exception:
                pass

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(resource.name)}"
    }
    return StreamingResponse(iter([payload]), media_type="application/octet-stream", headers=headers)


@router.post("/{course_id}/resources")
async def upload_resource(
    course_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_course_manager(course=course, user=user)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    suffix = file.filename.split(".")[-1] if "." in file.filename else "unknown"
    object_name = f"courses/{course_id}/{uuid4().hex}_{file.filename}"

    try:
        upload_bytes(
            object_name=object_name,
            data=payload,
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to upload resource: {exc}") from exc

    resource = CourseResource(
        course_id=course_id,
        name=file.filename,
        file_type=suffix.lower(),
        file_path=object_name,
        file_size=len(payload),
        processing_status="pending",
    )
    db.add(resource)
    await db.flush()
    await db.refresh(resource)

    try:
        process_resource.apply_async(args=[resource.id], countdown=1)
    except Exception as exc:
        resource.processing_status = "failed"
        resource.processing_error = f"task dispatch failed: {exc}"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process resource: {exc}") from exc

    return {"id": resource.id, "name": resource.name, "message": "uploaded"}


@router.delete("/{course_id}/resources/{resource_id}")
async def delete_resource(
    course_id: int,
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_course_manager(course=course, user=user)
    resource_result = await db.execute(
        select(CourseResource).where(CourseResource.id == resource_id, CourseResource.course_id == course_id)
    )
    resource = resource_result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    await db.execute(delete(ResourceChunk).where(ResourceChunk.resource_id == resource.id))
    await db.execute(delete(CourseResource).where(CourseResource.id == resource.id))

    minio_deleted = False
    try:
        remove_object(object_name=resource.file_path)
        minio_deleted = True
    except Exception:
        minio_deleted = False

    await db.commit()
    return {"message": "deleted", "minio_deleted": minio_deleted}


@router.post("/{course_id}/resources/{resource_id}/retry")
async def retry_resource_processing(
    course_id: int,
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_course_manager(course=course, user=user)
    resource_result = await db.execute(
        select(CourseResource).where(CourseResource.id == resource_id, CourseResource.course_id == course_id)
    )
    resource = resource_result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource.processing_status == "processing":
        raise HTTPException(status_code=409, detail="Resource is processing")

    await db.execute(delete(ResourceChunk).where(ResourceChunk.resource_id == resource.id))
    resource.processing_status = "pending"
    resource.processing_error = None
    resource.chunk_count = 0
    resource.is_processed = False
    await db.commit()

    try:
        process_resource.apply_async(args=[resource.id], countdown=1)
    except Exception as exc:
        resource.processing_status = "failed"
        resource.processing_error = f"task dispatch failed: {exc}"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to retry resource processing: {exc}") from exc

    return {"message": "retry_queued", "id": resource.id, "name": resource.name}

