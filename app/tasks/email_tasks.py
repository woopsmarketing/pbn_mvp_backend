"""
?�메??발송 ?�스??모듈 - Supabase REST API 방식
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from app.tasks.celery_app import celery as app
from app.services.email import EmailService
from app.services.supabase_client import supabase

logger = logging.getLogger(__name__)


# ?�버깅용 print ?�수
def debug_print(message: str, task_name: str = ""):
    """?�버깅용 print ?�수"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [EMAIL_TASK] [{task_name}] {message}")
    logger.info(f"[EMAIL_TASK] [{task_name}] {message}")


def safe_str(value, default="N/A"):
    """
    ?�전??문자??변???�수
    Args:
        value: 변?�할 �?
        default: 기본�?
    Returns:
        str: ?�전?�게 변?�된 문자??
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
    ?�규 ?�용???�영 ?�메??발송 (5.4 기능)
    Args:
        user_email: ?�용???�메??주소
    """
    debug_print(f"=== ?�영 ?�메???�스???�작 ===", "send_welcome_email")
    debug_print(f"?�신?? {user_email}", "send_welcome_email")

    try:
        debug_print("EmailService 초기??�?..", "send_welcome_email")
        email_service = EmailService()

        # HTML 콘텐�?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">?�� BacklinkVending???�신 것을 ?�영?�니??</h2>
            
            <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">?�작?�기</h3>
                <p>??무료 PBN 백링???�비?��? ?�용?�실 ???�습?�다</p>
                <p>???�문?�인 SEO ?�담??받으?????�습?�다</p>
                <p>???�양??백링???�키지�??�인?�세??/p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                궁금???�이 ?�으?�면 ?�제???�락주세??<br>
                BacklinkVending ?�
            </p>
        </div>
        """

        debug_print("?�메??발송 ?�작...", "send_welcome_email")
        # ?�메??발송
        result = email_service.send_email(
            to_email=user_email,
            subject="[BacklinkVending] ?�영?�니?? ?��",
            html_content=html_content,
        )
        debug_print(f"?�메??발송 결과: {result}", "send_welcome_email")

        debug_print("?�메??로그 ?�???�작...", "send_welcome_email")
        # Supabase REST API�??�메??로그 ?�??
        create_email_log_via_api(
            email_type="welcome",
            recipient_email=user_email,
            subject="[BacklinkVending] ?�영?�니?? ?��",
            message_id=result.get("message_id"),
            template_type="user_welcome",
            extra_data={"signup_source": "pbn_rest_api"},
            status="sent" if result.get("success") else "failed",
        )

        debug_print(f"?�영 ?�메???�스???�료 - ?�공", "send_welcome_email")
        logger.info(f"Welcome email sent to {user_email}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": user_email,
        }

    except Exception as e:
        debug_print(f"?�영 ?�메???�스???�패: {e}", "send_welcome_email")
        logger.error(f"Failed to send welcome email: {e}")
        return {"success": False, "error": str(e)}


@app.task
def send_order_confirmation_email(user_email: str, order_id: str, order_details: dict):
    """
    주문 ?�인 ?�메??발송 (5.4 기능)
    Args:
        user_email: ?�용???�메??주소
        order_id: 주문 ID
        order_details: 주문 ?�세 ?�보
    """
    debug_print(
        f"=== 주문 ?�인 ?�메???�스???�작 ===", "send_order_confirmation_email"
    )
    debug_print(
        f"?�신?? {user_email}, 주문ID: {order_id}", "send_order_confirmation_email"
    )
    debug_print(f"주문 ?�세: {order_details}", "send_order_confirmation_email")

    try:
        debug_print("EmailService 초기??�?..", "send_order_confirmation_email")
        email_service = EmailService()

        target_url = safe_str(order_details.get("target_url", ""))
        keyword = safe_str(order_details.get("keyword", ""))

        debug_print(
            f"처리??URL: {target_url}, ?�워?? {keyword}",
            "send_order_confirmation_email",
        )

        # HTML 콘텐�?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">?�� 주문???�공?�으�??�수?�었?�니??</h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">주문 ?�보</h3>
                <p><strong>주문 번호:</strong> {order_id}</p>
                <p><strong>?�??URL:</strong> {target_url}</p>
                <p><strong>?�워??</strong> {keyword}</p>
                <p><strong>주문 ?�시:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #059669; margin-top: 0;">?�음 ?�계</h3>
                <p>??주문???�수?�었?�니??/p>
                <p>?�� 백링??구축 ?�업???�작?�니??/p>
                <p>?�� ?�료 ??결과�??�메?�로 ?�려?�립?�다</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                감사?�니??<br>
                BacklinkVending ?�
            </p>
        </div>
        """

        debug_print("?�메??발송 ?�작...", "send_order_confirmation_email")
        # ?�메??발송
        result = email_service.send_email(
            to_email=user_email,
            subject=f"[BacklinkVending] 주문???�수?�었?�니??- {order_id}",
            html_content=html_content,
        )
        debug_print(f"?�메??발송 결과: {result}", "send_order_confirmation_email")

        debug_print("?�메??로그 ?�???�작...", "send_order_confirmation_email")
        # Supabase REST API�??�메??로그 ?�??
        create_email_log_via_api(
            email_type="order_confirmation",
            recipient_email=user_email,
            subject=f"[BacklinkVending] 주문???�수?�었?�니??- {order_id}",
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
            f"주문 ?�인 ?�메???�스???�료 - ?�공", "send_order_confirmation_email"
        )
        logger.info(f"Order confirmation email sent to {user_email}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": user_email,
        }

    except Exception as e:
        debug_print(
            f"주문 ?�인 ?�메???�스???�패: {e}", "send_order_confirmation_email"
        )
        logger.error(f"Failed to send order confirmation email: {e}")
        return {"success": False, "error": str(e)}


@app.task
def send_backlink_completion_email(
    user_email: str, order_id: str, backlink_result: dict
):
    """
    백링??구축 ?�료 ?�메??발송 (5.4 기능)
    Args:
        user_email: ?�용???�메??주소
        order_id: 주문 ID
        backlink_result: 백링??구축 결과
    """
    try:
        email_service = EmailService()

        # 백링??결과 ?�보 추출
        target_url = safe_str(backlink_result.get("target_url", ""))
        keyword = safe_str(backlink_result.get("keyword", ""))
        pbn_urls = backlink_result.get("pbn_urls", [])
        total_backlinks = len(pbn_urls)

        # PBN URL 리스??HTML ?�성
        pbn_list_html = ""
        for i, pbn_url in enumerate(pbn_urls[:10], 1):  # 최�? 10개까지�??�시
            pbn_list_html += f"<p>?�� {i}. {safe_str(pbn_url)}</p>"

        if total_backlinks > 10:
            pbn_list_html += f"<p>... ??{total_backlinks - 10}�???/p>"

        # HTML 콘텐�?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #059669;">?�� 백링??구축???�료?�었?�니??</h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">주문 ?�보</h3>
                <p><strong>주문 번호:</strong> {order_id}</p>
                <p><strong>?�??URL:</strong> {target_url}</p>
                <p><strong>?�워??</strong> {keyword}</p>
                <p><strong>?�료 ?�시:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #059669; margin-top: 0;">구축 결과</h3>
                <p><strong>�?백링????</strong> {total_backlinks}�?/p>
                <div style="margin-top: 15px;">
                    <h4 style="color: #374151; margin-bottom: 10px;">구축??PBN ?�이??</h4>
                    {pbn_list_html}
                </div>
            </div>
            
            <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #92400e; margin-top: 0;">?�� SEO ?�과 ?�내</h3>
                <p>??백링???�과??보통 2-4�??��????��??�니??/p>
                <p>??지?�적??SEO 최적?��? 권장?�니??/p>
                <p>??추�? 백링?��? ?�요?�시�??�제???�락주세??/p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                감사?�니??<br>
                BacklinkVending ?�
            </p>
        </div>
        """

        # ?�메??발송
        result = email_service.send_email(
            to_email=user_email,
            subject=f"[BacklinkVending] 백링??구축???�료?�었?�니?? - {order_id}",
            html_content=html_content,
        )

        # Supabase REST API�??�메??로그 ?�??
        create_email_log_via_api(
            email_type="backlink_completion",
            recipient_email=user_email,
            subject=f"[BacklinkVending] 백링??구축???�료?�었?�니?? - {order_id}",
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
    관리자 ?�패 ?�림 ?�메??발송 (5.4 기능)
    Args:
        order_id: 주문 ID
        error_details: ?�러 ?�세 ?�보
        admin_email: 관리자 ?�메??주소
    """
    try:
        email_service = EmailService()

        error_type = safe_str(error_details.get("error_type", "Unknown"))
        error_message = safe_str(error_details.get("error_message", ""))
        target_url = safe_str(error_details.get("target_url", ""))
        keyword = safe_str(error_details.get("keyword", ""))

        # HTML 콘텐�?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc2626;">?�� 백링??구축 ?�패 ?�림</h2>
            
            <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
                <h3 style="color: #991b1b; margin-top: 0;">?�패 ?�보</h3>
                <p><strong>주문 번호:</strong> {order_id}</p>
                <p><strong>?�러 ?�??</strong> {error_type}</p>
                <p><strong>?�러 메시지:</strong> {error_message}</p>
                <p><strong>?�??URL:</strong> {target_url}</p>
                <p><strong>?�워??</strong> {keyword}</p>
                <p><strong>발생 ?�간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #92400e; margin-top: 0;">?�� 권장 조치?�항</h3>
                <p>???�러 로그�??�인?�여 ?�인???�악?�세??/p>
                <p>???�요???�동?�로 백링?��? 구축?�세??/p>
                <p>??고객?�게 ?�황???�내?�세??/p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                ?�스???�동 ?�림<br>
                BacklinkVending 관리시?�템
            </p>
        </div>
        """

        # ?�메??발송
        result = email_service.send_email(
            to_email=admin_email,
            subject=f"[BacklinkVending 관리자] 백링??구축 ?�패 - {order_id}",
            html_content=html_content,
        )

        # Supabase REST API�??�메??로그 ?�??
        create_email_log_via_api(
            email_type="admin_alert",
            recipient_email=admin_email,
            subject=f"[BacklinkVending 관리자] 백링??구축 ?�패 - {order_id}",
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
    백링??보고???�메??발송 (5.4 기능)
    Args:
        user_email: ?�용???�메??주소
        backlinks: 백링??목록
    """
    try:
        email_service = EmailService()

        total_backlinks = len(backlinks)

        # 백링??리스??HTML ?�성 (최�? 20개까지�??�시)
        backlink_list_html = ""
        for i, backlink in enumerate(backlinks[:20], 1):
            source_url = safe_str(backlink.get("source_url", ""))
            target_url = safe_str(backlink.get("target_url", ""))
            keyword = safe_str(backlink.get("keyword", ""))

            backlink_list_html += f"""
            <div style="border-bottom: 1px solid #e5e7eb; padding: 10px 0;">
                <p><strong>{i}. {keyword}</strong></p>
                <p style="margin: 5px 0; font-size: 14px; color: #6b7280;">
                    ?�� 출처: {source_url}<br>
                    ?�� ?�?? {target_url}
                </p>
            </div>
            """

        if total_backlinks > 20:
            backlink_list_html += f"<p style='text-align: center; color: #6b7280; margin-top: 15px;'>... ??{total_backlinks - 20}�???/p>"

        # HTML 콘텐�?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">?�� 백링??보고??/h2>
            
            <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">?�� ?�약</h3>
                <p><strong>�?백링????</strong> {total_backlinks}�?/p>
                <p><strong>보고???�성??</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #374151; margin-top: 0;">?�� 백링??목록</h3>
                {backlink_list_html}
            </div>
            
            <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #059669; margin-top: 0;">?�� SEO ??/h3>
                <p>??백링???�질???�보??중요?�니??/p>
                <p>???�양???�메?�에?�의 백링?��? ?�과?�입?�다</p>
                <p>???�기?�인 백링??모니?�링??권장?�니??/p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                감사?�니??<br>
                BacklinkVending ?�
            </p>
        </div>
        """

        # ?�메??발송
        result = email_service.send_email(
            to_email=user_email,
            subject=f"[BacklinkVending] 백링??보고??({total_backlinks}�?",
            html_content=html_content,
        )

        # Supabase REST API�??�메??로그 ?�??
        create_email_log_via_api(
            email_type="backlink_report",
            recipient_email=user_email,
            subject=f"[BacklinkVending] 백링??보고??({total_backlinks}�?",
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
    ?�벤???�림 ?�메??발송 (5.4 기능)
    Args:
        user_email: ?�용???�메??주소
        event_type: ?�벤???�??
        event_data: ?�벤???�이??
    """
    try:
        email_service = EmailService()

        # ?�벤???�?�별 ?�목�??�용 ?�정
        if event_type == "promotion":
            subject = "[BacklinkVending] ?�� ?�별 ?�로모션 ?�내"
            content = "?�로???�로모션???�작?�었?�니??"
        elif event_type == "system_update":
            subject = "[BacklinkVending] ?�� ?�스???�데?�트 ?�내"
            content = "?�스?�이 ?�데?�트?�었?�니??"
        else:
            subject = f"[BacklinkVending] {event_type} ?�림"
            content = "?�로???�림???�습?�다."

        # HTML 콘텐�?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">{content}</h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">?�림 ?�용</h3>
                <p>{safe_str(event_data.get('message', ''))}</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                BacklinkVending ?�
            </p>
        </div>
        """

        # ?�메??발송
        result = email_service.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
        )

        # Supabase REST API�??�메??로그 ?�??
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
    범용 ?�메??발송 ?�스??(5.4 기능)
    Args:
        to_email: ?�신???�메??
        subject: ?�메???�목
        html_content: HTML ?�용
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
    Supabase REST API�??�한 ?�메??로그 ?�??
    Args:
        email_type: ?�메???�??
        recipient_email: ?�신???�메??
        subject: ?�메???�목 (최�? 200??
        message_id: 메시지 ID
        order_id: 주문 ID
        template_type: ?�플�??�??
        extra_data: 추�? ?�이??(JSONB)
        status: ?�태
    """
    try:
        debug_print(
            f"?�메??로그 ?�???�작: {email_type} -> {recipient_email}",
            "create_email_log_via_api",
        )

        # ?�목 길이 ?�한 (200??
        subject_limited = subject[:200] if subject else ""

        log_data = {
            "email_type": email_type,
            "recipient_email": recipient_email,
            "subject": subject_limited,
            "status": status,
            "sent_at": datetime.now().isoformat(),
        }

        # ?�택???�드??
        if message_id:
            log_data["message_id"] = message_id
        if order_id:
            log_data["order_id"] = order_id
        if template_type:
            log_data["template_type"] = template_type
        if extra_data:
            log_data["extra_data"] = extra_data

        debug_print(f"Supabase???�입???�이?? {log_data}", "create_email_log_via_api")

        # Supabase???�입
        result = supabase.table("email_logs").insert(log_data).execute()

        debug_print(f"?�메??로그 ?�???�료: {result.data}", "create_email_log_via_api")
        logger.info(f"Email log saved via API: {email_type} to {recipient_email}")
        return result.data

    except Exception as e:
        debug_print(f"?�메??로그 ?�???�패: {e}", "create_email_log_via_api")
        logger.error(f"Failed to save email log via API: {e}")
        # ?�메??로그 ?�???�패?�도 ?�메??발송?� ?�공?�로 처리
        return None
