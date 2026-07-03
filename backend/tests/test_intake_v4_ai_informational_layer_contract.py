"""Intake V4 AI Informational Layer — read-only contract tests (SVG review context)."""

from __future__ import annotations

import json

from schemas.ai_informational_layer import (
    AI_INFORMATIONAL_SOURCE_CONTEXTS,
    AI_SUGGESTION_CATEGORIES,
    AiInformationalSuggestionEnvelope,
)
from schemas.intake_v4 import (
    IntakeV4ClientRequest,
    IntakeV4FinishSetup,
    IntakeV4LayerRoleSetup,
    IntakeV4ProductBinding,
    IntakeV4WorkspacePayload,
)
from services.ai_informational_layer_service import (
    ai_informational_boundary_flags,
    build_informational_envelope,
)
from services.intake_v4_ai_semantic_classification_service import (
    AI_SEMANTIC_CLASSIFICATION_SCHEMA_VERSION,
    build_ai_semantic_classification_candidate_payload,
    build_intake_v4_ai_informational_assist_preview,
    build_mock_ai_semantic_suggestion,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.intake_v4_pricing_input_service import build_v4_pricing_input_preview
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


class TestIntakeV4AiInformationalLayerContract:
    def test_informational_assist_preview_is_read_only(self):
        preview = build_intake_v4_ai_informational_assist_preview(
            workspace_id="ws-info-1",
            payload=_multi_layer_payload(),
        )
        assert preview.preview_only is True
        assert preview.ai_not_called is True
        assert preview.context == "intake_v4_svg_review"
        assert preview.informational_envelope.writes_business_state is False

    def test_ai_not_called_true(self):
        preview = build_intake_v4_ai_informational_assist_preview(
            workspace_id="ws-info-2",
            payload=_multi_layer_payload(),
        )
        assert preview.ai_not_called is True

    def test_boundary_flags_block_pricing_production_task_generation(self):
        preview = build_intake_v4_ai_informational_assist_preview(
            workspace_id="ws-info-3",
            payload=_multi_layer_payload(),
        )
        flags = preview.boundary_flags
        assert flags.informational_only is True
        assert flags.requires_operator_confirmation is True
        assert flags.used_for_pricing is False
        assert flags.used_for_production is False
        assert flags.used_for_task_generation is False
        assert flags.can_create_order is False
        assert flags.can_create_execution_tasks is False
        assert preview.informational_envelope.used_for_pricing is False
        assert preview.informational_envelope.used_for_production is False
        assert preview.informational_envelope.used_for_task_generation is False

    def test_mock_suggestions_require_operator_confirmation_for_semantic_items(self):
        preview = build_intake_v4_ai_informational_assist_preview(
            workspace_id="ws-info-4",
            payload=_multi_layer_payload(),
        )
        semantic_items = [
            item
            for item in preview.mock_suggestions
            if item.category == "semantic_classification"
        ]
        assert semantic_items
        for item in semantic_items:
            assert item.requires_confirmation is True
            assert item.boundary_flags.requires_operator_confirmation is True
            assert item.payload.get("suggested_text") is None

    def test_material_breakdown_unchanged_after_informational_preview(self):
        payload = _multi_layer_payload()
        payload_raw = payload.model_dump(mode="json")
        before = build_intake_v4_material_breakdown(workspace_id="ws-info-5", payload_raw=payload_raw)
        build_intake_v4_ai_informational_assist_preview(workspace_id="ws-info-5", payload=payload)
        after = build_intake_v4_material_breakdown(workspace_id="ws-info-5", payload_raw=payload_raw)
        assert before.model_dump(mode="json") == after.model_dump(mode="json")

    def test_task_dry_run_unchanged_after_informational_preview(self):
        payload = _multi_layer_payload()
        before = build_v4_production_task_dry_run(workspace_id="ws-info-6", payload=payload)
        build_intake_v4_ai_informational_assist_preview(workspace_id="ws-info-6", payload=payload)
        after = build_v4_production_task_dry_run(workspace_id="ws-info-6", payload=payload)
        assert before.model_dump(mode="json") == after.model_dump(mode="json")

    def test_pricing_input_unchanged_after_informational_preview(self):
        payload = _multi_layer_payload()
        before = build_v4_pricing_input_preview(workspace_id="ws-info-7", payload=payload)
        build_intake_v4_ai_informational_assist_preview(workspace_id="ws-info-7", payload=payload)
        after = build_v4_pricing_input_preview(workspace_id="ws-info-7", payload=payload)
        assert before.model_dump(mode="json") == after.model_dump(mode="json")

    def test_schema_supports_future_website_contexts(self):
        assert "intake_v4_svg_review" in AI_INFORMATIONAL_SOURCE_CONTEXTS
        assert "website_chatbot" in AI_INFORMATIONAL_SOURCE_CONTEXTS
        assert "website_order_form" in AI_INFORMATIONAL_SOURCE_CONTEXTS

        chatbot_envelope = build_informational_envelope(
            source_context="website_chatbot",
            suggestions=[],
            warnings=["Draft chat summary only."],
        )
        order_form_envelope = build_informational_envelope(
            source_context="website_order_form",
            suggestions=[],
            warnings=["Draft order form assist only."],
        )
        assert isinstance(chatbot_envelope, AiInformationalSuggestionEnvelope)
        assert chatbot_envelope.source_context == "website_chatbot"
        assert order_form_envelope.source_context == "website_order_form"
        assert chatbot_envelope.writes_business_state is False
        assert "semantic_classification" in AI_SUGGESTION_CATEGORIES
        assert "template_recommendation" in AI_SUGGESTION_CATEGORIES

    def test_candidate_payload_includes_groups_without_invented_text(self):
        payload = _multi_layer_payload()
        candidate = build_ai_semantic_classification_candidate_payload(
            workspace_id="ws-info-8",
            payload=payload,
        )
        dumped = candidate.model_dump(mode="json")
        assert "suggested_text" not in json.dumps(dumped)
        assert len(candidate.groups) == 3

    def test_legacy_semantic_mock_still_available_on_informational_preview(self):
        preview = build_intake_v4_ai_informational_assist_preview(
            workspace_id="ws-info-9",
            payload=_multi_layer_payload(),
        )
        assert preview.mock_suggestion is not None
        assert preview.mock_suggestion.schema_version == AI_SEMANTIC_CLASSIFICATION_SCHEMA_VERSION

    def test_unknown_role_stays_unknown_in_semantic_mock(self):
        payload = IntakeV4WorkspacePayload(
            client=IntakeV4ClientRequest(),
            product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
            finish_setup=IntakeV4FinishSetup(confirmed=True, illuminated=False),
            svg_analysis_json={
                "layers": [{"id": "mystery", "name": "mystery", "perimeterMl": 2.0, "boundingAreaSqm": 0.5}],
                "parts": {"items": [_part("mystery-1", layer="mystery", outer_mm=300)]},
            },
            layer_role_setup=_layer_setup(("mystery", "unknown")),
        )
        candidate = build_ai_semantic_classification_candidate_payload(
            workspace_id="ws-info-10",
            payload=payload,
        )
        mock = build_mock_ai_semantic_suggestion(candidate)
        assert mock.suggestions[0].suggested_kind == "unknown"
        assert mock.suggestions[0].suggested_text is None

    def test_shared_boundary_factory_matches_preview_flags(self):
        preview = build_intake_v4_ai_informational_assist_preview(
            workspace_id="ws-info-11",
            payload=_multi_layer_payload(),
        )
        assert preview.boundary_flags.model_dump() == ai_informational_boundary_flags().model_dump()
