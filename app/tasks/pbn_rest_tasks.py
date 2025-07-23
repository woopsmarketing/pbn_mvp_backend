"""
REST-only PBN 백링크 Celery 태스크 (Supabase API + LangChain 콘텐츠 생성)
- LangChain 기반 제목/콘텐츠/이미지 자동 생성
- 자연스러운 앵커텍스트 삽입
- 워드프레스 자동 업로드
- v1.2 - debug_print 제거 및 로그 최적화 (2025.07.15)
"""

import logging
import random
import time
from datetime import datetime
from typing import List

from app.tasks.celery_app import celery as app
from app.services.supabase_client import supabase_client
from app.services.pbn_poster import build_html_content
from app.services.pbn_content_service import get_pbn_content_service

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def create_pbn_backlink_rest(
    self,
    order_id: str,
    target_url: str,
    keyword: str,
    pbn_site_domain: str | None = None,
):
    """무료 PBN 1개 생성 – LangChain 콘텐츠 생성 통합 버전"""
    logger.info(
        f"PBN 백링크 생성 태스크 시작: order_id={order_id}, target_url={target_url}, keyword={keyword}"
    )

    try:
        logger.info(f"주문 상태를 processing으로 업데이트 중... (order_id: {order_id})")

        # 1) 주문을 processing 상태로 업데이트
        supabase_client.update_order_status(order_id, "processing")
        logger.info("주문 상태 업데이트 완료")

        # 2) 실제 PBN 포스팅으로 바로 진행 (시뮬레이션 제거)
        logger.info("실제 PBN 포스팅 프로세스 시작...")

        # 3) PBN 사이트 선택 및 포스팅 시도 (최대 5개 사이트까지 시도)
        max_pbn_attempts = 5  # 서버 문제가 많으므로 시도 횟수 증가
        backlink_url = None
        used_sites = []
        server_error_codes = [503, 504, 508, 502, 500]  # 서버 오류 코드들

        for attempt in range(max_pbn_attempts):
            # PBN 사이트 선택 (이전에 시도했던 사이트는 제외)
            if attempt == 0 and pbn_site_domain:
                site = pbn_site_domain  # 첫 번째 시도는 지정된 사이트 사용
            else:
                # 랜덤 PBN 사이트 선택 (이전에 실패한 사이트 제외)
                site = supabase_client.get_random_pbn_site_excluding(used_sites)
                if not site:
                    logger.warning("사용 가능한 PBN 사이트가 없습니다")
                    break

            # 도메인 정리 (https://, http://, 끝 / 제거)
            clean_domain = (
                site.replace("https://", "").replace("http://", "").rstrip("/")
            )
            used_sites.append(clean_domain)
            logger.info(
                f"PBN 사이트 시도 {attempt + 1}/{max_pbn_attempts}: {clean_domain}"
            )

            # Supabase DB에서 해당 도메인의 PBN 자격정보 조회
            site_record = supabase_client.get_pbn_site_by_domain(clean_domain)
            logger.debug(f"PBN 사이트 레코드: {site_record}")

            # 사이트 정보가 없으면 다음 사이트로
            if not site_record:
                logger.warning(
                    f"PBN 사이트 정보 없음: {clean_domain}, 다음 사이트 시도"
                )
                continue

            # PBN 사이트 정보가 있으면 포스팅 시도
            site = clean_domain  # 이후 로직에서 사용할 변수명 통일

            # 사용자명 추출 - Supabase DB 컬럼명에 맞춤
            wp_user = (
                site_record.get("wp_admin_id")  # 실제 DB 컬럼명
                or site_record.get("wp_admin_user")
                or site_record.get("username")
            )

            # Application Password 추출 (REST API용) - Supabase DB 컬럼명에 맞춤
            wp_app_password = (
                site_record.get("wp_app_key")  # 실제 DB 컬럼명
                or site_record.get("wp_app_password")
                or site_record.get("application_password")
                or site_record.get("app_password")
                or site_record.get("wp_admin_pw")  # 백업으로 관리자 비밀번호 사용
                or site_record.get("wp_admin_password")
                or site_record.get("password")
            )

            # XML-RPC Password (이미지 업로드용)
            wp_xmlrpc_password = (
                site_record.get("wp_admin_pw")
                or site_record.get("wp_admin_password")
                or site_record.get("password")
                or wp_app_password  # 백업으로 app_password 사용
            )

            logger.info(f"PBN 사이트 자격정보 확인:")
            logger.info(f"  - 사용자명: {wp_user}")
            logger.info(f"  - App Password 존재: {'Yes' if wp_app_password else 'No'}")
            logger.info(
                f"  - XMLRPC Password 존재: {'Yes' if wp_xmlrpc_password else 'No'}"
            )
            logger.info(f"  - 사이트 레코드 키들: {list(site_record.keys())}")

            if wp_user and wp_app_password:
                logger.info(f"실제 워드프레스 사이트에 포스팅 시도: {site}")

                try:
                    # PBN 콘텐츠 서비스 가져오기
                    content_service = get_pbn_content_service()

                    # LangChain을 통한 완전한 콘텐츠 생성
                    logger.info("LangChain 콘텐츠 생성 서비스 시작...")
                    content_result = content_service.generate_complete_content(
                        keyword=keyword, target_url=target_url
                    )

                    if content_result["success"]:
                        logger.info(f"LangChain 콘텐츠 생성 성공")
                        title = content_result["title"]
                        html_content = content_result["html_content"]
                        featured_image_path = content_result.get("featured_image_path")

                    else:
                        logger.warning(
                            f"LangChain 콘텐츠 생성 실패, 폴백 방식 사용: {content_result.get('error', '알 수 없는 오류')}"
                        )
                        # 폴백: 기존 방식으로 글 작성
                        title = (
                            f"Test BackLink for SEO 백링크 {random.randint(1, 1000)}"
                        )
                        logger.info(f"폴백 글 제목: {title}")

                        content = f"""
<h2>{keyword}에 대한 유용한 정보</h2>
<p>이 글에서는 <a href="{target_url}">{keyword}</a>에 대해 자세히 알아보겠습니다.</p>
<p>{keyword}는 많은 사람들이 관심을 가지는 주제입니다.</p>
<p>더 자세한 정보는 링크를 참고해 주세요.</p>
"""
                        html_content = build_html_content(
                            title, content, target_url, keyword
                        )
                        featured_image_path = None

                    # 워드프레스에 포스팅 (WordPressUploader 사용)
                    logger.info(f"워드프레스 포스팅 시작: {site}")
                    from app.utils.wordpress_uploader import WordPressUploader

                    # URL 형식 정리 (https:// 접두사와 끝 / 제거)
                    clean_site_url = (
                        site.replace("https://", "").replace("http://", "").rstrip("/")
                    )
                    full_site_url = f"https://{clean_site_url}"

                    logger.info(f"정리된 사이트 URL: {full_site_url}")

                    # 사이트 헬스체크 (간단한 접근성 확인)
                    try:
                        import requests

                        health_response = requests.get(full_site_url, timeout=10)
                        if health_response.status_code in server_error_codes:
                            logger.warning(
                                f"사이트 헬스체크 실패: {full_site_url} - HTTP {health_response.status_code}"
                            )
                            logger.info("다음 PBN 사이트로 시도합니다...")
                            continue
                        logger.info(f"사이트 헬스체크 통과: {full_site_url}")
                    except Exception as e:
                        logger.warning(f"사이트 헬스체크 오류: {full_site_url} - {e}")
                        logger.info("다음 PBN 사이트로 시도합니다...")
                        continue

                    uploader = WordPressUploader(
                        site_url=full_site_url,
                        username=wp_user,
                        password=wp_xmlrpc_password,  # XML-RPC용 (이미지 업로드)
                        app_password=wp_app_password,  # REST API용 (포스트 생성)
                    )

                    post_result = uploader.upload_complete_post(
                        title=title,
                        content=html_content,
                        image_path=featured_image_path,
                        keyword=keyword,
                        status="publish",
                    )

                    if post_result["success"] and post_result.get("post_created"):
                        backlink_url = post_result.get("post_url")
                        logger.info(f"워드프레스 포스팅 성공: {backlink_url}")
                        break  # 성공하면 루프 종료
                    else:
                        logger.error(
                            f"워드프레스 포스팅 실패: {post_result.get('error', '알 수 없는 오류')}"
                        )
                        logger.info("다음 PBN 사이트로 시도합니다...")

                except Exception as e:
                    logger.error(f"실제 포스팅 중 오류 발생: {e}")
                    logger.info("다음 PBN 사이트로 시도합니다...")
            else:
                logger.warning(f"PBN 사이트 자격정보 부족: {site}")
                logger.warning(f"  - wp_user: {wp_user}")
                logger.warning(
                    f"  - wp_app_password: {'[설정됨]' if wp_app_password else '[없음]'}"
                )
                logger.warning("다음 사이트로 시도합니다...")

        # 모든 PBN 사이트 시도 완료
        if not backlink_url:
            logger.error("모든 PBN 사이트에서 포스팅 실패")
            supabase_client.update_order_status(order_id, "failed")
            return {
                "success": False,
                "order_id": order_id,
                "message": "모든 PBN 사이트에서 포스팅 실패",
                "attempted_sites": used_sites,
            }

        # 4) 주문 메타데이터 업데이트
        logger.info("주문 메타데이터 업데이트 중...")

        metadata = {
            "completed_at": datetime.now().isoformat(),
            "pbn_site": site,
            "target_url": target_url,
            "keyword": keyword,
        }

        if backlink_url:
            metadata["backlink_url"] = backlink_url

        supabase_client.update_order_metadata(order_id, metadata)
        logger.info("주문 메타데이터 업데이트 완료")

        # 5) 주문 상태를 completed로 업데이트
        supabase_client.update_order_status(order_id, "completed")

        # 6) 완료 이메일 발송 (별도 태스크로 실행)
        logger.info("백링크 완료 이메일 발송 준비 중...")
        from app.tasks.email_tasks import send_backlink_completion_email

        # 주문 정보 조회
        order_info = supabase_client.get_order(order_id)
        logger.debug(f"주문 정보 조회 결과: {order_info}")

        if order_info and order_info.get("user_id"):
            user_info = supabase_client.get_user(order_info["user_id"])
            if user_info and user_info.get("email"):
                logger.info(f"이메일 발송 대기열에 추가: {user_info['email']}")

                # 백링크 결과 딕셔너리 준비
                backlink_result = {
                    "target_url": target_url,
                    "keyword": keyword,
                    "pbn_urls": (
                        [backlink_url]
                        if backlink_url
                        else [f"https://{site}/completed"]
                    ),
                    "total_backlinks": 1,
                    "pbn_domain": site,
                    "backlink_url": backlink_url or f"https://{site}/completed",
                }

                send_backlink_completion_email.delay(
                    user_email=user_info["email"],
                    order_id=order_id,
                    backlink_result=backlink_result,
                )

        logger.info(f"PBN 백링크 태스크 완료: order_id={order_id}")

        return {
            "success": True,
            "order_id": order_id,
            "target_url": target_url,
            "keyword": keyword,
            "pbn_site": site,
            "backlink_url": backlink_url,
            "message": "PBN backlink created successfully",
        }

    except Exception as e:
        logger.error(f"PBN 태스크 오류: {e}", exc_info=True)
        supabase_client.update_order_status(order_id, "failed")
        raise self.retry(exc=e)


# 시뮬레이션 함수 제거됨 - 실제 포스팅으로 바로 진행


@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2})
def create_multiple_backlinks_rest(
    self, order_id: str, target_url: str, keyword: str, quantity: int = 5
):
    """다중 PBN 백링크 생성 태스크"""
    logger.info(f"다중 백링크 생성 시작: {quantity}개 (order_id: {order_id})")

    try:
        # PBN 사이트 목록 조회
        pbn_sites = supabase_client.get_active_pbn_sites(limit=quantity)
        logger.info(f"사용 가능한 PBN 사이트 {len(pbn_sites)}개 조회")

        if not pbn_sites:
            logger.error("사용 가능한 PBN 사이트가 없습니다")
            supabase_client.update_order_status(order_id, "failed")
            return {
                "success": False,
                "message": "No available PBN sites",
                "order_id": order_id,
            }

        created_backlinks = []
        failed_sites = []

        # 각 사이트에 백링크 생성
        for i, site in enumerate(pbn_sites[:quantity], 1):
            try:
                logger.info(f"백링크 {i}/{quantity} 생성 중: {site.get('domain')}")

                # 개별 백링크 생성 태스크 호출
                result = create_pbn_backlink_rest.apply(
                    args=[
                        f"{order_id}_sub_{i}",
                        target_url,
                        keyword,
                        site.get("domain"),
                    ]
                )

                if result.result.get("success"):
                    created_backlinks.append(result.result)
                    logger.info(f"백링크 {i} 생성 성공")
                else:
                    failed_sites.append(site.get("domain"))
                    logger.warning(f"백링크 {i} 생성 실패: {site.get('domain')}")

            except Exception as e:
                logger.error(f"백링크 {i} 생성 중 오류: {e}")
                failed_sites.append(site.get("domain"))

        # 결과 요약
        success_count = len(created_backlinks)
        logger.info(f"다중 백링크 생성 완료: 성공 {success_count}/{quantity}")

        # 메타데이터 업데이트
        metadata = {
            "completed_at": datetime.now().isoformat(),
            "requested_quantity": quantity,
            "successful_count": success_count,
            "failed_sites": failed_sites,
            "created_backlinks": created_backlinks,
        }

        supabase_client.update_order_metadata(order_id, metadata)

        # 성공률에 따른 상태 업데이트
        if success_count >= quantity * 0.7:  # 70% 이상 성공 시
            supabase_client.update_order_status(order_id, "completed")
            status = "completed"
        else:
            supabase_client.update_order_status(order_id, "partial")
            status = "partial"

        return {
            "success": success_count > 0,
            "order_id": order_id,
            "status": status,
            "requested_quantity": quantity,
            "successful_count": success_count,
            "failed_count": len(failed_sites),
            "created_backlinks": created_backlinks,
            "message": f"Created {success_count}/{quantity} backlinks",
        }

    except Exception as e:
        logger.error(f"다중 백링크 생성 오류: {e}", exc_info=True)
        supabase_client.update_order_status(order_id, "failed")
        raise self.retry(exc=e)
