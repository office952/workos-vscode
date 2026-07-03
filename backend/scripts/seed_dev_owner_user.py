"""Local/dev User seed for Owner Employee Mobile readiness (env-driven, idempotent).

Creates only a User row when local DB has no OIDC login yet.
Does NOT create Employee, attendance, requests, or payroll.

Usage (PowerShell):
    $env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
    $env:WORKOS_DEV_OWNER_DRY_RUN='1'
    python backend/scripts/seed_dev_owner_user.py

Real run: set WORKOS_DEV_OWNER_DRY_RUN='0'
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from core.config import resolve_database_url  # noqa: E402
from core.database import db_manager  # noqa: E402
from services.dev_owner_user_seed_service import (  # noqa: E402
    load_dev_owner_user_seed_config_from_env,
    seed_dev_owner_user,
)


async def run() -> dict:
    await db_manager.ensure_initialized()
    if not db_manager.async_session_maker:
        raise RuntimeError("seed_dev_owner_user: database not initialized")

    config = load_dev_owner_user_seed_config_from_env()
    async with db_manager.async_session_maker() as session:
        result = await seed_dev_owner_user(session, config)
    return result.to_dict()


def main() -> int:
    try:
        resolve_database_url()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = asyncio.run(run())
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
