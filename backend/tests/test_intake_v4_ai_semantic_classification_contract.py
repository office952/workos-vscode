"""Intake V4 AI-assisted semantic classification — read-only contract tests."""

from __future__ import annotations

import json

import pytest

from schemas.intake_v4 import (
    IntakeV4ClientRequest,
    IntakeV4FinishSetup,
    IntakeV4LayerRoleSetup,
    IntakeV4ProductBinding,
    IntakeV4WorkspacePayload,
)
from services.intake_v4_ai_semantic_classification_service import (
    AI_SEMANTIC_CLASSIFICATION_SCHEMA_VERSION,
    build_intake_v4_ai_semantic_classification_preview,
    build_mock_ai_semantic_suggestion,
    build_ai_semantic_classification_candidate_payload,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.intake_v4_production_task_dry_run_service import build_v4_production_task_dry_run


def _part(
    part_id: str,
    *,
    layer: str,
    x: float = 0,
    y: float = 0,
    width: float = 100,
    height: float = 100,
    outer_mm: float = 500,
    inner_mm: float = 0,
    inner_count: int = 0,
    contour_count: int = 1,
    can_nest: bool = True,
) -> dict:
    return {
        "id": part_id,
        "sourceLayerName": layer,
        "source": {"layerName": layer, "layerId": layer},
        "boundsMm": {"x": x, "y": y, "width": width, "height": height},
        "outerPerimeterMm": outer_mm,
        "innerPerimeterMm": inner_mm,
        "innerContourCount": inner_count,
        "contourCount": contour_count,
        "canNest": can_nest,
    }


def _layer_setup(*entries: tuple[str, str]) -> IntakeV4LayerRoleSetup:
    return IntakeV4LayerRoleSetup(
        confirmation_status="complete",
        layers=[
            {
                "layer_key": layer_key,
                "layer_name": layer_key,
                "confirmed_role": role,
                "confirmation_state": "confirmed",
            }
            for layer_key, role in entries
        ],
    )


def _multi_layer_payload() -> IntakeV4WorkspacePayload:
    analysis = {
        "layers": [
            {"id": "art-layer", "name": "art-layer", "perimeterMl": 1.0, "boundingAreaSqm": 0.2},
            {"id": "face-a", "name": "face-a", "perimeterMl": 6.0, "boundingAreaSqm": 1.0},
            {"id": "face-b", "name": "face-b", "perimeterMl": 7.0, "boundingAreaSqm": 1.1},
        ],
        "parts": {
            "count": 11,
            "nestableCount": 11,
            "items": [
                _part("art-1", layer="art-layer", outer_mm=400),
                *[
                    _part(f"face-a-{index}", layer="face-a", x=index * 120, outer_mm=500)
                    for index in range(5)
                ],
                *[
                    _part(f"face-b-{index}", layer="face-b", x=index * 120, y=200, outer_mm=500)
                    for index in range(5)
                ],
            ],
        },
    }
    return IntakeV4WorkspacePayload(
        client=IntakeV4ClientRequest(),
        product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
        finish_setup=IntakeV4FinishSetup(
            confirmed=True,
            illuminated=False,
            return_finish_type="standard_aluminum",
            return_depth_mm=60,
        ),
        svg_analysis_json=analysis,
        layer_role_setup=_layer_setup(
            ("art-layer", "printed_artwork"),
            ("face-a", "face"),
            ("face-b", "face"),
        ),
    )


class TestIntakeV4AiSemanticClassificationContract:
    def test_candidate_payload_includes_groups_per_layer_role(self):
        payload = _multi_layer_payload()
        candidate = build_ai_semantic_classification_candidate_payload(
            workspace_id="ws-ai-1",
            payload=payload,
        )
        assert candidate.workspace_id == "ws-ai-1"
        assert candidate.template_id == "TPL-VOLUMETRIC-LETTERS"
        assert len(candidate.groups) == 3
        roles = {group.operator_role for group in candidate.groups}
        assert roles == {"printed_artwork", "face"}
        layers = {group.source_layer for group in candidate.groups}
        assert layers == {"art-layer", "face-a", "face-b"}

    def test_candidate_payload_includes_geometry_without_invented_text(self):
        payload = _multi_layer_payload()
        candidate = build_ai_semantic_classification_candidate_payload(
            workspace_id="ws-ai-2",
            payload=payload,
        )
        dumped = candidate.model_dump(mode="json")
        assert "suggested_text" not in json.dumps(dumped)
        face_groups = [group for group in candidate.groups if group.operator_role == "face"]
        assert face_groups
        for group in face_groups:
            assert group.geometry.outer_contours_count >= 1
            assert group.geometry.outer_perimeter_ml is not None
        assert candidate.render_preview.available is False

    def test_boundary_flags_block_pricing_production_task_generation(self):
        preview = build_intake_v4_ai_semantic_classification_preview(
            workspace_id="ws-ai-3",
            payload=_multi_layer_payload(),
        )
        flags = preview.boundary_flags
        assert flags.is_ai_suggestion is True
        assert flags.requires_operator_confirmation is True
        assert flags.used_for_pricing is False
        assert flags.used_for_production is False
        assert flags.used_for_task_generation is False
        for suggestion in preview.mock_suggestion.suggestions:
            assert suggestion.boundary_flags.used_for_pricing is False
            assert suggestion.boundary_flags.used_for_production is False
            assert suggestion.boundary_flags.used_for_task_generation is False

    def test_mock_suggestion_requires_operator_confirmation(self):
        preview = build_intake_v4_ai_semantic_classification_preview(
            workspace_id="ws-ai-4",
            payload=_multi_layer_payload(),
        )
        assert preview.ai_not_called is True
        assert preview.preview_only is True
        assert preview.mock_suggestion.schema_version == AI_SEMANTIC_CLASSIFICATION_SCHEMA_VERSION
        assert preview.mock_suggestion.suggestions
        for suggestion in preview.mock_suggestion.suggestions:
            assert suggestion.requires_operator_confirmation is True
            assert suggestion.suggested_text is None

    def test_preview_marks_ai_not_called_without_external_provider(self):
        preview = build_intake_v4_ai_semantic_classification_preview(
            workspace_id="ws-ai-5",
            payload=_multi_layer_payload(),
        )
        assert preview.ai_not_called is True
        assert preview.preview_only is True
        dumped = json.dumps(preview.model_dump(mode="json"))
        assert "openai" not in dumped.lower()
        assert "anthropic" not in dumped.lower()
        assert "api_key" not in dumped.lower()

    def test_ai_preview_does_not_modify_material_breakdown(self):
        payload = _multi_layer_payload()
        payload_raw = payload.model_dump(mode="json")
        before = build_intake_v4_material_breakdown(workspace_id="ws-ai-6", payload_raw=payload_raw)
        build_intake_v4_ai_semantic_classification_preview(workspace_id="ws-ai-6", payload=payload)
        after = build_intake_v4_material_breakdown(workspace_id="ws-ai-6", payload_raw=payload_raw)
        assert before.model_dump(mode="json") == after.model_dump(mode="json")

    def test_ai_preview_does_not_modify_task_dry_run(self):
        payload = _multi_layer_payload()
        prod_before = build_v4_production_task_dry_run(workspace_id="ws-ai-7", payload=payload)
        build_intake_v4_ai_semantic_classification_preview(workspace_id="ws-ai-7", payload=payload)
        prod_after = build_v4_production_task_dry_run(workspace_id="ws-ai-7", payload=payload)
        assert prod_before.model_dump(mode="json") == prod_after.model_dump(mode="json")

    def test_unknown_role_stays_unknown_without_confirmation(self):
        payload = IntakeV4WorkspacePayload(
            client=IntakeV4ClientRequest(),
            product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
            finish_setup=IntakeV4FinishSetup(confirmed=True, illuminated=False),
            svg_analysis_json={
                "layers": [{"id": "mystery", "name": "mystery", "perimeterMl": 2.0, "boundingAreaSqm": 0.5}],
                "parts": {
                    "items": [_part("mystery-1", layer="mystery", outer_mm=300)],
                },
            },
            layer_role_setup=_layer_setup(("mystery", "unknown")),
        )
        candidate = build_ai_semantic_classification_candidate_payload(
            workspace_id="ws-ai-8",
            payload=payload,
        )
        mock = build_mock_ai_semantic_suggestion(candidate)
        assert len(mock.suggestions) == 1
        suggestion = mock.suggestions[0]
        assert suggestion.suggested_kind == "unknown"
        assert suggestion.suggested_text is None
        assert suggestion.requires_operator_confirmation is True
        assert suggestion.confidence <= 0.40
