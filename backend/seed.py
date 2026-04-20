from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import models  # noqa: F401  # 触发表注册
from core.config import get_settings
from core.security import hash_password
from models.course import Course, Enrollment, KnowledgeRelation, KnowledgeUnit
from models.user import User, UserRole

settings = get_settings()
engine = create_engine(settings.DATABASE_SYNC_URL)
SessionLocal = sessionmaker(bind=engine)


def get_or_create_user(
    session: Session,
    *,
    username: str,
    email: str,
    full_name: str,
    role: UserRole,
    password: str = "123456",
) -> User:
    user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user:
        return user

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    session.add(user)
    session.flush()
    return user


def get_or_create_course(
    session: Session,
    *,
    name: str,
    code: str,
    description: str,
    domain: str,
    teacher_id: int,
) -> Course:
    course = session.execute(select(Course).where(Course.code == code)).scalar_one_or_none()
    if course:
        return course

    course = Course(
        name=name,
        code=code,
        description=description,
        domain=domain,
        teacher_id=teacher_id,
    )
    session.add(course)
    session.flush()
    return course


def ensure_enrollment(session: Session, student_id: int, course_id: int) -> None:
    existing = session.execute(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        )
    ).scalar_one_or_none()
    if not existing:
        session.add(Enrollment(student_id=student_id, course_id=course_id))


def ensure_java_knowledge_graph(session: Session, java_course: Course) -> None:
    kp_data = [
        ("类与对象", "类的定义、对象创建、构造方法", 1),
        ("封装", "访问控制修饰符、getter/setter方法", 2),
        ("继承", "extends关键字、方法重写、super关键字", 2),
        ("多态", "向上转型、动态绑定、接口实现", 3),
        ("异常处理", "try-catch-finally、自定义异常类", 2),
        ("集合框架", "ArrayList、HashMap、迭代器模式", 3),
    ]

    existing_units = {
        item.name: item
        for item in session.execute(
            select(KnowledgeUnit).where(KnowledgeUnit.course_id == java_course.id)
        ).scalars()
    }

    ordered_units: list[KnowledgeUnit] = []
    for index, (name, description, difficulty) in enumerate(kp_data):
        unit = existing_units.get(name)
        if not unit:
            unit = KnowledgeUnit(
                course_id=java_course.id,
                name=name,
                description=description,
                domain="Java编程",
                difficulty=difficulty,
                order_index=index,
            )
            session.add(unit)
            session.flush()
        ordered_units.append(unit)

    relations = [
        (ordered_units[0].id, ordered_units[1].id, "prerequisite"),
        (ordered_units[0].id, ordered_units[2].id, "prerequisite"),
        (ordered_units[2].id, ordered_units[3].id, "prerequisite"),
    ]

    for source_id, target_id, relation_type in relations:
        existing = session.execute(
            select(KnowledgeRelation).where(
                KnowledgeRelation.source_id == source_id,
                KnowledgeRelation.target_id == target_id,
                KnowledgeRelation.relation_type == relation_type,
            )
        ).scalar_one_or_none()
        if not existing:
            session.add(
                KnowledgeRelation(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                )
            )


def seed() -> None:
    with SessionLocal() as session:
        try:
            teacher = get_or_create_user(
                session,
                username="teacher_zhang",
                email="zhang@edu.com",
                full_name="张伟老师",
                role=UserRole.TEACHER,
            )

            students = [
                get_or_create_user(
                    session,
                    username=f"student_{index:02d}",
                    email=f"student{index:02d}@edu.com",
                    full_name=f"学生{index:02d}号",
                    role=UserRole.STUDENT,
                )
                for index in range(1, 11)
            ]

            java_course = get_or_create_course(
                session,
                name="面向对象程序设计（Java）",
                code="CS101",
                description="学习Java面向对象核心概念",
                domain="计算机科学",
                teacher_id=teacher.id,
            )
            intro_course = get_or_create_course(
                session,
                name="计算机科学与技术专业导论",
                code="CS100",
                description="了解计算机科学的基础方向",
                domain="计算机科学",
                teacher_id=teacher.id,
            )
            ds_course = get_or_create_course(
                session,
                name="数据结构与算法",
                code="CS201",
                description="常用数据结构和算法设计",
                domain="计算机科学",
                teacher_id=teacher.id,
            )

            for student in students:
                for course in (java_course, intro_course, ds_course):
                    ensure_enrollment(session, student.id, course.id)

            ensure_java_knowledge_graph(session, java_course)

            session.commit()
            print("✅ 种子数据写入成功")
            print(f"   教师: {teacher.username}")
            print(f"   学生: {len(students)}")
            print("   课程: CS100 / CS101 / CS201")
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    seed()
