from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.exercise import ExerciseAttempt, ExercisePool, ExerciseType, GeneratedExercise
from models.learning import StudentKnowledgeMastery


@dataclass
class AttemptEvaluation:
    course_id: int
    knowledge_point_ids: list[int]
    is_correct: bool
    score: float
    feedback: str


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
    score_ratio = min(max(score / 100.0, 0.0), 1.0)

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
                mastery_score=0.5,
                attempt_count=0,
                correct_count=0,
            )
            db.add(mastery)
            await db.flush()

        mastery.attempt_count += 1
        mastery.correct_count += 1 if is_correct else 0
        outcome = score_ratio if is_correct else max(score_ratio * 0.5, 0.0)
        # EMA smoothing keeps history and latest attempt balanced.
        mastery.mastery_score = round(min(max(mastery.mastery_score * 0.7 + outcome * 0.3, 0.0), 1.0), 4)
        mastery.last_assessed_at = now


async def generate_targeted_exercises(
    db: AsyncSession,
    *,
    student_id: int,
    course_id: int,
    knowledge_point_ids: list[int],
    exercise_type: ExerciseType,
    difficulty: int,
    count: int,
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(ExercisePool).where(
            ExercisePool.course_id == course_id,
            ExercisePool.exercise_type == exercise_type,
        )
    )
    candidates = result.scalars().all()
    target_kps = set(knowledge_point_ids)
    filtered = [
        item
        for item in candidates
        if abs(int(item.difficulty) - int(difficulty)) <= 1
        and bool(set(int(kp) for kp in item.knowledge_point_ids) & target_kps)
    ]

    chosen = filtered[:count]
    if len(chosen) >= count:
        return [
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
            question=f"Explain the core concept of knowledge points {knowledge_point_ids} (auto item {index + 1})",
            options=None,
            answer="Include definition, key features, and one example.",
            explanation="Auto-generated fallback exercise for weak-point practice.",
            target_knowledge_points=knowledge_point_ids,
            difficulty=difficulty,
        )
        db.add(generated)
        await db.flush()
        output.append(
            {
                "id": generated.id,
                "source": "generated",
                "type": generated.exercise_type,
                "question": generated.question,
                "options": generated.options,
                "difficulty": generated.difficulty,
                "knowledge_point_ids": generated.target_knowledge_points,
            }
        )

    return output
