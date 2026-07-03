from __future__ import annotations

import argparse
import asyncio
import os

from core.database import db_manager
from services.smartbill_client import SmartbillClient, normalize_tax_id


async def _run(tax_id: str, country: str) -> int:
    if str(os.environ.get("SMARTBILL_UAT_ENABLED", "false")).strip().lower() not in {"1", "true", "yes", "on"}:
        print("SMARTBILL_UAT_ENABLED is not enabled. Aborting controlled UAT.")
        return 2

    normalized = normalize_tax_id(tax_id, country=country)
    if not normalized:
        print("Invalid tax_id. Expected RO CUI format.")
        return 2

    await db_manager.init_db()
    async with db_manager.async_session_maker() as db:
        client = await SmartbillClient.from_db_or_env(db)
        result = await client.lookup_company(country=country, tax_id=normalized)

    print(
        {
            "provider": "smartbill",
            "mode": "controlled_uat",
            "status": result.status,
            "message": result.message,
            "normalized": result.normalized,
            "warnings": result.warnings,
        }
    )
    return 0 if result.status in {"found", "not_found"} else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled SmartBill UAT lookup (manual, explicit, no CI live call).")
    parser.add_argument("--tax-id", required=True, help="RO CUI (with or without RO prefix)")
    parser.add_argument("--country", default="RO", choices=["RO"])
    args = parser.parse_args()

    return asyncio.run(_run(args.tax_id, args.country))


if __name__ == "__main__":
    raise SystemExit(main())
