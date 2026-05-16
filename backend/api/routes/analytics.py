from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from education.analytics_engine import class_report, refresh_learning_alerts, student_mastery_overview, weak_points
from models.course import Course
from models.learning import LearningAlert
from models.user import User, UserRole

router = APIRouter()


async def _get_course_or_404(db: AsyncSession, course_id: int) -> Course:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _ensure_course_teacher_or_admin(*, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Teacher or admin access required")


def _ensure_student_or_teacher_access(*, course: Course, student_id: int, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    if user.role == UserRole.STUDENT and user.id == student_id:
        return
    raise HTTPException(status_code=403, detail="Not allowed to access this student analytics")


@router.get("/student/{student_id}/mastery")
async def get_student_mastery(
    student_id: int,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_student_or_teacher_access(course=course, student_id=student_id, user=user)
    return await student_mastery_overview(db, student_id=student_id, course_id=course_id)


@router.get("/student/{student_id}/weak-points")
async def get_weak_points(
    student_id: int,
    course_id: int,
    threshold: float = 0.4,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_student_or_teacher_access(course=course, student_id=student_id, user=user)
    return await weak_points(db, student_id=student_id, course_id=course_id, threshold=threshold)


@router.get("/course/{course_id}/class-report")
async def get_class_report(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_course_teacher_or_admin(course=course, user=user)
    return await class_report(db, course_id=course_id)


@router.post("/course/{course_id}/refresh-alerts")
async def refresh_alerts(
    course_id: int,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    course = await _get_course_or_404(db, course_id)
    _ensure_course_teacher_or_admin(course=course, user=user)
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
    elif user.role == UserRole.TEACHER:
        if course_id is None:
            raise HTTPException(status_code=400, detail="course_id is required for teacher alert queries")
        course = await _get_course_or_404(db, course_id)
        _ensure_course_teacher_or_admin(course=course, user=user)
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
