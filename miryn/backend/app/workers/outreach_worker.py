from app.workers.celery_app import celery_app
from app.services.outreach_scheduler import OutreachScheduler


@celery_app.task(name="outreach.scan")
def scan_outreach():
    """
    Run an outreach scan and return the discovered notifications.
    
    Returns:
        dict: A mapping with the key "notifications" whose value is the scan result (the notifications discovered by the outreach scheduler).
    """
    scheduler = OutreachScheduler()
    return {"notifications": scheduler.scan()}
