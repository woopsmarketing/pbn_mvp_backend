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
        print("[rest_test_request] 1. 요청 시작", flush=True)
        logger.info("[rest_test_request] 1. 요청 시작")
        print(f"[rest_test_request] 2. 입력값: {request}", flush=True)
        logger.info(f"[rest_test_request] 2. 입력값: {request}")
        # 1. PBN 사이트 조회 (활성 사이트만)
        random_pbn = supabase_client.get_random_active_pbn_site()
        print(f"[rest_test_request] 3. 랜덤 PBN 조회 결과: {random_pbn}", flush=True)
        logger.info(f"[rest_test_request] 3. 랜덤 PBN 조회 결과: {random_pbn}")
        if not random_pbn:
            print("[rest_test_request] 4. 활성 PBN 사이트 없음", flush=True)
            logger.error("[rest_test_request] 4. 활성 PBN 사이트 없음")
            raise HTTPException(status_code=500, detail="활성 PBN 사이트가 없습니다")
        # 2. 사용자 정보 설정 (기본 이메일 사용)
        user_email = "vnfm0580@gmail.com"
        clerk_id = f"manual_user_{int(datetime.utcnow().timestamp())}"
        existing_users = supabase_client._make_request(
            "GET", "users", params={"email": f"eq.{user_email}"}, use_service_role=True
        )
        print(
            f"[rest_test_request] 5. 기존 사용자 조회 결과: {existing_users}",
            flush=True,
        )
        logger.info(f"[rest_test_request] 5. 기존 사용자 조회 결과: {existing_users}")
        if existing_users and len(existing_users) > 0:
            user = existing_users[0]
            print(f"[rest_test_request] 6. 기존 사용자 사용: {user}", flush=True)
            logger.info(f"[rest_test_request] 6. 기존 사용자 사용: {user}")
        else:
            user_data = {
                "email": user_email,
                "clerk_id": clerk_id,
                "role": "user",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            user = supabase_client.create_user(user_data)
            print(f"[rest_test_request] 7. 새 사용자 생성: {user}", flush=True)
            logger.info(f"[rest_test_request] 7. 새 사용자 생성: {user}")
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
                "request_type": "manual_test",
                "pbn_count": 1,
                "selected_pbn_site": selected_pbn["domain"],
                "method": "supabase_rest_api",
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        order = supabase_client.create_order(order_data)
        print(f"[rest_test_request] 8. 주문 생성 결과: {order}", flush=True)
        logger.info(f"[rest_test_request] 8. 주문 생성 결과: {order}")
        if not order:
            print("[rest_test_request] 9. 주문 생성 실패", flush=True)
            logger.error("[rest_test_request] 9. 주문 생성 실패")
            raise HTTPException(status_code=500, detail="주문 생성 실패")
        # 4. 이메일 발송 Celery Task 등록
        email_task_status = "scheduled"
        pbn_task_status = "scheduled"
        try:
            from app.tasks.email_tasks import send_order_confirmation_email

            print("[rest_test_request] 10. 이메일 태스크 등록 시도", flush=True)
            logger.info("[rest_test_request] 10. 이메일 태스크 등록 시도")
            print(f"[rest_test_request] 10-1. 큐 이름: default", flush=True)
            logger.info(f"[rest_test_request] 10-1. 큐 이름: default")
            import os

            print(
                f"[rest_test_request] 10-2. 브로커 주소: {os.getenv('CELERY_BROKER_URL')}",
                flush=True,
            )
            logger.info(
                f"[rest_test_request] 10-2. 브로커 주소: {os.getenv('CELERY_BROKER_URL')}"
            )
            # queue 파라미터를 빼고 기본값(celery)로도 테스트할 수 있도록 주석 처리
            # send_order_confirmation_email.apply_async(
            #     args=[
            #         user["email"],
            #         order["id"],
            #         {
            #             "target_url": request.target_url,
            #             "keyword": request.keyword,
            #             "pbn_domain": selected_pbn["domain"],
            #         },
            #     ],
            #     # queue="default",
            # )
            # 기본값 celery로 큐 등록 테스트
            send_order_confirmation_email.apply_async(
                args=[
                    user["email"],
                    order["id"],
                    {
                        "target_url": request.target_url,
                        "keyword": request.keyword,
                        "pbn_domain": selected_pbn["domain"],
                    },
                ],
                queue="default",
            )
            print("[rest_test_request] 11. 이메일 태스크 큐 등록 완료", flush=True)
            logger.info("[rest_test_request] 11. 이메일 태스크 큐 등록 완료")
        except Exception as e:
            print(f"[rest_test_request] 12. 이메일 태스크 등록 실패: {e}", flush=True)
            logger.warning(f"[rest_test_request] 12. 이메일 태스크 등록 실패: {e}")
            import os

            print(f"[rest_test_request] 12-1. 큐 이름: default", flush=True)
            print(
                f"[rest_test_request] 12-2. 브로커 주소: {os.getenv('CELERY_BROKER_URL')}",
                flush=True,
            )
            print(
                f"[rest_test_request] 12-3. 환경변수 CELERY_RESULT_BACKEND: {os.getenv('CELERY_RESULT_BACKEND')}",
                flush=True,
            )
            email_task_status = "failed_redis_connection"
        # 5. PBN 백링크 구축 Celery Task 등록
        try:
            from app.tasks.pbn_rest_tasks import create_pbn_backlink_rest

            print("[rest_test_request] 13. PBN 태스크 등록 시도", flush=True)
            logger.info("[rest_test_request] 13. PBN 태스크 등록 시도")
            create_pbn_backlink_rest.apply_async(
                args=[
                    order["id"],
                    request.target_url,
                    request.keyword,
                    selected_pbn["domain"],
                ],
                queue="default",
            )
            print("[rest_test_request] 14. PBN 태스크 큐 등록 완료", flush=True)
            logger.info("[rest_test_request] 14. PBN 태스크 큐 등록 완료")
        except Exception as e:
            print(f"[rest_test_request] 15. PBN 태스크 등록 실패: {e}", flush=True)
            logger.warning(f"[rest_test_request] 15. PBN 태스크 등록 실패: {e}")
            pbn_task_status = "failed_redis_connection"
        # 6. 결과 메시지
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
        print(
            f"[rest_test_request] 16. 최종 반환: {message}, {note}, {method}",
            flush=True,
        )
        logger.info(f"[rest_test_request] 16. 최종 반환: {message}, {note}, {method}")
        return {
            "success": True,
            "message": message,
            "order_id": order["id"],
            "note": note,
            "method": method,
        }
    except Exception as e:
        print(f"[rest_test_request] 17. 예외 발생: {e}", flush=True)
        logger.error(f"[rest_test_request] 17. 예외 발생: {e}")
        raise


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
    """
    /pbn/sample-request 경로 호환용 (rest_test_request 재사용)
    """
    try:
        print("[sample_request_alias] 1. 요청 시작", flush=True)
        logger.info("[sample_request_alias] 1. 요청 시작")
        print(f"[sample_request_alias] 2. 입력값: {request}", flush=True)
        logger.info(f"[sample_request_alias] 2. 입력값: {request}")
        # 실제 rest_test_request 호출 전후로도 print/log 추가
        result = await rest_test_request(request)
        print("[sample_request_alias] 3. rest_test_request 호출 완료", flush=True)
        logger.info("[sample_request_alias] 3. rest_test_request 호출 완료")
        print(f"[sample_request_alias] 4. 반환값: {result}", flush=True)
        logger.info(f"[sample_request_alias] 4. 반환값: {result}")
        return result
    except Exception as e:
        print(f"[sample_request_alias] 5. 예외 발생: {e}", flush=True)
        logger.error(f"[sample_request_alias] 5. 예외 발생: {e}")
        raise
