import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


# Shared properties
class PBNTaskBase(BaseModel):
    """기본 PBN 작업 속성"""

    target_url: str
    anchor_text: str
    keywords: Optional[list[str]] = None
    status: str = "pending"


# Properties to receive on task creation
class PBNTaskCreate(PBNTaskBase):
    """PBN 작업 생성 요청 스키마"""

    order_id: uuid.UUID
    pbn_site_id: Optional[int] = None
    content: Optional[str] = None
    scheduled_date: Optional[date] = None


# Properties to receive on task update
class PBNTaskUpdate(BaseModel):
    """PBN 작업 업데이트 요청 스키마"""

    status: Optional[str] = None
    pbn_site_id: Optional[int] = None
    content: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    post_url: Optional[str] = None
    error_message: Optional[str] = None


# Properties shared by models stored in DB
class PBNTaskInDBBase(PBNTaskBase):
    """DB 저장용 기본 PBN 작업 스키마"""

    id: uuid.UUID
    order_id: uuid.UUID
    pbn_site_id: Optional[int] = None
    content: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    post_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Properties to return to client
class PBNTask(PBNTaskInDBBase):
    """클라이언트 반환용 PBN 작업 스키마"""

    pass


# Properties stored in DB
class PBNTaskInDB(PBNTaskInDBBase):
    """DB 완전 저장용 PBN 작업 스키마"""

    pass
