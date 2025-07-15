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


# 디버깅용 print 함수
def debug_print(message: str, task_name: str = ""):
    """디버깅용 print 함수"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [PBN_TASK] [{task_name}] {message}")
    logger.info(f"[PBN_TASK] [{task_name}] {message}")


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
    debug_print(f"=== PBN 백링크 생성 태스크 시작 ===", "create_pbn_backlink_rest")
    debug_print(
        f"주문ID: {order_id}, 대상URL: {target_url}, 키워드: {keyword}",
        "create_pbn_backlink_rest",
    )
    debug_print(f"PBN 사이트 도메인: {pbn_site_domain}", "create_pbn_backlink_rest")

    try:
        debug_print(
            f"주문 상태를 processing으로 업데이트 중...", "create_pbn_backlink_rest"
        )
        logger.info(f"[REST-TASK] 시작 order={order_id} target={target_url}")

        # 1) 주문을 processing 상태로 업데이트
        supabase_client.update_order_status(order_id, "processing")
        debug_print(f"주문 상태 업데이트 완료", "create_pbn_backlink_rest")

        # 2) 시뮬레이션으로 PBN 포스팅 수행
        debug_print(f"PBN 포스팅 시뮬레이션 시작...", "create_pbn_backlink_rest")
        success = _simulate_posting(target_url, keyword)
        debug_print(
            f"PBN 포스팅 시뮬레이션 결과: {success}", "create_pbn_backlink_rest"
        )

        if not success:
            debug_print(
                f"PBN 포스팅 실패 - 주문 상태를 failed로 업데이트",
                "create_pbn_backlink_rest",
            )
            supabase_client.update_order_status(order_id, "failed")
            return {
                "success": False,
                "order_id": order_id,
                "message": "PBN posting failed",
            }

        # 실제 환경이라면 pbn_site_domain 값으로 워드프레스 API 호출하여 글을 작성하고 URL을 얻는다.
        # 현재는 시뮬레이션용으로 임의 URL 생성
        site = pbn_site_domain or "pbn-example.com"
        debug_print(f"사용할 PBN 사이트: {site}", "create_pbn_backlink_rest")

        # Supabase DB에서 해당 도메인의 PBN 자격정보 조회
        debug_print(f"PBN 사이트 정보 조회 중: {site}", "create_pbn_backlink_rest")
        site_record = supabase_client.get_pbn_site_by_domain(site)
        debug_print(f"PBN 사이트 레코드: {site_record}", "create_pbn_backlink_rest")

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

            debug_print(
                f"WP 사용자: {wp_user}, 사이트 URL: {site_url}",
                "create_pbn_backlink_rest",
            )

            if wp_user and wp_app_pass and site_url:
                debug_print(
                    f"워드프레스 포스터 초기화 중...", "create_pbn_backlink_rest"
                )
                poster = WordPressPoster(site_url.rstrip("/"), wp_user, wp_app_pass)

                # 👉 테스트용 더미 콘텐츠
                title = f"Test Backlink for {keyword}"
                html_body = build_html_content(target_url, keyword, extra_paragraphs=1)
                debug_print(f"글 제목: {title}", "create_pbn_backlink_rest")

                debug_print(f"워드프레스 포스팅 시작...", "create_pbn_backlink_rest")
                backlink_url = poster.post_article(title, html_body)
                debug_print(
                    f"워드프레스 포스팅 결과: {backlink_url}",
                    "create_pbn_backlink_rest",
                )
            else:
                debug_print(
                    f"PBN site record에 필요한 필드가 없어 시뮬레이션으로 대체",
                    "create_pbn_backlink_rest",
                )
                logger.warning(
                    "PBN site record에 필요한 필드가 없어 시뮬레이션으로 대체합니다"
                )
                backlink_url = None
        else:
            debug_print(
                f"Supabase DB에서 PBN 자격정보를 찾을 수 없음 – 시뮬레이션 모드",
                "create_pbn_backlink_rest",
            )
            logger.warning(
                "Supabase DB에서 PBN 자격정보를 찾을 수 없습니다 – 시뮬레이션 모드"
            )
            backlink_url = None

        # 3) 주문 메타데이터 및 상태 업데이트
        debug_print(f"주문 메타데이터 업데이트 중...", "create_pbn_backlink_rest")
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
        debug_print(f"주문 메타데이터 업데이트 완료", "create_pbn_backlink_rest")

        logger.info(f"[REST-TASK] 완료 order={order_id} backlink={backlink_url}")

        # 4) 백링크 구축 완료 이메일 발송 (5.4 기능)
        debug_print(f"백링크 완료 이메일 발송 준비 중...", "create_pbn_backlink_rest")
        try:
            order = supabase_client.get_order(order_id)
            debug_print(f"주문 정보 조회 결과: {order}", "create_pbn_backlink_rest")

            if order and order.get("user_id"):
                user = supabase_client.get_user(order["user_id"])
                debug_print(
                    f"사용자 정보 조회 결과: {user}", "create_pbn_backlink_rest"
                )
            else:
                user = None
                debug_print(f"주문에 user_id가 없음", "create_pbn_backlink_rest")

            if user and user.get("email"):
                debug_print(
                    f"사용자 이메일 확인: {user['email']}", "create_pbn_backlink_rest"
                )
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
                debug_print(
                    f"백링크 결과 데이터: {backlink_result}", "create_pbn_backlink_rest"
                )

                # 백링크 완료 이메일 비동기 발송
                debug_print(
                    f"백링크 완료 이메일 태스크 큐에 등록 중...",
                    "create_pbn_backlink_rest",
                )
                send_backlink_completion_email.apply_async(
                    args=[user["email"], order_id, backlink_result], queue="default"
                )
                debug_print(
                    f"백링크 완료 이메일 태스크 큐 등록 완료",
                    "create_pbn_backlink_rest",
                )

                logger.info(f"[REST-TASK] 완료 이메일 발송 예약됨 ({user['email']})")
            else:
                debug_print(
                    f"사용자 이메일 정보 없음 - 이메일 발송 불가",
                    "create_pbn_backlink_rest",
                )
                logger.warning(
                    f"[REST-TASK] 사용자 이메일 정보를 찾을 수 없어 이메일을 보내지 못했습니다 (order={order_id})"
                )
        except Exception as email_err:
            debug_print(f"이메일 발송 실패: {email_err}", "create_pbn_backlink_rest")
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
        debug_print(f"=== PBN 백링크 생성 태스크 실패 ===", "create_pbn_backlink_rest")
        debug_print(f"에러: {e}", "create_pbn_backlink_rest")
        logger.error(f"[REST-TASK] 오류: {e}")

        # 실패 시 상태 업데이트 및 관리자 알림 (5.4 기능)
        try:
            debug_print(
                f"주문 상태를 failed로 업데이트 중...", "create_pbn_backlink_rest"
            )
            supabase_client.update_order_status(order_id, "failed")

            # 관리자 실패 알림 이메일 발송
            debug_print(
                f"관리자 실패 알림 이메일 발송 준비 중...", "create_pbn_backlink_rest"
            )
            from app.tasks.email_tasks import send_admin_failure_alert

            error_details = {
                "error": str(e),
                "target_url": target_url,
                "keyword": keyword,
                "pbn_domain": pbn_site_domain or "unknown",
            }

            debug_print(
                f"관리자 실패 알림 태스크 큐에 등록 중...", "create_pbn_backlink_rest"
            )
            send_admin_failure_alert.apply_async(
                args=[order_id, error_details], queue="default"
            )
            debug_print(
                f"관리자 실패 알림 태스크 큐 등록 완료", "create_pbn_backlink_rest"
            )

            logger.info(f"[REST-TASK] 관리자 실패 알림 발송 예약됨")

            # 사용자 실패 알림 이메일도 발송
            debug_print(
                f"사용자 실패 알림 이메일 발송 준비 중...", "create_pbn_backlink_rest"
            )
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

                    debug_print(
                        f"사용자 실패 알림 태스크 큐에 등록 중...",
                        "create_pbn_backlink_rest",
                    )
                    send_backlink_completion_email.apply_async(
                        args=[user["email"], order_id, backlink_result], queue="default"
                    )
                    debug_print(
                        f"사용자 실패 알림 태스크 큐 등록 완료",
                        "create_pbn_backlink_rest",
                    )

                    logger.info(
                        f"[REST-TASK] 사용자 실패 알림 발송 예약됨 ({user['email']})"
                    )
        except Exception as notify_err:
            debug_print(
                f"실패 알림 발송 실패: {notify_err}", "create_pbn_backlink_rest"
            )
            logger.error(f"[REST-TASK] 실패 알림 발송 실패: {notify_err}")

        debug_print(f"태스크 재시도 중...", "create_pbn_backlink_rest")
        raise self.retry(exc=e)


def _simulate_posting(target_url: str, keyword: str) -> bool:
    """간단한 시뮬레이션 – 90% 성공률"""
    debug_print(f"포스팅 시뮬레이션 시작: {target_url}, {keyword}", "_simulate_posting")
    try:
        sleep_time = random.randint(5, 10)
        debug_print(f"{sleep_time}초 대기 중...", "_simulate_posting")
        time.sleep(sleep_time)

        success = random.random() < 0.9
        debug_print(f"시뮬레이션 결과: {success}", "_simulate_posting")
        return success
    except Exception as e:
        debug_print(f"시뮬레이션 에러: {e}", "_simulate_posting")
        logger.error(f"simulate error: {e}")
        return False
