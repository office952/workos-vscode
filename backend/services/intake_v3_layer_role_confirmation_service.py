"""Intake V3 operator layer role confirmation — draft workspace only, no production side effects."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from schemas.intake_v3 import (
    IntakeV3LayerRoleConfirmationLayer,
    IntakeV3LayerRoleConfirmationResponse,
    IntakeV3LayerRoleConfirmationSnapshot,
    IntakeV3LayerRoleConfirmationUpdateRequest,
    IntakeV3LayerRoleConfirmationWarning,
    IntakeV3Workspace,
)
from services.intake_v3_geometry_path_perimeter_classification_service import normalize_svg_layer_role
from services.intake_v3_material_quantity_breakdown_service import (
    Iv3SourceContext,
    load_iv3_source_context,
)
from services.intake_v3_real_commercial_quote_creation_service import INTAKE_V3_SOURCE_MODULE

LAYER_ROLE_CONFIRMATION_VERSION = "layer_role_confirmation_v1"
WARN_LAYER_ROLE_CONFIRMATION_RESET_AFTER_SVG_REUPLOAD = "layer_role_confirmation_reset_after_svg_reupload"

ALLOWED_LAYER_ROLES: frozenset[str] = frozenset(
    {
        "face",
        "backing",
        "return",
        "bevel",
        "inner_hole",
        "support_panel",
        "frame",
        "vinyl",
        "drill",
        "reference",
        "ignore",
        "unknown",
        "printed_artwork",
        "logo",
        "artwork",
        "policromie",
    }
)

ALLOWED_CONFIRMATION_STATES: frozenset[str] = frozenset(
    {"confirmed", "ignored", "pending", "unconfirmed"}
)

PRODUCTION_CLASSIFICATION_ROLES: frozenset[str] = frozenset(
    {"face", "backing", "return", "bevel", "inner_hole", "support_panel", "frame", "vinyl"}
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _warning(code: str, message: str, *, source: str) -> IntakeV3LayerRoleConfirmationWarning:
    return IntakeV3LayerRoleConfirmationWarning(
        code=code,
        severity="warning",
        message=message,
        source=source,
    )


def layer_key_from_path_layer(layer: dict[str, Any]) -> str:
    layer_id = layer.get("layer_id")
    layer_name = layer.get("layer_name")
    if layer_id:
        return str(layer_id)
    if layer_name:
        return str(layer_name)
    return "__ungrouped__"


def _normalize_confirmed_role(role: str | None) -> str:
    if not role:
        return "unknown"
    normalized = role.strip().lower()
    if normalized == "letters":
        return "face"
    return normalized


def _auto_role_for_layer(layer: dict[str, Any]) -> str:
    layer_id = layer.get("layer_id")
    layer_name = layer.get("layer_name")
    token = str(layer_name or layer_id or "")
    color_evidence = layer.get("color_evidence") if isinstance(layer.get("color_evidence"), dict) else {}
    element_counts = layer.get("element_counts") if isinstance(layer.get("element_counts"), dict) else {}

    polygons = int(element_counts.get("polygons") or layer.get("polygon_count") or 0)
    rects = int(element_counts.get("rects") or layer.get("rect_count") or 0)
    paths = int(element_counts.get("paths") or layer.get("path_count") or 0)
    fills = color_evidence.get("fills") or []
    strokes = color_evidence.get("strokes") or []
    is_multicolor = bool(color_evidence.get("is_multicolor"))

    token_lower = token.lower()
    if is_multicolor or (polygons >= 50 and len(fills) >= 3):
        if any(marker in token_lower for marker in ("emblema", "logo", "policrom", "artwork", "print")):
            return "printed_artwork"
        if polygons >= 20:
            return "printed_artwork"

    if rects > 0 and paths == 0 and polygons == 0 and not fills:
        if any(marker in token_lower for marker in ("cadru", "guide", "ghidaj", "referin", "alignment")):
            return "reference"
        return "reference"

    role = normalize_svg_layer_role(token)
    if role == "letters":
        return "face"
    if role == "frame" and rects > 0 and paths == 0:
        return "reference"
    return role


def _layer_metrics(layer: dict[str, Any]) -> dict[str, Any]:
    element_counts = layer.get("element_counts") if isinstance(layer.get("element_counts"), dict) else {}
    return {
        "perimeter_mm": layer.get("perimeter_mm"),
        "area_mm2": layer.get("area_mm2"),
        "closed_contour_count": layer.get("closed_contour_count"),
        "path_count": layer.get("path_count"),
        "polygon_count": element_counts.get("polygons", layer.get("polygon_count")),
        "rect_count": element_counts.get("rects", layer.get("rect_count")),
        "element_total": element_counts.get("total"),
    }


def _layer_color_evidence(layer: dict[str, Any]) -> dict[str, Any] | None:
    raw = layer.get("color_evidence")
    return raw if isinstance(raw, dict) else None


def _layer_font_evidence(layer: dict[str, Any]) -> dict[str, Any] | None:
    raw = layer.get("font_evidence")
    return raw if isinstance(raw, dict) else None


def extract_path_geometry_summary_from_workspace(workspace: IntakeV3Workspace | None) -> dict[str, Any] | None:
    if workspace is None or not workspace.path_geometry_summary:
        return None
    summary = workspace.path_geometry_summary
    return summary if isinstance(summary, dict) else None


def extract_layer_role_confirmation_snapshot(
    context: Iv3SourceContext,
) -> IntakeV3LayerRoleConfirmationSnapshot | None:
    raw = context.sections.get("layer_role_confirmation_snapshot")
    if isinstance(raw, dict):
        try:
            return IntakeV3LayerRoleConfirmationSnapshot.model_validate(raw)
        except Exception:
            pass
    if context.workspace and context.workspace.layer_role_confirmation_snapshot:
        try:
            return IntakeV3LayerRoleConfirmationSnapshot.model_validate(
                context.workspace.layer_role_confirmation_snapshot
            )
        except Exception:
            return None
    nested = context.sections.get("workspace_payload_snapshot")
    if isinstance(nested, dict):
        nested_raw = nested.get("layer_role_confirmation_snapshot")
        if isinstance(nested_raw, dict):
            try:
                return IntakeV3LayerRoleConfirmationSnapshot.model_validate(nested_raw)
            except Exception:
                return None
    return None


def build_layer_role_confirmation_draft_from_path_geometry(
    path_summary: dict[str, Any] | None,
    *,
    workspace_id: str,
) -> IntakeV3LayerRoleConfirmationSnapshot:
    warnings: list[IntakeV3LayerRoleConfirmationWarning] = []
    layers: list[IntakeV3LayerRoleConfirmationLayer] = []
    ignored_layers: list[str] = []
    unknown_layers: list[str] = []

    if not path_summary or path_summary.get("parse_status") != "parsed":
        warnings.append(
            _warning(
                "path_geometry_summary_missing",
                "Path geometry summary is missing or not parsed — layer role confirmation unavailable.",
                source="path_geometry_summary",
            )
        )
        return IntakeV3LayerRoleConfirmationSnapshot(
            workspace_id=workspace_id,
            confirmation_status="missing",
            layers=[],
            ignored_layers=[],
            unknown_layers=[],
            warnings=warnings,
        )

    path_layers = path_summary.get("layers") or []
    if not path_layers:
        warnings.append(
            _warning(
                "layer_metrics_missing",
                "Path geometry summary has no layer breakdown.",
                source="path_geometry_summary.layers",
            )
        )

    for layer in path_layers:
        if not isinstance(layer, dict):
            continue
        layer_key = layer_key_from_path_layer(layer)
        auto_role = _auto_role_for_layer(layer)
        auto_confidence = "medium" if auto_role not in {"unknown", "ignore"} else "low"
        if auto_role in {"printed_artwork", "reference"}:
            auto_confidence = "high" if auto_role == "printed_artwork" else "medium"
        color_raw = _layer_color_evidence(layer)
        font_raw = _layer_font_evidence(layer)
        entry = IntakeV3LayerRoleConfirmationLayer(
            layer_key=layer_key,
            layer_id=layer.get("layer_id"),
            layer_name=layer.get("layer_name"),
            auto_role=auto_role,
            auto_confidence=auto_confidence,
            confirmed_role=None,
            confirmed_confidence=None,
            confirmation_state="pending",
            operator_note=None,
            metrics=_layer_metrics(layer),
            color_evidence=color_raw,
            font_evidence=font_raw,
        )
        layers.append(entry)
        if auto_role == "unknown":
            unknown_layers.append(layer_key)

    status = "missing"
    if layers:
        status = "partial"

    return IntakeV3LayerRoleConfirmationSnapshot(
        workspace_id=workspace_id,
        confirmation_status=status,
        layers=layers,
        ignored_layers=ignored_layers,
        unknown_layers=unknown_layers,
        warnings=warnings,
    )


def validate_layer_role_confirmation_update(
    path_summary: dict[str, Any] | None,
    request: IntakeV3LayerRoleConfirmationUpdateRequest,
) -> tuple[dict[str, dict[str, Any]], list[IntakeV3LayerRoleConfirmationWarning]]:
    if not path_summary or path_summary.get("parse_status") != "parsed":
        raise HTTPException(
            status_code=422,
            detail={
                "error": "PATH_GEOMETRY_SUMMARY_MISSING",
                "message": "SVG layer path geometry is required before confirming layer roles.",
            },
        )

    valid_keys = {
        layer_key_from_path_layer(layer)
        for layer in (path_summary.get("layers") or [])
        if isinstance(layer, dict)
    }
    if not valid_keys:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "LAYER_METRICS_MISSING",
                "message": "No SVG layers available for role confirmation.",
            },
        )

    updates: dict[str, dict[str, Any]] = {}
    warnings: list[IntakeV3LayerRoleConfirmationWarning] = []

    for item in request.layers:
        layer_key = item.layer_key.strip()
        if layer_key not in valid_keys:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "UNKNOWN_LAYER_KEY",
                    "message": f"Layer key '{layer_key}' is not present in path_geometry_summary.layers.",
                    "layer_key": layer_key,
                },
            )

        confirmed_role = _normalize_confirmed_role(item.confirmed_role)
        if confirmed_role not in ALLOWED_LAYER_ROLES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_LAYER_ROLE",
                    "message": f"Role '{item.confirmed_role}' is not allowed.",
                    "allowed_roles": sorted(ALLOWED_LAYER_ROLES),
                },
            )

        state = item.confirmation_state.strip().lower()
        if state not in ALLOWED_CONFIRMATION_STATES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_CONFIRMATION_STATE",
                    "message": f"Confirmation state '{item.confirmation_state}' is not allowed.",
                },
            )

        if state == "ignored" or confirmed_role == "ignore":
            state = "ignored"
            confirmed_role = "ignore"

        updates[layer_key] = {
            "confirmed_role": confirmed_role,
            "confirmation_state": state,
            "operator_note": item.operator_note,
        }

    return updates, warnings


def apply_layer_role_updates_to_snapshot(
    draft: IntakeV3LayerRoleConfirmationSnapshot,
    updates: dict[str, dict[str, Any]],
    *,
    confirmed_by: str | None = None,
) -> IntakeV3LayerRoleConfirmationSnapshot:
    layers: list[IntakeV3LayerRoleConfirmationLayer] = []
    ignored_layers: list[str] = []
    unknown_layers: list[str] = []
    warnings = list(draft.warnings)

    confirmed_count = 0
    pending_count = 0

    for layer in draft.layers:
        update = updates.get(layer.layer_key)
        confirmed_role = layer.confirmed_role
        confirmation_state = layer.confirmation_state
        confirmed_confidence = layer.confirmed_confidence
        operator_note = layer.operator_note

        if update:
            confirmed_role = _normalize_confirmed_role(update["confirmed_role"])
            confirmation_state = update["confirmation_state"]
            operator_note = update.get("operator_note")
            if confirmation_state == "ignored" or confirmed_role == "ignore":
                confirmation_state = "ignored"
                confirmed_role = "ignore"
                confirmed_confidence = "high"
                ignored_layers.append(layer.layer_key)
            elif confirmation_state == "confirmed" and confirmed_role not in {"unknown", "ignore"}:
                confirmed_confidence = "high"
                confirmed_count += 1
            elif confirmation_state == "confirmed" and confirmed_role == "unknown":
                confirmed_confidence = "high"
                unknown_layers.append(layer.layer_key)
                confirmed_count += 1
            else:
                pending_count += 1
                confirmed_confidence = None
        else:
            if layer.auto_role == "unknown":
                unknown_layers.append(layer.layer_key)
            pending_count += 1

        layers.append(
            layer.model_copy(
                update={
                    "confirmed_role": confirmed_role,
                    "confirmed_confidence": confirmed_confidence,
                    "confirmation_state": confirmation_state,
                    "operator_note": operator_note,
                }
            )
        )

    if confirmed_count == len(layers) and layers:
        status = "complete"
    elif confirmed_count > 0:
        status = "partial"
    else:
        status = "partial" if layers else "missing"

    if pending_count > 0:
        warnings.append(
            _warning(
                "layer_roles_unconfirmed",
                "Some SVG layers remain unconfirmed by the operator.",
                source="layer_role_confirmation_snapshot",
            )
        )
    if unknown_layers:
        warnings.append(
            _warning(
                "unknown_layers_present",
                "Some layers are marked unknown and will not contribute to perimeter classification.",
                source="layer_role_confirmation_snapshot",
            )
        )
    if ignored_layers:
        warnings.append(
            _warning(
                "ignored_layers_present",
                "Some layers are ignored and excluded from perimeter classification.",
                source="layer_role_confirmation_snapshot",
            )
        )

    return draft.model_copy(
        update={
            "confirmed_at": _utcnow_iso(),
            "confirmed_by": confirmed_by,
            "confirmation_status": status,
            "layers": layers,
            "ignored_layers": ignored_layers,
            "unknown_layers": unknown_layers,
            "warnings": warnings,
        }
    )


def merge_layer_role_confirmation_into_workspace_payload(
    payload: dict[str, Any],
    snapshot: IntakeV3LayerRoleConfirmationSnapshot,
) -> dict[str, Any]:
    updated = dict(payload)
    updated["layer_role_confirmation_snapshot"] = snapshot.model_dump(mode="json")
    return updated


def layer_keys_from_path_geometry_summary(path_summary: dict[str, Any] | None) -> frozenset[str]:
    if not path_summary or path_summary.get("parse_status") != "parsed":
        return frozenset()
    keys: set[str] = set()
    for layer in path_summary.get("layers") or []:
        if isinstance(layer, dict):
            keys.add(layer_key_from_path_layer(layer))
    return frozenset(keys)


def layer_keys_from_confirmation_snapshot(
    snapshot: IntakeV3LayerRoleConfirmationSnapshot | None,
) -> frozenset[str]:
    if snapshot is None:
        return frozenset()
    return frozenset(layer.layer_key for layer in snapshot.layers)


def is_layer_role_confirmation_stale(
    path_summary: dict[str, Any] | None,
    snapshot: IntakeV3LayerRoleConfirmationSnapshot | None,
) -> bool:
    if snapshot is None:
        return False
    new_keys = layer_keys_from_path_geometry_summary(path_summary)
    if not new_keys:
        return False
    return new_keys != layer_keys_from_confirmation_snapshot(snapshot)


def _recompute_confirmation_status(
    snapshot: IntakeV3LayerRoleConfirmationSnapshot,
) -> IntakeV3LayerRoleConfirmationSnapshot:
    ignored_layers: list[str] = []
    unknown_layers: list[str] = []
    confirmed_count = 0
    pending_count = 0

    for layer in snapshot.layers:
        if layer.confirmation_state == "ignored" or layer.confirmed_role == "ignore":
            ignored_layers.append(layer.layer_key)
        elif layer.confirmation_state == "confirmed" and layer.confirmed_role:
            if layer.confirmed_role == "unknown":
                unknown_layers.append(layer.layer_key)
            confirmed_count += 1
        else:
            if layer.auto_role == "unknown":
                unknown_layers.append(layer.layer_key)
            pending_count += 1

    if confirmed_count == len(snapshot.layers) and snapshot.layers:
        status = "complete"
    elif confirmed_count > 0 or snapshot.layers:
        status = "partial"
    else:
        status = "missing"

    warnings = list(snapshot.warnings)
    if pending_count > 0 and not any(w.code == "layer_roles_unconfirmed" for w in warnings):
        warnings.append(
            _warning(
                "layer_roles_unconfirmed",
                "Some SVG layers remain unconfirmed by the operator.",
                source="layer_role_confirmation_snapshot",
            )
        )

    return snapshot.model_copy(
        update={
            "confirmation_status": status,
            "ignored_layers": ignored_layers,
            "unknown_layers": unknown_layers,
            "warnings": warnings,
        }
    )


def merge_preserved_roles_into_draft(
    draft: IntakeV3LayerRoleConfirmationSnapshot,
    previous: IntakeV3LayerRoleConfirmationSnapshot | None,
) -> IntakeV3LayerRoleConfirmationSnapshot:
    if previous is None:
        return draft

    prev_lookup = build_layer_role_confirmation_lookup(previous)
    merged_layers: list[IntakeV3LayerRoleConfirmationLayer] = []

    for layer in draft.layers:
        prev = prev_lookup.get(layer.layer_key)
        if prev is None:
            merged_layers.append(layer)
            continue
        if prev.confirmation_state == "ignored" or prev.confirmed_role == "ignore":
            merged_layers.append(
                layer.model_copy(
                    update={
                        "confirmed_role": "ignore",
                        "confirmed_confidence": "high",
                        "confirmation_state": "ignored",
                        "operator_note": prev.operator_note,
                    }
                )
            )
        elif prev.confirmation_state == "confirmed" and prev.confirmed_role:
            merged_layers.append(
                layer.model_copy(
                    update={
                        "confirmed_role": prev.confirmed_role,
                        "confirmed_confidence": prev.confirmed_confidence or "high",
                        "confirmation_state": "confirmed",
                        "operator_note": prev.operator_note,
                    }
                )
            )
        else:
            merged_layers.append(layer)

    return _recompute_confirmation_status(
        draft.model_copy(
            update={
                "layers": merged_layers,
                "confirmed_at": previous.confirmed_at,
                "confirmed_by": previous.confirmed_by,
            }
        )
    )


def reconcile_layer_role_confirmation_after_path_geometry_update(
    payload: dict[str, Any],
    *,
    workspace_id: str,
    path_summary: dict[str, Any] | None,
    svg_source_replaced: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Rebuild layer role confirmation when SVG path geometry layer set changes."""
    previous: IntakeV3LayerRoleConfirmationSnapshot | None = None
    previous_raw = payload.get("layer_role_confirmation_snapshot")
    if isinstance(previous_raw, dict):
        try:
            previous = IntakeV3LayerRoleConfirmationSnapshot.model_validate(previous_raw)
        except Exception:
            previous = None

    new_keys = layer_keys_from_path_geometry_summary(path_summary)
    if not new_keys:
        return payload, []

    old_keys = layer_keys_from_confirmation_snapshot(previous)
    draft = build_layer_role_confirmation_draft_from_path_geometry(
        path_summary,
        workspace_id=workspace_id,
    )
    warning_codes: list[str] = []

    if previous is not None and new_keys == old_keys and not svg_source_replaced:
        snapshot = merge_preserved_roles_into_draft(draft, previous)
        return merge_layer_role_confirmation_into_workspace_payload(payload, snapshot), warning_codes

    if previous is not None and (new_keys != old_keys or svg_source_replaced):
        warning_codes.append(WARN_LAYER_ROLE_CONFIRMATION_RESET_AFTER_SVG_REUPLOAD)
        if new_keys & old_keys and not svg_source_replaced:
            snapshot = merge_preserved_roles_into_draft(draft, previous)
        else:
            snapshot = _recompute_confirmation_status(draft)
        snapshot = snapshot.model_copy(
            update={
                "confirmed_at": None,
                "confirmed_by": None,
                "warnings": [
                    *snapshot.warnings,
                    _warning(
                        WARN_LAYER_ROLE_CONFIRMATION_RESET_AFTER_SVG_REUPLOAD,
                        "SVG re-upload changed detected layers — layer role confirmation was rebuilt.",
                        source="svg_reupload",
                    ),
                ],
            }
        )
    else:
        snapshot = draft

    return merge_layer_role_confirmation_into_workspace_payload(payload, snapshot), warning_codes


def build_layer_role_confirmation_lookup(
    snapshot: IntakeV3LayerRoleConfirmationSnapshot | None,
) -> dict[str, IntakeV3LayerRoleConfirmationLayer]:
    if snapshot is None:
        return {}
    return {layer.layer_key: layer for layer in snapshot.layers}


def build_layer_role_confirmation_response(
    context: Iv3SourceContext,
    *,
    snapshot: IntakeV3LayerRoleConfirmationSnapshot | None = None,
    persisted: bool = False,
) -> IntakeV3LayerRoleConfirmationResponse:
    if not context.is_intake_v3 and context.source_type != "workspace":
        return IntakeV3LayerRoleConfirmationResponse(
            source_module=INTAKE_V3_SOURCE_MODULE,
            source_type=context.source_type,
            source_id=context.source_id,
            is_intake_v3=False,
            snapshot_available=False,
            confirmation_status="missing",
            warnings=[
                _warning(
                    "not_intake_v3_source",
                    "Source is not an Intake V3 order/quote/workspace payload.",
                    source="source_detection",
                )
            ],
        )

    workspace_id = context.source_id if context.source_type == "workspace" else None
    if context.quote_linkage:
        workspace_id = workspace_id or context.quote_linkage.get("source_workspace_id")
    if context.order_linkage and not workspace_id:
        workspace_id = context.order_linkage.get("source_workspace_id")

    if snapshot is None:
        snapshot = extract_layer_role_confirmation_snapshot(context)
        if snapshot is None and context.workspace is not None:
            path_summary = extract_path_geometry_summary_from_workspace(context.workspace)
            snapshot = build_layer_role_confirmation_draft_from_path_geometry(
                path_summary,
                workspace_id=str(workspace_id or context.source_id),
            )

    order_id = context.order.id if context.order else None
    quote_id = context.quote.id if context.quote else None

    return IntakeV3LayerRoleConfirmationResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        order_id=order_id,
        quote_id=quote_id,
        source_workspace_id=str(workspace_id) if workspace_id else None,
        is_intake_v3=context.is_intake_v3 or context.source_type == "workspace",
        snapshot_available=snapshot is not None and bool(snapshot.layers),
        confirmation_status=snapshot.confirmation_status if snapshot else "missing",
        persisted=persisted,
        layer_role_confirmation_snapshot=snapshot,
        warnings=list(snapshot.warnings) if snapshot else [],
    )


async def get_layer_role_confirmation_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3LayerRoleConfirmationResponse:
    context = await load_iv3_source_context(db, workspace_id=workspace_id)
    if context.workspace is None:
        raise HTTPException(status_code=404, detail={"error": "workspace_not_found"})
    snapshot = extract_layer_role_confirmation_snapshot(context)
    path_summary = extract_path_geometry_summary_from_workspace(context.workspace)
    persisted = snapshot is not None
    if snapshot is not None and is_layer_role_confirmation_stale(path_summary, snapshot):
        stale_snapshot = snapshot
        snapshot = build_layer_role_confirmation_draft_from_path_geometry(
            path_summary,
            workspace_id=workspace_id,
        )
        if stale_snapshot.layers and layer_keys_from_path_geometry_summary(path_summary) & layer_keys_from_confirmation_snapshot(
            stale_snapshot
        ):
            snapshot = merge_preserved_roles_into_draft(snapshot, stale_snapshot)
        persisted = False
    elif snapshot is None:
        snapshot = build_layer_role_confirmation_draft_from_path_geometry(
            path_summary,
            workspace_id=workspace_id,
        )
    return build_layer_role_confirmation_response(context, snapshot=snapshot, persisted=persisted)


async def save_layer_role_confirmation_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3LayerRoleConfirmationUpdateRequest,
    current_user_id: str | None,
) -> IntakeV3LayerRoleConfirmationResponse:
    from services.intake_v3_geometry_metrics_snapshot_service import (
        build_and_attach_geometry_snapshot_for_workspace_payload,
    )
    from services.intake_v3_workspace_service import (
        _derive_readiness_status,
        _derive_workspace_status,
        _get_record_or_404,
        _json_dumps,
        _json_loads,
        _utcnow,
        sanitize_intake_v3_workspace_payload,
    )

    record = await _get_record_or_404(db, workspace_id)
    if record.archived_at is not None:
        raise HTTPException(
            status_code=400,
            detail={"error": "workspace_archived", "workspace_id": workspace_id},
        )

    payload = _json_loads(record.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}

    workspace = sanitize_intake_v3_workspace_payload(payload)
    path_summary = extract_path_geometry_summary_from_workspace(workspace)
    updates, _ = validate_layer_role_confirmation_update(path_summary, request)

    draft = extract_layer_role_confirmation_snapshot(
        Iv3SourceContext(
            source_type="workspace",
            source_id=workspace_id,
            is_intake_v3=True,
            order=None,
            quote=None,
            quote_linkage=None,
            order_linkage=None,
            sections={},
            linkage_sections={},
            workspace=workspace,
            product_template=workspace.product_selection.template_code or PILOT_TEMPLATE_CODE,
        )
    )
    if draft is None:
        draft = build_layer_role_confirmation_draft_from_path_geometry(path_summary, workspace_id=workspace_id)

    snapshot = apply_layer_role_updates_to_snapshot(
        draft,
        updates,
        confirmed_by=current_user_id,
    )
    payload = merge_layer_role_confirmation_into_workspace_payload(payload, snapshot)
    payload, _ = build_and_attach_geometry_snapshot_for_workspace_payload(payload, workspace_id=workspace_id)

    workspace = sanitize_intake_v3_workspace_payload(payload)
    record.payload_json = _json_dumps(workspace.model_dump(mode="json"))
    record.readiness_status = _derive_readiness_status(workspace)
    record.status = _derive_workspace_status(workspace, record.readiness_status)
    record.updated_by_user_id = current_user_id
    record.updated_at = _utcnow()
    await db.commit()
    await db.refresh(record)

    context = await load_iv3_source_context(db, workspace_id=workspace_id)
    return build_layer_role_confirmation_response(
        context,
        snapshot=snapshot,
        persisted=True,
    )


async def get_layer_role_confirmation_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3LayerRoleConfirmationResponse:
    context = await load_iv3_source_context(db, quote_id=quote_id)
    return build_layer_role_confirmation_response(context)


async def get_layer_role_confirmation_for_order(
    db: AsyncSession,
    order_id: int,
) -> IntakeV3LayerRoleConfirmationResponse:
    context = await load_iv3_source_context(db, order_id=order_id)
    return build_layer_role_confirmation_response(context)
