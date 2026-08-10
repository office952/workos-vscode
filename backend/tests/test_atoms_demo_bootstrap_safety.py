"""Bootstrap safety + deterministic DEMO identity constants."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from demo.db_guard import (
    DEFAULT_DEMO_DB_PATH,
    DemoDbGuardError,
    assert_safe_demo_database_url,
    default_demo_database_url,
)


def test_default_url_never_points_at_dev_db() -> None:
    url = default_demo_database_url()
    path = assert_safe_demo_database_url(url)
    assert path == DEFAULT_DEMO_DB_PATH.resolve()
    assert path.name == "workos_demo.db"
    assert "dev.db" not in path.name


def test_env_dev_db_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = Path(__file__).resolve().parents[1]
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///" + (backend / "dev.db").resolve().as_posix(),
    )
    with pytest.raises(DemoDbGuardError):
        assert_safe_demo_database_url(os.environ["DATABASE_URL"])


def test_seed_module_demo_constants() -> None:
    from scripts import seed_atoms_demo_v1 as seed

    assert seed.DEMO_WORKSPACE_COMPLETE_CODE == "DEMO-INTAKE-LETTERS-001"
    assert seed.DEMO_WORKSPACE_DRAFT_CODE == "DEMO-INTAKE-DRAFT-001"
    assert seed.DEMO_QUOTE_CODE == "DEMO-QUOTE-EUR-001"
    assert seed.DEMO_ORDER_CODE == "DEMO-ORDER-001"
    assert seed.DEMO_WORKSPACE_COMPLETE_ID != seed.HISTORICAL_GOLDEN_ID


@pytest.mark.skipif(
    not DEFAULT_DEMO_DB_PATH.exists(),
    reason="demo DB not bootstrapped in this environment",
)
def test_bootstrapped_demo_db_has_demo_rows() -> None:
    import sqlite3

    conn = sqlite3.connect(DEFAULT_DEMO_DB_PATH)
    codes = [
        r[0]
        for r in conn.execute("select workspace_code from intake_v6_workspaces")
    ]
    assert "DEMO-INTAKE-LETTERS-001" in codes
    assert "DEMO-INTAKE-DRAFT-001" in codes
    q = conn.execute("select code from quotes where code = 'DEMO-QUOTE-EUR-001'").fetchone()
    assert q is not None
    # Guard: never confuse with Owner historical golden id
    assert (
        conn.execute(
            "select count(*) from intake_v6_workspaces where id = ?",
            ("4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1",),
        ).fetchone()[0]
        == 0
    )


def test_last_seed_summary_is_synthetic_when_present() -> None:
    summary_path = Path(__file__).resolve().parents[1] / "demo" / "last_seed_summary.json"
    if not summary_path.exists():
        pytest.skip("no local seed summary")
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data.get("synthetic") is True
    assert data.get("historical_golden_mutated") is False
    assert "dev.db" not in str(data.get("demo_db_path", "")).lower().replace(
        "workos_demo.db", ""
    )
