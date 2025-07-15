"""
이메일 발송 태스크 모듈 - Supabase REST API 방식
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from app.tasks.celery_app import celery as app
from app.services.email import EmailService
from app.services.supabase_client import supabase

logger = logging.getLogger(__name__)


# 디버깅용 print 함수
def debug_print(message: str, task_name: str = ""):
    """디버깅용 print 함수"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [EMAIL_TASK] [{task_name}] {message}")
    logger.info(f"[EMAIL_TASK] [{task_name}] {message}")


def safe_str(value, default="N/A"):
    """
    안전한 문자열 변환 함수
    Args:
        value: 변환할 값
        default: 기본값
    Returns:
        str: 안전하게 변환된 문자열
    """
    if value is None:
        return default

    try:
        return str(value)
    except Exception:
        return default


@app.task
def send_welcome_email(user_email: str):
    """
    신규 사용자 환영 이메일 발송 (5.4 기능)
    Args:
        user_email: 사용자 이메일 주소
    """
    debug_print(f"=== 환영 이메일 태스크 시작 ===", "send_welcome_email")
    debug_print(f"수신자: {user_email}", "send_welcome_email")

    try:
        debug_print("EmailService 초기화 중...", "send_welcome_email")
        email_service = EmailService()

        # HTML 콘텐츠
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">🎉 FollowSales에 오신 것을 환영합니다!</h2>
            
            <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">시작하기</h3>
                <p>✅ 무료 PBN 백링크 서비스를 이용하실 수 있습니다</p>
                <p>✅ 전문적인 SEO 상담을 받으실 수 있습니다</p>
                <p>✅ 다양한 백링크 패키지를 확인하세요</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                궁금한 점이 있으시면 언제든 연락주세요!<br>
                FollowSales 팀
            </p>
        </div>
        """

        debug_print("이메일 발송 시작...", "send_welcome_email")
        # 이메일 발송
        result = email_service.send_email(
            to_email=user_email,
            subject="[FollowSales] 환영합니다! 🎉",
            html_content=html_content,
        )
        debug_print(f"이메일 발송 결과: {result}", "send_welcome_email")

        debug_print("이메일 로그 저장 시작...", "send_welcome_email")
        # Supabase REST API로 이메일 로그 저장
        create_email_log_via_api(
            email_type="welcome",
            recipient_email=user_email,
            subject="[FollowSales] 환영합니다! 🎉",
            message_id=result.get("message_id"),
            template_type="user_welcome",
            extra_data={"signup_source": "pbn_rest_api"},
            status="sent" if result.get("success") else "failed",
        )

        debug_print(f"환영 이메일 태스크 완료 - 성공", "send_welcome_email")
        logger.info(f"Welcome email sent to {user_email}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": user_email,
        }

    except Exception as e:
        debug_print(f"환영 이메일 태스크 실패: {e}", "send_welcome_email")
        logger.error(f"Failed to send welcome email: {e}")
        return {"success": False, "error": str(e)}


@app.task
def send_order_confirmation_email(user_email: str, order_id: str, order_details: dict):
    """
    주문 확인 이메일 발송 (5.4 기능)
    Args:
        user_email: 사용자 이메일 주소
        order_id: 주문 ID
        order_details: 주문 상세 정보
    """
    debug_print(
        f"=== 주문 확인 이메일 태스크 시작 ===", "send_order_confirmation_email"
    )
    debug_print(
        f"수신자: {user_email}, 주문ID: {order_id}", "send_order_confirmation_email"
    )
    debug_print(f"주문 상세: {order_details}", "send_order_confirmation_email")

    try:
        debug_print("EmailService 초기화 중...", "send_order_confirmation_email")
        email_service = EmailService()

        target_url = safe_str(order_details.get("target_url", ""))
        keyword = safe_str(order_details.get("keyword", ""))

        debug_print(
            f"처리할 URL: {target_url}, 키워드: {keyword}",
            "send_order_confirmation_email",
        )

        # HTML 콘텐츠
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">🎉 주문이 성공적으로 접수되었습니다!</h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">주문 정보</h3>
                <p><strong>주문 번호:</strong> {order_id}</p>
                <p><strong>대상 URL:</strong> {target_url}</p>
                <p><strong>키워드:</strong> {keyword}</p>
                <p><strong>주문 일시:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #059669; margin-top: 0;">다음 단계</h3>
                <p>✅ 주문이 접수되었습니다</p>
                <p>🔄 백링크 구축 작업이 시작됩니다</p>
                <p>📧 완료 시 결과를 이메일로 알려드립니다</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                감사합니다!<br>
                FollowSales 팀
            </p>
        </div>
        """

        debug_print("이메일 발송 시작...", "send_order_confirmation_email")
        # 이메일 발송
        result = email_service.send_email(
            to_email=user_email,
            subject=f"[FollowSales] 주문이 접수되었습니다 - {order_id}",
            html_content=html_content,
        )
        debug_print(f"이메일 발송 결과: {result}", "send_order_confirmation_email")

        debug_print("이메일 로그 저장 시작...", "send_order_confirmation_email")
        # Supabase REST API로 이메일 로그 저장
        create_email_log_via_api(
            email_type="order_confirmation",
            recipient_email=user_email,
            subject=f"[FollowSales] 주문이 접수되었습니다 - {order_id}",
            message_id=result.get("message_id"),
            order_id=order_id,
            template_type="pbn_order",
            extra_data={
                "target_url": target_url,
                "keyword": keyword,
                "api_endpoint": "/api/v1/pbn/rest",
            },
            status="sent" if result.get("success") else "failed",
        )

        debug_print(
            f"주문 확인 이메일 태스크 완료 - 성공", "send_order_confirmation_email"
        )
        logger.info(f"Order confirmation email sent to {user_email}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": user_email,
        }

    except Exception as e:
        debug_print(
            f"주문 확인 이메일 태스크 실패: {e}", "send_order_confirmation_email"
        )
        logger.error(f"Failed to send order confirmation email: {e}")
        return {"success": False, "error": str(e)}


@app.task
def send_backlink_completion_email(
    user_email: str, order_id: str, backlink_result: dict
):
    """
    백링크 구축 완료 이메일 발송 (5.4 기능)
    Args:
        user_email: 사용자 이메일 주소
        order_id: 주문 ID
        backlink_result: 백링크 구축 결과
    """
    try:
        email_service = EmailService()

        # 백링크 결과 정보 추출
        target_url = safe_str(backlink_result.get("target_url", ""))
        keyword = safe_str(backlink_result.get("keyword", ""))
        pbn_urls = backlink_result.get("pbn_urls", [])
        total_backlinks = len(pbn_urls)

        # PBN URL 리스트 HTML 생성
        pbn_list_html = ""
        for i, pbn_url in enumerate(pbn_urls[:10], 1):  # 최대 10개까지만 표시
            pbn_list_html += f"<p>🔗 {i}. {safe_str(pbn_url)}</p>"

        if total_backlinks > 10:
            pbn_list_html += f"<p>... 외 {total_backlinks - 10}개 더</p>"

        # HTML 콘텐츠
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #059669;">🎉 백링크 구축이 완료되었습니다!</h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">주문 정보</h3>
                <p><strong>주문 번호:</strong> {order_id}</p>
                <p><strong>대상 URL:</strong> {target_url}</p>
                <p><strong>키워드:</strong> {keyword}</p>
                <p><strong>완료 일시:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #059669; margin-top: 0;">구축 결과</h3>
                <p><strong>총 백링크 수:</strong> {total_backlinks}개</p>
                <div style="margin-top: 15px;">
                    <h4 style="color: #374151; margin-bottom: 10px;">구축된 PBN 사이트:</h4>
                    {pbn_list_html}
                </div>
            </div>
            
            <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #92400e; margin-top: 0;">📈 SEO 효과 안내</h3>
                <p>• 백링크 효과는 보통 2-4주 후부터 나타납니다</p>
                <p>• 지속적인 SEO 최적화를 권장합니다</p>
                <p>• 추가 백링크가 필요하시면 언제든 연락주세요</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                감사합니다!<br>
                FollowSales 팀
            </p>
        </div>
        """

        # 이메일 발송
        result = email_service.send_email(
            to_email=user_email,
            subject=f"[FollowSales] 백링크 구축이 완료되었습니다! - {order_id}",
            html_content=html_content,
        )

        # Supabase REST API로 이메일 로그 저장
        create_email_log_via_api(
            email_type="backlink_completion",
            recipient_email=user_email,
            subject=f"[FollowSales] 백링크 구축이 완료되었습니다! - {order_id}",
            message_id=result.get("message_id"),
            order_id=order_id,
            template_type="pbn_completion",
            extra_data={
                "target_url": target_url,
                "keyword": keyword,
                "total_backlinks": total_backlinks,
                "pbn_urls": pbn_urls,
            },
            status="sent" if result.get("success") else "failed",
        )

        logger.info(f"Backlink completion email sent to {user_email}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": user_email,
            "total_backlinks": total_backlinks,
        }

    except Exception as e:
        logger.error(f"Failed to send backlink completion email: {e}")
        return {"success": False, "error": str(e)}


@app.task
def send_admin_failure_alert(
    order_id: str, error_details: dict, admin_email: str = "vnfm0580@gmail.com"
):
    """
    관리자 실패 알림 이메일 발송 (5.4 기능)
    Args:
        order_id: 주문 ID
        error_details: 에러 상세 정보
        admin_email: 관리자 이메일 주소
    """
    try:
        email_service = EmailService()

        error_type = safe_str(error_details.get("error_type", "Unknown"))
        error_message = safe_str(error_details.get("error_message", ""))
        target_url = safe_str(error_details.get("target_url", ""))
        keyword = safe_str(error_details.get("keyword", ""))

        # HTML 콘텐츠
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc2626;">🚨 백링크 구축 실패 알림</h2>
            
            <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
                <h3 style="color: #991b1b; margin-top: 0;">실패 정보</h3>
                <p><strong>주문 번호:</strong> {order_id}</p>
                <p><strong>에러 타입:</strong> {error_type}</p>
                <p><strong>에러 메시지:</strong> {error_message}</p>
                <p><strong>대상 URL:</strong> {target_url}</p>
                <p><strong>키워드:</strong> {keyword}</p>
                <p><strong>발생 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #92400e; margin-top: 0;">🔧 권장 조치사항</h3>
                <p>• 에러 로그를 확인하여 원인을 파악하세요</p>
                <p>• 필요시 수동으로 백링크를 구축하세요</p>
                <p>• 고객에게 상황을 안내하세요</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                시스템 자동 알림<br>
                FollowSales 관리시스템
            </p>
        </div>
        """

        # 이메일 발송
        result = email_service.send_email(
            to_email=admin_email,
            subject=f"[FollowSales 관리자] 백링크 구축 실패 - {order_id}",
            html_content=html_content,
        )

        # Supabase REST API로 이메일 로그 저장
        create_email_log_via_api(
            email_type="admin_alert",
            recipient_email=admin_email,
            subject=f"[FollowSales 관리자] 백링크 구축 실패 - {order_id}",
            message_id=result.get("message_id"),
            order_id=order_id,
            template_type="admin_failure",
            extra_data={
                "error_type": error_type,
                "error_message": error_message,
                "target_url": target_url,
                "keyword": keyword,
            },
            status="sent" if result.get("success") else "failed",
        )

        logger.info(f"Admin failure alert sent for order {order_id}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": admin_email,
        }

    except Exception as e:
        logger.error(f"Failed to send admin failure alert: {e}")
        return {"success": False, "error": str(e)}


@app.task
def send_backlink_report_email(user_email: str, backlinks: List[Dict[str, Any]]):
    """
    백링크 보고서 이메일 발송 (5.4 기능)
    Args:
        user_email: 사용자 이메일 주소
        backlinks: 백링크 목록
    """
    try:
        email_service = EmailService()

        total_backlinks = len(backlinks)

        # 백링크 리스트 HTML 생성 (최대 20개까지만 표시)
        backlink_list_html = ""
        for i, backlink in enumerate(backlinks[:20], 1):
            source_url = safe_str(backlink.get("source_url", ""))
            target_url = safe_str(backlink.get("target_url", ""))
            keyword = safe_str(backlink.get("keyword", ""))

            backlink_list_html += f"""
            <div style="border-bottom: 1px solid #e5e7eb; padding: 10px 0;">
                <p><strong>{i}. {keyword}</strong></p>
                <p style="margin: 5px 0; font-size: 14px; color: #6b7280;">
                    📍 출처: {source_url}<br>
                    🎯 대상: {target_url}
                </p>
            </div>
            """

        if total_backlinks > 20:
            backlink_list_html += f"<p style='text-align: center; color: #6b7280; margin-top: 15px;'>... 외 {total_backlinks - 20}개 더</p>"

        # HTML 콘텐츠
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">📊 백링크 보고서</h2>
            
            <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">📈 요약</h3>
                <p><strong>총 백링크 수:</strong> {total_backlinks}개</p>
                <p><strong>보고서 생성일:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #374151; margin-top: 0;">🔗 백링크 목록</h3>
                {backlink_list_html}
            </div>
            
            <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #059669; margin-top: 0;">💡 SEO 팁</h3>
                <p>• 백링크 품질이 양보다 중요합니다</p>
                <p>• 다양한 도메인에서의 백링크가 효과적입니다</p>
                <p>• 정기적인 백링크 모니터링을 권장합니다</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                감사합니다!<br>
                FollowSales 팀
            </p>
        </div>
        """

        # 이메일 발송
        result = email_service.send_email(
            to_email=user_email,
            subject=f"[FollowSales] 백링크 보고서 ({total_backlinks}개)",
            html_content=html_content,
        )

        # Supabase REST API로 이메일 로그 저장
        create_email_log_via_api(
            email_type="backlink_report",
            recipient_email=user_email,
            subject=f"[FollowSales] 백링크 보고서 ({total_backlinks}개)",
            message_id=result.get("message_id"),
            template_type="report",
            extra_data={
                "total_backlinks": total_backlinks,
                "report_type": "backlink_summary",
            },
            status="sent" if result.get("success") else "failed",
        )

        logger.info(f"Backlink report email sent to {user_email}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": user_email,
            "total_backlinks": total_backlinks,
        }

    except Exception as e:
        logger.error(f"Failed to send backlink report email: {e}")
        return {"success": False, "error": str(e)}


@app.task
def send_event_notification_email(user_email: str, event_type: str, event_data: dict):
    """
    이벤트 알림 이메일 발송 (5.4 기능)
    Args:
        user_email: 사용자 이메일 주소
        event_type: 이벤트 타입
        event_data: 이벤트 데이터
    """
    try:
        email_service = EmailService()

        # 이벤트 타입별 제목과 내용 설정
        if event_type == "promotion":
            subject = "[FollowSales] 🎁 특별 프로모션 안내"
            content = "새로운 프로모션이 시작되었습니다!"
        elif event_type == "system_update":
            subject = "[FollowSales] 🔧 시스템 업데이트 안내"
            content = "시스템이 업데이트되었습니다."
        else:
            subject = f"[FollowSales] {event_type} 알림"
            content = "새로운 알림이 있습니다."

        # HTML 콘텐츠
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">{content}</h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">알림 내용</h3>
                <p>{safe_str(event_data.get('message', ''))}</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                FollowSales 팀
            </p>
        </div>
        """

        # 이메일 발송
        result = email_service.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
        )

        # Supabase REST API로 이메일 로그 저장
        create_email_log_via_api(
            email_type="event_notification",
            recipient_email=user_email,
            subject=subject,
            message_id=result.get("message_id"),
            template_type=f"event_{event_type}",
            extra_data=event_data,
            status="sent" if result.get("success") else "failed",
        )

        logger.info(f"Event notification email sent to {user_email}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": user_email,
        }

    except Exception as e:
        logger.error(f"Failed to send event notification email: {e}")
        return {"success": False, "error": str(e)}


@app.task(queue="email")
def send_email_task(to_email: str, subject: str, html_content: str):
    """
    범용 이메일 발송 태스크 (5.4 기능)
    Args:
        to_email: 수신자 이메일
        subject: 이메일 제목
        html_content: HTML 내용
    """
    try:
        email_service = EmailService()
        result = email_service.send_email(to_email, subject, html_content)

        logger.info(f"Email sent to {to_email}")
        return result
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"success": False, "error": str(e)}


def create_email_log_via_api(
    email_type: str,
    recipient_email: str,
    subject: str,
    message_id: str = None,
    order_id: str = None,
    template_type: str = None,
    extra_data: dict = None,
    status: str = "sent",
):
    """
    Supabase REST API를 통한 이메일 로그 저장
    Args:
        email_type: 이메일 타입
        recipient_email: 수신자 이메일
        subject: 이메일 제목 (최대 200자)
        message_id: 메시지 ID
        order_id: 주문 ID
        template_type: 템플릿 타입
        extra_data: 추가 데이터 (JSONB)
        status: 상태
    """
    try:
        debug_print(
            f"이메일 로그 저장 시작: {email_type} -> {recipient_email}",
            "create_email_log_via_api",
        )

        # 제목 길이 제한 (200자)
        subject_limited = subject[:200] if subject else ""

        log_data = {
            "email_type": email_type,
            "recipient_email": recipient_email,
            "subject": subject_limited,
            "status": status,
            "sent_at": datetime.now().isoformat(),
        }

        # 선택적 필드들
        if message_id:
            log_data["message_id"] = message_id
        if order_id:
            log_data["order_id"] = order_id
        if template_type:
            log_data["template_type"] = template_type
        if extra_data:
            log_data["extra_data"] = extra_data

        debug_print(f"Supabase에 삽입할 데이터: {log_data}", "create_email_log_via_api")

        # Supabase에 삽입
        result = supabase.table("email_logs").insert(log_data).execute()

        debug_print(f"이메일 로그 저장 완료: {result.data}", "create_email_log_via_api")
        logger.info(f"Email log saved via API: {email_type} to {recipient_email}")
        return result.data

    except Exception as e:
        debug_print(f"이메일 로그 저장 실패: {e}", "create_email_log_via_api")
        logger.error(f"Failed to save email log via API: {e}")
        # 이메일 로그 저장 실패해도 이메일 발송은 성공으로 처리
        return None
