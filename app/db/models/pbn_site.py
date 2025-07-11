from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class PBNSite(Base):
    """
    PBN 사이트 모델
    - PBN 사이트의 정보와 상태를 관리
    - pbn_sites.csv 파일의 데이터를 저장
    """

    __tablename__ = "pbn_sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String, nullable=False, index=True)
    niche = Column(String, nullable=True)
    da = Column(Integer, nullable=True)  # Domain Authority
    pa = Column(Integer, nullable=True)  # Page Authority
    tf = Column(Integer, nullable=True)  # Trust Flow
    cf = Column(Integer, nullable=True)  # Citation Flow
    status = Column(String, default="active")  # 'active', 'inactive', 'maintenance'

    # 로그인 정보
    login_url = Column(String, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)

    # 메타데이터
    notes = Column(Text, nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 관계 설정
    pbn_tasks = relationship("PBNTask", back_populates="pbn_site")

    def __repr__(self):
        return f"<PBNSite(id={self.id}, domain={self.domain}, status={self.status})>"

    @property
    def is_ready_for_posting(self):
        """포스팅 가능 상태인지 확인"""
        return self.status == "active"
