from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class PBNTask(Base):
    """
    PBN 백링크 작업 모델
    - 개별 백링크 작업의 상태와 정보를 관리
    - 데이터베이스 기본값 활용으로 안정성 향상
    """

    __tablename__ = "pbn_tasks"

    # 데이터베이스에서 gen_random_uuid() 기본값 사용
    id = Column(UUID(as_uuid=True), primary_key=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    pbn_site_id = Column(Integer, ForeignKey("pbn_sites.id"), nullable=True)

    # 백링크 정보
    target_url = Column(String, nullable=False)  # 백링크를 받을 URL
    anchor_text = Column(String, nullable=False)  # 앵커 텍스트
    keywords = Column(ARRAY(String), nullable=True)  # 관련 키워드 배열
    content = Column(Text, nullable=True)  # 포스트 내용 (AI 생성 또는 수동)

    # 작업 상태
    status = Column(String, default="pending")  # 'pending', 'in_progress', 'completed', 'failed'
    post_url = Column(String, nullable=True)  # 완성된 포스트 URL

    # 스케줄링
    scheduled_date = Column(Date, nullable=True)  # 예정된 포스팅 날짜
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 완료 시간

    # 에러 처리
    error_message = Column(Text, nullable=True)  # 실패 시 에러 메시지

    # 타임스탬프 (데이터베이스 기본값 사용)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 관계 설정
    order = relationship("Order", back_populates="pbn_tasks")
    pbn_site = relationship("PBNSite", back_populates="pbn_tasks")

    def __repr__(self):
        return f"<PBNTask(id={self.id}, target_url={self.target_url}, status={self.status})>"

    @property
    def is_ready_to_execute(self):
        """실행 준비가 되었는지 확인"""
        return (
            self.status == "pending"
            and self.pbn_site_id is not None
            and self.target_url
            and self.anchor_text
        )
