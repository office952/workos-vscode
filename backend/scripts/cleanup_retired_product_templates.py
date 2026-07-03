from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from sqlalchemy import text

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from core.database import db_manager  # noqa: E402
import models  # noqa: F401,E402


RETIRED_PRODUCT_TEMPLATE_CODES = (
    "TPL-BANNER-STANDARD",
    "TPL-PLEXI-PLATE",
    "TPL-VINYL-STICKER",
    "TPL-LIGHTBOX-STANDARD",
    "TPL-MESH-EXTERNALIZED",
    "TPL-VOLUMETRIC-LETTERS",
)


async def cleanup_retired_product_templates() -> dict[str, Any]:
    deleted: list[str] = []
    skipped: dict[str, dict[str, int]] = {}
    missing: list[str] = []

    async with db_manager.async_session_maker() as session:
        for template_code in RETIRED_PRODUCT_TEMPLATE_CODES:
            row = (
                await session.execute(
                    text(
                        "select id, template_code from product_templates "
                        "where template_code = :template_code"
                    ),
                    {"template_code": template_code},
                )
            ).mappings().first()
            if not row:
                missing.append(template_code)
                continue

            template_id = int(row["id"])
            refs = {
                "intake_v3_workspaces": (
                    await session.execute(
                        text("select count(*) from intake_v3_workspaces where template_code = :template_code"),
                        {"template_code": template_code},
                    )
                ).scalar_one(),
                "intake_v4_workspaces": (
                    await session.execute(
                        text("select count(*) from intake_v4_workspaces where template_code = :template_code"),
                        {"template_code": template_code},
                    )
                ).scalar_one(),
                "intake_v5_projects": (
                    await session.execute(
                        text("select count(*) from intake_v5_projects where template_code = :template_code"),
                        {"template_code": template_code},
                    )
                ).scalar_one(),
                "quote_output_snapshots": (
                    await session.execute(
                        text(
                            "select count(*) from quote_output_snapshots "
                            "where source_template_id = :template_id or source_template_code = :template_code"
                        ),
                        {"template_id": template_id, "template_code": template_code},
                    )
                ).scalar_one(),
                "order_output_snapshot_references": (
                    await session.execute(
                        text(
                            "select count(*) from order_output_snapshot_references "
                            "where source_template_id = :template_id or source_template_code = :template_code"
                        ),
                        {"template_id": template_id, "template_code": template_code},
                    )
                ).scalar_one(),
            }
            blocking_refs = {key: int(value) for key, value in refs.items() if int(value) > 0}
            if blocking_refs:
                skipped[template_code] = blocking_refs
                continue

            await session.execute(
                text("update product_families set default_template_id = null where default_template_id = :template_id"),
                {"template_id": template_id},
            )
            await session.execute(
                text("delete from product_blueprint_dossier where template_id = :template_id or template_code = :template_code"),
                {"template_id": template_id, "template_code": template_code},
            )
            await session.execute(
                text("delete from product_templates where id = :template_id"),
                {"template_id": template_id},
            )
            deleted.append(template_code)

        await session.commit()

    return {"deleted": deleted, "skipped": skipped, "missing": missing}


async def _main() -> None:
    await db_manager.init_db()
    result = await cleanup_retired_product_templates()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(_main())