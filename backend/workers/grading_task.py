from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

from agent_core.agent_base import AgentConfig, GradingAgent
from core.config import get_settings
from education.exercise_engine import DEFAULT_INITIAL_MASTERY, apply_mastery_update
from models.assignment import Assignment, GradingResult, Submission, SubmissionAnnotation, SubmissionStatus
from models.course import KnowledgeUnit
from models.learning import LearningAlert, StudentKnowledgeMastery
from workers.celery_app import celery_app

settings = get_settings()
sync_engine = create_engine(settings.DATABASE_SYNC_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)

MAX_GRADING_CONTENT_CHARS = 12000
MASTERY_ALERT_THRESHOLD = 0.4
ANNOTATION_TYPES = {"error", "warning", "suggestion", "praise"}
ANNOTATION_SEVERITIES = {"low", "medium", "high", "critical"}


def _calculate_score(*, content: str | None, has_file: bool, max_score: float) -> float:
    base_score = 60.0
    length_bonus = min((len((content or "").strip()) / 50.0), 30.0)
    file_bonus = 10.0 if has_file else 0.0
    score = min(max_score, base_score + length_bonus + file_bonus)
    return round(max(score, 0.0), 2)


def _knowledge_point_ids(value: list | None) -> list[int]:
    if not value:
        return []

    output: list[int] = []
    for item in value:
        try:
            output.append(int(item))
        except (TypeError, ValueError):
            continue
    return output


def _safe_json_loads(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fenced:
        text = fenced.group(1).strip()
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("LLM grading output must be a JSON object")
    return data


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _normalize_score(value: Any, max_score: float) -> float:
    try:
        if isinstance(value, str):
            match = re.search(r"-?\d+(?:\.\d+)?", value)
            score = float(match.group(0)) if match else 0.0
        else:
            score = float(value)
    except (TypeError, ValueError):
        score = 0.0
    return round(min(max(score, 0.0), float(max_score)), 2)


def _file_type_from_path(path: str | None) -> str:
    if not path or "." not in path:
        return "txt"
    return path.rsplit(".", 1)[-1].lower()


def _load_submission_file_text(file_path: str | None) -> tuple[str, str | None]:
    if not file_path:
        return "", None

    response = None
    try:
        from workers.embedding_task import get_minio_client, parse_resource_content

        client = get_minio_client()
        response = client.get_object(settings.MINIO_BUCKET, file_path)
        payload = response.read()
        file_type = _file_type_from_path(file_path)
        text = parse_resource_content(file_type, payload).strip()
        if not text:
            return "", f"Attachment {file_path} did not produce usable text"
        return text, None
    except Exception as exc:
        return "", f"Attachment {file_path} parsing failed: {exc}"
    finally:
        if response is not None:
            try:
                response.close()
                response.release_conn()
            except Exception:
                pass


def _build_grading_content(submission: Submission) -> tuple[str, str]:
    text_parts: list[str] = []
    warnings: list[str] = []

    if submission.content and submission.content.strip():
        text_parts.append(f"[鏂囨湰鎻愪氦]\n{submission.content.strip()}")

    file_text, file_warning = _load_submission_file_text(submission.file_path)
    if file_text:
        text_parts.append(f"[闄勪欢瑙ｆ瀽鍐呭]\n{file_text}")
    if file_warning:
        warnings.append(file_warning)

    merged = "\n\n".join(text_parts).strip()
    if len(merged) > MAX_GRADING_CONTENT_CHARS:
        merged = merged[:MAX_GRADING_CONTENT_CHARS] + "\n\n[鍐呭杩囬暱锛屽凡鎴柇鐢ㄤ簬鑷姩鎵规敼]"

    return merged, "\n".join(warnings)


def _format_assignment_context(assignment: Assignment) -> str:
    rubric_text = json.dumps(assignment.rubric, ensure_ascii=False) if assignment.rubric else "No rubric provided. Use correctness 60%, completeness 25%, clarity 15%."
    reference_answer = assignment.reference_answer or "No reference answer provided. Grade according to the assignment description and rubric."
    knowledge_point_ids = _knowledge_point_ids(assignment.knowledge_points)
    return (
        f"Assignment title: {assignment.title}\n"
        f"Description: {assignment.description or 'N/A'}\n"
        f"Type: {assignment.assignment_type}\n"
        f"Max score: {assignment.max_score}\n"
        f"Knowledge point IDs: {knowledge_point_ids or 'N/A'}\n"
        f"Rubric: {rubric_text}\n"
        f"Reference answer: {reference_answer}"
    )

def _fallback_knowledge_scores(knowledge_point_ids: list[int], score: float, max_score: float) -> dict[str, float]:
    if not knowledge_point_ids:
        return {}
    ratio = min(max(score / max(max_score, 1.0), 0.0), 1.0)
    return {str(kp_id): round(ratio * 100, 2) for kp_id in knowledge_point_ids}


def _normalize_knowledge_scores(
    value: Any,
    *,
    knowledge_point_ids: list[int],
    score: float,
    max_score: float,
) -> dict[str, float]:
    allowed_ids = {str(kp_id) for kp_id in knowledge_point_ids}
    output: dict[str, float] = {}

    if isinstance(value, dict):
        items = value.items()
    elif isinstance(value, list):
        items = []
        for item in value:
            if isinstance(item, dict):
                kp_id = item.get("knowledge_point_id") or item.get("knowledge_unit_id") or item.get("id")
                kp_score = item.get("score")
                items.append((kp_id, kp_score))
    else:
        items = []

    for key, raw_score in items:
        key_text = str(key).strip()
        if not key_text:
            continue
        if allowed_ids and key_text not in allowed_ids:
            continue
        output[key_text] = _normalize_score(raw_score, 100.0)

    return output or _fallback_knowledge_scores(knowledge_point_ids, score, max_score)


def _normalize_annotations(value: Any, *, knowledge_point_ids: list[int]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    allowed_ids = set(knowledge_point_ids)
    annotations: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue

        annotation_type = str(item.get("annotation_type") or item.get("type") or "suggestion").strip().lower()
        severity = str(item.get("severity") or item.get("level") or "medium").strip().lower()
        content = str(item.get("content") or item.get("comment") or item.get("text") or item.get("message") or "").strip()
        if not content:
            continue

        position = item.get("position") or item.get("anchor") or item.get("location")
        if not isinstance(position, dict):
            position = {}
        position = {"type": "text", **position}

        raw_kp_id = item.get("knowledge_point_id") or item.get("knowledge_unit_id") or item.get("kp_id")
        try:
            kp_id = int(raw_kp_id) if raw_kp_id is not None else None
        except (TypeError, ValueError):
            kp_id = None
        if kp_id is not None and allowed_ids and kp_id not in allowed_ids:
            kp_id = None

        annotations.append(
            {
                "annotation_type": annotation_type if annotation_type in ANNOTATION_TYPES else "suggestion",
                "position": position,
                "content": content,
                "severity": severity if severity in ANNOTATION_SEVERITIES else "medium",
                "knowledge_point_id": kp_id,
            }
        )

    return annotations


def _standardize_grading_payload(
    data: dict[str, Any] | None,
    *,
    assignment: Assignment,
    source: str,
    submission: Submission | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    data = data if isinstance(data, dict) else {}
    max_score = float(assignment.max_score)
    fallback_score = (
        _calculate_score(content=submission.content, has_file=bool(submission.file_path), max_score=max_score)
        if submission is not None
        else 0.0
    )
    raw_score = data.get("score")
    score = _normalize_score(raw_score, max_score) if raw_score is not None else fallback_score
    knowledge_point_ids = _knowledge_point_ids(assignment.knowledge_points)
    overall_comment = str(data.get("overall_comment") or data.get("comment") or "").strip()
    if not overall_comment:
        overall_comment = "Automatic grading completed."
        if source == "fallback" and error:
            overall_comment += f" LLM grading unavailable; rule fallback used: {error[:180]}"

    return {
        "score": score,
        "max_score": max_score,
        "overall_comment": overall_comment,
        "strengths": _normalize_list(data.get("strengths")),
        "weaknesses": _normalize_list(data.get("weaknesses")),
        "annotations": _normalize_annotations(data.get("annotations"), knowledge_point_ids=knowledge_point_ids),
        "knowledge_point_scores": _normalize_knowledge_scores(
            data.get("knowledge_point_scores"),
            knowledge_point_ids=knowledge_point_ids,
            score=score,
            max_score=max_score,
        ),
        "source": source,
    }

async def _grade_with_llm(*, assignment: Assignment, submission: Submission) -> dict[str, Any]:
    content, warning_text = _build_grading_content(submission)
    file_note = f"Student submitted attachment: {submission.file_path}" if submission.file_path else "Student did not submit an attachment."
    if warning_text:
        file_note += f"\nAttachment processing warning: {warning_text}"

    agent = GradingAgent(
        AgentConfig(
            name="AssignmentGradingAgent",
            course_id=assignment.course_id,
            system_prompt=(
                "You are EduAI's assignment grading agent. Grade according to the assignment, rubric, "
                "reference answer, related knowledge points, and student submission. Return only JSON."
            ),
            llm_provider=settings.DEFAULT_LLM_PROVIDER,
            llm_model=settings.QWEN_MODEL,
            temperature=0.2,
        )
    )
    agent_result = await agent.grade(
        submission_content=f"{file_note}\n\n{content or 'No parseable submission text.'}",
        assignment_info={
            "title": assignment.title,
            "description": assignment.description,
            "assignment_type": assignment.assignment_type,
            "max_score": assignment.max_score,
            "rubric": assignment.rubric,
            "reference_answer": assignment.reference_answer,
            "knowledge_points": _knowledge_point_ids(assignment.knowledge_points),
        },
    )
    return _standardize_grading_payload(
        agent_result,
        assignment=assignment,
        submission=submission,
        source=agent_result.get("source") or "llm",
    )

def _fallback_grading(*, assignment: Assignment, submission: Submission, error: str | None = None) -> dict[str, Any]:
    score = _calculate_score(
        content=submission.content,
        has_file=bool(submission.file_path),
        max_score=float(assignment.max_score),
    )
    data = {
        "score": score,
        "overall_comment": "Automatic fallback grading completed.",
        "strengths": ["Submission format is complete"] if submission.content or submission.file_path else [],
        "weaknesses": [] if score >= float(assignment.max_score) * 0.6 else ["Submission content is too short; add key steps, evidence, or examples"],
        "annotations": [
            {
                "annotation_type": "suggestion",
                "position": {"type": "text", "paragraph": 1, "quote": (submission.content or "")[:80]},
                "content": "Add key steps, evidence, or examples to make the answer more complete.",
                "severity": "medium",
                "knowledge_point_id": None,
            }
        ] if score < float(assignment.max_score) * 0.6 else [],
    }
    if error:
        data["overall_comment"] += f" LLM grading unavailable; rule fallback used: {error[:180]}"
    return _standardize_grading_payload(data, assignment=assignment, submission=submission, source="fallback")

def _grade_submission_content(*, assignment: Assignment, submission: Submission) -> dict[str, Any]:
    try:
        return asyncio.run(_grade_with_llm(assignment=assignment, submission=submission))
    except Exception as exc:
        return _fallback_grading(assignment=assignment, submission=submission, error=str(exc))


def _write_annotations(db, *, submission_id: int, course_id: int, annotations: list[dict[str, Any]]) -> None:
    candidate_ids = {
        item["knowledge_point_id"]
        for item in annotations
        if item.get("knowledge_point_id") is not None
    }
    valid_ids = (
        set(
            db.execute(
                select(KnowledgeUnit.id).where(
                    KnowledgeUnit.course_id == course_id,
                    KnowledgeUnit.id.in_(candidate_ids),
                )
            )
            .scalars()
            .all()
        )
        if candidate_ids
        else set()
    )

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
                    "source": "assignment_grading",
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

            grading_payload = _grade_submission_content(assignment=assignment, submission=submission)

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
                "source": grading_payload["source"],
                "first_success": first_success,
                "annotations": grading_payload["annotations"],
                "annotations_count": len(grading_payload["annotations"]),
                "knowledge_point_scores": grading_payload["knowledge_point_scores"],
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
