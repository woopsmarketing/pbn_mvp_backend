"""
작업 모니터링 API 엔드포인트
- 작업 상태 조회 및 통계 제공
- 실패한 작업 리스트 조회
- Docker 환경에서도 동작하는 모니터링 인터페이스
- v1.0 - 초기 구현 (2025.01.08)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.task_tracker import get_task_tracker, TaskTracker
from app.db.models.task_result import TaskResult

router = APIRouter()


@router.get("/tasks/statistics", response_model=Dict[str, Any])
async def get_task_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    작업 통계 정보 조회
    - 전체/성공/실패/대기 작업 수
    - 성공률 계산
    """
    try:
        tracker = get_task_tracker(db)
        stats = tracker.get_task_statistics()

        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 통계 조회 실패: {str(e)}")


@router.get("/tasks/status/{task_id}")
async def get_task_status(
    task_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    특정 작업의 상태 조회
    """
    try:
        tracker = get_task_tracker(db)
        task_result = tracker.get_task_status(task_id)

        if not task_result:
            raise HTTPException(
                status_code=404, detail=f"작업을 찾을 수 없습니다: {task_id}"
            )

        return {
            "success": True,
            "data": {
                "task_id": task_result.task_id,
                "task_name": task_result.task_name,
                "status": task_result.status,
                "created_at": (
                    task_result.created_at.isoformat()
                    if task_result.created_at
                    else None
                ),
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
                "duration_seconds": task_result.duration_seconds,
                "worker_name": task_result.worker_name,
                "retry_count": task_result.retry_count,
                "is_critical": task_result.is_critical,
                "result": task_result.result,
                "error_message": task_result.error_message,
                "is_completed": task_result.is_completed,
                "is_successful": task_result.is_successful,
                "needs_retry": task_result.needs_retry,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 상태 조회 실패: {str(e)}")


@router.get("/tasks/failed", response_model=Dict[str, Any])
async def get_failed_tasks(
    limit: int = Query(default=50, ge=1, le=200),
    critical_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    실패한 작업 목록 조회
    - 최근 실패한 작업들을 시간순으로 정렬
    - 중요 작업만 필터링 옵션
    """
    try:
        tracker = get_task_tracker(db)

        if critical_only:
            failed_tasks = tracker.get_critical_failures(limit)
        else:
            failed_tasks = tracker.get_failed_tasks(limit)

        tasks_data = []
        for task in failed_tasks:
            tasks_data.append(
                {
                    "task_id": task.task_id,
                    "task_name": task.task_name,
                    "status": task.status,
                    "completed_at": (
                        task.completed_at.isoformat() if task.completed_at else None
                    ),
                    "error_message": task.error_message,
                    "retry_count": task.retry_count,
                    "max_retries": task.max_retries,
                    "is_critical": task.is_critical,
                    "worker_name": task.worker_name,
                    "needs_retry": task.needs_retry,
                }
            )

        return {
            "success": True,
            "data": {
                "failed_tasks": tasks_data,
                "total_count": len(tasks_data),
                "critical_only": critical_only,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"실패한 작업 목록 조회 실패: {str(e)}"
        )


@router.get("/tasks/recent", response_model=Dict[str, Any])
async def get_recent_tasks(
    hours: int = Query(default=24, ge=1, le=168),  # 최대 1주일
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    최근 작업 목록 조회
    - 지정된 시간 범위 내의 작업들
    - 상태별 필터링 가능
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = db.query(TaskResult).filter(TaskResult.created_at >= cutoff_time)

        if status:
            query = query.filter(TaskResult.status == status.upper())

        recent_tasks = query.order_by(TaskResult.created_at.desc()).limit(limit).all()

        tasks_data = []
        for task in recent_tasks:
            tasks_data.append(
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
                    "duration_seconds": task.duration_seconds,
                    "is_critical": task.is_critical,
                    "worker_name": task.worker_name,
                    "error_message": (
                        task.error_message if task.status == "FAILURE" else None
                    ),
                }
            )

        return {
            "success": True,
            "data": {
                "recent_tasks": tasks_data,
                "total_count": len(tasks_data),
                "time_range_hours": hours,
                "status_filter": status,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"최근 작업 목록 조회 실패: {str(e)}"
        )


@router.get("/system/health", response_model=Dict[str, Any])
async def get_system_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    시스템 전체 상태 확인
    - 데이터베이스 연결 상태
    - 최근 작업 실행 상태
    - 시스템 통계
    """
    try:
        health_status = {
            "database": "healthy",
            "task_system": "unknown",
            "last_check": datetime.utcnow().isoformat(),
        }

        # 데이터베이스 연결 테스트
        try:
            db.execute("SELECT 1")
            health_status["database"] = "healthy"
        except Exception as e:
            health_status["database"] = "error"
            health_status["database_error"] = str(e)

        # 최근 작업 실행 상태 확인 (지난 1시간)
        try:
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            recent_tasks = (
                db.query(TaskResult)
                .filter(TaskResult.created_at >= recent_cutoff)
                .count()
            )

            if recent_tasks > 0:
                health_status["task_system"] = "active"
                health_status["recent_tasks_count"] = recent_tasks
            else:
                health_status["task_system"] = "idle"
                health_status["recent_tasks_count"] = 0

        except Exception as e:
            health_status["task_system"] = "error"
            health_status["task_system_error"] = str(e)

        # 전체 시스템 상태 결정
        overall_status = "healthy"
        if health_status["database"] != "healthy":
            overall_status = "error"
        elif health_status["task_system"] == "error":
            overall_status = "warning"

        return {
            "success": True,
            "overall_status": overall_status,
            "components": health_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 상태 확인 실패: {str(e)}")


@router.post("/tasks/cleanup", response_model=Dict[str, Any])
async def cleanup_old_tasks(
    days: int = Query(default=30, ge=7, le=365),
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    오래된 작업 결과 정리
    - 지정된 일수보다 오래된 완료된 작업들 삭제
    - dry_run 모드로 안전하게 테스트 가능
    """
    try:
        if dry_run:
            # 삭제 예정 작업 수만 계산
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            count = (
                db.query(TaskResult)
                .filter(
                    TaskResult.completed_at < cutoff_date,
                    TaskResult.status.in_(["SUCCESS", "FAILURE"]),
                )
                .count()
            )

            return {
                "success": True,
                "data": {
                    "dry_run": True,
                    "would_delete_count": count,
                    "cutoff_date": cutoff_date.isoformat(),
                    "days": days,
                },
                "message": f"{count}개의 작업 결과가 삭제 예정입니다 (실제 삭제되지 않음)",
            }
        else:
            # 실제 정리 실행
            tracker = get_task_tracker(db)
            deleted_count = tracker.cleanup_old_results(days)

            return {
                "success": True,
                "data": {
                    "dry_run": False,
                    "deleted_count": deleted_count,
                    "days": days,
                },
                "message": f"{deleted_count}개의 오래된 작업 결과를 정리했습니다",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 결과 정리 실패: {str(e)}")
