from __future__ import annotations

import os
import random
from typing import Any

from locust import HttpUser, LoadTestShape, between, task


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


USERNAME_PREFIX = os.getenv("EDUAI_USERNAME_PREFIX", "student_")
PASSWORD = os.getenv("EDUAI_PASSWORD", "123456")
USER_COUNT = max(_env_int("EDUAI_USER_COUNT", 10), 1)
FIXED_COURSE_ID = _env_int("EDUAI_COURSE_ID", 0)
USERNAME_PADDING = max(_env_int("EDUAI_USERNAME_PADDING", max(2, len(str(USER_COUNT)))), 0)


class AuthenticatedStudentUser(HttpUser):
    """
    Read-only baseline load test user.

    This class intentionally avoids:
    - /chat/send and /chat/send-stream
    - /assignments/{id}/submit
    - /exercises/generate

    Those paths either hit real LLM providers or dispatch async workloads and
    should be evaluated separately after baseline read-path capacity is known.
    """

    wait_time = between(1, 3)
    token: str
    headers: dict[str, str]
    course_id: int
    resource_id: int | None

    def on_start(self) -> None:
        self.course_id = FIXED_COURSE_ID
        self.resource_id = None

        user_idx = random.randint(1, USER_COUNT)
        username = (
            f"{USERNAME_PREFIX}{user_idx:0{USERNAME_PADDING}d}"
            if USERNAME_PADDING > 0
            else f"{USERNAME_PREFIX}{user_idx}"
        )

        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": username, "password": PASSWORD},
            name="auth.login",
        )
        response.raise_for_status()
        payload = response.json()
        self.token = payload["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

        if not self.course_id:
            courses = self.client.get("/api/v1/courses", headers=self.headers, name="courses.list.on_start")
            courses.raise_for_status()
            course_items = courses.json()
            if not course_items:
                raise RuntimeError("No enrolled courses found for load-test user")
            self.course_id = int(course_items[0]["id"])

    def _cache_first_resource_id(self) -> None:
        if self.resource_id is not None:
            return
        response = self.client.get(
            f"/api/v1/courses/{self.course_id}/resources",
            headers=self.headers,
            name="resources.list.cache",
        )
        if response.status_code != 200:
            return
        items = response.json()
        if items:
            self.resource_id = int(items[0]["id"])

    @task(35)
    def list_courses(self) -> None:
        self.client.get("/api/v1/courses", headers=self.headers, name="courses.list")

    @task(20)
    def get_course_detail(self) -> None:
        self.client.get(f"/api/v1/courses/{self.course_id}", headers=self.headers, name="courses.detail")

    @task(15)
    def list_resources(self) -> None:
        self.client.get(
            f"/api/v1/courses/{self.course_id}/resources",
            headers=self.headers,
            name="resources.list",
        )

    @task(10)
    def list_chat_sessions(self) -> None:
        self.client.get(
            f"/api/v1/chat/sessions?course_id={self.course_id}",
            headers=self.headers,
            name="chat.sessions.list",
        )

    @task(10)
    def list_assignments(self) -> None:
        self.client.get(
            f"/api/v1/assignments?course_id={self.course_id}",
            headers=self.headers,
            name="assignments.list",
        )

    @task(7)
    def list_exercise_pool(self) -> None:
        self.client.get(
            f"/api/v1/exercises/pool?course_id={self.course_id}",
            headers=self.headers,
            name="exercises.pool",
        )

    @task(3)
    def download_first_resource(self) -> None:
        self._cache_first_resource_id()
        if self.resource_id is None:
            return
        self.client.get(
            f"/api/v1/courses/{self.course_id}/resources/{self.resource_id}/download",
            headers=self.headers,
            name="resources.download",
        )


class Baseline500Shape(LoadTestShape):
    """
    500-user baseline:
    - 0-120s: warm up to 50
    - 120-420s: ramp to 500
    - 420-1020s: hold 500
    - 1020-1200s: ramp down
    """

    stages = [
        {"duration": 120, "users": 50, "spawn_rate": 10},
        {"duration": 420, "users": 500, "spawn_rate": 50},
        {"duration": 1020, "users": 500, "spawn_rate": 10},
        {"duration": 1200, "users": 0, "spawn_rate": 100},
    ]

    def tick(self) -> tuple[int, int] | None:
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None


def summarize_user_config() -> dict[str, Any]:
    return {
        "username_prefix": USERNAME_PREFIX,
        "password_masked": "***" if PASSWORD else "",
        "user_count": USER_COUNT,
        "fixed_course_id": FIXED_COURSE_ID,
        "username_padding": USERNAME_PADDING,
    }
