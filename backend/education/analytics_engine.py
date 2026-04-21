from __future__ import annotations

from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.course import KnowledgeUnit
from models.learning import LearningAlert, StudentKnowledgeMastery


async def student_mastery_overview(
    db: AsyncSession,
    *,
    student_id: int,
    course_id: int,
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(StudentKnowledgeMastery, KnowledgeUnit)
        .join(KnowledgeUnit, StudentKnowledgeMastery.knowledge_unit_id == KnowledgeUnit.id)
        .where(
            StudentKnowledgeMastery.student_id == student_id,
            KnowledgeUnit.course_id == course_id,
        )
        .order_by(StudentKnowledgeMastery.mastery_score)
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


async def weak_points(
    db: AsyncSession,
    *,
    student_id: int,
    course_id: int,
    threshold: float = 0.4,
) -> list[dict[str, Any]]:
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
        {
            "knowledge_unit_id": ku.id,
            "name": ku.name,
            "mastery_score": round(float(m.mastery_score), 4),
            "attempt_count": m.attempt_count,
        }
        for m, ku in rows
    ]


async def class_report(db: AsyncSession, *, course_id: int) -> dict[str, Any]:
    result = await db.execute(
        select(
            KnowledgeUnit.id.label("knowledge_unit_id"),
            KnowledgeUnit.name.label("name"),
            func.avg(StudentKnowledgeMastery.mastery_score).label("avg_mastery"),
            func.count(StudentKnowledgeMastery.id).label("student_count"),
            func.sum(case((StudentKnowledgeMastery.mastery_score < 0.4, 1), else_=0)).label("risk_count"),
        )
        .join(KnowledgeUnit, StudentKnowledgeMastery.knowledge_unit_id == KnowledgeUnit.id)
        .where(KnowledgeUnit.course_id == course_id)
        .group_by(KnowledgeUnit.id, KnowledgeUnit.name)
        .order_by(func.avg(StudentKnowledgeMastery.mastery_score))
    )

    by_knowledge_unit = []
    rows = result.all()
    for row in rows:
        by_knowledge_unit.append(
            {
                "knowledge_unit_id": row.knowledge_unit_id,
                "name": row.name,
                "avg_mastery": round(float(row.avg_mastery), 4) if row.avg_mastery is not None else 0.0,
                "student_count": int(row.student_count or 0),
                "risk_count": int(row.risk_count or 0),
            }
        )

    overall_avg = round(
        sum(item["avg_mastery"] for item in by_knowledge_unit) / len(by_knowledge_unit),
        4,
    ) if by_knowledge_unit else 0.0

    return {
        "course_id": course_id,
        "overall_avg_mastery": overall_avg,
        "knowledge_unit_count": len(by_knowledge_unit),
        "by_knowledge_unit": by_knowledge_unit,
    }


async def refresh_learning_alerts(
    db: AsyncSession,
    *,
    course_id: int,
    student_id: int | None = None,
    threshold: float = 0.4,
) -> int:
    query = (
        select(StudentKnowledgeMastery, KnowledgeUnit)
        .join(KnowledgeUnit, StudentKnowledgeMastery.knowledge_unit_id == KnowledgeUnit.id)
        .where(
            KnowledgeUnit.course_id == course_id,
            StudentKnowledgeMastery.mastery_score < threshold,
        )
    )
    if student_id:
        query = query.where(StudentKnowledgeMastery.student_id == student_id)
    rows = (await db.execute(query)).all()

    created = 0
    for mastery, ku in rows:
        duplicate_query = select(LearningAlert).where(
            LearningAlert.student_id == mastery.student_id,
            LearningAlert.course_id == course_id,
            LearningAlert.alert_type == "knowledge_weak",
            LearningAlert.is_resolved.is_(False),
            LearningAlert.details["knowledge_unit_id"].as_integer() == ku.id,
        )
        existing = (await db.execute(duplicate_query)).scalar_one_or_none()
        if existing:
            continue

        severity = "high" if mastery.mastery_score < 0.25 else "medium"
        db.add(
            LearningAlert(
                student_id=mastery.student_id,
                course_id=course_id,
                alert_type="knowledge_weak",
                severity=severity,
                message=f"Knowledge unit '{ku.name}' is below threshold ({mastery.mastery_score:.2f})",
                details={
                    "knowledge_unit_id": ku.id,
                    "knowledge_unit_name": ku.name,
                    "mastery_score": float(mastery.mastery_score),
                    "threshold": threshold,
                },
            )
        )
        created += 1

    return created
