import uuid
from datetime import datetime
from typing import Optional, Any
from decimal import Decimal
from pydantic import BaseModel


# Shared properties
class SiteRequestBase(BaseModel):
    """기본 사이트 요청 속성"""

    site_type: str  # 'pbn', 'guest_post', 'niche_edit'
    niche: Optional[str] = None
    da_requirement: Optional[int] = None
    pa_requirement: Optional[int] = None
    target_url: Optional[str] = None
    anchor_text: Optional[str] = None
    content_requirements: Optional[str] = None
    budget_range: Optional[str] = None
    status: str = "pending"


# Properties to receive on request creation
class SiteRequestCreate(SiteRequestBase):
    """사이트 요청 생성 스키마"""

    order_id: uuid.UUID


# Properties to receive on request update
class SiteRequestUpdate(BaseModel):
    """사이트 요청 업데이트 스키마"""

    status: Optional[str] = None
    site_url: Optional[str] = None
    post_url: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    site_metrics: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None


# Properties shared by models stored in DB
class SiteRequestInDBBase(SiteRequestBase):
    """DB 저장용 기본 사이트 요청 스키마"""

    id: uuid.UUID
    order_id: uuid.UUID
    site_url: Optional[str] = None
    post_url: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    site_metrics: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Properties to return to client
class SiteRequest(SiteRequestInDBBase):
    """클라이언트 반환용 사이트 요청 스키마"""

    pass


# Properties stored in DB
class SiteRequestInDB(SiteRequestInDBBase):
    """DB 완전 저장용 사이트 요청 스키마"""

    pass
