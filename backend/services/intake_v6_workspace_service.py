"""Intake V6 workspace persistence, with its own payload contract."""

from __future__ import annotations

import copy
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake_requests import Intake_requests
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.auth import UserResponse
from schemas.intake_v6 import (
    INTAKE_V6_SCHEMA_VERSION,
    IntakeV6AnalysisBundleRequest,
    IntakeV6ClientRequest,
    IntakeV6FinishSetup,
    IntakeV6LayerRoleSetup,
    IntakeV6LayerRoleUpdateRequest,
    IntakeV6ProductTruthWriterDryRunRequest,
    IntakeV6ProductTruthWriterPromoteRequest,
    IntakeV6ProductSystemBindingResponse,
    IntakeV6SvgUploadResponse,
    IntakeV6TaskPreviewResponse,
    IntakeV6WorkspaceCreateRequest,
    IntakeV6WorkspaceListResponse,
    IntakeV6WorkspacePayload,
    IntakeV6WorkspaceResponse,
)
from services.intake_v6_quote_geometry_service import (
    build_quote_geometry_from_analysis,
    merge_quote_geometry_into_path_summary,
)
from services.intake_v3_geometry_metrics_snapshot_service import build_path_geometry_summary_from_svg_text
from services.intake_v3_svg_analysis_service import analyze_svg_content, validate_svg_upload
from services.intake_v6_analysis_bundle_guard_service import assert_analysis_bundle_child_parts_or_raise
from services.intake_v6_layer_role_service import (
    apply_layer_role_updates,
    build_layer_role_setup_from_path_summary,
    merge_layer_roles_after_reupload,
    selected_layer_refs_runtime_state,
)
from services.intake_v4_layer_role_service import sync_selected_layer_refs_on_payload
from services.intake_v6_layer_binding_persistence_service import (
    persist_logo_layer_bindings_from_composition_confirmation,
)
from services.intake_v6_product_composition_recommendation_service import (
    apply_product_composition_recommendation,
)
from services.intake_v6_product_system_service import (
    build_binding_response,
    resolve_product_template_or_raise,
)
from services.product_template_availability_service import ProductTemplateAvailabilityService
from services.intake_v6_production_preview_service import build_v6_task_preview_response
from services.form_system_runtime_capture_read_model_service import (
    build_form_system_runtime_capture_read_model,
)
from services.product_truth_promotion_planner_service import (
    build_product_truth_promotion_plan,
)
from services.product_truth_writer_dry_run_service import (
    build_product_truth_writer_dry_run_response,
    compute_payload_hash,
    compute_planner_hash,
    downstream_write_intent_is_all_false,
)
from services.product_truth_writer_service import (
    promote_product_truth_snapshot,
    proposed_mutations_match_confirmed_snapshot,
)
from services.return_cant_product_truth_bridge import (
    apply_return_cant_runtime_product_truth_bridge,
    clear_return_cant_runtime_product_truth,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _workspace_code() -> str:
    return f"IV6-{uuid.uuid4().hex[:8].upper()}"


def _parse_payload(raw: dict[str, Any]) -> IntakeV6WorkspacePayload:
    return IntakeV6WorkspacePayload.model_validate(raw)


def _layer_setup_from_payload(raw: dict[str, Any]) -> IntakeV6LayerRoleSetup | None:
    setup = raw.get("layer_role_setup")
    if not isinstance(setup, dict):
        return None
    return IntakeV6LayerRoleSetup.model_validate(setup)


def _sync_selected_layer_refs(payload_raw: dict[str, Any]) -> None:
    sync_selected_layer_refs_on_payload(payload_raw, _layer_setup_from_payload(payload_raw))


def _offer_scope_ready(payload: IntakeV6WorkspacePayload) -> bool:
    """Legacy workspaces without offer_scope remain valid (full product)."""
    if payload.offer_scope is None:
        if payload.offer_scope_confirmed is None:
            return True
        return isinstance(payload.offer_scope_confirmed, dict) and payload.offer_scope_confirmed.get(
            "confirmed"
        ) is True

    confirmed = payload.offer_scope_confirmed
    if not (isinstance(confirmed, dict) and confirmed.get("confirmed") is True):
        return False

    from schemas.offer_scope import OfferScopeInput
    from services.offer_scope_resolver_service import resolve_offer_scope

    resolved = resolve_offer_scope(
        OfferScopeInput(
            contract_version=payload.offer_scope.contract_version,
            mode=payload.offer_scope.mode,
            sold_modules=list(payload.offer_scope.sold_modules),
        )
    )
    if resolved.validation_errors:
        return False

    from services.sold_scope_dependency_validator_service import validate_sold_graph_from_payload

    payload_raw = payload.model_dump(mode="json")
    dependency = validate_sold_graph_from_payload(payload_raw if isinstance(payload_raw, dict) else None)
    return dependency.valid_for_confirmation


def _derive_readiness_status(payload: IntakeV6WorkspacePayload) -> str:
    if payload.svg_source is None or payload.svg_source.upload_status != "analyzed":
        return "missing_svg"
    setup = payload.layer_role_setup
    if setup is None or setup.confirmation_status != "complete":
        return "layer_roles_incomplete"
    recommendation = payload.product_composition_recommendation
    if isinstance(recommendation, dict) and recommendation.get("status") == "blocked":
        blockers = recommendation.get("blockers")
        if isinstance(blockers, list) and blockers:
            return str(blockers[0].get("code") if isinstance(blockers[0], dict) else blockers[0]).lower()
        return "product_composition_blocked"
    if isinstance(recommendation, dict):
        confirmed = payload.product_composition_confirmed
        if not (isinstance(confirmed, dict) and confirmed.get("confirmed") is True):
            return "product_composition_not_confirmed"
    if not _offer_scope_ready(payload):
        return "offer_scope_not_confirmed"
    if payload.finish_setup is None or not payload.finish_setup.confirmed:
        return "finish_setup_incomplete"
    if _is_logo_only_candidate_not_offerable(payload):
        return "logo_only_candidate_not_offerable"

    from services.intake_v6_canonical_readiness_service import (
        list_runtime_capture_fatal_blocker_codes,
        resolve_workspace_readiness_with_capture_blockers,
    )

    template_code = (
        payload.product_binding.template_code
        if payload.product_binding and payload.product_binding.template_code
        else None
    )
    capture_blockers = list_runtime_capture_fatal_blocker_codes(
        payload.model_dump(mode="json"),
        template_code=template_code,
    )
    return resolve_workspace_readiness_with_capture_blockers(
        "ready_for_quote_preview",
        capture_blockers=capture_blockers,
    )


def _is_logo_only_candidate_not_offerable(payload: IntakeV6WorkspacePayload) -> bool:
    """Logo remains candidate-only / non-offerable until a separate owner GO.

    Confirmed artwork may make a Logo candidate technically complete, but must not
    surface ready_for_quote_preview on a Logo-only or Logo-root workspace.
    """
    from services.template_usage_mode_policy import (
        TPL_VOLUMETRIC_LOGO_V1,
        normalize_template_code,
    )

    recommendation = payload.product_composition_recommendation
    if isinstance(recommendation, dict) and recommendation.get("composition_type") == "logo_only":
        return True

    template_code = (
        payload.product_binding.template_code
        if payload.product_binding and payload.product_binding.template_code
        else None
    )
    if normalize_template_code(template_code) == normalize_template_code(TPL_VOLUMETRIC_LOGO_V1):
        return True

    setup = payload.layer_role_setup
    finish = payload.finish_setup
    if setup is None or finish is None:
        return False

    has_letter_role = any(
        (layer.confirmed_role or layer.auto_role) == "face"
        for layer in setup.layers
        if layer.confirmation_state != "ignored"
    )
    if has_letter_role:
        return False

    has_logo_artwork_role = any(
        (layer.confirmed_role or layer.auto_role) in {"printed_artwork", "logo"}
        for layer in setup.layers
        if layer.confirmation_state != "ignored"
    )
    if not has_logo_artwork_role:
        return False

    letter_rows = finish.letter_group_finishes or []
    artwork_rows = finish.artwork_finishes or []
    # Constructive-model confirmation does not clear the candidate/non-offerable boundary.
    return len(letter_rows) == 0 and len(artwork_rows) > 0


def _derive_workspace_status(readiness_status: str) -> str:
    if readiness_status == "ready_for_quote_preview":
        return "ready_for_quote_preview"
    if readiness_status in {
        "missing_svg",
        "layer_roles_incomplete",
        "product_composition_not_confirmed",
        "logo_only_candidate_not_offerable",
    }:
        return "collecting_data"
    if readiness_status == "finish_setup_incomplete":
        return "collecting_data"
    return "draft"


async def _resolve_offerable_template_code_or_raise(
    db: AsyncSession,
    selected_template_code: str | None,
    *,
    require_selected: bool,
) -> str:
    candidate = (selected_template_code or "").strip()
    if not candidate:
        if require_selected:
            raise HTTPException(status_code=422, detail={"error": "selected_template_code_required"})
        return "TPL-VOLUMETRIC-LETTERS_v2"

    availability = await ProductTemplateAvailabilityService(db).list_availability()
    by_code = {item.template_code.upper(): item for item in availability.items}
    item = by_code.get(candidate.upper())
    if item is None:
        raise HTTPException(
            status_code=422,
            detail={"error": "selected_template_not_found", "selected_template_code": candidate},
        )
    if not item.quote_offerable:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "selected_template_not_quote_offerable",
                "selected_template_code": item.template_code,
                "status": item.status,
                "status_reason": item.status_reason,
            },
        )
    return item.template_code


def _reset_internal_draft_quote_confirmation(payload_raw: dict[str, Any]) -> None:
    finish = payload_raw.get("finish_setup")
    if isinstance(finish, dict) and finish.get("internal_draft_quote_confirmed"):
        finish["internal_draft_quote_confirmed"] = False
        payload_raw["finish_setup"] = finish


def _read_scope_sold_modules(payload_raw: dict[str, Any]) -> set[str]:
    scope = payload_raw.get("offer_scope")
    if not isinstance(scope, dict):
        return set()
    if scope.get("mode") == "full_product":
        return set()
    sold = scope.get("sold_modules")
    if not isinstance(sold, list):
        return set()
    return {str(code).strip() for code in sold if str(code).strip()}


def _invalidate_finish_confirmations_for_deselected_scope(
    payload_raw: dict[str, Any],
    *,
    previous_modules: set[str],
    next_modules: set[str],
) -> None:
    deselected = previous_modules - next_modules
    if not deselected:
        return

    finish = payload_raw.get("finish_setup")
    if not isinstance(finish, dict):
        return

    if deselected.intersection({"FACE", "RETURN-CANT"}):
        groups = finish.get("letter_group_finishes")
        if isinstance(groups, list):
            for group in groups:
                if isinstance(group, dict) and group.get("confirmed") is True:
                    group["confirmed"] = False

    if "RETURN-CANT" in deselected:
        artwork = finish.get("artwork_finishes")
        if isinstance(artwork, list):
            for row in artwork:
                if isinstance(row, dict) and row.get("confirmed") is True:
                    row["confirmed"] = False

    if deselected.intersection({"FACE", "RETURN-CANT", "BACK"}):
        finish["confirmed"] = False

    payload_raw["finish_setup"] = finish


def _record_to_response(record: IntakeV6WorkspaceRecord) -> IntakeV6WorkspaceResponse:
    return IntakeV6WorkspaceResponse(
        id=record.id,
        workspace_code=record.workspace_code,
        title=record.title,
        template_code=record.template_code,
        status=record.status,  # type: ignore[arg-type]
        payload=_json_loads(record.payload_json, {}),
        readiness_status=record.readiness_status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


async def _find_workspace_by_intake_request_code(
    db: AsyncSession,
    intake_request_code: str,
) -> IntakeV6WorkspaceRecord | None:
    code = intake_request_code.strip()
    if not code:
        return None
    result = await db.execute(
        select(IntakeV6WorkspaceRecord)
        .where(IntakeV6WorkspaceRecord.archived_at.is_(None))
        .order_by(IntakeV6WorkspaceRecord.updated_at.desc())
    )
    for record in result.scalars().all():
        payload = _json_loads(record.payload_json, {})
        if isinstance(payload, dict) and payload.get("intake_request_code") == code:
            return record
    return None


async def _get_record_or_404(db: AsyncSession, workspace_id: str) -> IntakeV6WorkspaceRecord:
    key = workspace_id.strip()
    result = await db.execute(
        select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == key)
    )
    record = result.scalar_one_or_none()
    if record is None:
        result = await db.execute(
            select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == key)
        )
        record = result.scalar_one_or_none()
    if record is None:
        record = await _find_workspace_by_intake_request_code(db, key)
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "workspace_not_found", "workspace_id": workspace_id})
    return record


async def _persist_payload(
    db: AsyncSession,
    record: IntakeV6WorkspaceRecord,
    payload: IntakeV6WorkspacePayload,
    *,
    current_user: UserResponse,
) -> IntakeV6WorkspaceResponse:
    record.payload_json = _json_dumps(payload.model_dump(mode="json"))
    record.readiness_status = _derive_readiness_status(payload)
    record.status = _derive_workspace_status(record.readiness_status)
    record.updated_by_user_id = current_user.id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)
    return _record_to_response(record)


async def _persist_payload_json_raw_for_product_truth_writer(
    db: AsyncSession,
    record: IntakeV6WorkspaceRecord,
    payload_raw: dict[str, Any],
    *,
    current_user: UserResponse,
) -> IntakeV6WorkspaceResponse:
    payload = _parse_payload(payload_raw)
    record.payload_json = _json_dumps(payload_raw)
    record.readiness_status = _derive_readiness_status(payload)
    record.status = _derive_workspace_status(record.readiness_status)
    record.updated_by_user_id = current_user.id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)
    return _record_to_response(record)


async def create_intake_v6_workspace(
    db: AsyncSession,
    request: IntakeV6WorkspaceCreateRequest,
    current_user: UserResponse,
) -> IntakeV6WorkspaceResponse:
    intake_request_code = (request.intake_request_code or "").strip() or None
    if intake_request_code:
        existing = await _find_workspace_by_intake_request_code(db, intake_request_code)
        if existing is not None:
            return _record_to_response(existing)

    template = await resolve_product_template_or_raise(db, request.template_code)
    now = _utcnow()
    payload = IntakeV6WorkspacePayload(
        schema_version=INTAKE_V6_SCHEMA_VERSION,
        client=IntakeV6ClientRequest(
            client_name=request.client_name,
            job_title=request.job_title,
        ),
        product_binding={
            "template_code": template.template_code,
            "template_id": template.template_id,
            "template_label": template.template_label,
            "product_family": template.product_family,
            "product_family_name": template.product_family_name,
            "bound_at": now,
        },
        intake_request_code=intake_request_code,
        offer_method=(request.offer_method or None),
        analyzer_mode=(request.analyzer_mode or None),
        template_hint_code=(request.template_hint_code or None),
        selected_template_code=(request.selected_template_code or request.template_code),
        source=(request.source or None),
        work_intake_context={
            "offer_method": request.offer_method,
            "analyzer_mode": request.analyzer_mode,
            "template_hint_code": request.template_hint_code,
            "selected_template_code": request.selected_template_code or request.template_code,
            "source": request.source,
            "selected_template_is_initial": True,
            "product_truth_final_decided_later": True,
        },
    )
    record = IntakeV6WorkspaceRecord(
        id=str(uuid.uuid4()),
        workspace_code=_workspace_code(),
        title=request.title.strip(),
        template_code=template.template_code,
        status="draft",
        payload_json=_json_dumps(payload.model_dump(mode="json")),
        readiness_status=_derive_readiness_status(payload),
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
        created_at=now,
        updated_at=now,
    )
    record.status = _derive_workspace_status(record.readiness_status)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _record_to_response(record)


async def get_intake_v6_workspace(db: AsyncSession, workspace_id: str) -> IntakeV6WorkspaceResponse:
    record = await _get_record_or_404(db, workspace_id)
    return _record_to_response(record)


async def get_form_system_runtime_capture_read_model_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> dict[str, Any]:
    workspace = await get_intake_v6_workspace(db, workspace_id)
    payload = workspace.payload if isinstance(workspace.payload, dict) else {}
    product_binding = payload.get("product_binding") if isinstance(payload.get("product_binding"), dict) else {}
    read_model = build_form_system_runtime_capture_read_model(
        payload,
        template_code=workspace.template_code,
    )
    return {
        "read_only": True,
        "workspace_id": workspace_id,
        "workspace_record_id": workspace.id,
        "workspace_code": workspace.workspace_code,
        "root_template_code": workspace.template_code,
        "product_binding_template_code": product_binding.get("template_code"),
        "read_model_version": "v1",
        "fields": read_model.get("fields") or [],
        "blockers": read_model.get("blockers") or [],
        "downstream_write_intent": read_model.get("downstream_write_intent") or {},
        "notes": read_model.get("notes") or [],
    }


async def get_product_truth_promotion_planner_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> dict[str, Any]:
    workspace = await get_intake_v6_workspace(db, workspace_id)
    payload = workspace.payload if isinstance(workspace.payload, dict) else {}
    product_binding = payload.get("product_binding") if isinstance(payload.get("product_binding"), dict) else {}
    planner = build_product_truth_promotion_plan(
        payload,
        template_code=workspace.template_code,
    )
    downstream_write_intent = dict(planner.get("downstream_write_intent") or {})
    downstream_write_intent.setdefault("product_truth_write", False)
    return {
        "read_only": True,
        "workspace_id": workspace_id,
        "workspace_record_id": workspace.id,
        "workspace_code": workspace.workspace_code,
        "root_template_code": workspace.template_code,
        "product_binding_template_code": product_binding.get("template_code"),
        "planner_version": planner.get("planner_version") or "v1",
        "eligible_entries": planner.get("eligible_entries") or [],
        "blocked_entries": planner.get("blocked_entries") or [],
        "blockers": planner.get("blockers") or [],
        "downstream_write_intent": downstream_write_intent,
        "notes": planner.get("notes") or [],
    }


async def get_product_truth_writer_dry_run_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV6ProductTruthWriterDryRunRequest,
) -> dict[str, Any]:
    if request.dry_run_only is not True:
        raise HTTPException(status_code=422, detail={"error": "dry_run_only_required"})

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    product_binding = payload_raw.get("product_binding") if isinstance(payload_raw.get("product_binding"), dict) else {}
    planner = build_product_truth_promotion_plan(
        payload_raw,
        template_code=record.template_code,
    )
    planner_response = {
        "read_only": True,
        "workspace_id": workspace_id,
        "workspace_record_id": record.id,
        "workspace_code": record.workspace_code,
        "root_template_code": record.template_code,
        "product_binding_template_code": product_binding.get("template_code"),
        "planner_version": planner.get("planner_version") or "v1",
        "eligible_entries": planner.get("eligible_entries") or [],
        "blocked_entries": planner.get("blocked_entries") or [],
        "blockers": planner.get("blockers") or [],
        "downstream_write_intent": dict(planner.get("downstream_write_intent") or {}),
        "notes": planner.get("notes") or [],
    }
    planner_response["downstream_write_intent"].setdefault("product_truth_write", False)

    if planner_response.get("read_only") is not True:
        raise HTTPException(status_code=422, detail={"error": "planner_not_read_only"})
    if not downstream_write_intent_is_all_false(planner_response.get("downstream_write_intent") or {}):
        raise HTTPException(status_code=422, detail={"error": "downstream_write_intent_not_false"})
    if request.expected_workspace_code and request.expected_workspace_code != record.workspace_code:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "workspace_code_mismatch",
                "expected_workspace_code": request.expected_workspace_code,
                "workspace_code": record.workspace_code,
            },
        )
    if request.expected_root_template_code != record.template_code:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "root_template_code_mismatch",
                "expected_root_template_code": request.expected_root_template_code,
                "root_template_code": record.template_code,
            },
        )
    if request.expected_product_binding_template_code != product_binding.get("template_code"):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "product_binding_template_code_mismatch",
                "expected_product_binding_template_code": request.expected_product_binding_template_code,
                "product_binding_template_code": product_binding.get("template_code"),
            },
        )
    if request.planner_version != planner_response.get("planner_version"):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "planner_version_mismatch",
                "expected_planner_version": request.planner_version,
                "planner_version": planner_response.get("planner_version"),
            },
        )

    payload_hash_basis = compute_payload_hash(payload_raw)
    planner_hash = compute_planner_hash(planner_response)
    if request.payload_hash_basis and request.payload_hash_basis != payload_hash_basis:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "payload_hash_basis_mismatch",
                "expected_payload_hash_basis": request.payload_hash_basis,
                "payload_hash_basis": payload_hash_basis,
            },
        )
    if request.planner_hash and request.planner_hash != planner_hash:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "planner_hash_mismatch",
                "expected_planner_hash": request.planner_hash,
                "planner_hash": planner_hash,
            },
        )

    return build_product_truth_writer_dry_run_response(
        workspace_id=workspace_id,
        workspace_record_id=record.id,
        workspace_code=record.workspace_code,
        root_template_code=record.template_code,
        product_binding_template_code=product_binding.get("template_code"),
        payload_raw=copy.deepcopy(payload_raw),
        planner_response=copy.deepcopy(planner_response),
        actor=request.actor,
        requested_entry_keys=request.requested_entry_keys,
    )


def _payload_without_product_truth_confirmed_snapshot(payload_raw: dict[str, Any]) -> dict[str, Any]:
    payload_copy = copy.deepcopy(payload_raw)
    product_truth = payload_copy.get("product_truth")
    if not isinstance(product_truth, dict):
        return payload_copy
    product_truth.pop("confirmed_snapshot_v1", None)
    if not product_truth:
        payload_copy.pop("product_truth", None)
    return payload_copy


async def promote_product_truth_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV6ProductTruthWriterPromoteRequest,
    current_user: UserResponse,
) -> dict[str, Any]:
    if request.promotion_confirmed is not True:
        raise HTTPException(status_code=422, detail={"error": "promotion_confirmed_required"})

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    current_payload_hash = compute_payload_hash(payload_raw)
    payload_hash_without_snapshot = compute_payload_hash(
        _payload_without_product_truth_confirmed_snapshot(payload_raw)
    )
    existing_snapshot = (
        payload_raw.get("product_truth") if isinstance(payload_raw.get("product_truth"), dict) else {}
    )
    existing_snapshot = (
        existing_snapshot.get("confirmed_snapshot_v1") if isinstance(existing_snapshot, dict) else {}
    )
    existing_planner_basis = (
        existing_snapshot.get("planner_basis") if isinstance(existing_snapshot, dict) else {}
    )
    replay_basis_hash = (
        existing_planner_basis.get("payload_hash_basis") if isinstance(existing_planner_basis, dict) else None
    )
    payload_hash_matches_current_basis = request.payload_hash_basis in {
        current_payload_hash,
        payload_hash_without_snapshot,
    }
    payload_hash_matches_replay_basis = bool(
        request.payload_hash_basis and request.payload_hash_basis == replay_basis_hash
    )
    if request.payload_hash_basis and not payload_hash_matches_current_basis and not payload_hash_matches_replay_basis:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "payload_hash_basis_mismatch",
                "expected_payload_hash_basis": request.payload_hash_basis,
                "payload_hash_basis": current_payload_hash,
                "payload_hash_basis_without_confirmed_snapshot": payload_hash_without_snapshot,
            },
        )

    dry_run_request = IntakeV6ProductTruthWriterDryRunRequest.model_validate(
        {
            "dry_run_only": True,
            "expected_workspace_code": request.expected_workspace_code,
            "expected_root_template_code": request.expected_root_template_code,
            "expected_product_binding_template_code": request.expected_product_binding_template_code,
            "planner_version": request.planner_version,
            "planner_hash": request.planner_hash,
            "payload_hash_basis": current_payload_hash,
            "actor": request.actor,
            "requested_entry_keys": request.requested_entry_keys,
        }
    )
    dry_run_response = await get_product_truth_writer_dry_run_for_workspace(db, workspace_id, dry_run_request)
    downstream_write_intent = dry_run_response.get("downstream_write_intent") or {}
    if not downstream_write_intent_is_all_false(downstream_write_intent):
        raise HTTPException(status_code=422, detail={"error": "downstream_write_intent_not_false"})
    if payload_hash_matches_replay_basis and not payload_hash_matches_current_basis:
        if not proposed_mutations_match_confirmed_snapshot(
            payload_raw,
            dry_run_response.get("proposed_mutations") or [],
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "payload_hash_basis_mismatch",
                    "expected_payload_hash_basis": request.payload_hash_basis,
                    "payload_hash_basis": current_payload_hash,
                    "payload_hash_basis_without_confirmed_snapshot": payload_hash_without_snapshot,
                },
            )

    actor_payload = copy.deepcopy(request.actor) if isinstance(request.actor, dict) else {}
    actor_payload.setdefault("actor_id", current_user.id)
    actor_payload.setdefault("actor_email", current_user.email)
    actor_payload.setdefault("actor_role", current_user.role)
    actor_payload.setdefault("actor_label", current_user.name or current_user.email or str(current_user.id))

    payload_before, response = promote_product_truth_snapshot(
        workspace_id=workspace_id,
        workspace_code=record.workspace_code,
        payload_raw=payload_raw,
        dry_run_response=dry_run_response,
        actor=actor_payload,
    )
    if response.get("write_performed") is not True:
        return response

    await _persist_payload_json_raw_for_product_truth_writer(
        db,
        record,
        payload_raw,
        current_user=current_user,
    )
    persisted_payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(persisted_payload_raw, dict):
        persisted_payload_raw = {}
    response["payload_hash_before"] = compute_payload_hash(payload_before)
    response["payload_hash_after"] = compute_payload_hash(persisted_payload_raw)
    return response


async def ensure_intake_v6_workspace_for_intake_request(
    db: AsyncSession,
    intake_request_code: str,
    current_user: UserResponse,
    *,
    offer_method: str | None = None,
    analyzer_mode: str | None = None,
    template_hint_code: str | None = None,
    selected_template_code: str | None = None,
    source: str | None = None,
) -> IntakeV6WorkspaceResponse:
    code = intake_request_code.strip()
    if not code:
        raise HTTPException(status_code=422, detail={"error": "intake_request_code_required"})

    existing = await _find_workspace_by_intake_request_code(db, code)
    if existing is not None:
        return _record_to_response(existing)

    result = await db.execute(select(Intake_requests).where(Intake_requests.code == code).limit(1))
    intake = result.scalar_one_or_none()
    if intake is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "intake_request_not_found", "intake_request_code": code},
        )

    description = (intake.description or "").strip()
    title_source = description or code
    title = f"{intake.client_name} — {title_source}"[:200]
    resolved_template_code = await _resolve_offerable_template_code_or_raise(
        db,
        selected_template_code or template_hint_code,
        require_selected=(source == "work_intake_new_request" and analyzer_mode != "analyzer_first"),
    )
    create_request = IntakeV6WorkspaceCreateRequest(
        title=title,
        template_code=resolved_template_code,
        client_name=intake.client_name,
        job_title=description or None,
        intake_request_code=code,
        offer_method=offer_method,
        analyzer_mode=analyzer_mode,
        template_hint_code=template_hint_code,
        selected_template_code=selected_template_code,
        source=source,
    )
    return await create_intake_v6_workspace(db, create_request, current_user)


async def list_intake_v6_workspaces(
    db: AsyncSession,
    *,
    include_archived: bool = False,
) -> IntakeV6WorkspaceListResponse:
    query = select(IntakeV6WorkspaceRecord).order_by(IntakeV6WorkspaceRecord.updated_at.desc())
    if not include_archived:
        query = query.where(IntakeV6WorkspaceRecord.archived_at.is_(None))
    result = await db.execute(query)
    records = list(result.scalars().all())
    items = [_record_to_response(record) for record in records]
    return IntakeV6WorkspaceListResponse(items=items, total=len(items))


async def upload_svg_to_intake_v6_workspace(
    db: AsyncSession,
    workspace_id: str,
    *,
    file_name: str,
    content_type: str | None,
    raw_bytes: bytes,
    current_user: UserResponse,
) -> IntakeV6SvgUploadResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived", "workspace_id": workspace_id})

    validation = validate_svg_upload(
        raw_name=file_name,
        content_type=content_type,
        raw_bytes=raw_bytes,
    )
    analysis, _vector_asset = analyze_svg_content(
        file_name=validation.file_name,
        file_size_bytes=validation.file_size_bytes,
        svg_text=validation.svg_text,
    )
    path_summary = build_path_geometry_summary_from_svg_text(
        validation.svg_text,
        source_file_name=validation.file_name,
    )
    if path_summary is None:
        raise HTTPException(status_code=422, detail={"error": "path_geometry_summary_failed"})

    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    previous_payload = copy.deepcopy(payload_raw)
    previous_setup = _layer_setup_from_payload(previous_payload)

    file_hash = hashlib.sha256(raw_bytes).hexdigest()
    previous_hash = None
    previous_svg = previous_payload.get("svg_source")
    if isinstance(previous_svg, dict):
        previous_hash = previous_svg.get("file_hash")
    svg_source_replaced = previous_hash is not None and previous_hash != file_hash

    draft_setup = build_layer_role_setup_from_path_summary(path_summary)
    if svg_source_replaced:
        layer_setup = draft_setup
    else:
        layer_setup = merge_layer_roles_after_reupload(draft_setup, previous_setup)

    payload_raw["path_geometry_summary"] = path_summary
    payload_raw["svg_source"] = {
        "file_name": validation.file_name,
        "file_size_bytes": validation.file_size_bytes,
        "file_hash": file_hash,
        "upload_status": "analyzed",
    }
    # Persist source text so Page 1 can hydrate via the canonical client analyzer
    # (server path_geometry_summary alone does not populate nest2 svg_analysis_json).
    payload_raw["svg_source_text"] = validation.svg_text
    payload_raw["layer_role_setup"] = layer_setup.model_dump(mode="json")
    _sync_selected_layer_refs(payload_raw)
    apply_product_composition_recommendation(payload_raw)
    if svg_source_replaced:
        payload_raw.pop("finish_setup", None)
        # Clear stale client analysis when a different SVG replaces the source.
        payload_raw.pop("svg_analysis_json", None)
        clear_return_cant_runtime_product_truth(payload_raw)
    else:
        _reset_internal_draft_quote_confirmation(payload_raw)
        if payload_raw.get("finish_setup"):
            apply_return_cant_runtime_product_truth_bridge(payload_raw)

    payload = _parse_payload(payload_raw)
    response = await _persist_payload(db, record, payload, current_user=current_user)

    warnings = list(analysis.warnings)
    warnings.extend(layer_setup.warnings)
    return IntakeV6SvgUploadResponse(
        workspace=response,
        layer_role_setup=layer_setup,
        warnings=warnings,
    )


async def save_analysis_bundle_for_intake_v6_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV6AnalysisBundleRequest,
    current_user: UserResponse,
) -> IntakeV6WorkspaceResponse:
    """Persist nest2 svg_analysis_json + operator layer roles + SVG source (Step 1 handoff)."""
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived", "workspace_id": workspace_id})

    assert_analysis_bundle_child_parts_or_raise(request.svg_analysis_json)

    raw_bytes = request.svg_text.encode("utf-8")
    validation = validate_svg_upload(
        raw_name=request.file_name,
        content_type="image/svg+xml",
        raw_bytes=raw_bytes,
    )
    path_summary = build_path_geometry_summary_from_svg_text(
        validation.svg_text,
        source_file_name=validation.file_name,
    )
    if path_summary is None:
        raise HTTPException(status_code=422, detail={"error": "path_geometry_summary_failed"})

    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    file_hash = hashlib.sha256(raw_bytes).hexdigest()
    previous_hash = None
    previous_svg = payload_raw.get("svg_source")
    if isinstance(previous_svg, dict):
        previous_hash = previous_svg.get("file_hash")
    svg_source_replaced = previous_hash is not None and previous_hash != file_hash

    layer_setup_dict = request.layer_role_setup.model_dump(mode="json")
    quote_geometry = build_quote_geometry_from_analysis(request.svg_analysis_json, layer_setup_dict)
    path_summary = merge_quote_geometry_into_path_summary(path_summary, quote_geometry)

    payload_raw["path_geometry_summary"] = path_summary
    payload_raw["quote_geometry"] = quote_geometry
    payload_raw["svg_source"] = {
        "file_name": validation.file_name,
        "file_size_bytes": validation.file_size_bytes,
        "file_hash": file_hash,
        "upload_status": "analyzed",
    }
    payload_raw["svg_analysis_json"] = request.svg_analysis_json
    payload_raw["layer_role_setup"] = layer_setup_dict
    payload_raw["svg_source_text"] = validation.svg_text
    _sync_selected_layer_refs(payload_raw)
    apply_product_composition_recommendation(payload_raw)
    if svg_source_replaced:
        payload_raw.pop("finish_setup", None)
        clear_return_cant_runtime_product_truth(payload_raw)
    else:
        from services.intake_v6_pricing_preview_sync_service import apply_v6_pricing_preview_derived_state

        apply_v6_pricing_preview_derived_state(payload_raw)
        _reset_internal_draft_quote_confirmation(payload_raw)
        if payload_raw.get("finish_setup"):
            apply_return_cant_runtime_product_truth_bridge(payload_raw)

    payload = _parse_payload(payload_raw)
    return await _persist_payload(db, record, payload, current_user=current_user)


async def save_layer_roles_for_intake_v6_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV6LayerRoleUpdateRequest,
    current_user: UserResponse,
) -> IntakeV6WorkspaceResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived", "workspace_id": workspace_id})

    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    setup = _layer_setup_from_payload(payload_raw)
    if setup is None:
        raise HTTPException(status_code=422, detail={"error": "layer_role_setup_missing"})

    updates = [item.model_dump(mode="json") for item in request.layers]
    updated_setup = apply_layer_role_updates(setup, updates)
    payload_raw["layer_role_setup"] = updated_setup.model_dump(mode="json")
    _sync_selected_layer_refs(payload_raw)
    apply_product_composition_recommendation(payload_raw)
    _reset_internal_draft_quote_confirmation(payload_raw)
    if payload_raw.get("finish_setup"):
        from services.intake_v6_pricing_preview_sync_service import apply_v6_pricing_preview_derived_state

        apply_v6_pricing_preview_derived_state(payload_raw)
        apply_return_cant_runtime_product_truth_bridge(payload_raw)
    payload = _parse_payload(payload_raw)
    return await _persist_payload(db, record, payload, current_user=current_user)


async def save_product_composition_confirmation_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    *,
    confirmed: bool,
    items: list[dict[str, Any]] | None = None,
    operator_note: str | None = None,
    current_user: UserResponse,
) -> IntakeV6WorkspaceResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived", "workspace_id": workspace_id})

    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    if not isinstance(payload_raw.get("product_composition_recommendation"), dict):
        if payload_raw.get("layer_role_setup"):
            apply_product_composition_recommendation(payload_raw)
        else:
            raise HTTPException(status_code=422, detail={"error": "product_composition_recommendation_missing"})

    recommendation = payload_raw.get("product_composition_recommendation")
    if isinstance(recommendation, dict) and recommendation.get("status") == "blocked" and confirmed:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "product_composition_blocked",
                "blockers": recommendation.get("blockers") or [],
            },
        )

    confirmed_items = items if items is not None else (
        recommendation.get("composition_items") if isinstance(recommendation, dict) else []
    )
    payload_raw["product_composition_confirmed"] = {
        "confirmed": bool(confirmed),
        "confirmed_at": _utcnow().isoformat() if confirmed else None,
        "confirmed_by": current_user.email or current_user.name or str(current_user.id),
        "items": confirmed_items,
        "operator_note": operator_note,
        "source": "operator_confirmation_v1",
    }
    # Sync ACM panel instance composition_status (does not auto-confirm association/technical).
    finish = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else None
    if isinstance(finish, dict):
        acm_codes = {"TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"}
        items_list = confirmed_items if isinstance(confirmed_items, list) else []
        has_acm = any(
            isinstance(it, dict) and str(it.get("template_code") or "") in acm_codes for it in items_list
        )
        next_comp_status = "confirmed" if (confirmed and has_acm) else "unconfirmed"
        inst = finish.get("acm_panel_instance")
        if isinstance(inst, dict) and inst.get("schema") == "acm_panel_component_instance_v1":
            finish["acm_panel_instance"] = {**inst, "composition_status": next_comp_status}
        sel = finish.get("svg_support_selection")
        if isinstance(sel, dict) and isinstance(sel.get("acm_panel_instance"), dict):
            nested = dict(sel["acm_panel_instance"])
            nested["composition_status"] = next_comp_status
            finish["svg_support_selection"] = {**sel, "acm_panel_instance": nested}
        payload_raw["finish_setup"] = finish
    persist_logo_layer_bindings_from_composition_confirmation(
        payload_raw,
        confirmed=bool(confirmed),
        confirmed_items=confirmed_items if isinstance(confirmed_items, list) else [],
    )
    _reset_internal_draft_quote_confirmation(payload_raw)
    payload = _parse_payload(payload_raw)
    return await _persist_payload(db, record, payload, current_user=current_user)


async def save_offer_scope_for_intake_v6_workspace(
    db: AsyncSession,
    workspace_id: str,
    *,
    mode: str,
    sold_modules: list[str],
    confirmed: bool,
    operator_note: str | None = None,
    dependency_confirmation_codes: list[str] | None = None,
    current_user: UserResponse,
) -> IntakeV6WorkspaceResponse:
    from schemas.offer_scope import OfferScope, OfferScopeInput
    from services.offer_scope_resolver_service import resolve_offer_scope
    from services.sold_scope_dependency_validator_service import (
        merge_dependency_confirmations,
        sync_offer_scope_dependency_validation,
        validate_sold_graph,
    )

    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived", "workspace_id": workspace_id})

    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    normalized_mode = str(mode or "full_product").strip()
    normalized_modules = [str(code).strip() for code in (sold_modules or []) if str(code).strip()]
    previous_modules = _read_scope_sold_modules(payload_raw)
    previous_scope = payload_raw.get("offer_scope")
    previous_mode = previous_scope.get("mode") if isinstance(previous_scope, dict) else None
    sold_modules_changed = set(previous_modules) != set(normalized_modules) or (
        previous_mode != normalized_mode
    )
    if normalized_mode == "full_product":
        scope = OfferScope(mode="full_product", sold_modules=[])
        next_modules: set[str] = set()
    else:
        scope = OfferScope(mode="component_subset", sold_modules=normalized_modules)  # type: ignore[arg-type]
        next_modules = set(normalized_modules)

    resolved = resolve_offer_scope(
        OfferScopeInput(
            contract_version=scope.contract_version,
            mode=scope.mode,
            sold_modules=list(scope.sold_modules),
        )
    )
    if confirmed and resolved.validation_errors:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "offer_scope_invalid",
                "blockers": resolved.validation_errors,
            },
        )

    merge_dependency_confirmations(
        payload_raw,
        new_codes=dependency_confirmation_codes,
        sold_modules_changed=sold_modules_changed,
    )

    template_code = None
    product_binding = payload_raw.get("product_binding")
    if isinstance(product_binding, dict):
        template_code = product_binding.get("template_code")

    from services.sold_scope_dependency_validator_service import _read_dependency_confirmations

    dependency = validate_sold_graph(
        mode=scope.mode,
        sold_modules=list(scope.sold_modules),
        template_code=str(template_code) if template_code else None,
        dependency_confirmations=_read_dependency_confirmations(payload_raw),
    )

    if confirmed and not dependency.valid_for_save:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "offer_scope_dependency_invalid",
                "dependency_validation": dependency.model_dump(mode="json"),
            },
        )

    payload_raw["offer_scope"] = scope.model_dump(mode="json")
    payload_raw["offer_scope_confirmed"] = {
        "confirmed": bool(confirmed),
        "confirmed_at": _utcnow().isoformat() if confirmed else None,
        "confirmed_by": current_user.email or current_user.name or str(current_user.id),
        "operator_note": operator_note,
        "source": "operator_offer_scope_v1",
        "dependency_confirmations": (
            payload_raw.get("offer_scope_confirmed", {}).get("dependency_confirmations", [])
            if isinstance(payload_raw.get("offer_scope_confirmed"), dict)
            else []
        ),
    }
    sync_offer_scope_dependency_validation(payload_raw)
    if normalized_mode == "component_subset":
        _invalidate_finish_confirmations_for_deselected_scope(
            payload_raw,
            previous_modules=previous_modules,
            next_modules=next_modules,
        )
    _reset_internal_draft_quote_confirmation(payload_raw)
    if payload_raw.get("finish_setup"):
        from services.intake_v6_pricing_preview_sync_service import apply_v6_pricing_preview_derived_state

        apply_v6_pricing_preview_derived_state(payload_raw)
        apply_return_cant_runtime_product_truth_bridge(payload_raw)

    payload = _parse_payload(payload_raw)
    return await _persist_payload(db, record, payload, current_user=current_user)


async def get_product_system_binding_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV6ProductSystemBindingResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload = _parse_payload(_json_loads(record.payload_json, {}))
    template = await resolve_product_template_or_raise(db, payload.product_binding.template_code)
    return await build_binding_response(db, workspace_id, template)


async def get_task_preview_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    finish_override: dict[str, Any] | None = None,
) -> IntakeV6TaskPreviewResponse:
    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    payload = _parse_payload(payload_raw if isinstance(payload_raw, dict) else {})
    template = await resolve_product_template_or_raise(db, payload.product_binding.template_code)
    return build_v6_task_preview_response(
        workspace_id=workspace_id,
        template_code=template.template_code,
        payload=payload,
        finish_override=finish_override,
    )


def _binding_geometry_role(raw: Any) -> str:
    if isinstance(raw, dict):
        return str(raw.get("geometry_role") or "").strip().upper()
    return str(getattr(raw, "geometry_role", "") or "").strip().upper()


def is_early_svg_component_association(request: IntakeV6FinishSetup) -> bool:
    """Step-1 Contur suport / SUPPORT_CONTOUR may persist before layer roles are complete.

    Derived closed-contour geometry is canonical via svg_component_bindings — it must not
    be forced through a fake legacy layer role. Full confirmed FinishSetup still requires
    complete layer roles.
    """
    if bool(getattr(request, "confirmed", False)):
        return False
    bindings = list(getattr(request, "svg_component_bindings", None) or [])
    if any(_binding_geometry_role(item) == "SUPPORT_CONTOUR" for item in bindings):
        return True
    selection = getattr(request, "svg_support_selection", None)
    if isinstance(selection, dict):
        status = str(selection.get("status") or "").strip().lower()
        role = str(selection.get("role") or "").strip().upper()
        if status in {"proposed", "confirmed", "draft", "reconfirm_required"} and role == "ALUCOBOND_CASED_PANEL":
            return True
    if getattr(request, "acm_panel_instance", None):
        return True
    return False


def _assert_early_svg_association_preconditions(payload_raw: dict[str, Any]) -> None:
    """Lightweight gate for Step-1 support association — does not require complete layer roles."""
    blockers: list[str] = []
    svg_source = payload_raw.get("svg_source") if isinstance(payload_raw.get("svg_source"), dict) else {}
    if not str(svg_source.get("file_hash") or "").strip() and not payload_raw.get("svg_analysis_json"):
        blockers.append("missing_svg_analysis")
    if _layer_setup_from_payload(payload_raw) is None:
        blockers.append("missing_layer_role_setup")
    if blockers:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "early_svg_association_blocked",
                "message": "SVG analysis and layer_role_setup must exist before Contur suport association.",
                "blockers": blockers,
            },
        )


async def save_finish_setup_for_intake_v6_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV6FinishSetup,
    current_user: UserResponse,
) -> IntakeV6WorkspaceResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived", "workspace_id": workspace_id})

    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    setup = _layer_setup_from_payload(payload_raw)
    roles_complete = setup is not None and setup.confirmation_status == "complete"
    early_svg_association = is_early_svg_component_association(request)

    if setup is None:
        raise HTTPException(status_code=422, detail={"error": "layer_roles_incomplete"})
    if not roles_complete and not early_svg_association:
        raise HTTPException(status_code=422, detail={"error": "layer_roles_incomplete"})

    payload = _parse_payload(payload_raw)
    from services.intake_v6_analysis_boundary_service import assert_v6_analysis_boundary_or_raise

    if early_svg_association and not roles_complete:
        # early_svg_component_association: skip full analysis-boundary layer_roles gate
        _assert_early_svg_association_preconditions(payload_raw)
    else:
        assert_v6_analysis_boundary_or_raise(payload)

    from services.intake_v6_finish_truth_service import normalize_intake_v6_finish_setup
    from services.intake_v4_finish_truth_service import (
        dump_intake_v4_finish_setup_for_persist,
        strip_global_backing_mirror_from_finish_dict,
    )
    from services.svg_component_binding_persistence import (
        persist_normalized_bindings_on_finish,
        sync_support_selection_from_bindings,
        validate_bindings_for_new_selection,
    )
    from schemas.intake_v4 import IntakeV4FinishSetup

    # Merge early association into existing finish_setup so sparse Step-1 patches do not wipe Review fields.
    if early_svg_association and not roles_complete:
        existing_finish = payload_raw.get("finish_setup")
        req_dump = request.model_dump(mode="json")
        if isinstance(existing_finish, dict) and existing_finish:
            merged = dict(existing_finish)
            for key in (
                "svg_component_bindings",
                "svg_support_selection",
                "mounting_solution",
                "power_supply_service_corner",
                "segmented_background",
                "acm_panel_instance",
                "acm_panel_domain_action",
            ):
                if req_dump.get(key) is not None:
                    merged[key] = req_dump[key]
            merged["confirmed"] = False
            merged["internal_draft_quote_confirmed"] = False
            request = IntakeV6FinishSetup.model_validate(merged)

    normalized = normalize_intake_v6_finish_setup(request)
    normalized = normalized.model_copy(update={"internal_draft_quote_confirmed": False})
    if early_svg_association and not roles_complete:
        # Never mark finish confirmed via early Contur suport association.
        normalized = normalized.model_copy(update={"confirmed": False})

    finish_doc = normalized.model_dump(mode="json")
    finish_doc = persist_normalized_bindings_on_finish(finish_doc)
    binding_blockers = validate_bindings_for_new_selection(finish_doc.get("svg_component_bindings") or [])
    if binding_blockers:
        raise HTTPException(
            status_code=422,
            detail={"error": "svg_component_binding_invalid", "blockers": binding_blockers},
        )
    finish_doc = sync_support_selection_from_bindings(finish_doc)
    from services.acm_segmented_background_service import (
        coalesce_segmented_background_for_finish,
        persist_segmented_background_on_finish,
    )

    existing_finish_doc = (
        payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else None
    )
    finish_doc = coalesce_segmented_background_for_finish(finish_doc, existing_finish_doc)
    from services.acm_panel_domain_service import coalesce_acm_panel_domain_for_finish

    layer_setup_raw = (
        payload_raw.get("layer_role_setup") if isinstance(payload_raw.get("layer_role_setup"), dict) else None
    )
    finish_doc = coalesce_acm_panel_domain_for_finish(
        finish_doc,
        existing_finish_doc,
        layer_role_setup=layer_setup_raw,
    )

    try:
        finish_doc = persist_segmented_background_on_finish(finish_doc)
    except ValueError as exc:
        detail = exc.args[0] if exc.args else {"error": "segmented_background_invalid"}
        if not isinstance(detail, dict):
            detail = {"error": str(detail)}
        raise HTTPException(status_code=422, detail=detail) from exc
    normalized = IntakeV4FinishSetup.model_validate(finish_doc)

    # Validate against dossier (non-blocking — warnings stored in payload)
    from services.intake_v6_template_option_contract_service import validate_finish_setup_against_dossier

    template_code = record.template_code or "TPL-VOLUMETRIC-LETTERS"
    dossier_warnings = await validate_finish_setup_against_dossier(db, template_code, normalized)

    payload_raw["finish_setup"] = dump_intake_v4_finish_setup_for_persist(normalized)
    from services.intake_v6_volum_aluminum_module_truth_service import (
        apply_volum_aluminum_module_truth_to_workspace_payload,
    )

    await apply_volum_aluminum_module_truth_to_workspace_payload(
        db,
        template_code=template_code,
        payload_raw=payload_raw,
    )
    if payload_raw.get("finish_setup", {}).get("volum_aluminum_module_template_code"):
        code = payload_raw["finish_setup"]["volum_aluminum_module_template_code"]
        normalized = normalized.model_copy(update={"volum_aluminum_module_template_code": code})
    if payload_raw.get("layer_role_setup"):
        apply_product_composition_recommendation(payload_raw)
    if dossier_warnings:
        payload_raw.setdefault("_dossier_validation_warnings", [])
        payload_raw["_dossier_validation_warnings"] = dossier_warnings
    from services.intake_v6_pricing_preview_sync_service import apply_v6_pricing_preview_derived_state

    apply_v6_pricing_preview_derived_state(payload_raw)
    strip_global_backing_mirror_from_finish_dict(payload_raw.get("finish_setup"))
    apply_return_cant_runtime_product_truth_bridge(payload_raw)
    return await _persist_payload_json_raw_for_product_truth_writer(
        db,
        record,
        payload_raw,
        current_user=current_user,
    )


async def save_sheet_footprint_override_for_intake_v6_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: "IntakeV6SheetFootprintOverrideRequest",
    current_user: UserResponse,
):
    from schemas.intake_v6 import IntakeV6SheetFootprintOverrideResponse
    from services.intake_v6_sheet_footprint_override_service import (
        build_sheet_quote_override_record,
        validate_sheet_footprint_override_request,
    )

    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived", "workspace_id": workspace_id})

    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    if not payload_raw.get("svg_analysis_json"):
        raise HTTPException(status_code=422, detail={"error": "analysis_missing"})

    from services.intake_v6_nesting_material_precision import (
        apply_sheet_material_quantity_floor,
        compute_eligible_sheet_face_area_sum_sqm,
        compute_sheet_nesting_material_split,
        compute_sheet_quote_material_candidates,
    )
    from services.intake_v6_sheet_footprint_override_service import SheetFootprintCandidateAreas

    analysis = payload_raw.get("svg_analysis_json")
    layer_role_setup = payload_raw.get("layer_role_setup")
    eligible_face_area_sqm = None
    candidate_areas: SheetFootprintCandidateAreas | None = None
    if isinstance(analysis, dict):
        eligible_face_area_sqm = compute_eligible_sheet_face_area_sum_sqm(
            analysis,
            layer_role_setup if isinstance(layer_role_setup, dict) else None,
        )
        nesting = analysis.get("nesting")
        if isinstance(nesting, dict):
            sheet_split = compute_sheet_nesting_material_split(
                nesting,
                analysis,
                layer_role_setup if isinstance(layer_role_setup, dict) else None,
                face_area=eligible_face_area_sqm,
                backing_area=eligible_face_area_sqm,
            )
            sheet_split_pre = sheet_split
            floor_applied = False
            if sheet_split.mode != "prorated_fallback":
                sheet_split, floor_applied = apply_sheet_material_quantity_floor(
                    sheet_split,
                    eligible_face_area_sqm=eligible_face_area_sqm,
                )
            preview_candidates = compute_sheet_quote_material_candidates(
                nesting,
                analysis,
                layer_role_setup if isinstance(layer_role_setup, dict) else None,
                eligible_face_area_sqm=eligible_face_area_sqm,
                sheet_split_pre_floor=sheet_split_pre,
                selected_quote_sheet_area_sqm=sheet_split.face_area_sqm,
                sheet_quantity_floor_applied=floor_applied,
                sheet_quote_override=None,
            )
            if preview_candidates is not None:
                candidate_areas = SheetFootprintCandidateAreas(
                    eligible_face_area_sqm=preview_candidates.eligible_face_area_sqm,
                    placement_footprint_face_sqm=preview_candidates.placement_footprint_face_sqm,
                    face_union_bbox_sqm=preview_candidates.face_union_bbox_sqm,
                    layout_occupied_area_sqm=preview_candidates.layout_occupied_area_sqm,
                    full_sheet_allocation_sqm=preview_candidates.full_sheet_allocation_sqm,
                    operator_manual_footprint_sqm=None,
                )

    previous_override = payload_raw.get("sheet_quote_override")
    selected_source = request.selected_footprint_source.strip()
    try:
        resolved_area_sqm, validation_warnings = validate_sheet_footprint_override_request(
            selected_footprint_source=selected_source,
            width_cm=request.width_cm,
            height_cm=request.height_cm,
            reason=request.reason,
            use_for_quote_estimate=request.use_for_quote_estimate,
            eligible_face_area_sqm=eligible_face_area_sqm,
            candidate_areas=candidate_areas,
            full_sheet_sqm=6.0,
        )
    except ValueError as exc:
        code = str(exc)
        status_code = 422
        if code == "note_required":
            detail = {"error": code, "message": "Notă operator obligatorie pentru footprint manual."}
        elif code == "footprint_below_eligible_area":
            detail = {
                "error": code,
                "message": "Footprint manual este sub aria pieselor eligibile.",
            }
        elif code == "footprint_source_unavailable":
            detail = {
                "error": code,
                "message": "Sursa footprint selectată nu are valoare disponibilă în analiza curentă.",
            }
        elif code == "invalid_footprint_source":
            detail = {"error": code, "message": "Sursă footprint invalidă."}
        else:
            detail = {"error": code, "message": "Dimensiuni footprint invalide."}
        raise HTTPException(status_code=status_code, detail=detail) from exc

    override_record = build_sheet_quote_override_record(
        selected_footprint_source=selected_source,
        width_cm=request.width_cm,
        height_cm=request.height_cm,
        reason=request.reason or f"Sursă footprint: {selected_source}",
        applies_to=request.applies_to,
        use_for_quote_estimate=request.use_for_quote_estimate,
        created_by=current_user.email or str(current_user.id),
        previous=previous_override if isinstance(previous_override, dict) else None,
    )
    if resolved_area_sqm is not None:
        override_record["areaSqm"] = resolved_area_sqm
    if validation_warnings:
        override_record["validationWarnings"] = validation_warnings
    payload_raw["sheet_quote_override"] = override_record
    payload = _parse_payload(payload_raw)
    await _persist_payload(db, record, payload, current_user=current_user)
    return IntakeV6SheetFootprintOverrideResponse(
        enabled=True,
        source="operator_manual_footprint",
        selected_footprint_source=override_record.get("selectedFootprintSource"),
        width_cm=override_record.get("widthCm"),
        height_cm=override_record.get("heightCm"),
        area_sqm=resolved_area_sqm or override_record.get("areaSqm"),
        reason=override_record["reason"],
        applies_to=override_record["appliesTo"],
        use_for_quote_estimate=override_record["useForQuoteEstimate"],
        created_by=override_record.get("createdBy"),
        created_at=override_record.get("createdAt"),
    )


async def preview_reanalyze_for_intake_v6_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: "IntakeV6ReanalyzePreviewRequest",
    current_user: UserResponse,
):
    from schemas.intake_v6 import IntakeV6ReanalyzePreviewResponse, IntakeV6ReanalyzePreviewSnapshot
    from services.intake_v6_reanalyze_preview_service import compare_reanalyze_preview
    from services.intake_v6_sheet_footprint_override_service import sheet_quote_override_from_payload

    _ = current_user
    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    persisted = payload_raw.get("svg_analysis_json")
    if not isinstance(persisted, dict):
        raise HTTPException(status_code=422, detail={"error": "analysis_missing"})

    layer_role_setup = payload_raw.get("layer_role_setup")
    if not isinstance(layer_role_setup, dict):
        layer_role_setup = None

    diff = compare_reanalyze_preview(
        persisted_analysis=persisted,
        fresh_analysis=request.svg_analysis_json,
        layer_role_setup=layer_role_setup,
        sheet_quote_override=sheet_quote_override_from_payload(payload_raw),
    )

    def _snapshot(raw: dict[str, Any] | None) -> IntakeV6ReanalyzePreviewSnapshot | None:
        if not raw:
            return None
        return IntakeV6ReanalyzePreviewSnapshot(**raw)

    return IntakeV6ReanalyzePreviewResponse(
        workspace_id=workspace_id,
        before=_snapshot(diff.get("before")),
        after=_snapshot(diff.get("after")),
        selected_quantity_unchanged=bool(diff.get("selected_quantity_unchanged")),
        persists_changes=False,
        stale_snapshot_detected=bool(diff.get("stale_snapshot_detected")),
        preview_available=bool(diff.get("preview_available")),
    )


async def save_internal_draft_quote_confirmation_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    *,
    confirmed: bool,
    current_user: UserResponse,
) -> IntakeV6WorkspaceResponse:
    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(status_code=400, detail={"error": "workspace_archived", "workspace_id": workspace_id})

    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    payload = _parse_payload(payload_raw)
    setup = payload.finish_setup
    if setup is None or not setup.confirmed:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "finish_setup_not_confirmed",
                "message": "Finalizează și confirmă finisajele în Review înainte de draft quote.",
                "blockers": ["finish_setup_not_confirmed"],
            },
        )

    if confirmed:
        from services.intake_v6_internal_draft_quote_policy_service import evaluate_internal_draft_quote_policy

        preview_policy = evaluate_internal_draft_quote_policy(
            record,
            payload,
            include_hash_sync=False,
        )
        fatal_for_confirm = [
            code for code in preview_policy.fatal_blockers if code != "operator_confirmation_missing"
        ]
        if fatal_for_confirm:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "INTERNAL_DRAFT_CONFIRMATION_BLOCKED",
                    "message": "Internal draft quote confirmation blocked by fatal readiness issues.",
                    "fatal_blockers": fatal_for_confirm,
                },
            )

    finish_dict = setup.model_dump(mode="json")
    finish_dict["internal_draft_quote_confirmed"] = confirmed
    payload_raw["finish_setup"] = finish_dict
    payload = _parse_payload(payload_raw)
    return await _persist_payload(db, record, payload, current_user=current_user)


async def get_pricing_input_preview_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from schemas.intake_v6 import IntakeV6PricingInputPreviewResponse
    from services.intake_v6_analysis_boundary_service import assert_v6_analysis_boundary_or_raise
    from services.intake_v6_pricing_input_service import build_v6_pricing_input_preview

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    payload = _parse_payload(payload_raw)
    assert_v6_analysis_boundary_or_raise(payload)
    return build_v6_pricing_input_preview(
        workspace_id=workspace_id,
        payload=payload,
        template_code=record.template_code,
        payload_raw=payload_raw,
    )


async def get_production_task_dry_run_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v6_production_task_dry_run_service import build_v6_production_task_dry_run

    record = await _get_record_or_404(db, workspace_id)
    payload = _parse_payload(_json_loads(record.payload_json, {}))
    return build_v6_production_task_dry_run(workspace_id=workspace_id, payload=payload)


async def get_production_handoff_preview_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v6_production_handoff_preview_service import (
        build_intake_v6_production_handoff_preview,
    )

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    payload = _parse_payload(payload_raw)
    return await build_intake_v6_production_handoff_preview(
        db,
        workspace_id,
        payload_raw,
        payload,
    )


async def get_task_generation_dry_run_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v6_task_generation_dry_run_service import (
        build_intake_v6_task_generation_dry_run,
    )

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    payload = _parse_payload(payload_raw)
    return await build_intake_v6_task_generation_dry_run(
        db,
        workspace_id,
        payload_raw,
        payload,
    )


async def get_order_bound_task_readiness_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v6_order_bound_task_readiness_service import (
        build_intake_v6_order_bound_task_readiness,
    )

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    payload = _parse_payload(payload_raw)
    return await build_intake_v6_order_bound_task_readiness(
        db,
        workspace_id,
        payload_raw,
        payload,
    )


async def get_ai_informational_assist_candidate_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v6_ai_semantic_classification_service import (
        build_intake_v6_ai_informational_assist_preview,
    )

    record = await _get_record_or_404(db, workspace_id)
    payload = _parse_payload(_json_loads(record.payload_json, {}))
    return build_intake_v6_ai_informational_assist_preview(
        workspace_id=workspace_id,
        payload=payload,
    )


async def get_ai_semantic_classification_candidate_for_workspace(
    db: AsyncSession,
    workspace_id: str,
):
    from services.intake_v6_ai_semantic_classification_service import (
        build_intake_v6_ai_semantic_classification_preview,
    )

    record = await _get_record_or_404(db, workspace_id)
    payload = _parse_payload(_json_loads(record.payload_json, {}))
    return build_intake_v6_ai_semantic_classification_preview(
        workspace_id=workspace_id,
        payload=payload,
    )


async def create_draft_quote_for_intake_v6_workspace(
    db: AsyncSession,
    workspace_id: str,
    request,
    current_user: UserResponse,
):
    from schemas.intake_v6 import IntakeV6CreateDraftQuoteRequest, IntakeV6CreateDraftQuoteResponse
    from services.intake_v6_commercial_quote_service import create_guarded_draft_quote_from_intake_v6_workspace

    if not isinstance(request, IntakeV6CreateDraftQuoteRequest):
        request = IntakeV6CreateDraftQuoteRequest.model_validate(request)
    return await create_guarded_draft_quote_from_intake_v6_workspace(
        db,
        workspace_id,
        request,
        current_user,
    )

