from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from agent_core.llm_provider import get_llm_provider
from core.config import get_settings
from models.assignment import Assignment, GradingResult, Submission, SubmissionStatus
from models.course import KnowledgeUnit
from models.learning import LearningAlert, StudentKnowledgeMastery
from workers.celery_app import celery_app

settings = get_settings()
sync_engine = create_engine(settings.DATABASE_SYNC_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)
MAX_GRADING_CONTENT_CHARS = 12000
ANNOTATION_TYPES = {"error", "warning", "suggestion", "praise"}
ANNOTATION_SEVERITIES = {"low", "medium", "high", "critical"}


def _calculate_score(*, content: str | None, has_file: bool, max_score: float) -> float:
    """规则兜底评分：在 LLM 批改失败时保证任务不会中断。"""
    base_score = 60.0
    length_bonus = min((len((content or "").strip()) / 50.0), 30.0)
    file_bonus = 10.0 if has_file else 0.0
    score = min(max_score, base_score + length_bonus + file_bonus)
    return round(max(score, 0.0), 2)


def _knowledge_point_ids(value: list | None) -> list[int]:
    """规范化作业的知识点列表，将其转换为整数 ID 列表。"""
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
    """从 LLM 输出中提取 JSON；如果模型包了 markdown 代码块，也尽量兼容。"""
    text = raw_text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fenced:
        text = fenced.group(1)
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
    """从 MinIO 读取附件并解析文本；解析失败时返回错误说明，避免中断批改。"""
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
            return "", f"附件 {file_path} 未解析出可用文本"
        return text, None
    except Exception as exc:
        return "", f"附件 {file_path} 解析失败：{exc}"
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
        text_parts.append(f"[文本提交]\n{submission.content.strip()}")

    file_text, file_warning = _load_submission_file_text(submission.file_path)
    if file_text:
        text_parts.append(f"[附件解析内容]\n{file_text}")
    if file_warning:
        warnings.append(file_warning)

    merged = "\n\n".join(text_parts).strip()
    if len(merged) > MAX_GRADING_CONTENT_CHARS:
        merged = merged[:MAX_GRADING_CONTENT_CHARS] + "\n\n[内容过长，已截断用于自动批改]"

    return merged, "\n".join(warnings)


def _format_assignment_context(assignment: Assignment) -> str:
    if assignment.rubric:
        rubric_text = json.dumps(assignment.rubric, ensure_ascii=False)
    else:
        rubric_text = "老师未填写评分标准。默认按正确性 60%、完整性 25%、表达清晰度 15% 进行参考评分。"

    reference_answer = assignment.reference_answer or "老师未提供参考答案，请主要依据作业说明和评分标准进行审慎评分。"
    knowledge_point_ids = _knowledge_point_ids(assignment.knowledge_points)
    return (
        f"作业标题：{assignment.title}\n"
        f"作业说明：{assignment.description or '无'}\n"
        f"作业类型：{assignment.assignment_type}\n"
        f"满分：{assignment.max_score}\n"
        f"关联知识点 ID：{knowledge_point_ids or '无'}\n"
        f"作业补充信息：\n"
        f"- 评分标准：{rubric_text}\n"
        f"- 参考答案：{reference_answer}"
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
                kp_id = item.get("knowledge_point_id") or item.get("id")
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
        severity = str(item.get("severity") or "medium").strip().lower()
        content = str(item.get("content") or item.get("message") or "").strip()
        if not content:
            continue

        position = item.get("position")
        if not isinstance(position, dict):
            position = {}
        position = {"type": "text", **position}

        kp_id = item.get("knowledge_point_id")
        try:
            kp_id = int(kp_id) if kp_id is not None else None
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
    data: dict[str, Any],
    *,
    assignment: Assignment,
    source: str,
) -> dict[str, Any]:
    score = _normalize_score(data.get("score"), assignment.max_score)
    knowledge_point_ids = _knowledge_point_ids(assignment.knowledge_points)
    overall_comment = str(data.get("overall_comment") or data.get("comment") or "已完成自动批改。").strip()

    return {
        "score": score,
        "overall_comment": overall_comment or "已完成自动批改。",
        "strengths": _normalize_list(data.get("strengths")),
        "weaknesses": _normalize_list(data.get("weaknesses")),
        "annotations": _normalize_annotations(data.get("annotations"), knowledge_point_ids=knowledge_point_ids),
        "knowledge_point_scores": _normalize_knowledge_scores(
            data.get("knowledge_point_scores"),
            knowledge_point_ids=knowledge_point_ids,
            score=score,
            max_score=assignment.max_score,
        ),
        "source": source,
    }


async def _grade_with_llm(*, assignment: Assignment, submission: Submission) -> dict[str, Any]:
    provider = get_llm_provider()
    assignment_context = _format_assignment_context(assignment)
    content, warning_text = _build_grading_content(submission)
    file_note = f"学生提交了附件：{submission.file_path}" if submission.file_path else "学生未提交附件。"
    if warning_text:
        file_note += f"\n附件处理提示：{warning_text}"

    messages = [
        {
            "role": "system",
            "content": (
                "你是教学平台的自动批改助手。请根据作业题目、评分标准、参考答案、关联知识点和学生提交内容进行评分。"
                "必须只返回 JSON 对象，不要返回 markdown，不要添加解释性前后缀。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"{assignment_context}\n"
                f"{file_note}\n\n"
                f"学生提交内容（包含文本提交和可解析附件内容）：\n{content or '无可解析文本内容'}\n\n"
                "请严格返回如下 JSON 结构：\n"
                "{\n"
                '  "score": 0 到满分之间的数字,\n'
                '  "overall_comment": "总体评价，不能为空",\n'
                '  "strengths": ["优点1"],\n'
                '  "weaknesses": ["不足1"],\n'
                '  "knowledge_point_scores": {"知识点ID": 0 到 100 的数字},\n'
                '  "annotations": [\n'
                "    {\n"
                '      "annotation_type": "error|warning|suggestion|praise",\n'
                '      "position": {"type": "text", "line": 1, "paragraph": 1, "quote": "学生原文片段"},\n'
                '      "content": "批注意见",\n'
                '      "severity": "low|medium|high|critical",\n'
                '      "knowledge_point_id": 知识点ID或null\n'
                "    }\n"
                "  ]\n"
                "}"
            ),
        },
    ]
    raw = await provider.chat(messages, temperature=0.2)
    return _standardize_grading_payload(_safe_json_loads(raw), assignment=assignment, source="llm")


def _fallback_grading(*, assignment: Assignment, submission: Submission, error: str | None = None) -> dict[str, Any]:
    score = _calculate_score(
        content=submission.content,
        has_file=bool(submission.file_path),
        max_score=assignment.max_score,
    )
    comment = "已完成自动批改（规则兜底）。"
    if error:
        comment += f" LLM 批改暂不可用，已回退到基础规则：{error[:180]}"
    data = {
        "score": score,
        "overall_comment": comment,
        "strengths": ["提交格式完整"] if submission.content or submission.file_path else [],
        "weaknesses": [] if score >= assignment.max_score * 0.6 else ["答案内容偏少，建议补充细节"],
        "annotations": [
            {
                "annotation_type": "suggestion",
                "position": {"type": "text", "paragraph": 1, "quote": (submission.content or "")[:80]},
                "content": "建议补充关键步骤、依据或示例，使答案更完整。",
                "severity": "medium",
                "knowledge_point_id": None,
            }
        ]
        if score < assignment.max_score * 0.6
        else [],
    }
    return _standardize_grading_payload(data, assignment=assignment, source="fallback")


def _grade_submission_content(*, assignment: Assignment, submission: Submission) -> dict[str, Any]:
    try:
        return asyncio.run(_grade_with_llm(assignment=assignment, submission=submission))
    except Exception as exc:
        return _fallback_grading(assignment=assignment, submission=submission, error=str(exc))


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
    """评分后更新学生的知识掌握度，并在掌握度低于阈值时创建未解决的弱点预警。"""
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

        # grading worker 是同步任务，所以在本地更新学情，避免额外引入事件同步复杂度。
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
        # 使用 EMA 平滑更新，既保留历史掌握度，也反映本次批改结果。
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
    """异步批改作业任务。"""
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

            submission.status = SubmissionStatus.GRADING
            db.flush()

            grading = _grade_submission_content(assignment=assignment, submission=submission)
            mastery_point_scores = _update_mastery_from_grading(
                db,
                student_id=submission.student_id,
                course_id=assignment.course_id,
                knowledge_point_ids=_knowledge_point_ids(assignment.knowledge_points),
                score=grading["score"],
                max_score=assignment.max_score,
            )
            knowledge_point_scores = grading.get("knowledge_point_scores") or {
                str(kp_id): score for kp_id, score in mastery_point_scores.items()
            }

            existing = db.execute(
                select(GradingResult).where(GradingResult.submission_id == submission.id)
            ).scalar_one_or_none()
            if existing:
                existing.score = grading["score"]
                existing.max_score = assignment.max_score
                existing.overall_comment = grading["overall_comment"]
                existing.strengths = grading["strengths"]
                existing.weaknesses = grading["weaknesses"]
                existing.knowledge_point_scores = knowledge_point_scores
            else:
                db.add(
                    GradingResult(
                        submission_id=submission.id,
                        score=grading["score"],
                        max_score=assignment.max_score,
                        overall_comment=grading["overall_comment"],
                        strengths=grading["strengths"],
                        weaknesses=grading["weaknesses"],
                        knowledge_point_scores=knowledge_point_scores,
                    )
                )

            submission.status = SubmissionStatus.GRADED
            db.commit()

            return {
                "submission_id": submission_id,
                "status": "graded",
                "score": grading["score"],
                "source": grading["source"],
                "annotations": grading["annotations"],
                "knowledge_point_scores": knowledge_point_scores,
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
    """批量批改某个作业的所有待批改提交。"""
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
