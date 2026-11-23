from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import BACKEND_DIR, resolve_database_url


def test_relative_sqlite_path_resolves_from_backend_directory():
    resolved = make_url(resolve_database_url("sqlite:///./app.db"))
    assert Path(resolved.database) == BACKEND_DIR / "app.db"


def test_absolute_sqlite_path_is_preserved():
    configured = (BACKEND_DIR / "custom.db").resolve()
    resolved = make_url(resolve_database_url(f"sqlite:///{configured.as_posix()}"))
    assert Path(resolved.database) == configured
