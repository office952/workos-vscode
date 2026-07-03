"""Intake V3 layer role confirmation propagation — workspace vs quote snapshot freshness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.orders import Orders
from models.quotes import Quotes
from schemas.intake_v3 import (
    IntakeV3LayerRoleConfirmationPropagationResponse,
    IntakeV3LayerRoleConfirmationSnapshot,
    IntakeV3LayerRolePropagationBoundary,
    IntakeV3LayerRolePropagationCounts,
    IntakeV3LayerRolePropagationWarning,
    IntakeV3LayerRoleSnapshotChangedLayer,
    IntakeV3LayerRoleTechnicalSnapshotRefreshResponse,
    IntakeV3Workspace,
)
from services.intake_v3_material_quantity_breakdown_service import (
    Iv3SourceContext,
    load_iv3_source_context,
)
from services.intake_v3_guarded_convert_to_order_service import check_existing_order_for_iv3_quote
from services.intake_v3_quote_linkage_utils import (
    is_iv3_accept_completed,
    is_iv3_convert_completed,
)
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_JSON_KEY,
    INTAKE_V3_SOURCE_MODULE,
    parse_intake_v3_linkage_from_notes,
)
from services.quotes import QuotesService

EFFECTIVE_SOURCE_WORKSPACE_LIVE = "workspace_live"
EFFECTIVE_SOURCE_QUOTE_SNAPSHOT = "quote_linkage_snapshot"
EFFECTIVE_SOURCE_WORKSPACE_ONLY = "workspace_payload"
SNAPSHOT_SOURCE_QUOTE_LINKAGE = "quote_linkage_snapshot"
SNAPSHOT_SOURCE_MISSING = "missing"

STALE_REASON_NEWER = "workspace_confirmation_newer_than_quote_snapshot"
STALE_REASON_CHANGED = "layer_roles_changed"
STALE_REASON_MISSING_QUOTE = "quote_snapshot_missing"

REFRESH_BLOCKED_ACCEPTED = "accepted_quote_refresh_blocked"
REFRESH_BLOCKED_CONVERTED = "converted_quote_refresh_blocked"
REFRESH_BLOCKED_STATUS = "quote_status_refresh_blocked"


@dataclass
class LayerRolePropagationMeta:
    effective_source: str
    snapshot_source: str
    layer_role_confirmation_status: str
    effective_confirmed_at: str | None
    snapshot_confirmed_at: str | None
    is_snapshot_stale: bool
    stale_reason: str | None
    can_refresh_quote_snapshot: bool
    refresh_blocked_reason: str | None
    refresh_required_for_downstream_read: bool
    downstream_uses_effective_source: bool
    counts: IntakeV3LayerRolePropagationCounts
    changed_layers: list[IntakeV3LayerRoleSnapshotChangedLayer]
    warnings: list[IntakeV3LayerRolePropagationWarning]


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (TypeError, ValueError):
        return None


def _parse_snapshot(raw: Any) -> IntakeV3LayerRoleConfirmationSnapshot | None:
    if not isinstance(raw, dict):
        return None
    try:
        return IntakeV3LayerRoleConfirmationSnapshot.model_validate(raw)
    except Exception:
        return None


def _effective_role_for_layer(layer: dict[str, Any]) -> str:
    confirmed = layer.get("confirmed_role")
    if confirmed:
        return str(confirmed)
    auto = layer.get("auto_role")
    if auto:
        return str(auto)
    return "unknown"


def _role_map(snapshot: IntakeV3LayerRoleConfirmationSnapshot | None) -> dict[str, str]:
    if snapshot is None:
        return {}
    result: dict[str, str] = {}
    for layer in snapshot.layers:
        if layer.confirmation_state == "ignored" or layer.confirmed_role == "ignore":
            result[layer.layer_key] = "ignore"
        elif layer.confirmation_state == "confirmed" and layer.confirmed_role:
            result[layer.layer_key] = layer.confirmed_role
        elif layer.auto_role:
            result[layer.layer_key] = layer.auto_role
        else:
            result[layer.layer_key] = "unknown"
    return result


def _confirmed_layer_count(snapshot: IntakeV3LayerRoleConfirmationSnapshot | None) -> int:
    if snapshot is None:
        return 0
    return sum(
        1
        for layer in snapshot.layers
        if layer.confirmation_state == "confirmed" and layer.confirmed_role not in {None, "unknown", "ignore"}
    )


def compare_confirmation_snapshots(
    workspace_snapshot: IntakeV3LayerRoleConfirmationSnapshot | None,
    quote_snapshot: IntakeV3LayerRoleConfirmationSnapshot | None,
) -> tuple[list[IntakeV3LayerRoleSnapshotChangedLayer], bool, str | None]:
    if quote_snapshot is None and workspace_snapshot is None:
        return [], False, None
    if quote_snapshot is None and workspace_snapshot is not None:
        return [], True, STALE_REASON_MISSING_QUOTE

    workspace_roles = _role_map(workspace_snapshot)
    quote_roles = _role_map(quote_snapshot)
    keys = sorted(set(workspace_roles) | set(quote_roles))
    changed: list[IntakeV3LayerRoleSnapshotChangedLayer] = []
    for key in keys:
        ws_role = workspace_roles.get(key)
        quote_role = quote_roles.get(key)
        if ws_role == quote_role:
            continue
        change_type = "role_changed"
        if quote_role is None:
            change_type = "layer_added"
        elif ws_role is None:
            change_type = "layer_removed"
        changed.append(
            IntakeV3LayerRoleSnapshotChangedLayer(
                layer_key=key,
                snapshot_role=quote_role,
                effective_role=ws_role,
                change_type=change_type,
            )
        )

    ws_at = _parse_iso(workspace_snapshot.confirmed_at if workspace_snapshot else None)
    quote_at = _parse_iso(quote_snapshot.confirmed_at if quote_snapshot else None)
    if changed:
        return changed, True, STALE_REASON_CHANGED
    if ws_at and quote_at and ws_at > quote_at:
        return changed, True, STALE_REASON_NEWER
    if ws_at and quote_at is None and workspace_snapshot is not None:
        return changed, True, STALE_REASON_NEWER
    return changed, False, None


def _load_notes_payload(notes: str | None) -> dict[str, Any]:
    if not notes:
        return {}
    try:
        payload = json.loads(notes)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def can_refresh_quote_technical_snapshot(
    quote: Quotes | None,
    linkage: dict[str, Any] | None,
    *,
    order: Any | None = None,
) -> tuple[bool, str | None]:
    if quote is None or linkage is None:
        return False, "quote_linkage_missing"
    if is_iv3_accept_completed(linkage, quote.status):
        return False, REFRESH_BLOCKED_ACCEPTED
    if is_iv3_convert_completed(linkage) or order is not None:
        return False, REFRESH_BLOCKED_CONVERTED
    if quote.status not in ("draft", "priced"):
        return False, REFRESH_BLOCKED_STATUS
    return True, None


async def load_workspace_confirmation_snapshot(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3LayerRoleConfirmationSnapshot | None:
    from services.intake_v3_workspace_service import get_intake_v3_workspace, sanitize_intake_v3_workspace_payload

    record = await get_intake_v3_workspace(db, workspace_id)
    workspace = sanitize_intake_v3_workspace_payload(record.payload)
    return _parse_snapshot(workspace.layer_role_confirmation_snapshot)


def load_quote_confirmation_snapshot_from_sections(
    sections: dict[str, Any],
) -> IntakeV3LayerRoleConfirmationSnapshot | None:
    return _parse_snapshot(sections.get("layer_role_confirmation_snapshot"))


def resolve_effective_layer_role_snapshot(
    workspace_snapshot: IntakeV3LayerRoleConfirmationSnapshot | None,
    quote_snapshot: IntakeV3LayerRoleConfirmationSnapshot | None,
    *,
    workspace_id: str | None,
) -> tuple[IntakeV3LayerRoleConfirmationSnapshot | None, str]:
    if workspace_snapshot is not None and workspace_id:
        return workspace_snapshot, EFFECTIVE_SOURCE_WORKSPACE_LIVE
    if quote_snapshot is not None:
        return quote_snapshot, EFFECTIVE_SOURCE_QUOTE_SNAPSHOT
    if workspace_snapshot is not None:
        return workspace_snapshot, EFFECTIVE_SOURCE_WORKSPACE_ONLY
    return None, "missing"


def build_layer_role_propagation_meta(
    *,
    workspace_snapshot: IntakeV3LayerRoleConfirmationSnapshot | None,
    quote_snapshot: IntakeV3LayerRoleConfirmationSnapshot | None,
    workspace_id: str | None,
    quote: Quotes | None = None,
    linkage: dict[str, Any] | None = None,
    order: Orders | None = None,
) -> LayerRolePropagationMeta:
    effective, effective_source = resolve_effective_layer_role_snapshot(
        workspace_snapshot,
        quote_snapshot,
        workspace_id=workspace_id,
    )
    snapshot_source = SNAPSHOT_SOURCE_QUOTE_LINKAGE if quote_snapshot is not None else SNAPSHOT_SOURCE_MISSING
    changed_layers, is_stale, stale_reason = compare_confirmation_snapshots(
        workspace_snapshot,
        quote_snapshot,
    )
    can_refresh, refresh_blocked = can_refresh_quote_technical_snapshot(quote, linkage, order=order)

    warnings: list[IntakeV3LayerRolePropagationWarning] = []
    if is_stale:
        warnings.append(
            IntakeV3LayerRolePropagationWarning(
                code="quote_snapshot_stale",
                severity="warning",
                message="Quote linkage layer role confirmation snapshot is older than workspace confirmation.",
                source="layer_role_confirmation_propagation",
            )
        )
        if stale_reason == STALE_REASON_NEWER:
            warnings.append(
                IntakeV3LayerRolePropagationWarning(
                    code="operator_confirmation_newer_than_quote_snapshot",
                    severity="warning",
                    message="Operator confirmation in workspace is newer than the quote snapshot.",
                    source="layer_role_confirmation_propagation",
                )
            )

    unknown_count = len(effective.unknown_layers) if effective else 0
    ignored_count = len(effective.ignored_layers) if effective else 0

    return LayerRolePropagationMeta(
        effective_source=effective_source,
        snapshot_source=snapshot_source,
        layer_role_confirmation_status=(effective.confirmation_status if effective else "missing"),
        effective_confirmed_at=effective.confirmed_at if effective else None,
        snapshot_confirmed_at=quote_snapshot.confirmed_at if quote_snapshot else None,
        is_snapshot_stale=is_stale,
        stale_reason=stale_reason,
        can_refresh_quote_snapshot=can_refresh and is_stale,
        refresh_blocked_reason=refresh_blocked if not can_refresh else None,
        refresh_required_for_downstream_read=False,
        downstream_uses_effective_source=True,
        counts=IntakeV3LayerRolePropagationCounts(
            effective_confirmed_layers=_confirmed_layer_count(effective),
            snapshot_confirmed_layers=_confirmed_layer_count(quote_snapshot),
            changed_layers=len(changed_layers),
            unknown_layers=unknown_count,
            ignored_layers=ignored_count,
        ),
        changed_layers=changed_layers,
        warnings=warnings,
    )


def evaluate_layer_role_propagation(context: Iv3SourceContext) -> LayerRolePropagationMeta:
    workspace_id = None
    if context.quote_linkage:
        workspace_id = context.quote_linkage.get("source_workspace_id")
    if context.order_linkage and not workspace_id:
        workspace_id = context.order_linkage.get("source_workspace_id")
    if context.source_type == "workspace":
        workspace_id = context.source_id

    workspace_snapshot = _parse_snapshot(
        context.workspace.layer_role_confirmation_snapshot if context.workspace else None
    )
    quote_snapshot = load_quote_confirmation_snapshot_from_sections(context.linkage_sections)
    return build_layer_role_propagation_meta(
        workspace_snapshot=workspace_snapshot,
        quote_snapshot=quote_snapshot,
        workspace_id=str(workspace_id) if workspace_id else None,
        quote=context.quote,
        linkage=context.quote_linkage,
        order=context.order,
    )


def propagation_meta_to_response(
    context: Iv3SourceContext,
    meta: LayerRolePropagationMeta,
) -> IntakeV3LayerRoleConfirmationPropagationResponse:
    workspace_id = None
    if context.quote_linkage:
        workspace_id = context.quote_linkage.get("source_workspace_id")
    if context.order_linkage and not workspace_id:
        workspace_id = context.order_linkage.get("source_workspace_id")
    if context.source_type == "workspace":
        workspace_id = context.source_id

    return IntakeV3LayerRoleConfirmationPropagationResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        workspace_id=str(workspace_id) if workspace_id else None,
        quote_id=context.quote.id if context.quote else None,
        order_id=context.order.id if context.order else None,
        is_intake_v3=context.is_intake_v3,
        effective_source=meta.effective_source,
        snapshot_source=meta.snapshot_source,
        layer_role_confirmation_status=meta.layer_role_confirmation_status,
        effective_confirmed_at=meta.effective_confirmed_at,
        snapshot_confirmed_at=meta.snapshot_confirmed_at,
        is_snapshot_stale=meta.is_snapshot_stale,
        stale_reason=meta.stale_reason,
        can_refresh_quote_snapshot=meta.can_refresh_quote_snapshot,
        refresh_blocked_reason=meta.refresh_blocked_reason,
        refresh_required_for_downstream_read=meta.refresh_required_for_downstream_read,
        downstream_uses_effective_source=meta.downstream_uses_effective_source,
        counts=meta.counts,
        changed_layers=meta.changed_layers,
        warnings=meta.warnings,
        boundary=IntakeV3LayerRolePropagationBoundary(),
    )


def stale_propagation_warnings(meta: LayerRolePropagationMeta) -> list[tuple[str, str]]:
    """Return (code, message) pairs for downstream warning lists."""
    result: list[tuple[str, str]] = []
    for warning in meta.warnings:
        result.append((warning.code, warning.message))
    if meta.is_snapshot_stale:
        result.append(
            (
                "quote_layer_role_snapshot_stale",
                "Quote linkage layer role snapshot is stale relative to workspace confirmation.",
            )
        )
    return result


def build_non_iv3_propagation_response(context: Iv3SourceContext) -> IntakeV3LayerRoleConfirmationPropagationResponse:
    return IntakeV3LayerRoleConfirmationPropagationResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        order_id=context.order.id if context.order else None,
        quote_id=context.quote.id if context.quote else None,
        is_intake_v3=False,
        effective_source="missing",
        snapshot_source=SNAPSHOT_SOURCE_MISSING,
        layer_role_confirmation_status="missing",
        downstream_uses_effective_source=False,
        warnings=[
            IntakeV3LayerRolePropagationWarning(
                code="not_intake_v3_source",
                severity="info",
                message="Source is not an Intake V3 order/quote/workspace payload.",
                source="source_detection",
            )
        ],
        boundary=IntakeV3LayerRolePropagationBoundary(),
    )


def downstream_propagation_fields(
    context: Iv3SourceContext,
) -> tuple[dict[str, Any], LayerRolePropagationMeta | None, list[tuple[str, str]]]:
    if not context.is_intake_v3 and context.source_type != "workspace":
        return {}, None, []
    meta = evaluate_layer_role_propagation(context)
    fields = {
        "layer_role_confirmation_effective_source": meta.effective_source,
        "layer_role_confirmation_snapshot_source": meta.snapshot_source,
        "layer_role_confirmation_snapshot_stale": meta.is_snapshot_stale,
        "layer_role_confirmation_stale_reason": meta.stale_reason,
        "downstream_uses_effective_source": meta.downstream_uses_effective_source,
    }
    return fields, meta, stale_propagation_warnings(meta)


async def get_layer_role_confirmation_propagation_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3LayerRoleConfirmationPropagationResponse:
    context = await load_iv3_source_context(db, workspace_id=workspace_id)
    if context.workspace is None:
        raise HTTPException(status_code=404, detail={"error": "workspace_not_found", "workspace_id": workspace_id})
    meta = evaluate_layer_role_propagation(context)
    return propagation_meta_to_response(context, meta)


async def get_layer_role_confirmation_propagation_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3LayerRoleConfirmationPropagationResponse:
    context = await load_iv3_source_context(db, quote_id=quote_id)
    if not context.is_intake_v3:
        return build_non_iv3_propagation_response(context)
    meta = evaluate_layer_role_propagation(context)
    return propagation_meta_to_response(context, meta)


async def get_layer_role_confirmation_propagation_for_order(
    db: AsyncSession,
    order_id: int,
) -> IntakeV3LayerRoleConfirmationPropagationResponse:
    context = await load_iv3_source_context(db, order_id=order_id)
    if not context.is_intake_v3:
        return build_non_iv3_propagation_response(context)
    meta = evaluate_layer_role_propagation(context)
    return propagation_meta_to_response(context, meta)


def _update_linkage_technical_sections(
    linkage: dict[str, Any],
    workspace: IntakeV3Workspace,
) -> dict[str, Any]:
    updated = dict(linkage)
    snapshot = updated.get("snapshot")
    if not isinstance(snapshot, dict):
        raise HTTPException(
            status_code=422,
            detail={"error": "SNAPSHOT_MISSING", "message": "Quote linkage snapshot is missing."},
        )
    snapshot = dict(snapshot)
    sections = snapshot.get("sections")
    if not isinstance(sections, dict):
        sections = {}
    sections = dict(sections)
    if workspace.layer_role_confirmation_snapshot:
        sections["layer_role_confirmation_snapshot"] = workspace.layer_role_confirmation_snapshot
    if workspace.geometry_metrics_snapshot:
        sections["geometry_metrics_snapshot"] = workspace.geometry_metrics_snapshot
    snapshot["sections"] = sections
    updated["snapshot"] = snapshot
    return updated


async def refresh_quote_iv3_technical_snapshots_from_workspace(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3LayerRoleTechnicalSnapshotRefreshResponse:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail={"error": "quote_not_found", "quote_id": quote_id})

    linkage = parse_intake_v3_linkage_from_notes(quote.notes)
    if linkage is None:
        raise HTTPException(status_code=422, detail={"error": "not_intake_v3_quote"})

    order = await check_existing_order_for_iv3_quote(db, quote_id)
    can_refresh, blocked = can_refresh_quote_technical_snapshot(quote, linkage, order=order)
    if not can_refresh:
        raise HTTPException(
            status_code=422,
            detail={
                "error": blocked or "refresh_blocked",
                "message": "Quote technical snapshot refresh is not allowed for this quote state.",
            },
        )

    workspace_id = linkage.get("source_workspace_id")
    if not workspace_id:
        raise HTTPException(status_code=422, detail={"error": "workspace_id_missing"})

    from services.intake_v3_workspace_service import get_intake_v3_workspace, sanitize_intake_v3_workspace_payload

    record = await get_intake_v3_workspace(db, str(workspace_id))
    workspace = sanitize_intake_v3_workspace_payload(record.payload)
    if not workspace.layer_role_confirmation_snapshot:
        raise HTTPException(
            status_code=422,
            detail={"error": "workspace_confirmation_missing", "message": "Workspace has no layer role confirmation."},
        )

    status_before = quote.status
    subtotal_before = float(quote.subtotal or 0)
    total_before = float(quote.grand_total or 0)

    payload = _load_notes_payload(quote.notes)
    payload[INTAKE_V3_LINKAGE_JSON_KEY] = _update_linkage_technical_sections(linkage, workspace)
    updated_notes = json.dumps(payload, default=str)

    updated_quote = await quotes_service.update(quote.id, {"notes": updated_notes})
    if updated_quote is None:
        raise HTTPException(status_code=500, detail={"error": "quote_update_failed"})

    assert updated_quote.status == status_before
    assert float(updated_quote.subtotal or 0) == subtotal_before
    assert float(updated_quote.grand_total or 0) == total_before

    context = await load_iv3_source_context(db, quote_id=quote_id)
    meta = evaluate_layer_role_propagation(context)

    return IntakeV3LayerRoleTechnicalSnapshotRefreshResponse(
        quote_id=quote_id,
        workspace_id=str(workspace_id),
        refresh_status="refreshed",
        is_snapshot_stale=meta.is_snapshot_stale,
        effective_source=meta.effective_source,
        snapshot_source=meta.snapshot_source,
        layer_role_confirmation_status=meta.layer_role_confirmation_status,
        warnings=meta.warnings,
        boundary=IntakeV3LayerRolePropagationBoundary(),
        modifies_quote_status=False,
        modifies_quote_pricing=False,
        modifies_order=False,
        creates_execution_plan=False,
        creates_execution_tasks=False,
        mutates_inventory=False,
        costengine_used=False,
    )
