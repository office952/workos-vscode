"""Tests for Intake V4 → TPL-VOLUMETRIC-LETTERS template option contract."""

from __future__ import annotations

import pytest

from schemas.intake_v4 import IntakeV4FinishSetup, IntakeV4ProductBinding, IntakeV4WorkspacePayload
from services.intake_v4_template_option_contract_service import (
    DOSSIER_VARIANT_KEYS,
    MATERIAL_INTENT_REGISTRY,
    RETURN_DEPTH_ALLOWED,
    PSU_WATTS_ALLOWED,
    V4_FACE_FINISH_TO_TEMPLATE,
    evaluate_v4_template_option_contract,
    get_canonical_mapping_catalog,
)


def _payload(**finish_kwargs) -> IntakeV4WorkspacePayload:
    setup = IntakeV4FinishSetup(confirmed=True, **finish_kwargs)
    return IntakeV4WorkspacePayload(
        product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
        finish_setup=setup,
    )


class TestCanonicalCatalog:
    def test_catalog_has_minimum_matrix_rows(self):
        rows = get_canonical_mapping_catalog()
        labels = {r.discovered_option for r in rows}
        assert "Plexiglas față 3 mm" in labels
        assert "Forex backing 10 mm" in labels
        assert "Oracal 651 față" in labels
        assert "Montaj direct pe perete" in labels
        assert "Montaj pe structură (bare oțel/aluminiu)" in labels
        assert len(rows) >= 30

    def test_return_depths_all_canonical(self):
        rows = get_canonical_mapping_catalog()
        depth_rows = [r for r in rows if r.discovered_option.startswith("Cant/lateral")]
        assert len(depth_rows) == 4
        assert all(r.status == "aligned" for r in depth_rows)

    def test_psu_watts_all_canonical(self):
        rows = get_canonical_mapping_catalog()
        psu_rows = [r for r in rows if r.discovered_option.startswith("PSU")]
        assert len(psu_rows) == 4
        assert all(r.status == "aligned" for r in psu_rows)

    def test_major_materials_have_registry_codes(self):
        for key in ("plexiglas_face", "forex_backing", "face_vinyl", "led_modules", "led_psu"):
            assert key in MATERIAL_INTENT_REGISTRY


class TestEvaluateContract:
    def test_aligned_oracal_651_no_template_option_missing(self):
        result = evaluate_v4_template_option_contract(
            _payload(
                face_finish_type="oracal_651",
                return_finish_type="oracal_wrapped",
                return_depth_mm=60,
                illuminated=False,
            )
        )
        codes = {w.code for w in result.warnings}
        assert "template_option_missing" not in codes
        assert result.blockers == []

    def test_oracal_641_is_aligned_after_dossier_extension(self):
        """oracal_641 was promoted to a dossier allowed_value — now aligned."""
        result = evaluate_v4_template_option_contract(
            _payload(face_finish_type="oracal_641", return_depth_mm=60, illuminated=False)
        )
        face_warnings = [
            w for w in result.warnings
            if w.option_key == "oracal_641"
        ]
        assert face_warnings == [], f"Expected no warnings for oracal_641, got: {face_warnings}"
        tpl, status = V4_FACE_FINISH_TO_TEMPLATE["oracal_641"]
        assert tpl == "oracal_641"
        assert status == "aligned"

    def test_oracal_8500_is_aligned_as_separate_v4_material(self):
        result = evaluate_v4_template_option_contract(
            _payload(face_finish_type="oracal_8500", return_depth_mm=60, illuminated=False)
        )
        warnings = [
            w
            for w in result.warnings
            if w.code == "discovered_option_not_canonicalized" and w.option_key == "oracal_8500"
        ]
        assert warnings == []
        tpl, status = V4_FACE_FINISH_TO_TEMPLATE["oracal_8500"]
        assert tpl == "oracal_8500"
        assert status == "aligned"

    def test_return_depth_30_60_80_100_allowed(self):
        for depth in RETURN_DEPTH_ALLOWED:
            result = evaluate_v4_template_option_contract(
                _payload(return_depth_mm=depth, illuminated=False)
            )
            depth_warnings = [
                w
                for w in result.warnings
                if w.code == "template_material_intent_missing" and w.option_key == str(depth)
            ]
            assert depth_warnings == []

    def test_invalid_return_depth_warns(self):
        result = evaluate_v4_template_option_contract(
            _payload(return_depth_mm=45, illuminated=False)
        )
        assert any(w.code == "template_material_intent_missing" for w in result.warnings)

    def test_print_laminate_aligned_mapping(self):
        result = evaluate_v4_template_option_contract(
            _payload(face_finish_type="print_laminate", return_depth_mm=60, illuminated=False)
        )
        tpl, status = V4_FACE_FINISH_TO_TEMPLATE["print_laminate"]
        assert tpl == "printed_laminated_vinyl"
        assert status == "aligned"
        assert not any(w.code == "template_option_missing" for w in result.warnings)

    def test_led_psu_mapping_allowed_watts(self):
        result = evaluate_v4_template_option_contract(
            _payload(
                return_depth_mm=60,
                illuminated=True,
                psu_configuration=[100],
                lighting_system_type="led_modules",
            )
        )
        psu_bad = [w for w in result.warnings if w.code == "template_pricing_code_missing" and w.option_key == "100"]
        assert psu_bad == []

    def test_multi_psu_emits_discovered_not_canonicalized(self):
        result = evaluate_v4_template_option_contract(
            _payload(
                return_depth_mm=60,
                illuminated=True,
                psu_configuration=[100, 60],
            )
        )
        assert any(w.code == "discovered_option_not_canonicalized" for w in result.warnings)

    def test_led_strip_not_template_backed(self):
        result = evaluate_v4_template_option_contract(
            _payload(
                return_depth_mm=60,
                illuminated=True,
                psu_configuration=[100],
                lighting_system_type="led_strip",
            )
        )
        assert any(
            w.code == "form_option_not_template_backed" and w.option_key == "led_strip"
            for w in result.warnings
        )

    def test_ral_paint_return_warns_paint_tubes(self):
        result = evaluate_v4_template_option_contract(
            _payload(return_finish_type="ral_paint", return_depth_mm=60, illuminated=False)
        )
        assert any(w.code == "template_pricing_code_missing" and w.option_key == "ral_paint" for w in result.warnings)

    def test_ral_paint_return_with_perimeter_auto_fills_paint_tubes(self):
        payload = IntakeV4WorkspacePayload(
            product_binding=IntakeV4ProductBinding(template_code="TPL-VOLUMETRIC-LETTERS"),
            finish_setup=IntakeV4FinishSetup(
                confirmed=True,
                return_finish_type="ral_paint",
                return_oracal_code="9005",
                return_depth_mm=60,
                illuminated=False,
            ),
            quote_geometry={
                "letter_return_perimeter_ml": 16.2,
                "return_material_perimeter_ml": 16.2,
            },
        )
        result = evaluate_v4_template_option_contract(payload)

        assert not any(
            w.code == "template_pricing_code_missing" and w.option_key == "ral_paint"
            for w in result.warnings
        )

    def test_multi_group_finish_uses_v4_per_group_handoff(self):
        result = evaluate_v4_template_option_contract(
            _payload(
                return_depth_mm=60,
                illuminated=False,
                letter_group_finishes=[
                    {
                        "group_key": "g1",
                        "layer_name": "L1",
                        "face_finish_type": "oracal_651",
                        "return_finish_type": "oracal_wrapped",
                        "return_depth_mm": 60,
                    },
                    {
                        "group_key": "g2",
                        "layer_name": "L2",
                        "face_finish_type": "print_laminate",
                        "return_finish_type": "ral_paint",
                        "return_depth_mm": 80,
                    },
                ],
            )
        )
        assert result.discovered_v4_values["letter_group_finish_count"] == 2
        assert result.discovered_v4_values["letter_group_finish_pricing_mode"] == "per_group_handoff"
        assert not any(w.source == "intake_v4_finish_adapter" for w in result.warnings)

    def test_production_preview_uses_canonical_operation_registry_without_contract_warning(self):
        result = evaluate_v4_template_option_contract(
            _payload(return_depth_mm=60, illuminated=False)
        )
        assert not any(w.code == "production_preview_not_template_backed" for w in result.warnings)

    def test_unsupported_template_blocks(self):
        payload = IntakeV4WorkspacePayload(
            product_binding=IntakeV4ProductBinding(template_code="TPL-OTHER"),
            finish_setup=IntakeV4FinishSetup(confirmed=True),
        )
        result = evaluate_v4_template_option_contract(payload)
        assert any(b.code == "unsupported_template" for b in result.blockers)

    def test_dossier_variant_keys_match_seed_contract(self):
        assert "return_depth_mm" in DOSSIER_VARIANT_KEYS
        assert "selected_psu_watts" in DOSSIER_VARIANT_KEYS
        assert PSU_WATTS_ALLOWED == frozenset({60, 100, 160, 200})


class TestProductionHandoffIntegration:
    @pytest.mark.asyncio
    async def test_handoff_preview_includes_contract_warnings(self):
        from unittest.mock import AsyncMock, patch

        from services.intake_v4_production_handoff_preview_service import (
            build_intake_v4_production_handoff_preview,
        )

        payload_dict = {
            "schema_version": "1.0.0",
            "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
            "svg_source": {"file_name": "t.svg", "file_size_bytes": 100, "file_hash": "a" * 64, "upload_status": "analyzed"},
            "svg_analysis_json": {"schemaVersion": "1.10.0", "nesting": {"sheets": [], "rolls": []}},
            "quote_geometry": {"letter_perimeter_m": 5.0, "face_area_m2": 1.0},
            "layer_role_setup": {"confirmation_status": "complete", "layers": []},
            "finish_setup": {
                "confirmed": True,
                "face_finish_type": "oracal_641",
                "return_depth_mm": 60,
                "illuminated": True,
                "psu_configuration": [100, 60],
                "lighting_system_type": "led_strip",
            },
        }
        from schemas.intake_v4 import IntakeV4WorkspacePayload

        payload = IntakeV4WorkspacePayload.model_validate(payload_dict)

        with patch(
            "services.intake_v4_production_handoff_preview_service.build_intake_v4_material_breakdown_with_registry",
            new_callable=AsyncMock,
        ) as mock_bd:
            from schemas.intake_v4 import (
                IntakeV4MaterialBreakdownResponse,
                IntakeV4MaterialBreakdownTotals,
            )

            mock_bd.return_value = IntakeV4MaterialBreakdownResponse(
                workspace_id="ws-test",
                template_code="TPL-VOLUMETRIC-LETTERS",
                material_rows=[],
                consumable_rows=[],
                nesting_rows=[],
                warnings=[],
                totals=IntakeV4MaterialBreakdownTotals(
                    contains_missing_prices=False,
                ),
            )
            preview = await build_intake_v4_production_handoff_preview(
                db=AsyncMock(),
                workspace_id="ws-test",
                payload_raw=payload_dict,
                payload=payload,
            )

        warn_codes = {w.code for w in preview.warnings}
        assert "discovered_option_not_canonicalized" in warn_codes
        assert "form_option_not_template_backed" in warn_codes
        assert "production_preview_not_template_backed" not in warn_codes
        assert all(
            group.operation_code_source == "product_system_dossier"
            for group in preview.operation_groups
            if group.canonical_operation_keys
        )
        assert all(
            not group.legacy_operation_codes or group.operation_codes != group.legacy_operation_codes
            for group in preview.operation_groups
            if group.canonical_operation_keys
        )
        assert preview.creates_execution_tasks is False
        assert preview.stock_consumption is False


class TestVariantFieldsFromDossier:
    """Test that _variant_fields_from_dossier builds correct contract fields."""

    def test_fallback_variants_include_all_dossier_keys(self):
        from services.intake_v4_template_option_contract_service import (
            FALLBACK_DOSSIER_VARIANTS,
        )

        keys = {v["variant_key"] for v in FALLBACK_DOSSIER_VARIANTS}
        assert keys == DOSSIER_VARIANT_KEYS

    def test_face_finish_fallback_includes_oracal_641_and_8500(self):
        from services.intake_v4_template_option_contract_service import (
            FALLBACK_DOSSIER_VARIANTS,
        )

        face = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "face_finish_type")
        assert "oracal_641" in face["allowed_values"]
        assert "oracal_8500" in face["allowed_values"]
        assert "oracal_651" in face["allowed_values"]
        assert "none" in face["allowed_values"]
        assert face["default_value"] == "none"

    def test_mounting_system_has_four_options(self):
        from services.intake_v4_template_option_contract_service import (
            FALLBACK_DOSSIER_VARIANTS,
        )

        ms = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "mounting_system")
        assert set(ms["allowed_values"]) == {"direct_wall", "steel_bars", "aluminum_bars", "acm_panel"}
        assert ms["default_value"] == "direct_wall"

    def test_psu_watts_defaults_to_100(self):
        from services.intake_v4_template_option_contract_service import (
            FALLBACK_DOSSIER_VARIANTS,
        )

        psu = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "selected_psu_watts")
        assert sorted(psu["allowed_values"]) == [60, 100, 160, 200]
        assert psu["default_value"] == 100

    def test_return_depth_defaults_to_60(self):
        from services.intake_v4_template_option_contract_service import (
            FALLBACK_DOSSIER_VARIANTS,
        )

        depth = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "return_depth_mm")
        assert sorted(depth["allowed_values"]) == [30, 60, 80, 100]
        assert depth["default_value"] == 60

    def test_mounting_bar_profile_single_option(self):
        from services.intake_v4_template_option_contract_service import (
            FALLBACK_DOSSIER_VARIANTS,
        )

        bar = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "mounting_bar_profile")
        assert bar["allowed_values"] == ["30x30x1.5"]
        assert bar["default_value"] == "30x30x1.5"

    def test_variant_fields_include_default_value(self):
        from services.intake_v4_template_option_contract_service import (
            _variant_fields_from_dossier,
            FALLBACK_DOSSIER_VARIANTS,
        )

        fields = _variant_fields_from_dossier(
            FALLBACK_DOSSIER_VARIANTS,
            source="static_contract_fallback",
        )
        face_field = next(f for f in fields if f.field_key == "face_finish_type")
        assert face_field.default_value == "none"
        assert "oracal_641" in face_field.allowed_values
        assert face_field.owner == "product_system_dossier"

        depth_field = next(f for f in fields if f.field_key == "return_depth_mm")
        assert depth_field.default_value == 60

        psu_field = next(f for f in fields if f.field_key == "selected_psu_watts")
        assert psu_field.default_value == 100

        mount_field = next(f for f in fields if f.field_key == "mounting_system")
        assert mount_field.default_value == "direct_wall"
        assert "acm_panel" in mount_field.allowed_values

    def test_return_finish_type_dossier_variant(self):
        from services.intake_v4_template_option_contract_service import FALLBACK_DOSSIER_VARIANTS

        rf = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "return_finish_type")
        assert set(rf["allowed_values"]) == {"white_aluminum", "black_aluminum", "gold_aluminum", "mirror_silver", "ral_paint", "oracal_wrapped"}
        assert rf["default_value"] == "white_aluminum"

    def test_lighting_system_type_dossier_variant(self):
        from services.intake_v4_template_option_contract_service import FALLBACK_DOSSIER_VARIANTS

        ls = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "lighting_system_type")
        assert set(ls["allowed_values"]) == {"led_modules", "led_strip"}
        assert ls["default_value"] == "led_modules"

    def test_light_color_dossier_variant(self):
        from services.intake_v4_template_option_contract_service import FALLBACK_DOSSIER_VARIANTS

        lc = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "light_color")
        assert set(lc["allowed_values"]) == {"warm", "neutral", "cool"}
        assert lc["default_value"] == "warm"

    def test_led_module_power_w_dossier_variant(self):
        from services.intake_v4_template_option_contract_service import FALLBACK_DOSSIER_VARIANTS

        lm = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "led_module_power_w")
        assert sorted(lm["allowed_values"]) == [0.75, 1.0, 1.44]
        assert lm["default_value"] == 0.75

    def test_mounting_template_material_type_dossier_variant(self):
        from services.intake_v4_template_option_contract_service import FALLBACK_DOSSIER_VARIANTS

        mt = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "mounting_template_material_type")
        assert set(mt["allowed_values"]) == {"forex", "paper"}
        assert mt["default_value"] == "forex"

    def test_face_vinyl_roll_width_mm_dossier_variant(self):
        from services.intake_v4_template_option_contract_service import FALLBACK_DOSSIER_VARIANTS

        fw = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "face_vinyl_roll_width_mm")
        assert sorted(fw["allowed_values"]) == [1000, 1260]
        assert fw["default_value"] == 1000

    def test_emblem_lighting_mode_dossier_variant(self):
        from services.intake_v4_template_option_contract_service import FALLBACK_DOSSIER_VARIANTS

        el = next(v for v in FALLBACK_DOSSIER_VARIANTS if v["variant_key"] == "emblem_lighting_mode")
        assert set(el["allowed_values"]) == {"area_lit", "excluded"}
        assert el["default_value"] == "area_lit"

    def test_adapter_only_fields_now_empty(self):
        from services.intake_v4_template_option_contract_service import V4_ADAPTER_ONLY_FORM_FIELDS

        assert V4_ADAPTER_ONLY_FORM_FIELDS == []

    def test_all_face_finish_mappings_are_aligned(self):
        """After dossier extension, all V4 face finishes should be aligned."""
        for v4_val, (tpl_val, status) in V4_FACE_FINISH_TO_TEMPLATE.items():
            assert status == "aligned", f"{v4_val} maps to {tpl_val} with status {status}, expected aligned"


class TestDossierSeedAlignment:
    """Verify the dossier seed matches the contract service fallback."""

    def test_seed_face_finish_includes_extended_values(self):
        from seeds.seed_tpl_volumetric_letters_dossier import _variants

        variants = _variants()
        face = next(v for v in variants if v["variant_key"] == "face_finish_type")
        assert "oracal_641" in face["allowed_values"]
        assert "oracal_8500" in face["allowed_values"]
        assert "printed_vinyl" in face["allowed_values"]
        assert "printed_laminated_vinyl" in face["allowed_values"]

    def test_seed_variant_keys_match_service_keys(self):
        from seeds.seed_tpl_volumetric_letters_dossier import _variants

        seed_keys = {v["variant_key"] for v in _variants()}
        assert seed_keys == DOSSIER_VARIANT_KEYS

    def test_seed_return_depth_matches_service(self):
        from seeds.seed_tpl_volumetric_letters_dossier import _variants

        depth = next(v for v in _variants() if v["variant_key"] == "return_depth_mm")
        assert set(depth["allowed_values"]) == RETURN_DEPTH_ALLOWED

    def test_seed_psu_watts_matches_service(self):
        from seeds.seed_tpl_volumetric_letters_dossier import _variants

        psu = next(v for v in _variants() if v["variant_key"] == "selected_psu_watts")
        assert set(psu["allowed_values"]) == PSU_WATTS_ALLOWED

    def test_seed_has_all_14_variant_keys(self):
        from seeds.seed_tpl_volumetric_letters_dossier import _variants

        seed_keys = {v["variant_key"] for v in _variants()}
        assert len(seed_keys) == 14
        assert seed_keys == DOSSIER_VARIANT_KEYS

    def test_seed_return_finish_type(self):
        from seeds.seed_tpl_volumetric_letters_dossier import _variants

        rf = next(v for v in _variants() if v["variant_key"] == "return_finish_type")
        assert set(rf["allowed_values"]) == {"white_aluminum", "black_aluminum", "gold_aluminum", "mirror_silver", "ral_paint", "oracal_wrapped"}
        assert rf["default_value"] == "white_aluminum"

    def test_seed_lighting_system_type(self):
        from seeds.seed_tpl_volumetric_letters_dossier import _variants

        ls = next(v for v in _variants() if v["variant_key"] == "lighting_system_type")
        assert set(ls["allowed_values"]) == {"led_modules", "led_strip"}

    def test_seed_emblem_lighting_mode(self):
        from seeds.seed_tpl_volumetric_letters_dossier import _variants

        el = next(v for v in _variants() if v["variant_key"] == "emblem_lighting_mode")
        assert set(el["allowed_values"]) == {"area_lit", "excluded"}
