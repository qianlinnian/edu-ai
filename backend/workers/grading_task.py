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
from workers.embedding_task import get_minio_client, parse_resource_content

settings = get_settings()
sync_engine = create_engine(settings.DATABASE_SYNC_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)
MAX_GRADING_CONTENT_CHARS = 12000


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
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return json.loads(text)


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


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
            response.close()
            response.release_conn()


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
    return (
        f"作业标题：{assignment.title}\n"
        f"作业说明：{assignment.description or '无'}\n"
        f"作业类型：{assignment.assignment_type}\n"
        f"满分：{assignment.max_score}\n"
        f"作业补充信息：\n"
        f"- 评分标准：{rubric_text}\n"
        f"- 参考答案：{reference_answer}"
    )


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
                "你是教学平台的自动批改助手。请根据作业题目、评分标准、参考答案和学生提交内容进行评分。"
                "必须只返回 JSON，不要返回 markdown，不要添加解释性前后缀。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"{assignment_context}\n"
                f"{file_note}\n\n"
                f"学生提交内容（包含文本提交和可解析附件内容）：\n{content or '无可解析文本内容'}\n\n"
                "请返回如下 JSON："
                "{"
                '"score": 0 到满分之间的数字, '
                '"overall_comment": "总体评价", '
                '"strengths": ["优点1"], '
                '"weaknesses": ["不足1"]'
                "}"
            ),
        },
    ]
    raw = await provider.chat(messages, temperature=0.2)
    data = _safe_json_loads(raw)
    score = float(data.get("score", 0.0))
    score = round(min(max(score, 0.0), float(assignment.max_score)), 2)
    return {
        "score": score,
        "overall_comment": str(data.get("overall_comment") or "已完成自动批改。"),
        "strengths": _normalize_list(data.get("strengths")),
        "weaknesses": _normalize_list(data.get("weaknesses")),
        "source": "llm",
    }


def _fallback_grading(*, assignment: Assignment, submission: Submission, error: str | None = None) -> dict[str, Any]:
    score = _calculate_score(
        content=submission.content,
        has_file=bool(submission.file_path),
        max_score=assignment.max_score,
    )
    comment = "已完成自动批改（规则兜底）。"
    if error:
        comment += f" LLM 批改暂不可用，已回退到基础规则：{error[:180]}"
    return {
        "score": score,
        "overall_comment": comment,
        "strengths": ["提交格式完整"] if submission.content or submission.file_path else [],
        "weaknesses": [] if score >= assignment.max_score * 0.6 else ["答案内容偏少，建议补充细节"],
        "source": "fallback",
    }


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
            knowledge_point_scores = _update_mastery_from_grading(
                db,
                student_id=submission.student_id,
                course_id=assignment.course_id,
                knowledge_point_ids=_knowledge_point_ids(assignment.knowledge_points),
                score=grading["score"],
                max_score=assignment.max_score,
            )

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
