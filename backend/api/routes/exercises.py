from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from education.analytics_engine import refresh_learning_alerts
from education.exercise_engine import create_attempt_and_update_mastery, generate_targeted_exercises
from models.exercise import ExercisePool, ExerciseType, GeneratedExercise
from models.user import User

router = APIRouter()


class ExerciseGenRequest(BaseModel):
    course_id: int
    knowledge_point_ids: list[int]
    exercise_type: ExerciseType = ExerciseType.CHOICE
    difficulty: int = 2
    count: int = 5


class ExerciseAttemptRequest(BaseModel):
    exercise_id: int | None = None
    generated_exercise_id: int | None = None
    student_answer: str


@router.post("/generate")
async def generate_exercises(
    data: ExerciseGenRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate targeted exercises by course and knowledge points."""
    exercises = await generate_targeted_exercises(
        db,
        student_id=user.id,
        course_id=data.course_id,
        knowledge_point_ids=data.knowledge_point_ids,
        exercise_type=data.exercise_type,
        difficulty=data.difficulty,
        count=data.count,
    )
    return {
        "message": f"Generated {len(exercises)} exercises",
        "exercises": exercises,
    }


@router.post("/attempt")
async def submit_attempt(
    data: ExerciseAttemptRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit attempt, auto-grade it, and update mastery."""
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
    if attempt.exercise_id:
        exercise = (
            await db.execute(select(ExercisePool).where(ExercisePool.id == attempt.exercise_id))
        ).scalar_one_or_none()
        if exercise:
            await refresh_learning_alerts(db, course_id=exercise.course_id, student_id=user.id)
    elif attempt.generated_exercise_id:
        generated = (
            await db.execute(select(GeneratedExercise).where(GeneratedExercise.id == attempt.generated_exercise_id))
        ).scalar_one_or_none()
        if generated:
            await refresh_learning_alerts(db, course_id=generated.course_id, student_id=user.id)

    return {
        "id": attempt.id,
        "is_correct": attempt.is_correct,
        "score": attempt.score,
        "feedback": attempt.feedback,
    }


@router.get("/pool")
async def list_exercise_pool(course_id: int, db: AsyncSession = Depends(get_db)):
    """List course exercise pool."""
    result = await db.execute(
        select(ExercisePool).where(ExercisePool.course_id == course_id).order_by(ExercisePool.created_at.desc())
    )
    return result.scalars().all()
