from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    """
    사용자 모델 - Clerk 인증과 연동
    - Supabase Auth와 독립적인 사용자 관리
    - 모든 필드는 데이터베이스 기본값 활용
    """

    __tablename__ = "users"

    # 데이터베이스에서 gen_random_uuid() 기본값 사용
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    clerk_id = Column(String, unique=True, nullable=True, index=True)
    role = Column(Text, default="user")  # 'user', 'admin'

    # 모든 시간 필드는 데이터베이스 기본값(now()) 사용
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    signup_date = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, clerk_id={self.clerk_id})>"
