from datetime import datetime, timedelta, timezone
import hashlib

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_principal
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models import AdminUser, AuditEvent
from app.models.entities import RefreshSession
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter()


def issue_tokens(db: Session, user: AdminUser) -> TokenResponse:
    refresh, digest, expires = create_refresh_token()
    db.add(RefreshSession(admin_user_id=user.id, token_hash=digest, expires_at=expires))
    access = create_access_token(str(user.id), user.role, user.tenant_id, user.permissions)
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=settings.access_token_minutes * 60)


def _authenticate(body: LoginRequest, request: Request, db: Session, allowed_roles: set[str] | None = None):
    user = db.scalar(select(AdminUser).where(AdminUser.email == body.email.lower()))
    now = datetime.now(timezone.utc)
    locked = user.locked_until if user else None
    if locked and locked.tzinfo is None:
        locked = locked.replace(tzinfo=timezone.utc)
    if user is None or not user.is_active or (allowed_roles is not None and user.role not in allowed_roles) or (locked and locked > now) or not verify_password(body.password.get_secret_value(), user.password_hash):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)
            db.add(AuditEvent(actor_id=user.id, tenant_id=user.tenant_id, action="login_failed", module="authentication", ip_address=request.client.host if request.client else None))
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    user.failed_login_attempts = 0
    user.locked_until = None
    db.add(AuditEvent(actor_id=user.id, tenant_id=user.tenant_id, action="login_succeeded", module="authentication", ip_address=request.client.host if request.client else None))
    response = issue_tokens(db, user)
    db.commit()
    return response


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    return _authenticate(body, request, db)


@router.post("/super-admin/login", response_model=TokenResponse)
def super_admin_login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    return _authenticate(body, request, db, {"super_admin"})


@router.post("/tenant/login", response_model=TokenResponse)
def tenant_login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    return _authenticate(body, request, db, {"tenant_admin", "manager", "profile_moderator", "payment_manager", "support_staff", "matrimony_agent"})


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    digest = hashlib.sha256(body.refresh_token.encode()).hexdigest()
    session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == digest).with_for_update())
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at if session else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    user = db.get(AdminUser, session.admin_user_id) if session else None
    if session is None or session.revoked_at is not None or expires_at <= now or user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    session.revoked_at = now
    response = issue_tokens(db, user)
    db.commit()
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, principal: dict = Depends(get_current_principal), db: Session = Depends(get_db)):
    digest = hashlib.sha256(body.refresh_token.encode()).hexdigest()
    session = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == digest, RefreshSession.admin_user_id == principal["id"]))
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()


@router.get("/me")
def get_me(principal: dict = Depends(get_current_principal)):
    return principal
