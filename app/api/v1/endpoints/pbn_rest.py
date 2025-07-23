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
    url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    # 환경변수 검증
    logger.info(f"[Supabase] URL: {url}")
    logger.info(f"[Supabase] ANON_KEY 설정됨: {bool(anon_key)}")
    logger.info(f"[Supabase] SERVICE_ROLE_KEY 설정됨: {bool(service_role_key)}")

    if not all([url, anon_key, service_role_key]):
        missing = []
        if not url:
            missing.append("SUPABASE_URL")
        if not anon_key:
            missing.append("SUPABASE_ANON_KEY")
        if not service_role_key:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        logger.error(f"[Supabase] 누락된 환경변수: {', '.join(missing)}")

    return {
        "url": url,
        "anon_key": anon_key,
        "service_role_key": service_role_key,
    }


def create_user_via_rest(user_data):
    """REST API를 통한 사용자 생성"""
    supabase = get_supabase_client()

    headers = {
        "apikey": supabase["service_role_key"],
        "Authorization": f"Bearer {supabase['service_role_key']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",  # 🔧 생성된 데이터 반환 요청
    }

    url = f"{supabase['url']}/rest/v1/users"

    try:
        response = requests.post(url, json=user_data, headers=headers)
        logger.info(
            f"Supabase 응답: status={response.status_code}, content_length={len(response.content)}"
        )

        if response.status_code in [200, 201]:
            if not response.content:
                logger.warning("빈 응답 받음 - 사용자 생성 실패")
                return None

            try:
                json_data = response.json()
                logger.info(f"사용자 생성 성공: {json_data}")
                return (
                    json_data[0]
                    if isinstance(json_data, list) and json_data
                    else json_data
                )
            except ValueError as e:
                logger.error(f"JSON 파싱 에러: {e}, 응답 내용: {response.text[:200]}")
                return None
        else:
            logger.error(f"사용자 생성 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"사용자 생성 요청 중 에러: {e}")
        return None


def create_order_via_rest(order_data):
    """REST API를 통한 주문 생성"""
    supabase = get_supabase_client()

    headers = {
        "apikey": supabase["service_role_key"],
        "Authorization": f"Bearer {supabase['service_role_key']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",  # 🔧 생성된 데이터 반환 요청
    }

    url = f"{supabase['url']}/rest/v1/orders"

    try:
        response = requests.post(url, json=order_data, headers=headers)
        logger.info(
            f"주문 생성 응답: status={response.status_code}, content_length={len(response.content)}"
        )

        if response.status_code in [200, 201]:
            if not response.content:
                logger.warning("빈 응답 받음 - 주문 생성 실패")
                return None

            try:
                json_data = response.json()
                logger.info(f"주문 생성 성공: {json_data}")
                return (
                    json_data[0]
                    if isinstance(json_data, list) and json_data
                    else json_data
                )
            except ValueError as e:
                logger.error(f"JSON 파싱 에러: {e}, 응답 내용: {response.text[:200]}")
                return None
        else:
            logger.error(f"주문 생성 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"주문 생성 요청 중 에러: {e}")
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

    try:
        response = requests.get(url, headers=headers)
        logger.info(
            f"사용자 조회 응답: status={response.status_code}, content_length={len(response.content)}"
        )

        if response.status_code == 200:
            if not response.content:
                logger.info("사용자 조회 결과: 빈 응답 (사용자 없음)")
                return None

            try:
                users = response.json()
                logger.info(
                    f"사용자 조회 결과: {len(users) if isinstance(users, list) else 1}명"
                )
                return users[0] if users else None
            except ValueError as e:
                logger.error(f"JSON 파싱 에러: {e}, 응답 내용: {response.text[:200]}")
                return None
        else:
            logger.error(f"사용자 조회 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"사용자 조회 요청 중 에러: {e}")
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

    try:
        response = requests.get(url, headers=headers)
        logger.info(
            f"PBN 사이트 조회 응답: status={response.status_code}, content_length={len(response.content)}"
        )

        if response.status_code == 200:
            if not response.content:
                logger.info("PBN 사이트 조회 결과: 빈 응답")
                return []

            try:
                pbn_sites = response.json()
                logger.info(f"PBN 사이트 조회 결과: {len(pbn_sites)}개")
                return pbn_sites if isinstance(pbn_sites, list) else []
            except ValueError as e:
                logger.error(f"JSON 파싱 에러: {e}, 응답 내용: {response.text[:200]}")
                return []
        else:
            logger.error(
                f"PBN 사이트 조회 실패: {response.status_code} - {response.text}"
            )
            return []
    except Exception as e:
        logger.error(f"PBN 사이트 조회 요청 중 에러: {e}")
        return []


@router.post("/pbn/rest-test-request")
async def rest_test_request(request: PbnSampleRequest):
    """REST API 기반 PBN 백링크 요청 처리"""
    logger.info(
        f"PBN 백링크 요청 시작: target_url={request.target_url}, keyword={request.keyword}"
    )

    try:
        # 1. PBN 사이트 활성 상태 확인 및 랜덤 선택
        random_pbn = supabase_client.get_random_active_pbn_site()
        logger.debug(
            f"랜덤 PBN 사이트 선택: {random_pbn.get('domain') if random_pbn else 'None'}"
        )

        if not random_pbn:
            logger.warning("활성 PBN 사이트 없음")
            raise HTTPException(status_code=503, detail="No active PBN sites available")

        # 2. 테스트 사용자 조회 또는 생성
        test_clerk_id = "test_user_123"
        user = get_user_via_rest(test_clerk_id)

        if user:
            logger.debug(f"기존 사용자 사용: {user.get('id')}")
        else:
            # 새 사용자 생성 (실제 이메일 사용)
            user_data = {
                "clerk_id": test_clerk_id,
                "email": "vnfm0580@gmail.com",  # 실제 사용자 이메일
                "created_at": datetime.now().isoformat(),
            }
            user = create_user_via_rest(user_data)
            logger.info(f"새 사용자 생성: {user.get('id') if user else 'Failed'}")

        if not user:
            raise HTTPException(status_code=500, detail="Failed to create/get user")

        # 3. 주문 생성 (테이블 스키마에 맞게 수정)
        order_data = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "type": "free_pbn",  # orders 테이블의 실제 컬럼
            "status": "pending",
            "amount": 0.0,
            "payment_status": "paid",  # 무료이므로 바로 paid
            "order_metadata": {
                "target_url": request.target_url,
                "keyword": request.keyword,
                "service_type": "pbn_backlink",
                "quantity": 1,
                "request_type": "sample",
                "pbn_count": 1,
            },
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
        email_task_result = None  # 변수 초기화

        try:
            from app.tasks.email_tasks import send_order_confirmation_email

            # 함수 시그니처에 맞게 order_details 딕셔너리로 전달
            order_details = {
                "target_url": request.target_url,
                "keyword": request.keyword,
                "service_type": "PBN 백링크",
                "quantity": 1,
                "price": 0.0,
                "type": "free_pbn",
                "status": "pending",
            }

            email_task_result = send_order_confirmation_email.delay(
                user_email=user["email"],
                order_id=order_id,
                order_details=order_details,
            )

            logger.info(f"이메일 태스크 등록 완료: {email_task_result.id}")

        except Exception as e:
            logger.warning(f"이메일 태스크 등록 실패: {e}")

        # 5. PBN 백링크 생성 태스크 등록
        logger.info("PBN 태스크 등록 시도")
        pbn_task_result = None  # 변수 초기화

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


# 인증 기반 실제 엔드포인트
@router.post("/pbn/sample-request")
async def sample_request_authenticated(
    request: PbnSampleRequest, current_user: dict = Depends(get_current_clerk_user)
):
    """실제 로그인 사용자 기반 PBN 백링크 요청"""
    logger.info(f"인증 사용자 PBN 요청: {current_user.get('sub', 'unknown')}")

    try:
        # 1. PBN 사이트 활성 상태 확인 및 랜덤 선택 (테스트용)
        random_pbn = supabase_client.get_random_active_pbn_site()
        logger.debug(
            f"테스트용 랜덤 PBN 사이트 선택: {random_pbn.get('domain') if random_pbn else 'None'}"
        )

        if not random_pbn:
            logger.warning("활성 PBN 사이트 없음")
            raise HTTPException(status_code=503, detail="No active PBN sites available")

        # 2. 현재 로그인 사용자 정보 추출 (verify.py 방식 적용)
        clerk_id = current_user.get("sub")
        user_email = current_user.get("email")

        if not clerk_id:
            logger.error("Clerk ID missing from token")
            raise HTTPException(status_code=400, detail="Clerk ID가 토큰에 없습니다")

        # 이메일 정보 확보 (토큰에 없으면 Clerk API로 조회)
        if not user_email:
            try:
                from app.core.clerk_api import get_clerk_user_email

                user_email = get_clerk_user_email(clerk_id)
                logger.info(f"Clerk API에서 이메일 조회 성공: {user_email}")
            except Exception as e:
                logger.error(f"Failed to get email from Clerk API: {e}")
                raise HTTPException(
                    status_code=400, detail="이메일 정보를 가져올 수 없습니다"
                )

        if not user_email:
            logger.error(f"No email found for clerk_id: {clerk_id}")
            raise HTTPException(status_code=400, detail="이메일이 필요합니다")

        logger.info(f"실제 사용자: {user_email} (clerk_id: {clerk_id})")

        # 3. 사용자 조회 또는 생성
        user = get_user_via_rest(clerk_id)

        if user:
            logger.debug(f"기존 사용자 사용: {user.get('id')}")
        else:
            # 새 사용자 생성 (실제 로그인 사용자 정보)
            user_data = {
                "clerk_id": clerk_id,
                "email": user_email,
                "created_at": datetime.now().isoformat(),
            }
            user = create_user_via_rest(user_data)
            logger.info(f"새 사용자 생성: {user.get('id') if user else 'Failed'}")

        if not user:
            raise HTTPException(status_code=500, detail="Failed to create/get user")

        # 4. 주문 생성
        order_data = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "type": "free_pbn",
            "status": "pending",
            "amount": 0.0,
            "payment_status": "paid",
            "order_metadata": {
                "target_url": request.target_url,
                "keyword": request.keyword,
                "service_type": "pbn_backlink",
                "quantity": 1,
                "request_type": "authenticated",
                "pbn_count": 1,
            },
            "created_at": datetime.now().isoformat(),
        }

        order = create_order_via_rest(order_data)
        logger.info(f"주문 생성 결과: {order.get('id') if order else 'Failed'}")

        if not order:
            logger.error("주문 생성 실패")
            raise HTTPException(status_code=500, detail="Failed to create order")

        order_id = order["id"]

        # 5. 이메일 확인 태스크 등록
        logger.info("이메일 태스크 등록 시도")
        email_task_result = None

        try:
            from app.tasks.email_tasks import send_order_confirmation_email

            order_details = {
                "target_url": request.target_url,
                "keyword": request.keyword,
                "service_type": "PBN 백링크",
                "quantity": 1,
                "price": 0.0,
                "type": "free_pbn",
                "status": "pending",
            }

            email_task_result = send_order_confirmation_email.delay(
                user_email=user_email,  # 실제 사용자 이메일
                order_id=order_id,
                order_details=order_details,
            )

            logger.info(f"이메일 태스크 등록 완료: {email_task_result.id}")

        except Exception as e:
            logger.warning(f"이메일 태스크 등록 실패: {e}")

        # 6. PBN 백링크 생성 태스크 등록
        logger.info("PBN 태스크 등록 시도")
        pbn_task_result = None

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
            "user_email": user_email,
            "estimated_completion": "5-10 minutes",
            "email_task_id": getattr(email_task_result, "id", None),
            "pbn_task_id": getattr(pbn_task_result, "id", None),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증 엔드포인트에서 예외 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# 테스트용 별칭 엔드포인트 (개발 전용)
@router.post("/pbn/test-request")
async def test_request_alias(request: PbnSampleRequest):
    """개발/테스트용 엔드포인트 (인증 없음)"""
    logger.info("test-request 개발용 엔드포인트 호출")

    try:
        result = await rest_test_request(request)
        logger.info("rest_test_request 호출 완료")
        return result
    except Exception as e:
        logger.error(f"테스트 엔드포인트에서 예외 발생: {e}")
        raise
