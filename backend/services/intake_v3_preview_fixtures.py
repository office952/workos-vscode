"""Intake V3 read-only preview scenario fixtures — in-memory workspaces, no DB writes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from schemas.intake_v3 import (
    ConfirmedProductionModel,
    CutContourItem,
    CutContourModel,
    FaceFinishSpec,
    FinishAssignment,
    IntakeV3Workspace,
    LetterItem,
    LetterModel,
    MaterialIntent,
    PowerSupplyIntent,
    ReturnFinishSpec,
)

INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL: Final[str] = "hub_wrapped_face_vinyl"
INTAKE_V3_PREVIEW_SCENARIO_HUB_PAINTED_FACE_VINYL: Final[str] = "hub_painted_face_vinyl"
INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH: Final[str] = "hub_missing_face_roll_width"

SUPPORTED_INTAKE_V3_PREVIEW_SCENARIOS: Final[tuple[str, ...]] = (
    INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL,
    INTAKE_V3_PREVIEW_SCENARIO_HUB_PAINTED_FACE_VINYL,
    INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH,
)


def list_intake_v3_preview_scenarios() -> list[str]:
    return list(SUPPORTED_INTAKE_V3_PREVIEW_SCENARIOS)


def build_intake_v3_preview_workspace_for_scenario(scenario: str) -> IntakeV3Workspace:
    if scenario == INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL:
        return build_hub_wrapped_face_vinyl_workspace()
    if scenario == INTAKE_V3_PREVIEW_SCENARIO_HUB_PAINTED_FACE_VINYL:
        return build_hub_painted_face_vinyl_workspace()
    if scenario == INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH:
        return build_hub_missing_face_roll_width_workspace()
    raise ValueError(
        f"Unknown Intake V3 preview scenario: {scenario!r}. "
        f"Supported: {', '.join(SUPPORTED_INTAKE_V3_PREVIEW_SCENARIOS)}"
    )


def _hub_confirmed_model() -> ConfirmedProductionModel:
    letters = [
        LetterItem(letter_id=f"L-{i:02d}", label="A", outer_contour_ids=[f"C-{i:02d}"])
        for i in range(1, 19)
    ]
    contours = [
        CutContourItem(contour_id=f"C-{i:02d}", role="outer", parent_letter_id=f"L-{i:02d}")
        for i in range(1, 19)
    ]
    contours.extend(
        CutContourItem(
            contour_id=f"H-{i:02d}",
            role="inner_hole",
            parent_letter_id=f"L-{i:02d}",
        )
        for i in range(1, 10)
    )
    return ConfirmedProductionModel(
        confirmed_by_user_id="op-preview",
        confirmed_at=datetime.now(timezone.utc),
        letter_count=18,
        cut_contour_count=27,
        inner_hole_count=9,
        letter_model=LetterModel(letters=letters, count_confirmed=True),
        cut_contour_model=CutContourModel(
            contours=contours,
            outer_contour_count=18,
            inner_hole_count=9,
            cut_contour_count=27,
        ),
        confirmation_status="confirmed",
    )


def _hub_material_intent() -> MaterialIntent:
    return MaterialIntent(
        roll_materials=[],
        sheet_materials=[],
        led_materials=[],
        power_supplies=[
            PowerSupplyIntent(
                wattage=100,
                quantity=2,
                delivery_mode="pack_with_job",
                packaging_required=True,
                mounted_on_shared_support=False,
                source_rule="no_shared_support_psu_at_packaging",
            )
        ],
        accessories=[],
        estimate_status="complete",
        inventory_mutation_allowed=False,
    )


def _base_finish(**overrides) -> FinishAssignment:
    payload = {
        "assignment_mode": "all",
        "confirmed_by_operator": True,
        "face_finish": FaceFinishSpec(
            finish_type="oracal_8500",
            material_code="Oracal 8500",
            color_code="527",
            color_name="Pastel blue",
            face_vinyl_roll_width_mm=1260,
            confirmed=True,
        ),
        "return_finish": ReturnFinishSpec(
            finish_type="oracal_wrapped",
            material_code="Oracal 651",
            color_code="055m",
            color_name="Int",
            return_depth_mm=60,
            confirmed=True,
        ),
        "backing_finish": {"material": "Forex", "thickness_mm": 10, "confirmed": True},
    }
    payload.update(overrides)
    return FinishAssignment.model_validate(payload)


def _hub_workspace(finish: FinishAssignment) -> IntakeV3Workspace:
    return IntakeV3Workspace.model_validate(
        {
            "client_request": {
                "client_name": "HUB MEDIA PRODUCTION",
                "request_code": "INK-2026-0847",
                "job_title": "Litere volumetrice luminoase",
                "width_mm": 9250,
                "height_mm": 550,
                "depth_mm": 80,
            },
            "product_selection": {
                "template_code": "TPL-VOLUMETRIC-LETTERS",
                "product_family": "volumetric_letters",
                "pilot_scope": True,
            },
            "vector_asset": {
                "file_name": "hub-media-production.svg",
                "upload_status": "parsed",
                "declared_width_mm": 9250,
                "declared_height_mm": 550,
            },
            "raw_svg_analysis": {
                "path_count": 42,
                "closed_contour_count": 30,
                "detected_color_count": 3,
                "confidence": 0.82,
            },
            "confirmed_production_model": _hub_confirmed_model().model_dump(mode="json"),
            "finish_assignment": finish.model_dump(mode="json"),
            "material_intent": _hub_material_intent().model_dump(mode="json"),
            "production_handoff": {
                "preview_only": True,
                "task_seed": [],
                "materials_summary": [],
                "source_rules": [],
            },
            "employee_preview_seed": {
                "non_executable": True,
                "preview_tasks": [],
            },
        }
    )


def build_hub_wrapped_face_vinyl_workspace() -> IntakeV3Workspace:
    """HUB no_shared_support, Oracal wrapped return, Oracal 8500 face vinyl, PSU in packaging."""
    return _hub_workspace(_base_finish())


def build_hub_painted_face_vinyl_workspace() -> IntakeV3Workspace:
    """HUB painted return after assembly; face vinyl after painting; PSU in packaging."""
    finish = _base_finish(
        return_finish=ReturnFinishSpec(
            finish_type="painted",
            material_code="RAL 9005",
            color_code="9005",
            color_name="Jet black",
            return_depth_mm=60,
            confirmed=True,
        ),
    )
    return _hub_workspace(finish)


def build_hub_missing_face_roll_width_workspace() -> IntakeV3Workspace:
    """Face vinyl enabled but roll width missing — readiness/pricing blockers, preview still builds."""
    finish = _base_finish(
        face_finish=FaceFinishSpec(
            finish_type="oracal_8500",
            material_code="Oracal 8500",
            color_code="527",
            color_name="Pastel blue",
            face_vinyl_roll_width_mm=None,
            confirmed=True,
        ),
    )
    return _hub_workspace(finish)
