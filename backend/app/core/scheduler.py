"""
Lightweight background scheduler for periodic, non-request-triggered
jobs. Currently runs one job: warning file owners when a public share
link is about to expire (slide 6 / spec item "Expiration reminders").

Uses APScheduler's BackgroundScheduler, which runs jobs on a thread
inside the same process as the API — no separate worker or message
queue needed, which fits a project already running a single FastAPI
process. If this ever needs to scale beyond one process, this job
should move to whatever the project's task queue is instead, so it
doesn't run redundantly once per process.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.crud.monitoring import check_expiring_share_links
from app.db.session import SessionLocal

logger = logging.getLogger("trustshare.scheduler")

CHECK_INTERVAL_MINUTES = 60

_scheduler: BackgroundScheduler | None = None


def _run_expiry_check() -> None:
    db = SessionLocal()
    try:
        sent = check_expiring_share_links(db)
        if sent:
            logger.info("Sent %d share-link expiry reminder(s).", sent)
    except Exception:
        # A failed job run should never crash the scheduler thread or
        # take down the API; log it and let the next scheduled run retry.
        logger.exception("Share-link expiry check failed.")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _run_expiry_check,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        next_run_time=datetime.now(timezone.utc),  # also run once immediately on startup
        id="share_link_expiry_check",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Share-link expiry scheduler started (every %d minutes).",
        CHECK_INTERVAL_MINUTES,
    )
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
