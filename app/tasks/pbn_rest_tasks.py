"""
REST-only PBN 백링크 Celery 태스크 (Supabase API)
"""

import logging
import random
import time
from datetime import datetime
from typing import List

from app.tasks.celery_app import celery as app
from app.services.supabase_client import supabase_client
from app.services.pbn_poster import WordPressPoster, build_html_content

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
    """무료 PBN 1개 생성 – REST 버전"""
    try:
        logger.info(f"[REST-TASK] 시작 order={order_id} target={target_url}")

        # 1) 주문을 processing 상태로 업데이트
        supabase_client.update_order_status(order_id, "processing")

        # 2) 시뮬레이션으로 PBN 포스팅 수행
        success = _simulate_posting(target_url, keyword)

        if not success:
            supabase_client.update_order_status(order_id, "failed")
            return {
                "success": False,
                "order_id": order_id,
                "message": "PBN posting failed",
            }

        # 실제 환경이라면 pbn_site_domain 값으로 워드프레스 API 호출하여 글을 작성하고 URL을 얻는다.
        # 현재는 시뮬레이션용으로 임의 URL 생성
        site = pbn_site_domain or "pbn-example.com"

        # Supabase DB에서 해당 도메인의 PBN 자격정보 조회
        site_record = supabase_client.get_pbn_site_by_domain(site)

        if site_record:
            wp_user = (
                site_record.get("wp_admin_user")
                or site_record.get("wp_admin_id")
                or site_record.get("username")
            )
            wp_app_pass = (
                site_record.get("wp_app_pass")
                or site_record.get("wp_app_key")
                or site_record.get("app_password")
            )
            site_url = (
                site_record.get("domain")
                or site_record.get("site_url")
                or site_record.get("wp_admin_url")
                or site
            )

            if wp_user and wp_app_pass and site_url:
                poster = WordPressPoster(site_url.rstrip("/"), wp_user, wp_app_pass)

                # 👉 테스트용 더미 콘텐츠
                title = f"Test Backlink for {keyword}"
                html_body = build_html_content(target_url, keyword, extra_paragraphs=1)

                backlink_url = poster.post_article(title, html_body)
            else:
                logger.warning(
                    "PBN site record에 필요한 필드가 없어 시뮬레이션으로 대체합니다"
                )
                backlink_url = None
        else:
            logger.warning(
                "Supabase DB에서 PBN 자격정보를 찾을 수 없습니다 – 시뮬레이션 모드"
            )
            backlink_url = None

        # 3) 주문 메타데이터 및 상태 업데이트
        meta_patch = {
            "status": "completed",
            "order_metadata": {
                "backlink_url": backlink_url,
                "completed_at": datetime.utcnow().isoformat(),
                "anchor_text": keyword,
                "target_url": target_url,
                "selected_pbn_site": site,
                "method": "supabase_rest",
            },
        }
        supabase_client.update_order(order_id, meta_patch)

        logger.info(f"[REST-TASK] 완료 order={order_id} backlink={backlink_url}")

        # 4) 백링크 구축 완료 이메일 발송 (5.4 기능)
        try:
            order = supabase_client.get_order(order_id)
            if order and order.get("user_id"):
                user = supabase_client.get_user(order["user_id"])
            else:
                user = None

            if user and user.get("email"):
                # 새로운 이메일 작업 사용 (5.4 기능)
                from app.tasks.email_tasks import send_backlink_completion_email

                # 백링크 구축 결과 데이터 준비
                backlink_result = {
                    "success": True,
                    "target_url": target_url,
                    "keyword": keyword,
                    "pbn_urls": [backlink_url] if backlink_url else [],
                    "total_backlinks": 1 if backlink_url else 0,
                    "pbn_domain": site,
                    "backlink_url": backlink_url,
                }

                # 백링크 완료 이메일 비동기 발송
                send_backlink_completion_email.apply_async(
                    args=[user["email"], order_id, backlink_result], queue="default"
                )

                logger.info(f"[REST-TASK] 완료 이메일 발송 예약됨 ({user['email']})")
            else:
                logger.warning(
                    f"[REST-TASK] 사용자 이메일 정보를 찾을 수 없어 이메일을 보내지 못했습니다 (order={order_id})"
                )
        except Exception as email_err:
            logger.error(f"[REST-TASK] 이메일 발송 실패: {email_err}")

        # fallback: simulation when real posting fails
        if not backlink_url:
            backlink_url = f"https://{site.strip('/')}/post-{random.randint(1000,9999)}"
            logger.warning(
                f"[REST-TASK] 실제 업로드 실패 – 시뮬레이션 URL 저장 ({backlink_url})"
            )
            supabase_client.update_order(
                order_id,
                {
                    "status": "completed",
                    "order_metadata": {
                        "backlink_url": backlink_url,
                        "completed_at": datetime.utcnow().isoformat(),
                        "anchor_text": keyword,
                        "target_url": target_url,
                        "selected_pbn_site": site,
                        "method": "simulation",
                    },
                },
            )
            return {
                "success": True,
                "order_id": order_id,
                "backlink_url": backlink_url,
                "pbn_site": site,
                "simulated": True,
            }

        return {
            "success": True,
            "order_id": order_id,
            "backlink_url": backlink_url,
            "pbn_site": site,
        }

    except Exception as e:
        logger.error(f"[REST-TASK] 오류: {e}")

        # 실패 시 상태 업데이트 및 관리자 알림 (5.4 기능)
        try:
            supabase_client.update_order_status(order_id, "failed")

            # 관리자 실패 알림 이메일 발송
            from app.tasks.email_tasks import send_admin_failure_alert

            error_details = {
                "error": str(e),
                "target_url": target_url,
                "keyword": keyword,
                "pbn_domain": pbn_site_domain or "unknown",
            }

            send_admin_failure_alert.apply_async(
                args=[order_id, error_details], queue="default"
            )

            logger.info(f"[REST-TASK] 관리자 실패 알림 발송 예약됨")

            # 사용자 실패 알림 이메일도 발송
            order = supabase_client.get_order(order_id)
            if order and order.get("user_id"):
                user = supabase_client.get_user(order["user_id"])
                if user and user.get("email"):
                    from app.tasks.email_tasks import send_backlink_completion_email

                    backlink_result = {
                        "success": False,
                        "target_url": target_url,
                        "keyword": keyword,
                        "pbn_urls": [],
                        "total_backlinks": 0,
                        "pbn_domain": pbn_site_domain or "unknown",
                        "error": str(e),
                    }

                    send_backlink_completion_email.apply_async(
                        args=[user["email"], order_id, backlink_result], queue="default"
                    )

                    logger.info(
                        f"[REST-TASK] 사용자 실패 알림 발송 예약됨 ({user['email']})"
                    )
        except Exception as notify_err:
            logger.error(f"[REST-TASK] 실패 알림 발송 실패: {notify_err}")

        raise self.retry(exc=e)


def _simulate_posting(target_url: str, keyword: str) -> bool:
    """간단한 시뮬레이션 – 90% 성공률"""
    try:
        time.sleep(random.randint(5, 10))
        return random.random() < 0.9
    except Exception as e:
        logger.error(f"simulate error: {e}")
        return False
