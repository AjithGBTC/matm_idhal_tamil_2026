from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.database import Base
from app.core.security import hash_password, verify_password
from app.main import app
from app.models import AdminUser


@pytest.fixture
def auth_client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with TestSession.begin() as db:
        db.add(AdminUser(tenant_id=None, email="platform@example.com", full_name="Test Admin", password_hash=hash_password("only-test-password-123"), role="super_admin", permissions=["*"], is_active=True))
        db.add(AdminUser(tenant_id=None, email="inactive@example.com", full_name="Inactive Admin", password_hash=hash_password("only-test-password-456"), role="super_admin", permissions=["*"], is_active=False))

    def override_get_db():
        with TestSession() as db:
            yield db

    monkeypatch.setattr("app.core.security.settings", SimpleNamespace(jwt_secret_key="test-only-secret-key-which-is-long-enough", access_token_minutes=15, refresh_token_days=14))
    monkeypatch.setattr("app.api.v1.endpoints.auth.settings", SimpleNamespace(access_token_minutes=15, refresh_token_days=14))
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    engine.dispose()


def test_bootstrap_hash_verifies_with_login_verifier():
    password = "test-password-created-in-memory"
    stored_hash = hash_password(password)
    assert verify_password(password, stored_hash)
    assert not verify_password("wrong-test-password", stored_hash)


def test_super_admin_login_normalizes_email_and_returns_tokens(auth_client):
    response = auth_client.post("/api/v1/auth/super-admin/login", json={"email": "PLATFORM@EXAMPLE.COM", "password": "only-test-password-123"})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_super_admin_login_rejects_wrong_password_and_inactive_account(auth_client):
    wrong_password = auth_client.post("/api/v1/auth/super-admin/login", json={"email": "platform@example.com", "password": "not-the-password"})
    inactive_account = auth_client.post("/api/v1/auth/super-admin/login", json={"email": "inactive@example.com", "password": "only-test-password-456"})
    assert wrong_password.status_code == 401
    assert inactive_account.status_code == 401
