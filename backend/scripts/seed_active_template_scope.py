"""CLI — apply owner-valid active template scope (TPL-VOLUMETRIC-LETTERS only)."""

from __future__ import annotations

import asyncio
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from core.database import db_manager  # noqa: E402
from seeds.seed_active_template_scope import seed_active_template_scope  # noqa: E402


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_active_template_scope()
    print(f"[seed_active_template_scope] {stats}")


if __name__ == "__main__":
    asyncio.run(_main())
