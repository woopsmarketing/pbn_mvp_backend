from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.tasks.email_tasks import send_welcome_email

# from app.services.email import EmailService

router = APIRouter()


# 임시 회원가입 스키마 정의
class UserCreateSchema(BaseModel):
    email: EmailStr
    name: str
    password: str


# 임시 유저 DB (메모리)
fake_users_db = {}


def create_user(user_data: UserCreateSchema):
    # 중복 체크 없이 항상 덮어쓰기
    fake_users_db[user_data.email] = {
        "email": user_data.email,
        "name": user_data.name,
        "password": user_data.password,  # 실제 서비스에서는 해싱 필요
    }
    return fake_users_db[user_data.email]


@router.post("/signup")
async def signup(user_data: UserCreateSchema):
    # TODO: 실제 DB에 유저 저장 로직 구현
    # 회원가입 환영 이메일 발송 - 수정된 함수 시그니처에 맞게 수정
    send_welcome_email.delay(user_data.email)  # 🔧 user_email만 전달
    return {"message": "회원가입 성공! 환영 이메일이 발송되었습니다."}


@router.get("/confirm-email")
async def confirm_email(token: str):
    # 실제로는 토큰 검증 로직이 들어가야 함
    return {"message": "이메일 인증 성공!", "token": token}
