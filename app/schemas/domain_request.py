import uuid
from datetime import datetime
from typing import Optional, Any
from decimal import Decimal
from pydantic import BaseModel


# Shared properties
class DomainRequestBase(BaseModel):
    """기본 도메인 요청 속성"""
    domain_name: str
    niche: Optional[str] = None
    da_requirement: Optional[int] = None
    pa_requirement: Optional[int] = None
    budget_range: Optional[str] = None
    special_requirements: Optional[str] = None
    status: str = "pending"


# Properties to receive on request creation
class DomainRequestCreate(DomainRequestBase):
    """도메인 요청 생성 스키마"""
    order_id: uuid.UUID


# Properties to receive on request update
class DomainRequestUpdate(BaseModel):
    """도메인 요청 업데이트 스키마"""
    status: Optional[str] = None
    purchased_domain: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    domain_metrics: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None


# Properties shared by models stored in DB
class DomainRequestInDBBase(DomainRequestBase):
    """DB 저장용 기본 도메인 요청 스키마"""
    id: uuid.UUID
    order_id: uuid.UUID
    purchased_domain: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    domain_metrics: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Properties to return to client
class DomainRequest(DomainRequestInDBBase):
    """클라이언트 반환용 도메인 요청 스키마"""
    pass


# Properties stored in DB
class DomainRequestInDB(DomainRequestInDBBase):
    """DB 완전 저장용 도메인 요청 스키마"""
    pass
