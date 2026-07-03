"""Unified API-level E2E smoke test for EduAI.

This script exercises a realistic cross-role workflow against a running EduAI
backend. It is suitable as an API-level end-to-end / system integration test,
but it is not a browser UI E2E test.
"""

from __future__ import annotations

import argparse
import io
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_PASSWORD = "password123"
DEFAULT_TIMEOUT = 30


@dataclass
class Context:
    session: requests.Session
    base_url: str
    password: str
    poll_timeout: int
    teacher: dict[str, Any] = field(default_factory=dict)
    student: dict[str, Any] = field(default_factory=dict)
    course: dict[str, Any] = field(default_factory=dict)
    knowledge_units: list[dict[str, Any]] = field(default_factory=list)
    resource: dict[str, Any] = field(default_factory=dict)
    agent: dict[str, Any] = field(default_factory=dict)
    workflow: dict[str, Any] = field(default_factory=dict)
    assignment: dict[str, Any] = field(default_factory=dict)
    submission: dict[str, Any] = field(default_factory=dict)
    grading_result: dict[str, Any] = field(default_factory=dict)
    annotations: list[dict[str, Any]] = field(default_factory=list)
    teacher_session_id: int | None = None
    student_session_id: int | None = None
    generated_exercises: list[dict[str, Any]] = field(default_factory=list)
    alerts: list[dict[str, Any]] = field(default_factory=list)


def make_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def log_step(name: str) -> None:
    print(f"\n=== {name} ===")


def ensure_ok(response: requests.Response, action: str) -> dict[str, Any]:
    print(f"{action}: {response.status_code}")
    if response.status_code >= 400:
        raise RuntimeError(f"{action} failed: {response.status_code} {response.text[:500]}")
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"{action} returned non-JSON response: {response.text[:200]}") from exc


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def request_json(
    ctx: Context,
    method: str,
    path: str,
    *,
    action: str,
    token: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> dict[str, Any]:
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers.update(auth_headers(token))
    response = ctx.session.request(
        method,
        f"{ctx.base_url}{path}",
        headers=headers,
        timeout=timeout,
        **kwargs,
    )
    return ensure_ok(response, action)


def request_list(
    ctx: Context,
    method: str,
    path: str,
    *,
    action: str,
    token: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers.update(auth_headers(token))
    response = ctx.session.request(
        method,
        f"{ctx.base_url}{path}",
        headers=headers,
        timeout=timeout,
        **kwargs,
    )
    print(f"{action}: {response.status_code}")
    if response.status_code >= 400:
        raise RuntimeError(f"{action} failed: {response.status_code} {response.text[:500]}")
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"{action} returned non-list payload: {payload}")
    return payload


def build_workflow(course_id: int) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": "input",
                "type": "custom",
                "position": {"x": 0, "y": 0},
                "data": {"label": "Input", "nodeType": "input_node"},
            },
            {
                "id": "rag",
                "type": "custom",
                "position": {"x": 0, "y": 120},
                "data": {
                    "label": "RAG",
                    "nodeType": "rag_node",
                    "course": course_id,
                    "topK": 5,
                    "similarity": 0.7,
                },
            },
            {
                "id": "llm",
                "type": "custom",
                "position": {"x": 0, "y": 240},
                "data": {"label": "LLM", "nodeType": "llm_node", "model": "qwen-max"},
            },
            {
                "id": "output",
                "type": "custom",
                "position": {"x": 0, "y": 360},
                "data": {"label": "Output", "nodeType": "output_node"},
            },
            {
                "id": "grading",
                "type": "custom",
                "position": {"x": 280, "y": 120},
                "data": {"label": "Grading", "nodeType": "grading_node"},
            },
            {
                "id": "analytics",
                "type": "custom",
                "position": {"x": 280, "y": 240},
                "data": {"label": "Analytics", "nodeType": "analytics_node"},
            },
            {
                "id": "exercise",
                "type": "custom",
                "position": {"x": 280, "y": 360},
                "data": {"label": "Exercise", "nodeType": "exercise_node"},
            },
        ],
        "edges": [
            {"id": "e1", "source": "input", "target": "rag"},
            {"id": "e2", "source": "rag", "target": "llm"},
            {"id": "e3", "source": "llm", "target": "output"},
        ],
    }


def register_user(ctx: Context, *, role: str, full_name: str) -> dict[str, Any]:
    username = unique_name(role)
    payload = {
        "username": username,
        "email": f"{username}@test.com",
        "password": ctx.password,
        "full_name": full_name,
        "role": role,
    }
    data = request_json(ctx, "POST", "/auth/register", action=f"register_{role}", json=payload)
    return {"username": username, "token": "", "profile": data}


def login_user(ctx: Context, username: str) -> str:
    last_error = ""
    for attempt in range(3):
        response = ctx.session.post(
            f"{ctx.base_url}/auth/login",
            data={"username": username, "password": ctx.password},
            timeout=DEFAULT_TIMEOUT,
        )
        print(f"login_{username}: {response.status_code}")
        if response.status_code < 400:
            return response.json()["access_token"]
        last_error = response.text
        time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"login_{username} failed after retries: {last_error[:500]}")


def wait_for_resource_processed(ctx: Context, course_id: int, resource_id: int, token: str) -> dict[str, Any]:
    deadline = time.time() + ctx.poll_timeout
    while time.time() < deadline:
        resources = request_list(ctx, "GET", f"/courses/{course_id}/resources", action="list_resources_poll", token=token)
        match = next((item for item in resources if int(item["id"]) == resource_id), None)
        if match is None:
            raise RuntimeError(f"Resource {resource_id} disappeared during polling")
        status = match["processing_status"]
        if status == "processed":
            return match
        if status == "failed":
            raise RuntimeError(f"Resource processing failed: {match.get('processing_error')}")
        time.sleep(2)
    raise RuntimeError(f"Timed out waiting for resource {resource_id} to be processed")


def parse_sse(response: requests.Response) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for raw_line in response.iter_lines():
        if not raw_line:
            continue
        line = raw_line.decode("utf-8")
        if not line.startswith("data: "):
            continue
        payload = json.loads(line[6:])
        events.append(payload)
    return events


def wait_for_grading(ctx: Context, submission_id: int, token: str) -> dict[str, Any]:
    deadline = time.time() + ctx.poll_timeout
    while time.time() < deadline:
        response = ctx.session.get(
            f"{ctx.base_url}/assignments/submissions/{submission_id}/result",
            headers=auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        print(f"poll_grading_result: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 409:
            raise RuntimeError(f"Grading terminal failure: {response.text[:500]}")
        time.sleep(2)
    raise RuntimeError(f"Timed out waiting for grading result on submission {submission_id}")


def run(ctx: Context) -> None:
    log_step("Health")
    health = ensure_ok(ctx.session.get("http://127.0.0.1:8000/health", timeout=DEFAULT_TIMEOUT), "health")
    print(json.dumps(health, ensure_ascii=False))

    log_step("Teacher registration and login")
    ctx.teacher = register_user(ctx, role="teacher", full_name="Smoke Teacher")
    ctx.teacher["token"] = login_user(ctx, ctx.teacher["username"])
    teacher_me = request_json(ctx, "GET", "/auth/me", action="teacher_me", token=ctx.teacher["token"])
    print(f"teacher: {teacher_me['username']} ({teacher_me['role']})")

    log_step("Student registration and login")
    ctx.student = register_user(ctx, role="student", full_name="Smoke Student")
    ctx.student["token"] = login_user(ctx, ctx.student["username"])
    student_me = request_json(ctx, "GET", "/auth/me", action="student_me", token=ctx.student["token"])
    print(f"student: {student_me['username']} ({student_me['role']})")

    log_step("Teacher creates and updates a course")
    course_suffix = ctx.teacher["username"][-4:]
    ctx.course = request_json(
        ctx,
        "POST",
        "/courses",
        action="create_course",
        token=ctx.teacher["token"],
        json={
            "name": f"Smoke Course {course_suffix}",
            "code": f"SMK-{course_suffix}",
            "description": "Disposable course for API E2E validation",
            "domain": "testing",
        },
    )
    course_id = int(ctx.course["id"])
    ctx.course = request_json(
        ctx,
        "PUT",
        f"/courses/{course_id}",
        action="update_course",
        token=ctx.teacher["token"],
        json={
            "name": f"Smoke Course {course_suffix} Updated",
            "code": f"SMK-{course_suffix}",
            "description": "Updated course description",
            "domain": "testing",
        },
    )
    teacher_courses = request_list(ctx, "GET", "/courses", action="teacher_list_courses", token=ctx.teacher["token"])
    assert any(int(item["id"]) == course_id for item in teacher_courses)

    log_step("Teacher creates knowledge units")
    for index, name in enumerate(("Intro", "Loop", "Function"), start=1):
        item = request_json(
            ctx,
            "POST",
            f"/courses/{course_id}/knowledge-units",
            action=f"create_knowledge_unit_{index}",
            token=ctx.teacher["token"],
            json={
                "name": name,
                "description": f"{name} topic",
                "domain": "testing",
                "difficulty": index,
                "tags": ["smoke", "e2e"],
            },
        )
        ctx.knowledge_units.append(item)
    generated = request_json(
        ctx,
        "POST",
        f"/courses/{course_id}/knowledge-units/generate",
        action="generate_knowledge_units",
        token=ctx.teacher["token"],
    )
    print(f"generated_knowledge_units: {generated['created']}")
    knowledge_units = request_list(
        ctx,
        "GET",
        f"/courses/{course_id}/knowledge-units",
        action="list_knowledge_units",
        token=ctx.teacher["token"],
    )
    assert len(knowledge_units) >= len(ctx.knowledge_units)

    log_step("Teacher uploads and validates a resource")
    files = {
        "file": (
            "smoke-resource.md",
            io.BytesIO(
                b"# Smoke Resource\n\nRecursion reduces a problem into smaller subproblems.\n\nBase case stops recursion.\n"
            ),
            "text/markdown",
        )
    }
    upload_result = request_json(
        ctx,
        "POST",
        f"/courses/{course_id}/resources",
        action="upload_resource",
        token=ctx.teacher["token"],
        files=files,
    )
    resource_id = int(upload_result["id"])
    ctx.resource = wait_for_resource_processed(ctx, course_id, resource_id, ctx.teacher["token"])
    download_response = ctx.session.get(
        f"{ctx.base_url}/courses/{course_id}/resources/{resource_id}/download",
        headers=auth_headers(ctx.teacher["token"]),
        timeout=DEFAULT_TIMEOUT,
    )
    print(f"download_resource: {download_response.status_code}")
    if download_response.status_code >= 400:
        raise RuntimeError(f"download_resource failed: {download_response.text[:500]}")
    assert b"Recursion" in download_response.content

    log_step("Teacher creates agent and publishes workflow")
    ctx.agent = request_json(
        ctx,
        "POST",
        "/agents/instances",
        action="create_agent",
        token=ctx.teacher["token"],
        json={
            "template_id": None,
            "course_id": course_id,
            "name": f"Smoke Agent {course_suffix}",
            "description": "Disposable agent for API E2E validation",
            "system_prompt": "You are a helpful tutor.",
            "config": {},
            "tools": [],
            "llm_provider": "dashscope",
            "llm_model": "qwen-max",
        },
    )
    ctx.workflow = request_json(
        ctx,
        "POST",
        "/agents/workflows",
        action="create_workflow",
        token=ctx.teacher["token"],
        json={
            "agent_id": ctx.agent["id"],
            "name": f"Smoke Workflow {course_suffix}",
            "description": "Disposable workflow for API E2E validation",
            "workflow_dag": build_workflow(course_id),
        },
    )
    request_json(
        ctx,
        "POST",
        f"/agents/workflows/{ctx.workflow['id']}/publish",
        action="publish_workflow",
        token=ctx.teacher["token"],
    )

    log_step("Teacher chat and stream chat")
    teacher_chat = request_json(
        ctx,
        "POST",
        "/chat/send",
        action="teacher_chat_send",
        token=ctx.teacher["token"],
        timeout=90,
        json={
            "agent_id": ctx.agent["id"],
            "course_id": course_id,
            "message": "Explain recursion in one short sentence.",
        },
    )
    ctx.teacher_session_id = int(teacher_chat["session_id"])
    stream_response = ctx.session.post(
        f"{ctx.base_url}/chat/send-stream",
        headers={**auth_headers(ctx.teacher["token"]), "Content-Type": "application/json"},
        timeout=90,
        stream=True,
        json={
            "agent_id": ctx.agent["id"],
            "course_id": course_id,
            "session_id": ctx.teacher_session_id,
            "message": "Give one more short example of recursion.",
        },
    )
    print(f"teacher_chat_stream: {stream_response.status_code}")
    if stream_response.status_code >= 400:
        raise RuntimeError(f"teacher_chat_stream failed: {stream_response.text[:500]}")
    events = parse_sse(stream_response)
    assert any(event.get("type") == "chunk" for event in events)
    assert any(event.get("type") == "done" for event in events)
    teacher_messages = request_list(
        ctx,
        "GET",
        f"/chat/sessions/{ctx.teacher_session_id}/messages",
        action="teacher_list_messages",
        token=ctx.teacher["token"],
    )
    assert len(teacher_messages) >= 4

    log_step("Student enrolls and accesses course")
    request_json(
        ctx,
        "POST",
        f"/courses/{course_id}/enroll",
        action="student_enroll",
        token=ctx.student["token"],
    )
    request_json(
        ctx,
        "GET",
        f"/courses/{course_id}",
        action="student_get_course",
        token=ctx.student["token"],
    )
    browse_courses = request_list(ctx, "GET", "/courses/browse", action="student_browse_courses", token=ctx.student["token"])
    assert any(int(item["id"]) == course_id for item in browse_courses)
    teacher_students = request_list(
        ctx,
        "GET",
        f"/courses/{course_id}/students",
        action="teacher_list_students",
        token=ctx.teacher["token"],
    )
    assert any(item["username"] == ctx.student["username"] for item in teacher_students)

    log_step("Student resource access and chat")
    student_resources = request_list(
        ctx,
        "GET",
        f"/courses/{course_id}/resources",
        action="student_list_resources",
        token=ctx.student["token"],
    )
    assert any(int(item["id"]) == resource_id for item in student_resources)
    student_chat = request_json(
        ctx,
        "POST",
        "/chat/send",
        action="student_chat_send",
        token=ctx.student["token"],
        timeout=90,
        json={
            "agent_id": ctx.agent["id"],
            "course_id": course_id,
            "message": "What is the base case in recursion?",
        },
    )
    ctx.student_session_id = int(student_chat["session_id"])
    student_sessions = request_list(
        ctx,
        "GET",
        f"/chat/sessions?course_id={course_id}",
        action="student_list_sessions",
        token=ctx.student["token"],
    )
    assert any(int(item["id"]) == ctx.student_session_id for item in student_sessions)

    log_step("Teacher creates assignment; student submits; teacher and student inspect")
    ctx.assignment = request_json(
        ctx,
        "POST",
        "/assignments",
        action="create_assignment",
        token=ctx.teacher["token"],
        json={
            "course_id": course_id,
            "title": "Explain recursion",
            "description": "State definition, base case, and one example.",
            "assignment_type": "text",
            "max_score": 100,
            "rubric": {"dimensions": [{"name": "concept", "max_score": 50}, {"name": "example", "max_score": 50}]},
            "reference_answer": "Recursion solves a problem by reducing it to smaller subproblems until a base case.",
            "knowledge_points": [int(ctx.knowledge_units[0]["id"])],
        },
    )
    teacher_assignments = request_list(
        ctx,
        "GET",
        f"/assignments?course_id={course_id}",
        action="teacher_list_assignments",
        token=ctx.teacher["token"],
    )
    assert any(int(item["id"]) == int(ctx.assignment["id"]) for item in teacher_assignments)
    ctx.submission = request_json(
        ctx,
        "POST",
        f"/assignments/{ctx.assignment['id']}/submit",
        action="student_submit_assignment",
        token=ctx.student["token"],
        files={"content": (None, "Recursion calls the same function on a smaller input until a base case stops it.")},
    )
    submission_id = int(ctx.submission["id"])
    student_submissions = request_list(
        ctx,
        "GET",
        f"/assignments/{ctx.assignment['id']}/submissions",
        action="student_list_submissions",
        token=ctx.student["token"],
    )
    assert any(int(item["id"]) == submission_id for item in student_submissions)
    teacher_submissions = request_list(
        ctx,
        "GET",
        f"/assignments/{ctx.assignment['id']}/submissions",
        action="teacher_list_submissions",
        token=ctx.teacher["token"],
    )
    assert any(int(item["id"]) == submission_id for item in teacher_submissions)
    ctx.grading_result = wait_for_grading(ctx, submission_id, ctx.student["token"])
    ctx.annotations = request_list(
        ctx,
        "GET",
        f"/assignments/submissions/{submission_id}/annotations",
        action="list_annotations",
        token=ctx.student["token"],
    )

    log_step("Student exercise generation and attempt")
    exercise_generation = request_json(
        ctx,
        "POST",
        "/exercises/generate",
        action="generate_exercises",
        token=ctx.student["token"],
        timeout=90,
        json={
            "course_id": course_id,
            "knowledge_point_ids": [int(ctx.knowledge_units[0]["id"])],
            "exercise_type": "choice",
            "difficulty": 2,
            "count": 2,
            "use_llm": True,
        },
    )
    ctx.generated_exercises = list(exercise_generation["exercises"])
    if not ctx.generated_exercises:
        raise RuntimeError("generate_exercises returned no exercises")
    first_generated = ctx.generated_exercises[0]
    student_answer = first_generated.get("answer") or "A"
    attempt_result = request_json(
        ctx,
        "POST",
        "/exercises/attempt",
        action="submit_exercise_attempt",
        token=ctx.student["token"],
        json={
            "generated_exercise_id": first_generated["id"],
            "student_answer": student_answer,
        },
    )
    print(json.dumps(attempt_result, ensure_ascii=False))
    exercise_pool = request_list(
        ctx,
        "GET",
        f"/exercises/pool?course_id={course_id}",
        action="list_exercise_pool",
        token=ctx.student["token"],
    )
    print(f"exercise_pool_count: {len(exercise_pool)}")

    log_step("Analytics and alerts")
    student_id = int(ctx.student["profile"]["id"])
    mastery = request_list(
        ctx,
        "GET",
        f"/analytics/student/{student_id}/mastery?course_id={course_id}",
        action="student_mastery",
        token=ctx.student["token"],
    )
    weak_points = request_list(
        ctx,
        "GET",
        f"/analytics/student/{student_id}/weak-points?course_id={course_id}",
        action="student_weak_points",
        token=ctx.student["token"],
    )
    class_report = request_json(
        ctx,
        "GET",
        f"/analytics/course/{course_id}/class-report",
        action="teacher_class_report",
        token=ctx.teacher["token"],
    )
    print(f"mastery_items: {len(mastery)}")
    print(f"weak_points_items: {len(weak_points)}")
    print(f"class_report_items: {len(class_report.get('by_knowledge_unit', []))}")
    request_json(
        ctx,
        "POST",
        f"/analytics/course/{course_id}/refresh-alerts",
        action="teacher_refresh_alerts",
        token=ctx.teacher["token"],
    )
    ctx.alerts = request_list(
        ctx,
        "GET",
        f"/analytics/alerts?course_id={course_id}",
        action="teacher_list_alerts",
        token=ctx.teacher["token"],
    )
    _ = request_list(
        ctx,
        "GET",
        f"/analytics/alerts?course_id={course_id}",
        action="student_list_alerts",
        token=ctx.student["token"],
    )

    log_step("Platform simulated integration")
    _ = request_json(
        ctx,
        "POST",
        "/platform/connections",
        action="create_platform_connection",
        token=ctx.teacher["token"],
        json={
            "platform_type": "chaoxing",
            "name": "Smoke Chaoxing",
            "config": {
                "lti_key": "key-1",
                "lti_secret": "secret-1",
                "callback_url": "https://example.com/callback",
            },
        },
    )
    _ = request_list(ctx, "GET", "/platform/connections", action="list_platform_connections", token=ctx.teacher["token"])
    _ = request_json(
        ctx,
        "POST",
        "/platform/chaoxing/lti-launch",
        action="chaoxing_launch",
        token=ctx.teacher["token"],
        json={"course_id": course_id, "role": "student", "launch_ticket": "ticket-001"},
    )
    _ = request_json(
        ctx,
        "GET",
        f"/platform/dingtalk/auth?code=auth-code-001&course_id={course_id}&role=teacher",
        action="dingtalk_auth",
        token=ctx.teacher["token"],
    )

    log_step("Session and resource cleanup checks")
    request_json(
        ctx,
        "DELETE",
        f"/chat/sessions/{ctx.student_session_id}",
        action="delete_student_session",
        token=ctx.student["token"],
    )
    request_json(
        ctx,
        "DELETE",
        f"/courses/{course_id}/resources/{resource_id}",
        action="delete_resource",
        token=ctx.teacher["token"],
    )

    print("\n" + "=" * 60)
    print("API E2E smoke test completed successfully")
    print("=" * 60)
    print(
        json.dumps(
            {
                "course_id": course_id,
                "teacher_username": ctx.teacher["username"],
                "student_username": ctx.student["username"],
                "resource_id": resource_id,
                "assignment_id": ctx.assignment["id"],
                "submission_id": submission_id,
                "teacher_session_id": ctx.teacher_session_id,
                "student_session_id": ctx.student_session_id,
                "generated_exercise_count": len(ctx.generated_exercises),
                "alerts_count": len(ctx.alerts),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the EduAI API-level E2E smoke test.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend API base URL, e.g. http://127.0.0.1:8000/api/v1")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password used for disposable users")
    parser.add_argument("--poll-timeout", default=120, type=int, help="Seconds to wait for async resource/grading processing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ctx = Context(
        session=make_session(),
        base_url=args.base_url.rstrip("/"),
        password=args.password,
        poll_timeout=max(args.poll_timeout, 10),
    )
    run(ctx)


if __name__ == "__main__":
    main()
