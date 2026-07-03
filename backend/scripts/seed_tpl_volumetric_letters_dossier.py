"""Run TPL-VOLUMETRIC-LETTERS blueprint dossier seed on dev/local DB."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import db_manager
from seeds.seed_tpl_volumetric_letters_dossier import seed_tpl_volumetric_letters_dossier

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    await db_manager.init_db()
    result = await seed_tpl_volumetric_letters_dossier()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
