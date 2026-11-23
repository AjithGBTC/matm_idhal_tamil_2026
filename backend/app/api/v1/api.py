from fastapi import APIRouter

from app.api.v1.endpoints import auth, platform, tenant

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(platform.router, prefix="/super-admin", tags=["super admin"])
api_router.include_router(tenant.router, prefix="/tenant", tags=["tenant administration"])
