from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.commercial_markup_policies import Commercial_markup_policies
from models.inventory_materials import Inventory_materials


VALID_SCOPE_TYPES: frozenset[str] = frozenset({"global", "category", "subcategory", "material"})
VALID_MARKUP_TYPES: frozenset[str] = frozenset({"percent", "fixed", "hybrid"})
VALID_ROUNDING_MODES: frozenset[str] = frozenset(
    {"none", "nearest_0_10", "nearest_0_50", "nearest_1", "nearest_5"}
)
VALID_STATUSES: frozenset[str] = frozenset({"draft", "active", "archived"})
VALID_APPLIES_TO: frozenset[str] = frozenset({"material_cost", "production_cost", "composite_cost"})

SCOPE_RANK: dict[str, int] = {
    "material": 0,
    "subcategory": 1,
    "category": 2,
    "global": 3,
}


COMMERCIAL_MARKUP_POLICY_CONFIG: Dict[str, Any] = {
    "scope_types": sorted(VALID_SCOPE_TYPES),
    "markup_types": sorted(VALID_MARKUP_TYPES),
    "rounding_modes": sorted(VALID_ROUNDING_MODES),
    "applies_to": sorted(VALID_APPLIES_TO),
    "statuses": sorted(VALID_STATUSES),
    "conflict_resolution": "material > subcategory > category > global; then lower priority value wins",
    "separation_notice": "Commercial markup policy is separate from Material Registry unit_cost.",
    "no_write_notice": "Dry-run only. No material, ProductSystem, quote, order, or CostEngine state is changed.",
}


class CommercialMarkupPolicyValidationError(ValueError):
    """Raised when a markup policy payload is invalid."""


def _round_value(value: float, mode: str) -> float:
    if mode == "none":
        return value
    if mode == "nearest_0_10":
        return round(value * 10.0) / 10.0
    if mode == "nearest_0_50":
        return round(value * 2.0) / 2.0
    if mode == "nearest_1":
        return round(value)
    if mode == "nearest_5":
        return round(value / 5.0) * 5.0
    return value


def _validate_policy_row(row: Commercial_markup_policies) -> None:
    if row.scope_type not in VALID_SCOPE_TYPES:
        raise CommercialMarkupPolicyValidationError(
            f"Invalid scope_type '{row.scope_type}'. Allowed: {sorted(VALID_SCOPE_TYPES)}"
        )
    if row.markup_type not in VALID_MARKUP_TYPES:
        raise CommercialMarkupPolicyValidationError(
            f"Invalid markup_type '{row.markup_type}'. Allowed: {sorted(VALID_MARKUP_TYPES)}"
        )
    if row.rounding_mode not in VALID_ROUNDING_MODES:
        raise CommercialMarkupPolicyValidationError(
            f"Invalid rounding_mode '{row.rounding_mode}'. Allowed: {sorted(VALID_ROUNDING_MODES)}"
        )
    if row.status not in VALID_STATUSES:
        raise CommercialMarkupPolicyValidationError(
            f"Invalid status '{row.status}'. Allowed: {sorted(VALID_STATUSES)}"
        )
    if row.applies_to not in VALID_APPLIES_TO:
        raise CommercialMarkupPolicyValidationError(
            f"Invalid applies_to '{row.applies_to}'. Allowed: {sorted(VALID_APPLIES_TO)}"
        )

    if row.markup_type in {"percent", "hybrid"}:
        if row.markup_percent is None:
            raise CommercialMarkupPolicyValidationError("markup_percent is required for percent/hybrid markup_type")
        if row.markup_percent < 0:
            raise CommercialMarkupPolicyValidationError("markup_percent must be >= 0")

    if row.markup_type in {"fixed", "hybrid"}:
        if row.markup_fixed is None:
            raise CommercialMarkupPolicyValidationError("markup_fixed is required for fixed/hybrid markup_type")
        if row.markup_fixed < 0:
            raise CommercialMarkupPolicyValidationError("markup_fixed must be >= 0")

    if row.markup_fixed is not None and row.markup_fixed > 0 and not (row.currency or "").strip():
        raise CommercialMarkupPolicyValidationError("currency is required when markup_fixed is used")

    if row.scope_type == "global" and row.scope_value != "global":
        raise CommercialMarkupPolicyValidationError("global scope requires scope_value='global'")


def _row_to_dict(row: Commercial_markup_policies) -> Dict[str, Any]:
    return {
        "id": row.id,
        "scope_type": row.scope_type,
        "scope_value": row.scope_value,
        "markup_type": row.markup_type,
        "markup_percent": row.markup_percent,
        "markup_fixed": row.markup_fixed,
        "currency": row.currency,
        "min_margin_amount": row.min_margin_amount,
        "rounding_mode": row.rounding_mode,
        "applies_to": row.applies_to,
        "status": row.status,
        "priority": row.priority,
        "notes": row.notes,
        "valid_from": row.valid_from.isoformat() if row.valid_from else None,
        "valid_to": row.valid_to.isoformat() if row.valid_to else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _is_currently_valid(now: datetime, row: Commercial_markup_policies) -> bool:
    if row.valid_from and row.valid_from > now:
        return False
    if row.valid_to and row.valid_to < now:
        return False
    return True


def _match_scope(row: Commercial_markup_policies, material: Inventory_materials) -> bool:
    if row.scope_type == "global":
        return row.scope_value == "global"
    if row.scope_type == "category":
        return (material.category or "") == row.scope_value
    if row.scope_type == "subcategory":
        return (material.subcategory or "") == row.scope_value
    if row.scope_type == "material":
        return material.code == row.scope_value
    return False


async def list_commercial_markup_policies(
    db: AsyncSession,
    *,
    status_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    stmt = select(Commercial_markup_policies)
    if status_filter:
        stmt = stmt.where(Commercial_markup_policies.status == status_filter)
    stmt = stmt.order_by(
        Commercial_markup_policies.scope_type,
        Commercial_markup_policies.scope_value,
        Commercial_markup_policies.priority.asc(),
        Commercial_markup_policies.id.asc(),
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_row_to_dict(row) for row in rows]


async def resolve_applicable_markup_policy(
    db: AsyncSession,
    *,
    material: Inventory_materials,
) -> Optional[Commercial_markup_policies]:
    now = datetime.now()
    rows = (
        await db.execute(
            select(Commercial_markup_policies).where(
                Commercial_markup_policies.status == "active"
            )
        )
    ).scalars().all()

    candidates: List[Commercial_markup_policies] = []
    for row in rows:
        _validate_policy_row(row)
        if not _is_currently_valid(now, row):
            continue
        if _match_scope(row, material):
            candidates.append(row)

    if not candidates:
        return None

    candidates.sort(
        key=lambda row: (
            SCOPE_RANK.get(row.scope_type, 99),
            row.priority,
            row.id,
        )
    )
    return candidates[0]


def _add_warning(warnings: List[Dict[str, str]], code: str, message: str) -> None:
    warnings.append({"code": code, "message": message})


async def dry_run_commercial_markup(
    db: AsyncSession,
    *,
    material_code: str,
    quantity: float = 1.0,
) -> Dict[str, Any]:
    row = (
        await db.execute(
            select(Inventory_materials).where(Inventory_materials.code == material_code)
        )
    ).scalar_one_or_none()
    if row is None:
        raise CommercialMarkupPolicyValidationError(f"inventory_material '{material_code}' not found")

    qty = quantity if quantity and quantity > 0 else 1.0
    warnings: List[Dict[str, str]] = []

    if row.status == "archived":
        _add_warning(warnings, "material_archived", "Material is archived")
    elif row.status != "active":
        _add_warning(warnings, "material_not_active", "Material is not active")

    missing_fields: List[str] = []
    if not row.unit:
        missing_fields.append("unit")
    if row.unit_cost is None or row.unit_cost <= 0:
        missing_fields.append("unit_cost")
    if not row.currency:
        missing_fields.append("currency")
    if row.vat_percent is None:
        missing_fields.append("vat_percent")
    if row.valid_from is None:
        missing_fields.append("valid_from")
    if missing_fields:
        _add_warning(
            warnings,
            "material_not_ready_for_pricing",
            f"Material missing pricing fields: {', '.join(missing_fields)}",
        )

    source_status = (row.source_review_status or "missing").strip().lower()
    if source_status not in {"reviewed", "accepted_override"}:
        _add_warning(
            warnings,
            "source_review_not_ready",
            f"Source review status is '{source_status or 'missing'}'",
        )

    policy = await resolve_applicable_markup_policy(db, material=row)
    if policy is None:
        _add_warning(warnings, "no_markup_policy", "No active commercial markup policy matches this material")

    unit_cost = float(row.unit_cost) if row.unit_cost is not None else None
    base_cost_total = float(unit_cost * qty) if unit_cost is not None else None

    markup_unit_amount: Optional[float] = None
    commercial_unit_price: Optional[float] = None
    markup_total: Optional[float] = None
    commercial_total: Optional[float] = None
    applied_policy: Optional[Dict[str, Any]] = None

    if unit_cost is not None and policy is not None:
        _validate_policy_row(policy)
        markup_unit_amount = 0.0
        if policy.markup_type in {"percent", "hybrid"}:
            markup_unit_amount += unit_cost * float(policy.markup_percent or 0.0) / 100.0
        if policy.markup_type in {"fixed", "hybrid"}:
            markup_unit_amount += float(policy.markup_fixed or 0.0)

        if policy.min_margin_amount is not None:
            markup_unit_amount = max(markup_unit_amount, float(policy.min_margin_amount))

        gross_unit_price = unit_cost + markup_unit_amount
        commercial_unit_price = _round_value(gross_unit_price, policy.rounding_mode)

        if policy.markup_type in {"fixed", "hybrid"} and policy.currency and row.currency and policy.currency != row.currency:
            _add_warning(
                warnings,
                "currency_mismatch",
                f"Policy currency '{policy.currency}' differs from material currency '{row.currency}'",
            )

        markup_total = (commercial_unit_price - unit_cost) * qty
        commercial_total = commercial_unit_price * qty
        applied_policy = {
            "id": policy.id,
            "scope_type": policy.scope_type,
            "scope_value": policy.scope_value,
            "markup_type": policy.markup_type,
            "markup_percent": policy.markup_percent,
            "markup_fixed": policy.markup_fixed,
            "currency": policy.currency,
            "rounding_mode": policy.rounding_mode,
            "applies_to": policy.applies_to,
            "priority": policy.priority,
            "status": policy.status,
        }

    return {
        "material_code": row.code,
        "material_name": row.name,
        "quantity": qty,
        "unit_cost": unit_cost,
        "currency": row.currency,
        "vat_percent": row.vat_percent,
        "vat_mode": "excluded",
        "base_cost_total": base_cost_total,
        "applied_policy": applied_policy,
        "markup_amount": markup_total,
        "commercial_unit_price": commercial_unit_price,
        "commercial_total_price": commercial_total,
        "warnings": warnings,
        "no_write_guarantee": True,
    }