import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class ExerciseType(str, enum.Enum):
    CHOICE = "choice"          # 选择题
    FILL_BLANK = "fill_blank"  # 填空题
    SHORT_ANSWER = "short_answer"  # 简答题
    CODING = "coding"          # 编程题


class ExercisePool(Base):
    __tablename__ = "exercise_pool"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    exercise_type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)  # 选择题选项
    answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    knowledge_point_ids: Mapped[list] = mapped_column(JSON)  # 关联知识点
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False)  # AI生成 or 人工录入
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class GeneratedExercise(Base):
    __tablename__ = "generated_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    exercise_type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType))
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_knowledge_points: Mapped[list] = mapped_column(JSON)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    exercise_id: Mapped[int | None] = mapped_column(ForeignKey("exercise_pool.id"), nullable=True)
    generated_exercise_id: Mapped[int | None] = mapped_column(ForeignKey("generated_exercises.id"), nullable=True)
    student_answer: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
