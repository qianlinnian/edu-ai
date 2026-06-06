from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.normalization import extract_json_value
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_core.llm_provider import get_llm_provider
from models.course import Course, KnowledgeUnit
from models.exercise import ExerciseAttempt, ExercisePool, ExerciseType, GeneratedExercise
from models.learning import StudentKnowledgeMastery


@dataclass
class AttemptEvaluation:
    course_id: int
    knowledge_point_ids: list[int]
    is_correct: bool
    score: float
    feedback: str


DEFAULT_INITIAL_MASTERY = 0.5
EMA_HISTORY_WEIGHT = 0.7
EMA_LATEST_WEIGHT = 0.3
MIN_GENERATION_COUNT = 1
MAX_GENERATION_COUNT = 10


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _judge_answer(exercise_type: ExerciseType, expected: str, actual: str) -> tuple[bool, float]:
    expected_norm = _normalize_text(expected)
    actual_norm = _normalize_text(actual)
    if not expected_norm:
        return False, 0.0

    if exercise_type in {ExerciseType.CHOICE, ExerciseType.FILL_BLANK}:
        is_correct = expected_norm == actual_norm
        return is_correct, 1.0 if is_correct else 0.0

    if exercise_type in {ExerciseType.SHORT_ANSWER, ExerciseType.CODING}:
        expected_tokens = set(expected_norm.split())
        actual_tokens = set(actual_norm.split())
        if not expected_tokens:
            return False, 0.0
        overlap = len(expected_tokens & actual_tokens) / len(expected_tokens)
        score = min(max(overlap, 0.0), 1.0)
        return score >= 0.6, round(score, 3)

    return False, 0.0


async def evaluate_attempt(
    db: AsyncSession,
    *,
    exercise_id: int | None,
    generated_exercise_id: int | None,
    student_answer: str,
) -> AttemptEvaluation:
    if bool(exercise_id) == bool(generated_exercise_id):
        raise ValueError("Exactly one of exercise_id or generated_exercise_id is required")

    if exercise_id:
        result = await db.execute(select(ExercisePool).where(ExercisePool.id == exercise_id))
        exercise = result.scalar_one_or_none()
        if not exercise:
            raise ValueError("Exercise not found")
        source_course_id = exercise.course_id
        kp_ids = [int(kp) for kp in exercise.knowledge_point_ids]
        ex_type = exercise.exercise_type
        expected_answer = exercise.answer
    else:
        result = await db.execute(select(GeneratedExercise).where(GeneratedExercise.id == generated_exercise_id))
        exercise = result.scalar_one_or_none()
        if not exercise:
            raise ValueError("Generated exercise not found")
        source_course_id = exercise.course_id
        kp_ids = [int(kp) for kp in exercise.target_knowledge_points]
        ex_type = exercise.exercise_type
        expected_answer = exercise.answer

    is_correct, score_ratio = _judge_answer(ex_type, expected_answer, student_answer)
    feedback = "Correct answer" if is_correct else "Answer is below target. Review related knowledge points and retry."

    return AttemptEvaluation(
        course_id=source_course_id,
        knowledge_point_ids=kp_ids,
        is_correct=is_correct,
        score=round(score_ratio * 100, 2),
        feedback=feedback,
    )


async def create_attempt_and_update_mastery(
    db: AsyncSession,
    *,
    student_id: int,
    exercise_id: int | None,
    generated_exercise_id: int | None,
    student_answer: str,
) -> ExerciseAttempt:
    evaluation = await evaluate_attempt(
        db,
        exercise_id=exercise_id,
        generated_exercise_id=generated_exercise_id,
        student_answer=student_answer,
    )

    attempt = ExerciseAttempt(
        student_id=student_id,
        exercise_id=exercise_id,
        generated_exercise_id=generated_exercise_id,
        student_answer=student_answer,
        is_correct=evaluation.is_correct,
        score=evaluation.score,
        feedback=evaluation.feedback,
    )
    db.add(attempt)
    await db.flush()

    await _update_mastery(
        db,
        student_id=student_id,
        knowledge_point_ids=evaluation.knowledge_point_ids,
        is_correct=evaluation.is_correct,
        score=evaluation.score,
    )

    await db.refresh(attempt)
    return attempt


async def _update_mastery(
    db: AsyncSession,
    *,
    student_id: int,
    knowledge_point_ids: list[int],
    is_correct: bool,
    score: float,
) -> None:
    if not knowledge_point_ids:
        return

    now = datetime.now(timezone.utc)
    score_ratio = normalize_score_ratio(score)

    for kp_id in knowledge_point_ids:
        result = await db.execute(
            select(StudentKnowledgeMastery).where(
                StudentKnowledgeMastery.student_id == student_id,
                StudentKnowledgeMastery.knowledge_unit_id == kp_id,
            )
        )
        mastery = result.scalar_one_or_none()
        if mastery is None:
            mastery = StudentKnowledgeMastery(
                student_id=student_id,
                knowledge_unit_id=kp_id,
                mastery_score=DEFAULT_INITIAL_MASTERY,
                attempt_count=0,
                correct_count=0,
            )
            db.add(mastery)
            await db.flush()

        apply_mastery_update(mastery, score_ratio=score_ratio, is_correct=is_correct, assessed_at=now)


def normalize_score_ratio(score: float) -> float:
    return min(max(score / 100.0, 0.0), 1.0)


def derive_mastery_outcome(*, score_ratio: float, is_correct: bool) -> float:
    if is_correct:
        return score_ratio
    return max(score_ratio * 0.5, 0.0)


def blend_mastery_score(*, previous_mastery: float, outcome: float) -> float:
    return round(
        min(max(previous_mastery * EMA_HISTORY_WEIGHT + outcome * EMA_LATEST_WEIGHT, 0.0), 1.0),
        4,
    )


def apply_mastery_update(
    mastery: StudentKnowledgeMastery,
    *,
    score_ratio: float,
    is_correct: bool,
    assessed_at: datetime,
) -> None:
    mastery.attempt_count += 1
    mastery.correct_count += 1 if is_correct else 0
    outcome = derive_mastery_outcome(score_ratio=score_ratio, is_correct=is_correct)
    mastery.mastery_score = blend_mastery_score(previous_mastery=mastery.mastery_score, outcome=outcome)
    mastery.last_assessed_at = assessed_at


def _clamp_int(value: int, *, minimum: int, maximum: int) -> int:
    return min(max(int(value), minimum), maximum)


def _safe_json_loads(raw: str) -> Any:
    return extract_json_value(raw)


def _normalize_choice_options(options: Any) -> list[dict[str, str]]:
    if not isinstance(options, list):
        return []

    normalized: list[dict[str, str]] = []
    for index, option in enumerate(options[:6]):
        default_key = chr(65 + index)
        if isinstance(option, str):
            text = option.strip()
            key_match = re.match(r"^([A-Fa-f])[\.\、\s]+(.+)$", text)
            if key_match:
                key = key_match.group(1).upper()
                label = key_match.group(2).strip()
            else:
                key = default_key
                label = text
        elif isinstance(option, dict):
            key = str(option.get("key") or option.get("value") or default_key).strip().upper()
            label = str(option.get("label") or option.get("text") or option.get("content") or "").strip()
        else:
            continue

        if label:
            normalized.append({"key": key[:1] or default_key, "label": label})

    return normalized


def _normalize_generated_item(
    item: Any,
    *,
    fallback_knowledge_point_ids: list[int],
    fallback_difficulty: int,
    exercise_type: ExerciseType,
) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    question = str(item.get("question") or item.get("stem") or item.get("title") or "").strip()
    if not question:
        return None

    answer = str(item.get("answer") or item.get("correct_answer") or "").strip()
    explanation = str(item.get("explanation") or item.get("analysis") or item.get("feedback") or "").strip()
    difficulty = _clamp_int(int(item.get("difficulty") or fallback_difficulty), minimum=1, maximum=5)

    kp_values = item.get("knowledge_point_ids") or item.get("target_knowledge_points") or fallback_knowledge_point_ids
    if not isinstance(kp_values, list):
        kp_values = fallback_knowledge_point_ids
    knowledge_point_ids = []
    for kp in kp_values:
        try:
            kp_id = int(kp)
        except (TypeError, ValueError):
            continue
        if kp_id not in knowledge_point_ids:
            knowledge_point_ids.append(kp_id)
    if not knowledge_point_ids:
        knowledge_point_ids = fallback_knowledge_point_ids

    options = _normalize_choice_options(item.get("options") or item.get("choices"))
    if exercise_type == ExerciseType.CHOICE:
        if len(options) < 2:
            return None
        if answer:
            answer = answer.strip().upper()[:1]
        if answer not in {option["key"] for option in options}:
            answer = options[0]["key"]
    elif not answer:
        return None

    return {
        "question": question,
        "options": options if exercise_type == ExerciseType.CHOICE else None,
        "answer": answer,
        "explanation": explanation or "请结合相关知识点复习本题。",
        "difficulty": difficulty,
        "knowledge_point_ids": knowledge_point_ids,
    }


async def _get_course_context(db: AsyncSession, *, course_id: int) -> Course | None:
    return (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()


async def _get_knowledge_context(
    db: AsyncSession,
    *,
    course_id: int,
    student_id: int,
    knowledge_point_ids: list[int],
    limit: int = 6,
) -> list[dict[str, Any]]:
    if knowledge_point_ids:
        result = await db.execute(
            select(KnowledgeUnit, StudentKnowledgeMastery)
            .outerjoin(
                StudentKnowledgeMastery,
                (StudentKnowledgeMastery.knowledge_unit_id == KnowledgeUnit.id)
                & (StudentKnowledgeMastery.student_id == student_id),
            )
            .where(KnowledgeUnit.course_id == course_id, KnowledgeUnit.id.in_(knowledge_point_ids))
            .order_by(KnowledgeUnit.order_index.asc(), KnowledgeUnit.id.asc())
        )
    else:
        result = await db.execute(
            select(KnowledgeUnit, StudentKnowledgeMastery)
            .outerjoin(
                StudentKnowledgeMastery,
                (StudentKnowledgeMastery.knowledge_unit_id == KnowledgeUnit.id)
                & (StudentKnowledgeMastery.student_id == student_id),
            )
            .where(KnowledgeUnit.course_id == course_id)
            .order_by(StudentKnowledgeMastery.mastery_score.asc().nullsfirst(), KnowledgeUnit.difficulty.desc())
            .limit(limit)
        )

    context: list[dict[str, Any]] = []
    for unit, mastery in result.all():
        mastery_score = float(mastery.mastery_score) if mastery else DEFAULT_INITIAL_MASTERY
        context.append(
            {
                "id": unit.id,
                "name": unit.name,
                "description": unit.description or "",
                "difficulty": unit.difficulty,
                "mastery_score": round(mastery_score, 4),
                "attempt_count": int(mastery.attempt_count) if mastery else 0,
                "correct_count": int(mastery.correct_count) if mastery else 0,
            }
        )
    return context


async def _get_recent_generated_questions(
    db: AsyncSession,
    *,
    student_id: int,
    course_id: int,
    limit: int = 5,
) -> list[str]:
    result = await db.execute(
        select(GeneratedExercise.question)
        .where(GeneratedExercise.student_id == student_id, GeneratedExercise.course_id == course_id)
        .order_by(desc(GeneratedExercise.created_at))
        .limit(limit)
    )
    return [str(question) for question in result.scalars().all() if question]


def _build_exercise_generation_prompt(
    *,
    course: Course | None,
    knowledge_context: list[dict[str, Any]],
    recent_questions: list[str],
    exercise_type: ExerciseType,
    difficulty: int,
    count: int,
) -> list[dict[str, str]]:
    course_name = course.name if course else f"课程 {knowledge_context[0]['id'] if knowledge_context else ''}"
    course_domain = course.domain if course else ""
    payload = {
        "course": {"name": course_name, "domain": course_domain},
        "target_exercise_type": exercise_type.value,
        "target_difficulty": difficulty,
        "count": count,
        "student_learning_state": knowledge_context,
        "recent_generated_questions_to_avoid": recent_questions,
    }
    return [
        {
            "role": "system",
            "content": (
                "你是教学练习题生成助手。请根据学生薄弱知识点生成中文个性化练习题。"
                "必须只返回 JSON，不要返回 Markdown 或额外解释。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请根据下面 JSON 生成练习题。返回格式必须为数组，每个元素包含："
                "question, options, answer, explanation, knowledge_point_ids, difficulty。"
                "如果是 choice 题，options 必须是 [{\"key\":\"A\",\"label\":\"...\"}] 形式，answer 必须是 A/B/C/D。"
                "题目要面向薄弱点，避免 recent_generated_questions_to_avoid 中的重复题。\n"
                f"{json.dumps(payload, ensure_ascii=False)}"
            ),
        },
    ]


async def _generate_exercises_with_llm(
    db: AsyncSession,
    *,
    student_id: int,
    course_id: int,
    knowledge_context: list[dict[str, Any]],
    exercise_type: ExerciseType,
    difficulty: int,
    count: int,
) -> list[dict[str, Any]]:
    if not knowledge_context:
        return []

    course = await _get_course_context(db, course_id=course_id)
    recent_questions = await _get_recent_generated_questions(db, student_id=student_id, course_id=course_id)
    target_kps = [int(item["id"]) for item in knowledge_context]
    messages = _build_exercise_generation_prompt(
        course=course,
        knowledge_context=knowledge_context,
        recent_questions=recent_questions,
        exercise_type=exercise_type,
        difficulty=difficulty,
        count=count,
    )

    provider = get_llm_provider()
    raw = await provider.chat(messages, temperature=0.3)
    parsed = _safe_json_loads(raw)
    items = parsed.get("exercises", parsed.get("items", [])) if isinstance(parsed, dict) else parsed
    if not isinstance(items, list):
        return []

    output: list[dict[str, Any]] = []
    for item in items:
        normalized = _normalize_generated_item(
            item,
            fallback_knowledge_point_ids=target_kps,
            fallback_difficulty=difficulty,
            exercise_type=exercise_type,
        )
        if normalized:
            output.append(normalized)
        if len(output) >= count:
            break
    return output


def _serialize_generated_exercise(item: GeneratedExercise, *, generation_method: str = "llm") -> dict[str, Any]:
    return {
        "id": item.id,
        "source": "generated",
        "generation_method": generation_method,
        "type": item.exercise_type,
        "question": item.question,
        "options": item.options,
        "answer": item.answer,
        "explanation": item.explanation,
        "difficulty": item.difficulty,
        "knowledge_point_ids": item.target_knowledge_points,
        "generated_exercise_id": item.id,
    }


async def generate_targeted_exercises(
    db: AsyncSession,
    *,
    student_id: int,
    course_id: int,
    knowledge_point_ids: list[int],
    exercise_type: ExerciseType,
    difficulty: int,
    count: int,
    use_llm: bool = True,
) -> list[dict[str, Any]]:
    count = _clamp_int(count, minimum=MIN_GENERATION_COUNT, maximum=MAX_GENERATION_COUNT)
    difficulty = _clamp_int(difficulty, minimum=1, maximum=5)
    knowledge_context = await _get_knowledge_context(
        db,
        course_id=course_id,
        student_id=student_id,
        knowledge_point_ids=knowledge_point_ids,
    )
    target_kps = [int(item["id"]) for item in knowledge_context] or knowledge_point_ids
    target_summary = [
        {
            "knowledge_unit_id": int(item["id"]),
            "name": item["name"],
            "mastery_score": item["mastery_score"],
            "attempt_count": item["attempt_count"],
        }
        for item in knowledge_context
    ]

    if use_llm and target_kps:
        try:
            llm_items = await _generate_exercises_with_llm(
                db,
                student_id=student_id,
                course_id=course_id,
                knowledge_context=knowledge_context,
                exercise_type=exercise_type,
                difficulty=difficulty,
                count=count,
            )
        except Exception:
            llm_items = []

        if llm_items:
            output: list[dict[str, Any]] = []
            for item in llm_items:
                generated = GeneratedExercise(
                    student_id=student_id,
                    course_id=course_id,
                    exercise_type=exercise_type,
                    question=item["question"],
                    options=item["options"],
                    answer=item["answer"],
                    explanation=item["explanation"],
                    target_knowledge_points=item["knowledge_point_ids"],
                    difficulty=item["difficulty"],
                )
                db.add(generated)
                await db.flush()
                output.append(_serialize_generated_exercise(generated, generation_method="llm"))
            return {
                "exercises": output,
                "source": "generated",
                "generation_method": "llm",
                "target_knowledge_points": target_summary,
                "source_summary": {"llm": len(output), "pool": 0, "fallback": 0},
                "fallback_used": False,
            }

    result = await db.execute(
        select(ExercisePool).where(
            ExercisePool.course_id == course_id,
            ExercisePool.exercise_type == exercise_type,
        )
    )
    candidates = result.scalars().all()
    target_kp_set = set(target_kps)
    filtered = [
        item
        for item in candidates
        if abs(int(item.difficulty) - int(difficulty)) <= 1
        and bool(set(int(kp) for kp in item.knowledge_point_ids) & target_kp_set)
    ]

    chosen = filtered[:count]
    if len(chosen) >= count:
        output = [
            {
                "id": item.id,
                "source": "pool",
                "type": item.exercise_type,
                "question": item.question,
                "options": item.options,
                "difficulty": item.difficulty,
                "knowledge_point_ids": item.knowledge_point_ids,
            }
            for item in chosen
        ]
        return {
            "exercises": output,
            "source": "pool",
            "generation_method": "pool_recommendation",
            "target_knowledge_points": target_summary,
            "source_summary": {"llm": 0, "pool": len(output), "fallback": 0},
            "fallback_used": False,
        }

    output: list[dict[str, Any]] = [
        {
            "id": item.id,
            "source": "pool",
            "type": item.exercise_type,
            "question": item.question,
            "options": item.options,
            "difficulty": item.difficulty,
            "knowledge_point_ids": item.knowledge_point_ids,
        }
        for item in chosen
    ]

    missing_count = count - len(output)
    for index in range(missing_count):
        generated = GeneratedExercise(
            student_id=student_id,
            course_id=course_id,
            exercise_type=exercise_type,
            question=f"请说明知识点 {target_kps} 的核心概念，并结合一个简单例子解释。（自动兜底题 {index + 1}）",
            options=None if exercise_type != ExerciseType.CHOICE else [
                {"key": "A", "label": "能够准确解释核心概念并举例"},
                {"key": "B", "label": "只需要写出知识点名称"},
                {"key": "C", "label": "不需要结合例子"},
                {"key": "D", "label": "与该知识点无关也可以"},
            ],
            answer="A" if exercise_type == ExerciseType.CHOICE else "应包含概念定义、关键特征和一个示例。",
            explanation="这是 AI 生成失败后的兜底练习，用于保持薄弱点练习链路可用。",
            target_knowledge_points=target_kps,
            difficulty=difficulty,
        )
        db.add(generated)
        await db.flush()
        output.append(_serialize_generated_exercise(generated, generation_method="fallback"))

    fallback_count = sum(1 for item in output if item.get("generation_method") == "fallback")
    pool_count = sum(1 for item in output if item.get("source") == "pool")
    return {
        "exercises": output,
        "source": output[0]["source"] if output else "empty",
        "generation_method": "fallback" if fallback_count else "pool_recommendation",
        "target_knowledge_points": target_summary,
        "source_summary": {"llm": 0, "pool": pool_count, "fallback": fallback_count},
        "fallback_used": fallback_count > 0,
    }
