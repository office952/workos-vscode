from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.product_definition_builder_service import ProductDefinitionBuilderService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = "TPL-VOLUMETRIC-LOGO_v1"


@pytest_asyncio.fixture
async def pd_builder(volumetric_v2_db):
    yield ProductDefinitionBuilderService(volumetric_v2_db)


def _gradi_payload() -> dict:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "gradi-curat.svg", "file_size_bytes": 27173},
        "client": {"width_mm": 5087, "height_mm": 600},
        "quote_geometry": {
            "letter_count": 19,
            "letter_perimeter_m": 31.638,
            "letter_face_area_m2": 3.05,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "pseudo:maria",
                    "layer_id": "pseudo:maria",
                    "layer_name": "pseudo maria (blue)",
                    "auto_role": "face",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "pseudo:soare",
                    "layer_id": "pseudo:soare",
                    "layer_name": "pseudo soare (red)",
                    "auto_role": "face",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "pseudo:ana",
                    "layer_id": "pseudo:ana",
                    "layer_name": "pseudo ana (green)",
                    "auto_role": "face",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "pseudo:gradinita",
                    "layer_id": "pseudo:gradinita",
                    "layer_name": "pseudo gradinita (orange)",
                    "auto_role": "face",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "logo-stanga",
                    "layer_id": "logo-stanga",
                    "layer_name": "logo stanga",
                    "auto_role": "printed_artwork",
                    "confirmed_role": "printed_artwork",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_id": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "auto_role": "printed_artwork",
                    "confirmed_role": "printed_artwork",
                    "confirmation_state": "confirmed",
                },
            ],
            "layer_bindings": [
                {
                    "layer_key": "logo-stanga",
                    "source_layer_name": "logo stanga",
                    "suggested_semantic_role": "printed_artwork",
                    "confirmed_semantic_role": "printed_artwork",
                    "target_template_code": LOGO,
                    "target_module_code": "logo_finish",
                    "binding_status": "suggested",
                    "binding_reason": "additional_template_suggestion_requires_binding_confirmation",
                },
                {
                    "layer_key": "logo-dreapta",
                    "source_layer_name": "logo dreapta",
                    "suggested_semantic_role": "printed_artwork",
                    "confirmed_semantic_role": "printed_artwork",
                    "target_template_code": LOGO,
                    "target_module_code": "logo_finish",
                    "binding_status": "suggested",
                    "binding_reason": "additional_template_suggestion_requires_binding_confirmation",
                },
            ],
        },
        "finish_setup": {
            "face_finish_type": "oracal_651",
            "return_depth_mm": 60,
            "return_finish_type": "white_aluminum",
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "closed_back",
            "mounting_system": "direct_wall",
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "artwork_finishes": [
                {
                    "layer_key": "logo-stanga",
                    "layer_name": "logo stanga",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "print_transparency": "translucent",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                    "confirmed": True,
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "print_transparency": "translucent",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                    "confirmed": True,
                },
            ],
        },
    }


@pytest.mark.asyncio
async def test_gradi_curat_builds_single_root_preview_with_linked_logo_candidate(
    pd_builder: ProductDefinitionBuilderService,
    volumetric_v2_db,
):
    workspace_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-GRADI-{workspace_id[:8]}",
            title="Gradi composition workspace",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(_gradi_payload()),
        )
    )
    await volumetric_v2_db.commit()

    preview = await pd_builder.build_preview(ROOT, workspace_id=workspace_id)

    assert preview is not None
    assert preview.template_code == ROOT
    assert preview.linked_template_runtime_segments is not None

    linked = preview.linked_template_runtime_segments
    assert linked["root_template_code"] == ROOT
    assert linked["composition_mode"] == "root_with_linked_segments"
    assert linked["summary"]["root_offerable_activation"] is False
    assert linked["summary"]["separate_quote_activation"] is False
    assert linked["summary"]["task_graph_activation"] is False
    assert linked["summary"]["segments_count"] == 2

    segments = linked["segments"]
    assert {segment["segment_key"] for segment in segments} == {"logo-stanga", "logo-dreapta"}
    assert all(segment["parent_root_template_code"] == ROOT for segment in segments)
    assert all(segment["owning_template_code"] == LOGO for segment in segments)
    assert all(segment["composition_role"] == "linked_logo_segment" for segment in segments)
    assert all(segment["binding_status"] == "suggested" for segment in segments)
    assert all(segment["product_truth_readiness"]["ready_for_pricing"] is False for segment in segments)
    assert all(segment["product_truth_readiness"]["ready_for_quote"] is False for segment in segments)
    assert all(segment["product_truth_readiness"]["ready_for_order"] is False for segment in segments)
    assert all(segment["product_truth_readiness"]["ready_for_execution"] is False for segment in segments)

    dumped = preview.model_dump()
    assert "cost_result" not in dumped
    assert "price" not in dumped
    assert "grand_total" not in dumped
    assert dumped["source_context"]["template_code"] == ROOT