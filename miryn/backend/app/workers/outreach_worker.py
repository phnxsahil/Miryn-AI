from app.workers.celery_app import celery_app
from app.services.outreach_scheduler import OutreachScheduler


@celery_app.task(name="outreach.scan")
def scan_outreach():
    scheduler = OutreachScheduler()
    return {"notifications": scheduler.scan()}
