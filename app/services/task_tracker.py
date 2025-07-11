# TaskTracker 서비스 - Celery 작업 추적 및 관리
# v1.0 - 작업 결과 추적 및 오류 처리 구현 (2024.01.05)

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
import traceback as tb
import logging

from app.models.task_result import TaskResult, TaskStatus
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def get_db_session():
    """데이터베이스 세션을 생성하는 컨텍스트 매니저"""

    class DatabaseSession:
        def __enter__(self):
            self.db = SessionLocal()
            return self.db

        def __exit__(self, exc_type, exc_val, exc_tb):
            try:
                if exc_type:
                    self.db.rollback()
                else:
                    self.db.commit()
            finally:
                self.db.close()

    return DatabaseSession()


class TaskTracker:
    """
    Celery 작업 추적 및 관리 서비스

    주요 기능:
    1. 작업 시작/완료/실패 추적
    2. 작업 통계 제공
    3. 실패한 작업 관리
    4. 작업 결과 정리
    """

    @staticmethod
    def track_task_start(
        task_id: str,
        task_name: str,
        args: List = None,
        kwargs: Dict = None,
        worker_name: str = None,
        queue_name: str = None,
        eta: datetime = None,
    ) -> TaskResult:
        """
        작업 시작 추적

        Args:
            task_id: Celery 작업 ID
            task_name: 작업 함수명
            args: 작업 인수
            kwargs: 작업 키워드 인수
            worker_name: 워커 이름
            queue_name: 큐 이름
            eta: 예상 실행 시간

        Returns:
            TaskResult: 생성된 작업 추적 레코드
        """
        try:
            with get_db_session() as db:
                # 기존 레코드가 있는지 확인
                existing = (
                    db.query(TaskResult).filter(TaskResult.task_id == task_id).first()
                )

                if existing:
                    # 기존 레코드 업데이트
                    existing.mark_started(worker_name, queue_name)
                    task_result = existing
                else:
                    # 새 레코드 생성
                    task_result = TaskResult.create_task(
                        task_id=task_id,
                        task_name=task_name,
                        args=args,
                        kwargs=kwargs,
                        eta=eta,
                    )
                    task_result.mark_started(worker_name, queue_name)
                    db.add(task_result)

                logger.info(f"작업 시작 추적: {task_name} (ID: {task_id})")
                return task_result

        except Exception as e:
            logger.error(f"작업 시작 추적 실패: {e}")
            raise

    @staticmethod
    def track_task_success(
        task_id: str, result_data: Dict[str, Any] = None
    ) -> Optional[TaskResult]:
        """
        작업 성공 추적

        Args:
            task_id: Celery 작업 ID
            result_data: 작업 결과 데이터

        Returns:
            TaskResult: 업데이트된 작업 추적 레코드
        """
        try:
            with get_db_session() as db:
                task_result = (
                    db.query(TaskResult).filter(TaskResult.task_id == task_id).first()
                )

                if task_result:
                    task_result.mark_success(result_data)
                    logger.info(
                        f"작업 성공 추적: {task_result.task_name} (ID: {task_id})"
                    )
                    return task_result
                else:
                    logger.warning(f"작업 성공 추적 실패 - 레코드 없음: {task_id}")
                    return None

        except Exception as e:
            logger.error(f"작업 성공 추적 실패: {e}")
            raise

    @staticmethod
    def track_task_failure(
        task_id: str, error_message: str, traceback_info: str = None
    ) -> Optional[TaskResult]:
        """
        작업 실패 추적

        Args:
            task_id: Celery 작업 ID
            error_message: 오류 메시지
            traceback_info: 스택 트레이스

        Returns:
            TaskResult: 업데이트된 작업 추적 레코드
        """
        try:
            with get_db_session() as db:
                task_result = (
                    db.query(TaskResult).filter(TaskResult.task_id == task_id).first()
                )

                if task_result:
                    task_result.mark_failure(error_message, traceback_info)
                    logger.error(
                        f"작업 실패 추적: {task_result.task_name} (ID: {task_id}) - {error_message}"
                    )
                    return task_result
                else:
                    logger.warning(f"작업 실패 추적 실패 - 레코드 없음: {task_id}")
                    return None

        except Exception as e:
            logger.error(f"작업 실패 추적 실패: {e}")
            raise

    @staticmethod
    def track_task_retry(task_id: str) -> Optional[TaskResult]:
        """
        작업 재시도 추적

        Args:
            task_id: Celery 작업 ID

        Returns:
            TaskResult: 업데이트된 작업 추적 레코드
        """
        try:
            with get_db_session() as db:
                task_result = (
                    db.query(TaskResult).filter(TaskResult.task_id == task_id).first()
                )

                if task_result:
                    task_result.mark_retry()
                    logger.info(
                        f"작업 재시도 추적: {task_result.task_name} (ID: {task_id}, 시도: {task_result.retry_count})"
                    )
                    return task_result
                else:
                    logger.warning(f"작업 재시도 추적 실패 - 레코드 없음: {task_id}")
                    return None

        except Exception as e:
            logger.error(f"작업 재시도 추적 실패: {e}")
            raise

    @staticmethod
    def get_task_statistics(days: int = 7) -> Dict[str, Any]:
        """
        작업 통계 조회

        Args:
            days: 조회할 일수 (기본 7일)

        Returns:
            Dict: 작업 통계 정보
        """
        try:
            with get_db_session() as db:
                since_date = datetime.utcnow() - timedelta(days=days)

                # 전체 작업 수
                total_tasks = (
                    db.query(TaskResult)
                    .filter(TaskResult.created_at >= since_date)
                    .count()
                )

                # 상태별 작업 수
                status_counts = (
                    db.query(
                        TaskResult.status, func.count(TaskResult.id).label("count")
                    )
                    .filter(TaskResult.created_at >= since_date)
                    .group_by(TaskResult.status)
                    .all()
                )

                # 작업 유형별 통계
                task_type_stats = (
                    db.query(
                        TaskResult.task_name,
                        func.count(TaskResult.id).label("total"),
                        func.sum(
                            func.case(
                                (TaskResult.status == TaskStatus.SUCCESS, 1), else_=0
                            )
                        ).label("success"),
                        func.sum(
                            func.case(
                                (TaskResult.status == TaskStatus.FAILURE, 1), else_=0
                            )
                        ).label("failure"),
                    )
                    .filter(TaskResult.created_at >= since_date)
                    .group_by(TaskResult.task_name)
                    .all()
                )

                # 결과 구성
                status_breakdown = {status: count for status, count in status_counts}

                task_type_breakdown = {}
                for stat in task_type_stats:
                    task_type_breakdown[stat.task_name] = {
                        "total": stat.total,
                        "success": stat.success or 0,
                        "failure": stat.failure or 0,
                        "success_rate": (
                            (stat.success or 0) / stat.total * 100
                            if stat.total > 0
                            else 0
                        ),
                    }

                return {
                    "period_days": days,
                    "total_tasks": total_tasks,
                    "status_breakdown": status_breakdown,
                    "task_type_breakdown": task_type_breakdown,
                    "generated_at": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"작업 통계 조회 실패: {e}")
            raise

    @staticmethod
    def get_failed_tasks(limit: int = 50) -> List[Dict[str, Any]]:
        """
        실패한 작업 목록 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            List[Dict]: 실패한 작업 목록
        """
        try:
            with get_db_session() as db:
                failed_tasks = (
                    db.query(TaskResult)
                    .filter(TaskResult.status == TaskStatus.FAILURE)
                    .order_by(desc(TaskResult.updated_at))
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "task_id": task.task_id,
                        "task_name": task.task_name,
                        "error_message": task.error_message,
                        "retry_count": task.retry_count,
                        "failed_at": (
                            task.updated_at.isoformat() if task.updated_at else None
                        ),
                        "worker_name": task.worker_name,
                    }
                    for task in failed_tasks
                ]

        except Exception as e:
            logger.error(f"실패한 작업 조회 실패: {e}")
            raise

    @staticmethod
    def get_recent_tasks(limit: int = 100, hours: int = 24) -> List[Dict[str, Any]]:
        """
        최근 작업 목록 조회

        Args:
            limit: 조회할 최대 개수
            hours: 조회할 시간 범위 (시간)

        Returns:
            List[Dict]: 최근 작업 목록
        """
        try:
            with get_db_session() as db:
                since_time = datetime.utcnow() - timedelta(hours=hours)

                recent_tasks = (
                    db.query(TaskResult)
                    .filter(TaskResult.created_at >= since_time)
                    .order_by(desc(TaskResult.created_at))
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "task_id": task.task_id,
                        "task_name": task.task_name,
                        "status": task.status,
                        "created_at": (
                            task.created_at.isoformat() if task.created_at else None
                        ),
                        "completed_at": (
                            task.completed_at.isoformat() if task.completed_at else None
                        ),
                        "worker_name": task.worker_name,
                        "retry_count": task.retry_count,
                    }
                    for task in recent_tasks
                ]

        except Exception as e:
            logger.error(f"최근 작업 조회 실패: {e}")
            raise

    @staticmethod
    def cleanup_old_results(days: int = 30) -> int:
        """
        오래된 작업 결과 정리

        Args:
            days: 보관할 일수 (이보다 오래된 것은 삭제)

        Returns:
            int: 삭제된 레코드 수
        """
        try:
            with get_db_session() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days)

                # 완료된 작업만 삭제 (성공 또는 실패)
                deleted_count = (
                    db.query(TaskResult)
                    .filter(
                        and_(
                            TaskResult.created_at < cutoff_date,
                            TaskResult.status.in_(
                                [TaskStatus.SUCCESS, TaskStatus.FAILURE]
                            ),
                        )
                    )
                    .delete(synchronize_session=False)
                )

                logger.info(f"오래된 작업 결과 정리 완료: {deleted_count}개 삭제")
                return deleted_count

        except Exception as e:
            logger.error(f"작업 결과 정리 실패: {e}")
            raise

    @staticmethod
    def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
        """
        작업 ID로 작업 정보 조회

        Args:
            task_id: Celery 작업 ID

        Returns:
            Dict: 작업 정보 또는 None
        """
        try:
            with get_db_session() as db:
                task_result = (
                    db.query(TaskResult).filter(TaskResult.task_id == task_id).first()
                )

                if task_result:
                    return {
                        "task_id": task_result.task_id,
                        "task_name": task_result.task_name,
                        "status": task_result.status,
                        "result": task_result.result,
                        "error_message": task_result.error_message,
                        "traceback": task_result.traceback,
                        "started_at": (
                            task_result.started_at.isoformat()
                            if task_result.started_at
                            else None
                        ),
                        "completed_at": (
                            task_result.completed_at.isoformat()
                            if task_result.completed_at
                            else None
                        ),
                        "worker_name": task_result.worker_name,
                        "queue_name": task_result.queue_name,
                        "retry_count": task_result.retry_count,
                        "max_retries": task_result.max_retries,
                        "args": task_result.args,
                        "kwargs": task_result.kwargs,
                    }
                else:
                    return None

        except Exception as e:
            logger.error(f"작업 조회 실패: {e}")
            raise
