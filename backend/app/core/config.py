import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

BACKEND_DIR = Path(__file__).resolve().parents[2]


def resolve_database_url(value: str) -> str:
    """Resolve relative SQLite paths from the backend directory, not the caller's cwd."""
    url = make_url(value)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return value
    db_path = Path(url.database)
    if not db_path.is_absolute():
        return url.set(database=str((BACKEND_DIR / db_path).resolve())).render_as_string(hide_password=False)
    return value


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = resolve_database_url(os.getenv("DATABASE_URL", "sqlite:///./app.db"))
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
    refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_DAYS", "14"))
    cors_origins: tuple[str, ...] = tuple(origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip())


settings = Settings()
