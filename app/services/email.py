import resend
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        """
        EmailService 초기화
        """
        self.resend_api_key = settings.RESEND_API_KEY
        if not self.resend_api_key:
            logger.warning("RESEND_API_KEY가 설정되지 않았습니다.")

    def send_email(
        self, to_email: str, subject: str, html_content: str, text_content: str = None
    ):
        """
        기본 이메일 발송 메소드
        """
        try:
            if not self.resend_api_key:
                logger.error("RESEND_API_KEY가 설정되지 않았습니다.")
                return {"success": False, "error": "API key not configured"}

            resend.api_key = self.resend_api_key

            params = {
                "from": settings.EMAIL_FROM,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }

            if text_content:
                params["text"] = text_content

            result = resend.Emails.send(params)
            logger.info(f"Email sent successfully to {to_email}")

            return {
                "success": True,
                "message_id": result.get("id"),
                "recipient": to_email,
            }

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return {"success": False, "error": str(e), "recipient": to_email}

    @staticmethod
    def send_welcome_email(user_email: str, user_name: str = None):
        """
        환영 이메일을 발송합니다.
        """
        try:
            resend.api_key = settings.RESEND_API_KEY
            if not resend.api_key:
                raise ValueError("RESEND_API_KEY가 설정되지 않았습니다.")

            subject = "FollowSales에 오신 것을 환영합니다! 🎉"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #007bff;">FollowSales에 오신 것을 환영합니다! 🎉</h1>
                <p>안녕하세요, {user_name or user_email}님!</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>🎯 무료 서비스 이용하기</h3>
                    <ul>
                        <li>무료 PBN 백링크 구축</li>
                        <li>무료 SEO 진단</li>
                        <li>전문 SEO 상담</li>
                    </ul>
                </div>
                
                <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>💼 프리미엄 서비스</h3>
                    <ul>
                        <li>고품질 PBN 백링크 패키지</li>
                        <li>도메인 구매 및 웹사이트 제작</li>
                        <li>맞춤형 SEO 전략 수립</li>
                    </ul>
                </div>
                
                <p>궁금한 점이 있으시면 언제든 연락주세요!</p>
                <p>감사합니다!</p>
                
                <hr style="margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    FollowSales 팀<br>
                    이 이메일은 자동으로 발송된 메시지입니다.
                </p>
            </body>
            </html>
            """

            # 환경별 발신자 이메일 설정
            from_email = settings.get_email_from
            from_name = settings.EMAIL_FROM_NAME
            from_address = f"{from_name} <{from_email}>" if from_name else from_email

            params = {
                "from": from_address,
                "to": [user_email],
                "subject": subject,
                "html": html_content,
            }

            result = resend.Emails.send(params)
            logger.info(f"Welcome email sent to {user_email}")

            return {
                "success": True,
                "message_id": result.get("id"),
                "recipient": user_email,
            }

        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def send_seo_diagnosis(user_email: str, diagnosis_data: dict):
        """
        SEO 진단 결과 이메일을 발송합니다.
        """
        try:
            resend.api_key = settings.RESEND_API_KEY
            if not resend.api_key:
                raise ValueError("RESEND_API_KEY가 설정되지 않았습니다.")

            subject = "🔍 SEO 진단 결과가 도착했습니다!"
            website_url = diagnosis_data.get("website_url", "")
            score = diagnosis_data.get("score", "N/A")
            issues = diagnosis_data.get("issues", [])
            recommendations = diagnosis_data.get("recommendations", [])

            issues_html = ""
            for issue in issues[:5]:  # 최대 5개까지
                issues_html += f"<li>{issue}</li>"

            recommendations_html = ""
            for rec in recommendations[:5]:  # 최대 5개까지
                recommendations_html += f"<li>{rec}</li>"

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #007bff;">🔍 SEO 진단 결과</h1>
                <p>안녕하세요!</p>
                <p>요청하신 SEO 진단이 완료되었습니다.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>📊 진단 결과</h3>
                    <ul>
                        <li><strong>웹사이트:</strong> {website_url}</li>
                        <li><strong>SEO 점수:</strong> {score}</li>
                    </ul>
                </div>
                
                {f'<div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;"><h3>⚠️ 개선이 필요한 부분</h3><ul>{issues_html}</ul></div>' if issues else ''}
                
                {f'<div style="background: #d1edff; padding: 15px; border-radius: 5px; margin: 20px 0;"><h3>💡 개선 권장사항</h3><ul>{recommendations_html}</ul></div>' if recommendations else ''}
                
                <p>더 자세한 SEO 개선을 원하시면 언제든 연락주세요!</p>
                
                <hr style="margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    FollowSales 팀<br>
                    이 이메일은 자동으로 발송된 메시지입니다.
                </p>
            </body>
            </html>
            """

            # 환경별 발신자 이메일 설정
            from_email = settings.get_email_from
            from_name = settings.EMAIL_FROM_NAME
            from_address = f"{from_name} <{from_email}>" if from_name else from_email

            params = {
                "from": from_address,
                "to": [user_email],
                "subject": subject,
                "html": html_content,
            }

            result = resend.Emails.send(params)
            logger.info(f"SEO diagnosis email sent to {user_email}")

            return {
                "success": True,
                "message_id": result.get("id"),
                "recipient": user_email,
            }

        except Exception as e:
            logger.error(f"Failed to send SEO diagnosis email: {str(e)}")
            return {"success": False, "error": str(e)}


def send_report_email(user_email: str, order_id: str):
    """
    보고서 이메일 발송 (레거시 함수 - 호환성 유지)
    """
    try:
        logger.info(f"Report email request for order {order_id} to {user_email}")
        return {"success": True, "message": "Report email functionality deprecated"}
    except Exception as e:
        logger.error(f"Report email error: {str(e)}")
        return {"success": False, "error": str(e)}
