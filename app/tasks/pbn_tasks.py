"""
PBN 백링크 구축 관련 Celery 태스크
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import Celery
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Order, User, PBNTask, PBNSite, EmailLog
import random
import time
from app.tasks.celery_app import celery as app

# 로깅 설정
logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def create_pbn_backlink_task(
    self, order_id: str, target_url: str, anchor_text: str, keywords: List[str]
):
    """
    PBN 백링크 구축 메인 태스크

    Args:
        order_id: 주문 ID
        target_url: 백링크를 받을 사이트 URL
        anchor_text: 앵커 텍스트 (키워드)
        keywords: 키워드 리스트
    """
    db = next(get_db())

    try:
        logger.info(f"PBN backlink task started for order: {order_id}")

        # 주문 정보 조회
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order not found: {order_id}")

        # 주문 상태를 '처리중'으로 변경
        order.status = "processing"

        # PBN 태스크 생성
        pbn_task = PBNTask(
            order_id=order.id,
            assigned_count=1,  # 무료는 1개
            completed_count=0,
            status="pending",
            target_url=target_url,
            anchor_text=anchor_text,
            keywords=keywords,
        )

        db.add(pbn_task)
        db.commit()
        db.refresh(pbn_task)

        logger.info(f"PBN task created: {pbn_task.id}")

        # 실제 PBN 백링크 구축 시뮬레이션
        # 실제 환경에서는 여기서 PBN 사이트에 글을 포스팅합니다
        success = simulate_pbn_posting(target_url, anchor_text, keywords)

        if success:
            # 성공 시 태스크 완료 처리
            pbn_task.completed_count = 1
            pbn_task.status = "completed"
            pbn_task.completed_at = datetime.utcnow()

            # 주문 상태를 '완료'로 변경
            order.status = "completed"

            # 백링크 정보를 order_metadata에 추가
            if not order.order_metadata:
                order.order_metadata = {}

            order.order_metadata.update(
                {
                    "backlink_url": f"https://pbn-site-example.com/post-{random.randint(1000, 9999)}",
                    "completed_at": datetime.utcnow().isoformat(),
                    "anchor_text": anchor_text,
                    "target_url": target_url,
                }
            )

            db.commit()

            logger.info(f"PBN task completed successfully: {pbn_task.id}")

            # 완료 이메일 발송 - 🔧 email_tasks.py의 함수로 통합
            from app.tasks.email_tasks import send_backlink_completion_email

            # 백링크 결과 데이터 준비
            backlink_result = {
                "success": True,
                "target_url": target_url,
                "keyword": anchor_text,
                "pbn_urls": (
                    [order.order_metadata.get("backlink_url", "")]
                    if order.order_metadata.get("backlink_url")
                    else []
                ),
                "total_backlinks": 1 if order.order_metadata.get("backlink_url") else 0,
                "pbn_domain": "example-pbn.com",  # 실제 PBN 도메인으로 교체 필요
                "backlink_url": order.order_metadata.get("backlink_url", ""),
            }

            # 사용자 이메일 가져오기
            user = db.query(User).filter(User.id == order.user_id).first()
            user_email = user.email if user else "vnfm0580@gmail.com"  # 기본값

            send_backlink_completion_email.delay(
                user_email, str(order.id), backlink_result
            )

            return {
                "success": True,
                "order_id": order_id,
                "pbn_task_id": str(pbn_task.id),
                "backlink_url": order.order_metadata.get("backlink_url"),
                "message": "PBN 백링크가 성공적으로 구축되었습니다",
            }
        else:
            # 실패 시 에러 처리
            pbn_task.status = "failed"
            order.status = "failed"
            db.commit()

            logger.error(f"PBN task failed: {pbn_task.id}")

            return {
                "success": False,
                "order_id": order_id,
                "message": "PBN 백링크 구축에 실패했습니다",
            }

    except Exception as e:
        logger.error(f"PBN task error: {str(e)}")

        # 에러 시 주문 상태 업데이트
        if "order" in locals():
            order.status = "failed"
            db.commit()

        # Celery 재시도
        raise self.retry(exc=e, countdown=60, max_retries=3)

    finally:
        db.close()


def simulate_pbn_posting(
    target_url: str, anchor_text: str, keywords: List[str]
) -> bool:
    """
    PBN 포스팅 시뮬레이션 함수
    실제 환경에서는 여기서 PBN 사이트에 글을 작성하고 백링크를 삽입합니다
    """
    try:
        logger.info(f"Starting PBN posting simulation for {target_url}")

        # 시뮬레이션: 5-15초 대기 (실제 포스팅 시간 시뮬레이션)
        wait_time = random.randint(5, 15)
        time.sleep(wait_time)

        # 시뮬레이션: 90% 성공률
        success_rate = 0.9
        success = random.random() < success_rate

        if success:
            logger.info(f"PBN posting simulation completed successfully")
        else:
            logger.warning(f"PBN posting simulation failed")

        return success

    except Exception as e:
        logger.error(f"PBN posting simulation error: {str(e)}")
        return False


@app.task
def process_scheduled_pbn_tasks():
    """
    스케줄된 PBN 태스크들을 처리하는 정기 작업
    """
    db = next(get_db())

    try:
        # 오래된 pending 태스크들을 조회 (30분 이상)
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)

        old_tasks = (
            db.query(PBNTask)
            .filter(PBNTask.status == "pending", PBNTask.created_at < cutoff_time)
            .all()
        )

        logger.info(f"Found {len(old_tasks)} old pending tasks to process")

        for task in old_tasks:
            try:
                # 관련 주문 정보 조회
                order = db.query(Order).filter(Order.id == task.order_id).first()
                if not order:
                    continue

                # 메타데이터에서 정보 추출
                target_url = order.order_metadata.get("target_url")
                keyword = order.order_metadata.get("keyword")

                if target_url and keyword:
                    # PBN 백링크 태스크 재시작
                    create_pbn_backlink_task.delay(
                        order_id=str(order.id),
                        target_url=target_url,
                        anchor_text=keyword,
                        keywords=[keyword],
                    )

                    logger.info(f"Restarted PBN task for order: {order.id}")

            except Exception as e:
                logger.error(f"Error processing old task {task.id}: {str(e)}")
                continue

        return {"processed_tasks": len(old_tasks)}

    except Exception as e:
        logger.error(f"Error in process_scheduled_pbn_tasks: {str(e)}")
        return {"error": str(e)}

    finally:
        db.close()


@app.task
def check_pbn_site_health():
    """
    PBN 사이트들의 상태를 체크하는 정기 작업
    """
    db = next(get_db())

    try:
        # 모든 활성 PBN 사이트 조회
        pbn_sites = db.query(PBNSite).filter(PBNSite.status == "active").all()

        healthy_sites = 0
        unhealthy_sites = 0

        for site in pbn_sites:
            try:
                # 실제 환경에서는 여기서 사이트 상태를 체크합니다
                # 현재는 시뮬레이션으로 처리
                is_healthy = random.random() > 0.1  # 90% 정상 가정

                if is_healthy:
                    site.last_check = datetime.utcnow()
                    healthy_sites += 1
                else:
                    site.status = "maintenance"
                    unhealthy_sites += 1
                    logger.warning(f"PBN site health check failed: {site.domain}")

            except Exception as e:
                logger.error(f"Error checking site {site.domain}: {str(e)}")
                unhealthy_sites += 1

        db.commit()

        logger.info(
            f"PBN health check completed. Healthy: {healthy_sites}, Unhealthy: {unhealthy_sites}"
        )

        return {
            "total_sites": len(pbn_sites),
            "healthy_sites": healthy_sites,
            "unhealthy_sites": unhealthy_sites,
        }

    except Exception as e:
        logger.error(f"Error in check_pbn_site_health: {str(e)}")
        return {"error": str(e)}

    finally:
        db.close()
