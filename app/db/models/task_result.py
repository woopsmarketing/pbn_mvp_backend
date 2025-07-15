"""
작업 결과 추적 모델
- Celery 작업의 실행 결과를 데이터베이스에 저장
- 작업 상태, 결과, 오류 정보 등을 추적
- 모니터링 및 디버깅 용도로 활용
"""

from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
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
    """작업 결과 추적 테이블"""

    __tablename__ = "task_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(
        String(255), unique=True, index=True, nullable=False, comment="Celery 작업 ID"
    )
    task_name = Column(String(255), nullable=False, comment="작업 이름")

    # 작업 상태 정보
    status = Column(
        String(50),
        nullable=False,
        default="PENDING",
        comment="작업 상태 (PENDING, STARTED, SUCCESS, FAILURE, RETRY)",
    )

    # 시간 정보
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="작업 생성 시간"
    )
    started_at = Column(
        DateTime(timezone=True), nullable=True, comment="작업 시작 시간"
    )
    completed_at = Column(
        DateTime(timezone=True), nullable=True, comment="작업 완료 시간"
    )

    # 결과 정보
    result = Column(JSON, nullable=True, comment="작업 결과 데이터")
    error_message = Column(Text, nullable=True, comment="오류 메시지")
    traceback = Column(Text, nullable=True, comment="오류 스택 트레이스")

    # 실행 정보
    worker_name = Column(String(255), nullable=True, comment="실행한 워커 이름")
    retry_count = Column(Integer, default=0, comment="재시도 횟수")
    max_retries = Column(Integer, default=3, comment="최대 재시도 횟수")

    # 메타데이터
    duration_seconds = Column(Integer, nullable=True, comment="실행 시간(초)")
    is_critical = Column(Boolean, default=False, comment="중요 작업 여부")
    metadata = Column(JSON, nullable=True, comment="추가 메타데이터")

    def __repr__(self):
        return f"<TaskResult(task_id='{self.task_id}', status='{self.status}', task_name='{self.task_name}')>"

    @property
    def is_completed(self):
        """작업이 완료되었는지 확인"""
        return self.status in ["SUCCESS", "FAILURE"]

    @property
    def is_successful(self):
        """작업이 성공했는지 확인"""
        return self.status == "SUCCESS"

    @property
    def needs_retry(self):
        """재시도가 필요한지 확인"""
        return self.status == "FAILURE" and self.retry_count < self.max_retries
