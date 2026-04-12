# backend/seed.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import get_settings
import models  # 导入所有模型，触发表注册

# 从已有的 models 文件导入具体的类
from models.user import User, UserRole
from models.course import Course, Enrollment, KnowledgeUnit, KnowledgeRelation

settings = get_settings()

# 建立同步数据库连接
engine = create_engine(settings.DATABASE_SYNC_URL)
Session = sessionmaker(bind=engine)


def seed():
    session = Session()
    try:

        # ========== 1. 创建用户 ==========
        from core.security import get_password_hash

        teacher = User(
            username="teacher_zhang",
            email="zhang@edu.com",
            hashed_password=get_password_hash("123456"),
            role=UserRole.teacher,
            full_name="张伟老师",
        )
        students = [
            User(
                username=f"student_{i:02d}",
                email=f"student{i:02d}@edu.com",
                hashed_password=get_password_hash("123456"),
                role=UserRole.student,
                full_name=f"学生{i:02d}号",
            )
            for i in range(1, 11)  # 10个学生
        ]

        session.add(teacher)
        session.add_all(students)
        session.flush()  # flush之后 teacher.id 才有值，后面能用

        # ========== 2. 创建课程 ==========
        java_course = Course(
            name="面向对象程序设计（Java）",
            code="CS101",
            description="学习Java面向对象核心概念",
            domain="计算机科学",
            teacher_id=teacher.id,
        )
        intro_course = Course(
            name="计算机科学与技术专业导论",
            code="CS100",
            description="了解计算机科学的基础方向",
            domain="计算机科学",
            teacher_id=teacher.id,
        )
        ds_course = Course(
            name="数据结构与算法",
            code="CS201",
            description="常用数据结构和算法设计",
            domain="计算机科学",
            teacher_id=teacher.id,
        )

        session.add_all([java_course, intro_course, ds_course])
        session.flush()  # 课程id才有值

        # ========== 3. 学生选课 ==========
        for student in students:
            for course in [java_course, intro_course, ds_course]:
                session.add(Enrollment(student_id=student.id, course_id=course.id))

        # ========== 4. 创建知识点（以Java课程为例）==========
        kp_data = [
            ("类与对象", "类的定义、对象创建、构造方法", 1),
            ("封装", "访问控制修饰符、getter/setter方法", 2),
            ("继承", "extends关键字、方法重写、super关键字", 2),
            ("多态", "向上转型、动态绑定、接口实现", 3),
            ("异常处理", "try-catch-finally、自定义异常类", 2),
            ("集合框架", "ArrayList、HashMap、迭代器模式", 3),
        ]

        kps = []
        for i, (name, desc, difficulty) in enumerate(kp_data):
            kp = KnowledgeUnit(
                course_id=java_course.id,
                name=name,
                description=desc,
                domain="Java编程",
                difficulty=difficulty,
                order_index=i,
            )
            session.add(kp)
            kps.append(kp)
        session.flush()

        # ========== 5. 创建知识点关联关系 ==========
        # 比如"继承"的前置知识是"类与对象"
        relations = [
            (kps[0].id, kps[1].id, "prerequisite"),  # 类与对象 → 封装
            (kps[0].id, kps[2].id, "prerequisite"),  # 类与对象 → 继承
            (kps[2].id, kps[3].id, "prerequisite"),  # 继承 → 多态
        ]
        for source_id, target_id, rel_type in relations:
            session.add(KnowledgeRelation(
                source_id=source_id,
                target_id=target_id,
                relation_type=rel_type,
            ))

        # ========== 6. 提交 ==========
        session.commit()
        print("✅ 种子数据写入成功！")
        print(f"   用户：1名教师 + {len(students)}名学生")
        print(f"   课程：3门")
        print(f"   知识点：{len(kps)}个（Java课程）")

    except Exception as e:
        session.rollback()
        print(f"❌ 出错了，已回滚：{e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()