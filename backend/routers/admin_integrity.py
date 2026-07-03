"""Admin integrity health-check endpoints for the Product Families Registry.

This router exposes read-only diagnostics that surface referential-integrity
drift between `product_families`, `product_templates`, and `intake_requests`.

Sprint #5 — complements the canonical Product Families Registry shipped in
Sprint #4. It does NOT mutate any data; it only reports.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from models.intake_requests import Intake_requests
from models.product_families import Product_families
from models.product_templates import Product_templates

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/integrity",
    tags=["admin_integrity"],
    dependencies=[Depends(get_current_user)],
)


async def _collect_registry_slugs(db: AsyncSession) -> Dict[str, Dict[str, Any]]:
    """Return a dict keyed by family_id with `{active, default_template_id}`."""
    rows = (await db.execute(select(Product_families))).scalars().all()
    return {
        r.family_id: {
            "id": r.id,
            "label": r.label,
            "active": bool(r.active),
            "default_template_id": r.default_template_id,
        }
        for r in rows
    }


@router.get("/product-families")
async def product_families_integrity(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Integrity health-check for the Product Families Registry.

    Reports:
      - `registry.total` / `registry.active`: counts of canonical families.
      - `templates.orphan_family_id`: templates whose `family_id` is not in
        the registry (or registry entry is inactive).
      - `templates.missing_family_id`: active templates with no family_id.
      - `templates.ambiguous_families`: family_ids with >1 active template
        and no `default_template_id` set on the registry row.
      - `intake.orphan_family_id`: intake rows whose `product_family` value
        is not a valid registry slug (legacy label or typo).
      - `status`: "ok" if no issues found, otherwise "degraded".
    """
    try:
        registry = await _collect_registry_slugs(db)
        registry_total = len(registry)
        registry_active = sum(1 for v in registry.values() if v["active"])
        active_slugs = {k for k, v in registry.items() if v["active"]}

        # ---- templates diagnostics ----
        tpl_rows = (await db.execute(select(Product_templates))).scalars().all()
        orphan_templates: List[Dict[str, Any]] = []
        missing_fid_templates: List[Dict[str, Any]] = []
        active_by_family: Dict[str, List[int]] = {}

        for t in tpl_rows:
            is_active = t.active is None or bool(t.active)
            if not t.family_id:
                if is_active:
                    missing_fid_templates.append(
                        {"id": t.id, "template_code": t.template_code}
                    )
                continue
            if t.family_id not in active_slugs:
                orphan_templates.append(
                    {
                        "id": t.id,
                        "template_code": t.template_code,
                        "family_id": t.family_id,
                        "reason": (
                            "family_id not in registry"
                            if t.family_id not in registry
                            else "registry entry is inactive"
                        ),
                    }
                )
            if is_active and t.family_id in registry:
                active_by_family.setdefault(t.family_id, []).append(t.id)

        ambiguous_families: List[Dict[str, Any]] = []
        for fid, tpl_ids in active_by_family.items():
            if len(tpl_ids) > 1 and not registry[fid]["default_template_id"]:
                ambiguous_families.append(
                    {
                        "family_id": fid,
                        "label": registry[fid]["label"],
                        "active_template_ids": sorted(tpl_ids),
                        "count": len(tpl_ids),
                    }
                )

        # ---- intake diagnostics ----
        intake_rows = (
            await db.execute(
                select(
                    Intake_requests.id,
                    Intake_requests.code,
                    Intake_requests.product_family,
                )
            )
        ).all()
        orphan_intake: List[Dict[str, Any]] = []
        intake_total = len(intake_rows)
        for row in intake_rows:
            pf = row.product_family
            if not pf:
                continue
            if pf not in active_slugs:
                orphan_intake.append(
                    {
                        "id": row.id,
                        "code": row.code,
                        "product_family": pf,
                        "reason": (
                            "not a registry slug"
                            if pf not in registry
                            else "registry entry is inactive"
                        ),
                    }
                )

        issues_count = (
            len(orphan_templates)
            + len(missing_fid_templates)
            + len(ambiguous_families)
            + len(orphan_intake)
        )
        status = "ok" if issues_count == 0 else "degraded"

        result = {
            "status": status,
            "issues_count": issues_count,
            "registry": {
                "total": registry_total,
                "active": registry_active,
            },
            "templates": {
                "total": len(tpl_rows),
                "orphan_family_id": orphan_templates,
                "missing_family_id": missing_fid_templates,
                "ambiguous_families": ambiguous_families,
            },
            "intake": {
                "total": intake_total,
                "orphan_family_id": orphan_intake,
            },
        }
        logger.info(
            "product_families integrity check: status=%s issues=%d "
            "(orphan_tpl=%d missing_fid=%d ambig=%d orphan_intake=%d)",
            status,
            issues_count,
            len(orphan_templates),
            len(missing_fid_templates),
            len(ambiguous_families),
            len(orphan_intake),
        )
        return result
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error("Integrity check failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Integrity check failed: {str(e)}"
        )