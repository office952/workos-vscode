"""Controlled activate-only for TPL-VOLUM-ALUMINIU_v1.

Owner ACTIVATION GO — flips product_templates.active True for the canonical row only.
Does NOT publish child or parent. Does NOT touch module links, formulas, or pricing.
Idempotent. Auditable. No schema migration.

Usage (from backend/, with env injected):
  .\\.venv\\Scripts\\python.exe scripts\\activate_tpl_volum_aluminiu_v1.py
  .\\.venv\\Scripts\\python.exe scripts\\activate_tpl_volum_aluminiu_v1.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from core.database import db_manager
import models  # noqa: F401
from models.product_templates import Product_templates
from services.volum_aluminiu_component_contract import (
    ACTIVATION_FORBIDDEN_IN_THIS_BUILD,
    BOM_COMPONENT_ID,
    PARENT_TEMPLATE_CODE,
    TEMPLATE_CODE,
)

logger = logging.getLogger(__name__)

ACTOR = "product_system_activation_controller"
FORBIDDEN_ALIAS_CODES = (
    "TPL-COMP-LETTER-RETURN-CANT_v1",
    "TPL-VOLUMETRIC-LOGO-RETURN_v1",
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _preflight(session) -> dict[str, Any]:
    if ACTIVATION_FORBIDDEN_IN_THIS_BUILD:
        raise RuntimeError("ACTIVATION_FORBIDDEN_IN_THIS_BUILD is still True — refuse write")

    rows = (
        await session.execute(
            select(Product_templates).where(Product_templates.template_code == TEMPLATE_CODE)
        )
    ).scalars().all()
    if len(rows) != 1:
        raise RuntimeError(
            f"Canonical identity ambiguous: expected 1 row for {TEMPLATE_CODE}, found {len(rows)}"
        )
    row = rows[0]

    dup_active = (
        await session.execute(
            select(func.count())
            .select_from(Product_templates)
            .where(
                Product_templates.template_code == TEMPLATE_CODE,
                Product_templates.active.is_(True),
            )
        )
    ).scalar()
    # 0 or 1 ok (idempotent); >1 impossible with unique code but keep fail-closed
    if int(dup_active or 0) > 1:
        raise RuntimeError("Duplicate active rows for TPL-VOLUM-ALUMINIU_v1")

    # Do not activate aliases / logo return in this script.
    for alias in FORBIDDEN_ALIAS_CODES:
        alias_rows = (
            await session.execute(
                select(Product_templates).where(Product_templates.template_code == alias)
            )
        ).scalars().all()
        if any(bool(r.active) is False for r in alias_rows):
            # Aliases may be inactive or missing — never flip them here.
            pass
        _ = alias_rows

    parent = (
        await session.execute(
            select(Product_templates)
            .where(Product_templates.template_code == PARENT_TEMPLATE_CODE)
            .limit(1)
        )
    ).scalar_one_or_none()
    if parent is None:
        raise RuntimeError(f"Parent {PARENT_TEMPLATE_CODE} missing — refuse activation")

    return {
        "row_id": row.id,
        "template_code": row.template_code,
        "prior_active": row.active,
        "prior_publication_status": row.publication_status,
        "prior_published_at": str(row.published_at) if row.published_at else None,
        "parent_active": parent.active,
        "parent_publication_status": parent.publication_status,
        "parent_published_at": str(parent.published_at) if parent.published_at else None,
        "bom_component_id": BOM_COMPONENT_ID,
    }


async def activate(*, dry_run: bool, actor: str) -> dict[str, Any]:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as session:
        pre = await _preflight(session)
        row = (
            await session.execute(
                select(Product_templates).where(Product_templates.id == pre["row_id"]).limit(1)
            )
        ).scalar_one()

        already = bool(row.active) is True
        mutated = False
        if not already and not dry_run:
            row.active = True
            # Activate-only: never set publication fields.
            await session.commit()
            await session.refresh(row)
            mutated = True

        result_active = bool(row.active)
        would_set_active = True if (dry_run and not already) else None
        if dry_run and not already:
            result_active = False

        result = {
            "schema": "volum_aluminiu_controlled_activation_v1",
            "actor": actor,
            "timestamp_utc": _utcnow().isoformat(),
            "dry_run": dry_run,
            "command": "activate_tpl_volum_aluminiu_v1",
            "canonical_template_code": TEMPLATE_CODE,
            "row_id": row.id,
            "row_count_matched": 1,
            "fields_mutated": ["active"] if mutated else [],
            "previous": {
                "active": pre["prior_active"],
                "publication_status": pre["prior_publication_status"],
                "published_at": pre["prior_published_at"],
            },
            "result": {
                "active": result_active,
                "publication_status": row.publication_status,
                "published_at": str(row.published_at) if row.published_at else None,
                "would_set_active": would_set_active,
            },
            "idempotent_noop": already,
            "mutated": mutated,
            "parent": {
                "template_code": PARENT_TEMPLATE_CODE,
                "active": pre["parent_active"],
                "publication_status": pre["parent_publication_status"],
                "published_at": pre["parent_published_at"],
                "published": pre["parent_publication_status"] == "PUBLISHED",
                "touched": False,
            },
            "aliases_activated": False,
            "logo_return_touched": False,
            "audit_event": {
                "type": "component_template_activate_only",
                "template_code": TEMPLATE_CODE,
                "from_active": pre["prior_active"],
                "to_active": True if (mutated or already or (dry_run and not already)) else pre["prior_active"],
            },
        }
        logger.info("Activation result: %s", json.dumps(result, default=str))
        return result


def _write_evidence(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


async def _main() -> int:
    parser = argparse.ArgumentParser(description="Activate TPL-VOLUM-ALUMINIU_v1 (activate-only)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--actor", default=ACTOR)
    parser.add_argument(
        "--evidence",
        default=str(
            Path(__file__).resolve().parents[2]
            / "docs/qa/product-system-authoring-runtime-codesign-e2e"
            / "volum-aluminiu-activation"
            / "activation_write_receipt.json"
        ),
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    result = await activate(dry_run=args.dry_run, actor=args.actor)
    _write_evidence(result, Path(args.evidence))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
