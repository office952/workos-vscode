"""CLI — set CostEngine template costing base currency to EUR (idempotent)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from core.database import db_manager  # noqa: E402
import models  # noqa: F401,E402

from seeds.seed_cost_engine_template_currency import (  # noqa: E402
    seed_cost_engine_template_base_currency,
)


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    await db_manager.init_db()
    summary = await seed_cost_engine_template_base_currency()
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
