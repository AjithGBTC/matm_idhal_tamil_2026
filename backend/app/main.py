from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(title="Manam Matrimony SaaS API", version="0.1.0", description="Tenant-scoped administration API for the Manam matrimony platform.", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type", "X-Request-ID"])
app.include_router(api_router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "manam-api"}
