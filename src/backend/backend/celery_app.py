from celery import Celery

from backend.settings import settings

celery_app = Celery("tasks", broker=settings.REDIS_URL, backend=settings.REDIS_URL, include=["backend.tasks"])

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
