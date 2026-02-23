from celery import Celery
from app.config import settings


celery_app = Celery("miryn")
celery_app.conf.broker_url = settings.REDIS_URL
celery_app.conf.result_backend = settings.REDIS_URL
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "memory-gc-nightly": {
        "task": "memory.gc",
        "schedule": 60 * 60 * 24,
    },
    "memory-summarize-nightly": {
        "task": "memory.summarize",
        "schedule": 60 * 60 * 24,
    },
    "outreach-scan-hourly": {
        "task": "outreach.scan",
        "schedule": 60 * 60,
    },
}

# Import worker modules so Celery discovers all tasks at startup
from app.workers import reflection_worker, memory_worker, outreach_worker  # noqa: E402, F401
