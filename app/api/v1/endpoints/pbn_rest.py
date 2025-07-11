"""
PBN 백링크 구축 API (Supabase REST API 버전)
UTF-8 인코딩 문제 해결을 위해 PostgreSQL 직접 연결 대신 REST API 사용
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


@router.post("/pbn/rest-test")
async def rest_test_request(request: PbnSampleRequest):
    """
    REST API 버전 PBN 백링크 구축 요청 (인증 선택적)
    - PostgreSQL 직접 연결 없이 Supabase REST API만 사용
    - UTF-8 인코딩 문제 우회
    - 로그인된 사용자 이메일로 발송 (인증이 없으면 기본 이메일 사용)
    """
    try:
        logger.info(f"PBN REST test request: {request.target_url} - {request.keyword}")

        # 1. PBN 사이트 조회 (활성 사이트만)
        random_pbn = supabase_client.get_random_active_pbn_site()
        if not random_pbn:
            raise HTTPException(status_code=500, detail="활성 PBN 사이트가 없습니다")

        logger.info(f"Selected PBN site: {random_pbn['domain']}")

        # 2. 사용자 정보 설정 (기본 이메일 사용) 🔧
        user_email = "vnfm0580@gmail.com"  # 🔧 기본 이메일 사용
        clerk_id = f"manual_user_{int(datetime.utcnow().timestamp())}"  # 고유 ID 생성

        # Supabase에서 이메일로 기존 사용자 찾기
        existing_users = supabase_client._make_request(
            "GET", "users", params={"email": f"eq.{user_email}"}, use_service_role=True
        )

        if existing_users and len(existing_users) > 0:
            user = existing_users[0]
            logger.info(f"✅ Using existing user: {user['id']} ({user['email']})")
        else:
            # 새 사용자 생성
            user_data = {
                "email": user_email,
                "clerk_id": clerk_id,
                "role": "user",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            user = supabase_client.create_user(user_data)
            logger.info(f"✅ Created new user: {user['id']} ({user['email']})")

        # 3. 주문 생성
        order_id = str(uuid.uuid4())
        selected_pbn = random_pbn

        order_data = {
            "id": order_id,
            "user_id": user["id"],
            "type": "free_pbn",
            "status": "pending",
            "amount": 0.00,
            "payment_status": "paid",
            "order_metadata": {
                "target_url": request.target_url,
                "keyword": request.keyword,
                "request_type": "manual_test",  # 🔧 수동 테스트
                "pbn_count": 1,
                "selected_pbn_site": selected_pbn["domain"],
                "method": "supabase_rest_api",
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        order = supabase_client.create_order(order_data)
        if not order:
            raise HTTPException(status_code=500, detail="주문 생성 실패")

        logger.info(f"REST order created: {order['id']} for user {user['email']}")

        # 4. 주문 확인 이메일 발송 (Redis 연결 처리)
        email_task_status = "scheduled"
        pbn_task_status = "scheduled"

        # 이메일 발송 태스크 등록
        try:
            from app.tasks.email_tasks import send_order_confirmation_email

            send_order_confirmation_email.apply_async(
                args=[
                    user["email"],  # vnfm0580@gmail.com으로 발송
                    order["id"],
                    {
                        "target_url": request.target_url,
                        "keyword": request.keyword,
                        "pbn_domain": selected_pbn["domain"],
                    },
                ],
                queue="default",
            )
            logger.info("✅ 이메일 태스크가 Redis 큐에 등록되었습니다")
        except Exception as e:
            logger.warning(f"⚠️ 이메일 태스크 등록 실패 (Redis 연결 문제): {str(e)}")
            email_task_status = "failed_redis_connection"

        # PBN 백링크 구축 태스크 등록
        try:
            from app.tasks.pbn_rest_tasks import create_pbn_backlink_rest

            create_pbn_backlink_rest.apply_async(
                args=[
                    order["id"],
                    request.target_url,
                    request.keyword,
                    selected_pbn["domain"],
                ],
                queue="default",
            )
            logger.info("✅ PBN 백링크 태스크가 Redis 큐에 등록되었습니다")
        except Exception as e:
            logger.warning(f"⚠️ PBN 태스크 등록 실패 (Redis 연결 문제): {str(e)}")
            pbn_task_status = "failed_redis_connection"

        # Redis 연결 상태에 따른 메시지 설정
        if (
            email_task_status == "failed_redis_connection"
            or pbn_task_status == "failed_redis_connection"
        ):
            message = "PBN 백링크 구축 요청이 접수되었습니다 (Redis 서비스 연결 필요)"
            note = "⚠️ Redis 서비스 연결 후 백그라운드 처리가 시작됩니다"
            method = "supabase_rest_api_redis_pending"
        else:
            message = "PBN 백링크 구축이 시작되었습니다! 이메일을 확인해주세요"
            note = "✅ Redis 서비스 연결 완료, 백그라운드 처리 중 (이메일 발송됨)"
            method = "supabase_rest_api_with_redis"

        return {
            "success": True,
            "message": message,
            "order_id": order["id"],
            "task_id": f"rest-task-{order['id']}",
            "estimated_completion": "5-10분 이내",
            "user_email": user["email"],  # 🔧 vnfm0580@gmail.com
            "note": note,
            "status": "pending",
            "selected_pbn_site": selected_pbn["domain"],
            "total_pbn_sites": 1,
            "method": method,
            "redis_status": {
                "email_task": email_task_status,
                "pbn_task": pbn_task_status,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PBN REST test request failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"REST 요청 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/pbn/rest-orders/{order_id}/status")
async def rest_order_status(order_id: str):
    """주문 진행 상태 조회"""
    try:
        order = supabase_client.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")
        return {
            "id": order["id"],
            "status": order["status"],
            "order_metadata": order.get("order_metadata", {}),
        }
    except Exception as e:
        logger.error(f"status check error: {e}")
        raise HTTPException(status_code=500, detail="상태 조회 실패")


@router.post("/pbn/sample-request", tags=["pbn"])
async def sample_request_alias(request: PbnSampleRequest):
    """/pbn/sample-request 경로 호환용 (rest_test_request 재사용)"""
    return await rest_test_request(request)
