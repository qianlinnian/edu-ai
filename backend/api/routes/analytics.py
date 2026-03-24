from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.learning import StudentKnowledgeMastery, LearningAlert
from models.course import KnowledgeUnit

router = APIRouter()


@router.get("/student/{student_id}/mastery")
async def get_student_mastery(student_id: int, course_id: int, db: AsyncSession = Depends(get_db)):
    """获取学生在某课程的知识点掌握情况"""
    result = await db.execute(
        select(StudentKnowledgeMastery, KnowledgeUnit)
        .join(KnowledgeUnit, StudentKnowledgeMastery.knowledge_unit_id == KnowledgeUnit.id)
        .where(
            StudentKnowledgeMastery.student_id == student_id,
            KnowledgeUnit.course_id == course_id,
        )
    )
    rows = result.all()
    return [
        {
            "knowledge_unit": {"id": ku.id, "name": ku.name, "difficulty": ku.difficulty},
            "mastery_score": m.mastery_score,
            "attempt_count": m.attempt_count,
            "correct_count": m.correct_count,
        }
        for m, ku in rows
    ]


@router.get("/student/{student_id}/weak-points")
async def get_weak_points(student_id: int, course_id: int, threshold: float = 0.4, db: AsyncSession = Depends(get_db)):
    """获取学生的薄弱知识点"""
    result = await db.execute(
        select(StudentKnowledgeMastery, KnowledgeUnit)
        .join(KnowledgeUnit, StudentKnowledgeMastery.knowledge_unit_id == KnowledgeUnit.id)
        .where(
            StudentKnowledgeMastery.student_id == student_id,
            KnowledgeUnit.course_id == course_id,
            StudentKnowledgeMastery.mastery_score < threshold,
        )
        .order_by(StudentKnowledgeMastery.mastery_score)
    )
    rows = result.all()
    return [
        {"knowledge_unit_id": ku.id, "name": ku.name, "mastery_score": m.mastery_score}
        for m, ku in rows
    ]


@router.get("/course/{course_id}/class-report")
async def get_class_report(course_id: int, db: AsyncSession = Depends(get_db)):
    """班级整体学情报告"""
    # 每个知识点的平均掌握度
    result = await db.execute(
        select(
            KnowledgeUnit.id,
            KnowledgeUnit.name,
            func.avg(StudentKnowledgeMastery.mastery_score).label("avg_mastery"),
            func.count(StudentKnowledgeMastery.id).label("student_count"),
        )
        .join(KnowledgeUnit, StudentKnowledgeMastery.knowledge_unit_id == KnowledgeUnit.id)
        .where(KnowledgeUnit.course_id == course_id)
        .group_by(KnowledgeUnit.id, KnowledgeUnit.name)
        .order_by(func.avg(StudentKnowledgeMastery.mastery_score))
    )
    rows = result.all()
    return [
        {
            "knowledge_unit_id": row.id,
            "name": row.name,
            "avg_mastery": round(float(row.avg_mastery), 3) if row.avg_mastery else 0,
            "student_count": row.student_count,
        }
        for row in rows
    ]


@router.get("/alerts")
async def get_alerts(
    course_id: int | None = None,
    student_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取学情预警列表"""
    query = select(LearningAlert).where(LearningAlert.is_resolved == False)
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
            "created_at": str(a.created_at),
        }
        for a in alerts
    ]
