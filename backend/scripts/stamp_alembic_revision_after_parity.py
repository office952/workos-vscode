#!/usr/bin/env python
"""Explicit Alembic baselining after schema parity verification.

NOT used by application runtime. Operators / agents only.

Use when a database already has Alembic-owned objects (e.g. table created by a
historical create_all race) and needs a supported revision stamp AFTER parity
checks — never write alembic_version via ad-hoc SQL from production code.

Example (isolated / non-QA only unless Owner authorizes):

  cd backend
  $env:DATABASE_URL='sqlite+aiosqlite:///./some-isolated.db'
  .\\.venv\\Scripts\\python.exe scripts\\stamp_alembic_revision_after_parity.py \\
      --revision s63_execution_task_assignment_transitions \\
      --require-table execution_task_assignment_transitions \\
      --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _sync_url(async_url: str) -> str:
    if "+aiosqlite" in async_url:
        return async_url.replace("sqlite+aiosqlite", "sqlite", 1)
    if "+asyncpg" in async_url:
        return async_url.replace("postgresql+asyncpg", "postgresql", 1)
    return async_url


def _verify_table(engine, table_name: str) -> None:
    with engine.connect() as conn:
        names = set(inspect(conn).get_table_names())
        if table_name not in names:
            raise SystemExit(f"FAIL: required table missing: {table_name}")
        cols = {c["name"] for c in inspect(conn).get_columns(table_name)}
        if not cols:
            raise SystemExit(f"FAIL: table {table_name} has no columns")
        print(f"OK: table {table_name} present with {len(cols)} columns")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stamp Alembic revision after explicit schema parity checks."
    )
    parser.add_argument(
        "--revision",
        required=True,
        help="Revision id to stamp (e.g. s63_execution_task_assignment_transitions)",
    )
    parser.add_argument(
        "--require-table",
        action="append",
        default=[],
        help="Table that must already exist (repeatable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verify only; do not call alembic stamp",
    )
    args = parser.parse_args()

    raw = os.environ.get("DATABASE_URL", "").strip()
    if not raw:
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 2

    engine = create_engine(_sync_url(raw))
    for table in args.require_table:
        _verify_table(engine, table)

    with engine.connect() as conn:
        try:
            current = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
            print("current alembic_version rows:", [r[0] for r in current])
        except Exception as exc:  # noqa: BLE001 — diagnostic only
            print(f"alembic_version not readable yet: {exc}")

    if args.dry_run:
        print(f"DRY-RUN: would stamp revision={args.revision}")
        return 0

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    # env.py resolves DATABASE_URL via resolve_database_url
    command.stamp(cfg, args.revision)
    print(f"STAMPED: {args.revision} via alembic.command.stamp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
