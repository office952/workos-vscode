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

_LEGACY_LETTERS_ALIAS = "TPL-VOLUMETRIC-LETTERS"
_CANONICAL_LETTERS_CODE = normalize_template_code(OWNER_VALID_ACTIVE_TEMPLATE_CODE)
_ALLOWED_ACTIVE_LOGO_STRATEGY_TEMPLATE = normalize_template_code("TPL-VOLUMETRIC-LOGO-LIGHTING_v1")


def validate_active_template_scope_postcondition(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate owner policy for Product System / Work Intake scope.

    Canonical policy:
    - TPL-VOLUMETRIC-LETTERS_v2 is the only Work Intake offerable root.
    - TPL-VOLUMETRIC-LOGO_v1 may exist as a Product Template candidate, but not offerable.
    - component roots / component_only quote modes remain blocked.
    - legacy logo component templates must not appear owner-facing active.
    """
    blockers: List[str] = []
    normalized_rows = []
    for row in rows:
        normalized = dict(row)
        normalized["template_code"] = normalize_template_code(normalized.get("template_code"))
        if normalized["template_code"] == normalize_template_code(_LEGACY_LETTERS_ALIAS):
            normalized["template_code"] = _CANONICAL_LETTERS_CODE
        normalized_rows.append(normalized)

    offerable_roots = tuple(
        sorted(
            row["template_code"]
            for row in normalized_rows
            if row.get("db_active") is not False and row.get("quote_offerable") is True
        )
    )
    expected_roots = (_CANONICAL_LETTERS_CODE,)
    if offerable_roots != expected_roots:
        blockers.append("work_intake_offerable_roots_mismatch")

    for row in normalized_rows:
        code = str(row.get("template_code") or "")
        quote_offerable = row.get("quote_offerable") is True
        root_type = str(row.get("root_type") or "product_template")
        quote_mode = str(row.get("quote_mode") or "product_total")
        product_system_role = str(row.get("product_system_role") or "")
        display_group = str(row.get("display_group") or "")
        db_active = row.get("db_active") is not False

        if quote_offerable and code not in expected_roots:
            blockers.append(f"unexpected_work_intake_offerable:{code}")

        if code == normalize_template_code("TPL-VOLUMETRIC-LOGO_v1"):
            if quote_offerable:
                blockers.append("logo_root_offerability_enabled")
            if product_system_role != "candidate_product":
                blockers.append("logo_not_candidate_product")
            if display_group != "candidate_products":
                blockers.append("logo_not_in_candidate_group")

        if root_type == "component_template":
            blockers.append(f"component_template_root_or_quote_enabled:{code}")
        if quote_mode == "component_only":
            blockers.append(f"component_quote_enabled:{code}")

        if code.startswith("TPL-VOLUMETRIC-LOGO-") and code not in {
            normalize_template_code("TPL-VOLUMETRIC-LOGO-V1"),
            _ALLOWED_ACTIVE_LOGO_STRATEGY_TEMPLATE,
        } and db_active:
            blockers.append(f"legacy_logo_component_owner_facing_active:{code}")

    return {
        "ok": len(blockers) == 0,
        "blockers": tuple(sorted(set(blockers))),
        "work_intake_offerable_roots": offerable_roots,
    }


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
