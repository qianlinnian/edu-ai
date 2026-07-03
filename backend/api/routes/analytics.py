from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.agent_capability import get_published_course_agent_capability
from core.course_helpers import get_course_or_404
from core.database import get_db
from core.permissions import ensure_course_access, ensure_course_manager, ensure_student_or_teacher_access
from core.security import get_current_user
from education.analytics_engine import class_report, refresh_learning_alerts, student_mastery_overview, weak_points
from models.learning import LearningAlert
from models.user import User, UserRole

router = APIRouter()

async def _ensure_analytics_capability(db: AsyncSession, *, course_id: int) -> None:
    capability = await get_published_course_agent_capability(db, course_id=course_id)
    if not capability.has_analytics:
        raise HTTPException(status_code=409, detail="Current course has not published analytics capability")


@router.get("/student/{student_id}/mastery")
async def get_student_mastery(
    student_id: int,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await get_course_or_404(db, course_id)
    await ensure_student_or_teacher_access(db, course=course, student_id=student_id, user=user)
    await _ensure_analytics_capability(db, course_id=course_id)
    return await student_mastery_overview(db, student_id=student_id, course_id=course_id)


@router.get("/student/{student_id}/weak-points")
async def get_weak_points(
    student_id: int,
    course_id: int,
    threshold: float = 0.4,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await get_course_or_404(db, course_id)
    await ensure_student_or_teacher_access(db, course=course, student_id=student_id, user=user)
    await _ensure_analytics_capability(db, course_id=course_id)
    return await weak_points(db, student_id=student_id, course_id=course_id, threshold=threshold)


@router.get("/course/{course_id}/class-report")
async def get_class_report(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await get_course_or_404(db, course_id)
    ensure_course_manager(course=course, user=user)
    await _ensure_analytics_capability(db, course_id=course_id)
    return await class_report(db, course_id=course_id)


@router.post("/course/{course_id}/refresh-alerts")
async def refresh_alerts(
    course_id: int,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await get_course_or_404(db, course_id)
    ensure_course_manager(course=course, user=user)
    await _ensure_analytics_capability(db, course_id=course_id)
    created = await refresh_learning_alerts(db, course_id=course_id, student_id=student_id)
    return {"created": created, "course_id": course_id, "student_id": student_id}


@router.get("/alerts")
async def get_alerts(
    course_id: int | None = None,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.STUDENT:
        student_id = user.id
        if course_id is not None:
            course = await get_course_or_404(db, course_id)
            await ensure_course_access(db, course=course, user=user)
            await _ensure_analytics_capability(db, course_id=course_id)
    elif user.role == UserRole.TEACHER:
        if course_id is None:
            raise HTTPException(status_code=400, detail="course_id is required for teacher alert queries")
        course = await get_course_or_404(db, course_id)
        ensure_course_manager(course=course, user=user)
        await _ensure_analytics_capability(db, course_id=course_id)
    elif user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed to access alerts")

    query = select(LearningAlert).where(LearningAlert.is_resolved.is_(False))
    if course_id:
        query = query.where(LearningAlert.course_id == course_id)
    if student_id:
        query = query.where(LearningAlert.student_id == student_id)

    result = await db.execute(query.order_by(LearningAlert.created_at.desc()))
    alerts = result.scalars().all()
    return [
        {
            "id": alert.id,
            "student_id": alert.student_id,
            "course_id": alert.course_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "details": alert.details,
            "created_at": str(alert.created_at),
        }
        for alert in alerts
    ]
