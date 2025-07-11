from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class Order(Base):
    """주문 모델 - 모든 종류의 주문을 통합 관리"""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(
        String, nullable=False
    )  # 'free_pbn', 'paid_pbn', 'domain_request', 'site_request'
    status = Column(
        String, default="pending"
    )  # 'pending', 'processing', 'completed', 'cancelled'
    amount = Column(Numeric(10, 2), nullable=True)  # 결제 금액
    payment_status = Column(String, default="unpaid")  # 'unpaid', 'paid', 'refunded'
    order_metadata = Column(JSONB, nullable=True)  # 추가 주문 정보 (JSON 형태)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 관계 설정
    user = relationship("User", back_populates="orders")
    pbn_tasks = relationship(
        "PBNTask", back_populates="order", cascade="all, delete-orphan"
    )
    domain_requests = relationship(
        "DomainRequest", back_populates="order", cascade="all, delete-orphan"
    )
    site_requests = relationship(
        "SiteRequest", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, type={self.type}, status={self.status})>"
