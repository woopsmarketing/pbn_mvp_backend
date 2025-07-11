"""
이메일 로그 모델 - 최적화된 구조
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class EmailLog(Base):
    """
    이메일 발송 로그 테이블 - 간소화된 구조
    """

    __tablename__ = "email_logs"

    # 기본 필드
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 사용자 및 주문 관련
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)

    # 이메일 기본 정보
    email_type = Column(
        String(50),
        nullable=False,
        comment="이메일 유형: order_confirmation, backlink_completion, welcome, admin_alert",
    )
    template_type = Column(
        String(50), nullable=True, comment="템플릿 유형: 더 세분화된 분류"
    )
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(200), nullable=True)

    # 발송 상태 및 결과
    status = Column(
        String(20), default="pending", comment="발송 상태: pending, sent, failed"
    )
    message_id = Column(
        String(255), nullable=True, comment="Resend API에서 반환하는 고유 메시지 ID"
    )
    external_id = Column(String(255), nullable=True, comment="외부 서비스 ID")

    # 에러 및 메타데이터
    error_message = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True, comment="추가 정보 (JSON 형태)")

    # 타임스탬프
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 관계 설정
    user = relationship("User", back_populates="email_logs")

    def __repr__(self):
        return f"<EmailLog(id={self.id}, type={self.email_type}, recipient={self.recipient_email}, status={self.status})>"
