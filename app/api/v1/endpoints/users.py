from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserBase
from app.services.user_service import UserService
from app.core.supabase_jwt import get_current_user
from app.core.clerk_jwt import get_current_clerk_user
from app.db.models.user import User as UserModel
from app.db.base import Base
from app.db import get_db  # get_db: SQLAlchemy 세션 의존성

router = APIRouter()
user_service = UserService()


# 유저 프로필 조회 예시 (실제 서비스에서는 인증 필요)
class UserProfile(BaseModel):
    email: EmailStr
    name: str


@router.get("/profile", response_model=UserProfile)
def get_profile(current_user: dict = Depends(get_current_user)):
    # 인증된 유저 정보 반환
    return UserProfile(
        email=current_user.get("email", "unknown"),
        name=current_user.get("user_metadata", {}).get("nickname", "알수없음"),
    )


@router.get("/me", response_model=UserProfile)
def read_me(current_user: dict = Depends(get_current_user)):
    # Supabase JWT payload에서 정보 추출
    return UserProfile(
        email=current_user.get("email", "unknown"),
        name=current_user.get("user_metadata", {}).get("nickname", "알수없음"),
    )


# 회원가입 엔드포인트
@router.post("/register")
def register(user: UserCreate):
    try:
        result = user_service.register_user(user.email, user.password)
        return {"user": str(result["user"]), "session": str(result["session"])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 로그인 엔드포인트
@router.post("/login")
def login(user: UserCreate):
    try:
        result = user_service.login_user(user.email, user.password)
        return {"user": str(result["user"]), "session": str(result["session"])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Clerk 인증 기반 자동 등록/조회
class ClerkUserProfile(BaseModel):
    email: EmailStr
    name: str
    clerk_id: str


@router.get("/me_clerk", response_model=ClerkUserProfile)
def get_or_create_clerk_user(
    clerk_user=Depends(get_current_clerk_user), db: Session = Depends(get_db)
):
    # Clerk JWT payload에서 sub(고유ID), email, name 추출
    clerk_id = clerk_user.get("sub")
    email = None
    name = None
    # Clerk JWT 구조에 따라 email 추출
    if "email_addresses" in clerk_user and clerk_user["email_addresses"]:
        email = clerk_user["email_addresses"][0].get("email_address")
    elif "email" in clerk_user:
        email = clerk_user["email"]
    name = clerk_user.get("first_name", "") + " " + clerk_user.get("last_name", "")
    if not email:
        raise HTTPException(
            status_code=400, detail="Clerk JWT에 이메일 정보가 없습니다."
        )
    # users 테이블에서 clerk_id로 조회
    db_user = db.query(UserModel).filter_by(clerk_id=clerk_id).first()
    if not db_user:
        db_user = UserModel(
            email=email,
            name=name.strip() or email,
            password_hash=None,
            role="user",
            clerk_id=clerk_id,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return ClerkUserProfile(
        email=db_user.email, name=db_user.name, clerk_id=db_user.clerk_id
    )
