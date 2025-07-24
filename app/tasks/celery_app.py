"""
Celery ? í”Œë¦¬ì??´ì…˜ ?¤ì • ë°?êµ¬ì„±
- Redisë¥?ë¸Œë¡œì»?ë°?ê²°ê³¼ ë°±ì—”?œë¡œ ?¬ìš©
- Windows ?¸í™˜?±ì„ ?„í•œ ?¤ì • ?¬í•¨
- ?‘ì—… ê²°ê³¼ ì¶”ì  ë°?ëª¨ë‹ˆ?°ë§ ?¤ì •
- v1.3 - ?‘ì—… ê²°ê³¼ ì¶”ì  ë°??¤ë¥˜ ì²˜ë¦¬ ê°•í™” (2025.01.08)
"""

import os
import sys
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from kombu import Exchange, Queue

# Celery ???ì„± (celery_worker.py?€ ?™ì¼???´ë¦„ ?¬ìš©)
celery = Celery("backlinkvending")

# v1.1 - Celery ?Œì»¤ Task ëª¨ë“ˆ ëª…ì‹œ??import (2025.07.15)
# celery ?¸ìŠ¤?´ìŠ¤ ?ì„± ?´í›„?ë§Œ import (?œí™˜ ì°¸ì¡° ë°©ì?)
import app.tasks.email_tasks  # ?´ë©”??ê´€???œìŠ¤???±ë¡
import app.tasks.pbn_rest_tasks  # REST PBN ?œìŠ¤???±ë¡

# ?˜ê²½ë³€??ë¡œë“œ
load_dotenv()

# ?„ìˆ˜ Supabase ?˜ê²½ë³€??ì¡´ì¬ ?¬ë? ê²€ì¦?
required_env = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
missing = [e for e in required_env if not os.getenv(e)]

if missing:
    missing_str = ", ".join(missing)
    print(f"[Celery App] ? ï¸ .env???¤ìŒ Supabase ë³€?˜ê? ?†ìŠµ?ˆë‹¤: {missing_str}")
    print("?¼ë? ê¸°ëŠ¥???œí•œ?????ˆìŠµ?ˆë‹¤.")

# Redis URL ?¤ì •
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ?˜ê²½ë³€?˜ì—??Redis URL ê°€?¸ì˜¤ê¸?(Docker ?˜ê²½ ê³ ë ¤)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# ?¤ì œ ?ìš©??ë¸Œë¡œì»?ë°±ì—”??ì£¼ì†Œë¥?ëª…í™•?˜ê²Œ ë¡œê·¸ë¡?ì¶œë ¥ (?˜ê²½ë³€???ìš© ì§„ë‹¨)
print("[Celery ?˜ê²½] CELERY_BROKER_URL:", CELERY_BROKER_URL)
print("[Celery ?˜ê²½] CELERY_RESULT_BACKEND:", CELERY_RESULT_BACKEND)

# Celery ???ì„± (celery_worker.py?€ ?™ì¼???´ë¦„ ?¬ìš©)
# Celery Beat ?¤ì?ì¤??¤ì •
beat_schedule = {
    # ë§¤ì¼ ?ˆë²½ 2?œì— PBN ?¬ì´???íƒœ ì²´í¬
    "daily-pbn-health-check": {
        "task": "check_pbn_sites_health",
        "schedule": crontab(hour=2, minute=0),
    },
    # ë§¤ì¼ ?ˆë²½ 3?œì— ?„ë£Œ???‘ì—… ?•ë¦¬
    "daily-cleanup-completed-tasks": {
        "task": "cleanup_completed_tasks",
        "schedule": crontab(hour=3, minute=0),
    },
    # ë§¤ì¼ ?ˆë²½ 4?œì— ?¼ê°„ ë³´ê³ ???ì„±
    "daily-report-generation": {
        "task": "generate_daily_report",
        "schedule": crontab(hour=4, minute=0),
    },
    # ë§¤ì£¼ ?”ìš”???ˆë²½ 5?œì— ì£¼ê°„ ë³´ê³ ???ì„±
    "weekly-report-generation": {
        "task": "generate_weekly_report",
        "schedule": crontab(hour=5, minute=0, day_of_week=1),
    },
    # ë§¤ì›” 1???ˆë²½ 6?œì— ?”ê°„ ë³´ê³ ???ì„±
    "monthly-report-generation": {
        "task": "generate_monthly_report",
        "schedule": crontab(hour=6, minute=0, day_of_month=1),
    },
    # ë§?30ë¶„ë§ˆ???¤íŒ¨???´ë©”???¬ì‹œ??
    "retry-failed-emails": {
        "task": "retry_failed_emails",
        "schedule": crontab(minute="*/30"),
    },
    # ë§?15ë¶„ë§ˆ???œìŠ¤???¬ìŠ¤ì²´í¬
    "system-health-check": {
        "task": "system_health_check",
        "schedule": crontab(minute="*/15"),
    },
    # ë§¤ì¼ ?ì •??ë¡œê·¸ ?•ë¦¬
    "daily-log-cleanup": {
        "task": "cleanup_old_logs",
        "schedule": crontab(hour=0, minute=0),
    },
}

# Celery ?¤ì •
celery.conf.update(
    # ë¸Œë¡œì»?ë°?ê²°ê³¼ ë°±ì—”???¤ì •
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    # ???¤ì • - default ??ëª…ì‹œ??ì¶”ê?
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    # ???•ì˜
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("celery", Exchange("celery"), routing_key="celery"),
    ),
    # ?¼ìš°???¤ì •
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "default"},
        "app.tasks.pbn_rest_tasks.*": {"queue": "default"},
        "app.tasks.pbn_tasks.*": {"queue": "default"},
        "app.tasks.report_tasks.*": {"queue": "default"},
        "app.tasks.scheduled_tasks.*": {"queue": "default"},
    },
    # Windows ?¸í™˜?±ì„ ?„í•œ ?¤ì •
    worker_pool="solo",
    worker_concurrency=1,
    # ì§ë ¬???¤ì • (ë³´ì•ˆ ë°??¸í™˜??
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # ?‘ì—… ê²°ê³¼ ì¶”ì  ?¤ì •
    result_expires=3600 * 24 * 7,  # ê²°ê³¼ë¥?7?¼ê°„ ë³´ê?
    result_persistent=True,  # ê²°ê³¼ë¥??êµ¬ ?€??
    task_track_started=True,  # ?‘ì—… ?œì‘ ì¶”ì 
    task_send_sent_event=True,  # ?‘ì—… ?„ì†¡ ?´ë²¤??ì¶”ì 
    # ?‘ì—… ?¤í–‰ ì¶”ì  ?¤ì •
    worker_send_task_events=True,  # ?Œì»¤ ?´ë²¤???„ì†¡
    # ?€?„ì¡´ ?¤ì •
    timezone="Asia/Seoul",
    enable_utc=True,
    # ?‘ì—… ?¬ì‹œ???¤ì •
    task_annotations={
        "*": {
            "rate_limit": "10/s",
            "max_retries": 3,
            "default_retry_delay": 60,
        }
    },
    # ?¤ë¥˜ ì²˜ë¦¬ ?¤ì •
    task_reject_on_worker_lost=True,  # ?Œì»¤ ?ì‹¤ ???‘ì—… ê±°ë?
    task_acks_late=True,  # ?‘ì—… ?„ë£Œ ??ACK
    worker_prefetch_multiplier=1,  # ??ë²ˆì— ?˜ë‚˜??ì²˜ë¦¬
    # ëª¨ë‹ˆ?°ë§ ?¤ì •
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    # ?‘ì—… ?ë™ ë°œê²¬ ?¤ì •
    include=["app.tasks.scheduled_tasks"],
)

# ?œìŠ¤???ë™ ë°œê²¬
celery.autodiscover_tasks(
    [
        "app.tasks.pbn_tasks",
        "app.tasks.pbn_rest_tasks",
        "app.tasks.email_tasks",
        "app.tasks.report_tasks",
        "app.tasks.scheduled_tasks",  # ?ˆë¡œ ì¶”ê????ˆì•½ ?‘ì—… ëª¨ë“ˆ
    ]
)


# ?¬ìŠ¤ì²´í¬??ê¸°ë³¸ ?‘ì—…
@celery.task(bind=True, name="health_check")
def health_check(self):
    """?œìŠ¤???¬ìŠ¤ì²´í¬ ?‘ì—…"""
    try:
        return {
            "status": "healthy",
            "task_id": self.request.id,
            "worker": self.request.hostname,
            "timestamp": str(self.request.timestamp),
        }
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)
