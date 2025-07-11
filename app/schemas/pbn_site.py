from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# Shared properties
class PBNSiteBase(BaseModel):
    """기본 PBN 사이트 속성"""

    domain: str
    wp_admin_url: str
    wp_admin_id: str
    da_score: Optional[int] = None
    pa_score: Optional[int] = None
    tf_score: Optional[int] = None
    cf_score: Optional[int] = None
    dr_score: Optional[int] = None
    monthly_visitors: Optional[int] = None
    niche: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    status: str = "active"


# Properties to receive on site creation
class PBNSiteCreate(PBNSiteBase):
    """PBN 사이트 생성 스키마"""

    wp_admin_pw: str
    wp_app_key: Optional[str] = None


# Properties to receive on site update
class PBNSiteUpdate(BaseModel):
    """PBN 사이트 업데이트 스키마"""

    wp_admin_pw: Optional[str] = None
    wp_app_key: Optional[str] = None
    da_score: Optional[int] = None
    pa_score: Optional[int] = None
    tf_score: Optional[int] = None
    cf_score: Optional[int] = None
    dr_score: Optional[int] = None
    monthly_visitors: Optional[int] = None
    niche: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    status: Optional[str] = None
    last_used: Optional[datetime] = None
    notes: Optional[str] = None


# Properties shared by models stored in DB
class PBNSiteInDBBase(PBNSiteBase):
    """DB 저장용 기본 PBN 사이트 스키마"""

    id: int
    last_used: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Properties to return to client (비밀번호 제외)
class PBNSite(PBNSiteInDBBase):
    """클라이언트 반환용 PBN 사이트 스키마 (비밀번호 제외)"""

    pass


# Properties stored in DB (비밀번호 포함)
class PBNSiteInDB(PBNSiteInDBBase):
    """DB 완전 저장용 PBN 사이트 스키마 (비밀번호 포함)"""

    wp_admin_pw: str
    wp_app_key: Optional[str] = None


# PBN 사이트 선택용 스키마 (통계만)
class PBNSiteBasic(BaseModel):
    """PBN 사이트 기본 정보 (선택용)"""

    id: int
    domain: str
    da_score: Optional[int] = None
    pa_score: Optional[int] = None
    niche: Optional[str] = None
    status: str

    class Config:
        from_attributes = True
