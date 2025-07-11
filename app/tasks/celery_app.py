"""
Celery 애플리케이션 설정 및 구성
- Redis를 브로커 및 결과 백엔드로 사용
- Windows 호환성을 위한 설정 포함
- 작업 결과 추적 및 모니터링 설정
- v1.3 - 작업 결과 추적 및 오류 처리 강화 (2025.01.08)
"""

import os
import sys
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from kombu import Exchange, Queue

# 환경변수 로드
load_dotenv()

# 필수 Supabase 환경변수 존재 여부 검증
required_env = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
missing = [e for e in required_env if not os.getenv(e)]

if missing:
    missing_str = ", ".join(missing)
    print(f"[Celery App] ⚠️ .env에 다음 Supabase 변수가 없습니다: {missing_str}")
    print("일부 기능이 제한될 수 있습니다.")

# Redis URL 설정
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 환경변수에서 Redis URL 가져오기 (Docker 환경 고려)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Celery 앱 생성 (celery_worker.py와 동일한 이름 사용)
celery = Celery("followsales")

# Celery Beat 스케줄 설정
beat_schedule = {
    # 매일 새벽 2시에 PBN 사이트 상태 체크
    "daily-pbn-health-check": {
        "task": "check_pbn_sites_health",
        "schedule": crontab(hour=2, minute=0),
    },
    # 매일 새벽 3시에 완료된 작업 정리
    "daily-cleanup-completed-tasks": {
        "task": "cleanup_completed_tasks",
        "schedule": crontab(hour=3, minute=0),
    },
    # 매일 새벽 4시에 일간 보고서 생성
    "daily-report-generation": {
        "task": "generate_daily_report",
        "schedule": crontab(hour=4, minute=0),
    },
    # 매주 월요일 새벽 5시에 주간 보고서 생성
    "weekly-report-generation": {
        "task": "generate_weekly_report",
        "schedule": crontab(hour=5, minute=0, day_of_week=1),
    },
    # 매월 1일 새벽 6시에 월간 보고서 생성
    "monthly-report-generation": {
        "task": "generate_monthly_report",
        "schedule": crontab(hour=6, minute=0, day_of_month=1),
    },
    # 매 30분마다 실패한 이메일 재시도
    "retry-failed-emails": {
        "task": "retry_failed_emails",
        "schedule": crontab(minute="*/30"),
    },
    # 매 15분마다 시스템 헬스체크
    "system-health-check": {
        "task": "system_health_check",
        "schedule": crontab(minute="*/15"),
    },
    # 매일 자정에 로그 정리
    "daily-log-cleanup": {
        "task": "cleanup_old_logs",
        "schedule": crontab(hour=0, minute=0),
    },
}

# Celery 설정
celery.conf.update(
    # 브로커 및 결과 백엔드 설정
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    # Windows 호환성을 위한 설정
    worker_pool="solo",
    worker_concurrency=1,
    # 직렬화 설정 (보안 및 호환성)
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # 작업 결과 추적 설정
    result_expires=3600 * 24 * 7,  # 결과를 7일간 보관
    result_persistent=True,  # 결과를 영구 저장
    task_track_started=True,  # 작업 시작 추적
    task_send_sent_event=True,  # 작업 전송 이벤트 추적
    # 작업 실행 추적 설정
    worker_send_task_events=True,  # 워커 이벤트 전송
    # 타임존 설정
    timezone="Asia/Seoul",
    enable_utc=True,
    # 작업 재시도 설정
    task_annotations={
        "*": {
            "rate_limit": "10/s",
            "max_retries": 3,
            "default_retry_delay": 60,
        }
    },
    # 오류 처리 설정
    task_reject_on_worker_lost=True,  # 워커 손실 시 작업 거부
    task_acks_late=True,  # 작업 완료 후 ACK
    worker_prefetch_multiplier=1,  # 한 번에 하나씩 처리
    # 모니터링 설정
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    # 작업 자동 발견 설정
    include=["app.tasks.scheduled_tasks"],
)

# 태스크 자동 발견
celery.autodiscover_tasks(
    [
        "app.tasks.pbn_tasks",
        "app.tasks.pbn_rest_tasks",
        "app.tasks.email_tasks",
        "app.tasks.report_tasks",
        "app.tasks.scheduled_tasks",  # 새로 추가된 예약 작업 모듈
    ]
)


# 헬스체크용 기본 작업
@celery.task(bind=True, name="health_check")
def health_check(self):
    """시스템 헬스체크 작업"""
    try:
        return {
            "status": "healthy",
            "task_id": self.request.id,
            "worker": self.request.hostname,
            "timestamp": str(self.request.timestamp),
        }
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)
