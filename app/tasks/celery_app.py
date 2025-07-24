"""
Celery ?�플리�??�션 ?�정 �?구성
- Redis�?브로�?�?결과 백엔?�로 ?�용
- Windows ?�환?�을 ?�한 ?�정 ?�함
- ?�업 결과 추적 �?모니?�링 ?�정
- v1.3 - ?�업 결과 추적 �??�류 처리 강화 (2025.01.08)
"""

import os
import sys
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from kombu import Exchange, Queue

# Celery ???�성 (celery_worker.py?� ?�일???�름 ?�용)
celery = Celery("backlinkvending")

# v1.1 - Celery ?�커 Task 모듈 명시??import (2025.07.15)
# celery ?�스?�스 ?�성 ?�후?�만 import (?�환 참조 방�?)
import app.tasks.email_tasks  # ?�메??관???�스???�록
import app.tasks.pbn_rest_tasks  # REST PBN ?�스???�록

# ?�경변??로드
load_dotenv()

# ?�수 Supabase ?�경변??존재 ?��? 검�?
required_env = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
missing = [e for e in required_env if not os.getenv(e)]

if missing:
    missing_str = ", ".join(missing)
    print(f"[Celery App] ?�️ .env???�음 Supabase 변?��? ?�습?�다: {missing_str}")
    print("?��? 기능???�한?????�습?�다.")

# Redis URL ?�정
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ?�경변?�에??Redis URL 가?�오�?(Docker ?�경 고려)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# ?�제 ?�용??브로�?백엔??주소�?명확?�게 로그�?출력 (?�경변???�용 진단)
print("[Celery ?�경] CELERY_BROKER_URL:", CELERY_BROKER_URL)
print("[Celery ?�경] CELERY_RESULT_BACKEND:", CELERY_RESULT_BACKEND)

# Celery ???�성 (celery_worker.py?� ?�일???�름 ?�용)
# Celery Beat ?��?�??�정
beat_schedule = {
    # 매일 ?�벽 2?�에 PBN ?�이???�태 체크
    "daily-pbn-health-check": {
        "task": "check_pbn_sites_health",
        "schedule": crontab(hour=2, minute=0),
    },
    # 매일 ?�벽 3?�에 ?�료???�업 ?�리
    "daily-cleanup-completed-tasks": {
        "task": "cleanup_completed_tasks",
        "schedule": crontab(hour=3, minute=0),
    },
    # 매일 ?�벽 4?�에 ?�간 보고???�성
    "daily-report-generation": {
        "task": "generate_daily_report",
        "schedule": crontab(hour=4, minute=0),
    },
    # 매주 ?�요???�벽 5?�에 주간 보고???�성
    "weekly-report-generation": {
        "task": "generate_weekly_report",
        "schedule": crontab(hour=5, minute=0, day_of_week=1),
    },
    # 매월 1???�벽 6?�에 ?�간 보고???�성
    "monthly-report-generation": {
        "task": "generate_monthly_report",
        "schedule": crontab(hour=6, minute=0, day_of_month=1),
    },
    # �?30분마???�패???�메???�시??
    "retry-failed-emails": {
        "task": "retry_failed_emails",
        "schedule": crontab(minute="*/30"),
    },
    # �?15분마???�스???�스체크
    "system-health-check": {
        "task": "system_health_check",
        "schedule": crontab(minute="*/15"),
    },
    # 매일 ?�정??로그 ?�리
    "daily-log-cleanup": {
        "task": "cleanup_old_logs",
        "schedule": crontab(hour=0, minute=0),
    },
}

# Celery ?�정
celery.conf.update(
    # 브로�?�?결과 백엔???�정
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    # ???�정 - default ??명시??추�?
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    # ???�의
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("celery", Exchange("celery"), routing_key="celery"),
    ),
    # ?�우???�정
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "default"},
        "app.tasks.pbn_rest_tasks.*": {"queue": "default"},
        "app.tasks.pbn_tasks.*": {"queue": "default"},
        "app.tasks.report_tasks.*": {"queue": "default"},
        "app.tasks.scheduled_tasks.*": {"queue": "default"},
    },
    # Windows ?�환?�을 ?�한 ?�정
    worker_pool="solo",
    worker_concurrency=1,
    # 직렬???�정 (보안 �??�환??
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # ?�업 결과 추적 ?�정
    result_expires=3600 * 24 * 7,  # 결과�?7?�간 보�?
    result_persistent=True,  # 결과�??�구 ?�??
    task_track_started=True,  # ?�업 ?�작 추적
    task_send_sent_event=True,  # ?�업 ?�송 ?�벤??추적
    # ?�업 ?�행 추적 ?�정
    worker_send_task_events=True,  # ?�커 ?�벤???�송
    # ?�?�존 ?�정
    timezone="Asia/Seoul",
    enable_utc=True,
    # ?�업 ?�시???�정
    task_annotations={
        "*": {
            "rate_limit": "10/s",
            "max_retries": 3,
            "default_retry_delay": 60,
        }
    },
    # ?�류 처리 ?�정
    task_reject_on_worker_lost=True,  # ?�커 ?�실 ???�업 거�?
    task_acks_late=True,  # ?�업 ?�료 ??ACK
    worker_prefetch_multiplier=1,  # ??번에 ?�나??처리
    # 모니?�링 ?�정
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    # ?�업 ?�동 발견 ?�정
    include=["app.tasks.scheduled_tasks"],
)

# ?�스???�동 발견
celery.autodiscover_tasks(
    [
        "app.tasks.pbn_tasks",
        "app.tasks.pbn_rest_tasks",
        "app.tasks.email_tasks",
        "app.tasks.report_tasks",
        "app.tasks.scheduled_tasks",  # ?�로 추�????�약 ?�업 모듈
    ]
)


# ?�스체크??기본 ?�업
@celery.task(bind=True, name="health_check")
def health_check(self):
    """?�스???�스체크 ?�업"""
    try:
        return {
            "status": "healthy",
            "task_id": self.request.id,
            "worker": self.request.hostname,
            "timestamp": str(self.request.timestamp),
        }
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)
