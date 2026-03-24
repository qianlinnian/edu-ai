from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.exercise import ExercisePool, GeneratedExercise, ExerciseAttempt, ExerciseType

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
    data: ExerciseGenRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """根据薄弱知识点生成练习题"""
    # TODO: 先从题库匹配，不足时调用LLM生成
    # from education.exercise_generator import generate_targeted_exercises
    # exercises = await generate_targeted_exercises(data)

    # 临时模拟
    return {
        "message": f"已生成{data.count}道练习题",
        "exercises": [
            {
                "id": i,
                "type": data.exercise_type,
                "question": f"[模拟] 关于知识点{data.knowledge_point_ids}的第{i+1}题",
                "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"] if data.exercise_type == ExerciseType.CHOICE else None,
            }
            for i in range(data.count)
        ],
    }


@router.post("/attempt")
async def submit_attempt(
    data: ExerciseAttemptRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """提交练习作答"""
    # TODO: 自动评判并更新掌握度
    attempt = ExerciseAttempt(
        student_id=user.id,
        exercise_id=data.exercise_id,
        generated_exercise_id=data.generated_exercise_id,
        student_answer=data.student_answer,
        is_correct=False,  # TODO: 自动判断
        score=0.0,
    )
    db.add(attempt)
    await db.flush()
    await db.refresh(attempt)
    return {"id": attempt.id, "is_correct": attempt.is_correct, "feedback": "评判模块开发中..."}


@router.get("/pool")
async def list_exercise_pool(course_id: int, db: AsyncSession = Depends(get_db)):
    """获取课程题库"""
    result = await db.execute(
        select(ExercisePool).where(ExercisePool.course_id == course_id).order_by(ExercisePool.created_at.desc())
    )
    return result.scalars().all()
