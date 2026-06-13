from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "healthcare_fi",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(["app.tasks"])

celery_app.conf.beat_schedule = {
    "refresh-kpi-every-15-minutes": {
        "task": "app.tasks.kpi.refresh_kpis",
        "schedule": crontab(minute="*/15"),
    },
    "detect-anomalies-every-hour": {
        "task": "app.tasks.intelligence.detect_anomalies",
        "schedule": crontab(minute=0),
    },
    "generate-daily-briefing": {
        "task": "app.tasks.intelligence.generate_daily_briefing",
        "schedule": crontab(hour=6, minute=0),
    },
    "run-quality-validation-daily": {
        "task": "app.tasks.quality.run_validation",
        "schedule": crontab(hour=2, minute=0),
    },
    "sync-duckdb-daily": {
        "task": "app.tasks.data_sync.sync_to_duckdb",
        "schedule": crontab(hour=3, minute=0),
    },
}
