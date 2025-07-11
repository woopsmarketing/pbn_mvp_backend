import uuid
from datetime import datetime
from typing import Optional, Any
from decimal import Decimal
from pydantic import BaseModel


# Shared properties
class OrderBase(BaseModel):
    """기본 주문 속성"""

    type: str  # 'free_pbn', 'paid_pbn', 'domain_request', 'site_request'
    status: str = "pending"  # 'pending', 'processing', 'completed', 'cancelled'
    amount: Optional[Decimal] = None
    payment_status: str = "unpaid"


# Properties to receive on order creation
class OrderCreate(OrderBase):
    """주문 생성 요청 스키마"""

    user_id: Optional[uuid.UUID] = None  # 무료 주문시 자동 생성
    metadata: Optional[dict[str, Any]] = None


# Properties to receive on order update
class OrderUpdate(BaseModel):
    """주문 업데이트 요청 스키마"""

    status: Optional[str] = None
    payment_status: Optional[str] = None
    amount: Optional[Decimal] = None
    metadata: Optional[dict[str, Any]] = None


# Properties shared by models stored in DB
class OrderInDBBase(OrderBase):
    """DB 저장용 기본 주문 스키마"""

    id: uuid.UUID
    user_id: uuid.UUID
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Properties to return to client
class Order(OrderInDBBase):
    """클라이언트 반환용 주문 스키마"""

    pass


# Properties stored in DB
class OrderInDB(OrderInDBBase):
    """DB 완전 저장용 주문 스키마"""

    pass


# Special schemas for different order types
class FreePBNOrderCreate(BaseModel):
    """무료 PBN 주문 생성 스키마"""

    url: str
    keyword: str
    email: str

    class Config:
        from_attributes = True


class PaidPBNOrderCreate(BaseModel):
    """유료 PBN 주문 생성 스키마"""

    url: str
    keywords: list[str]
    quantity: int
    payment_data: dict[str, Any]

    class Config:
        from_attributes = True
