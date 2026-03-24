import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    GRADING = "grading"
    GRADED = "graded"
    FAILED = "failed"


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignment_type: Mapped[str] = mapped_column(String(50))  # text, code, image, mixed
    max_score: Mapped[float] = mapped_column(Float, default=100.0)
    rubric: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 评分标准
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    knowledge_points: Mapped[list | None] = mapped_column(JSON, nullable=True)  # 关联知识点ID列表
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # 文本/代码内容
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 文件提交路径
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class GradingResult(Base):
    __tablename__ = "grading_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), unique=True, index=True)
    score: Mapped[float] = mapped_column(Float)
    max_score: Mapped[float] = mapped_column(Float)
    overall_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    knowledge_point_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {kp_id: score}
    graded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SubmissionAnnotation(Base):
    __tablename__ = "submission_annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    annotation_type: Mapped[str] = mapped_column(String(50))  # error, warning, suggestion, praise
    position: Mapped[dict] = mapped_column(JSON)  # {paragraph, offset, length} 或 {line, col}
    content: Mapped[str] = mapped_column(Text)  # 批注内容
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, critical
    knowledge_point_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_units.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
