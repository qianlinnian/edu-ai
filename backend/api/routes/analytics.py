from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from education.analytics_engine import class_report, refresh_learning_alerts, student_mastery_overview, weak_points
from models.learning import LearningAlert

router = APIRouter()


@router.get("/student/{student_id}/mastery")
async def get_student_mastery(student_id: int, course_id: int, db: AsyncSession = Depends(get_db)):
    """Get student mastery details under one course."""
    return await student_mastery_overview(db, student_id=student_id, course_id=course_id)


@router.get("/student/{student_id}/weak-points")
async def get_weak_points(student_id: int, course_id: int, threshold: float = 0.4, db: AsyncSession = Depends(get_db)):
    """Get student weak knowledge units."""
    return await weak_points(db, student_id=student_id, course_id=course_id, threshold=threshold)


@router.get("/course/{course_id}/class-report")
async def get_class_report(course_id: int, db: AsyncSession = Depends(get_db)):
    """Get aggregated class learning report."""
    return await class_report(db, course_id=course_id)


@router.post("/course/{course_id}/refresh-alerts")
async def refresh_alerts(course_id: int, student_id: int | None = None, db: AsyncSession = Depends(get_db)):
    """Recompute alerts from current mastery data."""
    created = await refresh_learning_alerts(db, course_id=course_id, student_id=student_id)
    return {"created": created, "course_id": course_id, "student_id": student_id}


@router.get("/alerts")
async def get_alerts(
    course_id: int | None = None,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List unresolved learning alerts."""
    query = select(LearningAlert).where(LearningAlert.is_resolved.is_(False))
    if course_id:
        query = query.where(LearningAlert.course_id == course_id)
    if student_id:
        query = query.where(LearningAlert.student_id == student_id)

    result = await db.execute(query.order_by(LearningAlert.created_at.desc()))
    alerts = result.scalars().all()
    return [
        {
            "id": a.id,
            "student_id": a.student_id,
            "course_id": a.course_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "details": a.details,
            "created_at": str(a.created_at),
        }
        for a in alerts
    ]
