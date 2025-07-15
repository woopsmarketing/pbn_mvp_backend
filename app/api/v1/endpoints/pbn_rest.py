"""
PBN 백링크 구축 API (Supabase REST API 버전)
UTF-8 인코딩 문제 해결을 위해 PostgreSQL 직접 연결 대신 REST API 사용
v1.1 - print 구문 제거 및 로그 최적화 (2025.07.15)
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging

import os

from app.core.clerk_jwt import get_current_clerk_user  # 인증 확인용 (필요 시)
from app.services.supabase_client import supabase_client

import requests  # 임시: supabase_client를 사용하지 않는 헬퍼에서 사용

router = APIRouter()
logger = logging.getLogger(__name__)


class PbnSampleRequest(BaseModel):
    target_url: str
    keyword: str


def get_supabase_client():
    """Supabase REST API 클라이언트 설정"""
    return {
        "url": os.environ.get("SUPABASE_URL"),
        "anon_key": os.environ.get("SUPABASE_ANON_KEY"),
        "service_role_key": os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    }


def create_user_via_rest(user_data):
    """REST API를 통한 사용자 생성"""
    supabase = get_supabase_client()

    headers = {
        "apikey": supabase["service_role_key"],
        "Authorization": f"Bearer {supabase['service_role_key']}",
        "Content-Type": "application/json",
    }

    url = f"{supabase['url']}/rest/v1/users"

    response = requests.post(url, json=user_data, headers=headers)
    if response.status_code in [200, 201]:
        return response.json()[0] if response.json() else None
    else:
        logger.error(f"User creation failed: {response.status_code} - {response.text}")
        return None


def create_order_via_rest(order_data):
    """REST API를 통한 주문 생성"""
    supabase = get_supabase_client()

    headers = {
        "apikey": supabase["service_role_key"],
        "Authorization": f"Bearer {supabase['service_role_key']}",
        "Content-Type": "application/json",
    }

    url = f"{supabase['url']}/rest/v1/orders"

    response = requests.post(url, json=order_data, headers=headers)
    if response.status_code in [200, 201]:
        return response.json()[0] if response.json() else None
    else:
        logger.error(f"Order creation failed: {response.status_code} - {response.text}")
        return None


def get_user_via_rest(clerk_id):
    """REST API를 통한 사용자 조회"""
    supabase = get_supabase_client()

    headers = {
        "apikey": supabase["service_role_key"],
        "Authorization": f"Bearer {supabase['service_role_key']}",
        "Content-Type": "application/json",
    }

    url = f"{supabase['url']}/rest/v1/users?clerk_id=eq.{clerk_id}"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        users = response.json()
        return users[0] if users else None
    else:
        logger.error(f"User query failed: {response.status_code} - {response.text}")
        return None


def get_pbn_sites_via_rest():
    """REST API를 통한 PBN 사이트 조회"""
    supabase = get_supabase_client()

    headers = {
        "apikey": supabase["service_role_key"],
        "Authorization": f"Bearer {supabase['service_role_key']}",
        "Content-Type": "application/json",
    }

    url = f"{supabase['url']}/rest/v1/pbn_sites?status=eq.active"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(
            f"PBN sites query failed: {response.status_code} - {response.text}"
        )
        return []


@router.post("/pbn/rest-test-request")
async def rest_test_request(request: PbnSampleRequest):
    """REST API 기반 PBN 백링크 요청 처리"""
    logger.info(
        f"PBN 백링크 요청 시작: target_url={request.target_url}, keyword={request.keyword}"
    )

    try:
        # 1. PBN 사이트 활성 상태 확인
        pbn_sites = get_pbn_sites_via_rest()
        random_pbn = pbn_sites[0] if pbn_sites else None
        logger.debug(f"활성 PBN 사이트 조회 결과: {len(pbn_sites)}개")

        if not random_pbn:
            logger.warning("활성 PBN 사이트 없음")
            raise HTTPException(status_code=503, detail="No active PBN sites available")

        # 2. 테스트 사용자 조회 또는 생성
        test_clerk_id = "test_user_123"
        user = get_user_via_rest(test_clerk_id)

        if user:
            logger.debug(f"기존 사용자 사용: {user.get('id')}")
        else:
            # 새 사용자 생성
            user_data = {
                "clerk_id": test_clerk_id,
                "email": "test@example.com",
                "name": "Test User",
                "created_at": datetime.now().isoformat(),
            }
            user = create_user_via_rest(user_data)
            logger.info(f"새 사용자 생성: {user.get('id') if user else 'Failed'}")

        if not user:
            raise HTTPException(status_code=500, detail="Failed to create/get user")

        # 3. 주문 생성
        order_data = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "service_type": "pbn_backlink",
            "status": "pending",
            "target_url": request.target_url,
            "keyword": request.keyword,
            "quantity": 1,
            "price": 0.0,
            "created_at": datetime.now().isoformat(),
        }

        order = create_order_via_rest(order_data)
        logger.info(f"주문 생성 결과: {order.get('id') if order else 'Failed'}")

        if not order:
            logger.error("주문 생성 실패")
            raise HTTPException(status_code=500, detail="Failed to create order")

        order_id = order["id"]

        # 4. 이메일 확인 태스크 등록
        logger.info("이메일 태스크 등록 시도")

        try:
            from app.tasks.email_tasks import send_order_confirmation_email

            email_task_result = send_order_confirmation_email.delay(
                user_email=user["email"],
                order_id=order_id,
                target_url=request.target_url,
                keyword=request.keyword,
                service_type="PBN 백링크",
                quantity=1,
                price=0.0,
            )

            logger.info(f"이메일 태스크 등록 완료: {email_task_result.id}")

        except Exception as e:
            logger.warning(f"이메일 태스크 등록 실패: {e}")

        # 5. PBN 백링크 생성 태스크 등록
        logger.info("PBN 태스크 등록 시도")

        try:
            from app.tasks.pbn_rest_tasks import create_pbn_backlink_rest

            pbn_task_result = create_pbn_backlink_rest.delay(
                order_id=order_id,
                target_url=request.target_url,
                keyword=request.keyword,
                pbn_site_domain=random_pbn.get("domain"),
            )

            logger.info(f"PBN 태스크 등록 완료: {pbn_task_result.id}")

        except Exception as e:
            logger.error(f"PBN 태스크 등록 실패: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to queue PBN task: {str(e)}"
            )

        return {
            "success": True,
            "message": "PBN backlink request submitted successfully",
            "order_id": order_id,
            "target_url": request.target_url,
            "keyword": request.keyword,
            "estimated_completion": "5-10 minutes",
            "email_task_id": getattr(email_task_result, "id", None),
            "pbn_task_id": getattr(pbn_task_result, "id", None),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예외 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 별칭 엔드포인트 (기존 호환성을 위해)
@router.post("/pbn/sample-request")
async def sample_request_alias(request: PbnSampleRequest):
    """기존 sample-request 엔드포인트 별칭"""
    logger.info("sample-request 별칭을 통한 요청")

    try:
        result = await rest_test_request(request)
        logger.info("rest_test_request 호출 완료")
        return result
    except Exception as e:
        logger.error(f"별칭 엔드포인트에서 예외 발생: {e}")
        raise
