"""Intake V4 pricing_input preview adapter (Sprint 2)."""

from __future__ import annotations

from schemas.intake_v4 import (
    IntakeV4ClientRequest,
    IntakeV4FinishSetup,
    IntakeV4LayerRoleSetup,
    IntakeV4LetterGroupFinish,
    IntakeV4ProductBinding,
    IntakeV4WorkspacePayload,
)
from services.intake_v4_pricing_input_service import (
    _patch_quote_input_from_v4_geometry,
    build_v4_pricing_input_preview,
)


def _nest2_analysis() -> dict:
    return {
        "document": {"widthMm": 3000, "heightMm": 1000},
        "layers": [
            {"id": "l1", "name": "litere-volumetrice-1", "perimeterMl": 12.5, "boundingAreaSqm": 1.2},
            {"id": "l2", "name": "litere-volumetrice-2", "perimeterMl": 8.0, "boundingAreaSqm": 0.8},
        ],
        "parts": {"count": 12, "nestableCount": 10},
    }


def _layer_roles_complete() -> IntakeV4LayerRoleSetup:
    return IntakeV4LayerRoleSetup(
        confirmation_status="complete",
        layers=[
            {"layer_key": "l1", "confirmed_role": "face", "confirmation_state": "confirmed"},
            {"layer_key": "l2", "confirmed_role": "face", "confirmation_state": "confirmed"},
        ],
    )


def _payload(
    *,
    finish: IntakeV4FinishSetup | None = None,
    quote_geometry: dict | None = None,
    path_geometry_summary: dict | None = None,
    svg_analysis_json: dict | None = None,
    layer_role_setup: IntakeV4LayerRoleSetup | None = None,
    use_default_quote_geometry: bool = True,
) -> IntakeV4WorkspacePayload:
    resolved_quote_geometry = (
        {"letter_count": 8, "letter_perimeter_m": 10.2}
        if use_default_quote_geometry and quote_geometry is None
        else quote_geometry
    )
    return IntakeV4WorkspacePayload(
        client=IntakeV4ClientRequest(),
        product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
        finish_setup=finish,
        svg_analysis_json=svg_analysis_json or {"layers": []},
        quote_geometry=resolved_quote_geometry,
        path_geometry_summary=path_geometry_summary,
        layer_role_setup=layer_role_setup,
    )


class TestIntakeV4PricingInputPreview:
    def test_patches_v4_geometry_and_lighting(self):
        finish = IntakeV4FinishSetup(
            face_finish_type="oracal_651",
            return_finish_type="oracal_wrapped",
            return_depth_mm=60,
            face_vinyl_roll_width_mm=1260,
            illuminated=True,
            lighting_system_type="led_modules",
            light_color="warm",
            estimated_led_watts=42.0,
            required_psu_watts=50.0,
            psu_configuration=[60],
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-test",
            payload=_payload(finish=finish),
        )
        assert preview.workspace_id == "ws-test"
        assert preview.template_code == "TPL-VOLUMETRIC-LETTERS"
        assert preview.preview_only is True
        assert preview.quote_input_payload.get("intake_source") == "intake_v4"
        assert preview.quote_input_payload.get("illuminated") is True
        assert preview.quote_input_payload.get("estimated_led_watts") == 42.0
        assert preview.quote_input_payload.get("letter_count") == 8
        assert preview.operation_flags.get("face_vinyl_application_required") is True

    def test_grouped_finish_sets_letter_group_count(self):
        finish = IntakeV4FinishSetup(
            illuminated=True,
            letter_group_finishes=[
                IntakeV4LetterGroupFinish(
                    group_key="g1",
                    layer_name="litere",
                    face_finish_type="oracal_651",
                    return_finish_type="oracal_wrapped",
                )
            ],
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-groups",
            payload=_payload(finish=finish),
        )
        assert preview.quote_input_payload.get("letter_group_count") == 1
        assert preview.quote_input_payload.get("grouped_finish_pricing_mode") == "per_group_handoff"
        assert preview.quote_input_payload.get("letter_group_face_vinyl_handoff", {}).get("groups")
        assert preview.quote_input_payload.get("letter_group_return_vinyl_handoff", {}).get("groups")
        assert preview.finish_summary.get("face_finish_type") in {"oracal_651", "vinyl"}

    def test_grouped_finish_handoff_preserves_each_letter_group(self):
        finish = IntakeV4FinishSetup(
            illuminated=True,
            return_depth_mm=60,
            face_vinyl_roll_width_mm=1260,
            letter_group_finishes=[
                IntakeV4LetterGroupFinish(
                    group_key="g1",
                    layer_name="litere-1",
                    face_finish_type="oracal_651",
                    face_oracal_code="010",
                    face_oracal_name="White",
                    return_finish_type="oracal_wrapped",
                    return_depth_mm=60,
                    confirmed=True,
                ),
                IntakeV4LetterGroupFinish(
                    group_key="g2",
                    layer_name="litere-2",
                    face_finish_type="oracal_8500",
                    face_oracal_code="020",
                    face_oracal_name="Yellow",
                    return_finish_type="oracal_wrapped",
                    return_depth_mm=80,
                    confirmed=True,
                ),
            ],
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-groups-handoff",
            payload=_payload(finish=finish),
        )
        qi = preview.quote_input_payload
        face_handoff = qi.get("letter_group_face_vinyl_handoff") or {}
        return_handoff = qi.get("letter_group_return_vinyl_handoff") or {}

        assert qi.get("grouped_finish_pricing_mode") == "per_group_handoff"
        assert qi.get("requires_grouped_finish_review") is False
        assert preview.requires_grouped_finish_review is False
        assert {g["group_id"] for g in face_handoff.get("groups", [])} == {"g1", "g2"}
        assert {g["group_id"] for g in return_handoff.get("groups", [])} == {"g1", "g2"}
        assert face_handoff.get("uniform_all_letters") is False
        assert return_handoff.get("uniform_all_letters") is False
        assert qi.get("face_finish_variation_count") == 2
        assert qi.get("return_finish_variation_count") == 2
        matrix = qi.get("letter_group_finish_matrix") or []
        assert [row["group_id"] for row in matrix] == ["g1", "g2"]
        assert matrix[1]["face_finish_template_type"] == "oracal_651"
        assert matrix[1]["return_depth_mm"] == 80

    def test_grouped_finish_perimeter_overrides_canonical_return_perimeter(self):
        finish = IntakeV4FinishSetup(
            illuminated=True,
            return_depth_mm=60,
            face_vinyl_roll_width_mm=1260,
            letter_group_finishes=[
                IntakeV4LetterGroupFinish(
                    group_key="g1",
                    layer_name="litere-1",
                    face_finish_type="oracal_651",
                    return_finish_type="white_aluminum",
                    perimeter_m=4.0,
                    confirmed=True,
                ),
                IntakeV4LetterGroupFinish(
                    group_key="g2",
                    layer_name="litere-2",
                    face_finish_type="oracal_651",
                    return_finish_type="white_aluminum",
                    perimeter_m=3.2,
                    confirmed=True,
                ),
            ],
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-group-perimeter",
            payload=_payload(
                finish=finish,
                quote_geometry={
                    "letter_count": 2,
                    "return_material_perimeter_ml": 9.9,
                    "letter_return_perimeter_ml": 9.9,
                },
            ),
        )
        qi = preview.quote_input_payload
        assert qi.get("grouped_finish_pricing_mode") == "per_group_handoff"
        assert qi.get("return_material_perimeter_ml") == 7.2
        assert qi.get("letter_return_perimeter_ml") == 7.2

    def test_ral_paint_tubes_are_estimated_from_painted_cant_perimeter(self):
        finish = IntakeV4FinishSetup(
            illuminated=False,
            return_depth_mm=60,
            return_finish_type="white_aluminum",
            letter_group_finishes=[
                IntakeV4LetterGroupFinish(
                    group_key="g1",
                    layer_name="litere-ral",
                    face_finish_type="oracal_651",
                    return_finish_type="ral_paint",
                    return_oracal_code="9005",
                    return_oracal_name="Jet black",
                    perimeter_m=16.2,
                    confirmed=True,
                )
            ],
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-ral-tubes",
            payload=_payload(finish=finish),
        )
        qi = preview.quote_input_payload

        assert qi.get("estimated_paint_tubes") == 1.08
        assert qi.get("paint_tube_count") == 1.08
        assert qi.get("painted_return_perimeter_m") == 16.2
        assert qi.get("paint_ral_code") == "9005"
        assert qi.get("volume_finish") == "paint_after_face_miter_bond"

    def test_mixed_ral_and_wrapped_cant_does_not_enable_global_paint_finish(self):
        finish = IntakeV4FinishSetup(
            illuminated=False,
            return_depth_mm=60,
            letter_group_finishes=[
                IntakeV4LetterGroupFinish(
                    group_key="painted",
                    layer_name="painted",
                    return_finish_type="ral_paint",
                    return_oracal_code="9005",
                    perimeter_m=5.0,
                    confirmed=True,
                ),
                IntakeV4LetterGroupFinish(
                    group_key="wrapped",
                    layer_name="wrapped",
                    return_finish_type="oracal_wrapped",
                    perimeter_m=7.0,
                    confirmed=True,
                ),
            ],
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-mixed-ral",
            payload=_payload(finish=finish),
        )
        qi = preview.quote_input_payload

        assert qi.get("estimated_paint_tubes") == 0.3333
        assert qi.get("painted_return_perimeter_m") == 5.0
        assert qi.get("volume_finish") is None

    def test_raw_vector_total_overrides_grouped_return_for_unclassified_artwork(self):
        finish = IntakeV4FinishSetup(
            illuminated=True,
            return_depth_mm=60,
            face_vinyl_roll_width_mm=1260,
            letter_group_finishes=[
                IntakeV4LetterGroupFinish(
                    group_key="letters",
                    layer_name="letters",
                    face_finish_type="oracal_651",
                    return_finish_type="white_aluminum",
                    perimeter_m=26.7472,
                    confirmed=True,
                )
            ],
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-raw-vector-pricing",
            payload=_payload(
                finish=finish,
                quote_geometry={
                    "letter_count": 19,
                    "return_material_perimeter_ml": 24.6488,
                    "letter_return_perimeter_ml": 24.6488,
                    "face_cutting_perimeter_ml": 24.6488,
                    "cutting_perimeter_ml": 24.6488,
                    "cnc_cutting_perimeter_ml": 24.6488,
                },
                path_geometry_summary={"perimeter_mm_approx": 31637.330856},
            ),
        )
        qi = preview.quote_input_payload
        assert qi.get("return_material_perimeter_ml") == 31.6373
        assert qi.get("letter_return_perimeter_ml") == 26.7472
        assert qi.get("artwork_return_perimeter_ml") == 4.8901
        assert qi.get("cnc_cutting_perimeter_ml") == 31.6373

    def test_artwork_needs_decision_adds_warning(self):
        finish = IntakeV4FinishSetup(
            illuminated=False,
            artwork_finishes=[
                {
                    "layer_key": "logo",
                    "layer_name": "logo",
                    "execution_type": "needs_decision",
                }
            ],
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-art",
            payload=_payload(finish=finish),
        )
        assert any("nedecisă" in w for w in preview.adapter_warnings)

    def test_derives_geometry_from_nest2_when_quote_geometry_missing(self):
        finish = IntakeV4FinishSetup(
            face_finish_type="oracal_651",
            return_finish_type="oracal_wrapped",
            return_depth_mm=60,
            face_vinyl_roll_width_mm=1260,
            illuminated=True,
            lighting_system_type="led_modules",
            light_color="warm",
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-derived",
            payload=_payload(
                finish=finish,
                quote_geometry={},
                use_default_quote_geometry=False,
                svg_analysis_json=_nest2_analysis(),
                layer_role_setup=_layer_roles_complete(),
            ),
        )
        assert preview.production_counts["letter_count"] == 10
        assert preview.quote_input_payload.get("letter_perimeter_m") == 20.5
        assert preview.quote_input_payload.get("face_area_m2") == 2.0

    def test_grouped_finish_setup_confirmed_clears_v3_blockers(self):
        finish = IntakeV4FinishSetup(
            illuminated=True,
            return_depth_mm=60,
            lighting_system_type="led_modules",
            light_color="warm",
            confirmed=True,
            letter_group_finishes=[
                IntakeV4LetterGroupFinish(
                    group_key="g1",
                    layer_name="litere-1",
                    face_finish_type="oracal_651",
                    return_finish_type="oracal_wrapped",
                    face_vinyl_roll_width_mm=1260,
                    confirmed=False,
                ),
                IntakeV4LetterGroupFinish(
                    group_key="g2",
                    layer_name="litere-2",
                    face_finish_type="oracal_651",
                    return_finish_type="oracal_wrapped",
                    face_vinyl_roll_width_mm=1260,
                    confirmed=False,
                ),
            ],
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-groups-ready",
            payload=_payload(
                finish=finish,
                svg_analysis_json=_nest2_analysis(),
                layer_role_setup=_layer_roles_complete(),
                quote_geometry={},
                use_default_quote_geometry=False,
            ),
        )
        assert preview.production_counts["letter_count"] == 10
        assert preview.is_ready_for_quote is True
        assert preview.adapter_status != "blocked"
        assert "MISSING_FACE_FINISH_CONFIRMATION" not in preview.adapter_blockers
        assert "MISSING_GROUP_FINISH_ASSIGNMENT" not in preview.adapter_blockers
        assert "MISSING_LIGHTING_ILLUMINATION_MODE" not in preview.adapter_blockers
        assert preview.requires_grouped_finish_review is False

    def test_without_backing_layer_sets_backing_present_false(self):
        finish = IntakeV4FinishSetup(
            face_finish_type="oracal_651",
            return_finish_type="oracal_wrapped",
            return_depth_mm=60,
            confirmed=True,
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-no-backing",
            payload=_payload(
                finish=finish,
                layer_role_setup=_layer_roles_complete(),
            ),
        )
        qi = preview.quote_input_payload
        assert qi.get("backing_present") is False
        assert qi.get("back_bevel_enabled") is False
        assert qi.get("backing_material") is None

    def test_confirmed_backing_layer_sets_backing_present_true(self):
        finish = IntakeV4FinishSetup(
            face_finish_type="oracal_651",
            return_finish_type="oracal_wrapped",
            return_depth_mm=60,
            confirmed=True,
        )
        layer_roles = IntakeV4LayerRoleSetup(
            confirmation_status="complete",
            layers=[
                {"layer_key": "l1", "confirmed_role": "face", "confirmation_state": "confirmed"},
                {"layer_key": "l2", "confirmed_role": "backing", "confirmation_state": "confirmed"},
            ],
        )
        preview = build_v4_pricing_input_preview(
            workspace_id="ws-backing",
            payload=_payload(finish=finish, layer_role_setup=layer_roles),
        )
        qi = preview.quote_input_payload
        assert qi.get("backing_present") is True
        assert qi.get("backing_material") == "FOREX_10MM"
        assert qi.get("backing_thickness_mm") == 10.0
        assert qi.get("back_bevel_enabled") is False
