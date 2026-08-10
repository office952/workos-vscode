"""Fail-closed protection: demo tooling must never target backend/dev.db."""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEMO_DB_PATH = BACKEND_ROOT / "demo" / "workos_demo.db"
FORBIDDEN_DEV_DB_PATH = BACKEND_ROOT / "dev.db"


class DemoDbGuardError(RuntimeError):
    """Raised when a demo bootstrap would touch the real local dev database."""


def resolve_sqlite_path_from_url(database_url: str) -> Path | None:
    """Return filesystem path for sqlite URLs; None for non-sqlite engines."""
    url = (database_url or "").strip()
    if not url:
        raise DemoDbGuardError("DATABASE_URL is empty")
    if not url.startswith("sqlite"):
        return None

    # sqlite+aiosqlite:///C:/path or sqlite:///./rel
    raw = url.split(":///", 1)[-1] if ":///" in url else url.split("://", 1)[-1]
    raw = unquote(raw)
    if raw.startswith("/") and re.match(r"^/[A-Za-z]:", raw):
        # /C:/... → C:/...
        raw = raw[1:]
    path = Path(raw)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    else:
        path = path.resolve()
    return path


def assert_safe_demo_db_path(path: Path) -> Path:
    """Accept only dedicated demo DB paths; never backend/dev.db."""
    resolved = path.resolve()
    forbidden = FORBIDDEN_DEV_DB_PATH.resolve()
    if resolved == forbidden:
        raise DemoDbGuardError(
            f"Refusing demo DB path {resolved}: equals forbidden {forbidden}"
        )
    if resolved.name.lower() == "dev.db":
        raise DemoDbGuardError(
            f"Refusing demo DB path {resolved}: basename dev.db is forbidden"
        )
    return resolved


def assert_safe_demo_database_url(database_url: str) -> Path:
    """Validate DATABASE_URL for demo bootstrap; return resolved sqlite path."""
    path = resolve_sqlite_path_from_url(database_url)
    if path is None:
        raise DemoDbGuardError(
            "Demo bootstrap currently supports SQLite only "
            f"(got non-sqlite DATABASE_URL scheme from {urlparse(database_url).scheme!r})"
        )
    return assert_safe_demo_db_path(path)


def default_demo_database_url() -> str:
    path = DEFAULT_DEMO_DB_PATH.resolve()
    assert_safe_demo_db_path(path)
    posix = path.as_posix()
    return f"sqlite+aiosqlite:///{posix}"


def ensure_demo_database_url_env() -> Path:
    """Require DATABASE_URL and validate it; return resolved path."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise DemoDbGuardError(
            "DATABASE_URL is required for demo bootstrap "
            "(must point at backend/demo/workos_demo.db, never backend/dev.db)"
        )
    return assert_safe_demo_database_url(url)
