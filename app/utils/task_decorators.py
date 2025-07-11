# Task Decorators - Celery 작업 추적 데코레이터
# v1.0 - 작업 결과 추적 및 오류 처리 구현 (2024.01.05)

from functools import wraps
from typing import Callable, Any, Dict, List
import traceback
import logging
from datetime import datetime

from app.services.task_tracker import TaskTracker

logger = logging.getLogger(__name__)


def track_task_execution(func: Callable) -> Callable:
    """
    Celery 작업 실행을 자동으로 추적하는 데코레이터

    사용법:
    @celery_app.task
    @track_task_execution
    def my_task(arg1, arg2):
        return "완료"
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        task_id = None
        task_name = func.__name__

        try:
            # Celery 작업 컨텍스트에서 task_id 가져오기
            if hasattr(self, "request"):
                task_id = self.request.id
                worker_name = getattr(self.request, "hostname", None)
                queue_name = getattr(self.request, "delivery_info", {}).get(
                    "routing_key", None
                )
                eta = getattr(self.request, "eta", None)

                # 작업 시작 추적
                TaskTracker.track_task_start(
                    task_id=task_id,
                    task_name=task_name,
                    args=list(args),
                    kwargs=kwargs,
                    worker_name=worker_name,
                    queue_name=queue_name,
                    eta=eta,
                )

            # 실제 작업 실행
            result = func(self, *args, **kwargs)

            # 작업 성공 추적
            if task_id:
                result_data = {
                    "result": (
                        result
                        if isinstance(result, (dict, list, str, int, float, bool))
                        else str(result)
                    ),
                    "completed_at": datetime.utcnow().isoformat(),
                }
                TaskTracker.track_task_success(task_id, result_data)

            return result

        except Exception as e:
            # 작업 실패 추적
            if task_id:
                error_message = str(e)
                traceback_info = traceback.format_exc()
                TaskTracker.track_task_failure(task_id, error_message, traceback_info)

            # 오류 재발생 (Celery가 처리하도록)
            raise

    return wrapper


def track_retry_task(func: Callable) -> Callable:
    """
    Celery 작업 재시도를 추적하는 데코레이터

    사용법:
    @celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
    @track_retry_task
    @track_task_execution
    def my_retry_task(self, arg1):
        # 작업 로직
        pass
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        task_id = None

        try:
            # 재시도 정보 확인
            if hasattr(self, "request"):
                task_id = self.request.id
                retries = getattr(self.request, "retries", 0)

                # 재시도인 경우 추적
                if retries > 0:
                    TaskTracker.track_task_retry(task_id)

            # 실제 작업 실행
            return func(self, *args, **kwargs)

        except Exception as e:
            # 재시도 여부 판단 후 추적
            if task_id and hasattr(self, "retry"):
                try:
                    # Celery에서 재시도를 시도하게 함
                    raise self.retry(exc=e)
                except Exception:
                    # 재시도 한도 초과 시 실패로 처리
                    raise e
            else:
                raise e

    return wrapper


class TaskExecutionContext:
    """
    작업 실행 컨텍스트 관리자

    사용법:
    with TaskExecutionContext("manual_task") as ctx:
        # 수동 작업 실행
        result = do_something()
        ctx.set_result(result)
    """

    def __init__(self, task_name: str, manual_task_id: str = None):
        self.task_name = task_name
        self.task_id = (
            manual_task_id
            or f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{task_name}"
        )
        self.task_result = None

    def __enter__(self):
        """컨텍스트 시작"""
        try:
            self.task_result = TaskTracker.track_task_start(
                task_id=self.task_id, task_name=self.task_name, worker_name="manual"
            )
            return self
        except Exception as e:
            logger.error(f"수동 작업 시작 추적 실패: {e}")
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 종료"""
        try:
            if exc_type is None:
                # 성공적으로 완료
                if not hasattr(self, "_result_set"):
                    TaskTracker.track_task_success(
                        self.task_id, {"status": "completed"}
                    )
            else:
                # 예외 발생
                error_message = str(exc_val) if exc_val else "Unknown error"
                traceback_info = traceback.format_exc() if exc_tb else None
                TaskTracker.track_task_failure(
                    self.task_id, error_message, traceback_info
                )
        except Exception as e:
            logger.error(f"수동 작업 종료 추적 실패: {e}")

        # 예외 억제하지 않음 (원래 예외가 재발생)
        return False

    def set_result(self, result_data: Any):
        """작업 결과 설정"""
        try:
            formatted_result = {
                "result": (
                    result_data
                    if isinstance(result_data, (dict, list, str, int, float, bool))
                    else str(result_data)
                ),
                "completed_at": datetime.utcnow().isoformat(),
            }
            TaskTracker.track_task_success(self.task_id, formatted_result)
            self._result_set = True
        except Exception as e:
            logger.error(f"수동 작업 결과 설정 실패: {e}")


def create_manual_task_tracker(task_name: str) -> TaskExecutionContext:
    """
    수동 작업 추적기 생성 (편의 함수)

    Args:
        task_name: 작업 이름

    Returns:
        TaskExecutionContext: 작업 실행 컨텍스트
    """
    return TaskExecutionContext(task_name)


# 로깅 설정 함수
def setup_task_logging():
    """작업 추적을 위한 로깅 설정"""
    # 작업 추적 전용 로거 설정
    task_logger = logging.getLogger("task_tracker")
    task_logger.setLevel(logging.INFO)

    # 파일 핸들러 추가 (옵션)
    if not task_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        task_logger.addHandler(handler)

    return task_logger
