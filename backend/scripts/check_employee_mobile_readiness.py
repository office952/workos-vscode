"""Read-only Employee Mobile readiness check for owner/tester account (env-driven).

Usage:
    $env:WORKOS_OWNER_EMAIL='<owner-email>'
    $env:WORKOS_OWNER_EMPLOYEE_NAME='Axinte Remus'
    python backend/scripts/check_employee_mobile_readiness.py
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
from services.owner_employee_bootstrap_service import (  # noqa: E402
    check_owner_mobile_readiness,
    load_bootstrap_config_from_env,
)


async def run() -> dict:
    await db_manager.ensure_initialized()
    if not db_manager.async_session_maker:
        raise RuntimeError("check_employee_mobile_readiness: database not initialized")

    config = load_bootstrap_config_from_env()
    async with db_manager.async_session_maker() as session:
        result = await check_owner_mobile_readiness(session, config)
    return result.to_dict()


def main() -> int:
    try:
        resolve_database_url()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = asyncio.run(run())
    print(json.dumps(payload, indent=2))
    status = payload.get("status")
    return 0 if status in ("PASS", "WARN") else 1


if __name__ == "__main__":
    raise SystemExit(main())
