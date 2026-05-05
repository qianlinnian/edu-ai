from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from models.assignment import Assignment, GradingResult, Submission, SubmissionStatus
from models.course import KnowledgeUnit
from models.learning import LearningAlert, StudentKnowledgeMastery
from workers.celery_app import celery_app

settings = get_settings()
sync_engine = create_engine(settings.DATABASE_SYNC_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)


def _calculate_score(*, content: str | None, has_file: bool, max_score: float) -> float:
    base_score = 60.0
    length_bonus = min((len((content or "").strip()) / 50.0), 30.0)
    file_bonus = 10.0 if has_file else 0.0
    score = min(max_score, base_score + length_bonus + file_bonus)
    return round(max(score, 0.0), 2)


def _knowledge_point_ids(value: list | None) -> list[int]:
    """正则化作业的知识点列表，将其转换为整数ID列表。"""
    if not value:
        return []

    output: list[int] = []
    for item in value:
        try:
            output.append(int(item))
        except (TypeError, ValueError):
            continue
    return output


def _update_mastery_from_grading(
    db,
    *,
    student_id: int,
    course_id: int,
    knowledge_point_ids: list[int],
    score: float,
    max_score: float,
    alert_threshold: float = 0.4,
) -> dict[int, float]:
    """评分后更新学生的知识掌握度，并在掌握度低于阈值时创建未解决的弱点警报。"""
    if not knowledge_point_ids:
        return {}

    now = datetime.now(timezone.utc)
    score_ratio = min(max(score / max(max_score, 1.0), 0.0), 1.0)
    is_correct = score_ratio >= 0.6
    point_scores: dict[int, float] = {}

    for kp_id in knowledge_point_ids:
        ku = db.execute(
            select(KnowledgeUnit).where(KnowledgeUnit.id == kp_id, KnowledgeUnit.course_id == course_id)
        ).scalar_one_or_none()
        if not ku:
            continue

        # grading worker 是同步的，所以保持这个更新在本地，而不是通过事件或消息队列异步通知分析引擎，以避免复杂性和潜在的同步问题。

        mastery = db.execute(
            select(StudentKnowledgeMastery).where(
                StudentKnowledgeMastery.student_id == student_id,
                StudentKnowledgeMastery.knowledge_unit_id == kp_id,
            )
        ).scalar_one_or_none()
        if mastery is None:
            mastery = StudentKnowledgeMastery(
                student_id=student_id,
                knowledge_unit_id=kp_id,
                mastery_score=0.5,
                attempt_count=0,
                correct_count=0,
            )
            db.add(mastery)
            db.flush()

        mastery.attempt_count += 1
        mastery.correct_count += 1 if is_correct else 0
        outcome = score_ratio if is_correct else max(score_ratio * 0.5, 0.0)
        # 使用 EMA 平滑更新，既保留历史掌握度，也能反映本次批改结果。
        mastery.mastery_score = round(min(max(mastery.mastery_score * 0.7 + outcome * 0.3, 0.0), 1.0), 4)
        mastery.last_assessed_at = now
        point_scores[kp_id] = round(score_ratio * 100, 2)

        if mastery.mastery_score < alert_threshold:
            # 避免为同一学生和同一知识点重复创建未解决的预警。
            existing_alert = db.execute(
                select(LearningAlert).where(
                    LearningAlert.student_id == student_id,
                    LearningAlert.course_id == course_id,
                    LearningAlert.alert_type == "knowledge_weak",
                    LearningAlert.is_resolved.is_(False),
                    LearningAlert.details["knowledge_unit_id"].as_integer() == kp_id,
                )
            ).scalar_one_or_none()
            if not existing_alert:
                severity = "high" if mastery.mastery_score < 0.25 else "medium"
                db.add(
                    LearningAlert(
                        student_id=student_id,
                        course_id=course_id,
                        alert_type="knowledge_weak",
                        severity=severity,
                        message=f"Knowledge unit '{ku.name}' is below threshold ({mastery.mastery_score:.2f})",
                        details={
                            "knowledge_unit_id": kp_id,
                            "knowledge_unit_name": ku.name,
                            "mastery_score": float(mastery.mastery_score),
                            "threshold": alert_threshold,
                            "source": "assignment_grading",
                        },
                    )
                )

    return point_scores


@celery_app.task(name="workers.grading_task.grade_submission")
def grade_submission(submission_id: int):
    """异步批改作业任务"""
    print(f"[Grading] 开始批改 submission_id={submission_id}")

    try:
        with SyncSessionLocal() as db:
            submission = db.execute(select(Submission).where(Submission.id == submission_id)).scalar_one_or_none()
            if not submission:
                return {"submission_id": submission_id, "status": "not_found"}

            assignment = db.execute(
                select(Assignment).where(Assignment.id == submission.assignment_id)
            ).scalar_one_or_none()
            if not assignment:
                submission.status = SubmissionStatus.FAILED
                db.commit()
                return {"submission_id": submission_id, "status": "assignment_not_found"}

            submission.status = SubmissionStatus.GRADING
            db.flush()

            score = _calculate_score(
                content=submission.content,
                has_file=bool(submission.file_path),
                max_score=assignment.max_score,
            )
            existing = db.execute(
                select(GradingResult).where(GradingResult.submission_id == submission.id)
            ).scalar_one_or_none()

            comment = "已完成自动批改（基础规则版）。后续可接入LLM精细批注。"
            strengths = ["提交格式完整"] if submission.content or submission.file_path else []
            weaknesses = [] if score >= assignment.max_score * 0.6 else ["答案内容偏少，建议补充细节"]
            knowledge_point_scores = _update_mastery_from_grading(
                db,
                student_id=submission.student_id,
                course_id=assignment.course_id,
                knowledge_point_ids=_knowledge_point_ids(assignment.knowledge_points),
                score=score,
                max_score=assignment.max_score,
            )

            if existing:
                existing.score = score
                existing.max_score = assignment.max_score
                existing.overall_comment = comment
                existing.strengths = strengths
                existing.weaknesses = weaknesses
                existing.knowledge_point_scores = knowledge_point_scores
            else:
                db.add(
                    GradingResult(
                        submission_id=submission.id,
                        score=score,
                        max_score=assignment.max_score,
                        overall_comment=comment,
                        strengths=strengths,
                        weaknesses=weaknesses,
                        knowledge_point_scores=knowledge_point_scores,
                    )
                )

            submission.status = SubmissionStatus.GRADED
            db.commit()

            return {"submission_id": submission_id, "status": "graded", "score": score}
    except Exception as exc:
        with SyncSessionLocal() as db:
            submission = db.execute(select(Submission).where(Submission.id == submission_id)).scalar_one_or_none()
            if submission:
                submission.status = SubmissionStatus.FAILED
                db.commit()
        return {"submission_id": submission_id, "status": "failed", "error": str(exc)}


@celery_app.task(name="workers.grading_task.batch_grade")
def batch_grade(assignment_id: int):
    """批量批改某作业的所有提交"""
    print(f"[Grading] 批量批改 assignment_id={assignment_id}")

    with SyncSessionLocal() as db:
        submission_ids = db.execute(
            select(Submission.id).where(
                Submission.assignment_id == assignment_id,
                Submission.status == SubmissionStatus.PENDING,
            )
        ).scalars().all()

    for sid in submission_ids:
        grade_submission.delay(sid)

    return {"assignment_id": assignment_id, "status": "completed", "count": len(submission_ids)}
