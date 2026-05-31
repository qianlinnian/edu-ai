"""
M4 测试数据初始化脚本
用于创建测试所需的：用户、课程、Agent 实例
"""
import asyncio
import sys
sys.path.insert(0, ".")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://eduai:eduai123@localhost:5432/eduai"


async def init_test_data():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. 创建测试用户 (role 使用大写枚举值, is_active 必须指定)
        result = await session.execute(text("""
            INSERT INTO users (username, email, hashed_password, full_name, role, is_active, created_at, updated_at)
            VALUES
                ('test_teacher', 'teacher@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qJwGPRl5mM8G2', '测试教师', 'TEACHER', true, NOW(), NOW()),
                ('test_student', 'student@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qJwGPRl5mM8G2', '测试学生', 'STUDENT', true, NOW(), NOW())
            ON CONFLICT (username) DO NOTHING
            RETURNING id, username;
        """))
        users = result.fetchall()
        print(f"Users: {users}")

        # 2. 创建测试课程
        result = await session.execute(text("""
            INSERT INTO courses (name, description, created_by, created_at, updated_at)
            VALUES
                ('Python程序设计', 'Python基础课程', (SELECT id FROM users WHERE username='test_teacher' LIMIT 1), NOW(), NOW()),
                ('数据结构', '数据结构与算法', (SELECT id FROM users WHERE username='test_teacher' LIMIT 1), NOW(), NOW())
            ON CONFLICT DO NOTHING
            RETURNING id, name;
        """))
        courses = result.fetchall()
        print(f"Courses: {courses}")

        # 3. 创建 Agent 实例
        result = await session.execute(text("""
            INSERT INTO agent_instances (template_id, course_id, name, description, system_prompt, llm_provider, llm_model, is_active, created_by, created_at, updated_at)
            VALUES
                (NULL, (SELECT id FROM courses WHERE name='Python程序设计' LIMIT 1), 'Python答疑Agent', 'Python课程智能答疑', '你是一个Python课程智能助教，擅长回答Python相关问题。', 'dashscope', 'qwen-max', true, (SELECT id FROM users WHERE username='test_teacher' LIMIT 1), NOW(), NOW()),
                (NULL, (SELECT id FROM courses WHERE name='Python程序设计' LIMIT 1), '作业批改Agent', '作业智能批改', '你是一个作业批改助手，擅长评估学生作业并给出反馈。', 'dashscope', 'qwen-max', true, (SELECT id FROM users WHERE username='test_teacher' LIMIT 1), NOW(), NOW())
            ON CONFLICT DO NOTHING
            RETURNING id, name;
        """))
        agents = result.fetchall()
        print(f"Agents: {agents}")

        await session.commit()

    await engine.dispose()
    print("\n测试数据初始化完成!")
    print("默认密码: password123")
    return users, courses, agents


if __name__ == "__main__":
    asyncio.run(init_test_data())
