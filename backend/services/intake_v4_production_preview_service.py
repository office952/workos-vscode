"""Intake V4 production task preview — V3 operation catalog (Sprint 1)."""

from __future__ import annotations

from typing import Any

from schemas.intake_v4 import IntakeV4TaskPreviewItem, IntakeV4TaskPreviewResponse, IntakeV4WorkspacePayload
from services.intake_v4_finish_adapter import (
    build_v3_workspace_from_v4_payload,
    derive_operation_flags_from_v4_finish,
    finish_assignment_from_v4_setup,
    merge_finish_setup_override,
)
from services.intake_v4_operator_task_labels import operator_task_label_for_seed
from services.intake_v3_production_handoff_adapter import build_task_seed_candidates

_CATALOG_OPERATION_ORDER = {
    "graphic_vector_preflight": 1,
    "confirmed_production_model": 2,
    "cnc_file_preparation": 3,
    "return_forming_file_preparation": 4,
    "return_vinyl_application_workbench": 5,
    "face_and_backing_cnc_cut": 6,
    "return_side_forming": 7,
    "return_face_bonding": 8,
    "led_installation_wiring_and_light_test": 9,
    "letter_assembly_no_shared_support": 10,
    "return_painting_after_assembly": 11,
    "face_vinyl_application_final": 12,
    "stretch_wrap_and_delivery_mounting_package": 13,
}

_LED_SEED_CODES = frozenset({"led_installation_wiring_and_light_test"})


def _sequence_for_seed(seed_code: str, index: int) -> int:
    return _CATALOG_OPERATION_ORDER.get(seed_code, 100 + index)


def _apply_v4_lighting_gates(seeds: list, illuminated: bool) -> None:
    if illuminated:
        return
    for seed in seeds:
        if seed.seed_code in _LED_SEED_CODES:
            seed.active = False
            seed.active_reason = "non_illuminated"


def _seed_to_preview_item(seed, index: int) -> IntakeV4TaskPreviewItem:
    return IntakeV4TaskPreviewItem(
        operation_code=seed.seed_code,
        label=operator_task_label_for_seed(seed.seed_code, seed.display_name),
        workcenter=seed.required_station,
        sequence=_sequence_for_seed(seed.seed_code, index),
        component_ref=None,
        active=seed.active,
        inactive_reason=None if seed.active else seed.active_reason,
        source="operation_catalog",
        depends_on=list(seed.depends_on),
        required_skill=list(seed.required_skill),
        active_reason=seed.active_reason if seed.active else seed.active_reason,
        operator_instruction=seed.operator_instruction,
    )


def build_v4_task_preview_response(
    *,
    workspace_id: str,
    template_code: str,
    payload: IntakeV4WorkspacePayload,
    finish_override: dict[str, Any] | None = None,
) -> IntakeV4TaskPreviewResponse:
    """Task preview via V3 operation catalog + per-layer finish flags."""
    merged_setup = merge_finish_setup_override(payload.finish_setup, finish_override)
    payload_for_handoff = payload.model_copy(update={"finish_setup": merged_setup})

    v3_workspace = build_v3_workspace_from_v4_payload(payload_for_handoff)
    finish = finish_assignment_from_v4_setup(merged_setup)
    illuminated = merged_setup.illuminated is not False if merged_setup else True

    flags = derive_operation_flags_from_v4_finish(
        finish,
        illuminated=illuminated,
        shared_support=False,
    )
    seeds = build_task_seed_candidates(v3_workspace, flags)
    _apply_v4_lighting_gates(seeds, illuminated)

    items = [_seed_to_preview_item(seed, idx) for idx, seed in enumerate(seeds)]
    items.sort(key=lambda item: (item.sequence, item.operation_code))

    return IntakeV4TaskPreviewResponse(
        workspace_id=workspace_id,
        template_code=template_code,
        items=items,
        preview_only=True,
        operation_flags=flags.model_dump(mode="json"),
        preview_engine="v3_operation_catalog",
    )
