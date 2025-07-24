"""
Celery 애플리케이션 설정 및 구성
- Redis를 브로커 및 결과 백엔드로 사용
- Windows 환경을 위한 설정 포함
- 작업 결과 추적 및 모니터링 설정
- v1.3 - 로그 가독성 개선 (2025.01.25)
"""

import os
import sys
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from kombu import Exchange, Queue

# Celery 인스턴스 생성
celery = Celery("backlinkvending")

# v1.1 - Celery 워커 Task 모듈 명시적 import (2025.07.15)
from app.core.config import settings

# 환경 변수 로드
load_dotenv()

# Redis 설정 - 브로커와 결과 백엔드 분리
broker_url = settings.CELERY_BROKER_URL or "redis://localhost:6379/0"
result_backend_url = settings.CELERY_RESULT_BACKEND or "redis://localhost:6379/1"

print(f"🔗 [Celery 설정] 브로커 URL: {broker_url}")
print(f"📊 [Celery 설정] 결과 백엔드 URL: {result_backend_url}")

# Celery 구성
celery.conf.update(
    # 브로커 설정
    broker_url=broker_url,
    result_backend=result_backend_url,
    # 클라우드 환경 최적화: 연결 설정
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_heartbeat=30,
    broker_pool_limit=10,
    # Redis 연결 타임아웃 설정
    redis_socket_timeout=30.0,
    redis_socket_connect_timeout=30.0,
    redis_retry_on_timeout=True,
    redis_health_check_interval=10,
    # 직렬화 설정
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    # 작업 결과 설정
    result_expires=3600,
    task_track_started=True,
    task_result_extended=True,
    result_extended=True,
    # 클라우드 환경 최적화: Worker 설정
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50,
    worker_max_memory_per_child=200000,
    worker_disable_rate_limits=True,
    # 로깅 설정 (간소화된 포맷)
    worker_log_format="[%(levelname)s] %(message)s",
    worker_task_log_format="[TASK] %(task_name)s - %(message)s",
    worker_send_task_events=True,
    task_send_sent_event=True,
    # 보안 설정
    worker_hijack_root_logger=False,
    worker_redirect_stdouts=False,
    # 라우팅 설정
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.pbn_tasks.*": {"queue": "pbn"},
        "app.tasks.pbn_rest_tasks.*": {"queue": "pbn"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
        "*": {"queue": "default"},
    },
    # 큐 설정
    task_default_queue="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("email", Exchange("email"), routing_key="email"),
        Queue("pbn", Exchange("pbn"), routing_key="pbn"),
        Queue("reports", Exchange("reports"), routing_key="reports"),
    ),
    # 스케줄 작업 설정 (Beat)
    beat_schedule={
        "daily-report": {
            "task": "app.tasks.report_tasks.generate_daily_report",
            "schedule": crontab(hour=9, minute=0),
        },
        "cleanup-old-logs": {
            "task": "app.tasks.scheduled_tasks.cleanup_old_email_logs",
            "schedule": crontab(hour=2, minute=0),
        },
        "check-pbn-status": {
            "task": "app.tasks.scheduled_tasks.check_pbn_site_status",
            "schedule": crontab(minute="*/30"),
        },
    },
    # 에러 처리 설정
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
)


# 디버그 태스크
@celery.task
def debug_task():
    """Celery 연결 테스트용 디버그 태스크"""
    print("🔍 [DEBUG] Celery 태스크 실행 테스트 성공!")
    return "debug_task_completed"


# Health check 태스크
@celery.task
def system_health_check():
    """시스템 상태 확인 태스크"""
    return {"status": "healthy", "message": "Celery worker is running"}


# 시그널 핸들러
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    worker_ready,
    worker_shutdown,
)


@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds
):
    """태스크 실행 전 로깅"""
    task_name = task.name.split(".")[-1] if task else "unknown"
    print(f"▶️  [TASK] {task_name} 시작")


@task_postrun.connect
def task_postrun_handler(
    sender=None,
    task_id=None,
    task=None,
    args=None,
    kwargs=None,
    retval=None,
    state=None,
    **kwds,
):
    """태스크 실행 후 로깅"""
    task_name = task.name.split(".")[-1] if task else "unknown"
    if state == "SUCCESS":
        print(f"✅ [TASK] {task_name} 완료")
    else:
        print(f"⚠️  [TASK] {task_name} 상태: {state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, einfo=None, **kwds):
    """태스크 실패 시 로깅"""
    task_name = sender.name.split(".")[-1] if sender else "unknown"
    print(f"❌ [TASK] {task_name} 실패: {exception}")


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Worker가 준비되었을 때"""
    print("🎉 [WORKER] 준비 완료 - 태스크 수신 가능!")
    print(f"   └─ Worker: {sender.hostname}")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Worker가 종료될 때"""
    print("👋 [WORKER] 종료됨")


# 간소화된 시작 로그
print("🚀 [CELERY] BacklinkVending Worker 초기화 완료")
print(f"   └─ 브로커: {broker_url.split('@')[-1] if '@' in broker_url else broker_url}")
print(f"   └─ 큐: default, email, pbn, reports")

# 태스크 모듈 자동 검색
try:
    celery.autodiscover_tasks(
        [
            "app.tasks.email_tasks",
            "app.tasks.pbn_rest_tasks",
            "app.tasks.pbn_tasks",
            "app.tasks.report_tasks",
            "app.tasks.scheduled_tasks",
        ]
    )
    print("✅ [CELERY] 태스크 모듈 로드 완료")
except Exception as e:
    print(f"⚠️  [CELERY] 태스크 모듈 로드 오류: {e}")

print("⏳ [CELERY] Worker 시작 대기 중...")
