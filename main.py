from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from supabase import create_client, Client
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import traceback
import os

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.verify import router as verify_router
from app.api.v1.endpoints.pbn_rest import router as pbn_rest_router
from app.api.monitoring import router as monitoring_router
from app.core.config import settings
import sentry_sdk

sentry_sdk.init(
    dsn="https://0659715a31771946c109265f4d1c3a64@o4507567364636672.ingest.us.sentry.io/4507567368437760",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


app = FastAPI(title=settings.PROJECT_NAME)

# 환경에 따른 CORS 설정
# 프로덕션: 실제 도메인만 허용
# 개발: localhost 허용
allowed_origins = [
    "http://localhost:3000",  # 로컬 개발
    "https://pbn-mvp-frontend.vercel.app",  # Vercel 배포된 프론트엔드 (슬래시 제거)
    "https://pbn-mvp-frontend-gogv.vercel.app",  # 기존 도메인
]

# 추가 도메인이 있다면 환경변수로 추가 가능
additional_origins = os.getenv("ADDITIONAL_CORS_ORIGINS", "").split(",")
if additional_origins and additional_origins[0]:  # 빈 문자열 체크
    allowed_origins.extend(additional_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}


app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(events_router, prefix="/api/v1/events", tags=["events"])
app.include_router(verify_router, prefix="/api/v1", tags=["verify"])
app.include_router(pbn_rest_router, prefix="/api/v1", tags=["pbn"])
app.include_router(monitoring_router, prefix="/api/v1", tags=["monitoring"])

# Add Sentry middleware
app.add_middleware(SentryAsgiMiddleware)

# (Windows 환경 등에서) utf-8 인코딩 강제: 실행 전 'set PYTHONUTF8=1' 또는 'export PYTHONUTF8=1' 적용 권장


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"{type(exc).__name__}: {str(exc)}",
            "traceback": traceback.format_exc(),
        },
    )
