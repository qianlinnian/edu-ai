from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from core.storage import upload_bytes
from models.course import Course, CourseResource, Enrollment, KnowledgeUnit
from models.user import User
from workers.embedding_task import process_resource

router = APIRouter()


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
    course_id: int
    name: str
    file_type: str
    file_size: int
    chunk_count: int
    is_processed: bool
    processing_status: str
    processing_error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=CourseResponse)
async def create_course(data: CourseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    course = Course(**data.model_dump(), teacher_id=user.id)
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


@router.get("", response_model=list[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Course).order_by(Course.created_at.desc()))
    return result.scalars().all()


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


@router.post("/{course_id}/enroll")
async def enroll_course(course_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    enrollment = Enrollment(student_id=user.id, course_id=course_id)
    db.add(enrollment)
    await db.flush()
    return {"message": "选课成功"}


@router.post("/{course_id}/knowledge-units", response_model=KnowledgeUnitResponse)
async def create_knowledge_unit(
    course_id: int,
    data: KnowledgeUnitCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ku = KnowledgeUnit(**data.model_dump(), course_id=course_id)
    db.add(ku)
    await db.flush()
    await db.refresh(ku)
    return ku


@router.get("/{course_id}/knowledge-units", response_model=list[KnowledgeUnitResponse])
async def list_knowledge_units(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeUnit).where(KnowledgeUnit.course_id == course_id).order_by(KnowledgeUnit.order_index)
    )
    return result.scalars().all()


@router.get("/{course_id}/resources", response_model=list[CourseResourceResponse])
async def list_resources(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    result = await db.execute(
        select(CourseResource)
        .where(CourseResource.course_id == course_id)
        .order_by(CourseResource.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{course_id}/resources")
async def upload_resource(
    course_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

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

    return {"id": resource.id, "name": resource.name, "message": "上传成功，正在处理中"}
