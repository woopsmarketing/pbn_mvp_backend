# TaskResult 모델 - Celery 작업 실행 결과 추적
# v1.0 - 작업 결과 추적 및 오류 처리 구현 (2024.01.05)

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from app.db.base import Base


class TaskStatus(str, Enum):
    """작업 상태 열거형"""

    PENDING = "PENDING"  # 대기 중
    STARTED = "STARTED"  # 시작됨
    SUCCESS = "SUCCESS"  # 성공
    FAILURE = "FAILURE"  # 실패
    RETRY = "RETRY"  # 재시도 중
    REVOKED = "REVOKED"  # 취소됨


class TaskResult(Base):
    """
    Celery 작업 실행 결과를 추적하는 모델

    사용 예시:
    - 작업 시작 시: TaskResult.create_task(task_id, task_name)
    - 작업 완료 시: task_result.mark_success(result_data)
    - 작업 실패 시: task_result.mark_failure(error_msg, traceback)
    """

    __tablename__ = "task_results"

    # 기본 식별 정보
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    task_id = Column(
        String(255), unique=True, nullable=False, index=True
    )  # Celery 작업 ID
    task_name = Column(String(255), nullable=False, index=True)  # 작업 함수명

    # 작업 상태
    status = Column(String(50), default=TaskStatus.PENDING, index=True)

    # 시간 정보
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 실행 결과
    result = Column(JSONB)  # 성공 시 결과 데이터
    error_message = Column(Text)  # 오류 메시지
    traceback = Column(Text)  # 전체 오류 스택 트레이스

    # 실행 환경
    worker_name = Column(String(255), index=True)  # 실행한 워커 이름
    queue_name = Column(String(255))  # 큐 이름

    # 재시도 정보
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 메타데이터
    args = Column(JSONB)  # 작업 인수
    kwargs = Column(JSONB)  # 작업 키워드 인수
    eta = Column(DateTime(timezone=True))  # 예상 실행 시간

    @classmethod
    def create_task(
        cls,
        task_id: str,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        eta: Optional[datetime] = None,
    ) -> "TaskResult":
        """새 작업 추적 레코드 생성"""
        return cls(
            task_id=task_id,
            task_name=task_name,
            status=TaskStatus.PENDING,
            args=args or [],
            kwargs=kwargs or {},
            eta=eta,
        )

    def mark_started(self, worker_name: str = None, queue_name: str = None) -> None:
        """작업 시작 표시"""
        self.status = TaskStatus.STARTED
        self.started_at = datetime.utcnow()
        if worker_name:
            self.worker_name = worker_name
        if queue_name:
            self.queue_name = queue_name

    def mark_success(self, result_data: Optional[Dict[str, Any]] = None) -> None:
        """작업 성공 표시"""
        self.status = TaskStatus.SUCCESS
        self.completed_at = datetime.utcnow()
        if result_data:
            self.result = result_data

    def mark_failure(self, error_message: str, traceback_info: str = None) -> None:
        """작업 실패 표시"""
        self.status = TaskStatus.FAILURE
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        if traceback_info:
            self.traceback = traceback_info

    def mark_retry(self) -> None:
        """재시도 표시"""
        self.status = TaskStatus.RETRY
        self.retry_count += 1

    def mark_revoked(self) -> None:
        """작업 취소 표시"""
        self.status = TaskStatus.REVOKED
        self.completed_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> Optional[float]:
        """작업 실행 시간 (초)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """작업이 완료되었는지 확인"""
        return self.status in [
            TaskStatus.SUCCESS,
            TaskStatus.FAILURE,
            TaskStatus.REVOKED,
        ]

    @property
    def is_successful(self) -> bool:
        """작업이 성공했는지 확인"""
        return self.status == TaskStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (API 응답용)"""
        return {
            "id": str(self.id),
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "duration_seconds": self.duration_seconds,
            "result": self.result,
            "error_message": self.error_message,
            "worker_name": self.worker_name,
            "queue_name": self.queue_name,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "args": self.args,
            "kwargs": self.kwargs,
        }

    def __repr__(self):
        return f"<TaskResult(task_id='{self.task_id}', task_name='{self.task_name}', status='{self.status}')>"
