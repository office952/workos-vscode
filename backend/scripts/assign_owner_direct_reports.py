"""Assign direct reports to owner/manager employee via manager_employee_id (env-driven).

Usage:
    $env:WORKOS_OWNER_EMAIL='<owner-email>'
    $env:WORKOS_DIRECT_REPORT_USER_EMAILS='<emp1>,<emp2>'
    $env:WORKOS_DIRECT_REPORTS_DRY_RUN='1'
    python backend/scripts/assign_owner_direct_reports.py
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
from services.employee_direct_reports_assignment_service import (  # noqa: E402
    assign_direct_reports,
    load_direct_reports_config_from_env,
)


async def run() -> dict:
    await db_manager.ensure_initialized()
    if not db_manager.async_session_maker:
        raise RuntimeError("assign_owner_direct_reports: database not initialized")

    config = load_direct_reports_config_from_env()
    async with db_manager.async_session_maker() as session:
        result = await assign_direct_reports(session, config)
    return result.to_dict()


def main() -> int:
    try:
        resolve_database_url()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = asyncio.run(run())
    print(json.dumps(payload, indent=2))
    if not payload.get("success"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
