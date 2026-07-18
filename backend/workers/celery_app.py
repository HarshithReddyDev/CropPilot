from celery import Celery

from core.config import settings

celery_app = Celery(
    "croppilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,
    timezone="Asia/Kolkata",
)

celery_app.autodiscover_tasks(["workers"])
