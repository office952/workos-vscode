"""Intake V4 guarded draft quote creation — pricing_input snapshot + QuoteWizard handoff (Sprint 3)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake_v4_workspace import IntakeV4WorkspaceRecord
from models.product_template_module_links import ProductTemplateModuleLink
from schemas.auth import UserResponse
from schemas.intake_v4 import (
    IntakeV4CreateDraftQuoteRequest,
    IntakeV4CreateDraftQuoteResponse,
    IntakeV4QuoteHandoffPreviewResponse,
    IntakeV4WorkspacePayload,
)
from services.intake_v4_internal_draft_quote_policy_service import (
    client_order_production_flags_for_quote,
    evaluate_internal_draft_quote_policy,
)
from services.intake_v4_pricing_input_service import build_v4_pricing_input_preview
from services.intake_v4_workspace_service import _get_record_or_404, _json_loads, _parse_payload
from services.quotes import QuotesService

logger = logging.getLogger(__name__)

INTAKE_V4_SOURCE_MODULE = "intake_v4"
INTAKE_V6_SOURCE_MODULE = "intake_v6"
INTAKE_V4_LINKAGE_CODE_PREFIX = "IV4-"
INTAKE_V6_LINKAGE_CODE_PREFIX = "IV6-"
INTAKE_V4_LINKAGE_JSON_KEY = "intake_v4_linkage_v1"
PRICING_SOURCE = "intake_v4_pricing_input_preview"
SNAPSHOT_POLICY_VERSION = "intake_v4_quote_handoff_v1"
METAL_SUPPORT_MOUNTING_SYSTEMS = frozenset({"steel_bars", "aluminum_bars"})


def intake_v4_linkage_code(workspace_id: str) -> str:
    return f"{INTAKE_V4_LINKAGE_CODE_PREFIX}{workspace_id}"


def _source_module_for_record(record: IntakeV4WorkspaceRecord) -> str:
    return INTAKE_V6_SOURCE_MODULE if str(record.workspace_code or "").startswith("IV6-") else INTAKE_V4_SOURCE_MODULE


def _source_version_for_record(record: IntakeV4WorkspaceRecord) -> str:
    return "V6" if _source_module_for_record(record) == INTAKE_V6_SOURCE_MODULE else "V4"


def _linkage_code_for_record(record: IntakeV4WorkspaceRecord) -> str:
    prefix = INTAKE_V6_LINKAGE_CODE_PREFIX if _source_module_for_record(record) == INTAKE_V6_SOURCE_MODULE else INTAKE_V4_LINKAGE_CODE_PREFIX
    return f"{prefix}{record.id}"


def _json_field(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


async def _build_linked_module_lines(
    db: AsyncSession,
    *,
    payload: IntakeV4WorkspacePayload,
    quote_input: dict[str, Any],
) -> list[dict[str, Any]]:
    setup = payload.finish_setup
    mounting_system = str(setup.mounting_system or "").strip() if setup else ""
    if mounting_system not in METAL_SUPPORT_MOUNTING_SYSTEMS:
        return []

    result = await db.execute(
        select(ProductTemplateModuleLink).where(
            ProductTemplateModuleLink.parent_template_code == payload.product_binding.template_code,
            ProductTemplateModuleLink.trigger_field == "metal_support_required",
            ProductTemplateModuleLink.active.is_(True),
        )
    )
    links = result.scalars().all()
    modules: list[dict[str, Any]] = []
    width_mm = quote_input.get("width_mm")
    support_material = "aluminum" if mounting_system == "aluminum_bars" else "steel"
    for link in links:
        defaults = _json_field(link.default_values_json, {})
        module_input = dict(defaults if isinstance(defaults, dict) else {})
        if width_mm is not None:
            premount_length_ml = round(float(width_mm) / 1000.0, 4)
            module_input["premount_bar_length_ml"] = premount_length_ml
            module_input["mounting_bar_length_m"] = premount_length_ml
            module_input["letter_perimeter_m"] = premount_length_ml
        module_input["bar_material"] = support_material
        module_input["mounting_bar_profile"] = quote_input.get("mounting_bar_profile") or module_input.get("mounting_bar_profile")
        modules.append(
            {
                "parent_template_code": link.parent_template_code,
                "module_template_code": link.module_template_code,
                "relation_type": link.relation_type,
                "trigger_field": link.trigger_field,
                "trigger_value": True,
                "pricing_mode": link.pricing_mode,
                "execution_mode": link.execution_mode,
                "input_payload": module_input,
            }
        )
    return modules


def _raise_blocked(error: str, message: str, blockers: list[str] | None = None) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "blockers": blockers or [error],
            "fatal_blockers": blockers or [error],
        },
    )


def evaluate_v4_quote_handoff_blockers(
    record: IntakeV4WorkspaceRecord,
    payload: IntakeV4WorkspacePayload,
    *,
    pricing_preview: Any | None = None,
    client_analysis_hash: str | None = None,
) -> list[str]:
    """Legacy flat blocker list — fatal blockers plus review warnings."""
    policy = evaluate_internal_draft_quote_policy(
        record,
        payload,
        pricing_preview=pricing_preview,
        client_analysis_hash=client_analysis_hash,
        include_hash_sync=True,
    )
    return [*policy.fatal_blockers, *policy.review_warnings]


def resolve_v4_quote_handoff_status_label(blockers: list[str]) -> str:
    from services.intake_v4_internal_draft_quote_policy_service import (
        classify_handoff_issue_codes,
        resolve_internal_draft_quote_status_label,
    )

    fatal, warnings = classify_handoff_issue_codes(blockers)
    return resolve_internal_draft_quote_status_label(fatal, warnings)


async def get_quote_handoff_preview_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    *,
    client_analysis_hash: str | None = None,
) -> IntakeV4QuoteHandoffPreviewResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    payload = _parse_payload(payload_raw if isinstance(payload_raw, dict) else {})
    pricing_preview = build_v4_pricing_input_preview(workspace_id=workspace_id, payload=payload)
    policy = evaluate_internal_draft_quote_policy(
        record,
        payload,
        pricing_preview=pricing_preview,
        client_analysis_hash=client_analysis_hash,
        include_hash_sync=bool(client_analysis_hash),
    )
    legacy_blockers = [*policy.fatal_blockers, *policy.review_warnings]
    return IntakeV4QuoteHandoffPreviewResponse(
        workspace_id=workspace_id,
        workspace_readiness_status=record.readiness_status,
        handoff_allowed=policy.can_create_internal_draft_quote,
        status_label=policy.status_label,  # type: ignore[arg-type]
        blockers=legacy_blockers,
        can_create_internal_draft_quote=policy.can_create_internal_draft_quote,
        requires_operator_confirmation=policy.requires_operator_confirmation,
        operator_confirmation_complete=policy.operator_confirmation_complete,
        fatal_blockers=policy.fatal_blockers,
        review_warnings=policy.review_warnings,
        client_send_allowed=policy.client_send_allowed,
        accept_allowed=policy.accept_allowed,
        convert_to_order_allowed=policy.convert_to_order_allowed,
        production_allowed=policy.production_allowed,
        preview_only=True,
    )


def parse_intake_v4_linkage_from_notes(notes: str | None) -> dict[str, Any] | None:
    if not notes:
        return None
    try:
        payload = json.loads(notes)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    linkage = payload.get(INTAKE_V4_LINKAGE_JSON_KEY)
    return linkage if isinstance(linkage, dict) else None


async def check_existing_quote_for_intake_v4_workspace(
    db: AsyncSession,
    workspace_id: str,
    record: IntakeV4WorkspaceRecord | None = None,
):
    linkage_code = _linkage_code_for_record(record) if record is not None else intake_v4_linkage_code(workspace_id)
    quotes_service = QuotesService(db)
    existing = await quotes_service.list_by_field("intake_code", linkage_code, limit=1)
    return existing[0] if existing else None


def build_v4_quote_snapshot_payload(
    *,
    workspace_id: str,
    workspace_code: str,
    payload: IntakeV4WorkspacePayload,
    pricing_preview: Any,
    current_user: UserResponse,
    decision_reason: str,
    review_warnings: list[str],
    source_module: str = INTAKE_V4_SOURCE_MODULE,
    linked_modules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    downstream_flags = client_order_production_flags_for_quote(review_warnings=review_warnings)
    integrity_rules = [
        "NEST2_GEOMETRY_OPERATOR_CONFIRMED",
        "CLIENT_ANALYSIS_HASH_SYNCED",
        "DRAFT_QUOTE_REQUIRES_PRICING_REVIEW",
        "NO_ORDER_NO_EXECUTION_NO_INVENTORY",
        "INTERNAL_DRAFT_REVIEW_ONLY",
    ]
    if review_warnings:
        integrity_rules.append("ARTWORK_OR_REVIEW_WARNING_BLOCKS_CLIENT_HANDOFF")

    return {
        "policy_version": SNAPSHOT_POLICY_VERSION,
        "source_module": source_module,
        "source_workspace_id": workspace_id,
        "source_workspace_code": workspace_code,
        "template_code": payload.product_binding.template_code,
        "quote_input_payload": dict(pricing_preview.quote_input_payload),
        "operation_flags": dict(pricing_preview.operation_flags or {}),
        "finish_summary": dict(pricing_preview.finish_summary or {}),
        "production_counts": dict(pricing_preview.production_counts or {}),
        "workspace_payload_snapshot": payload.model_dump(mode="json"),
        "linked_modules": list(linked_modules or []),
        "review_warnings": list(review_warnings),
        "owner_decision": {
            "owner_user_id": current_user.id,
            "owner_display_name": current_user.name or current_user.email,
            "decision_timestamp": datetime.now(timezone.utc).isoformat(),
            "decision_reason": decision_reason.strip(),
            "approval_source": "intake_v4_confirm_step",
            "internal_draft_quote_confirmed": True,
        },
        "integrity_rules": integrity_rules,
        **downstream_flags,
    }


def build_v4_quote_draft_payload(
    *,
    record: IntakeV4WorkspaceRecord,
    payload: IntakeV4WorkspacePayload,
    snapshot: dict[str, Any],
    quote_input: dict[str, Any],
    requires_pricing_review: bool,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    valid_until = (now + timedelta(days=30)).strftime("%Y-%m-%d")
    source_module = _source_module_for_record(record)
    source_version = _source_version_for_record(record)
    quote_code = f"Q-{source_version}-{record.workspace_code}-{int(now.timestamp())}"
    letter_count = quote_input.get("letter_count") or quote_input.get("real_letters_count") or 1
    try:
        qty = max(int(letter_count), 1)
    except (TypeError, ValueError):
        qty = 1

    line_items = [
        {
            "productCode": payload.product_binding.template_code,
            "description": payload.client.job_title or record.title,
            "quantity": qty,
            "unit_price": 0,
            "total": 0,
        }
    ]
    for module in snapshot.get("linked_modules") or []:
        module_input = module.get("input_payload") if isinstance(module, dict) else {}
        line_items.append(
            {
                "productCode": module.get("module_template_code"),
                "description": "Structură metalică premontaj",
                "quantity": module_input.get("bar_count", 1) if isinstance(module_input, dict) else 1,
                "unit_price": 0,
                "total": 0,
                "pricing_mode": module.get("pricing_mode"),
                "execution_mode": module.get("execution_mode"),
                "input_payload": module_input,
            }
        )
    linkage = {
        "source_module": source_module,
        "source_intake_version": source_version,
        "source_workspace_id": record.id,
        "source_workspace_code": record.workspace_code,
        "requires_pricing_review": requires_pricing_review,
        "pricing_source": PRICING_SOURCE,
        "snapshot": snapshot,
        "snapshot_policy_version": SNAPSHOT_POLICY_VERSION,
        "quote_input_payload": quote_input,
        "client_send_allowed": snapshot.get("client_send_allowed", False),
        "accept_allowed": snapshot.get("accept_allowed", False),
        "convert_to_order_allowed": snapshot.get("convert_to_order_allowed", False),
        "production_allowed": snapshot.get("production_allowed", False),
        "internal_draft_review_only": snapshot.get("internal_draft_review_only", True),
    }
    notes_payload = {
        "human_summary": (
            f"Draft quote from Intake {source_version} workspace {record.workspace_code}. "
            "Requires pricing review in QuoteWizard — no final commercial price. "
            "Internal review-only draft — not approved for client send, order, or production."
        ),
        INTAKE_V4_LINKAGE_JSON_KEY: linkage,
    }
    return {
        "code": quote_code,
        "intake_id": None,
        "intake_code": _linkage_code_for_record(record),
        "client_id": None,
        "client_name": payload.client.client_name or "Unknown Client",
        "contact_person": None,
        "status": "draft",
        "version": 1,
        "valid_until": valid_until,
        "line_items": json.dumps(line_items),
        "subtotal": 0.0,
        "discount": 0.0,
        "discount_pct": 0.0,
        "total_before_vat": 0.0,
        "vat": 0.0,
        "grand_total": 0.0,
        "margin_pct": 0.0,
        "notes": json.dumps(notes_payload, default=str),
        "assigned_to": snapshot.get("owner_decision", {}).get("owner_display_name"),
    }


async def create_guarded_draft_quote_from_intake_v4_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV4CreateDraftQuoteRequest,
    current_user: UserResponse,
) -> IntakeV4CreateDraftQuoteResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    payload = _parse_payload(payload_raw if isinstance(payload_raw, dict) else {})

    pricing_preview = build_v4_pricing_input_preview(workspace_id=workspace_id, payload=payload)
    policy = evaluate_internal_draft_quote_policy(
        record,
        payload,
        pricing_preview=pricing_preview,
        client_analysis_hash=request.client_analysis_hash,
        include_hash_sync=True,
    )

    if not request.confirm_internal_draft_quote:
        _raise_blocked(
            "INTERNAL_DRAFT_CONFIRMATION_REQUIRED",
            "Operator must confirm internal draft quote readiness before creation.",
            ["operator_confirmation_missing"],
        )

    if not payload.finish_setup or not payload.finish_setup.internal_draft_quote_confirmed:
        _raise_blocked(
            "INTERNAL_DRAFT_CONFIRMATION_REQUIRED",
            "Persisted operator confirmation for internal draft quote is missing.",
            ["operator_confirmation_missing"],
        )

    if policy.fatal_blockers:
        _raise_blocked(
            "INTERNAL_DRAFT_QUOTE_BLOCKED",
            "Workspace V4 is not ready for internal draft quote creation.",
            policy.fatal_blockers,
        )

    existing = await check_existing_quote_for_intake_v4_workspace(db, workspace_id, record)
    if existing is not None:
        _raise_blocked(
            "DUPLICATE_QUOTE_FOR_WORKSPACE",
            f"Quote already linked to Intake V4 workspace {workspace_id}.",
            ["DUPLICATE_QUOTE_FOR_WORKSPACE"],
        )

    requires_pricing_review = True if policy.review_warnings else False
    quote_input = dict(pricing_preview.quote_input_payload)
    linked_modules = await _build_linked_module_lines(
        db,
        payload=payload,
        quote_input=quote_input,
    )
    if linked_modules:
        quote_input["parent_mounting_system"] = quote_input.get("mounting_system")
        quote_input["metal_support_required"] = True
        quote_input["linked_support_pricing_mode"] = "separate_quote_line"
        quote_input["support_module_template_code"] = linked_modules[0].get("module_template_code")
        quote_input["mounting_system"] = "direct_wall"
        quote_input["linked_modules"] = linked_modules

    snapshot = build_v4_quote_snapshot_payload(
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        payload=payload,
        pricing_preview=pricing_preview,
        current_user=current_user,
        decision_reason=request.decision_reason,
        review_warnings=policy.review_warnings,
        source_module=_source_module_for_record(record),
        linked_modules=linked_modules,
    )
    quote_data = build_v4_quote_draft_payload(
        record=record,
        payload=payload,
        snapshot=snapshot,
        quote_input=quote_input,
        requires_pricing_review=requires_pricing_review,
    )

    quotes_service = QuotesService(db)
    try:
        quote_obj = await quotes_service.create(quote_data)
    except Exception as exc:
        logger.error("Intake V4 quote persistence failed for %s: %s", workspace_id, exc, exc_info=True)
        _raise_blocked("QUOTE_PERSISTENCE_FAILED", f"Quote persistence failed: {exc}")

    if quote_obj is None:
        _raise_blocked("QUOTE_PERSISTENCE_FAILED", "Quote persistence returned no object.")

    logger.info(
        "Internal draft quote created from Intake V4: quote_id=%s workspace_id=%s user=%s warnings=%s",
        quote_obj.id,
        workspace_id,
        current_user.id,
        policy.review_warnings,
    )

    downstream = client_order_production_flags_for_quote(review_warnings=policy.review_warnings)
    return IntakeV4CreateDraftQuoteResponse(
        quote_created=True,
        quote_id=quote_obj.id,
        quote_code=quote_obj.code,
        quote_status=quote_obj.status,
        source_module=_source_module_for_record(record),
        source_workspace_id=workspace_id,
        quote_input_payload=quote_input,
        snapshot_attached=True,
        requires_pricing_review=requires_pricing_review,
        client_send_allowed=downstream["client_send_allowed"],
        accept_allowed=downstream["accept_allowed"],
        convert_to_order_allowed=downstream["convert_to_order_allowed"],
        production_allowed=downstream["production_allowed"],
        order_created=False,
        execution_plan_created=False,
        inventory_mutated=False,
    )
