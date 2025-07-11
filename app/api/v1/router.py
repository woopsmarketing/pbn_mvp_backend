from fastapi import APIRouter
from app.api.v1.endpoints import auth, monitoring

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
