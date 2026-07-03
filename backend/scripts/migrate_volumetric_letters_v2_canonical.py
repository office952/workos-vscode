from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy import delete, select, text

from core.database import db_manager
from models.intake_v4_workspace import IntakeV4WorkspaceRecord
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates

OLD_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"
NEW_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"


async def _table_exists(session, table: str) -> bool:
    row = (
        await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table"),
            {"table": table},
        )
    ).first()
    return row is not None


async def _has_column(session, table: str, column: str) -> bool:
    rows = (await session.execute(text(f"PRAGMA table_info({table})"))).mappings().all()
    return any(row["name"] == column for row in rows)


async def migrate_volumetric_letters_v2_canonical() -> dict[str, int]:
    await db_manager.init_db()
    async with db_manager.async_session_maker() as session:
        new_template = (
            await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == NEW_TEMPLATE_CODE
                )
            )
        ).scalar_one_or_none()
        if new_template is None:
            raise RuntimeError(f"Missing canonical template {NEW_TEMPLATE_CODE}")

        old_template = (
            await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == OLD_TEMPLATE_CODE
                )
            )
        ).scalar_one_or_none()

        new_dossier = (
            await session.execute(
                select(ProductBlueprintDossier).where(
                    ProductBlueprintDossier.template_code == NEW_TEMPLATE_CODE
                )
            )
        ).scalar_one_or_none()
        if new_dossier is None:
            raise RuntimeError(f"Missing canonical dossier {NEW_TEMPLATE_CODE}")

        now = datetime.now(timezone.utc)
        stats = {
            "workspace_records_updated": 0,
            "workspace_payloads_updated": 0,
            "product_family_defaults_updated": 0,
            "intake_v5_projects_updated": 0,
            "legacy_dossiers_deleted": 0,
            "legacy_templates_deleted": 0,
        }

        new_template.active = True
        new_template.updated_at = now
        new_dossier.status = "approved"
        new_dossier.updated_at = now

        workspaces = (
            await session.execute(
                select(IntakeV4WorkspaceRecord).where(
                    IntakeV4WorkspaceRecord.template_code == OLD_TEMPLATE_CODE
                )
            )
        ).scalars().all()
        for record in workspaces:
            record.template_code = NEW_TEMPLATE_CODE
            record.updated_at = now
            stats["workspace_records_updated"] += 1
            try:
                payload = json.loads(record.payload_json or "{}")
            except json.JSONDecodeError:
                payload = {}
            if isinstance(payload, dict):
                binding = payload.setdefault("product_binding", {})
                if isinstance(binding, dict):
                    binding["template_code"] = NEW_TEMPLATE_CODE
                    binding["template_id"] = new_template.id
                    stats["workspace_payloads_updated"] += 1
                record.payload_json = json.dumps(payload, ensure_ascii=False)

        if (
            old_template is not None
            and await _table_exists(session, "product_families")
            and await _has_column(session, "product_families", "default_template_id")
        ):
            result = await session.execute(
                text(
                    "UPDATE product_families "
                    "SET default_template_id=:new_id "
                    "WHERE default_template_id=:old_id"
                ),
                {"new_id": new_template.id, "old_id": old_template.id},
            )
            stats["product_family_defaults_updated"] = result.rowcount or 0

        if await _table_exists(session, "intake_v5_projects") and await _has_column(
            session, "intake_v5_projects", "template_code"
        ):
            result = await session.execute(
                text(
                    "UPDATE intake_v5_projects "
                    "SET template_code=:new_code "
                    "WHERE template_code=:old_code"
                ),
                {"new_code": NEW_TEMPLATE_CODE, "old_code": OLD_TEMPLATE_CODE},
            )
            stats["intake_v5_projects_updated"] = result.rowcount or 0

        result = await session.execute(
            delete(ProductBlueprintDossier).where(
                ProductBlueprintDossier.template_code == OLD_TEMPLATE_CODE
            )
        )
        stats["legacy_dossiers_deleted"] = result.rowcount or 0

        result = await session.execute(
            delete(Product_templates).where(Product_templates.template_code == OLD_TEMPLATE_CODE)
        )
        stats["legacy_templates_deleted"] = result.rowcount or 0

        await session.commit()
        return stats


async def main() -> None:
    stats = await migrate_volumetric_letters_v2_canonical()
    print(f"[migrate_volumetric_letters_v2_canonical] {stats}")


if __name__ == "__main__":
    asyncio.run(main())
