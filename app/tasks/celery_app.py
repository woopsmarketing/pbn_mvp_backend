"""
Celery 애플리케이션 설정 및 구성
- Redis를 브로커 및 결과 백엔드로 사용
- Windows 환경을 위한 설정 포함
- 작업 결과 추적 및 모니터링 설정
- v1.3 - 작업 결과 추적 및 오류 처리 강화 (2025.01.08)
"""

import os
import sys
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from kombu import Exchange, Queue

# Celery 인스턴스 생성 (celery_worker.py와 동일한 이름 사용)
celery = Celery("backlinkvending")

# v1.1 - Celery 워커 Task 모듈 명시적 import (2025.07.15)
# celery 인스턴스 생성 이후에만 import (순환 참조 방지)
from app.core.config import settings

# 환경 변수 로드
load_dotenv()

# Windows 환경에서 pickle 직렬화 문제 해결
if sys.platform == "win32":
    os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")

# Redis 설정 - 브로커와 결과 백엔드 분리
broker_url = settings.CELERY_BROKER_URL or "redis://localhost:6379/0"
result_backend_url = settings.CELERY_RESULT_BACKEND or "redis://localhost:6379/1"

print(f"🔗 [Celery 설정] 브로커 URL: {broker_url}")
print(f"📊 [Celery 설정] 결과 백엔드 URL: {result_backend_url}")

# Celery 구성
celery.conf.update(
    # 브로커 설정 (올바른 환경변수 사용)
    broker_url=broker_url,
    result_backend=result_backend_url,  # 별도의 결과 백엔드 사용
    # 직렬화 설정
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    # 작업 결과 설정
    result_expires=3600,  # 1시간 후 결과 만료
    task_track_started=True,
    task_result_extended=True,
    result_extended=True,
    # 작업자(Worker) 설정
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50,
    # 라우팅 설정
    task_routes={
        # 이메일 관련 태스크
        "app.tasks.email_tasks.*": {"queue": "email"},
        # PBN 관련 태스크
        "app.tasks.pbn_tasks.*": {"queue": "pbn"},
        # 보고서 관련 태스크
        "app.tasks.report_tasks.*": {"queue": "reports"},
        # 기본 태스크
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
            "schedule": crontab(hour=9, minute=0),  # 매일 오전 9시
        },
        "cleanup-old-logs": {
            "task": "app.tasks.scheduled_tasks.cleanup_old_email_logs",
            "schedule": crontab(hour=2, minute=0),  # 매일 새벽 2시
        },
        "check-pbn-status": {
            "task": "app.tasks.scheduled_tasks.check_pbn_site_status",
            "schedule": crontab(minute="*/30"),  # 30분마다
        },
    },
    # 에러 처리 설정
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    # 로깅 설정 (더 상세한 로그 출력)
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    worker_send_task_events=True,  # 태스크 이벤트 전송 활성화
    task_send_sent_event=True,  # 태스크 전송 이벤트 활성화
    # 보안 설정
    worker_hijack_root_logger=False,
    worker_redirect_stdouts=True,  # stdout을 로그로 리다이렉트
)

# v1.2 - Task 자동 검색 설정 (2025.07.16)
celery.autodiscover_tasks(
    [
        "app.tasks.email_tasks",
        "app.tasks.pbn_tasks",
        "app.tasks.report_tasks",
        "app.tasks.scheduled_tasks",
        "app.tasks.pbn_rest_tasks",
    ]
)


# v1.3 - Celery 상태 모니터링 (2025.01.08)
@celery.task(bind=True)
def debug_task(self):
    """디버그용 태스크"""
    print(f"Request: {self.request!r}")
    return f"Task executed successfully: {self.request.id}"


# v1.3 - 에러 핸들러 (2025.01.08)
@celery.task(bind=True)
def error_handler(self, uuid, err, traceback):
    """에러 처리 태스크"""
    print(f"Task {uuid} raised exception: {err}\n{traceback}")


# 컨테이너 환경에서의 Celery 연결 테스트
@celery.task
def health_check():
    """Celery 상태 확인용 태스크"""
    return {
        "status": "healthy",
        "message": "BacklinkVending Celery worker is running",
        "timestamp": str(os.environ.get("CURRENT_TIME", "unknown")),
    }


# v1.3 - Celery 시그널 핸들러 (2025.01.08)
from celery.signals import task_prerun, task_postrun, task_failure


@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds
):
    """태스크 실행 전 로깅"""
    print(f"Task {task_id} started: {task.name}")


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
    print(f"Task {task_id} finished: {task.name} - State: {state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, einfo=None, **kwds):
    """태스크 실패 시 로깅"""
    print(f"Task {task_id} failed: {exception}")


# Celery 워커 시작 시 로그
print("BacklinkVending Celery application configured successfully")
print(f"Broker URL: {broker_url}")
print(f"Worker queues: default, email, pbn, reports")
