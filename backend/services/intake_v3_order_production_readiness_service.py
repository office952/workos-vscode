"""Intake V3 order production readiness — read-only audit, no Execution/Inventory mutations."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from models.stock_movements import StockMovement
from schemas.intake_v3 import (
    IntakeV3MaterialReadinessPreviewContract,
    IntakeV3OrderAvailableDataSummary,
    IntakeV3OrderMissingRequirement,
    IntakeV3OrderProductionReadinessResponse,
    IntakeV3ProductionHandoffPreview,
    IntakeV3TaskGenerationPreviewContract,
    IntakeV3Workspace,
)
from services.intake_v3_draft_quote_review_service import parse_intake_v3_quote_notes
from services.intake_v3_finish_material_service import derive_material_intent
from services.intake_v3_guarded_convert_to_order_service import check_existing_order_for_iv3_quote
from services.intake_v3_production_handoff_adapter import build_task_seed_candidates
from services.intake_v3_quote_linkage_utils import (
    IV3_ORDER_LINKAGE_JSON_KEY,
    get_accept_decision_record,
    get_convert_decision_record,
    get_pricing_review_record,
    is_iv3_accept_completed,
    is_iv3_convert_completed,
    is_pricing_review_completed,
)
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_CODE_PREFIX,
    INTAKE_V3_LINKAGE_JSON_KEY,
    INTAKE_V3_SOURCE_MODULE,
    check_existing_quote_for_intake_v3_workspace,
    parse_intake_v3_linkage_from_notes,
)
from services.orders import OrdersService
from services.quotes import QuotesService

STATUS_NOT_IV3 = "not_iv3_order"
STATUS_MISSING_ORDER = "missing_order"
STATUS_MISSING_QUOTE_LINKAGE = "missing_quote_linkage"
STATUS_MISSING_INTAKE_V3_LINKAGE = "missing_intake_v3_linkage"
STATUS_MISSING_CONFIRMED_MODEL = "missing_confirmed_production_model"
STATUS_MISSING_FINISH = "missing_finish_assignments"
STATUS_MISSING_PRICING = "missing_pricing_review"
STATUS_MISSING_ACCEPT = "missing_accept_decision"
STATUS_MISSING_CONVERT = "missing_convert_decision"
STATUS_READY = "ready_for_handoff_preview"
STATUS_BLOCKED = "blocked"

STATUS_PRIORITY = [
    STATUS_MISSING_ORDER,
    STATUS_MISSING_QUOTE_LINKAGE,
    STATUS_MISSING_INTAKE_V3_LINKAGE,
    STATUS_MISSING_CONFIRMED_MODEL,
    STATUS_MISSING_FINISH,
    STATUS_MISSING_PRICING,
    STATUS_MISSING_ACCEPT,
    STATUS_MISSING_CONVERT,
    STATUS_BLOCKED,
]

BLOCKER_TO_STATUS = {
    "missing_order": STATUS_MISSING_ORDER,
    "missing_quote_id": STATUS_MISSING_QUOTE_LINKAGE,
    "missing_quote": STATUS_MISSING_QUOTE_LINKAGE,
    "missing_quote_linkage": STATUS_MISSING_QUOTE_LINKAGE,
    "missing_quote_notes": STATUS_MISSING_QUOTE_LINKAGE,
    "invalid_quote_notes_json": STATUS_MISSING_QUOTE_LINKAGE,
    "missing_order_linkage": STATUS_MISSING_INTAKE_V3_LINKAGE,
    "missing_intake_v3_linkage": STATUS_MISSING_INTAKE_V3_LINKAGE,
    "missing_order_snapshot": STATUS_MISSING_INTAKE_V3_LINKAGE,
    "missing_confirmed_production_model": STATUS_MISSING_CONFIRMED_MODEL,
    "missing_finish_assignments": STATUS_MISSING_FINISH,
    "missing_pricing_review": STATUS_MISSING_PRICING,
    "missing_accept_decision": STATUS_MISSING_ACCEPT,
    "missing_convert_decision": STATUS_MISSING_CONVERT,
    "missing_dimensions": STATUS_BLOCKED,
    "unsupported_product_template": STATUS_BLOCKED,
}


def _missing(
    code: str,
    message: str,
    *,
    source: str,
    severity: str = "blocking",
) -> IntakeV3OrderMissingRequirement:
    return IntakeV3OrderMissingRequirement(
        code=code,
        severity=severity,
        message=message,
        source=source,
    )


def _parse_json_object(raw: str | None) -> dict[str, Any] | None:
    if not raw or not str(raw).strip():
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def load_iv3_order_linkage(order: Orders) -> dict[str, Any] | None:
    snapshot = _parse_json_object(order.snapshot_line_items)
    if snapshot and isinstance(snapshot.get(IV3_ORDER_LINKAGE_JSON_KEY), dict):
        return snapshot[IV3_ORDER_LINKAGE_JSON_KEY]
    notes = _parse_json_object(order.notes)
    if notes and isinstance(notes.get(IV3_ORDER_LINKAGE_JSON_KEY), dict):
        return notes[IV3_ORDER_LINKAGE_JSON_KEY]
    return None


def is_iv3_order(order: Orders, order_linkage: dict[str, Any] | None) -> bool:
    if order_linkage and order_linkage.get("source_module") == INTAKE_V3_SOURCE_MODULE:
        return True
    snapshot = _parse_json_object(order.snapshot_line_items)
    if snapshot and snapshot.get("source_module") == INTAKE_V3_SOURCE_MODULE:
        return True
    if snapshot and snapshot.get("snapshot_type") == "intake_v3_guarded_convert_order_snapshot_v1":
        return True
    return False


async def load_source_quote_for_iv3_order(db: AsyncSession, order: Orders) -> Quotes | None:
    if order.quote_id is None:
        return None
    quotes_service = QuotesService(db)
    return await quotes_service.get_by_id(order.quote_id)


def load_quote_intake_v3_linkage(quote: Quotes | None) -> tuple[dict[str, Any] | None, list[str]]:
    if quote is None:
        return None, []
    linkage, warnings = parse_intake_v3_quote_notes(quote.notes)
    return linkage, [w.code for w in warnings]


def _snapshot_sections(linkage: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(linkage, dict):
        return {}
    snapshot = linkage.get("snapshot")
    if not isinstance(snapshot, dict):
        return {}
    sections = snapshot.get("sections")
    return sections if isinstance(sections, dict) else {}


def _load_workspace_from_sections(sections: dict[str, Any]) -> IntakeV3Workspace | None:
    payload = sections.get("workspace_payload_snapshot")
    if not isinstance(payload, dict):
        return None
    try:
        return IntakeV3Workspace.model_validate(payload)
    except Exception:
        return None


def _resolve_product_template(sections: dict[str, Any], workspace: IntakeV3Workspace | None) -> str:
    identity = sections.get("workspace_identity_snapshot")
    if isinstance(identity, dict) and identity.get("template_code"):
        return str(identity["template_code"])
    if workspace is not None:
        return workspace.product_selection.template_code
    return PILOT_TEMPLATE_CODE


def build_iv3_order_missing_requirements(
    order: Orders | None,
    quote: Quotes | None,
    quote_linkage: dict[str, Any] | None,
    order_linkage: dict[str, Any] | None,
    *,
    quote_note_warnings: list[str] | None = None,
) -> list[IntakeV3OrderMissingRequirement]:
    missing: list[IntakeV3OrderMissingRequirement] = []

    if order is None:
        missing.append(
            _missing(
                "missing_order",
                "Order was not found for production readiness audit.",
                source="orders.id",
            )
        )
        return missing

    if order.quote_id is None:
        missing.append(
            _missing(
                "missing_quote_id",
                "Order is missing quote_id linkage.",
                source="orders.quote_id",
            )
        )

    if order_linkage is None:
        missing.append(
            _missing(
                "missing_order_linkage",
                "Intake V3 order linkage is missing from order notes/snapshot.",
                source=f"orders.snapshot_line_items.{IV3_ORDER_LINKAGE_JSON_KEY}",
            )
        )

    if quote is None and order.quote_id is not None:
        missing.append(
            _missing(
                "missing_quote",
                "Source quote for this order was not found.",
                source="quotes.id",
            )
        )

    if quote_note_warnings:
        for code in quote_note_warnings:
            if code == "NOTES_JSON_INVALID":
                missing.append(
                    _missing(
                        "invalid_quote_notes_json",
                        "Quote notes are not valid JSON — cannot audit IV3 production readiness.",
                        source="quotes.notes",
                    )
                )
            elif code in {"LINKAGE_MISSING", "NOTES_EMPTY"}:
                missing.append(
                    _missing(
                        "missing_quote_notes",
                        "Quote notes linkage is missing or empty.",
                        source="quotes.notes",
                    )
                )

    if quote is not None and quote_linkage is None and "invalid_quote_notes_json" not in {m.code for m in missing}:
        missing.append(
            _missing(
                "missing_intake_v3_linkage",
                "Quote is missing intake_v3_linkage_v1.",
                source=f"quotes.notes.{INTAKE_V3_LINKAGE_JSON_KEY}",
            )
        )

    sections = _snapshot_sections(quote_linkage)
    confirmed = sections.get("confirmed_production_model_snapshot")
    if not isinstance(confirmed, dict) or not confirmed:
        missing.append(
            _missing(
                "missing_confirmed_production_model",
                "Confirmed production model is required before production handoff.",
                source=f"quotes.notes.{INTAKE_V3_LINKAGE_JSON_KEY}.snapshot.sections.confirmed_production_model_snapshot",
            )
        )

    finish_snapshot = sections.get("finish_assignment_snapshot")
    workspace = _load_workspace_from_sections(sections)
    has_finish_snapshot = _has_finish_assignment_data(finish_snapshot, workspace)
    if not has_finish_snapshot:
        missing.append(
            _missing(
                "missing_finish_assignments",
                "Finish assignments are required before production handoff.",
                source=f"quotes.notes.{INTAKE_V3_LINKAGE_JSON_KEY}.snapshot.sections.finish_assignment_snapshot",
            )
        )
    elif isinstance(finish_snapshot, dict) and not finish_snapshot and workspace is not None and workspace.finish_assignment:
        missing.append(
            _missing(
                "finish_assignments_snapshot_incomplete",
                "Finish assignments exist in workspace payload but snapshot section is missing.",
                source=f"quotes.notes.{INTAKE_V3_LINKAGE_JSON_KEY}.snapshot.sections.finish_assignment_snapshot",
                severity="warning",
            )
        )

    if quote_linkage is not None and not is_pricing_review_completed(quote_linkage):
        missing.append(
            _missing(
                "missing_pricing_review",
                "Pricing review must be completed before production handoff.",
                source=f"quotes.notes.{INTAKE_V3_LINKAGE_JSON_KEY}.pricing_review",
            )
        )

    if quote_linkage is not None:
        accept_record = get_accept_decision_record(quote_linkage)
        if accept_record is None or accept_record.get("status") != "approved":
            missing.append(
                _missing(
                    "missing_accept_decision",
                    "Accept decision is required before production handoff.",
                    source=f"quotes.notes.{INTAKE_V3_LINKAGE_JSON_KEY}.accept_decision",
                )
            )

    convert_from_quote = is_iv3_convert_completed(quote_linkage) if quote_linkage else False
    convert_from_order = bool(
        order_linkage
        and order_linkage.get("created_from_guarded_convert") is True
        and order_linkage.get("source_quote_id")
    )
    if not convert_from_quote and not convert_from_order:
        missing.append(
            _missing(
                "missing_convert_decision",
                "Convert decision / guarded convert linkage is required before production handoff.",
                source=f"quotes.notes.{INTAKE_V3_LINKAGE_JSON_KEY}.convert_decision",
            )
        )

    if not _parse_json_object(order.snapshot_line_items):
        missing.append(
            _missing(
                "missing_order_snapshot",
                "Order snapshot_line_items is missing or invalid JSON.",
                source="orders.snapshot_line_items",
            )
        )

    if confirmed and isinstance(confirmed, dict):
        letter_count = confirmed.get("letter_count")
        if letter_count is None or int(letter_count or 0) <= 0:
            missing.append(
                _missing(
                    "missing_dimensions",
                    "Confirmed production model does not expose letter dimensions/count.",
                    source="confirmed_production_model_snapshot.letter_count",
                )
            )

    template = _resolve_product_template(sections, workspace)
    if template != PILOT_TEMPLATE_CODE:
        missing.append(
            _missing(
                "unsupported_product_template",
                f"Production readiness audit supports {PILOT_TEMPLATE_CODE} only; got {template}.",
                source="workspace_identity_snapshot.template_code",
                severity="warning",
            )
        )

    return missing


def _has_finish_assignment_data(
    finish_snapshot: Any,
    workspace: IntakeV3Workspace | None,
) -> bool:
    if isinstance(finish_snapshot, dict) and finish_snapshot:
        if finish_snapshot.get("assignment_mode") or finish_snapshot.get("face_finish"):
            return True
        if finish_snapshot.get("letter_group_finish_assignments") or finish_snapshot.get(
            "letter_finish_assignments"
        ):
            return True
        if finish_snapshot.get("groups"):
            return True
    if workspace is not None:
        if workspace.finish_assignment is not None:
            return True
        if workspace.letter_group_finish_assignments or workspace.letter_finish_assignments:
            return True
    return False


def _finish_summary_fields(
    finish_snapshot: dict[str, Any] | None,
    workspace: IntakeV3Workspace | None,
) -> tuple[Any, int, int]:
    global_finish = None
    group_overrides = 0
    letter_overrides = 0
    if isinstance(finish_snapshot, dict) and finish_snapshot:
        global_finish = finish_snapshot.get("assignment_mode") or finish_snapshot.get("face_finish")
        group_overrides = len(finish_snapshot.get("letter_group_finish_assignments") or finish_snapshot.get("groups") or [])
        letter_overrides = len(finish_snapshot.get("letter_finish_assignments") or [])
    elif workspace and workspace.finish_assignment:
        global_finish = workspace.finish_assignment.assignment_mode
        group_overrides = len(workspace.letter_group_finish_assignments or [])
        letter_overrides = len(workspace.letter_finish_assignments or [])
    return global_finish, group_overrides, letter_overrides


def build_iv3_order_available_data_summary(
    order: Orders | None,
    quote: Quotes | None,
    quote_linkage: dict[str, Any] | None,
    order_linkage: dict[str, Any] | None,
    *,
    sections_override: dict[str, Any] | None = None,
    workspace_override: IntakeV3Workspace | None = None,
    linkage_sections: dict[str, Any] | None = None,
) -> IntakeV3OrderAvailableDataSummary:
    sections = sections_override if sections_override is not None else _snapshot_sections(quote_linkage)
    confirmed = sections.get("confirmed_production_model_snapshot")
    finish_snapshot = sections.get("finish_assignment_snapshot")
    workspace = workspace_override or _load_workspace_from_sections(sections)
    global_finish, finish_groups, finish_letters = _finish_summary_fields(
        finish_snapshot if isinstance(finish_snapshot, dict) else None,
        workspace,
    )
    identity = sections.get("workspace_identity_snapshot")
    raw_ref = sections.get("raw_svg_analysis_reference")
    from services.intake_v3_geometry_metrics_snapshot_service import (
        parse_snapshot_from_sections,
        resolve_geometry_status,
    )

    geometry_snapshot = parse_snapshot_from_sections(sections)
    geometry_status = "geometry_missing"
    perimeter_classification_status: str | None = None
    face_cutting_perimeter_available = False
    backing_cutting_perimeter_available = False
    return_material_perimeter_available = False
    bevel_perimeter_available = False
    if geometry_snapshot is not None:
        geometry_status = resolve_geometry_status(geometry_snapshot)
        classification = geometry_snapshot.path_perimeter_classification
        if isinstance(classification, dict):
            perimeter_classification_status = classification.get("classification_status")
            perimeters = classification.get("perimeters") or {}
            face_cutting_perimeter_available = (
                (perimeters.get("face_cutting_perimeter_ml") or {}).get("value") is not None
            )
            backing_cutting_perimeter_available = (
                (perimeters.get("backing_cutting_perimeter_ml") or {}).get("value") is not None
            )
            return_material_perimeter_available = (
                (perimeters.get("return_material_perimeter_ml") or {}).get("value") is not None
            )
            bevel_perimeter_available = (
                (perimeters.get("bevel_perimeter_ml") or {}).get("value") is not None
            )
        elif geometry_snapshot.perimeters.face_cutting_perimeter_ml is not None:
            face_cutting_perimeter_available = True
        if geometry_snapshot.perimeters.backing_cutting_perimeter_ml is not None:
            backing_cutting_perimeter_available = True
        if geometry_snapshot.perimeters.return_material_perimeter_ml is not None:
            return_material_perimeter_available = True
        if geometry_snapshot.perimeters.bevel_perimeter_ml is not None:
            bevel_perimeter_available = True

    layer_role_confirmation_status: str | None = None
    operator_confirmed_layer_roles_count = 0
    unconfirmed_layer_roles_count = 0
    ignored_layer_roles_count = 0
    perimeter_classification_confidence: str | None = None
    layer_role_raw = sections.get("layer_role_confirmation_snapshot")
    if isinstance(layer_role_raw, dict):
        layer_role_confirmation_status = layer_role_raw.get("confirmation_status")
        for layer in layer_role_raw.get("layers") or []:
            if not isinstance(layer, dict):
                continue
            state = layer.get("confirmation_state")
            if state == "confirmed":
                operator_confirmed_layer_roles_count += 1
            elif state in {"pending", "unconfirmed", None}:
                unconfirmed_layer_roles_count += 1
        ignored_layer_roles_count = len(layer_role_raw.get("ignored_layers") or [])
    elif workspace and workspace.layer_role_confirmation_snapshot:
        nested = workspace.layer_role_confirmation_snapshot
        if isinstance(nested, dict):
            layer_role_confirmation_status = nested.get("confirmation_status")
            for layer in nested.get("layers") or []:
                if isinstance(layer, dict) and layer.get("confirmation_state") == "confirmed":
                    operator_confirmed_layer_roles_count += 1
            ignored_layer_roles_count = len(nested.get("ignored_layers") or [])
    if geometry_snapshot is not None:
        classification = geometry_snapshot.path_perimeter_classification
        if isinstance(classification, dict):
            perimeter_classification_confidence = classification.get("confidence")

    from services.intake_v3_layer_role_confirmation_propagation_service import (
        _parse_snapshot,
        build_layer_role_propagation_meta,
        load_quote_confirmation_snapshot_from_sections,
    )

    workspace_id = None
    if order_linkage:
        workspace_id = order_linkage.get("source_workspace_id")
    if quote_linkage and not workspace_id:
        workspace_id = quote_linkage.get("source_workspace_id")

    workspace_snapshot = _parse_snapshot(
        workspace.layer_role_confirmation_snapshot
        if workspace and workspace.layer_role_confirmation_snapshot
        else sections.get("layer_role_confirmation_snapshot")
        if isinstance(sections.get("layer_role_confirmation_snapshot"), dict)
        else None
    )
    quote_snapshot = load_quote_confirmation_snapshot_from_sections(linkage_sections or {})
    propagation_meta = build_layer_role_propagation_meta(
        workspace_snapshot=workspace_snapshot,
        quote_snapshot=quote_snapshot,
        workspace_id=str(workspace_id) if workspace_id else None,
        quote=quote,
        linkage=quote_linkage,
        order=order,
    )

    return IntakeV3OrderAvailableDataSummary(
        has_order_linkage=order_linkage is not None,
        has_quote_linkage=quote is not None and quote_linkage is not None,
        has_confirmed_model=isinstance(confirmed, dict) and bool(confirmed),
        has_finish_assignments=_has_finish_assignment_data(finish_snapshot, workspace),
        has_pricing_review=is_pricing_review_completed(quote_linkage) if quote_linkage else False,
        has_accept_decision=get_accept_decision_record(quote_linkage) is not None
        and get_accept_decision_record(quote_linkage or {}).get("status") == "approved",
        has_convert_decision=is_iv3_convert_completed(quote_linkage)
        or bool(order_linkage and order_linkage.get("created_from_guarded_convert")),
        has_dimensions=isinstance(confirmed, dict) and int(confirmed.get("letter_count") or 0) > 0,
        has_text_or_artwork_summary=isinstance(identity, dict)
        and bool(identity.get("job_title") or identity.get("client_name")),
        has_layer_summary=isinstance(raw_ref, dict) and raw_ref.get("present") is True,
        global_finish_summary=str(global_finish) if global_finish else None,
        group_overrides_count=finish_groups,
        letter_overrides_count=finish_letters,
        geometry_snapshot_available=geometry_snapshot is not None,
        geometry_status=geometry_status,
        perimeter_classification_status=perimeter_classification_status,
        face_cutting_perimeter_available=face_cutting_perimeter_available,
        backing_cutting_perimeter_available=backing_cutting_perimeter_available,
        return_material_perimeter_available=return_material_perimeter_available,
        bevel_perimeter_available=bevel_perimeter_available,
        layer_role_confirmation_status=layer_role_confirmation_status,
        operator_confirmed_layer_roles_count=operator_confirmed_layer_roles_count,
        unconfirmed_layer_roles_count=unconfirmed_layer_roles_count,
        ignored_layer_roles_count=ignored_layer_roles_count,
        perimeter_classification_confidence=perimeter_classification_confidence,
        layer_role_confirmation_effective_source=propagation_meta.effective_source,
        layer_role_confirmation_snapshot_stale=propagation_meta.is_snapshot_stale,
        layer_role_confirmation_stale_reason=propagation_meta.stale_reason,
        layer_role_confirmation_can_refresh_quote_snapshot=propagation_meta.can_refresh_quote_snapshot,
    )


def build_iv3_order_handoff_preview(
    order: Orders | None,
    quote: Quotes | None,
    quote_linkage: dict[str, Any] | None,
    order_linkage: dict[str, Any] | None,
) -> IntakeV3ProductionHandoffPreview:
    sections = _snapshot_sections(quote_linkage)
    confirmed = sections.get("confirmed_production_model_snapshot") or {}
    finish_snapshot = sections.get("finish_assignment_snapshot") or {}
    workspace = _load_workspace_from_sections(sections)
    pricing_review = get_pricing_review_record(quote_linkage) if quote_linkage else None

    real_letters = confirmed.get("letter_count") if isinstance(confirmed, dict) else None
    closed_contours = None
    holes = None
    if isinstance(confirmed, dict):
        closed_contours = confirmed.get("cut_contour_count")
        holes = confirmed.get("inner_hole_count")
        cut_model = confirmed.get("cut_contour_model")
        if isinstance(cut_model, dict):
            closed_contours = closed_contours or cut_model.get("contour_count")
            holes = holes or cut_model.get("inner_hole_count")

    global_finish, group_overrides, letter_overrides = _finish_summary_fields(
        finish_snapshot if isinstance(finish_snapshot, dict) else None,
        workspace,
    )

    order_total = float(order.total_amount or 0) if order else 0.0
    currency = "RON"
    if pricing_review and pricing_review.get("currency"):
        currency = str(pricing_review["currency"])
    elif order_linkage and order_linkage.get("commercial_currency"):
        currency = str(order_linkage["commercial_currency"])

    return IntakeV3ProductionHandoffPreview(
        product_template=_resolve_product_template(sections, workspace),
        production_model_summary={
            "real_letters_count": real_letters,
            "closed_contours_count": closed_contours,
            "holes_count": holes,
        },
        finish_summary={
            "global_finish": global_finish,
            "group_overrides_count": group_overrides,
            "letter_overrides_count": letter_overrides,
        },
        commercial_summary={
            "pricing_review_completed": is_pricing_review_completed(quote_linkage) if quote_linkage else False,
            "order_total": order_total,
            "currency": currency,
            "quote_grand_total": float(quote.grand_total or 0) if quote else None,
        },
        production_boundaries={
            "execution_plan_created": False,
            "execution_tasks_created": False,
            "inventory_mutated": False,
            "production_started": False,
        },
    )


def build_iv3_order_task_generation_preview_contract(
    quote_linkage: dict[str, Any] | None,
) -> IntakeV3TaskGenerationPreviewContract:
    sections = _snapshot_sections(quote_linkage)
    workspace = _load_workspace_from_sections(sections)
    candidate_groups: list[str] = []

    if workspace is not None:
        seeds = build_task_seed_candidates(workspace)
        candidate_groups = [seed.display_name for seed in seeds if seed.active]
    else:
        candidate_groups = [
            "Prepress / verificare fișiere",
            "CNC debitare fețe plexiglas",
            "CNC șanfren fețe",
            "Debitare backing Forex",
            "Modelare cant aluminiu",
            "Lipire cant pe față",
            "Colantare față / aplicare autocolant",
            "LED / electrică",
            "Asamblare",
            "Ambalare",
        ]

    return IntakeV3TaskGenerationPreviewContract(
        would_generate_execution_plan=False,
        would_generate_tasks_preview_only=True,
        candidate_task_groups=candidate_groups,
        requires_future_build=True,
    )


def build_iv3_order_material_readiness_preview_contract(
    quote_linkage: dict[str, Any] | None,
) -> IntakeV3MaterialReadinessPreviewContract:
    sections = _snapshot_sections(quote_linkage)
    workspace = _load_workspace_from_sections(sections)
    materials: list[str] = [
        "plexiglas față",
        "Forex / backing",
        "autocolant",
        "cant aluminiu",
        "LED-uri",
        "surse LED",
    ]

    if workspace is not None:
        try:
            intent = derive_material_intent(workspace)
            for roll in intent.roll_materials:
                if roll.material:
                    materials.append(str(roll.material))
            for sheet in intent.sheet_materials:
                if sheet.material:
                    materials.append(str(sheet.material))
            for led in intent.led_materials:
                if led.material:
                    materials.append(str(led.material))
            for psu in intent.power_supplies:
                if psu.material:
                    materials.append(str(psu.material))
        except Exception:
            pass

    deduped = list(dict.fromkeys(materials))
    return IntakeV3MaterialReadinessPreviewContract(
        would_check_materials_preview_only=True,
        materials_expected=deduped,
        material_cost_breakdown="future_build",
        inventory_check="future_build",
        inventory_mutation_allowed=False,
        requires_future_build=True,
    )


def _resolve_production_readiness_status(
    *,
    is_iv3: bool,
    blocking_missing: list[IntakeV3OrderMissingRequirement],
) -> str:
    if not is_iv3:
        return STATUS_NOT_IV3
    if not blocking_missing:
        return STATUS_READY
    codes = [item.code for item in blocking_missing]
    for status in STATUS_PRIORITY:
        for code in codes:
            if BLOCKER_TO_STATUS.get(code) == status:
                return status
    return STATUS_BLOCKED


def build_iv3_order_production_readiness_response(
    order: Orders | None,
    quote: Quotes | None,
    quote_linkage: dict[str, Any] | None,
    order_linkage: dict[str, Any] | None,
    *,
    quote_note_warnings: list[str] | None = None,
    sections_override: dict[str, Any] | None = None,
    workspace_override: IntakeV3Workspace | None = None,
    linkage_sections: dict[str, Any] | None = None,
) -> IntakeV3OrderProductionReadinessResponse:
    is_iv3 = order is not None and is_iv3_order(order, order_linkage)
    missing = build_iv3_order_missing_requirements(
        order,
        quote,
        quote_linkage,
        order_linkage,
        quote_note_warnings=quote_note_warnings,
    )
    blocking = [item for item in missing if item.severity == "blocking"]
    status = _resolve_production_readiness_status(is_iv3=is_iv3, blocking_missing=blocking)
    ready_preview = is_iv3 and status == STATUS_READY

    created_from_guarded = bool(
        order_linkage and order_linkage.get("created_from_guarded_convert") is True
    ) or is_iv3_convert_completed(quote_linkage)

    workspace_id = None
    if order_linkage:
        workspace_id = order_linkage.get("source_workspace_id")
    if quote_linkage and not workspace_id:
        workspace_id = quote_linkage.get("source_workspace_id")

    from services.intake_v3_layer_role_confirmation_propagation_service import (
        build_layer_role_propagation_meta,
        load_quote_confirmation_snapshot_from_sections,
        _parse_snapshot,
        stale_propagation_warnings,
    )

    sections = sections_override if sections_override is not None else _snapshot_sections(quote_linkage)
    workspace = workspace_override if workspace_override is not None else _load_workspace_from_sections(sections)
    workspace_snapshot = _parse_snapshot(
        workspace.layer_role_confirmation_snapshot
        if workspace and workspace.layer_role_confirmation_snapshot
        else None
    )
    quote_snapshot = load_quote_confirmation_snapshot_from_sections(linkage_sections or _snapshot_sections(quote_linkage))
    propagation_meta = build_layer_role_propagation_meta(
        workspace_snapshot=workspace_snapshot,
        quote_snapshot=quote_snapshot,
        workspace_id=str(workspace_id) if workspace_id else None,
        quote=quote,
        linkage=quote_linkage,
        order=order,
    )
    readiness_warnings = list(quote_note_warnings or [])
    for code, message in stale_propagation_warnings(propagation_meta):
        readiness_warnings.append(code)
        if code == "quote_layer_role_snapshot_stale":
            readiness_warnings.append("operator_confirmation_newer_than_quote_snapshot")

    return IntakeV3OrderProductionReadinessResponse(
        order_id=order.id if order else None,
        order_code=order.code if order else None,
        quote_id=order.quote_id if order else (quote.id if quote else None),
        quote_code=quote.code if quote else None,
        source_module=INTAKE_V3_SOURCE_MODULE if is_iv3 else None,
        source_workspace_id=str(workspace_id) if workspace_id else None,
        is_intake_v3_order=is_iv3,
        created_from_guarded_convert=created_from_guarded,
        order_status=order.status if order else None,
        production_readiness_status=status,
        ready_for_handoff_preview=ready_preview,
        can_generate_execution_plan_now=False,
        can_generate_execution_tasks_now=False,
        can_mutate_inventory_now=False,
        can_start_production_now=False,
        available_data=build_iv3_order_available_data_summary(
            order,
            quote,
            quote_linkage,
            order_linkage,
            sections_override=sections_override,
            workspace_override=workspace_override,
            linkage_sections=linkage_sections,
        ),
        missing_requirements=missing,
        handoff_preview=build_iv3_order_handoff_preview(
            order,
            quote,
            quote_linkage,
            order_linkage,
        ),
        task_generation_preview_contract=build_iv3_order_task_generation_preview_contract(quote_linkage),
        material_readiness_preview_contract=build_iv3_order_material_readiness_preview_contract(
            quote_linkage
        ),
        production_readiness_blockers=[item.code for item in blocking],
        execution_plan_created=False,
        execution_task_created=False,
        inventory_mutated=False,
        production_started=False,
        warnings=readiness_warnings,
    )


async def _attach_material_availability_to_readiness(
    db: AsyncSession,
    response: IntakeV3OrderProductionReadinessResponse,
    *,
    order_id: int | None = None,
    quote_id: int | None = None,
    workspace_id: str | None = None,
) -> IntakeV3OrderProductionReadinessResponse:
    from services.intake_v3_material_availability_service import (
        downstream_readiness_warnings,
        downstream_summary_fields,
        get_material_availability_for_order,
        get_material_availability_for_quote,
        get_material_availability_for_workspace,
    )

    if order_id is not None:
        availability = await get_material_availability_for_order(db, order_id)
    elif quote_id is not None:
        availability = await get_material_availability_for_quote(db, quote_id)
    elif workspace_id is not None:
        availability = await get_material_availability_for_workspace(db, workspace_id)
    else:
        return response

    summary_fields = downstream_summary_fields(availability)
    warnings = list(response.warnings)
    warnings.extend(downstream_readiness_warnings(availability))
    return response.model_copy(
        update={
            "available_data": response.available_data.model_copy(update=summary_fields),
            "warnings": list(dict.fromkeys(warnings)),
        }
    )


async def _attach_procurement_preview_to_readiness(
    db: AsyncSession,
    response: IntakeV3OrderProductionReadinessResponse,
    *,
    order_id: int | None = None,
    quote_id: int | None = None,
    workspace_id: str | None = None,
) -> IntakeV3OrderProductionReadinessResponse:
    from services.intake_v3_procurement_preview_service import (
        downstream_readiness_warnings as procurement_readiness_warnings,
        downstream_summary_fields as procurement_summary_fields,
        get_procurement_preview_for_order,
        get_procurement_preview_for_quote,
        get_procurement_preview_for_workspace,
    )

    if order_id is not None:
        preview = await get_procurement_preview_for_order(db, order_id)
    elif quote_id is not None:
        preview = await get_procurement_preview_for_quote(db, quote_id)
    elif workspace_id is not None:
        preview = await get_procurement_preview_for_workspace(db, workspace_id)
    else:
        return response

    summary_fields = procurement_summary_fields(preview)
    warnings = list(response.warnings)
    warnings.extend(procurement_readiness_warnings(preview))
    return response.model_copy(
        update={
            "available_data": response.available_data.model_copy(update=summary_fields),
            "warnings": list(dict.fromkeys(warnings)),
        }
    )


async def get_iv3_order_production_readiness(
    db: AsyncSession,
    order_id: int,
) -> IntakeV3OrderProductionReadinessResponse:
    orders_service = OrdersService(db)
    order = await orders_service.get_by_id(order_id)
    if order is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "order_not_found", "order_id": order_id},
        )

    order_linkage = load_iv3_order_linkage(order)
    quote = await load_source_quote_for_iv3_order(db, order)
    quote_linkage, quote_warnings = load_quote_intake_v3_linkage(quote)
    linkage_sections = dict(_snapshot_sections(quote_linkage))
    sections = dict(linkage_sections)
    workspace = _load_workspace_from_sections(sections)
    from services.intake_v3_material_quantity_breakdown_service import (
        hydrate_live_workspace_snapshot_sections,
    )

    sections, workspace = await hydrate_live_workspace_snapshot_sections(
        db, quote_linkage, sections, workspace
    )
    response = build_iv3_order_production_readiness_response(
        order,
        quote,
        quote_linkage,
        order_linkage,
        quote_note_warnings=quote_warnings,
        sections_override=sections,
        workspace_override=workspace,
        linkage_sections=linkage_sections,
    )
    response = await _attach_material_availability_to_readiness(db, response, order_id=order_id)
    return await _attach_procurement_preview_to_readiness(db, response, order_id=order_id)


async def get_iv3_order_production_readiness_by_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3OrderProductionReadinessResponse:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "quote_not_found", "quote_id": quote_id},
        )

    order = await check_existing_order_for_iv3_quote(db, quote_id)
    quote_linkage, quote_warnings = load_quote_intake_v3_linkage(quote)
    linkage_sections = dict(_snapshot_sections(quote_linkage))
    if order is None:
        sections = dict(linkage_sections)
        workspace = _load_workspace_from_sections(sections)
        from services.intake_v3_material_quantity_breakdown_service import (
            hydrate_live_workspace_snapshot_sections,
        )

        sections, workspace = await hydrate_live_workspace_snapshot_sections(
            db, quote_linkage, sections, workspace
        )
        response = build_iv3_order_production_readiness_response(
            None,
            quote,
            quote_linkage,
            None,
            quote_note_warnings=quote_warnings,
            sections_override=sections,
            workspace_override=workspace,
            linkage_sections=linkage_sections,
        )
        response = await _attach_material_availability_to_readiness(db, response, quote_id=quote_id)
        return await _attach_procurement_preview_to_readiness(db, response, quote_id=quote_id)

    order_linkage = load_iv3_order_linkage(order)
    sections = dict(linkage_sections)
    workspace = _load_workspace_from_sections(sections)
    from services.intake_v3_material_quantity_breakdown_service import (
        hydrate_live_workspace_snapshot_sections,
    )

    sections, workspace = await hydrate_live_workspace_snapshot_sections(
        db, quote_linkage, sections, workspace
    )
    response = build_iv3_order_production_readiness_response(
        order,
        quote,
        quote_linkage,
        order_linkage,
        quote_note_warnings=quote_warnings,
        sections_override=sections,
        workspace_override=workspace,
        linkage_sections=linkage_sections,
    )
    response = await _attach_material_availability_to_readiness(db, response, quote_id=quote_id)
    return await _attach_procurement_preview_to_readiness(db, response, quote_id=quote_id)


async def get_iv3_order_production_readiness_by_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3OrderProductionReadinessResponse:
    quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if quote is None:
        return IntakeV3OrderProductionReadinessResponse(
            production_readiness_status=STATUS_MISSING_QUOTE_LINKAGE,
            source_workspace_id=workspace_id,
            missing_requirements=[
                _missing(
                    "missing_quote",
                    "No Intake V3 quote exists for this workspace.",
                    source="quotes.intake_code",
                )
            ],
            production_readiness_blockers=["missing_quote"],
        )

    response = await get_iv3_order_production_readiness_by_quote(db, quote.id)
    if response.source_workspace_id and response.source_workspace_id != workspace_id:
        response.warnings.append("WORKSPACE_ID_MISMATCH")
    return response


async def assert_no_execution_inventory_side_effects(db: AsyncSession) -> dict[str, int]:
    """Helper for tests — snapshot counts only."""
    plans = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    movements = await db.scalar(select(func.count()).select_from(StockMovement))
    return {
        "execution_plan_count": int(plans or 0),
        "stock_movement_count": int(movements or 0),
    }
