# v1.0 - Redis 큐 상태 확인용 디버그 엔드포인트 (2025.07.15)
# 기능: celery, default 큐의 길이, 데이터, Redis 연결 상태 등을 종합적으로 확인
# 사용 예시: GET /api/v1/debug/redis-queue

from fastapi import APIRouter, HTTPException
import redis
import json
import os
from datetime import datetime

router = APIRouter()


@router.get("/debug/redis-queue")
def debug_redis_queue_status():
    """
    Redis 큐 상태를 종합적으로 확인하는 디버그 엔드포인트
    - celery, default 큐의 길이와 데이터 확인
    - Redis 연결 상태 확인
    - 환경변수 정보 확인
    """
    try:
        # Redis 연결 (실제 환경변수 사용)
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
        )

        # Redis 연결 테스트
        ping_result = r.ping()

        # 큐 길이 확인
        celery_len = r.llen("celery")
        default_len = r.llen("default")

        # 큐 데이터 확인 (최대 5개씩)
        celery_data = r.lrange("celery", 0, 4)
        default_data = r.lrange("default", 0, 4)

        # 모든 키 확인 (celery 관련)
        all_keys = r.keys("*")
        celery_keys = [key for key in all_keys if "celery" in key.lower()]

        # Redis 정보
        redis_info = {
            "connection": "성공",
            "ping": ping_result,
            "host": os.getenv('REDIS_HOST', 'redis'),
            "port": os.getenv('REDIS_PORT', '6379'),
            "total_keys": len(all_keys),
            "celery_related_keys": celery_keys,
        }

        # 큐 상태 정보
        queue_status = {
            "celery": {"length": celery_len, "data": celery_data, "sample_parsed": []},
            "default": {
                "length": default_len,
                "data": default_data,
                "sample_parsed": [],
            },
        }

        # celery 큐 데이터 파싱 시도 (JSON 형태인지 확인)
        for item in celery_data[:3]:  # 최대 3개만 파싱
            try:
                parsed = json.loads(item)
                queue_status["celery"]["sample_parsed"].append(parsed)
            except:
                queue_status["celery"]["sample_parsed"].append(
                    f"파싱 실패: {item[:100]}..."
                )

        # default 큐 데이터 파싱 시도
        for item in default_data[:3]:  # 최대 3개만 파싱
            try:
                parsed = json.loads(item)
                queue_status["default"]["sample_parsed"].append(parsed)
            except:
                queue_status["default"]["sample_parsed"].append(
                    f"파싱 실패: {item[:100]}..."
                )

        return {
            "timestamp": datetime.now().isoformat(),
            "redis_info": redis_info,
            "queue_status": queue_status,
            "summary": {
                "total_tasks": celery_len + default_len,
                "celery_tasks": celery_len,
                "default_tasks": default_len,
                "status": "정상" if ping_result else "연결 실패",
            },
        }

    except redis.ConnectionError as e:
        # Redis 연결 실패
        return {
            "timestamp": datetime.now().isoformat(),
            "error": "Redis 연결 실패",
            "details": str(e),
            "redis_config": {
                "host": os.getenv("REDIS_HOST", "redis"),
                "port": os.getenv("REDIS_PORT", "6379"),
            },
        }
    except Exception as e:
        # 기타 에러
        return {
            "timestamp": datetime.now().isoformat(),
            "error": "예상치 못한 에러 발생",
            "details": str(e),
            "type": type(e).__name__,
        }


@router.post("/debug/redis-test-task")
def debug_test_redis_task():
    """
    Redis에 테스트 태스크를 직접 삽입해서 큐 동작 확인
    """
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
        )

        # 테스트 태스크 데이터 생성
        test_task = {
            "id": f"test-task-{datetime.now().timestamp()}",
            "task": "app.tasks.email_tasks.send_test_email",
            "args": ["test@example.com"],
            "kwargs": {},
            "retries": 0,
            "eta": None,
            "expires": None,
            "utc": True,
            "callbacks": None,
            "errbacks": None,
            "timelimit": [None, None],
            "taskset": None,
            "chord": None,
            "reply_to": None,
            "correlation_id": None,
            "headers": {},
            "origin": "debug_endpoint",
        }

        # celery 큐에 직접 삽입
        result = r.lpush("celery", json.dumps(test_task))

        # 삽입 후 큐 상태 확인
        celery_len_after = r.llen("celery")

        return {
            "timestamp": datetime.now().isoformat(),
            "action": "테스트 태스크 삽입 완료",
            "result": result,
            "celery_queue_length_after": celery_len_after,
            "test_task_id": test_task["id"],
            "message": "Celery worker가 동작 중이라면 곧 이 태스크를 처리해야 합니다.",
        }

    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": "테스트 태스크 삽입 실패",
            "details": str(e),
            "type": type(e).__name__,
        }


@router.delete("/debug/redis-clear-queue/{queue_name}")
def debug_clear_redis_queue(queue_name: str):
    """
    지정된 큐를 비우는 디버그 엔드포인트 (주의: 실제 태스크 삭제됨)
    """
    if queue_name not in ["celery", "default"]:
        raise HTTPException(status_code=400, detail="허용된 큐 이름: celery, default")

    try:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
        )

        # 큐 비우기 전 길이 확인
        length_before = r.llen(queue_name)

        # 큐 비우기
        r.delete(queue_name)

        # 비운 후 길이 확인
        length_after = r.llen(queue_name)

        return {
            "timestamp": datetime.now().isoformat(),
            "action": f"{queue_name} 큐 비우기 완료",
            "length_before": length_before,
            "length_after": length_after,
            "deleted_tasks": length_before,
        }

    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": f"{queue_name} 큐 비우기 실패",
            "details": str(e),
            "type": type(e).__name__,
        }
