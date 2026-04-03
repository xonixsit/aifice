"""
24/7 Scheduler — runs all agent tasks on a configurable cron schedule.
Uses APScheduler with persistent job store so it survives restarts.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from loguru import logger

scheduler = BlockingScheduler(jobstores={"default": MemoryJobStore()})


def _run(task_name: str, **kwargs):
    from agents.orchestrator import build_orchestrator
    logger.info(f"[Scheduler] Running: {task_name}")
    try:
        orch = build_orchestrator()
        orch(f"Execute task: {task_name}. kwargs: {kwargs}")
    except Exception as e:
        logger.error(f"[Scheduler] {task_name} failed: {e}")


def register_jobs():
    # ── Daily content posts ────────────────────────────────────────────────
    scheduler.add_job(_run, "cron", hour=9,  minute=0,  id="morning_linkedin",
                      kwargs={"task_name": "run_content_creation", "platform": "linkedin"})
    scheduler.add_job(_run, "cron", hour=12, minute=0,  id="noon_instagram",
                      kwargs={"task_name": "run_content_creation", "platform": "instagram"})
    scheduler.add_job(_run, "cron", hour=17, minute=0,  id="evening_facebook",
                      kwargs={"task_name": "run_content_creation", "platform": "facebook"})
    scheduler.add_job(_run, "cron", hour=20, minute=0,  id="night_telegram",
                      kwargs={"task_name": "run_content_creation", "platform": "telegram"})

    # ── Lead generation (weekdays only) ───────────────────────────────────
    scheduler.add_job(_run, "cron", day_of_week="mon-fri", hour=8, minute=30,
                      id="lead_gen",
                      kwargs={"task_name": "run_lead_generation"})

    # ── Engagement checks (every 2 hours) ─────────────────────────────────
    scheduler.add_job(_run, "interval", hours=2, id="engagement",
                      kwargs={"task_name": "run_engagement",
                              "platform": "all", "context": "check for new comments and DMs"})

    # ── Follow-ups (twice daily) ───────────────────────────────────────────
    scheduler.add_job(_run, "cron", hour=10, minute=0, id="followup_am",
                      kwargs={"task_name": "run_followups"})
    scheduler.add_job(_run, "cron", hour=15, minute=0, id="followup_pm",
                      kwargs={"task_name": "run_followups"})

    # ── Learning cycle (daily at midnight) ────────────────────────────────
    scheduler.add_job(_run, "cron", hour=0, minute=0, id="learning",
                      kwargs={"task_name": "run_learning"})


def start():
    register_jobs()
    logger.info("Scheduler started. Running 24/7...")
    scheduler.start()
