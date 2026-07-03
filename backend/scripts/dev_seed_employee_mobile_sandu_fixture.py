"""Dev-only reproducible Employee Mobile fixture — Sandu user, task assignments, intake SVG.

Creates/updates a local dev scenario for Employee Mobile production document smoke.
Does NOT run at app startup or in migrations.

Usage (PowerShell):
    $env:APP_ENV='development'
    $env:ENVIRONMENT='development'
    $env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
    $env:JWT_SECRET_KEY='local-dev-secret-not-for-production'

    cd backend
    .\\.venv\\Scripts\\python.exe scripts/dev_seed_employee_mobile_sandu_fixture.py
    .\\.venv\\Scripts\\python.exe scripts/dev_seed_employee_mobile_sandu_fixture.py --apply

Safety:
    - Default is dry-run (no DB/storage writes).
    - --apply writes only in local/development/test APP_ENV with a local sqlite DATABASE_URL.
    - Set WORKOS_DEV_SANDU_FIXTURE_FORCE=1 with --apply to override non-sqlite guard (discouraged).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from core.config import resolve_database_url  # noqa: E402
from core.database import db_manager  # noqa: E402
from services.dev_employee_mobile_sandu_fixture_service import (  # noqa: E402
    DevSanduFixtureConfig,
    seed_dev_employee_mobile_sandu_fixture,
    smoke_commands_text,
)


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes")


async def run(apply: bool) -> dict:
    await db_manager.ensure_initialized()
    if not db_manager.async_session_maker:
        raise RuntimeError("dev_seed_employee_mobile_sandu_fixture: database not initialized")

    config = DevSanduFixtureConfig(
        apply=apply,
        force_non_sqlite=_truthy("WORKOS_DEV_SANDU_FIXTURE_FORCE"),
    )
    async with db_manager.async_session_maker() as session:
        result = await seed_dev_employee_mobile_sandu_fixture(session, config)
    payload = result.to_dict()
    payload["smoke_commands"] = smoke_commands_text()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Dev-only Sandu Employee Mobile production fixture")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply DB/storage changes (default: dry-run only)",
    )
    args = parser.parse_args()

    try:
        resolve_database_url()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.apply:
        print("WARNING: applying dev-only Sandu Employee Mobile fixture to DATABASE_URL")
    else:
        print("DRY-RUN: no changes will be written (pass --apply to modify dev DB/storage)")

    payload = asyncio.run(run(apply=args.apply))
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
