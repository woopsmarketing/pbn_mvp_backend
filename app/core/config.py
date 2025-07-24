from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Resend
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM: Optional[str] = "onboarding@resend.dev"  # 임시: 도메인 인증 완료까지
    EMAIL_FROM_NAME: Optional[str] = "FollowSales 팀"

    # Project
    PROJECT_NAME: str = "API_followsales"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Clerk
    CLERK_JWK_URL: Optional[str] = None
    CLERK_ISSUER: Optional[str] = None
    CLERK_AUDIENCE: Optional[str] = None

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg2://user:password@host:port/dbname"  # 실제 값은 .env에서 관리
    )

    # Supabase
    SUPABASE_PROJECT_ID: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_AUDIENCE: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}

    @property
    def get_email_from(self) -> str:
        """환경에 따른 발신자 이메일 주소 반환"""
        return self.EMAIL_FROM or "noreply@backlinkvending.com"


settings = Settings()
