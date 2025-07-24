"""
?´ë©”??ë°œì†¡ ?œìŠ¤??ëª¨ë“ˆ - Supabase REST API ë°©ì‹
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from app.tasks.celery_app import celery as app
from app.services.email import EmailService
from app.services.supabase_client import supabase

logger = logging.getLogger(__name__)


# ?”ë²„ê¹…ìš© print ?¨ìˆ˜
def debug_print(message: str, task_name: str = ""):
    """?”ë²„ê¹…ìš© print ?¨ìˆ˜"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [EMAIL_TASK] [{task_name}] {message}")
    logger.info(f"[EMAIL_TASK] [{task_name}] {message}")


def safe_str(value, default="N/A"):
    """
    ?ˆì „??ë¬¸ì??ë³€???¨ìˆ˜
    Args:
        value: ë³€?˜í•  ê°?
        default: ê¸°ë³¸ê°?
    Returns:
        str: ?ˆì „?˜ê²Œ ë³€?˜ëœ ë¬¸ì??
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
    ? ê·œ ?¬ìš©???˜ì˜ ?´ë©”??ë°œì†¡ (5.4 ê¸°ëŠ¥)
    Args:
        user_email: ?¬ìš©???´ë©”??ì£¼ì†Œ
    """
    debug_print(f"=== ?˜ì˜ ?´ë©”???œìŠ¤???œì‘ ===", "send_welcome_email")
    debug_print(f"?˜ì‹ ?? {user_email}", "send_welcome_email")

    try:
        debug_print("EmailService ì´ˆê¸°??ì¤?..", "send_welcome_email")
        email_service = EmailService()

        # HTML ì½˜í…ì¸?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">?‰ BacklinkVending???¤ì‹  ê²ƒì„ ?˜ì˜?©ë‹ˆ??</h2>
            
            <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">?œì‘?˜ê¸°</h3>
                <p>??ë¬´ë£Œ PBN ë°±ë§???œë¹„?¤ë? ?´ìš©?˜ì‹¤ ???ˆìŠµ?ˆë‹¤</p>
                <p>???„ë¬¸?ì¸ SEO ?ë‹´??ë°›ìœ¼?????ˆìŠµ?ˆë‹¤</p>
                <p>???¤ì–‘??ë°±ë§???¨í‚¤ì§€ë¥??•ì¸?˜ì„¸??/p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                ê¶ê¸ˆ???ì´ ?ˆìœ¼?œë©´ ?¸ì œ???°ë½ì£¼ì„¸??<br>
                BacklinkVending ?€
            </p>
        </div>
        """

        debug_print("?´ë©”??ë°œì†¡ ?œì‘...", "send_welcome_email")
        # ?´ë©”??ë°œì†¡
        result = email_service.send_email(
            to_email=user_email,
            subject="[BacklinkVending] ?˜ì˜?©ë‹ˆ?? ?‰",
            html_content=html_content,
        )
        debug_print(f"?´ë©”??ë°œì†¡ ê²°ê³¼: {result}", "send_welcome_email")

        debug_print("?´ë©”??ë¡œê·¸ ?€???œì‘...", "send_welcome_email")
        # Supabase REST APIë¡??´ë©”??ë¡œê·¸ ?€??
        create_email_log_via_api(
            email_type="welcome",
            recipient_email=user_email,
            subject="[BacklinkVending] ?˜ì˜?©ë‹ˆ?? ?‰",
            message_id=result.get("message_id"),
            template_type="user_welcome",
            extra_data={"signup_source": "pbn_rest_api"},
            status="sent" if result.get("success") else "failed",
        )

        debug_print(f"?˜ì˜ ?´ë©”???œìŠ¤???„ë£Œ - ?±ê³µ", "send_welcome_email")
        logger.info(f"Welcome email sent to {user_email}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": user_email,
        }

    except Exception as e:
        debug_print(f"?˜ì˜ ?´ë©”???œìŠ¤???¤íŒ¨: {e}", "send_welcome_email")
        logger.error(f"Failed to send welcome email: {e}")
        return {"success": False, "error": str(e)}


@app.task
def send_order_confirmation_email(user_email: str, order_id: str, order_details: dict):
    """
    ì£¼ë¬¸ ?•ì¸ ?´ë©”??ë°œì†¡ (5.4 ê¸°ëŠ¥)
    Args:
        user_email: ?¬ìš©???´ë©”??ì£¼ì†Œ
        order_id: ì£¼ë¬¸ ID
        order_details: ì£¼ë¬¸ ?ì„¸ ?•ë³´
    """
    debug_print(
        f"=== ì£¼ë¬¸ ?•ì¸ ?´ë©”???œìŠ¤???œì‘ ===", "send_order_confirmation_email"
    )
    debug_print(
        f"?˜ì‹ ?? {user_email}, ì£¼ë¬¸ID: {order_id}", "send_order_confirmation_email"
    )
    debug_print(f"ì£¼ë¬¸ ?ì„¸: {order_details}", "send_order_confirmation_email")

    try:
        debug_print("EmailService ì´ˆê¸°??ì¤?..", "send_order_confirmation_email")
        email_service = EmailService()

        target_url = safe_str(order_details.get("target_url", ""))
        keyword = safe_str(order_details.get("keyword", ""))

        debug_print(
            f"ì²˜ë¦¬??URL: {target_url}, ?¤ì›Œ?? {keyword}",
            "send_order_confirmation_email",
        )

        # HTML ì½˜í…ì¸?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">?‰ ì£¼ë¬¸???±ê³µ?ìœ¼ë¡??‘ìˆ˜?˜ì—ˆ?µë‹ˆ??</h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">ì£¼ë¬¸ ?•ë³´</h3>
                <p><strong>ì£¼ë¬¸ ë²ˆí˜¸:</strong> {order_id}</p>
                <p><strong>?€??URL:</strong> {target_url}</p>
                <p><strong>?¤ì›Œ??</strong> {keyword}</p>
                <p><strong>ì£¼ë¬¸ ?¼ì‹œ:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #059669; margin-top: 0;">?¤ìŒ ?¨ê³„</h3>
                <p>??ì£¼ë¬¸???‘ìˆ˜?˜ì—ˆ?µë‹ˆ??/p>
                <p>?”„ ë°±ë§??êµ¬ì¶• ?‘ì—…???œì‘?©ë‹ˆ??/p>
                <p>?“§ ?„ë£Œ ??ê²°ê³¼ë¥??´ë©”?¼ë¡œ ?Œë ¤?œë¦½?ˆë‹¤</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                ê°ì‚¬?©ë‹ˆ??<br>
                BacklinkVending ?€
            </p>
        </div>
        """

        debug_print("?´ë©”??ë°œì†¡ ?œì‘...", "send_order_confirmation_email")
        # ?´ë©”??ë°œì†¡
        result = email_service.send_email(
            to_email=user_email,
            subject=f"[BacklinkVending] ì£¼ë¬¸???‘ìˆ˜?˜ì—ˆ?µë‹ˆ??- {order_id}",
            html_content=html_content,
        )
        debug_print(f"?´ë©”??ë°œì†¡ ê²°ê³¼: {result}", "send_order_confirmation_email")

        debug_print("?´ë©”??ë¡œê·¸ ?€???œì‘...", "send_order_confirmation_email")
        # Supabase REST APIë¡??´ë©”??ë¡œê·¸ ?€??
        create_email_log_via_api(
            email_type="order_confirmation",
            recipient_email=user_email,
            subject=f"[BacklinkVending] ì£¼ë¬¸???‘ìˆ˜?˜ì—ˆ?µë‹ˆ??- {order_id}",
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
            f"ì£¼ë¬¸ ?•ì¸ ?´ë©”???œìŠ¤???„ë£Œ - ?±ê³µ", "send_order_confirmation_email"
        )
        logger.info(f"Order confirmation email sent to {user_email}")
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "recipient": user_email,
        }

    except Exception as e:
        debug_print(
            f"ì£¼ë¬¸ ?•ì¸ ?´ë©”???œìŠ¤???¤íŒ¨: {e}", "send_order_confirmation_email"
        )
        logger.error(f"Failed to send order confirmation email: {e}")
        return {"success": False, "error": str(e)}


@app.task
def send_backlink_completion_email(
    user_email: str, order_id: str, backlink_result: dict
):
    """
    ë°±ë§??êµ¬ì¶• ?„ë£Œ ?´ë©”??ë°œì†¡ (5.4 ê¸°ëŠ¥)
    Args:
        user_email: ?¬ìš©???´ë©”??ì£¼ì†Œ
        order_id: ì£¼ë¬¸ ID
        backlink_result: ë°±ë§??êµ¬ì¶• ê²°ê³¼
    """
    try:
        email_service = EmailService()

        # ë°±ë§??ê²°ê³¼ ?•ë³´ ì¶”ì¶œ
        target_url = safe_str(backlink_result.get("target_url", ""))
        keyword = safe_str(backlink_result.get("keyword", ""))
        pbn_urls = backlink_result.get("pbn_urls", [])
        total_backlinks = len(pbn_urls)

        # PBN URL ë¦¬ìŠ¤??HTML ?ì„±
        pbn_list_html = ""
        for i, pbn_url in enumerate(pbn_urls[:10], 1):  # ìµœë? 10ê°œê¹Œì§€ë§??œì‹œ
            pbn_list_html += f"<p>?”— {i}. {safe_str(pbn_url)}</p>"

        if total_backlinks > 10:
            pbn_list_html += f"<p>... ??{total_backlinks - 10}ê°???/p>"

        # HTML ì½˜í…ì¸?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #059669;">?‰ ë°±ë§??êµ¬ì¶•???„ë£Œ?˜ì—ˆ?µë‹ˆ??</h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">ì£¼ë¬¸ ?•ë³´</h3>
                <p><strong>ì£¼ë¬¸ ë²ˆí˜¸:</strong> {order_id}</p>
                <p><strong>?€??URL:</strong> {target_url}</p>
                <p><strong>?¤ì›Œ??</strong> {keyword}</p>
                <p><strong>?„ë£Œ ?¼ì‹œ:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #059669; margin-top: 0;">êµ¬ì¶• ê²°ê³¼</h3>
                <p><strong>ì´?ë°±ë§????</strong> {total_backlinks}ê°?/p>
                <div style="margin-top: 15px;">
                    <h4 style="color: #374151; margin-bottom: 10px;">êµ¬ì¶•??PBN ?¬ì´??</h4>
                    {pbn_list_html}
                </div>
            </div>
            
            <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #92400e; margin-top: 0;">?“ˆ SEO ?¨ê³¼ ?ˆë‚´</h3>
                <p>??ë°±ë§???¨ê³¼??ë³´í†µ 2-4ì£??„ë????˜í??©ë‹ˆ??/p>
                <p>??ì§€?ì ??SEO ìµœì ?”ë? ê¶Œì¥?©ë‹ˆ??/p>
                <p>??ì¶”ê? ë°±ë§?¬ê? ?„ìš”?˜ì‹œë©??¸ì œ???°ë½ì£¼ì„¸??/p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                ê°ì‚¬?©ë‹ˆ??<br>
                BacklinkVending ?€
            </p>
        </div>
        """

        # ?´ë©”??ë°œì†¡
        result = email_service.send_email(
            to_email=user_email,
            subject=f"[BacklinkVending] ë°±ë§??êµ¬ì¶•???„ë£Œ?˜ì—ˆ?µë‹ˆ?? - {order_id}",
            html_content=html_content,
        )

        # Supabase REST APIë¡??´ë©”??ë¡œê·¸ ?€??
        create_email_log_via_api(
            email_type="backlink_completion",
            recipient_email=user_email,
            subject=f"[BacklinkVending] ë°±ë§??êµ¬ì¶•???„ë£Œ?˜ì—ˆ?µë‹ˆ?? - {order_id}",
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
    ê´€ë¦¬ì ?¤íŒ¨ ?Œë¦¼ ?´ë©”??ë°œì†¡ (5.4 ê¸°ëŠ¥)
    Args:
        order_id: ì£¼ë¬¸ ID
        error_details: ?ëŸ¬ ?ì„¸ ?•ë³´
        admin_email: ê´€ë¦¬ì ?´ë©”??ì£¼ì†Œ
    """
    try:
        email_service = EmailService()

        error_type = safe_str(error_details.get("error_type", "Unknown"))
        error_message = safe_str(error_details.get("error_message", ""))
        target_url = safe_str(error_details.get("target_url", ""))
        keyword = safe_str(error_details.get("keyword", ""))

        # HTML ì½˜í…ì¸?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc2626;">?š¨ ë°±ë§??êµ¬ì¶• ?¤íŒ¨ ?Œë¦¼</h2>
            
            <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
                <h3 style="color: #991b1b; margin-top: 0;">?¤íŒ¨ ?•ë³´</h3>
                <p><strong>ì£¼ë¬¸ ë²ˆí˜¸:</strong> {order_id}</p>
                <p><strong>?ëŸ¬ ?€??</strong> {error_type}</p>
                <p><strong>?ëŸ¬ ë©”ì‹œì§€:</strong> {error_message}</p>
                <p><strong>?€??URL:</strong> {target_url}</p>
                <p><strong>?¤ì›Œ??</strong> {keyword}</p>
                <p><strong>ë°œìƒ ?œê°„:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #92400e; margin-top: 0;">?”§ ê¶Œì¥ ì¡°ì¹˜?¬í•­</h3>
                <p>???ëŸ¬ ë¡œê·¸ë¥??•ì¸?˜ì—¬ ?ì¸???Œì•…?˜ì„¸??/p>
                <p>???„ìš”???˜ë™?¼ë¡œ ë°±ë§?¬ë? êµ¬ì¶•?˜ì„¸??/p>
                <p>??ê³ ê°?ê²Œ ?í™©???ˆë‚´?˜ì„¸??/p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                ?œìŠ¤???ë™ ?Œë¦¼<br>
                BacklinkVending ê´€ë¦¬ì‹œ?¤í…œ
            </p>
        </div>
        """

        # ?´ë©”??ë°œì†¡
        result = email_service.send_email(
            to_email=admin_email,
            subject=f"[BacklinkVending ê´€ë¦¬ì] ë°±ë§??êµ¬ì¶• ?¤íŒ¨ - {order_id}",
            html_content=html_content,
        )

        # Supabase REST APIë¡??´ë©”??ë¡œê·¸ ?€??
        create_email_log_via_api(
            email_type="admin_alert",
            recipient_email=admin_email,
            subject=f"[BacklinkVending ê´€ë¦¬ì] ë°±ë§??êµ¬ì¶• ?¤íŒ¨ - {order_id}",
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
    ë°±ë§??ë³´ê³ ???´ë©”??ë°œì†¡ (5.4 ê¸°ëŠ¥)
    Args:
        user_email: ?¬ìš©???´ë©”??ì£¼ì†Œ
        backlinks: ë°±ë§??ëª©ë¡
    """
    try:
        email_service = EmailService()

        total_backlinks = len(backlinks)

        # ë°±ë§??ë¦¬ìŠ¤??HTML ?ì„± (ìµœë? 20ê°œê¹Œì§€ë§??œì‹œ)
        backlink_list_html = ""
        for i, backlink in enumerate(backlinks[:20], 1):
            source_url = safe_str(backlink.get("source_url", ""))
            target_url = safe_str(backlink.get("target_url", ""))
            keyword = safe_str(backlink.get("keyword", ""))

            backlink_list_html += f"""
            <div style="border-bottom: 1px solid #e5e7eb; padding: 10px 0;">
                <p><strong>{i}. {keyword}</strong></p>
                <p style="margin: 5px 0; font-size: 14px; color: #6b7280;">
                    ?“ ì¶œì²˜: {source_url}<br>
                    ?¯ ?€?? {target_url}
                </p>
            </div>
            """

        if total_backlinks > 20:
            backlink_list_html += f"<p style='text-align: center; color: #6b7280; margin-top: 15px;'>... ??{total_backlinks - 20}ê°???/p>"

        # HTML ì½˜í…ì¸?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">?“Š ë°±ë§??ë³´ê³ ??/h2>
            
            <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">?“ˆ ?”ì•½</h3>
                <p><strong>ì´?ë°±ë§????</strong> {total_backlinks}ê°?/p>
                <p><strong>ë³´ê³ ???ì„±??</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #374151; margin-top: 0;">?”— ë°±ë§??ëª©ë¡</h3>
                {backlink_list_html}
            </div>
            
            <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #059669; margin-top: 0;">?’¡ SEO ??/h3>
                <p>??ë°±ë§???ˆì§ˆ???‘ë³´??ì¤‘ìš”?©ë‹ˆ??/p>
                <p>???¤ì–‘???„ë©”?¸ì—?œì˜ ë°±ë§?¬ê? ?¨ê³¼?ì…?ˆë‹¤</p>
                <p>???•ê¸°?ì¸ ë°±ë§??ëª¨ë‹ˆ?°ë§??ê¶Œì¥?©ë‹ˆ??/p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                ê°ì‚¬?©ë‹ˆ??<br>
                BacklinkVending ?€
            </p>
        </div>
        """

        # ?´ë©”??ë°œì†¡
        result = email_service.send_email(
            to_email=user_email,
            subject=f"[BacklinkVending] ë°±ë§??ë³´ê³ ??({total_backlinks}ê°?",
            html_content=html_content,
        )

        # Supabase REST APIë¡??´ë©”??ë¡œê·¸ ?€??
        create_email_log_via_api(
            email_type="backlink_report",
            recipient_email=user_email,
            subject=f"[BacklinkVending] ë°±ë§??ë³´ê³ ??({total_backlinks}ê°?",
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
    ?´ë²¤???Œë¦¼ ?´ë©”??ë°œì†¡ (5.4 ê¸°ëŠ¥)
    Args:
        user_email: ?¬ìš©???´ë©”??ì£¼ì†Œ
        event_type: ?´ë²¤???€??
        event_data: ?´ë²¤???°ì´??
    """
    try:
        email_service = EmailService()

        # ?´ë²¤???€?…ë³„ ?œëª©ê³??´ìš© ?¤ì •
        if event_type == "promotion":
            subject = "[BacklinkVending] ? ?¹ë³„ ?„ë¡œëª¨ì…˜ ?ˆë‚´"
            content = "?ˆë¡œ???„ë¡œëª¨ì…˜???œì‘?˜ì—ˆ?µë‹ˆ??"
        elif event_type == "system_update":
            subject = "[BacklinkVending] ?”§ ?œìŠ¤???…ë°?´íŠ¸ ?ˆë‚´"
            content = "?œìŠ¤?œì´ ?…ë°?´íŠ¸?˜ì—ˆ?µë‹ˆ??"
        else:
            subject = f"[BacklinkVending] {event_type} ?Œë¦¼"
            content = "?ˆë¡œ???Œë¦¼???ˆìŠµ?ˆë‹¤."

        # HTML ì½˜í…ì¸?
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">{content}</h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin-top: 0;">?Œë¦¼ ?´ìš©</h3>
                <p>{safe_str(event_data.get('message', ''))}</p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                BacklinkVending ?€
            </p>
        </div>
        """

        # ?´ë©”??ë°œì†¡
        result = email_service.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
        )

        # Supabase REST APIë¡??´ë©”??ë¡œê·¸ ?€??
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
    ë²”ìš© ?´ë©”??ë°œì†¡ ?œìŠ¤??(5.4 ê¸°ëŠ¥)
    Args:
        to_email: ?˜ì‹ ???´ë©”??
        subject: ?´ë©”???œëª©
        html_content: HTML ?´ìš©
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
    Supabase REST APIë¥??µí•œ ?´ë©”??ë¡œê·¸ ?€??
    Args:
        email_type: ?´ë©”???€??
        recipient_email: ?˜ì‹ ???´ë©”??
        subject: ?´ë©”???œëª© (ìµœë? 200??
        message_id: ë©”ì‹œì§€ ID
        order_id: ì£¼ë¬¸ ID
        template_type: ?œí”Œë¦??€??
        extra_data: ì¶”ê? ?°ì´??(JSONB)
        status: ?íƒœ
    """
    try:
        debug_print(
            f"?´ë©”??ë¡œê·¸ ?€???œì‘: {email_type} -> {recipient_email}",
            "create_email_log_via_api",
        )

        # ?œëª© ê¸¸ì´ ?œí•œ (200??
        subject_limited = subject[:200] if subject else ""

        log_data = {
            "email_type": email_type,
            "recipient_email": recipient_email,
            "subject": subject_limited,
            "status": status,
            "sent_at": datetime.now().isoformat(),
        }

        # ? íƒ???„ë“œ??
        if message_id:
            log_data["message_id"] = message_id
        if order_id:
            log_data["order_id"] = order_id
        if template_type:
            log_data["template_type"] = template_type
        if extra_data:
            log_data["extra_data"] = extra_data

        debug_print(f"Supabase???½ì…???°ì´?? {log_data}", "create_email_log_via_api")

        # Supabase???½ì…
        result = supabase.table("email_logs").insert(log_data).execute()

        debug_print(f"?´ë©”??ë¡œê·¸ ?€???„ë£Œ: {result.data}", "create_email_log_via_api")
        logger.info(f"Email log saved via API: {email_type} to {recipient_email}")
        return result.data

    except Exception as e:
        debug_print(f"?´ë©”??ë¡œê·¸ ?€???¤íŒ¨: {e}", "create_email_log_via_api")
        logger.error(f"Failed to save email log via API: {e}")
        # ?´ë©”??ë¡œê·¸ ?€???¤íŒ¨?´ë„ ?´ë©”??ë°œì†¡?€ ?±ê³µ?¼ë¡œ ì²˜ë¦¬
        return None
