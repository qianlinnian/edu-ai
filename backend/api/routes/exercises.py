from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.agent_capability import get_published_course_agent_capability
from core.database import get_db
from core.permissions import ensure_course_access
from core.security import get_current_user
from education.analytics_engine import refresh_learning_alerts
from education.exercise_engine import create_attempt_and_update_mastery, generate_targeted_exercises
from models.course import Course, KnowledgeUnit
from models.exercise import ExercisePool, ExerciseType, GeneratedExercise
from models.user import User, UserRole

router = APIRouter()


class ExerciseGenRequest(BaseModel):
    course_id: int
    knowledge_point_ids: list[int] | None = None
    exercise_type: ExerciseType = ExerciseType.CHOICE
    difficulty: int = 2
    count: int = 5
    use_llm: bool = True


class ExerciseAttemptRequest(BaseModel):
    exercise_id: int | None = None
    generated_exercise_id: int | None = None
    student_answer: str


async def _load_knowledge_unit_name_map(db: AsyncSession, *, course_id: int) -> dict[int, str]:
    result = await db.execute(
        select(KnowledgeUnit.id, KnowledgeUnit.name)
        .where(KnowledgeUnit.course_id == course_id)
        .order_by(KnowledgeUnit.order_index.asc(), KnowledgeUnit.id.asc())
    )
    return {int(kp_id): str(name) for kp_id, name in result.all()}


def _map_knowledge_point_names(knowledge_point_ids: list | None, *, knowledge_unit_name_map: dict[int, str]) -> list[str]:
    names: list[str] = []
    for raw_id in knowledge_point_ids or []:
        try:
            kp_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        name = knowledge_unit_name_map.get(kp_id)
        if name:
            names.append(name)
    return names


def _serialize_pool_exercise(item: ExercisePool, *, knowledge_unit_name_map: dict[int, str]) -> dict:
    return {
        "id": item.id,
        "source": "pool",
        "type": item.exercise_type,
        "question": item.question,
        "options": item.options,
        "difficulty": item.difficulty,
        "knowledge_point_ids": item.knowledge_point_ids,
        "knowledge_point_names": _map_knowledge_point_names(
            item.knowledge_point_ids,
            knowledge_unit_name_map=knowledge_unit_name_map,
        ),
    }


async def _ensure_exercise_generation_capability(db: AsyncSession, *, course_id: int) -> None:
    capability = await get_published_course_agent_capability(db, course_id=course_id)
    if not capability.has_exercise:
        raise HTTPException(status_code=409, detail="Current course has not published exercise generation capability")


async def _resolve_attempt_course_id(
    *,
    db: AsyncSession,
    exercise_id: int | None,
    generated_exercise_id: int | None,
    user: User,
) -> int:
    if bool(exercise_id) == bool(generated_exercise_id):
        raise HTTPException(status_code=400, detail="Exactly one of exercise_id or generated_exercise_id is required")

    if exercise_id is not None:
        exercise = (await db.execute(select(ExercisePool).where(ExercisePool.id == exercise_id))).scalar_one_or_none()
        if not exercise:
            raise HTTPException(status_code=400, detail="Exercise not found")
        return exercise.course_id

    generated = (
        await db.execute(select(GeneratedExercise).where(GeneratedExercise.id == generated_exercise_id))
    ).scalar_one_or_none()
    if not generated:
        raise HTTPException(status_code=400, detail="Generated exercise not found")
    if generated.student_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to submit attempts for another student's exercise")
    return generated.course_id


@router.post("/generate")
async def generate_exercises(
    data: ExerciseGenRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate targeted exercises by student learning state and knowledge points."""
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can generate personalized exercises")

    course = (await db.execute(select(Course).where(Course.id == data.course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    await ensure_course_access(db, course=course, user=user)
    await _ensure_exercise_generation_capability(db, course_id=data.course_id)

    result = await generate_targeted_exercises(
        db,
        student_id=user.id,
        course_id=data.course_id,
        knowledge_point_ids=data.knowledge_point_ids or [],
        exercise_type=data.exercise_type,
        difficulty=data.difficulty,
        count=data.count,
        use_llm=data.use_llm,
    )
    knowledge_unit_name_map = await _load_knowledge_unit_name_map(db, course_id=data.course_id)
    exercises = [
        {
            **item,
            "knowledge_point_names": _map_knowledge_point_names(
                item.get("knowledge_point_ids"),
                knowledge_unit_name_map=knowledge_unit_name_map,
            ),
        }
        for item in result["exercises"]
    ]
    return {
        "message": f"Generated {len(exercises)} exercises",
        "exercises": exercises,
        "source": result["source"],
        "generation_method": result["generation_method"],
        "target_knowledge_points": result["target_knowledge_points"],
        "source_summary": result["source_summary"],
        "fallback_used": result["fallback_used"],
    }


@router.post("/attempt")
async def submit_attempt(
    data: ExerciseAttemptRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit attempt, auto-grade it, and update mastery."""
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit exercise attempts")

    course_id = await _resolve_attempt_course_id(
        db=db,
        exercise_id=data.exercise_id,
        generated_exercise_id=data.generated_exercise_id,
        user=user,
    )
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    await ensure_course_access(db, course=course, user=user)

    try:
        attempt = await create_attempt_and_update_mastery(
            db,
            student_id=user.id,
            exercise_id=data.exercise_id,
            generated_exercise_id=data.generated_exercise_id,
            student_answer=data.student_answer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Refresh weak-point alerts after each attempt.
    refreshed_alerts = 0
    course_id: int | None = None
    if attempt.exercise_id:
        exercise = (
            await db.execute(select(ExercisePool).where(ExercisePool.id == attempt.exercise_id))
        ).scalar_one_or_none()
        if exercise:
            course_id = exercise.course_id
            refreshed_alerts = await refresh_learning_alerts(db, course_id=exercise.course_id, student_id=user.id)
    elif attempt.generated_exercise_id:
        generated = (
            await db.execute(select(GeneratedExercise).where(GeneratedExercise.id == attempt.generated_exercise_id))
        ).scalar_one_or_none()
        if generated:
            course_id = generated.course_id
            refreshed_alerts = await refresh_learning_alerts(db, course_id=generated.course_id, student_id=user.id)

    return {
        "id": attempt.id,
        "is_correct": attempt.is_correct,
        "score": attempt.score,
        "feedback": attempt.feedback,
        "course_id": course_id,
        "mastery_updated": True,
        "alerts_refreshed": refreshed_alerts,
    }


@router.get("/pool")
async def list_exercise_pool(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List course exercise pool."""
    course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    await ensure_course_access(db, course=course, user=user)

    result = await db.execute(
        select(ExercisePool).where(ExercisePool.course_id == course_id).order_by(ExercisePool.created_at.desc())
    )
    knowledge_unit_name_map = await _load_knowledge_unit_name_map(db, course_id=course_id)
    return [
        _serialize_pool_exercise(item, knowledge_unit_name_map=knowledge_unit_name_map)
        for item in result.scalars().all()
    ]
