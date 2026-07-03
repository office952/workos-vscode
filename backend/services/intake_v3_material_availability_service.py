"""Intake V3 read-only material availability preview — no inventory mutation."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_materials import Inventory_materials
from models.orders import Orders
from schemas.intake_v3 import (
    AVAILABILITY_SCOPE_READ_ONLY,
    FinishAssignment,
    IntakeV3MaterialAvailabilityBoundary,
    IntakeV3MaterialAvailabilityMatch,
    IntakeV3MaterialAvailabilityQuantity,
    IntakeV3MaterialAvailabilityResponse,
    IntakeV3MaterialAvailabilityRow,
    IntakeV3MaterialAvailabilitySummary,
    IntakeV3MaterialAvailabilityWarning,
    IntakeV3MaterialQuantityRow,
)
from services.intake_v3_material_quantity_breakdown_service import (
    Iv3SourceContext,
    extract_finish_assignments,
    extract_geometry_summary,
    load_iv3_source_context,
    resolve_material_quantity_rows,
    resolve_registry_code_for_row,
)
from services.intake_v3_real_commercial_quote_creation_service import INTAKE_V3_SOURCE_MODULE

AVAILABILITY_SCOPE = AVAILABILITY_SCOPE_READ_ONLY

STOCK_TRACKED_KEYS = frozenset(
    {
        "plexiglas_face",
        "forex_backing",
        "face_vinyl",
        "aluminum_return",
        "led_modules",
        "led_power_supply",
    }
)

INDIRECT_CONSUMABLE_POLICY_ROWS: list[dict[str, str]] = [
    {
        "material_key": "mounting_cables",
        "display_name": "Cabluri montaj / alimentare",
        "category": "indirect_consumable",
        "material_intent": "indirect_consumable.cables",
    },
    {
        "material_key": "electrical_connectors",
        "display_name": "Conectori electrici",
        "category": "indirect_consumable",
        "material_intent": "indirect_consumable.connectors",
    },
    {
        "material_key": "mounting_screws",
        "display_name": "Suruburi montaj",
        "category": "indirect_consumable",
        "material_intent": "indirect_consumable.screws",
    },
    {
        "material_key": "silicone_sealant",
        "display_name": "Silicon etansare",
        "category": "indirect_consumable",
        "material_intent": "indirect_consumable.silicone",
    },
]

UNIT_ALIASES: dict[str, frozenset[str]] = {
    "m2": frozenset({"m2", "mp", "sqm", "m²"}),
    "ml": frozenset({"ml", "m", "lm"}),
    "buc": frozenset({"buc", "pcs", "bucati", "piece", "pieces"}),
    "placa": frozenset({"placa", "sheet", "tabla"}),
}


def _boundary() -> IntakeV3MaterialAvailabilityBoundary:
    return IntakeV3MaterialAvailabilityBoundary()


def _warning(code: str, message: str, *, source: str, severity: str = "warning") -> IntakeV3MaterialAvailabilityWarning:
    return IntakeV3MaterialAvailabilityWarning(
        code=code,
        severity=severity,
        message=message,
        source=source,
    )


def normalize_material_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    raw = str(unit).strip().lower().replace("²", "2")
    for canonical, aliases in UNIT_ALIASES.items():
        if raw == canonical or raw in aliases:
            return canonical
    return raw


def _units_compatible(required_unit: str | None, inventory_unit: str | None) -> bool:
    req = normalize_material_unit(required_unit)
    inv = normalize_material_unit(inventory_unit)
    if req is None or inv is None:
        return False
    if req == inv:
        return True
    if req == "m2" and inv == "placa":
        return True
    return False


def _sheet_area_m2(material: Inventory_materials) -> float | None:
    if not material.format_verified:
        return None
    width = material.usable_width or material.sheet_width
    height = material.usable_height or material.sheet_height
    if width is None or height is None or width <= 0 or height <= 0:
        return None
    sheet_unit = normalize_material_unit(material.sheet_unit)
    if sheet_unit == "mm":
        return (float(width) * float(height)) / 1_000_000.0
    if sheet_unit == "m":
        return float(width) * float(height)
    if sheet_unit == "cm":
        return (float(width) * float(height)) / 10_000.0
    return None


def _available_quantity_in_required_unit(
    material: Inventory_materials,
    required_unit: str,
) -> tuple[float | None, str | None, str]:
    stock = material.stock_current
    if stock is None:
        return None, normalize_material_unit(material.unit), "stock_missing"

    inv_unit = normalize_material_unit(material.unit)
    req_unit = normalize_material_unit(required_unit)
    if req_unit is None:
        return None, inv_unit, "required_unit_unknown"

    if inv_unit == req_unit:
        return float(stock), inv_unit, "direct"

    if req_unit == "m2" and inv_unit == "placa":
        area = _sheet_area_m2(material)
        if area is None:
            return None, inv_unit, "sheet_format_unverified"
        return float(stock) * area, "m2", "sheet_to_m2"

    return None, inv_unit, "incompatible"


def compare_required_vs_available(
    required: float,
    required_unit: str,
    material: Inventory_materials | None,
) -> tuple[float | None, float | None, str, str]:
    if material is None:
        return None, None, "not_applicable", "no_inventory_match"
    if not _units_compatible(required_unit, material.unit):
        return None, None, "incompatible", "unit_mismatch"

    available, available_unit, conversion = _available_quantity_in_required_unit(material, required_unit)
    if available is None:
        return None, None, "manual_check" if conversion in {"incompatible", "sheet_format_unverified"} else "not_applicable", conversion

    shortage = max(0.0, round(required - available, 6))
    return available, shortage if shortage > 0 else 0.0, "compatible", conversion


async def load_inventory_material_candidates(
    db: AsyncSession,
    *,
    registry_code: str | None = None,
    display_name: str | None = None,
) -> list[Inventory_materials]:
    if registry_code:
        row = await db.scalar(select(Inventory_materials).where(Inventory_materials.code == registry_code))
        return [row] if row is not None else []

    if not display_name:
        return []

    name_norm = display_name.strip().lower()
    rows = list(await db.scalars(select(Inventory_materials)))
    exact = [row for row in rows if row.name.strip().lower() == name_norm]
    if exact:
        return exact
    partial = [row for row in rows if name_norm in row.name.strip().lower()]
    return partial


def match_breakdown_material_to_inventory(
    *,
    registry_code: str | None,
    display_name: str,
    candidates: list[Inventory_materials],
) -> tuple[Inventory_materials | None, IntakeV3MaterialAvailabilityMatch, list[str]]:
    warnings: list[str] = []
    if registry_code and len(candidates) == 1 and candidates[0].code == registry_code:
        material = candidates[0]
        return material, IntakeV3MaterialAvailabilityMatch(
            match_strategy="code",
            confidence="high",
            inventory_material_id=material.id,
            inventory_code=material.code,
            inventory_name=material.name,
            inventory_unit=material.unit,
            inventory_status=material.status,
            source_review_status=material.source_review_status,
        ), warnings

    if registry_code and not candidates:
        warnings.append("no_registry_code_match")
        return None, IntakeV3MaterialAvailabilityMatch(
            match_strategy="none",
            confidence="low",
        ), warnings

    if len(candidates) > 1:
        warnings.append("ambiguous_inventory_match")
        return None, IntakeV3MaterialAvailabilityMatch(
            match_strategy="ambiguous",
            confidence="low",
            inventory_code=candidates[0].code,
            inventory_name=candidates[0].name,
        ), warnings

    if len(candidates) == 1:
        material = candidates[0]
        return material, IntakeV3MaterialAvailabilityMatch(
            match_strategy="name",
            confidence="medium",
            inventory_material_id=material.id,
            inventory_code=material.code,
            inventory_name=material.name,
            inventory_unit=material.unit,
            inventory_status=material.status,
            source_review_status=material.source_review_status,
        ), warnings

    warnings.append("no_inventory_match")
    return None, IntakeV3MaterialAvailabilityMatch(
        match_strategy="none",
        confidence="low",
    ), warnings


def _recommended_action(status: str) -> tuple[str, bool, bool]:
    if status == "available":
        return "verify_stock_if_needed", False, False
    if status == "shortage":
        return "manual_procurement_recommended", True, True
    if status == "indirect_consumable":
        return "manual_check_indirect_consumable", True, True
    if status in {"manual_check", "ambiguous_match", "no_match", "unknown"}:
        return "manual_check_required", True, True
    if status == "not_tracked":
        return "not_stock_tracked", True, False
    return "manual_check_required", True, True


def build_material_availability_row(
    breakdown_row: IntakeV3MaterialQuantityRow,
    material: Inventory_materials | None,
    match: IntakeV3MaterialAvailabilityMatch,
    row_warnings: list[str],
    finish: FinishAssignment | None,
) -> IntakeV3MaterialAvailabilityRow:
    registry_code, material_intent = resolve_registry_code_for_row(breakdown_row.material_key, finish)
    required = breakdown_row.quantity_with_waste or breakdown_row.quantity
    if not breakdown_row.included or breakdown_row.quantity_quality in {"missing", "not_applicable"}:
        quantity = IntakeV3MaterialAvailabilityQuantity(
            required=breakdown_row.quantity,
            required_unit=breakdown_row.unit,
            required_with_waste=breakdown_row.quantity_with_waste or None,
            unit_comparison="not_applicable",
        )
        return IntakeV3MaterialAvailabilityRow(
            material_key=breakdown_row.material_key,
            display_name=breakdown_row.display_name,
            category=breakdown_row.category,
            registry_code=registry_code or breakdown_row.registry_code,
            material_intent=material_intent or breakdown_row.material_intent,
            tracking_class="stock_tracked",
            availability_status="manual_check",
            recommended_action="manual_check_required",
            requires_operator_verification=True,
            recommends_manual_procurement=False,
            match=match,
            quantity=quantity,
            warnings=row_warnings + ["missing_required_quantity"],
        )

    available, shortage, unit_comparison, _conversion = compare_required_vs_available(
        float(required),
        breakdown_row.unit,
        material,
    )

    status = "unknown"
    if match.match_strategy == "ambiguous":
        status = "ambiguous_match"
    elif match.match_strategy == "none" or material is None:
        status = "no_match"
    elif unit_comparison == "incompatible":
        status = "manual_check"
        row_warnings.append("unit_incompatible")
    elif unit_comparison in {"sheet_format_unverified", "stock_missing"}:
        status = "manual_check"
        row_warnings.append(unit_comparison)
    elif available is not None and (shortage or 0) > 0:
        status = "shortage"
    elif available is not None:
        status = "available"
    else:
        status = "manual_check"

    action, requires_operator, recommends_procurement = _recommended_action(status)
    return IntakeV3MaterialAvailabilityRow(
        material_key=breakdown_row.material_key,
        display_name=breakdown_row.display_name,
        category=breakdown_row.category,
        registry_code=registry_code or breakdown_row.registry_code,
        material_intent=material_intent or breakdown_row.material_intent,
        tracking_class="stock_tracked",
        availability_status=status,
        recommended_action=action,
        requires_operator_verification=requires_operator,
        recommends_manual_procurement=recommends_procurement,
        match=match,
        quantity=IntakeV3MaterialAvailabilityQuantity(
            required=breakdown_row.quantity,
            required_unit=breakdown_row.unit,
            required_with_waste=breakdown_row.quantity_with_waste or None,
            available=available,
            available_unit=normalize_material_unit(material.unit) if material else None,
            shortage=shortage,
            unit_comparison=unit_comparison,
        ),
        warnings=row_warnings,
    )


def _indirect_policy_row(policy: dict[str, str]) -> IntakeV3MaterialAvailabilityRow:
    action, requires_operator, recommends_procurement = _recommended_action("indirect_consumable")
    return IntakeV3MaterialAvailabilityRow(
        material_key=policy["material_key"],
        display_name=policy["display_name"],
        category=policy["category"],
        registry_code=None,
        material_intent=policy["material_intent"],
        tracking_class="indirect_consumable",
        availability_status="indirect_consumable",
        recommended_action=action,
        requires_operator_verification=requires_operator,
        recommends_manual_procurement=recommends_procurement,
        match=IntakeV3MaterialAvailabilityMatch(match_strategy="policy", confidence="low"),
        quantity=IntakeV3MaterialAvailabilityQuantity(
            required=0.0,
            required_unit="policy",
            unit_comparison="not_applicable",
        ),
        warnings=["indirect_consumable_policy_row"],
    )


def build_material_availability_summary(
    rows: list[IntakeV3MaterialAvailabilityRow],
) -> IntakeV3MaterialAvailabilitySummary:
    counts = {
        "available": 0,
        "shortage": 0,
        "manual_check": 0,
        "indirect_consumable": 0,
        "no_match": 0,
        "ambiguous_match": 0,
        "not_tracked": 0,
        "unknown": 0,
    }
    for row in rows:
        key = row.availability_status
        if key not in counts:
            key = "unknown"
        counts[key] += 1

    if counts["shortage"] > 0:
        overall = "shortage"
    elif counts["manual_check"] + counts["no_match"] + counts["ambiguous_match"] > 0:
        overall = "manual_check"
    elif counts["available"] > 0 and sum(counts.values()) == counts["available"] + counts["indirect_consumable"]:
        overall = "available"
    elif counts["indirect_consumable"] == len(rows) and rows:
        overall = "indirect_consumable"
    elif rows:
        overall = "mixed"
    else:
        overall = "unknown"

    return IntakeV3MaterialAvailabilitySummary(
        total_rows=len(rows),
        available_count=counts["available"],
        shortage_count=counts["shortage"],
        manual_check_count=counts["manual_check"],
        indirect_consumables_count=counts["indirect_consumable"],
        no_match_count=counts["no_match"],
        ambiguous_match_count=counts["ambiguous_match"],
        not_tracked_count=counts["not_tracked"],
        unknown_count=counts["unknown"],
        overall_status=overall,
    )


def build_material_availability_warnings(
    *,
    material_breakdown_available: bool,
    rows: list[IntakeV3MaterialAvailabilityRow],
) -> list[IntakeV3MaterialAvailabilityWarning]:
    warnings: list[IntakeV3MaterialAvailabilityWarning] = []
    if not material_breakdown_available:
        warnings.append(
            _warning(
                "material_breakdown_missing",
                "Material breakdown unavailable — availability preview is incomplete.",
                source="material_breakdown",
            )
        )
    if any(row.availability_status == "shortage" for row in rows):
        warnings.append(
            _warning(
                "material_shortage_detected",
                "One or more stock-tracked materials show an estimated shortage.",
                source="inventory_comparison",
            )
        )
    if any(
        row.availability_status in {"manual_check", "no_match", "ambiguous_match", "unknown"}
        for row in rows
        if row.tracking_class == "stock_tracked"
    ):
        warnings.append(
            _warning(
                "material_manual_check_required",
                "Manual stock verification required for one or more materials.",
                source="inventory_comparison",
            )
        )
    return warnings


async def load_material_breakdown_rows(
    context: Iv3SourceContext,
) -> tuple[list[IntakeV3MaterialQuantityRow], bool, FinishAssignment | None]:
    if not context.is_intake_v3:
        return [], False, None
    geometry_summary, _ = extract_geometry_summary(context)
    finish = extract_finish_assignments(context)
    material_rows, _ = resolve_material_quantity_rows(context, geometry_summary, finish)
    included_rows = [row for row in material_rows if row.included]
    return included_rows, bool(included_rows), finish


async def build_material_availability_rows(
    db: AsyncSession,
    breakdown_rows: list[IntakeV3MaterialQuantityRow],
    finish: FinishAssignment | None,
) -> list[IntakeV3MaterialAvailabilityRow]:
    rows: list[IntakeV3MaterialAvailabilityRow] = []
    for breakdown_row in breakdown_rows:
        registry_code, _ = resolve_registry_code_for_row(breakdown_row.material_key, finish)
        candidates = await load_inventory_material_candidates(
            db,
            registry_code=registry_code,
            display_name=breakdown_row.display_name if not registry_code else None,
        )
        material, match, row_warnings = match_breakdown_material_to_inventory(
            registry_code=registry_code,
            display_name=breakdown_row.display_name,
            candidates=candidates,
        )
        rows.append(
            build_material_availability_row(
                breakdown_row,
                material,
                match,
                row_warnings,
                finish,
            )
        )
    rows.extend(_indirect_policy_row(policy) for policy in INDIRECT_CONSUMABLE_POLICY_ROWS)
    return rows


def downstream_summary_fields(
    availability: IntakeV3MaterialAvailabilityResponse,
) -> dict[str, Any]:
    return {
        "material_availability_available": availability.is_intake_v3 and availability.material_breakdown_available,
        "material_availability_status": availability.summary.overall_status,
        "material_shortage_rows_count": availability.summary.shortage_count,
        "material_manual_check_rows_count": availability.summary.manual_check_count
        + availability.summary.no_match_count
        + availability.summary.ambiguous_match_count,
        "material_indirect_consumables_count": availability.summary.indirect_consumables_count,
    }


def downstream_readiness_warnings(availability: IntakeV3MaterialAvailabilityResponse) -> list[str]:
    codes: list[str] = []
    if not availability.material_breakdown_available and availability.is_intake_v3:
        codes.append("material_availability_missing")
    for warning in availability.warnings:
        if warning.code in {
            "material_shortage_detected",
            "material_manual_check_required",
            "material_breakdown_missing",
        }:
            codes.append(warning.code)
    return list(dict.fromkeys(codes))


def availability_by_material_key(
    availability: IntakeV3MaterialAvailabilityResponse,
) -> dict[str, IntakeV3MaterialAvailabilityRow]:
    return {row.material_key: row for row in availability.rows}


async def build_material_availability_response(
    db: AsyncSession,
    context: Iv3SourceContext,
) -> IntakeV3MaterialAvailabilityResponse:
    workspace_id = None
    quote_id = context.quote.id if context.quote else None
    order_id = context.order.id if context.order else None
    if context.quote_linkage:
        workspace_id = context.quote_linkage.get("source_workspace_id")
    if context.order_linkage and not workspace_id:
        workspace_id = context.order_linkage.get("source_workspace_id")
    if context.source_type == "workspace":
        workspace_id = context.source_id

    if not context.is_intake_v3:
        return IntakeV3MaterialAvailabilityResponse(
            source_module=INTAKE_V3_SOURCE_MODULE,
            source_type=context.source_type,
            source_id=context.source_id,
            workspace_id=str(workspace_id) if workspace_id else None,
            quote_id=quote_id,
            order_id=order_id,
            is_intake_v3=False,
            availability_scope=AVAILABILITY_SCOPE,
            material_breakdown_available=False,
            inventory_source_available=True,
            summary=IntakeV3MaterialAvailabilitySummary(overall_status="unknown"),
            warnings=[
                _warning(
                    "not_intake_v3_source",
                    "Source is not an Intake V3 order/quote/workspace payload.",
                    source="source_detection",
                )
            ],
            boundary=_boundary(),
        )

    breakdown_rows, breakdown_available, finish = await load_material_breakdown_rows(context)
    if breakdown_available:
        rows = await build_material_availability_rows(db, breakdown_rows, finish)
    else:
        rows = [_indirect_policy_row(policy) for policy in INDIRECT_CONSUMABLE_POLICY_ROWS]

    summary = build_material_availability_summary(rows)
    warnings = build_material_availability_warnings(
        material_breakdown_available=breakdown_available,
        rows=rows,
    )

    return IntakeV3MaterialAvailabilityResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        workspace_id=str(workspace_id) if workspace_id else None,
        quote_id=quote_id,
        order_id=order_id,
        is_intake_v3=True,
        availability_scope=AVAILABILITY_SCOPE,
        material_breakdown_available=breakdown_available,
        inventory_source_available=True,
        summary=summary,
        rows=rows,
        warnings=warnings,
        boundary=_boundary(),
    )


def _non_iv3_response(source_type: str, source_id: str, order: Orders | None = None) -> IntakeV3MaterialAvailabilityResponse:
    return IntakeV3MaterialAvailabilityResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=source_type,
        source_id=source_id,
        order_id=order.id if order else None,
        is_intake_v3=False,
        availability_scope=AVAILABILITY_SCOPE,
        material_breakdown_available=False,
        warnings=[
            _warning(
                "not_intake_v3_source",
                "Source is not an Intake V3 order/quote/workspace payload.",
                source="source_detection",
            )
        ],
        boundary=_boundary(),
    )


async def get_material_availability_for_order(
    db: AsyncSession,
    order_id: int,
) -> IntakeV3MaterialAvailabilityResponse:
    context = await load_iv3_source_context(db, order_id=order_id)
    return await build_material_availability_response(db, context)


async def get_material_availability_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3MaterialAvailabilityResponse:
    context = await load_iv3_source_context(db, quote_id=quote_id)
    return await build_material_availability_response(db, context)


async def get_material_availability_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3MaterialAvailabilityResponse:
    context = await load_iv3_source_context(db, workspace_id=workspace_id)
    return await build_material_availability_response(db, context)
