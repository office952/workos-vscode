"""CLI entrypoint — apply Product 001 volumetric owner-confirmed material prices."""

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

from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    OWNER_CONFIRMED_NOT_ACTIVATED,
    seed_volumetric_owner_confirmed_prices,
)

logger = logging.getLogger(__name__)


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    await db_manager.init_db()
    summary = await seed_volumetric_owner_confirmed_prices()
    print(json.dumps(summary, indent=2, default=str))
    print("\nNot activated (by design):")
    for code, reason in OWNER_CONFIRMED_NOT_ACTIVATED.items():
        print(f"  {code}: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
