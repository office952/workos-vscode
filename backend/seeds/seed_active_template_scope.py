"""Restrict active ProductSystem scope to owner-valid templates.

Idempotent: deactivates all other product_templates rows (no hard delete).
Preserves template JSON/history for architecture tests and future reactivation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sqlalchemy import select

from core.database import db_manager
from services.active_template_scope import (
    ARCHIVE_NOTE_SUFFIX,
    OWNER_VALID_ACTIVE_TEMPLATE_CODE,
    OWNER_VALID_ACTIVE_TEMPLATE_CODES,
    append_archive_note,
    is_owner_valid_active_template,
    normalize_template_code,
)

logger = logging.getLogger(__name__)


async def seed_active_template_scope() -> Dict[str, Any]:
    activated: List[str] = []
    deactivated: List[str] = []
    skipped: List[str] = []

    async with db_manager.async_session_maker() as session:
        from models.product_templates import Product_templates

        rows = (await session.execute(select(Product_templates))).scalars().all()

        for row in rows:
            code = normalize_template_code(row.template_code)
            if not code:
                continue

            should_be_active = is_owner_valid_active_template(code)
            current_active = row.active is not False

            if should_be_active:
                changed = False
                if not current_active:
                    row.active = True
                    changed = True
                if changed:
                    activated.append(code)
                else:
                    skipped.append(code)
                continue

            changed = False
            if current_active:
                row.active = False
                changed = True
            new_notes = append_archive_note(row.notes)
            if (row.notes or "").strip() != new_notes.strip():
                row.notes = new_notes
                changed = True
            if changed:
                deactivated.append(code)
            else:
                skipped.append(code)

        await session.commit()

    logger.info(
        "Active template scope: owner-valid=%s activated=%s deactivated=%s skipped=%s",
        sorted(OWNER_VALID_ACTIVE_TEMPLATE_CODES),
        activated,
        deactivated,
        len(skipped),
    )
    return {
        "owner_valid_active": OWNER_VALID_ACTIVE_TEMPLATE_CODE,
        "owner_valid_active_codes": sorted(OWNER_VALID_ACTIVE_TEMPLATE_CODES),
        "activated": activated,
        "deactivated": deactivated,
        "skipped_count": len(skipped),
        "archive_note": ARCHIVE_NOTE_SUFFIX,
    }
