from __future__ import annotations

import asyncio
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, delete, desc, select
from sqlalchemy.orm import sessionmaker

from agent_core.agent_base import AgentConfig, GradingAgent
from agent_core.llm_provider import get_llm_provider
from core.config import get_settings
from core.normalization import extract_json_object, normalize_bounded_score, normalize_string_list
from education.exercise_engine import DEFAULT_INITIAL_MASTERY, apply_mastery_update
from models.agent import AgentInstance
from models.assignment import Assignment, GradingResult, Submission, SubmissionAnnotation, SubmissionStatus
from models.course import KnowledgeUnit, ResourceChunk
from models.learning import LearningAlert, StudentKnowledgeMastery
from workers.celery_app import celery_app

settings = get_settings()
sync_engine = create_engine(settings.DATABASE_SYNC_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)

MAX_GRADING_CONTENT_CHARS = 12000
MASTERY_ALERT_THRESHOLD = 0.4
ANNOTATION_TYPES = {"error", "warning", "suggestion", "praise"}
ANNOTATION_SEVERITIES = {"low", "medium", "high", "critical"}
GRADING_CONTEXT_TOP_K = 4
MAX_GRADING_CONTEXT_CHARS = 4000
REFERENCE_MATCH_MIN_CHARS = 2

TEXT_GRADING_REVIEW_MIN_SCORE = 45.0
TEXT_GRADING_REVIEW_MAX_SCORE = 90.0
TEXT_GRADING_REVIEW_MIN_LENGTH = 80


def _should_review_text_grading(*, assignment: Assignment, submission: Submission, grading_payload: dict[str, Any]) -> bool:
    if assignment.assignment_type != "text":
        return False
    content = (submission.content or "").strip()
    if len(content) < TEXT_GRADING_REVIEW_MIN_LENGTH:
        return False
    score = float(grading_payload.get("score") or 0.0)
    return TEXT_GRADING_REVIEW_MIN_SCORE <= score < TEXT_GRADING_REVIEW_MAX_SCORE


def _normalize_reference_match_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def _extract_explicit_reference_answers(reference_answer: str | None) -> list[str]:
    text = unicodedata.normalize("NFKC", str(reference_answer or "")).strip()
    if not text:
        return []

    patterns = [
        r"(?:答案是|标准答案是|正确答案是)\s*[:：]?\s*([^\n。；;]+)",
        r"(?:the\s+answer\s+is|correct\s+answer\s+is|expected\s+answer\s+is)\s*[:：]?\s*([^\n.;]+)",
    ]
    candidates: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            normalized = _normalize_reference_match_text(match)
            if len(normalized) >= REFERENCE_MATCH_MIN_CHARS and normalized not in candidates:
                candidates.append(normalized)
    return candidates


def _apply_reference_answer_match_rule(
    grading_payload: dict[str, Any],
    *,
    assignment: Assignment,
    submission: Submission,
) -> dict[str, Any]:
    submission_text = (submission.content or "").strip()
    reference_answer = str(assignment.reference_answer or "").strip()
    if not submission_text or not reference_answer:
        return grading_payload

    normalized_submission = _normalize_reference_match_text(submission_text)
    normalized_reference = _normalize_reference_match_text(reference_answer)
    explicit_answers = _extract_explicit_reference_answers(reference_answer)

    matched = False
    if (
        len(normalized_submission) >= REFERENCE_MATCH_MIN_CHARS
        and normalized_submission == normalized_reference
    ):
        matched = True
    elif normalized_submission in explicit_answers:
        matched = True

    if not matched:
        return grading_payload

    full_score = float(assignment.max_score)
    result = dict(grading_payload)
    result["score"] = full_score
    result["dimension_scores"] = {
        item["name"]: float(item["max_score"])
        for item in _build_dimension_definitions(assignment)
    }
    existing_comment = str(result.get("overall_comment") or "").strip()
    rule_comment = "Submission matches the teacher-provided reference answer; deterministic full-score rule applied."
    result["overall_comment"] = (
        f"{rule_comment} {existing_comment}".strip() if existing_comment else rule_comment
    )
    result["source"] = f"{grading_payload.get('source', 'llm')}+reference_match_rule"
    return result


def _build_dimension_definitions(assignment: Assignment) -> list[dict[str, Any]]:
    rubric = assignment.rubric
    max_score = float(assignment.max_score)

    if isinstance(rubric, dict):
        raw_dimensions = rubric.get("dimensions")
        if isinstance(raw_dimensions, list):
            output: list[dict[str, Any]] = []
            for item in raw_dimensions:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or item.get("id") or "").strip()
                if not name:
                    continue
                dim_max = normalize_bounded_score(item.get("max_score"), max_score)
                if dim_max <= 0:
                    continue
                output.append({"name": name, "max_score": dim_max})
            if output:
                return output

        numeric_items: list[tuple[str, float]] = []
        for key, raw_value in rubric.items():
            if key in {"text", "dimensions"}:
                continue
            if isinstance(raw_value, (int, float)):
                numeric_items.append((str(key).strip(), float(raw_value)))
        total = sum(value for _, value in numeric_items if value > 0)
        if total > 0:
            scale = max_score / total
            return [
                {"name": name, "max_score": round(value * scale, 2)}
                for name, value in numeric_items
                if name and value > 0
            ]

    ratios = [("correctness", 0.6), ("completeness", 0.25), ("clarity", 0.15)]
    output: list[dict[str, Any]] = []
    remaining = round(max_score, 2)
    for index, (name, ratio) in enumerate(ratios):
        if index == len(ratios) - 1:
            dim_max = round(remaining, 2)
        else:
            dim_max = round(max_score * ratio, 2)
            remaining = round(remaining - dim_max, 2)
        output.append({"name": name, "max_score": dim_max})
    return output


def _normalize_dimension_scores(value: Any, *, assignment: Assignment) -> tuple[dict[str, float], float | None]:
    if not isinstance(value, dict):
        return {}, None

    definitions = _build_dimension_definitions(assignment)
    allowed = {item["name"]: float(item["max_score"]) for item in definitions}
    output: dict[str, float] = {}
    total = 0.0
    for key, raw_score in value.items():
        name = str(key or "").strip()
        if not name or name not in allowed:
            continue
        score = normalize_bounded_score(raw_score, allowed[name])
        output[name] = score
        total += score

    return output, round(total, 2) if output else None


def _normalize_grading_score(raw_score: Any, *, max_score: float) -> float:
    normalized = normalize_bounded_score(raw_score, 100.0)
    if max_score != 100.0:
        normalized = round((normalized / 100.0) * max_score, 2)
    return normalize_bounded_score(normalized, max_score)


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
        text_parts.append(f"[附件解析内容]\n{file_text}")
    if file_warning:
        warnings.append(file_warning)

    merged = "\n\n".join(text_parts).strip()
    if len(merged) > MAX_GRADING_CONTENT_CHARS:
        merged = merged[:MAX_GRADING_CONTENT_CHARS] + "\n\n[内容过长，已截断用于自动批改]"

    return merged, "\n".join(warnings)


async def _retrieve_grading_context(*, assignment: Assignment, submission: Submission, db) -> str:
    if db is None or assignment.course_id is None:
        return ""

    parts: list[str] = []
    for value in [
        assignment.title,
        assignment.description,
        assignment.reference_answer,
        submission.content,
    ]:
        text = str(value or "").strip()
        if text:
            parts.append(text)
    kp_ids = _knowledge_point_ids(assignment.knowledge_points)
    if kp_ids:
        parts.append("knowledge points: " + ", ".join(str(item) for item in kp_ids))
    query = "\n".join(parts).strip()[:1200]
    if not query:
        return ""

    try:
        llm_provider = get_llm_provider("dashscope")
        embeddings = await llm_provider.embedding([query])
        if not embeddings:
            raise RuntimeError("grading query embedding generation returned no vectors")
        query_embedding = embeddings[0]
        result = db.execute(
            select(ResourceChunk)
            .where(ResourceChunk.course_id == assignment.course_id)
            .where(ResourceChunk.embedding.is_not(None))
            .order_by(ResourceChunk.embedding.cosine_distance(query_embedding))
            .limit(GRADING_CONTEXT_TOP_K)
        )
        chunks = result.scalars().all()
    except Exception:
        return ""
    if not chunks:
        return ""

    parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        parts.append(f"Course material {index}:\n{chunk.content}")
    context = "\n\n".join(parts).strip()
    if len(context) > MAX_GRADING_CONTEXT_CHARS:
        context = context[:MAX_GRADING_CONTEXT_CHARS] + "\n\n[course material context truncated]"
    return context

def _default_model_for_provider(provider: str | None) -> str:
    normalized = (provider or settings.DEFAULT_LLM_PROVIDER or "dashscope").strip().lower()
    return {
        "dashscope": settings.QWEN_MODEL,
        "zhipu": settings.ZHIPU_MODEL,
        "deepseek": settings.DEEPSEEK_MODEL,
    }.get(normalized, settings.QWEN_MODEL)


def _resolve_course_llm_config(db, *, course_id: int | None) -> dict[str, str | None]:
    if course_id is None:
        provider = settings.DEFAULT_LLM_PROVIDER
        return {
            "provider": provider,
            "model": _default_model_for_provider(provider),
            "system_prompt": None,
            "source": "default",
        }

    agent = db.execute(
        select(AgentInstance)
        .where(
            AgentInstance.course_id == course_id,
            AgentInstance.is_active.is_(True),
        )
        .order_by(desc(AgentInstance.updated_at), desc(AgentInstance.id))
    ).scalar_one_or_none()

    provider = (
        (agent.llm_provider or settings.DEFAULT_LLM_PROVIDER)
        if agent is not None
        else settings.DEFAULT_LLM_PROVIDER
    )
    provider = provider.strip().lower()
    model = agent.llm_model.strip() if agent is not None and agent.llm_model and agent.llm_model.strip() else _default_model_for_provider(provider)
    system_prompt = agent.system_prompt.strip() if agent is not None and agent.system_prompt else None
    return {
        "provider": provider,
        "model": model,
        "system_prompt": system_prompt,
        "source": "course_agent" if agent is not None else "default",
    }

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
        output[key_text] = normalize_bounded_score(raw_score, 100.0)

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
    dimension_scores, dimension_total = _normalize_dimension_scores(data.get("dimension_scores"), assignment=assignment)
    if dimension_total is not None:
        score = normalize_bounded_score(dimension_total, max_score)
    else:
        score = _normalize_grading_score(raw_score, max_score=max_score) if raw_score is not None else fallback_score
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
        "dimension_scores": dimension_scores,
        "strengths": normalize_string_list(data.get("strengths")),
        "weaknesses": normalize_string_list(data.get("weaknesses")),
        "annotations": _normalize_annotations(data.get("annotations"), knowledge_point_ids=knowledge_point_ids),
        "knowledge_point_scores": _normalize_knowledge_scores(
            data.get("knowledge_point_scores"),
            knowledge_point_ids=knowledge_point_ids,
            score=score,
            max_score=max_score,
        ),
        "source": source,
    }

async def _review_text_grading_if_needed(
    *,
    assignment: Assignment,
    submission: Submission,
    grading_payload: dict[str, Any],
    llm_config: dict[str, str | None],
    course_material_context: str,
) -> dict[str, Any]:
    if not _should_review_text_grading(assignment=assignment, submission=submission, grading_payload=grading_payload):
        return grading_payload

    agent = GradingAgent(
        AgentConfig(
            name="AssignmentGradingReviewAgent",
            course_id=assignment.course_id,
            system_prompt=(
                f"{llm_config['system_prompt']}\n\nYou are reviewing a prior grading result for fairness and calibration."
                if llm_config["system_prompt"]
                else "You are reviewing a prior grading result for fairness and calibration."
            ),
            llm_provider=llm_config["provider"],
            llm_model=llm_config["model"],
            temperature=0.1,
        )
    )
    reviewed = await agent.grade(
        submission_content=submission.content or "",
        assignment_info={
            "title": assignment.title,
            "description": assignment.description,
            "assignment_type": assignment.assignment_type,
            "max_score": assignment.max_score,
            "rubric": assignment.rubric,
            "reference_answer": assignment.reference_answer,
            "knowledge_points": _knowledge_point_ids(assignment.knowledge_points),
            "course_material_context": course_material_context,
            "grading_review_context": {
                "review_mode": "fairness_recheck",
                "previous_result": {
                    "score": grading_payload.get("score"),
                    "dimension_scores": grading_payload.get("dimension_scores"),
                    "overall_comment": grading_payload.get("overall_comment"),
                },
                "instruction": (
                    "Re-evaluate whether the previous result under-scored or over-scored the answer. "
                    "Keep the final score aligned with the rubric and submission quality."
                ),
            },
        },
    )
    reviewed_payload = _standardize_grading_payload(
        reviewed,
        assignment=assignment,
        submission=submission,
        source=reviewed.get("source") or "llm_review",
    )
    if float(reviewed_payload["score"]) > float(grading_payload["score"]):
        reviewed_payload["source"] = f"{grading_payload.get('source', 'llm')}+review"
        return reviewed_payload
    return grading_payload

async def _grade_with_llm(*, assignment: Assignment, submission: Submission, db=None) -> dict[str, Any]:
    content, warning_text = _build_grading_content(submission)
    file_note_parts: list[str] = []
    if submission.file_path:
        file_note_parts.append(f"Student submitted attachment: {submission.file_path}")
    elif assignment.assignment_type != "text":
        file_note_parts.append("No attachment was submitted.")
    if warning_text:
        file_note_parts.append(f"Attachment processing warning: {warning_text}")
    if assignment.assignment_type == "text" and (submission.content or "").strip():
        file_note_parts.append("Use the plain text submission below as the primary student answer.")
    file_note = "\n".join(file_note_parts).strip()

    grading_prompt = (
        "You are EduAI's assignment grading agent. Grade according to the assignment, rubric, "
        "reference answer, related knowledge points, and student submission. Return only JSON."
    )
    owns_session = db is None
    if owns_session:
        db = SyncSessionLocal()
    llm_config = _resolve_course_llm_config(db, course_id=assignment.course_id)
    if owns_session:
        db.close()

    agent = GradingAgent(
        AgentConfig(
            name="AssignmentGradingAgent",
            course_id=assignment.course_id,
            system_prompt=(
                f"{llm_config['system_prompt']}\n\n{grading_prompt}"
                if llm_config["system_prompt"]
                else grading_prompt
            ),
            llm_provider=llm_config["provider"],
            llm_model=llm_config["model"],
            temperature=0.2,
        )
    )
    course_material_context = await _retrieve_grading_context(assignment=assignment, submission=submission, db=db)
    agent_result = await agent.grade(
        submission_content=(
            f"{file_note}\n\n{content or 'No parseable submission text.'}".strip()
            if file_note
            else (content or "No parseable submission text.")
        ),
        assignment_info={
            "title": assignment.title,
            "description": assignment.description,
            "assignment_type": assignment.assignment_type,
            "max_score": assignment.max_score,
            "rubric": assignment.rubric,
            "reference_answer": assignment.reference_answer,
            "knowledge_points": _knowledge_point_ids(assignment.knowledge_points),
            "course_material_context": course_material_context,
        },
    )
    standardized = _standardize_grading_payload(
        agent_result,
        assignment=assignment,
        submission=submission,
        source=agent_result.get("source") or "llm",
    )
    standardized = _apply_reference_answer_match_rule(
        standardized,
        assignment=assignment,
        submission=submission,
    )
    return await _review_text_grading_if_needed(
        assignment=assignment,
        submission=submission,
        grading_payload=standardized,
        llm_config=llm_config,
        course_material_context=course_material_context,
    )

def _fallback_grading(*, assignment: Assignment, submission: Submission, error: str | None = None) -> dict[str, Any]:
    score = _calculate_score(
        content=submission.content,
        has_file=bool(submission.file_path),
        max_score=float(assignment.max_score),
    )
    data = {
        "score": score,
        "dimension_scores": {
            "correctness": round(score * 0.6, 2),
            "completeness": round(score * 0.25, 2),
            "clarity": round(score - round(score * 0.6, 2) - round(score * 0.25, 2), 2),
        },
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

def _grade_submission_content(*, assignment: Assignment, submission: Submission, db=None) -> dict[str, Any]:
    try:
        return asyncio.run(_grade_with_llm(assignment=assignment, submission=submission, db=db))
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

            grading_payload = _grade_submission_content(assignment=assignment, submission=submission, db=db)

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
