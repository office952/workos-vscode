"""Admin service layer for the `inventory_materials` registry (Sprint #20.5).

Scope: ONLY the canonical status + unit_cost management needed to lift
stubs from `missing_price` to `active`.

Canonical invariant (mirrors `workcenter_rates_service`):
  - status must be one of VALID_STATUSES.
  - status == "active" requires unit_cost IS NOT NULL AND > 0.
  - unit_cost, when provided, must be >= 0.

This service is additive: it does NOT touch the legacy
`Inventory_materialsService` used by the generic `/api/v1/entities/...`
CRUD router. It operates by canonical `code`, not numeric `id`.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_manager
from models.inventory_material_price_history import Inventory_material_price_history
from models.inventory_material_source_review_audit import Inventory_material_source_review_audit
from models.inventory_materials import Inventory_materials
from services.inventory_sheet_format import validate_sheet_format_payload
from services.inventory_materials_governance import (
    CANONICAL_CATEGORIES,
    INTELLIGENCE_POLICY,
    get_canonical_category,
    infer_recommended_subcategory,
)

logger = logging.getLogger(__name__)

VALID_STATUSES: frozenset[str] = frozenset(
    {"active", "missing_price", "needs_owner_input", "archived"}
)
VALID_SOURCE_REVIEW_STATUSES: frozenset[str] = frozenset(INTELLIGENCE_POLICY["source_review_policy"]["statuses"])
DEFAULT_STALE_SOURCE_DAYS = 90


class InventoryMaterialValidationError(ValueError):
    """Raised when an inventory material row violates canonical invariants."""


def _normalize_price_field_value(field_name: str, value: Any) -> Any:
    if value is None:
        return None
    if field_name in {"unit_cost", "vat_percent"}:
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return str(value).strip()
    if field_name == "currency":
        return str(value).strip()
    if field_name == "valid_from":
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value).strip()
    return value


def _row_to_dict(row: Inventory_materials) -> Dict[str, Any]:
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "category": row.category,
        "subcategory": row.subcategory,
        "unit": row.unit,
        "unit_cost": row.unit_cost,
        "currency": row.currency,
        "vat_percent": row.vat_percent,
        "valid_from": row.valid_from.isoformat() if row.valid_from else None,
        "status": row.status,
        "supplier": row.supplier,
        "supplier_id": row.supplier_id,
        "source_name": row.source_name,
        "source_url": row.source_url,
        "source_checked_at": row.source_checked_at.isoformat() if row.source_checked_at else None,
        "source_notes": row.source_notes,
        "source_review_status": row.source_review_status,
        "source_reviewed_at": row.source_reviewed_at.isoformat() if row.source_reviewed_at else None,
        "source_reviewed_by": row.source_reviewed_by,
        "stock_current": row.stock_current,
        "stock_min": row.stock_min,
        "stock_max": row.stock_max,
        "sheet_format_type": row.sheet_format_type,
        "sheet_width": row.sheet_width,
        "sheet_height": row.sheet_height,
        "sheet_unit": row.sheet_unit,
        "sheet_thickness": row.sheet_thickness,
        "sheet_thickness_unit": row.sheet_thickness_unit,
        "usable_width": row.usable_width,
        "usable_height": row.usable_height,
        "format_source": row.format_source,
        "format_verified": row.format_verified,
        "format_notes": row.format_notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def validate_status_and_cost(
    status: str,
    unit_cost: Optional[float],
    currency: Optional[str] = None,
    vat_percent: Optional[float] = None,
    valid_from: Optional[datetime] = None,
) -> None:
    """Enforce the canonical invariant.

    Rules:
      - status must be in VALID_STATUSES.
      - status == "active" requires unit_cost > 0.
      - unit_cost, when provided, must be >= 0.
    """
    if status not in VALID_STATUSES:
        raise InventoryMaterialValidationError(
            f"Invalid status '{status}'. Allowed: {sorted(VALID_STATUSES)}"
        )
    if unit_cost is not None and unit_cost < 0:
        raise InventoryMaterialValidationError(
            "unit_cost must be a non-negative number when provided"
        )
    if status == "active":
        if unit_cost is None or unit_cost <= 0:
            raise InventoryMaterialValidationError(
                "status='active' requires a non-null, positive unit_cost"
            )
        if not str(currency or "").strip():
            raise InventoryMaterialValidationError(
                "status='active' requires non-empty currency"
            )
        if vat_percent is None:
            raise InventoryMaterialValidationError(
                "status='active' requires vat_percent"
            )
        if valid_from is None:
            raise InventoryMaterialValidationError(
                "status='active' requires valid_from"
            )
        if vat_percent < 0 or vat_percent > 100:
            raise InventoryMaterialValidationError(
                "status='active' requires vat_percent in [0, 100]"
            )


def _is_price_governed_change(
    row: Inventory_materials,
    *,
    unit_cost: Optional[float],
    currency: Optional[str],
    vat_percent: Optional[float],
    valid_from: Optional[datetime],
    provided_fields: Optional[set[str]] = None,
) -> bool:
    updates: Dict[str, Any] = {
        "unit_cost": unit_cost,
        "currency": currency,
        "vat_percent": vat_percent,
        "valid_from": valid_from,
    }
    governed_fields = tuple(updates.keys())
    explicit_fields = set(provided_fields or [])
    explicit_mode = provided_fields is not None

    for field_name in governed_fields:
        if explicit_mode and field_name not in explicit_fields:
            continue
        incoming = updates[field_name]
        if not explicit_mode and incoming is None:
            continue

        current_value = getattr(row, field_name)
        if _normalize_price_field_value(field_name, current_value) != _normalize_price_field_value(
            field_name, incoming
        ):
            return True

    return False


def _is_source_stale(source_checked_at: Optional[datetime], stale_days: int = DEFAULT_STALE_SOURCE_DAYS) -> bool:
    if source_checked_at is None:
        return True
    now = datetime.now(source_checked_at.tzinfo) if source_checked_at.tzinfo else datetime.now()
    age_days = (now - source_checked_at).days
    return age_days > stale_days


def _derive_source_review_status(
    *,
    source_name: Optional[str],
    source_url: Optional[str],
    source_checked_at: Optional[datetime],
) -> str:
    has_name = bool(str(source_name or "").strip())
    has_url = bool(str(source_url or "").strip())
    if not has_name or not has_url:
        return "missing"
    if source_checked_at is None:
        return "needs_review"
    if _is_source_stale(source_checked_at):
        return "stale"
    return "needs_review"


def _normalize_source_review_status(
    incoming: Optional[str],
    *,
    source_name: Optional[str],
    source_url: Optional[str],
    source_checked_at: Optional[datetime],
    existing_status: Optional[str],
) -> str:
    if incoming is not None:
        normalized = str(incoming).strip().lower()
        if normalized not in VALID_SOURCE_REVIEW_STATUSES:
            raise InventoryMaterialValidationError(
                f"Invalid source_review_status '{incoming}'. Allowed: {sorted(VALID_SOURCE_REVIEW_STATUSES)}"
            )
        if normalized == "missing":
            return _derive_source_review_status(
                source_name=source_name,
                source_url=source_url,
                source_checked_at=source_checked_at,
            )
        return normalized

    existing = str(existing_status or "").strip().lower()
    if existing in {"reviewed", "accepted_override"}:
        return existing

    return _derive_source_review_status(
        source_name=source_name,
        source_url=source_url,
        source_checked_at=source_checked_at,
    )


def _make_source_review_audit_payload(
    *,
    row: Inventory_materials,
    old_status: Optional[str],
    new_status: Optional[str],
    old_source_checked_at: Optional[datetime],
    old_source_url: Optional[str],
    old_source_name: Optional[str],
    old_source_notes: Optional[str],
    reason: Optional[str],
    actor: Optional[str],
) -> Inventory_material_source_review_audit:
    return Inventory_material_source_review_audit(
        material_id=row.id,
        material_code=row.code,
        old_status=old_status,
        new_status=new_status,
        old_source_checked_at=old_source_checked_at,
        new_source_checked_at=row.source_checked_at,
        old_source_url=old_source_url,
        new_source_url=row.source_url,
        old_source_name=old_source_name,
        new_source_name=row.source_name,
        old_source_notes=old_source_notes,
        new_source_notes=row.source_notes,
        reason=reason,
        actor=actor,
    )


def _build_category_cleanup_issue(
    row: Inventory_materials,
) -> Optional[Dict[str, Any]]:
    canonical_category = get_canonical_category(row.category)
    suggested_subcategory = infer_recommended_subcategory(
        code=row.code,
        name=row.name,
        category=row.category,
        canonical_category=canonical_category,
    )

    issues: list[str] = []
    reason_parts: list[str] = []

    if canonical_category is None:
        issues.append("category_non_canonical")
        reason_parts.append("category is not canonical")
    elif row.category != canonical_category:
        issues.append("category_normalization_needed")
        reason_parts.append(f"category should normalize to {canonical_category}")

    if not str(row.subcategory or "").strip():
        issues.append("subcategory_missing")
        reason_parts.append("subcategory missing")
    elif suggested_subcategory and row.subcategory != suggested_subcategory:
        issues.append("subcategory_inconsistent")
        reason_parts.append(f"subcategory differs from suggested {suggested_subcategory}")

    product_reasons = []
    if row.status != "active":
        product_reasons.append("material not active")
    if row.status == "archived":
        product_reasons.append("material archived")
    if not canonical_category:
        product_reasons.append("invalid category policy")
    if not str(row.unit or "").strip():
        product_reasons.append("missing unit")
    if not row.source_review_status or str(row.source_review_status).strip().lower() not in {"reviewed", "accepted_override"}:
        product_reasons.append("source review missing or stale")

    if not issues and not product_reasons:
        return None

    if product_reasons and "productsystem_blocked" not in issues:
        issues.append("productsystem_blocked")
        reason_parts.append("ProductSystem readiness is blocked")

    return {
        "material_id": row.id,
        "code": row.code,
        "name": row.name,
        "current_category": row.category,
        "suggested_category": canonical_category,
        "current_subcategory": row.subcategory,
        "suggested_subcategory": suggested_subcategory,
        "issue_type": issues[0] if len(issues) == 1 else "multiple",
        "issues": issues,
        "reason": "; ".join(reason_parts),
        "would_change": bool(canonical_category and row.category != canonical_category) or bool(
            suggested_subcategory and row.subcategory != suggested_subcategory
        ),
        "safe_to_apply": bool(canonical_category and row.unit and row.status != "archived"),
        "product_system_blocked": bool(product_reasons),
        "product_system_reasons": product_reasons,
    }


async def list_inventory_materials_admin(
    db: AsyncSession, *, status_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return every inventory material row as a serialized dict, ordered by code."""
    stmt = select(Inventory_materials).order_by(Inventory_materials.code)
    if status_filter is not None:
        stmt = stmt.where(Inventory_materials.status == status_filter)
    rows = (await db.execute(stmt)).scalars().all()
    return [_row_to_dict(r) for r in rows]


async def get_inventory_material_by_code(
    db: AsyncSession, code: str
) -> Optional[Dict[str, Any]]:
    row = (
        await db.execute(
            select(Inventory_materials).where(Inventory_materials.code == code)
        )
    ).scalar_one_or_none()
    return _row_to_dict(row) if row else None


async def patch_inventory_material_by_code(
    db: AsyncSession,
    code: str,
    *,
    unit_cost: Optional[float] = None,
    currency: Optional[str] = None,
    vat_percent: Optional[float] = None,
    valid_from: Optional[datetime] = None,
    status: Optional[str] = None,
    supplier: Optional[str] = None,
    supplier_id: Optional[int] = None,
    source_name: Optional[str] = None,
    source_url: Optional[str] = None,
    source_checked_at: Optional[datetime] = None,
    source_notes: Optional[str] = None,
    source_review_status: Optional[str] = None,
    source_reviewed_at: Optional[datetime] = None,
    source_reviewed_by: Optional[str] = None,
    name: Optional[str] = None,
    subcategory: Optional[str] = None,
    change_reason: Optional[str] = None,
    changed_by: Optional[str] = None,
    snapshot_source: Optional[str] = "admin_patch",
    sheet_format_type: Optional[str] = None,
    sheet_width: Optional[float] = None,
    sheet_height: Optional[float] = None,
    sheet_unit: Optional[str] = None,
    sheet_thickness: Optional[float] = None,
    sheet_thickness_unit: Optional[str] = None,
    usable_width: Optional[float] = None,
    usable_height: Optional[float] = None,
    format_source: Optional[str] = None,
    format_verified: Optional[bool] = None,
    format_notes: Optional[str] = None,
    provided_fields: Optional[set[str]] = None,
) -> Optional[Dict[str, Any]]:
    """PATCH an inventory material by canonical code.

    Only provided (non-None) fields are applied. The combined
    (status, unit_cost) end-state is validated against the canonical
    invariant before commit.
    """
    row = (
        await db.execute(
            select(Inventory_materials).where(Inventory_materials.code == code)
        )
    ).scalar_one_or_none()
    if row is None:
        return None

    explicit_fields = set(provided_fields or [])

    def _is_supplied(field_name: str, incoming: Any) -> bool:
        if provided_fields is not None:
            return field_name in explicit_fields
        return incoming is not None

    old_source_status = row.source_review_status
    old_source_checked_at = row.source_checked_at
    old_source_url = row.source_url
    old_source_name = row.source_name
    old_source_notes = row.source_notes

    new_status = status if status is not None else (row.status or "missing_price")
    new_cost = unit_cost if _is_supplied("unit_cost", unit_cost) else row.unit_cost
    new_currency = currency if _is_supplied("currency", currency) else row.currency
    new_vat_percent = vat_percent if _is_supplied("vat_percent", vat_percent) else row.vat_percent
    new_valid_from = valid_from if _is_supplied("valid_from", valid_from) else row.valid_from
    validate_status_and_cost(new_status, new_cost, new_currency, new_vat_percent, new_valid_from)

    next_source_name = source_name if _is_supplied("source_name", source_name) else row.source_name
    next_source_url = source_url if _is_supplied("source_url", source_url) else row.source_url
    next_source_checked_at = (
        source_checked_at if _is_supplied("source_checked_at", source_checked_at) else row.source_checked_at
    )
    next_source_notes = source_notes if _is_supplied("source_notes", source_notes) else row.source_notes
    next_review_status = _normalize_source_review_status(
        source_review_status,
        source_name=next_source_name,
        source_url=next_source_url,
        source_checked_at=next_source_checked_at,
        existing_status=row.source_review_status,
    )

    if next_review_status == "accepted_override" and not str(next_source_notes or "").strip():
        raise InventoryMaterialValidationError(
            "source_review_status='accepted_override' requires source_notes"
        )

    should_write_history = _is_price_governed_change(
        row,
        unit_cost=unit_cost,
        currency=currency,
        vat_percent=vat_percent,
        valid_from=valid_from,
        provided_fields=provided_fields,
    )

    normalized_change_reason = str(change_reason or "").strip()
    if should_write_history and not normalized_change_reason:
        raise InventoryMaterialValidationError(
            "price-governed changes require non-empty change_reason"
        )

    merged_sheet = {
        "sheet_format_type": sheet_format_type if sheet_format_type is not None else row.sheet_format_type,
        "sheet_width": sheet_width if sheet_width is not None else row.sheet_width,
        "sheet_height": sheet_height if sheet_height is not None else row.sheet_height,
        "sheet_unit": sheet_unit if sheet_unit is not None else row.sheet_unit,
        "sheet_thickness": sheet_thickness if sheet_thickness is not None else row.sheet_thickness,
        "sheet_thickness_unit": (
            sheet_thickness_unit if sheet_thickness_unit is not None else row.sheet_thickness_unit
        ),
        "usable_width": usable_width if usable_width is not None else row.usable_width,
        "usable_height": usable_height if usable_height is not None else row.usable_height,
        "format_source": format_source if format_source is not None else row.format_source,
        "format_verified": format_verified if format_verified is not None else row.format_verified,
        "format_notes": format_notes if format_notes is not None else row.format_notes,
    }
    validate_sheet_format_payload(merged_sheet)

    if _is_supplied("unit_cost", unit_cost):
        row.unit_cost = unit_cost
    if _is_supplied("currency", currency):
        row.currency = currency
    if _is_supplied("vat_percent", vat_percent):
        row.vat_percent = vat_percent
    if _is_supplied("valid_from", valid_from):
        row.valid_from = valid_from
    if status is not None:
        row.status = status
    if supplier is not None:
        row.supplier = supplier
    if supplier_id is not None:
        row.supplier_id = supplier_id
    if source_name is not None:
        row.source_name = source_name
    if source_url is not None:
        row.source_url = source_url
    if source_checked_at is not None:
        row.source_checked_at = source_checked_at
    if source_notes is not None:
        row.source_notes = source_notes
    if _is_supplied("subcategory", subcategory):
        row.subcategory = subcategory

    source_review_status_changed = False
    if source_review_status is not None:
        source_review_status_changed = next_review_status != old_source_status
        row.source_review_status = next_review_status
        if next_review_status in {"reviewed", "accepted_override"}:
            row.source_reviewed_at = source_reviewed_at or datetime.now()
            row.source_reviewed_by = source_reviewed_by or changed_by
        else:
            row.source_reviewed_at = source_reviewed_at
            row.source_reviewed_by = source_reviewed_by
    elif any(
        _is_supplied(name, value)
        for name, value in (
            ("source_name", source_name),
            ("source_url", source_url),
            ("source_checked_at", source_checked_at),
            ("source_notes", source_notes),
        )
    ):
        row.source_review_status = next_review_status
        if next_review_status not in {"reviewed", "accepted_override"}:
            row.source_reviewed_at = None
            row.source_reviewed_by = None
    if name is not None:
        row.name = name
    if sheet_format_type is not None:
        row.sheet_format_type = sheet_format_type
    if sheet_width is not None:
        row.sheet_width = sheet_width
    if sheet_height is not None:
        row.sheet_height = sheet_height
    if sheet_unit is not None:
        row.sheet_unit = sheet_unit
    if sheet_thickness is not None:
        row.sheet_thickness = sheet_thickness
    if sheet_thickness_unit is not None:
        row.sheet_thickness_unit = sheet_thickness_unit
    if usable_width is not None:
        row.usable_width = usable_width
    if usable_height is not None:
        row.usable_height = usable_height
    if format_source is not None:
        row.format_source = format_source
    if format_verified is not None:
        row.format_verified = format_verified
    if format_notes is not None:
        row.format_notes = format_notes

    if should_write_history:
        db.add(
            Inventory_material_price_history(
                material_id=row.id,
                unit_cost=row.unit_cost,
                currency=row.currency,
                vat_percent=row.vat_percent,
                valid_from=row.valid_from,
                changed_by=changed_by,
                change_reason=normalized_change_reason,
                snapshot_source=snapshot_source,
            )
        )

    if source_review_status_changed:
        db.add(
            _make_source_review_audit_payload(
                row=row,
                old_status=old_source_status,
                new_status=row.source_review_status,
                old_source_checked_at=old_source_checked_at,
                old_source_url=old_source_url,
                old_source_name=old_source_name,
                old_source_notes=old_source_notes,
                reason=normalized_change_reason or None,
                actor=changed_by,
            )
        )

    await db.commit()
    await db.refresh(row)
    logger.info(
        "inventory_material updated: code=%s status=%s unit_cost=%s",
        code,
        row.status,
        row.unit_cost,
    )
    return _row_to_dict(row)


async def get_inventory_material_source_review_audit(
    db: AsyncSession,
    *,
    code: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    material = (
        await db.execute(select(Inventory_materials).where(Inventory_materials.code == code))
    ).scalar_one_or_none()
    if material is None:
        return []

    stmt = (
        select(Inventory_material_source_review_audit)
        .where(Inventory_material_source_review_audit.material_id == material.id)
        .order_by(Inventory_material_source_review_audit.created_at.desc())
        .limit(max(1, min(limit, 500)))
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": r.id,
            "material_id": r.material_id,
            "material_code": r.material_code,
            "old_status": r.old_status,
            "new_status": r.new_status,
            "old_source_checked_at": r.old_source_checked_at.isoformat() if r.old_source_checked_at else None,
            "new_source_checked_at": r.new_source_checked_at.isoformat() if r.new_source_checked_at else None,
            "old_source_url": r.old_source_url,
            "new_source_url": r.new_source_url,
            "old_source_name": r.old_source_name,
            "new_source_name": r.new_source_name,
            "old_source_notes": r.old_source_notes,
            "new_source_notes": r.new_source_notes,
            "reason": r.reason,
            "actor": r.actor,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


async def preview_category_cleanup(
    db: AsyncSession,
    *,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    rows = (
        await db.execute(select(Inventory_materials).order_by(Inventory_materials.code))
    ).scalars().all()
    out: List[Dict[str, Any]] = []
    for row in rows[: max(1, min(limit, 500))]:
        item = _build_category_cleanup_issue(row)
        if item is not None:
            out.append(item)
    return out


async def get_inventory_material_price_history(
    db: AsyncSession,
    *,
    code: Optional[str] = None,
    material_id: Optional[int] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Read-only history rows ordered newest-first.

    Accepts either material code or material_id.
    """
    if material_id is None:
        if not code:
            return []
        material_row = (
            await db.execute(
                select(Inventory_materials).where(Inventory_materials.code == code)
            )
        ).scalar_one_or_none()
        if material_row is None:
            return []
        material_id = int(material_row.id)

    stmt = (
        select(Inventory_material_price_history)
        .where(Inventory_material_price_history.material_id == material_id)
        .order_by(Inventory_material_price_history.changed_at.desc())
        .limit(max(1, min(limit, 500)))
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": r.id,
            "material_id": r.material_id,
            "unit_cost": r.unit_cost,
            "currency": r.currency,
            "vat_percent": r.vat_percent,
            "valid_from": r.valid_from.isoformat() if r.valid_from else None,
            "changed_at": r.changed_at.isoformat() if r.changed_at else None,
            "changed_by": r.changed_by,
            "change_reason": r.change_reason,
            "snapshot_source": r.snapshot_source,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# BLK-18 — Material cost bridge (mirrors load_workcenter_rate_dict)
# ---------------------------------------------------------------------------

async def load_material_pricing_dict(
    db: Optional[AsyncSession] = None,
) -> Dict[str, Dict[str, Any]]:
    """Rich bridge: {material_code: {unit_cost, currency, source}} for active rows.

    Same inclusion rules as load_material_cost_dict. Currency metadata is
    preserved for base-currency validation at the CostEngine boundary.
    """
    owns_session = db is None
    if owns_session:
        session_ctx = db_manager.async_session_maker()
        session = await session_ctx.__aenter__()
    else:
        session = db  # type: ignore[assignment]
        session_ctx = None

    try:
        rows = (
            await session.execute(
                select(Inventory_materials).where(
                    Inventory_materials.status == "active"
                )
            )
        ).scalars().all()
        out: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            if (
                r.unit_cost is not None
                and r.unit_cost > 0
                and str(r.currency or "").strip()
                and r.vat_percent is not None
                and r.valid_from is not None
            ):
                out[r.code] = {
                    "unit_cost": float(r.unit_cost),
                    "currency": str(r.currency).strip().upper(),
                    "source": "inventory_materials",
                }
        return out
    finally:
        if owns_session and session_ctx is not None:
            await session_ctx.__aexit__(None, None, None)


async def load_material_cost_dict(
    db: Optional[AsyncSession] = None,
) -> Dict[str, float]:
    """Canonical bridge: returns {material_code: unit_cost} for active rows.

        Returns ONLY rows where:
            - status == "active"
            - unit_cost IS NOT NULL AND > 0
            - currency IS NOT NULL/empty
            - vat_percent IS NOT NULL
            - valid_from IS NOT NULL

        Incomplete active rows are excluded to preserve strict missing-rate
        blocking semantics in the quote/cost bridge.

    BLK-18 ships this function AND wires it into the QuoteOrchestrator
    via `create_with_registry()`.
    """
    pricing = await load_material_pricing_dict(db)
    return {code: row["unit_cost"] for code, row in pricing.items()}