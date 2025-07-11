from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class DomainRequest(Base):
    """도메인 구매 요청 모델"""

    __tablename__ = "domain_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)

    # 도메인 요구사항
    domain_name = Column(String, nullable=False)  # 원하는 도메인명 (또는 키워드)
    niche = Column(String, nullable=True)  # 니치/카테고리
    da_requirement = Column(Integer, nullable=True)  # 최소 DA 요구사항
    pa_requirement = Column(Integer, nullable=True)  # 최소 PA 요구사항
    budget = Column(Numeric(10, 2), nullable=True)  # 예산
    requirements = Column(Text, nullable=True)  # 추가 요구사항

    # 상태 및 결과
    status = Column(
        String, default="pending"
    )  # 'pending', 'searching', 'found', 'purchased', 'rejected'
    found_domains = Column(JSONB, nullable=True)  # 찾은 도메인 목록 (JSON)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 관계 설정
    order = relationship("Order", back_populates="domain_requests")

    def __repr__(self):
        return f"<DomainRequest(id={self.id}, domain_name={self.domain_name}, status={self.status})>"
