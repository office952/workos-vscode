"""Intake V4 analysis snapshot boundary — persist gate for downstream endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from schemas.intake_v4 import IntakeV4WorkspacePayload


def list_v4_analysis_boundary_blockers(payload: IntakeV4WorkspacePayload) -> list[str]:
    """Fail-closed checks before Review/Confirm downstream actions."""
    blockers: list[str] = []

    svg_source = payload.svg_source
    if svg_source is None or not (svg_source.file_hash or "").strip():
        blockers.append("missing_svg_source_hash")
    elif svg_source.upload_status != "analyzed":
        blockers.append("svg_not_analyzed")

    if not payload.svg_analysis_json:
        blockers.append("missing_svg_analysis_json")

    layer_setup = payload.layer_role_setup
    if layer_setup is None:
        blockers.append("missing_layer_role_setup")
    elif layer_setup.confirmation_status != "complete":
        blockers.append("layer_roles_incomplete")

    quote_geom = resolve_v4_quote_geometry_for_boundary(payload)
    if not quote_geom.get("letter_perimeter_m") and not quote_geom.get("total_letter_perimeter_ml"):
        blockers.append("missing_quote_geometry_perimeter")
    if quote_geom.get("letter_count") is None and quote_geom.get("face_area_m2") is None:
        blockers.append("missing_quote_geometry_metrics")

    return blockers


def resolve_v4_quote_geometry_for_boundary(payload: IntakeV4WorkspacePayload) -> dict[str, Any]:
    from services.intake_v4_quote_geometry_service import resolve_v4_quote_geometry

    return resolve_v4_quote_geometry(payload)


def assert_v4_analysis_boundary_or_raise(payload: IntakeV4WorkspacePayload) -> None:
    blockers = list_v4_analysis_boundary_blockers(payload)
    if not blockers:
        return
    raise HTTPException(
        status_code=422,
        detail={
            "error": "analysis_boundary_blocked",
            "message": "Analysis snapshot must be persisted and current before this action.",
            "blockers": blockers,
        },
    )


def assert_v4_finish_boundary_or_raise(payload: IntakeV4WorkspacePayload) -> None:
    assert_v4_analysis_boundary_or_raise(payload)
    setup = payload.finish_setup
    if setup is None or not setup.confirmed:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "finish_setup_not_confirmed",
                "message": "Finish setup must be confirmed before this action.",
                "blockers": ["finish_setup_not_confirmed"],
            },
        )


def list_v4_analysis_hash_sync_blockers(
    payload: IntakeV4WorkspacePayload,
    client_analysis_hash: str | None,
) -> list[str]:
    """Fail-closed when operator attestation hash does not match persisted svg_source.file_hash."""
    blockers: list[str] = []
    client = (client_analysis_hash or "").strip()
    if not client:
        blockers.append("missing_client_analysis_hash")
        return blockers

    svg_source = payload.svg_source
    persisted = (svg_source.file_hash or "").strip() if svg_source is not None else ""
    if not persisted:
        blockers.append("missing_svg_source_hash")
        return blockers

    if client.lower() != persisted.lower():
        blockers.append("analysis_hash_mismatch")
    return blockers


def assert_v4_analysis_hash_sync_or_raise(
    payload: IntakeV4WorkspacePayload,
    client_analysis_hash: str | None,
) -> None:
    blockers = list_v4_analysis_hash_sync_blockers(payload, client_analysis_hash)
    if not blockers:
        return
    raise HTTPException(
        status_code=422,
        detail={
            "error": "analysis_hash_sync_blocked",
            "message": "Client analysis hash does not match persisted workspace analysis identity.",
            "blockers": blockers,
        },
    )
