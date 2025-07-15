from fastapi import APIRouter
from app.api.v1.endpoints import auth, monitoring, redis_debug

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(redis_debug.router, prefix="/debug", tags=["debug"])
