"""Intake V6 material and nesting preview service namespace."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.intake_v6 import IntakeV6MaterialBreakdownResponse, IntakeV6NestingPreviewResponse
from services.intake_v4_material_breakdown_service import (
    build_intake_v4_material_breakdown_with_registry,
)
from services.intake_v6_response_normalization import normalize_intake_v6_model
from services.intake_v6_workspace_service import _get_record_or_404, _json_loads, _parse_payload


async def get_material_breakdown_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV6MaterialBreakdownResponse:
    from services.intake_v6_analysis_boundary_service import assert_v6_analysis_boundary_or_raise

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    payload = _parse_payload(payload_raw)
    assert_v6_analysis_boundary_or_raise(payload)
    breakdown = normalize_intake_v6_model(
        await build_intake_v4_material_breakdown_with_registry(db, workspace_id, payload_raw)
    )
    if breakdown.nesting_preview is None:
        return breakdown
    return breakdown.model_copy(
        update={"nesting_preview": breakdown.nesting_preview.model_copy(update={"source": "intake_v6_workspace"})}
    )


async def get_nesting_preview_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV6NestingPreviewResponse:
    breakdown = await get_material_breakdown_for_workspace(db, workspace_id)
    if breakdown.nesting_preview is not None:
        return breakdown.nesting_preview
    from schemas.intake_v6 import IntakeV6NestingPreviewBoundary, IntakeV6NestingPreviewResponse

    return IntakeV6NestingPreviewResponse(
        preview_only=True,
        mutates_inventory=False,
        uses_stock=False,
        source="intake_v6_workspace",
        workspace_id=workspace_id,
        disclaimer="Nesting preview unavailable for this workspace payload.",
        boundary=IntakeV6NestingPreviewBoundary(),
        warnings=[],
    )
