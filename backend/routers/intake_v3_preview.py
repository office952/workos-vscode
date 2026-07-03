"""Intake V3 read-only preview HTTP surface — no quote/order/plan/inventory side effects."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from dependencies.auth import get_current_user
from schemas.intake_v3 import IntakeV3PreviewBuildResult
from services.intake_v3_preview_fixtures import (
    SUPPORTED_INTAKE_V3_PREVIEW_SCENARIOS,
    build_intake_v3_preview_workspace_for_scenario,
    list_intake_v3_preview_scenarios,
)
from services.intake_v3_workspace_preview_service import build_intake_v3_workspace_preview

# DEPRECATED: V3 preview endpoints superseded by V4. Router disabled from auto-discovery.
# V3 services are still imported by V4 as shared libraries — do not delete this file.
_deprecated_router = APIRouter(
    prefix="/api/v1/intake-v3",
    tags=["intake-v3-preview"],
    dependencies=[Depends(get_current_user)],
)


@_deprecated_router.get("/scenarios")
async def get_intake_v3_preview_scenarios() -> dict[str, list[str]]:
    """List supported read-only preview scenario identifiers."""
    return {"scenarios": list_intake_v3_preview_scenarios()}


@_deprecated_router.get("/preview", response_model=IntakeV3PreviewBuildResult)
async def get_intake_v3_preview(
    scenario: str = Query(
        ...,
        description="Preview scenario id",
        examples=["hub_wrapped_face_vinyl"],
    ),
) -> IntakeV3PreviewBuildResult:
    """Build in-memory Intake V3 workspace preview — read-only, no persistence."""
    if scenario not in SUPPORTED_INTAKE_V3_PREVIEW_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unknown_preview_scenario",
                "scenario": scenario,
                "supported_scenarios": list_intake_v3_preview_scenarios(),
            },
        )

    workspace = build_intake_v3_preview_workspace_for_scenario(scenario)
    return build_intake_v3_workspace_preview(workspace)
