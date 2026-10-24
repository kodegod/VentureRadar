from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery("ventureradar", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = "UTC"
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.beat_schedule = {
    "synthetic-pipeline-hourly": {
        "task": "app.workers.tasks.run_pipeline_task",
        "schedule": 3600.0,
    },
    "daily-trends": {
        "task": "app.workers.tasks.refresh_trends_task",
        "schedule": crontab(hour=3, minute=15),
    },
    "retention-pass": {
        "task": "app.workers.tasks.retention_pass_task",
        "schedule": crontab(hour=4, minute=10),
    },
}
celery_app.autodiscover_tasks(["app.workers"])
