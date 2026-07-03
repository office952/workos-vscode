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
)
from services.intake_v6_product_system_service import (
    build_binding_response,
    resolve_product_template_or_raise,
)
from services.product_template_availability_service import ProductTemplateAvailabilityService
from services.intake_v6_production_preview_service import build_v6_task_preview_response


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


def _derive_readiness_status(payload: IntakeV6WorkspacePayload) -> str:
    if payload.svg_source is None or payload.svg_source.upload_status != "analyzed":
        return "missing_svg"
    setup = payload.layer_role_setup
    if setup is None or setup.confirmation_status != "complete":
        return "layer_roles_incomplete"
    if payload.finish_setup is None or not payload.finish_setup.confirmed:
        return "finish_setup_incomplete"
    return "ready_for_quote_preview"


def _derive_workspace_status(readiness_status: str) -> str:
    if readiness_status == "ready_for_quote_preview":
        return "ready_for_quote_preview"
    if readiness_status in {"missing_svg", "layer_roles_incomplete"}:
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
        selected_template_code=(request.selected_template_code or request.template_code),
        source=(request.source or None),
        work_intake_context={
            "offer_method": request.offer_method,
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


async def ensure_intake_v6_workspace_for_intake_request(
    db: AsyncSession,
    intake_request_code: str,
    current_user: UserResponse,
    *,
    offer_method: str | None = None,
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
        selected_template_code,
        require_selected=(source == "work_intake_new_request"),
    )
    create_request = IntakeV6WorkspaceCreateRequest(
        title=title,
        template_code=resolved_template_code,
        client_name=intake.client_name,
        job_title=description or None,
        intake_request_code=code,
        offer_method=offer_method,
        selected_template_code=resolved_template_code,
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
    payload_raw["layer_role_setup"] = layer_setup.model_dump(mode="json")
    if svg_source_replaced:
        payload_raw.pop("finish_setup", None)
    else:
        _reset_internal_draft_quote_confirmation(payload_raw)

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
    if svg_source_replaced:
        payload_raw.pop("finish_setup", None)
        payload_raw.pop("quote_geometry", None)
    else:
        from services.intake_v6_pricing_preview_sync_service import apply_v6_pricing_preview_derived_state

        apply_v6_pricing_preview_derived_state(payload_raw)
        _reset_internal_draft_quote_confirmation(payload_raw)

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
    _reset_internal_draft_quote_confirmation(payload_raw)
    if payload_raw.get("finish_setup"):
        from services.intake_v6_pricing_preview_sync_service import apply_v6_pricing_preview_derived_state

        apply_v6_pricing_preview_derived_state(payload_raw)
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
    if setup is None or setup.confirmation_status != "complete":
        raise HTTPException(status_code=422, detail={"error": "layer_roles_incomplete"})

    payload = _parse_payload(payload_raw)
    from services.intake_v6_analysis_boundary_service import assert_v6_analysis_boundary_or_raise

    assert_v6_analysis_boundary_or_raise(payload)

    from services.intake_v6_finish_truth_service import normalize_intake_v6_finish_setup

    normalized = normalize_intake_v6_finish_setup(request)
    normalized = normalized.model_copy(update={"internal_draft_quote_confirmed": False})

    # Validate against dossier (non-blocking â€” warnings stored in payload)
    from services.intake_v6_template_option_contract_service import validate_finish_setup_against_dossier

    template_code = record.template_code or "TPL-VOLUMETRIC-LETTERS"
    dossier_warnings = await validate_finish_setup_against_dossier(db, template_code, normalized)

    payload_raw["finish_setup"] = normalized.model_dump(mode="json")
    if dossier_warnings:
        payload_raw.setdefault("_dossier_validation_warnings", [])
        payload_raw["_dossier_validation_warnings"] = dossier_warnings
    from services.intake_v6_pricing_preview_sync_service import apply_v6_pricing_preview_derived_state

    apply_v6_pricing_preview_derived_state(payload_raw)
    payload = _parse_payload(payload_raw)
    return await _persist_payload(db, record, payload, current_user=current_user)


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
            detail = {"error": code, "message": "NotÄƒ operator obligatorie pentru footprint manual."}
        elif code == "footprint_below_eligible_area":
            detail = {
                "error": code,
                "message": "Footprint manual este sub aria pieselor eligibile.",
            }
        elif code == "footprint_source_unavailable":
            detail = {
                "error": code,
                "message": "Sursa footprint selectatÄƒ nu are valoare disponibilÄƒ Ã®n analiza curentÄƒ.",
            }
        elif code == "invalid_footprint_source":
            detail = {"error": code, "message": "SursÄƒ footprint invalidÄƒ."}
        else:
            detail = {"error": code, "message": "Dimensiuni footprint invalide."}
        raise HTTPException(status_code=status_code, detail=detail) from exc

    override_record = build_sheet_quote_override_record(
        selected_footprint_source=selected_source,
        width_cm=request.width_cm,
        height_cm=request.height_cm,
        reason=request.reason or f"SursÄƒ footprint: {selected_source}",
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
                "message": "FinalizeazÄƒ È™i confirmÄƒ finisajele Ã®n Review Ã®nainte de draft quote.",
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
    payload = _parse_payload(_json_loads(record.payload_json, {}))
    assert_v6_analysis_boundary_or_raise(payload)
    return build_v6_pricing_input_preview(
        workspace_id=workspace_id,
        payload=payload,
        template_code=record.template_code,
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

