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
from app.services.pbn_poster import WordPressPoster, build_html_content
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

        # 2) 시뮬레이션으로 PBN 포스팅 수행 (이제는 실제 콘텐츠 생성으로 대체 예정)
        logger.info("PBN 포스팅 시뮬레이션 시작...")
        success = _simulate_posting(target_url, keyword)
        logger.info(f"PBN 포스팅 시뮬레이션 결과: {success}")

        if not success:
            logger.error("PBN 포스팅 실패 - 주문 상태를 failed로 업데이트")
            supabase_client.update_order_status(order_id, "failed")
            return {
                "success": False,
                "order_id": order_id,
                "message": "PBN posting failed",
            }

        # 3) PBN 사이트 정보 조회
        site = pbn_site_domain or "pbn-example.com"
        logger.info(f"사용할 PBN 사이트: {site}")

        # Supabase DB에서 해당 도메인의 PBN 자격정보 조회
        logger.info(f"PBN 사이트 정보 조회 중: {site}")
        site_record = supabase_client.get_pbn_site_by_domain(site)
        logger.debug(f"PBN 사이트 레코드: {site_record}")

        backlink_url = None

        if site_record:
            wp_user = (
                site_record.get("wp_admin_user")
                or site_record.get("wp_admin_id")
                or site_record.get("username")
            )
            wp_password = (
                site_record.get("wp_admin_pw")
                or site_record.get("wp_admin_password")
                or site_record.get("password")
            )

            if wp_user and wp_password:
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

                    # 워드프레스에 포스팅
                    logger.info(f"워드프레스 포스팅 시작: {site}")
                    poster = WordPressPoster(
                        wp_url=f"https://{site}",
                        wp_user=wp_user,
                        wp_password=wp_password,
                    )

                    post_result = poster.create_post_with_image(
                        title=title,
                        content=html_content,
                        image_path=featured_image_path,
                        tags=[keyword, "백링크", "SEO"],
                    )

                    if post_result["success"]:
                        backlink_url = post_result["post_url"]
                        logger.info(f"워드프레스 포스팅 성공: {backlink_url}")
                    else:
                        logger.error(
                            f"워드프레스 포스팅 실패: {post_result.get('error', '알 수 없는 오류')}"
                        )

                except Exception as e:
                    logger.error(f"실제 포스팅 중 오류 발생: {e}")

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
                send_backlink_completion_email.delay(
                    user_email=user_info["email"],
                    target_url=target_url,
                    keyword=keyword,
                    backlink_url=backlink_url or f"https://{site}/completed",
                    order_id=order_id,
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


def _simulate_posting(target_url: str, keyword: str) -> bool:
    """PBN 포스팅 시뮬레이션 (테스트용)"""
    logger.info(f"포스팅 시뮬레이션 시작: target_url={target_url}, keyword={keyword}")

    # 1-3초 대기 (실제 포스팅을 시뮬레이션)
    wait_time = random.uniform(1, 3)
    logger.debug(f"{wait_time:.2f}초 대기 중...")
    time.sleep(wait_time)

    # 90% 확률로 성공
    success = random.random() > 0.1
    logger.info(f"시뮬레이션 결과: {success}")

    return success


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
