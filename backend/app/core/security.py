from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def _secret() -> str:
    secret = settings.jwt_secret_key
    if len(secret) < 32 or secret.startswith("replace-with-"):
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters")
    return secret


def create_access_token(subject: str, role: str, tenant_id: int | None, permissions: list[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "role": role, "tenant_id": tenant_id, "permissions": permissions, "type": "access", "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes), "jti": secrets.token_urlsafe(16)}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def create_refresh_token() -> tuple[str, str, datetime]:
    token = secrets.token_urlsafe(48)
    digest = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
    return token, digest, expires_at


def decode_access_token(token: str) -> dict:
    claims = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    if claims.get("type") != "access":
        raise jwt.InvalidTokenError("Wrong token type")
    return claims
