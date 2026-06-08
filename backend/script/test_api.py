"""
Self-contained local smoke test for the EduAI M4 API surface.

The script creates disposable users and course data so it can be rerun without
depending on pre-seeded IDs such as agent_id=3/course_id=3.
"""

from __future__ import annotations

import json
import time
import uuid

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
PASSWORD = "password123"


def make_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def assert_ok(response: requests.Response, action: str) -> dict:
    print(f"{action}: {response.status_code}")
    if response.status_code >= 400:
        raise RuntimeError(f"{action} failed: {response.text}")
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"{action} returned non-JSON response: {response.text[:200]}") from exc


def register_user(session: requests.Session, *, role: str, full_name: str) -> dict:
    username = unique_name(role)
    payload = {
        "username": username,
        "email": f"{username}@test.com",
        "password": PASSWORD,
        "full_name": full_name,
        "role": role,
    }
    response = session.post(f"{BASE_URL}/auth/register", json=payload, timeout=30)
    data = assert_ok(response, f"register_{role}")
    return {"username": username, "token": None, "profile": data}


def login_user(session: requests.Session, username: str) -> str:
    last_response: requests.Response | None = None
    for attempt in range(3):
        response = session.post(
            f"{BASE_URL}/auth/login",
            data={"username": username, "password": PASSWORD},
            timeout=30,
        )
        if response.status_code < 400:
            data = response.json()
            print(f"login_{username}: {response.status_code}")
            return data["access_token"]
        last_response = response
        time.sleep(0.5 * (attempt + 1))

    assert last_response is not None
    data = assert_ok(last_response, f"login_{username}")
    return data["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def build_workflow(course_id: int) -> dict:
    return {
        "nodes": [
            {
                "id": "n1",
                "type": "custom",
                "position": {"x": 0, "y": 0},
                "data": {"label": "input", "nodeType": "input_node"},
            },
            {
                "id": "n2",
                "type": "custom",
                "position": {"x": 0, "y": 1},
                "data": {
                    "label": "rag",
                    "nodeType": "rag_node",
                    "course": course_id,
                    "topK": 5,
                    "similarity": 0.7,
                },
            },
            {
                "id": "n3",
                "type": "custom",
                "position": {"x": 0, "y": 2},
                "data": {"label": "llm", "nodeType": "llm_node", "model": "qwen-max"},
            },
            {
                "id": "n4",
                "type": "custom",
                "position": {"x": 0, "y": 3},
                "data": {"label": "output", "nodeType": "output_node"},
            },
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
        ],
    }


def main() -> None:
    session = make_session()

    print("=" * 60)
    print("EduAI local smoke test")
    print("=" * 60)

    health = assert_ok(session.get("http://127.0.0.1:8000/health", timeout=30), "health")
    print(json.dumps(health, ensure_ascii=False))

    teacher = register_user(session, role="teacher", full_name="Smoke Teacher")
    teacher["token"] = login_user(session, teacher["username"])
    teacher_headers = auth_headers(teacher["token"])
    me = assert_ok(session.get(f"{BASE_URL}/auth/me", headers=teacher_headers, timeout=30), "teacher_me")
    print(f"teacher: {me['username']} ({me['role']})")

    course = assert_ok(
        session.post(
            f"{BASE_URL}/courses",
            headers=teacher_headers,
            json={
                "name": f"Smoke Course {teacher['username'][-4:]}",
                "code": f"SMK-{teacher['username'][-4:]}",
                "description": "Disposable course for local smoke testing",
                "domain": "testing",
            },
            timeout=30,
        ),
        "create_course",
    )
    course_id = course["id"]

    for index, name in enumerate(("Intro", "Loop", "Function"), start=1):
        assert_ok(
            session.post(
                f"{BASE_URL}/courses/{course_id}/knowledge-units",
                headers=teacher_headers,
                json={
                    "name": name,
                    "description": f"{name} topic",
                    "domain": "testing",
                    "difficulty": index,
                },
                timeout=30,
            ),
            f"create_knowledge_unit_{index}",
        )

    agent = assert_ok(
        session.post(
            f"{BASE_URL}/agents/instances",
            headers=teacher_headers,
            json={
                "template_id": None,
                "course_id": course_id,
                "name": f"Smoke Agent {teacher['username'][-4:]}",
                "description": "Disposable agent for local smoke testing",
                "system_prompt": "You are a helpful tutor.",
                "config": {},
                "tools": [],
                "llm_provider": "dashscope",
                "llm_model": "qwen-max",
            },
            timeout=30,
        ),
        "create_agent",
    )

    workflow = assert_ok(
        session.post(
            f"{BASE_URL}/agents/workflows",
            headers=teacher_headers,
            json={
                "agent_id": agent["id"],
                "name": f"Smoke Workflow {teacher['username'][-4:]}",
                "description": "Disposable workflow for local smoke testing",
                "workflow_dag": build_workflow(course_id),
            },
            timeout=30,
        ),
        "create_workflow",
    )

    assert_ok(
        session.post(
            f"{BASE_URL}/agents/workflows/{workflow['id']}/publish",
            headers=teacher_headers,
            timeout=30,
        ),
        "publish_workflow",
    )

    chat_response = assert_ok(
        session.post(
            f"{BASE_URL}/chat/send",
            headers=teacher_headers,
            json={
                "agent_id": agent["id"],
                "course_id": course_id,
                "message": "请用一句话解释什么是循环。",
            },
            timeout=60,
        ),
        "teacher_chat_send",
    )
    print(chat_response["message"]["content"][:120])

    student = register_user(session, role="student", full_name="Smoke Student")
    student["token"] = login_user(session, student["username"])
    student_headers = auth_headers(student["token"])

    assert_ok(
        session.post(
            f"{BASE_URL}/courses/{course_id}/enroll",
            headers=student_headers,
            timeout=30,
        ),
        "student_enroll",
    )

    assert_ok(
        session.get(
            f"{BASE_URL}/courses/{course_id}",
            headers=student_headers,
            timeout=30,
        ),
        "student_get_course",
    )

    student_chat = assert_ok(
        session.post(
            f"{BASE_URL}/chat/send",
            headers=student_headers,
            json={
                "agent_id": agent["id"],
                "course_id": course_id,
                "message": "请再解释一次循环。",
            },
            timeout=60,
        ),
        "student_chat_send",
    )
    print(student_chat["message"]["content"][:120])

    print("=" * 60)
    print("Smoke test completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
