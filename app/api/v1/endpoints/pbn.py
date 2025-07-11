from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.clerk_jwt import get_current_clerk_user
from app.db.models import User, Order
from app.tasks.pbn_tasks import create_pbn_backlink_task
from pydantic import BaseModel
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class PbnSampleRequest(BaseModel):
    target_url: str
    keyword: str


@router.post("/pbn/sample-request")
async def sample_request(
    request: PbnSampleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user),
):
    """
    무료 PBN 백링크 구축 요청
    - 사용자 Clerk JWT 토큰 검증
    - 주문 정보 DB 저장
    - Celery 백그라운드 작업 시작
    """
    try:
        # Clerk JWT 토큰에서 사용자 ID 추출 (sub 키 사용)
        clerk_id = current_user.get("sub")
        if not clerk_id:
            logger.error("Clerk ID missing from token")
            raise HTTPException(status_code=400, detail="Clerk ID가 토큰에 없습니다")

        logger.info(f"PBN sample request from clerk_id: {clerk_id}")

        # 사용자 확인 (clerk_id로 조회)
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="사용자를 찾을 수 없습니다. 먼저 /verify 엔드포인트를 통해 인증해주세요.",
            )

        logger.info(f"User found: {user.id} ({user.email})")

        # 주문 생성
        new_order = Order(
            user_id=user.id,
            type="free_pbn",
            status="pending",
            amount=0.00,
            payment_status="paid",  # 무료이므로 바로 paid 상태
            order_metadata={
                "target_url": request.target_url,
                "keyword": request.keyword,
                "request_type": "sample",
                "pbn_count": 1,
            },
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        logger.info(f"Order created: {new_order.id}")

        # Celery 태스크 실행
        task_result = create_pbn_backlink_task.delay(
            order_id=str(new_order.id),
            target_url=request.target_url,
            anchor_text=request.keyword,
            keywords=[request.keyword],
        )

        logger.info(f"Celery task started: {task_result.id}")

        return {
            "success": True,
            "message": "무료 PBN 백링크 구축이 시작되었습니다",
            "order_id": str(new_order.id),
            "task_id": task_result.id,
            "estimated_completion": "5-10분",
            "user_email": user.email,
        }

    except Exception as e:
        logger.error(f"PBN sample request failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"요청 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/pbn/test-request")
async def test_request(
    request: PbnSampleRequest,
    db: Session = Depends(get_db),
):
    """
    개발 테스트용 PBN 백링크 구축 요청 (인증 없음, Celery 없음)
    - 테스트 사용자로 고정
    - 주문 정보 DB 저장
    - 즉시 완료 응답 반환 (Celery 없이)
    """
    try:
        logger.info(f"PBN test request: {request.target_url} - {request.keyword}")

        # 테스트용 사용자 조회 (기존 사용자 중 첫 번째)
        user = db.query(User).first()
        if not user:
            # 테스트용 사용자 생성
            test_user = User(
                email="test@followsales.com", clerk_id="test_clerk_123", role="user"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            user = test_user
            logger.info(f"Created test user: {user.id} ({user.email})")
        else:
            logger.info(f"Using existing user: {user.id} ({user.email})")

        # 주문 생성
        new_order = Order(
            user_id=user.id,
            type="free_pbn",
            status="completed",  # 즉시 완료 상태
            amount=0.00,
            payment_status="paid",
            order_metadata={
                "target_url": request.target_url,
                "keyword": request.keyword,
                "request_type": "test",
                "pbn_count": 1,
                "backlink_url": f"https://pbn-test-site.com/post-{hash(request.target_url) % 10000}",
                "completed_at": datetime.utcnow().isoformat(),
                "anchor_text": request.keyword,
            },
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        logger.info(f"Test order created and completed: {new_order.id}")

        return {
            "success": True,
            "message": "테스트 PBN 백링크 구축이 완료되었습니다",
            "order_id": str(new_order.id),
            "task_id": f"test-task-{new_order.id}",
            "estimated_completion": "즉시 완료",
            "user_email": user.email,
            "note": "개발 테스트용 요청입니다 (Celery 없이 즉시 완료)",
            "backlink_url": new_order.order_metadata.get("backlink_url"),
        }

    except Exception as e:
        logger.error(f"PBN test request failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"테스트 요청 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/pbn/orders/{order_id}/status")
async def get_order_status(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_clerk_user),
):
    """
    PBN 주문 상태 조회
    - 사용자의 주문 상태 및 진행률 확인
    """
    try:
        # Clerk JWT 토큰에서 사용자 ID 추출
        clerk_id = current_user.get("sub")
        if not clerk_id:
            logger.error("Clerk ID missing from token")
            raise HTTPException(status_code=400, detail="Clerk ID가 토큰에 없습니다")

        # 사용자 확인
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        # 주문 조회 (사용자 소유 주문만)
        order = (
            db.query(Order)
            .filter(Order.id == order_id, Order.user_id == user.id)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")

        return {
            "order_id": str(order.id),
            "status": order.status,
            "type": order.type,
            "created_at": order.created_at,
            "metadata": order.order_metadata,
            "user_email": user.email,
        }

    except Exception as e:
        logger.error(f"Order status check failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/pbn/test-orders/{order_id}/status")
async def get_test_order_status(
    order_id: str,
    db: Session = Depends(get_db),
):
    """
    테스트용 PBN 주문 상태 조회 (인증 없음)
    """
    try:
        # 주문 조회
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")

        # 사용자 정보 조회
        user = db.query(User).filter(User.id == order.user_id).first()

        return {
            "order_id": str(order.id),
            "status": order.status,
            "type": order.type,
            "created_at": order.created_at,
            "metadata": order.order_metadata,
            "user_email": user.email if user else "Unknown",
            "note": "테스트용 주문 조회",
        }

    except Exception as e:
        logger.error(f"Test order status check failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"테스트 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )
