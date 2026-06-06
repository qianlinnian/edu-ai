from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.assignment import Submission
from models.course import Course, Enrollment
from models.user import User, UserRole


async def ensure_course_access(db: AsyncSession, *, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    if user.role == UserRole.STUDENT:
        result = await db.execute(
            select(Enrollment.id).where(Enrollment.course_id == course.id, Enrollment.student_id == user.id)
        )
        if result.scalar_one_or_none() is not None:
            return
    raise HTTPException(status_code=403, detail="Not allowed to access this course")


def ensure_course_manager(*, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Teacher or admin access required")


def ensure_student_or_teacher_access(*, course: Course, student_id: int, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    if user.role == UserRole.STUDENT and user.id == student_id:
        return
    raise HTTPException(status_code=403, detail="Not allowed to access this student analytics")


def ensure_submission_access(*, submission: Submission, course: Course, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and course.teacher_id == user.id:
        return
    if user.role == UserRole.STUDENT and submission.student_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Not allowed to access this submission")
