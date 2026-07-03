"""Intake V3 guarded commercial quote draft creation — owner approval + snapshot, no order/execution/inventory."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from models.execution_plan import ExecutionPlan
from models.intake_v3_workspace import IntakeV3WorkspaceRecord
from models.orders import Orders
from models.quotes import Quotes
from schemas.intake_v3 import (
    IntakeV3CommercialQuoteBridgePreview,
    IntakeV3CreateDraftQuoteRequest,
    IntakeV3CreateDraftQuoteResponse,
    IntakeV3QuoteCreationSnapshotPayload,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)
from services.intake_v3_commercial_quote_bridge_service import build_commercial_quote_bridge_preview
from services.intake_v3_quote_creation_dry_run_service import build_intake_v3_quote_creation_dry_run
from services.intake_v3_quote_creation_enablement_policy_service import evaluate_quote_creation_enablement_policy
from services.intake_v3_quote_creation_final_blocker_service import evaluate_quote_creation_final_blockers
from services.intake_v3_quote_creation_guard_policy_service import evaluate_quote_creation_guard_policy
from services.intake_v3_quote_snapshot_policy_service import (
    SNAPSHOT_POLICY_VERSION,
    build_quote_snapshot_hash_marker,
    build_quote_snapshot_policy,
)
from services.intake_v3_real_quote_creation_enablement_readiness_service import (
    evaluate_real_quote_creation_enablement_readiness,
)
from services.intake_v3_workspace_preview_service import build_intake_v3_workspace_preview
from services.quotes import QuotesService
from schemas.auth import UserResponse

logger = logging.getLogger(__name__)

INTAKE_V3_SOURCE_MODULE = "intake_v3"
INTAKE_V3_LINKAGE_CODE_PREFIX = "IV3-"
INTAKE_V3_LINKAGE_JSON_KEY = "intake_v3_linkage_v1"
PRICING_SOURCE = "intake_v3_preview_only"
DECISION_SCOPE = "intake_v3_real_quote_creation"


def intake_v3_linkage_code(workspace_id: str) -> str:
    return f"{INTAKE_V3_LINKAGE_CODE_PREFIX}{workspace_id}"


def parse_intake_v3_linkage_from_notes(notes: str | None) -> dict[str, Any] | None:
    if not notes:
        return None
    try:
        payload = json.loads(notes)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    linkage = payload.get(INTAKE_V3_LINKAGE_JSON_KEY)
    return linkage if isinstance(linkage, dict) else None


def _raise_blocked(error: str, message: str, blockers: list[str] | None = None) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "blockers": blockers or [error],
        },
    )


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


async def _get_record_or_404(db: AsyncSession, workspace_id: str) -> IntakeV3WorkspaceRecord:
    result = await db.execute(
        select(IntakeV3WorkspaceRecord).where(IntakeV3WorkspaceRecord.id == workspace_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "workspace_not_found", "workspace_id": workspace_id},
        )
    return record


def _load_workspace_from_record(record: IntakeV3WorkspaceRecord) -> IntakeV3Workspace:
    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}
    return IntakeV3Workspace.model_validate(payload)


def _build_policy_chain(
    workspace: IntakeV3Workspace,
    record: IntakeV3WorkspaceRecord,
    *,
    archived: bool,
) -> dict[str, Any]:
    build_result = build_intake_v3_workspace_preview(workspace)
    preview = build_result.preview
    dry_run = build_intake_v3_quote_creation_dry_run(
        workspace,
        preview,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    guard_policy = evaluate_quote_creation_guard_policy(
        workspace,
        preview,
        dry_run,
        workspace_archived=archived,
    )
    bridge = build_commercial_quote_bridge_preview(
        workspace,
        preview,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    final_blocker_check = evaluate_quote_creation_final_blockers(
        workspace,
        preview,
        dry_run,
        guard_policy,
        bridge,
        workspace_archived=archived,
    )
    enablement_policy = evaluate_quote_creation_enablement_policy(
        workspace,
        preview,
        dry_run=dry_run,
        guard_policy=guard_policy,
        bridge=bridge,
        final_blocker_check=final_blocker_check,
        workspace_title=record.title,
        workspace_archived=archived,
    )
    readiness_bundle = evaluate_real_quote_creation_enablement_readiness(
        workspace,
        preview,
        bridge,
        enablement_policy,
        final_blocker_check,
        workspace_archived=archived,
    )
    snapshot_policy = readiness_bundle["snapshot_policy"]
    return {
        "preview": preview,
        "dry_run": dry_run,
        "guard_policy": guard_policy,
        "bridge": bridge,
        "final_blocker_check": final_blocker_check,
        "enablement_policy": enablement_policy,
        "readiness_bundle": readiness_bundle,
        "snapshot_policy": snapshot_policy,
    }


def build_owner_decision_record_for_quote_creation(
    workspace_id: str,
    request: IntakeV3CreateDraftQuoteRequest,
    current_user: UserResponse,
    *,
    workspace: IntakeV3Workspace | None = None,
    preview: IntakeV3WorkspacePreview | None = None,
) -> dict[str, Any]:
    bridge_marker = build_quote_snapshot_hash_marker(workspace, preview)
    return {
        "decision_scope": DECISION_SCOPE,
        "owner_user_id": current_user.id,
        "owner_display_name": current_user.name or current_user.email,
        "decision_status": request.owner_decision.decision_status,
        "decision_timestamp": datetime.now(timezone.utc).isoformat(),
        "decision_reason": request.owner_decision.decision_reason.strip(),
        "approved_workspace_id": workspace_id,
        "approved_bridge_preview_hash_or_marker": bridge_marker,
        "approved_snapshot_policy_version": SNAPSHOT_POLICY_VERSION,
        "approval_source": "UI",
        "approval_checkbox": request.owner_decision.approval_checkbox,
    }


def build_quote_creation_snapshot_payload(
    workspace: IntakeV3Workspace,
    preview: IntakeV3WorkspacePreview,
    bridge: IntakeV3CommercialQuoteBridgePreview,
    owner_decision: dict[str, Any],
    *,
    workspace_id: str,
    workspace_code: str,
    chain: dict[str, Any],
) -> IntakeV3QuoteCreationSnapshotPayload:
    confirmed = workspace.confirmed_production_model
    inner_hole_count = 0
    if confirmed and confirmed.cut_contour_model:
        inner_hole_count = confirmed.cut_contour_model.inner_hole_count
    sections: dict[str, Any] = {
        "workspace_identity_snapshot": {
            "workspace_id": workspace_id,
            "workspace_code": workspace_code,
            "template_code": workspace.product_selection.template_code,
            "job_title": workspace.client_request.job_title,
            "client_name": workspace.client_request.client_name,
        },
        "workspace_payload_snapshot": workspace.model_dump(mode="json"),
        "raw_svg_analysis_reference": {
            "present": workspace.raw_svg_analysis is not None,
            "not_production_truth": True,
            "analysis": workspace.raw_svg_analysis.model_dump(mode="json")
            if workspace.raw_svg_analysis
            else None,
        },
        "confirmed_production_model_snapshot": confirmed.model_dump(mode="json") if confirmed else None,
        "finish_assignment_snapshot": workspace.finish_assignment.model_dump(mode="json")
        if workspace.finish_assignment
        else None,
        "commercial_quote_bridge_snapshot": bridge.model_dump(mode="json"),
        "owner_decision_record_snapshot": owner_decision,
        "quote_readiness_snapshot": preview.quote_readiness.model_dump(mode="json")
        if preview.quote_readiness
        else None,
        "dry_run_snapshot": chain["dry_run"].model_dump(mode="json"),
        "guard_policy_snapshot": chain["guard_policy"].model_dump(mode="json"),
        "final_blocker_check_snapshot": chain["final_blocker_check"].model_dump(mode="json"),
    }
    if preview.finish_variation_summary is not None:
        sections["finish_variation_summary_snapshot"] = preview.finish_variation_summary.model_dump(mode="json")
    if preview.pricing_input_candidate is not None:
        sections["pricing_input_candidate_snapshot"] = preview.pricing_input_candidate.model_dump(mode="json")
    if preview.prequote_review is not None:
        sections["prequote_review_snapshot"] = preview.prequote_review.model_dump(mode="json")

    from services.intake_v3_geometry_metrics_snapshot_service import build_geometry_metrics_snapshot

    geometry_snapshot = build_geometry_metrics_snapshot(
        workspace=workspace,
        source_type="quote",
        source_id=workspace_id,
        path_geometry_summary=workspace.path_geometry_summary,
    )
    sections["geometry_metrics_snapshot"] = geometry_snapshot.model_dump(mode="json")
    if workspace.layer_role_confirmation_snapshot:
        sections["layer_role_confirmation_snapshot"] = workspace.layer_role_confirmation_snapshot

    return IntakeV3QuoteCreationSnapshotPayload(
        policy_version=SNAPSHOT_POLICY_VERSION,
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_workspace_id=workspace_id,
        sections=sections,
        integrity_rules=[
            "RAW_NOT_PRODUCTION_TRUTH",
            "CONFIRMED_MODEL_PRODUCTION_TRUTH",
            "HOLES_NOT_LETTERS",
            "FREEZE_OWNER_APPROVED_STATE",
        ],
        raw_analysis_not_production_truth=True,
        holes_not_letters=inner_hole_count >= 0,
    )


async def check_existing_quote_for_intake_v3_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> Quotes | None:
    linkage_code = intake_v3_linkage_code(workspace_id)
    quotes_service = QuotesService(db)
    existing = await quotes_service.list_by_field("intake_code", linkage_code, limit=1)
    return existing[0] if existing else None


def _validate_owner_decision(
    workspace_id: str,
    request: IntakeV3CreateDraftQuoteRequest,
    current_user: UserResponse | None,
) -> None:
    if current_user is None or not current_user.id:
        _raise_blocked("OWNER_IDENTITY_UNCLEAR", "Current user identity is required for owner decision capture.")
    if request.expected_workspace_id != workspace_id:
        _raise_blocked(
            "WORKSPACE_ID_MISMATCH",
            "expected_workspace_id does not match the workspace being updated.",
        )
    owner = request.owner_decision
    if not owner.approval_checkbox:
        _raise_blocked("OWNER_DECISION_REQUIRED", "Owner approval checkbox must be checked.")
    if owner.decision_status != "approved":
        _raise_blocked("OWNER_DECISION_REQUIRED", "Owner decision_status must be approved.")
    if not owner.decision_reason or not owner.decision_reason.strip():
        _raise_blocked("OWNER_DECISION_REQUIRED", "Owner decision_reason is required.")


def _validate_safety_confirmations(request: IntakeV3CreateDraftQuoteRequest) -> None:
    if not all(
        (
            request.confirm_create_draft_only,
            request.confirm_no_order,
            request.confirm_no_execution,
            request.confirm_no_inventory,
        )
    ):
        _raise_blocked(
            "SAFETY_CONFIRMATIONS_REQUIRED",
            "All draft-only and no-side-effect confirmations must be true.",
        )


def _validate_workspace_completeness(
    workspace: IntakeV3Workspace,
    preview: IntakeV3WorkspacePreview,
    *,
    archived: bool,
) -> None:
    if archived:
        _raise_blocked("WORKSPACE_ARCHIVED", "Archived workspaces cannot create quotes.")
    if workspace.product_selection.template_code != PILOT_TEMPLATE_CODE:
        _raise_blocked(
            "TEMPLATE_NOT_SUPPORTED",
            f"Template {workspace.product_selection.template_code} is not supported for guarded quote creation.",
        )
    confirmed = workspace.confirmed_production_model
    if confirmed is None or confirmed.confirmation_status != "confirmed":
        _raise_blocked("WORKSPACE_INCOMPLETE", "Confirmed production model is required.")
    if workspace.finish_assignment is None:
        _raise_blocked("WORKSPACE_INCOMPLETE", "Finish assignment is required.")
    quote_readiness = preview.quote_readiness
    if quote_readiness is None:
        _raise_blocked("READINESS_CHAIN_INCOMPLETE", "Quote readiness gate is missing.")
    if quote_readiness.status == "blocked":
        blocker_codes = [item.code for item in quote_readiness.blockers]
        _raise_blocked(
            "WORKSPACE_INCOMPLETE",
            "Quote readiness gate is blocked.",
            blocker_codes or ["QUOTE_READINESS_BLOCKED"],
        )
    if preview.prequote_review is None:
        _raise_blocked("READINESS_CHAIN_INCOMPLETE", "Pre-quote review is missing.")


def validate_real_quote_creation_allowed(
    record: IntakeV3WorkspaceRecord,
    workspace: IntakeV3Workspace,
    request: IntakeV3CreateDraftQuoteRequest,
    current_user: UserResponse | None,
    chain: dict[str, Any],
) -> None:
    archived = record.archived_at is not None
    _validate_owner_decision(record.id, request, current_user)
    _validate_safety_confirmations(request)

    bridge = chain["bridge"]
    enablement = chain["enablement_policy"]
    if request.expected_bridge_status and bridge.bridge_status != request.expected_bridge_status:
        _raise_blocked(
            "BRIDGE_STATUS_MISMATCH",
            f"Expected bridge status {request.expected_bridge_status}, got {bridge.bridge_status}.",
        )
    if (
        request.expected_enablement_status
        and enablement.enablement_status != request.expected_enablement_status
    ):
        _raise_blocked(
            "ENABLEMENT_STATUS_MISMATCH",
            f"Expected enablement status {request.expected_enablement_status}, "
            f"got {enablement.enablement_status}.",
        )

    _validate_workspace_completeness(workspace, chain["preview"], archived=archived)

    for key in ("dry_run", "guard_policy", "bridge", "final_blocker_check", "enablement_policy", "snapshot_policy"):
        if chain.get(key) is None:
            _raise_blocked("READINESS_CHAIN_INCOMPLETE", f"Missing policy chain component: {key}")

    dry_run = chain["dry_run"]
    if dry_run.safety_flags.quote_creation_endpoint_called:
        _raise_blocked("SAFETY_VIOLATION", "Recursive quote creation endpoint call detected.")
    if dry_run.safety_flags.order_created or dry_run.safety_flags.execution_plan_created:
        _raise_blocked("SAFETY_VIOLATION", "Prior order or execution side effect detected in dry-run flags.")
    if dry_run.safety_flags.inventory_mutated:
        _raise_blocked("SAFETY_VIOLATION", "Inventory mutation flag detected.")

    try:
        build_quote_creation_snapshot_payload(
            workspace,
            chain["preview"],
            bridge,
            build_owner_decision_record_for_quote_creation(
            record.id,
            request,
            current_user,
            workspace=workspace,
            preview=chain["preview"],
        ),
            workspace_id=record.id,
            workspace_code=record.workspace_code,
            chain=chain,
        )
    except Exception as exc:
        _raise_blocked("SNAPSHOT_BUILD_FAILED", f"Snapshot payload could not be built: {exc}")


def build_quote_draft_payload(
    workspace: IntakeV3Workspace,
    record: IntakeV3WorkspaceRecord,
    snapshot_payload: IntakeV3QuoteCreationSnapshotPayload,
    owner_decision: dict[str, Any],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    valid_until = (now + timedelta(days=30)).strftime("%Y-%m-%d")
    quote_code = f"Q-IV3-{record.workspace_code}-{int(now.timestamp())}"
    confirmed_count = 0
    if workspace.confirmed_production_model:
        confirmed_count = workspace.confirmed_production_model.letter_count
    line_item = {
        "productCode": workspace.product_selection.template_code,
        "description": workspace.client_request.job_title or workspace.client_request.request_code,
        "quantity": confirmed_count or 1,
        "unit_price": 0,
        "total": 0,
    }
    linkage = {
        "source_module": INTAKE_V3_SOURCE_MODULE,
        "source_workspace_id": record.id,
        "source_workspace_code": record.workspace_code,
        "requires_pricing_review": True,
        "pricing_source": PRICING_SOURCE,
        "owner_decision": owner_decision,
        "snapshot": snapshot_payload.model_dump(mode="json"),
        "snapshot_policy_version": SNAPSHOT_POLICY_VERSION,
        "integrity_markers": {
            "raw_analysis_not_production_truth": snapshot_payload.raw_analysis_not_production_truth,
            "confirmed_model_production_truth": True,
            "holes_not_letters": snapshot_payload.holes_not_letters,
        },
    }
    notes_payload = {
        "human_summary": (
            f"Draft quote from Intake V3 workspace {record.workspace_code}. "
            "Requires pricing review — no final commercial price calculated."
        ),
        INTAKE_V3_LINKAGE_JSON_KEY: linkage,
    }
    return {
        "code": quote_code,
        "intake_id": None,
        "intake_code": intake_v3_linkage_code(record.id),
        "client_id": None,
        "client_name": workspace.client_request.client_name or "Unknown Client",
        "contact_person": None,
        "status": "draft",
        "version": 1,
        "valid_until": valid_until,
        "line_items": json.dumps([line_item]),
        "subtotal": 0.0,
        "discount": 0.0,
        "discount_pct": 0.0,
        "total_before_vat": 0.0,
        "vat": 0.0,
        "grand_total": 0.0,
        "margin_pct": 0.0,
        "notes": json.dumps(notes_payload, default=str),
        "assigned_to": owner_decision.get("owner_display_name"),
    }


async def create_guarded_draft_quote_from_intake_v3_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3CreateDraftQuoteRequest,
    current_user: UserResponse,
) -> IntakeV3CreateDraftQuoteResponse:
    record = await _get_record_or_404(db, workspace_id)
    workspace = _load_workspace_from_record(record)
    archived = record.archived_at is not None
    chain = _build_policy_chain(workspace, record, archived=archived)

    validate_real_quote_creation_allowed(record, workspace, request, current_user, chain)

    existing = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if existing is not None:
        _raise_blocked(
            "DUPLICATE_QUOTE_FOR_WORKSPACE",
            f"Quote already linked to Intake V3 workspace {workspace_id}.",
            ["DUPLICATE_QUOTE_FOR_WORKSPACE"],
        )

    owner_decision = build_owner_decision_record_for_quote_creation(
        workspace_id,
        request,
        current_user,
        workspace=workspace,
        preview=chain["preview"],
    )
    snapshot_payload = build_quote_creation_snapshot_payload(
        workspace,
        chain["preview"],
        chain["bridge"],
        owner_decision,
        workspace_id=record.id,
        workspace_code=record.workspace_code,
        chain=chain,
    )
    quote_data = build_quote_draft_payload(workspace, record, snapshot_payload, owner_decision)

    quotes_service = QuotesService(db)
    try:
        quote_obj = await quotes_service.create(quote_data)
    except Exception as exc:
        logger.error("Guarded Intake V3 quote persistence failed for %s: %s", workspace_id, exc, exc_info=True)
        _raise_blocked("QUOTE_PERSISTENCE_FAILED", f"Quote persistence failed: {exc}")

    if quote_obj is None:
        _raise_blocked("QUOTE_PERSISTENCE_FAILED", "Quote persistence returned no object.")

    logger.info(
        "Guarded draft quote created from Intake V3: quote_id=%s workspace_id=%s user=%s",
        quote_obj.id,
        workspace_id,
        current_user.id,
    )

    return IntakeV3CreateDraftQuoteResponse(
        quote_created=True,
        quote_id=quote_obj.id,
        quote_code=quote_obj.code,
        quote_status=quote_obj.status,
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_workspace_id=workspace_id,
        snapshot_attached=True,
        owner_decision_record_attached=True,
        order_created=False,
        execution_plan_created=False,
        inventory_mutated=False,
        requires_pricing_review=True,
        cost_engine_called=False,
    )


async def count_orders_and_execution_plans(db: AsyncSession) -> tuple[int, int]:
    order_count = await db.scalar(select(func.count()).select_from(Orders))
    plan_count = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    return int(order_count or 0), int(plan_count or 0)
