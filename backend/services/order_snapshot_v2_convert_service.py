"""Order Snapshot V2 convert service (Step 9.2).

Converts accepted Quote Snapshot V2 to a locked order with frozen snapshot_v2_json.
Does NOT call /price, QuoteOrchestrator, CostEngine, or create ExecutionPlan.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.product_contracts import iso_now
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from models.quotes import Quotes
from schemas.auth import UserResponse
from schemas.order_snapshot_v2 import OrderSnapshotV2, OrderSnapshotV2ConvertResult
from schemas.quote_snapshot_v2 import QuoteSnapshotProvenanceEntry, QuoteSnapshotV2
from services.intake_v3_guarded_convert_to_order_service import (
    IV3_ORDER_STATUS_LOCKED,
    check_existing_order_for_iv3_quote,
)
from services.intake_v3_quote_linkage_utils import (
    ACCEPT_DECISION_JSON_KEY,
    CONVERT_DECISION_JSON_KEY,
    get_accept_decision_record,
    is_pricing_review_completed,
)
from services.intake_v4_quote_linkage_utils import (
    V4_ACCEPTED_STATUS,
    is_v4_accept_completed,
    is_v4_convert_completed,
)
from services.intake_v4_commercial_quote_service import INTAKE_V6_SOURCE_MODULE
from services.intake_v6_commercial_quote_service import (
    INTAKE_V6_LINKAGE_JSON_KEY,
    parse_intake_v6_linkage_from_notes,
)
from services.orders import OrdersService
from services.quotes import QuotesService
from services.quote_snapshot_v2_accept_gate_service import (
    HARD_BLOCKED_READINESS,
    validate_snapshot_for_accept,
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
)


def _raise_blocked(error: str, message: str, blockers: list[str] | None = None) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "blockers": blockers or [error],
        },
    )


def _compute_content_hash(snapshot_json: str) -> str:
    return hashlib.sha256(snapshot_json.encode()).hexdigest()[:32]


def _require_v6_linkage(quote: Quotes) -> dict[str, Any]:
    if not str(quote.intake_code or "").startswith("IV6-"):
        _raise_blocked("NOT_IV6_QUOTE", "Quote intake_code is not an Intake V6 linkage code.")
    linkage = parse_intake_v6_linkage_from_notes(quote.notes)
    if linkage is None:
        _raise_blocked("NOT_IV6_QUOTE", "Quote is not linked to Intake V6.")
    return linkage


def _update_linkage_in_notes(notes: str | None, linkage: dict[str, Any]) -> str:
    payload: dict[str, Any]
    if not notes:
        payload = {}
    else:
        try:
            parsed = json.loads(notes)
        except json.JSONDecodeError:
            parsed = {}
        payload = parsed if isinstance(parsed, dict) else {}
    payload[INTAKE_V6_LINKAGE_JSON_KEY] = linkage
    return json.dumps(payload, default=str)


def _validate_convert_confirmations(body: dict[str, Any]) -> None:
    if not all(
        (
            body.get("reviewer_confirmation"),
            body.get("confirm_quote_accepted"),
            body.get("confirm_pricing_review_completed"),
            body.get("confirm_create_order_only"),
            body.get("confirm_no_execution_plan"),
            body.get("confirm_no_execution_tasks"),
            body.get("confirm_no_inventory"),
            body.get("confirm_production_separate"),
        )
    ):
        _raise_blocked("CONFIRMATIONS_REQUIRED", "All convert confirmations must be true.")


def _validate_partial_accept_gate(linkage: dict[str, Any], record: QuoteSnapshotV2Record) -> None:
    if record.readiness != "partial_with_owner_decisions":
        return
    accept_record = get_accept_decision_record(linkage) or {}
    snapshot_v2_meta = accept_record.get("snapshot_v2")
    if not isinstance(snapshot_v2_meta, dict):
        _raise_blocked(
            "PARTIAL_SNAPSHOT_ACCEPT_GATE_MISSING",
            "Partial snapshot requires accept gate metadata in accept_decision.",
            ["partial_snapshot_accept_gate_missing"],
        )
    if snapshot_v2_meta.get("gate_status") != "snapshot_ready_for_acceptance":
        _raise_blocked(
            "PARTIAL_SNAPSHOT_ACCEPT_GATE_INCOMPLETE",
            "Partial snapshot accept gate was not captured at accept time.",
            ["partial_snapshot_accept_gate_incomplete"],
        )


def _resolve_commercial_total_amount(
    parsed: QuoteSnapshotV2,
) -> tuple[float, str]:
    commercial = parsed.commercial_price_proposal_snapshot
    if commercial is None:
        _raise_blocked(
            "SNAPSHOT_COMMERCIAL_MISSING",
            "CommercialPriceProposal snapshot missing.",
            ["commercial_snapshot_missing"],
        )
    total = commercial.commercial_total
    if total is None or float(total) <= 0:
        _raise_blocked(
            "SNAPSHOT_COMMERCIAL_TOTAL_MISSING",
            "Commercial snapshot total is required for order convert.",
            ["commercial_total_missing"],
        )
    currency = str(commercial.currency or "RON").strip().upper()
    if currency != "RON":
        _raise_blocked(
            "ORDER_CONVERT_CURRENCY_POLICY_REQUIRED",
            "Order convert from Quote Snapshot V2 requires RON commercial currency (no live FX).",
            ["ORDER_CONVERT_CURRENCY_POLICY_REQUIRED"],
        )
    return float(total), currency


def _component_scope_fields_from_quote(parsed: QuoteSnapshotV2) -> dict[str, Any]:
    """Copy frozen component scope verbatim — no resolver or aggregate rebuild."""
    return {
        "component_scope_version": parsed.component_scope_version,
        "offer_scope_snapshot": parsed.offer_scope_snapshot,
        "active_scope_snapshot": parsed.active_scope_snapshot,
        "component_instances": list(parsed.component_instances),
        "geometry_input_snapshot": parsed.geometry_input_snapshot,
        "product_aggregate_snapshot": parsed.product_aggregate_snapshot,
    }


def _enrich_order_provenance_with_product_truth(
    parsed: QuoteSnapshotV2,
    linkage: dict[str, Any],
) -> dict[str, Any]:
    """Product Truth freeze flags for audit (bag form used by readiness dry-run)."""
    base = dict(parsed.provenance or {}) if isinstance(parsed.provenance, dict) else {}
    base["product_truth_revision"] = linkage.get("product_truth_revision")
    base["product_truth_content_hash"] = linkage.get("product_truth_content_hash")
    base["freeze_from_pinned_product_truth"] = linkage.get("freeze_from_pinned_product_truth")
    base["no_live_workspace_reread"] = True
    return base


def _order_provenance_entries(
    parsed: QuoteSnapshotV2,
    linkage: dict[str, Any],
) -> list[QuoteSnapshotProvenanceEntry]:
    """OrderSnapshotV2.provenance is a list — never a dict bag."""
    entries: list[QuoteSnapshotProvenanceEntry] = []
    raw = parsed.provenance
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, QuoteSnapshotProvenanceEntry):
                entries.append(item)
            elif isinstance(item, dict):
                entries.append(QuoteSnapshotProvenanceEntry.model_validate(item))
    truth_bag = {
        "product_truth_revision": linkage.get("product_truth_revision"),
        "product_truth_content_hash": linkage.get("product_truth_content_hash"),
        "freeze_from_pinned_product_truth": linkage.get(
            "freeze_from_pinned_product_truth"
        ),
        "no_live_workspace_reread": True,
    }
    for key, value in truth_bag.items():
        entries.append(
            QuoteSnapshotProvenanceEntry(
                key=key,
                source="product_truth_freeze",
                detail="" if value is None else str(value),
            )
        )
    return entries


def _build_order_snapshot_v2(
    *,
    quote: Quotes,
    record: QuoteSnapshotV2Record,
    parsed: QuoteSnapshotV2,
    commercial_total: float,
    currency: str,
    linkage: dict[str, Any],
    current_user: UserResponse,
    order_id: int | None = None,
) -> OrderSnapshotV2:
    accept_record = get_accept_decision_record(linkage) or {}
    internal_total = None
    if parsed.estimated_internal_cost_snapshot is not None:
        raw_internal = parsed.estimated_internal_cost_snapshot.estimated_total_internal_cost
        internal_total = float(raw_internal) if raw_internal is not None else None

    converted_at = datetime.now(timezone.utc).isoformat()
    converted_by = current_user.name or current_user.email

    return OrderSnapshotV2(
        snapshot_code=record.snapshot_code,
        content_hash=record.content_hash,
        order_id=order_id,
        quote_id=quote.id,
        quote_snapshot_v2_id=record.id,
        product_definition_snapshot=parsed.product_definition_snapshot,
        **_component_scope_fields_from_quote(parsed),
        commercial_price_proposal_snapshot=parsed.commercial_price_proposal_snapshot,
        estimated_internal_cost_snapshot=parsed.estimated_internal_cost_snapshot,
        accepted_commercial_total=commercial_total,
        accepted_currency=currency,
        estimated_internal_total=internal_total,
        owner_decisions_snapshot=parsed.owner_decisions_snapshot,
        warnings_snapshot=parsed.warnings_snapshot,
        blockers_snapshot=parsed.blockers_snapshot,
        provenance=_order_provenance_entries(parsed, linkage),
        accepted_at=accept_record.get("accepted_at"),
        accepted_by=accept_record.get("accepted_by_display_name") or accept_record.get("accepted_by_user_id"),
        converted_at=converted_at,
        converted_by=converted_by,
        no_reprice_policy=True,
        execution_plan_source="order_snapshot_v2",
        execution_plan_created=False,
        notes=parsed.notes,
        input_summary=parsed.input_summary,
    )


async def convert_accepted_quote_snapshot_v2_to_order(
    db: AsyncSession,
    quote_id: int,
    body: dict[str, Any],
    current_user: UserResponse,
) -> dict[str, Any]:
    """Convert an accepted V6 quote with Quote Snapshot V2 into a locked order."""
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found.")

    snapshot_v2_id = getattr(quote, "accepted_snapshot_v2_id", None)
    if not snapshot_v2_id:
        _raise_blocked(
            "MISSING_ACCEPTED_SNAPSHOT_V2",
            "Quote has no accepted_snapshot_v2_id — use legacy convert path.",
            ["missing_accepted_snapshot_v2"],
        )

    linkage = _require_v6_linkage(quote)
    _validate_convert_confirmations(body)

    existing_order = await check_existing_order_for_iv3_quote(db, quote_id)
    if existing_order is not None or is_v4_convert_completed(linkage):
        _raise_blocked(
            "ORDER_ALREADY_EXISTS",
            f"An order already exists for quote id={quote.id}.",
            ["ORDER_ALREADY_EXISTS"],
        )

    if not is_v4_accept_completed(linkage, quote.status) or quote.status != V4_ACCEPTED_STATUS:
        _raise_blocked("QUOTE_NOT_ACCEPTED", "Quote must be accepted before convert.")
    if bool(linkage.get("requires_pricing_review", True)) or not is_pricing_review_completed(linkage):
        _raise_blocked("PRICING_REVIEW_REQUIRED", "Pricing review must be completed before convert.")

    record = await db.get(QuoteSnapshotV2Record, int(snapshot_v2_id))
    if record is None:
        _raise_blocked(
            "SNAPSHOT_V2_NOT_FOUND",
            f"Quote Snapshot V2 id={snapshot_v2_id} was not found.",
            ["snapshot_v2_not_found"],
        )

    if record.quote_id is not None and record.quote_id != quote.id:
        _raise_blocked(
            "SNAPSHOT_QUOTE_MISMATCH",
            "Accepted snapshot quote_id does not match quote.",
            ["snapshot_quote_mismatch"],
        )

    if record.status != "frozen":
        _raise_blocked(
            "SNAPSHOT_NOT_FROZEN",
            f"Snapshot status {record.status!r} is not acceptable for convert.",
            ["snapshot_not_frozen"],
        )

    if record.readiness in HARD_BLOCKED_READINESS:
        _raise_blocked(
            "SNAPSHOT_READINESS_BLOCKED",
            f"Snapshot readiness {record.readiness!r} blocks convert.",
            [record.readiness],
        )

    _validate_partial_accept_gate(linkage, record)

    gate_result = validate_snapshot_for_accept(
        record,
        quote_id=quote.id,
        workspace_id=linkage.get("source_workspace_id"),
        confirm_owner_decisions_acknowledged=True,
    )
    if not gate_result.accept_allowed:
        _raise_blocked(
            gate_result.error_code or "SNAPSHOT_CONVERT_BLOCKED",
            gate_result.message or "Quote Snapshot V2 convert gate blocked.",
            gate_result.blockers or [gate_result.gate_status],
        )

    try:
        parsed = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    except Exception as exc:
        _raise_blocked(
            "SNAPSHOT_JSON_INVALID",
            f"Snapshot JSON invalid: {exc}",
            ["snapshot_json_invalid"],
        )

    commercial_total, currency = _resolve_commercial_total_amount(parsed)

    if parsed.estimated_internal_cost_snapshot is None:
        _raise_blocked(
            "SNAPSHOT_INTERNAL_MISSING",
            "EstimatedInternalCost snapshot missing.",
            ["internal_snapshot_missing"],
        )

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))

    order_snapshot = _build_order_snapshot_v2(
        quote=quote,
        record=record,
        parsed=parsed,
        commercial_total=commercial_total,
        currency=currency,
        linkage=linkage,
        current_user=current_user,
    )
    snapshot_v2_json = order_snapshot.model_dump_json()

    order_code = f"ORD-IV6-V2-{int(datetime.now(timezone.utc).timestamp())}-{quote.id}"
    readiness_snapshot = {
        "source": "order_snapshot_v2_convert",
        "snapshot_type": "order_snapshot_v2_at_order_creation",
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "quote_status": quote.status,
        "source_intake_version": "V6",
        "quote_snapshot_v2_id": record.id,
        "requires_production_handoff_build": True,
        "production_started": False,
        "execution_plan_created": False,
        "inventory_mutated": False,
        "no_execution_plan_created": True,
    }

    orders_service = OrdersService(db)
    order = await orders_service.create(
        {
            "code": order_code,
            "quote_id": quote.id,
            "quote_code": quote.code,
            "client_name": quote.client_name,
            "contact_person": quote.contact_person,
            "status": IV3_ORDER_STATUS_LOCKED,
            "payment_status": "pending",
            "total_amount": commercial_total,
            "locked_at": iso_now(),
            "snapshot_version": 1,
            "snapshot_line_items": None,
            "quote_snapshot_v2_id": record.id,
            "snapshot_v2_json": snapshot_v2_json,
            "notes": None,
            "readiness_snapshot": readiness_snapshot,
        }
    )
    if order is None:
        _raise_blocked("ORDER_CREATE_FAILED", "Order persistence failed.")

    order_snapshot.order_id = order.id
    snapshot_v2_json = order_snapshot.model_dump_json()
    order.snapshot_v2_json = snapshot_v2_json
    await db.commit()
    await db.refresh(order)

    convert_record = {
        "status": "approved",
        "converted_at": datetime.now(timezone.utc).isoformat(),
        "converted_by_user_id": current_user.id,
        "converted_by_display_name": current_user.name or current_user.email,
        "source": INTAKE_V6_SOURCE_MODULE,
        "order_created": True,
        "order_id": order.id,
        "order_code": order.code,
        "quote_snapshot_v2_id": record.id,
        "accepted_commercial_total": commercial_total,
        "accepted_currency": currency,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "pricing_source": "quote_snapshot_v2",
    }
    linkage = dict(linkage)
    linkage[CONVERT_DECISION_JSON_KEY] = convert_record
    linkage[ACCEPT_DECISION_JSON_KEY] = linkage.get(ACCEPT_DECISION_JSON_KEY)
    updated_notes = _update_linkage_in_notes(quote.notes, linkage)
    await quotes_service.update(quote.id, {"notes": updated_notes})
    await db.commit()
    await db.refresh(order)

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before + 1 or plans_after != plans_before:
        await db.rollback()
        _raise_blocked("SAFETY_VIOLATION", "Unexpected order or execution plan side effect during convert.")

    result = OrderSnapshotV2ConvertResult(
        status="converted",
        quote_id=quote.id,
        quote_code=quote.code,
        order_id=order.id,
        order_code=order.code,
        order_status=order.status,
        quote_snapshot_v2_id=record.id,
        accepted_commercial_total=commercial_total,
        accepted_currency=currency,
        estimated_internal_total=order_snapshot.estimated_internal_total,
    )

    return {
        "converted": True,
        "quote_id": quote.id,
        "quote_code": quote.code,
        "quote_status": quote.status,
        "order_id": order.id,
        "order_code": order.code,
        "order_status": order.status,
        "source_module": INTAKE_V6_SOURCE_MODULE,
        "order_created": True,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "creates_execution_tasks": False,
        "writes_execution_plan": False,
        "stock_consumption": False,
        "order_snapshot_v2_convert": result.model_dump(mode="json"),
        "v6_order_conversion": {
            "converted": True,
            "order_id": order.id,
            "blocked_reasons": [],
        },
    }
