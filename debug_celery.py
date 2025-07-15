#!/usr/bin/env python3
"""
Celery 워커와 Redis 큐 상태 디버깅 스크립트
"""

import os
import sys
import redis
import json
from datetime import datetime

# 환경 변수 설정
os.environ.setdefault("PYTHONPATH", "/app")
sys.path.insert(0, "/app")


def debug_print(message: str, category: str = "DEBUG"):
    """디버깅용 print 함수"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{category}] {message}")


def check_environment():
    """환경 변수 확인"""
    debug_print("=== 환경 변수 확인 ===", "ENV")

    important_vars = [
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SMTP_SERVER",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
    ]

    for var in important_vars:
        value = os.getenv(var)
        if value:
            # 비밀번호는 마스킹
            if "PASSWORD" in var or "KEY" in var:
                masked_value = (
                    value[:4] + "*" * (len(value) - 8) + value[-4:]
                    if len(value) > 8
                    else "****"
                )
                debug_print(f"{var}: {masked_value}", "ENV")
            else:
                debug_print(f"{var}: {value}", "ENV")
        else:
            debug_print(f"{var}: NOT SET", "ENV")


def check_redis_connection():
    """Redis 연결 확인"""
    debug_print("=== Redis 연결 확인 ===", "REDIS")

    try:
        broker_url = os.getenv("CELERY_BROKER_URL")
        if not broker_url:
            debug_print("CELERY_BROKER_URL이 설정되지 않음", "REDIS")
            return None

        debug_print(f"브로커 URL: {broker_url}", "REDIS")

        # Redis 클라이언트 생성
        r = redis.from_url(broker_url)

        # 연결 테스트
        r.ping()
        debug_print("Redis 연결 성공", "REDIS")

        return r
    except Exception as e:
        debug_print(f"Redis 연결 실패: {e}", "REDIS")
        return None


def check_queues(redis_client):
    """큐 상태 확인"""
    if not redis_client:
        debug_print("Redis 클라이언트가 없어 큐 확인 불가", "QUEUE")
        return

    debug_print("=== 큐 상태 확인 ===", "QUEUE")

    queue_names = ["default", "celery", "email", "pbn"]

    for queue_name in queue_names:
        try:
            # 큐 길이 확인
            queue_length = redis_client.llen(queue_name)
            debug_print(f"큐 '{queue_name}': {queue_length}개 태스크 대기 중", "QUEUE")

            # 큐 내용 확인 (처음 5개만)
            if queue_length > 0:
                tasks = redis_client.lrange(queue_name, 0, 4)
                for i, task in enumerate(tasks):
                    try:
                        task_data = json.loads(task)
                        task_name = task_data.get("task", "Unknown")
                        task_id = task_data.get("id", "Unknown")
                        debug_print(f"  {i+1}. {task_name} (ID: {task_id})", "QUEUE")
                    except:
                        debug_print(f"  {i+1}. 파싱 불가: {task[:100]}...", "QUEUE")

        except Exception as e:
            debug_print(f"큐 '{queue_name}' 확인 실패: {e}", "QUEUE")


def check_celery_app():
    """Celery 앱 확인"""
    debug_print("=== Celery 앱 확인 ===", "CELERY")

    try:
        from app.tasks.celery_app import celery as app

        debug_print("Celery 앱 임포트 성공", "CELERY")

        # 등록된 태스크 확인
        tasks = list(app.tasks.keys())
        debug_print(f"등록된 태스크 수: {len(tasks)}", "CELERY")

        for task in tasks:
            if not task.startswith("celery."):  # 내장 태스크 제외
                debug_print(f"  - {task}", "CELERY")

        # 브로커 설정 확인
        debug_print(f"브로커 URL: {app.conf.broker_url}", "CELERY")
        debug_print(f"결과 백엔드: {app.conf.result_backend}", "CELERY")
        debug_print(f"기본 큐: {app.conf.task_default_queue}", "CELERY")

    except Exception as e:
        debug_print(f"Celery 앱 확인 실패: {e}", "CELERY")


def test_task_registration():
    """태스크 등록 테스트"""
    debug_print("=== 태스크 등록 테스트 ===", "TASK")

    try:
        from app.tasks.celery_app import celery as app
        from app.tasks.email_tasks import send_order_confirmation_email
        from app.tasks.pbn_rest_tasks import create_pbn_backlink_rest

        # 태스크 함수 직접 확인
        debug_print("이메일 태스크 함수 확인:", "TASK")
        debug_print(
            f"  - send_order_confirmation_email: {send_order_confirmation_email}",
            "TASK",
        )
        debug_print(f"  - 태스크 이름: {send_order_confirmation_email.name}", "TASK")

        debug_print("PBN 태스크 함수 확인:", "TASK")
        debug_print(f"  - create_pbn_backlink_rest: {create_pbn_backlink_rest}", "TASK")
        debug_print(f"  - 태스크 이름: {create_pbn_backlink_rest.name}", "TASK")

        # 태스크 등록 상태 확인
        email_task_registered = send_order_confirmation_email.name in app.tasks
        pbn_task_registered = create_pbn_backlink_rest.name in app.tasks

        debug_print(f"이메일 태스크 등록 상태: {email_task_registered}", "TASK")
        debug_print(f"PBN 태스크 등록 상태: {pbn_task_registered}", "TASK")

    except Exception as e:
        debug_print(f"태스크 등록 테스트 실패: {e}", "TASK")


def test_simple_task():
    """간단한 태스크 테스트"""
    debug_print("=== 간단한 태스크 테스트 ===", "TEST")

    try:
        from app.tasks.celery_app import celery as app

        # 간단한 테스트 태스크 생성
        @app.task
        def debug_test_task(message):
            debug_print(f"테스트 태스크 실행: {message}", "TEST_TASK")
            return f"테스트 완료: {message}"

        # 태스크 큐에 등록
        debug_print("테스트 태스크 큐에 등록 중...", "TEST")
        result = debug_test_task.apply_async(
            args=["Hello from debug script"], queue="default"
        )

        debug_print(f"태스크 ID: {result.id}", "TEST")
        debug_print("태스크가 큐에 등록되었습니다. 워커 로그를 확인하세요.", "TEST")

    except Exception as e:
        debug_print(f"간단한 태스크 테스트 실패: {e}", "TEST")


def main():
    """메인 함수"""
    debug_print("=== Celery 디버깅 스크립트 시작 ===", "MAIN")

    # 1. 환경 변수 확인
    check_environment()

    # 2. Redis 연결 확인
    redis_client = check_redis_connection()

    # 3. 큐 상태 확인
    check_queues(redis_client)

    # 4. Celery 앱 확인
    check_celery_app()

    # 5. 태스크 등록 테스트
    test_task_registration()

    # 6. 간단한 태스크 테스트
    test_simple_task()

    debug_print("=== Celery 디버깅 스크립트 완료 ===", "MAIN")


if __name__ == "__main__":
    main()
