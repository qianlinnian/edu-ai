from celery import Celery
from core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "eduai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "workers.grading_task.*": {"queue": "grading"},
        "workers.embedding_task.*": {"queue": "embedding"},
    },
)

# 自动发现任务
celery_app.autodiscover_tasks(["workers"])
