from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from education.exercise_engine import DEFAULT_INITIAL_MASTERY, apply_mastery_update
from models.assignment import Assignment, GradingResult, Submission, SubmissionAnnotation, SubmissionStatus
from models.course import KnowledgeUnit
from models.learning import LearningAlert, StudentKnowledgeMastery
from workers.celery_app import celery_app

settings = get_settings()
sync_engine = create_engine(settings.DATABASE_SYNC_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)

MASTERY_ALERT_THRESHOLD = 0.4


def _calculate_score(*, content: str | None, has_file: bool, max_score: float) -> float:
    base_score = 20.0
    length_bonus = min((len((content or "").strip()) / 5.0), 60.0)
    file_bonus = 20.0 if has_file else 0.0
    score = min(max_score, base_score + length_bonus + file_bonus)
    return round(max(score, 0.0), 2)


def _normalize_score_100(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    if 0.0 <= numeric <= 1.0:
        return round(numeric * 100.0, 2)
    return round(min(max(numeric, 0.0), 100.0), 2)


def _normalize_knowledge_point_scores(raw_scores: Any) -> dict[str, float]:
    if not isinstance(raw_scores, dict):
        return {}

    normalized: dict[str, float] = {}
    for kp_id, value in raw_scores.items():
        score_100 = _normalize_score_100(value)
        if score_100 is None:
            continue
        normalized[str(kp_id)] = score_100

    return normalized


def _normalize_annotations(raw_annotations: Any, fallback_knowledge_point_id: int | None) -> list[dict[str, Any]]:
    if not isinstance(raw_annotations, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in raw_annotations:
        if not isinstance(item, dict):
            continue

        content = item.get("content") or item.get("comment") or item.get("text") or item.get("message")
        if not content:
            continue

        annotation_type = item.get("annotation_type") or item.get("type") or "suggestion"
        severity = item.get("severity") or item.get("level") or "medium"
        position = item.get("position") or item.get("anchor") or item.get("location") or {"paragraph": 0}
        kp_id = (
            item.get("knowledge_point_id")
            or item.get("knowledge_unit_id")
            or item.get("kp_id")
            or fallback_knowledge_point_id
        )

        normalized.append(
            {
                "annotation_type": str(annotation_type),
                "position": position if isinstance(position, dict) else {"paragraph": 0},
                "content": str(content),
                "severity": str(severity),
                "knowledge_point_id": int(kp_id) if kp_id is not None else None,
            }
        )

    return normalized


def _fallback_annotation(*, score_100: float, knowledge_point_id: int | None) -> list[dict[str, Any]]:
    if score_100 >= 85.0:
        return [
            {
                "annotation_type": "praise",
                "position": {"paragraph": 0},
                "content": "This submission is complete and clearly structured.",
                "severity": "low",
                "knowledge_point_id": knowledge_point_id,
            }
        ]

    return [
        {
            "annotation_type": "suggestion",
            "position": {"paragraph": 0},
            "content": "Add more supporting detail and examples to strengthen the answer.",
            "severity": "medium",
            "knowledge_point_id": knowledge_point_id,
        }
    ]


def _build_fallback_grading_payload(assignment: Assignment, submission: Submission) -> dict[str, Any]:
    score = _calculate_score(
        content=submission.content,
        has_file=bool(submission.file_path),
        max_score=assignment.max_score,
    )
    overall_score_100 = round((score / assignment.max_score) * 100.0, 2) if assignment.max_score else 0.0
    knowledge_points = [int(kp) for kp in (assignment.knowledge_points or [])]
    knowledge_point_scores = {str(kp_id): overall_score_100 for kp_id in knowledge_points}

    strengths = ["Submission format is complete"] if submission.content or submission.file_path else []
    weaknesses = [] if overall_score_100 >= 60.0 else ["The answer is too brief and needs more detail."]

    return {
        "score": score,
        "max_score": assignment.max_score,
        "overall_comment": "Automated grading completed with the current fallback rules.",
        "strengths": strengths,
        "weaknesses": weaknesses,
        "knowledge_point_scores": knowledge_point_scores,
        "annotations": _fallback_annotation(
            score_100=overall_score_100,
            knowledge_point_id=knowledge_points[0] if knowledge_points else None,
        ),
    }


def _normalize_grading_payload(raw_payload: dict[str, Any] | None, assignment: Assignment, submission: Submission) -> dict[str, Any]:
    fallback = _build_fallback_grading_payload(assignment, submission)
    if not isinstance(raw_payload, dict):
        return fallback

    raw_score = raw_payload.get("score", fallback["score"])
    try:
        score = round(min(max(float(raw_score), 0.0), assignment.max_score), 2)
    except (TypeError, ValueError):
        score = fallback["score"]

    knowledge_point_scores = _normalize_knowledge_point_scores(
        raw_payload.get("knowledge_point_scores"),
    )
    if not knowledge_point_scores:
        knowledge_point_scores = fallback["knowledge_point_scores"]

    annotations = _normalize_annotations(
        raw_payload.get("annotations"),
        fallback_knowledge_point_id=(assignment.knowledge_points or [None])[0],
    )
    if not annotations:
        annotations = fallback["annotations"]

    return {
        "score": score,
        "max_score": assignment.max_score,
        "overall_comment": raw_payload.get("overall_comment") or raw_payload.get("comment") or fallback["overall_comment"],
        "strengths": raw_payload.get("strengths") if isinstance(raw_payload.get("strengths"), list) else fallback["strengths"],
        "weaknesses": raw_payload.get("weaknesses") if isinstance(raw_payload.get("weaknesses"), list) else fallback["weaknesses"],
        "knowledge_point_scores": knowledge_point_scores,
        "annotations": annotations,
    }


def _write_annotations(db, *, submission_id: int, course_id: int, annotations: list[dict[str, Any]]) -> None:
    candidate_ids = {
        item["knowledge_point_id"]
        for item in annotations
        if item.get("knowledge_point_id") is not None
    }
    valid_ids = set(
        db.execute(
            select(KnowledgeUnit.id).where(
                KnowledgeUnit.course_id == course_id,
                KnowledgeUnit.id.in_(candidate_ids),
            )
        ).scalars().all()
    ) if candidate_ids else set()

    db.execute(delete(SubmissionAnnotation).where(SubmissionAnnotation.submission_id == submission_id))
    for item in annotations:
        knowledge_point_id = item["knowledge_point_id"] if item["knowledge_point_id"] in valid_ids else None
        db.add(
            SubmissionAnnotation(
                submission_id=submission_id,
                annotation_type=item["annotation_type"],
                position=item["position"],
                content=item["content"],
                severity=item["severity"],
                knowledge_point_id=knowledge_point_id,
            )
        )


def _update_mastery_from_grading(
    db,
    *,
    student_id: int,
    knowledge_point_scores: dict[str, float],
) -> None:
    if not knowledge_point_scores:
        return

    now = datetime.now(timezone.utc)
    for raw_kp_id, score_100 in knowledge_point_scores.items():
        try:
            kp_id = int(raw_kp_id)
        except (TypeError, ValueError):
            continue

        knowledge_unit = db.execute(select(KnowledgeUnit.id).where(KnowledgeUnit.id == kp_id)).scalar_one_or_none()
        if knowledge_unit is None:
            continue

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
                mastery_score=DEFAULT_INITIAL_MASTERY,
                attempt_count=0,
                correct_count=0,
            )
            db.add(mastery)
            db.flush()

        score_ratio = min(max(float(score_100) / 100.0, 0.0), 1.0)
        is_correct = score_ratio >= 0.6
        apply_mastery_update(mastery, score_ratio=score_ratio, is_correct=is_correct, assessed_at=now)


def _refresh_learning_alerts_sync(
    db,
    *,
    course_id: int,
    student_id: int,
    threshold: float = MASTERY_ALERT_THRESHOLD,
) -> int:
    rows = db.execute(
        select(StudentKnowledgeMastery, KnowledgeUnit)
        .join(KnowledgeUnit, StudentKnowledgeMastery.knowledge_unit_id == KnowledgeUnit.id)
        .where(
            KnowledgeUnit.course_id == course_id,
            StudentKnowledgeMastery.student_id == student_id,
            StudentKnowledgeMastery.mastery_score < threshold,
        )
    ).all()

    created = 0
    for mastery, knowledge_unit in rows:
        existing = db.execute(
            select(LearningAlert).where(
                LearningAlert.student_id == student_id,
                LearningAlert.course_id == course_id,
                LearningAlert.alert_type == "knowledge_weak",
                LearningAlert.is_resolved.is_(False),
                LearningAlert.details["knowledge_unit_id"].as_integer() == knowledge_unit.id,
            )
        ).scalar_one_or_none()
        if existing:
            continue

        severity = "high" if mastery.mastery_score < 0.25 else "medium"
        db.add(
            LearningAlert(
                student_id=student_id,
                course_id=course_id,
                alert_type="knowledge_weak",
                severity=severity,
                message=f"Knowledge unit '{knowledge_unit.name}' is below threshold ({mastery.mastery_score:.2f})",
                details={
                    "knowledge_unit_id": knowledge_unit.id,
                    "knowledge_unit_name": knowledge_unit.name,
                    "mastery_score": float(mastery.mastery_score),
                    "threshold": threshold,
                },
            )
        )
        created += 1

    return created


@celery_app.task(name="workers.grading_task.grade_submission")
def grade_submission(submission_id: int):
    print(f"[Grading] start submission_id={submission_id}")

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

            previous_status = submission.status
            existing = db.execute(
                select(GradingResult).where(GradingResult.submission_id == submission.id)
            ).scalar_one_or_none()
            first_success = previous_status != SubmissionStatus.GRADED and existing is None

            submission.status = SubmissionStatus.GRADING
            db.flush()

            raw_payload: dict[str, Any] | None = None
            grading_payload = _normalize_grading_payload(raw_payload, assignment, submission)

            if existing:
                existing.score = grading_payload["score"]
                existing.max_score = grading_payload["max_score"]
                existing.overall_comment = grading_payload["overall_comment"]
                existing.strengths = grading_payload["strengths"]
                existing.weaknesses = grading_payload["weaknesses"]
                existing.knowledge_point_scores = grading_payload["knowledge_point_scores"]
            else:
                db.add(
                    GradingResult(
                        submission_id=submission.id,
                        score=grading_payload["score"],
                        max_score=grading_payload["max_score"],
                        overall_comment=grading_payload["overall_comment"],
                        strengths=grading_payload["strengths"],
                        weaknesses=grading_payload["weaknesses"],
                        knowledge_point_scores=grading_payload["knowledge_point_scores"],
                    )
                )

            _write_annotations(
                db,
                submission_id=submission.id,
                course_id=assignment.course_id,
                annotations=grading_payload["annotations"],
            )

            if first_success:
                _update_mastery_from_grading(
                    db,
                    student_id=submission.student_id,
                    knowledge_point_scores=grading_payload["knowledge_point_scores"],
                )
                _refresh_learning_alerts_sync(
                    db,
                    course_id=assignment.course_id,
                    student_id=submission.student_id,
                )

            submission.status = SubmissionStatus.GRADED
            db.commit()

            return {
                "submission_id": submission_id,
                "status": "graded",
                "score": grading_payload["score"],
                "first_success": first_success,
            }
    except Exception as exc:
        with SyncSessionLocal() as db:
            submission = db.execute(select(Submission).where(Submission.id == submission_id)).scalar_one_or_none()
            if submission:
                submission.status = SubmissionStatus.FAILED
                db.commit()
        return {"submission_id": submission_id, "status": "failed", "error": str(exc)}


@celery_app.task(name="workers.grading_task.batch_grade")
def batch_grade(assignment_id: int):
    print(f"[Grading] batch assignment_id={assignment_id}")

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
