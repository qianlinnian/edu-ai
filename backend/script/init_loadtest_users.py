from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import select


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from models.user import User, UserRole
from seed import SessionLocal, ensure_enrollment, get_or_create_course, get_or_create_user


DEFAULT_COURSES = (
    {
        "code": "CS100",
        "name": "计算机科学与技术专业导论",
        "description": "了解计算机科学的基础方向",
        "domain": "计算机科学",
    },
    {
        "code": "CS101",
        "name": "面向对象程序设计（Java）",
        "description": "学习 Java 面向对象核心概念",
        "domain": "计算机科学",
    },
    {
        "code": "CS201",
        "name": "数据结构与算法",
        "description": "常用数据结构和算法设计",
        "domain": "计算机科学",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create load-test students and enroll them into courses.")
    parser.add_argument("--count", type=int, default=500, help="Number of student accounts to create.")
    parser.add_argument("--start-index", type=int, default=1, help="Starting numeric suffix for usernames.")
    parser.add_argument("--prefix", default="student_", help="Username prefix.")
    parser.add_argument("--password", default="123456", help="Plain-text password for all created students.")
    parser.add_argument("--email-domain", default="edu.com", help="Email domain used for generated accounts.")
    parser.add_argument("--name-prefix", default="学生", help="Full-name prefix.")
    parser.add_argument(
        "--padding",
        type=int,
        default=3,
        help="Zero-padding width for usernames, for example 3 => student_001.",
    )
    return parser.parse_args()


def build_username(prefix: str, index: int, padding: int) -> str:
    return f"{prefix}{index:0{padding}d}" if padding > 0 else f"{prefix}{index}"


def main() -> None:
    args = parse_args()
    if args.count <= 0:
        raise SystemExit("--count must be greater than 0")
    if args.start_index <= 0:
        raise SystemExit("--start-index must be greater than 0")
    if args.padding < 0:
        raise SystemExit("--padding must be greater than or equal to 0")

    created_users = 0
    reused_users = 0
    enrollment_links = 0
    teacher_username = "teacher_zhang"

    with SessionLocal() as session:
        try:
            teacher = get_or_create_user(
                session,
                username="teacher_zhang",
                email="zhang@edu.com",
                full_name="张伟老师",
                role=UserRole.TEACHER,
            )
            teacher_username = teacher.username

            courses = [
                get_or_create_course(
                    session,
                    name=item["name"],
                    code=item["code"],
                    description=item["description"],
                    domain=item["domain"],
                    teacher_id=teacher.id,
                )
                for item in DEFAULT_COURSES
            ]

            for offset in range(args.count):
                index = args.start_index + offset
                username = build_username(args.prefix, index, args.padding)
                email = f"{username}@{args.email_domain}"
                full_name = f"{args.name_prefix}{index:0{max(args.padding, 2)}d}"
                existed = session.execute(select(User.id).where(User.username == username)).scalar_one_or_none() is not None

                user = get_or_create_user(
                    session,
                    username=username,
                    email=email,
                    full_name=full_name,
                    role=UserRole.STUDENT,
                    password=args.password,
                )

                if existed:
                    reused_users += 1
                else:
                    created_users += 1

                before_links = len(session.new)
                for course in courses:
                    ensure_enrollment(session, user.id, course.id)
                enrollment_links += max(len(session.new) - before_links, 0)

            session.commit()
        except Exception:
            session.rollback()
            raise

    print("Load-test users prepared.")
    print(f"teacher={teacher_username}")
    print(f"student_prefix={args.prefix}")
    print(f"student_range={args.start_index}-{args.start_index + args.count - 1}")
    print(f"password={args.password}")
    print(f"padding={args.padding}")
    print(f"created_users={created_users}")
    print(f"reused_users={reused_users}")
    print(f"new_enrollments={enrollment_links}")
    print("courses=CS100,CS101,CS201")


if __name__ == "__main__":
    main()
