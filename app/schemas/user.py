import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    """기본 사용자 속성"""

    email: EmailStr
    role: str = "user"


# Properties to receive on user creation
class UserCreate(UserBase):
    """사용자 생성 요청 스키마"""

    password: Optional[str] = None  # Clerk 사용시 불필요
    clerk_id: Optional[str] = None


# Properties to receive on user update
class UserUpdate(BaseModel):
    """사용자 업데이트 요청 스키마"""

    email: Optional[EmailStr] = None
    role: Optional[str] = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    """DB 저장용 기본 사용자 스키마"""

    id: uuid.UUID
    clerk_id: Optional[str] = None
    signup_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Properties to return to client
class User(UserInDBBase):
    """클라이언트 반환용 사용자 스키마"""

    pass


# Properties stored in DB
class UserInDB(UserInDBBase):
    """DB 완전 저장용 사용자 스키마 (비밀번호 포함)"""

    password_hash: Optional[str] = None


# Clerk integration schema
class ClerkUserCreate(BaseModel):
    """Clerk 사용자 생성 스키마"""

    clerk_id: str
    email: EmailStr
    role: str = "user"

    class Config:
        from_attributes = True
