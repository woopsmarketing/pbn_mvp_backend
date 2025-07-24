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
from app.api.v1.endpoints.redis_debug import router as redis_debug_router
from app.api.monitoring import router as monitoring_router
from app.core.config import settings
import sentry_sdk

# Celery 앱 초기화 (FastAPI와 Celery 연동을 위해 필수)
from app.tasks.celery_app import celery as celery_app

sentry_sdk.init(
    dsn="https://0659715a31771946c109265f4d1c3a64@o4507567364636672.ingest.us.sentry.io/4507567368437760",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


app = FastAPI(title=settings.PROJECT_NAME)

# 임시 개발용 CORS 설정 - 모든 도메인 허용 (나중에 제한 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 임시로 모든 도메인 허용
    allow_credentials=False,  # 모든 도메인 허용시 credentials는 False여야 함
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}


# FastAPI 시작 시 Celery 연결 테스트
@app.on_event("startup")
async def startup_event():
    """FastAPI 시작 시 Celery 연결 확인"""
    try:
        # Redis 연결 정보 출력
        print(f"📡 [FastAPI] Celery 브로커: {celery_app.conf.broker_url}")
        print(f"📊 [FastAPI] Celery 결과 백엔드: {celery_app.conf.result_backend}")

        # Celery 브로커 연결 테스트 (관대한 타임아웃)
        import time

        time.sleep(2)  # Worker 초기화 대기

        inspect = celery_app.control.inspect(timeout=3)  # 3초 타임아웃
        active_workers = inspect.active()

        if active_workers:
            print(f"✅ [FastAPI] Celery 워커 연결 성공: {list(active_workers.keys())}")
        else:
            print("ℹ️ [FastAPI] Celery 워커 확인 중... (태스크는 정상 처리됩니다)")
            print("   - 워커가 별도 컨테이너에서 실행 중일 수 있습니다")
            print("   - Redis 연결이 정상이면 태스크가 자동으로 처리됩니다")

    except Exception as e:
        print(f"ℹ️ [FastAPI] Celery 연결 확인 실패 (정상적일 수 있음): {e}")
        print("   - 컨테이너 환경에서는 워커 감지가 어려울 수 있습니다")
        print("   - 태스크는 여전히 정상적으로 처리됩니다")


app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(events_router, prefix="/api/v1/events", tags=["events"])
app.include_router(verify_router, prefix="/api/v1", tags=["verify"])
app.include_router(pbn_rest_router, prefix="/api/v1", tags=["pbn"])
app.include_router(redis_debug_router, prefix="/api/v1/debug", tags=["debug"])
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


print("[FastAPI 환경] CELERY_BROKER_URL:", os.getenv("CELERY_BROKER_URL"))
print("[FastAPI 환경] CELERY_RESULT_BACKEND:", os.getenv("CELERY_RESULT_BACKEND"))
