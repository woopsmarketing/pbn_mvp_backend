import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# Shared properties
class EmailLogBase(BaseModel):
    """기본 이메일 로그 속성"""

    email_type: str  # 'welcome', 'order_confirmation', 'task_completed', 'notification'
    recipient_email: EmailStr
    subject: Optional[str] = None
    body: Optional[str] = None
    status: str = "pending"


# Properties to receive on log creation
class EmailLogCreate(EmailLogBase):
    """이메일 로그 생성 스키마"""

    user_id: Optional[uuid.UUID] = None


# Properties to receive on log update
class EmailLogUpdate(BaseModel):
    """이메일 로그 업데이트 스키마"""

    status: Optional[str] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None


# Properties shared by models stored in DB
class EmailLogInDBBase(EmailLogBase):
    """DB 저장용 기본 이메일 로그 스키마"""

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Properties to return to client
class EmailLog(EmailLogInDBBase):
    """클라이언트 반환용 이메일 로그 스키마"""

    pass


# Properties stored in DB
class EmailLogInDB(EmailLogInDBBase):
    """DB 완전 저장용 이메일 로그 스키마"""

    pass
