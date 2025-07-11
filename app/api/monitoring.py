# Monitoring API - 작업 추적 모니터링 엔드포인트
# v1.0 - 작업 결과 추적 및 오류 처리 구현 (2024.01.05)

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.services.task_tracker import TaskTracker
from app.models.task_result import TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["모니터링"])


@router.get("/tasks/statistics", summary="작업 통계 조회")
async def get_task_statistics(
    days: int = Query(7, description="조회할 일수", ge=1, le=365)
) -> Dict[str, Any]:
    """
    지정된 기간 동안의 작업 실행 통계를 조회합니다.

    - **days**: 조회할 일수 (1-365일)

    반환 정보:
    - 전체 작업 수
    - 상태별 작업 분류
    - 작업 유형별 성공률
    - 평균 실행 시간
    """
    try:
        statistics = TaskTracker.get_task_statistics(days=days)
        return {"success": True, "data": statistics}
    except Exception as e:
        logger.error(f"작업 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/tasks/status/{task_id}", summary="특정 작업 상태 조회")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    특정 Celery 작업의 상태와 실행 정보를 조회합니다.

    - **task_id**: Celery 작업 ID
    """
    try:
        task_info = TaskTracker.get_task_by_id(task_id)

        if not task_info:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

        return {"success": True, "data": task_info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")


@router.get("/tasks/failed", summary="실패한 작업 목록 조회")
async def get_failed_tasks(
    limit: int = Query(50, description="조회할 최대 개수", ge=1, le=500)
) -> Dict[str, Any]:
    """
    최근 실패한 작업들의 목록을 조회합니다.

    - **limit**: 조회할 최대 개수 (1-500개)
    """
    try:
        failed_tasks = TaskTracker.get_failed_tasks(limit=limit)

        return {
            "success": True,
            "data": {"failed_tasks": failed_tasks, "total": len(failed_tasks)},
        }
    except Exception as e:
        logger.error(f"실패 작업 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"실패 작업 조회 실패: {str(e)}")


@router.get("/tasks/recent", summary="최근 작업 목록 조회")
async def get_recent_tasks(
    limit: int = Query(100, description="조회할 최대 개수", ge=1, le=1000),
    hours: int = Query(24, description="조회할 시간 범위(시간)", ge=1, le=168),
) -> Dict[str, Any]:
    """
    최근 실행된 작업들의 목록을 조회합니다.

    - **limit**: 조회할 최대 개수 (1-1000개)
    - **hours**: 조회할 시간 범위 (1-168시간, 1주일)
    """
    try:
        recent_tasks = TaskTracker.get_recent_tasks(limit=limit, hours=hours)

        return {
            "success": True,
            "data": {
                "recent_tasks": recent_tasks,
                "total": len(recent_tasks),
                "time_range_hours": hours,
            },
        }
    except Exception as e:
        logger.error(f"최근 작업 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"최근 작업 조회 실패: {str(e)}")


@router.get("/system/health", summary="시스템 건강 상태 확인")
async def get_system_health() -> Dict[str, Any]:
    """
    작업 추적 시스템의 전반적인 건강 상태를 확인합니다.

    반환 정보:
    - 최근 24시간 작업 통계
    - 실패율
    - 시스템 상태 평가
    """
    try:
        # 최근 24시간 통계
        stats_24h = TaskTracker.get_task_statistics(days=1)

        # 건강 상태 평가
        total_tasks = stats_24h.get("total_tasks", 0)
        failed_count = stats_24h.get("status_breakdown", {}).get(TaskStatus.FAILURE, 0)

        # 실패율 계산
        failure_rate = (failed_count / total_tasks * 100) if total_tasks > 0 else 0

        # 상태 판정
        if failure_rate < 5:
            health_status = "excellent"
            health_message = "시스템이 정상 작동 중입니다."
        elif failure_rate < 15:
            health_status = "good"
            health_message = "시스템이 양호한 상태입니다."
        elif failure_rate < 30:
            health_status = "warning"
            health_message = "주의가 필요한 상태입니다."
        else:
            health_status = "critical"
            health_message = "시스템 점검이 필요합니다."

        return {
            "success": True,
            "data": {
                "health_status": health_status,
                "health_message": health_message,
                "metrics": {
                    "total_tasks_24h": total_tasks,
                    "failed_tasks_24h": failed_count,
                    "failure_rate_percent": round(failure_rate, 2),
                    "average_duration_seconds": stats_24h.get(
                        "average_duration_seconds", 0
                    ),
                },
                "last_check": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"시스템 건강 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=f"건강 상태 확인 실패: {str(e)}")


@router.post("/tasks/cleanup", summary="오래된 작업 결과 정리")
async def cleanup_old_tasks(
    days: int = Query(30, description="보관할 일수", ge=7, le=365)
) -> Dict[str, Any]:
    """
    지정된 일수보다 오래된 성공한 작업 결과를 정리합니다.
    (실패한 작업은 디버깅을 위해 보관됩니다)

    - **days**: 보관할 일수 (7-365일)
    """
    try:
        deleted_count = TaskTracker.cleanup_old_results(days=days)

        return {
            "success": True,
            "data": {
                "deleted_count": deleted_count,
                "retention_days": days,
                "cleanup_time": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"작업 결과 정리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"정리 작업 실패: {str(e)}")


@router.get("/tasks/summary", summary="작업 요약 정보")
async def get_tasks_summary() -> Dict[str, Any]:
    """
    작업 추적 시스템의 요약 정보를 제공합니다.

    반환 정보:
    - 최근 1시간, 24시간, 7일 통계
    - 가장 자주 실행되는 작업들
    - 가장 자주 실패하는 작업들
    """
    try:
        # 다양한 시간대 통계
        stats_1d = TaskTracker.get_task_statistics(days=1)
        stats_7d = TaskTracker.get_task_statistics(days=7)

        # 최근 실패 작업
        recent_failures = TaskTracker.get_failed_tasks(limit=10)

        return {
            "success": True,
            "data": {
                "period_comparison": {
                    "last_24_hours": {
                        "total_tasks": stats_1d.get("total_tasks", 0),
                        "success_rate": (
                            (
                                (
                                    stats_1d.get("status_breakdown", {}).get(
                                        TaskStatus.SUCCESS, 0
                                    )
                                    / stats_1d.get("total_tasks", 1)
                                )
                                * 100
                            )
                            if stats_1d.get("total_tasks", 0) > 0
                            else 0
                        ),
                    },
                    "last_7_days": {
                        "total_tasks": stats_7d.get("total_tasks", 0),
                        "success_rate": (
                            (
                                (
                                    stats_7d.get("status_breakdown", {}).get(
                                        TaskStatus.SUCCESS, 0
                                    )
                                    / stats_7d.get("total_tasks", 1)
                                )
                                * 100
                            )
                            if stats_7d.get("total_tasks", 0) > 0
                            else 0
                        ),
                    },
                },
                "top_task_types": stats_7d.get("task_types", [])[:5],
                "recent_failures_count": len(recent_failures),
                "generated_at": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"작업 요약 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 조회 실패: {str(e)}")


# 에러 핸들러
# router.exception_handler는 APIRouter에 없으므로 FastAPI 앱 레벨에서 처리해야 함
# @router.exception_handler(HTTPException)
# async def http_exception_handler(request, exc):
#     """HTTP 예외 핸들러"""
#     logger.error(f"API 오류 - {request.url}: {exc.detail}")
#     return {"success": False, "error": exc.detail, "status_code": exc.status_code}
