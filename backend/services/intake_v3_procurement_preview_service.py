"""Intake V3 read-only procurement preview — translates Material Availability into recommendations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_materials import Inventory_materials
from schemas.intake_v3 import (
    PROCUREMENT_SCOPE_READ_ONLY,
    IntakeV3MaterialAvailabilityResponse,
    IntakeV3MaterialAvailabilityRow,
    IntakeV3ProcurementPreviewBoundary,
    IntakeV3ProcurementPreviewResponse,
    IntakeV3ProcurementPreviewRow,
    IntakeV3ProcurementPreviewSummary,
    IntakeV3ProcurementPreviewWarning,
    IntakeV3ProcurementQuantityHint,
    IntakeV3ProcurementSourceHint,
)
from services.intake_v3_material_availability_service import (
    build_material_availability_response,
    load_iv3_source_context,
)
from services.intake_v3_real_commercial_quote_creation_service import INTAKE_V3_SOURCE_MODULE

PROCUREMENT_SCOPE = PROCUREMENT_SCOPE_READ_ONLY

MAJOR_MATERIAL_KEYS = frozenset(
    {
        "plexiglas_face",
        "forex_backing",
        "aluminum_return",
        "face_vinyl",
        "led_power_supply",
        "acm_panel",
    }
)

INDIRECT_MATERIAL_KEYS = frozenset(
    {
        "mounting_cables",
        "electrical_connectors",
        "mounting_screws",
        "silicone_sealant",
    }
)

EXPENSIVE_UNIT_COST_HINT_THRESHOLD = 10.0
NEEDS_REVIEW_SOURCE_STATUSES = frozenset({"stale", "needs_owner_input", "needs_review", "missing_price"})


def _boundary() -> IntakeV3ProcurementPreviewBoundary:
    return IntakeV3ProcurementPreviewBoundary()


def _warning(code: str, message: str, *, severity: str = "warning") -> IntakeV3ProcurementPreviewWarning:
    return IntakeV3ProcurementPreviewWarning(code=code, severity=severity, message=message)


async def load_inventory_registry_metadata(
    db: AsyncSession,
    availability_row: IntakeV3MaterialAvailabilityRow,
) -> tuple[IntakeV3ProcurementSourceHint, list[str]]:
    row_warnings: list[str] = []
    material: Inventory_materials | None = None
    match = availability_row.match
    if match.inventory_material_id is not None:
        material = await db.get(Inventory_materials, match.inventory_material_id)
    elif match.inventory_code:
        material = await db.scalar(
            select(Inventory_materials).where(Inventory_materials.code == match.inventory_code)
        )

    if material is None:
        if availability_row.tracking_class != "indirect_consumable":
            row_warnings.append("supplier_source_missing")
        return IntakeV3ProcurementSourceHint(), row_warnings

    hint = IntakeV3ProcurementSourceHint(
        source_name=material.source_name,
        source_url=material.source_url,
        source_review_status=material.source_review_status,
        unit_cost_hint=material.unit_cost,
        currency=material.currency,
        notes=material.source_notes,
    )
    if not material.source_name and not material.source_url:
        row_warnings.append("supplier_source_missing")
    if material.source_review_status in NEEDS_REVIEW_SOURCE_STATUSES:
        row_warnings.append("supplier_source_needs_review")
    return hint, row_warnings


def _manual_check_reason(availability_status: str) -> str | None:
    mapping = {
        "manual_check": "availability_manual_check",
        "no_match": "no_inventory_match",
        "ambiguous_match": "ambiguous_inventory_match",
        "not_tracked": "not_stock_tracked",
        "unknown": "unknown_availability",
    }
    return mapping.get(availability_status)


def classify_procurement_decision(
    availability_row: IntakeV3MaterialAvailabilityRow,
    source_hint: IntakeV3ProcurementSourceHint,
) -> dict[str, Any]:
    avail = availability_row.availability_status
    key = availability_row.material_key
    is_indirect = (
        availability_row.tracking_class == "indirect_consumable"
        or key in INDIRECT_MATERIAL_KEYS
        or avail == "indirect_consumable"
    )
    is_expensive = key in MAJOR_MATERIAL_KEYS or (
        source_hint.unit_cost_hint is not None
        and float(source_hint.unit_cost_hint) >= EXPENSIVE_UNIT_COST_HINT_THRESHOLD
    )

    if is_indirect:
        return {
            "procurement_status": "indirect_consumable",
            "recommended_action": "preventive_restock_or_manual_check",
            "urgency": "low",
            "purchase_decision_type": "indirect_policy",
            "decision_required": True,
            "decision_owner": "operator",
            "advance_recommended": False,
            "is_expensive_material": False,
            "is_indirect_consumable": True,
            "requires_manual_stock_check": True,
            "row_warnings": ["indirect_consumable_policy", "preventive_restock_suggested"],
        }

    if avail == "available":
        return {
            "procurement_status": "no_action",
            "recommended_action": "no_action_needed",
            "urgency": "low",
            "purchase_decision_type": "none",
            "decision_required": False,
            "decision_owner": "none",
            "advance_recommended": False,
            "is_expensive_material": is_expensive,
            "is_indirect_consumable": False,
            "requires_manual_stock_check": False,
            "row_warnings": [],
        }

    if avail in {"manual_check", "no_match", "ambiguous_match", "unknown", "not_tracked"}:
        row_warnings = ["manual_stock_check_required"]
        if avail == "ambiguous_match":
            row_warnings.append("ambiguous_material_match")
        elif avail == "no_match":
            row_warnings.append("no_material_match")
        return {
            "procurement_status": "manual_check",
            "recommended_action": "manual_stock_verification",
            "urgency": "normal",
            "purchase_decision_type": "manual_review",
            "decision_required": True,
            "decision_owner": "operator",
            "advance_recommended": False,
            "is_expensive_material": is_expensive,
            "is_indirect_consumable": False,
            "requires_manual_stock_check": True,
            "row_warnings": row_warnings,
        }

    if avail == "shortage":
        if key in MAJOR_MATERIAL_KEYS or is_expensive:
            return {
                "procurement_status": "owner_decision_required",
                "recommended_action": "purchase_after_owner_approval",
                "urgency": "high",
                "purchase_decision_type": "owner_approved_purchase",
                "decision_required": True,
                "decision_owner": "owner",
                "advance_recommended": True,
                "is_expensive_material": True,
                "is_indirect_consumable": False,
                "requires_manual_stock_check": False,
                "row_warnings": [
                    "owner_decision_required",
                    "advance_recommended",
                    "expensive_material_shortage",
                    "purchase_recommended",
                ],
            }
        return {
            "procurement_status": "purchase_recommended",
            "recommended_action": "purchase_recommended",
            "urgency": "high",
            "purchase_decision_type": "standard_purchase",
            "decision_required": True,
            "decision_owner": "procurement",
            "advance_recommended": False,
            "is_expensive_material": False,
            "is_indirect_consumable": False,
            "requires_manual_stock_check": False,
            "row_warnings": ["purchase_recommended"],
        }

    return {
        "procurement_status": "unknown",
        "recommended_action": "manual_stock_verification",
        "urgency": "normal",
        "purchase_decision_type": "manual_review",
        "decision_required": True,
        "decision_owner": "operator",
        "advance_recommended": False,
        "is_expensive_material": is_expensive,
        "is_indirect_consumable": False,
        "requires_manual_stock_check": True,
        "row_warnings": ["manual_stock_check_required"],
    }


def build_procurement_preview_row(
    availability_row: IntakeV3MaterialAvailabilityRow,
    source_hint: IntakeV3ProcurementSourceHint,
    source_warnings: list[str],
) -> IntakeV3ProcurementPreviewRow:
    decision = classify_procurement_decision(availability_row, source_hint)
    qty = availability_row.quantity
    required = IntakeV3ProcurementQuantityHint(
        value=qty.required_with_waste or qty.required,
        unit=qty.required_unit,
        source="material_availability",
    )
    available = None
    if qty.available is not None:
        available = IntakeV3ProcurementQuantityHint(
            value=qty.available,
            unit=qty.available_unit,
            source="inventory_read_only",
        )
    shortage = None
    if qty.shortage is not None and qty.shortage > 0:
        shortage = IntakeV3ProcurementQuantityHint(
            value=qty.shortage,
            unit=qty.required_unit,
            source="material_availability",
        )

    row_warnings = list(dict.fromkeys(decision["row_warnings"] + source_warnings))

    return IntakeV3ProcurementPreviewRow(
        row_id=availability_row.material_key,
        material_key=availability_row.material_key,
        material_intent=availability_row.material_intent,
        material_code=availability_row.registry_code or availability_row.match.inventory_code,
        display_name=availability_row.display_name,
        availability_status=availability_row.availability_status,
        tracking_class=availability_row.tracking_class,
        required_quantity=required,
        available_quantity=available,
        shortage_quantity=shortage,
        manual_check_reason=_manual_check_reason(availability_row.availability_status),
        procurement_status=decision["procurement_status"],
        recommended_action=decision["recommended_action"],
        urgency=decision["urgency"],
        purchase_decision_type=decision["purchase_decision_type"],
        decision_required=decision["decision_required"],
        decision_owner=decision["decision_owner"],
        advance_recommended=decision["advance_recommended"],
        is_expensive_material=decision["is_expensive_material"],
        is_indirect_consumable=decision["is_indirect_consumable"],
        requires_manual_stock_check=decision["requires_manual_stock_check"],
        source_hint=source_hint,
        warnings=row_warnings,
    )


def build_procurement_preview_summary(
    rows: list[IntakeV3ProcurementPreviewRow],
) -> IntakeV3ProcurementPreviewSummary:
    counts = {
        "purchase_recommended": 0,
        "manual_check": 0,
        "owner_decision_required": 0,
        "advance_recommended": 0,
        "preventive_restock": 0,
        "indirect_consumable": 0,
        "no_action": 0,
        "unknown": 0,
    }
    advance_count = 0
    for row in rows:
        status = row.procurement_status
        if status not in counts:
            status = "unknown"
        counts[status] += 1
        if row.advance_recommended:
            advance_count += 1
        if row.procurement_status == "indirect_consumable":
            counts["preventive_restock"] += 1

    if counts["owner_decision_required"] > 0:
        overall = "owner_decision_required"
    elif counts["purchase_recommended"] > 0:
        overall = "purchase_recommended"
    elif counts["manual_check"] > 0:
        overall = "manual_check"
    elif counts["indirect_consumable"] > 0:
        overall = "indirect_consumable"
    elif counts["no_action"] == len(rows) and rows:
        overall = "no_action"
    elif rows:
        overall = "mixed"
    else:
        overall = "unknown"

    return IntakeV3ProcurementPreviewSummary(
        rows_count=len(rows),
        purchase_recommended_count=counts["purchase_recommended"],
        manual_check_count=counts["manual_check"],
        owner_decision_required_count=counts["owner_decision_required"],
        advance_recommended_count=advance_count,
        preventive_restock_count=counts["preventive_restock"],
        indirect_consumable_count=counts["indirect_consumable"],
        no_action_count=counts["no_action"],
        warnings_count=0,
        overall_status=overall,
    )


def build_procurement_preview_warnings(
    *,
    material_availability_available: bool,
    rows: list[IntakeV3ProcurementPreviewRow],
) -> list[IntakeV3ProcurementPreviewWarning]:
    warnings: list[IntakeV3ProcurementPreviewWarning] = [
        _warning(
            "procurement_preview_read_only",
            "This procurement preview is read-only and does not create purchase orders.",
        )
    ]
    if not material_availability_available:
        warnings.append(
            _warning(
                "material_availability_missing",
                "Material availability is missing — procurement preview is incomplete.",
            )
        )
    if any(row.procurement_status == "purchase_recommended" for row in rows):
        warnings.append(
            _warning(
                "purchase_recommended",
                "One or more materials have a recommended purchase action (preview only).",
            )
        )
    if any(row.procurement_status == "owner_decision_required" for row in rows):
        warnings.append(
            _warning(
                "owner_decision_required",
                "Owner decision is required before purchasing one or more expensive materials.",
            )
        )
    if any(row.advance_recommended for row in rows):
        warnings.append(
            _warning(
                "advance_recommended",
                "Advance payment or owner approval is recommended for expensive material shortages.",
            )
        )
    if any(row.procurement_status == "manual_check" for row in rows):
        warnings.append(
            _warning(
                "manual_stock_check_required",
                "Manual stock verification is required for one or more materials.",
            )
        )
    return list({warning.code: warning for warning in warnings}.values())


async def build_procurement_preview_rows(
    db: AsyncSession,
    availability: IntakeV3MaterialAvailabilityResponse,
) -> list[IntakeV3ProcurementPreviewRow]:
    rows: list[IntakeV3ProcurementPreviewRow] = []
    for availability_row in availability.rows:
        source_hint, source_warnings = await load_inventory_registry_metadata(db, availability_row)
        rows.append(
            build_procurement_preview_row(availability_row, source_hint, source_warnings)
        )
    return rows


def downstream_summary_fields(preview: IntakeV3ProcurementPreviewResponse) -> dict[str, Any]:
    return {
        "procurement_preview_available": preview.is_intake_v3 and preview.material_availability_available,
        "procurement_preview_status": preview.summary.overall_status,
        "procurement_purchase_recommended_count": preview.summary.purchase_recommended_count,
        "procurement_owner_decision_required_count": preview.summary.owner_decision_required_count,
        "procurement_advance_recommended_count": preview.summary.advance_recommended_count,
        "procurement_manual_check_count": preview.summary.manual_check_count,
    }


def downstream_readiness_warnings(preview: IntakeV3ProcurementPreviewResponse) -> list[str]:
    codes: list[str] = []
    for warning in preview.warnings:
        if warning.code in {
            "owner_decision_required",
            "manual_stock_check_required",
            "purchase_recommended",
            "material_availability_missing",
        }:
            codes.append(warning.code)
    if preview.summary.owner_decision_required_count > 0:
        codes.append("procurement_owner_decision_required")
    if preview.summary.manual_check_count > 0:
        codes.append("procurement_manual_check_required")
    if preview.summary.purchase_recommended_count > 0:
        codes.append("procurement_purchase_recommended")
    return list(dict.fromkeys(codes))


def procurement_by_material_key(
    preview: IntakeV3ProcurementPreviewResponse,
) -> dict[str, IntakeV3ProcurementPreviewRow]:
    return {row.material_key: row for row in preview.rows}


async def build_procurement_preview_response(
    db: AsyncSession,
    *,
    order_id: int | None = None,
    quote_id: int | None = None,
    workspace_id: str | None = None,
) -> IntakeV3ProcurementPreviewResponse:
    context = await load_iv3_source_context(
        db,
        order_id=order_id,
        quote_id=quote_id,
        workspace_id=workspace_id,
    )
    resolved_workspace_id = workspace_id
    resolved_quote_id = quote_id or (context.quote.id if context.quote else None)
    resolved_order_id = order_id or (context.order.id if context.order else None)
    if context.quote_linkage:
        resolved_workspace_id = resolved_workspace_id or context.quote_linkage.get("source_workspace_id")
    if context.order_linkage and not resolved_workspace_id:
        resolved_workspace_id = context.order_linkage.get("source_workspace_id")
    if context.source_type == "workspace":
        resolved_workspace_id = context.source_id

    if not context.is_intake_v3:
        return IntakeV3ProcurementPreviewResponse(
            source_module=INTAKE_V3_SOURCE_MODULE,
            source_type=context.source_type,
            source_id=context.source_id,
            workspace_id=str(resolved_workspace_id) if resolved_workspace_id else None,
            quote_id=resolved_quote_id,
            order_id=resolved_order_id,
            is_intake_v3=False,
            procurement_scope=PROCUREMENT_SCOPE,
            material_availability_available=False,
            warnings=[
                _warning(
                    "not_intake_v3_source",
                    "Source is not an Intake V3 order/quote/workspace payload.",
                )
            ],
            boundary=_boundary(),
        )

    availability = await build_material_availability_response(db, context)
    rows = await build_procurement_preview_rows(db, availability)
    summary = build_procurement_preview_summary(rows)
    warnings = build_procurement_preview_warnings(
        material_availability_available=availability.material_breakdown_available,
        rows=rows,
    )
    summary = summary.model_copy(update={"warnings_count": len(warnings)})

    return IntakeV3ProcurementPreviewResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        workspace_id=str(resolved_workspace_id) if resolved_workspace_id else None,
        quote_id=resolved_quote_id,
        order_id=resolved_order_id,
        is_intake_v3=True,
        procurement_scope=PROCUREMENT_SCOPE,
        material_availability_available=availability.material_breakdown_available,
        summary=summary,
        rows=rows,
        warnings=warnings,
        boundary=_boundary(),
    )


async def get_procurement_preview_for_order(
    db: AsyncSession,
    order_id: int,
) -> IntakeV3ProcurementPreviewResponse:
    return await build_procurement_preview_response(db, order_id=order_id)


async def get_procurement_preview_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3ProcurementPreviewResponse:
    return await build_procurement_preview_response(db, quote_id=quote_id)


async def get_procurement_preview_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3ProcurementPreviewResponse:
    return await build_procurement_preview_response(db, workspace_id=workspace_id)
