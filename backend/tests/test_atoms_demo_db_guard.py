"""Safety tests for Atoms demo DB isolation guard."""

from __future__ import annotations

from pathlib import Path

import pytest

from demo.db_guard import (
    DEFAULT_DEMO_DB_PATH,
    DemoDbGuardError,
    assert_safe_demo_database_url,
    assert_safe_demo_db_path,
    default_demo_database_url,
    resolve_sqlite_path_from_url,
)


def test_default_demo_path_is_accepted() -> None:
    path = assert_safe_demo_db_path(DEFAULT_DEMO_DB_PATH)
    assert path.name == "workos_demo.db"
    assert path.parent.name == "demo"


def test_dev_db_absolute_rejected() -> None:
    backend = Path(__file__).resolve().parents[1]
    with pytest.raises(DemoDbGuardError, match="forbidden"):
        assert_safe_demo_db_path(backend / "dev.db")


def test_dev_db_basename_rejected(tmp_path: Path) -> None:
    with pytest.raises(DemoDbGuardError, match="basename dev.db"):
        assert_safe_demo_db_path(tmp_path / "dev.db")


def test_database_url_to_dev_db_rejected() -> None:
    backend = Path(__file__).resolve().parents[1]
    url = "sqlite+aiosqlite:///" + (backend / "dev.db").resolve().as_posix()
    with pytest.raises(DemoDbGuardError):
        assert_safe_demo_database_url(url)


def test_default_demo_database_url_roundtrip() -> None:
    url = default_demo_database_url()
    path = resolve_sqlite_path_from_url(url)
    assert path is not None
    assert path.resolve() == DEFAULT_DEMO_DB_PATH.resolve()
    assert_safe_demo_database_url(url)
