from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from models.assignment import Assignment, GradingResult, Submission, SubmissionStatus
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

            if existing:
                existing.score = score
                existing.max_score = assignment.max_score
                existing.overall_comment = comment
                existing.strengths = strengths
                existing.weaknesses = weaknesses
            else:
                db.add(
                    GradingResult(
                        submission_id=submission.id,
                        score=score,
                        max_score=assignment.max_score,
                        overall_comment=comment,
                        strengths=strengths,
                        weaknesses=weaknesses,
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
