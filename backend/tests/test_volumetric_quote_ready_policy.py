"""Final commercial quote readiness gate for TPL-VOLUMETRIC-LETTERS."""

from __future__ import annotations

import unittest

from services.volumetric_material_rate_resolver import (
    READINESS_WARNING_PSU_VARIANT_PRICING_READY,
    READINESS_WARNING_VARIANT_PRICING_READY,
)
from services.volumetric_quote_ready_policy import evaluate_volumetric_quote_ready

BASE_QUOTE_INPUT = {
    "width_mm": 4800,
    "height_mm": 600,
    "depth_mm": 60,
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "letter_count": 9,
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
    "paint_tube_count": 3,
    "paint_ral_code": "RAL 9005",
    "mounting_template_area_m2": 2.88,
    "mounting_template_enabled": True,
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
}

READY_DOSSIER = {
    "ready_for_quote": True,
    "technical_readiness": {"status": "ready", "blockers": [], "warnings": []},
    "costengine_readiness": {"status": "ready", "blockers": [], "warnings": []},
    "document_output_readiness": {"status": "ready", "blockers": [], "warnings": []},
    "execution_preparation_readiness": {"status": "ready", "blockers": [], "warnings": []},
}

VECTOR_GATE_SPEC = {
    "vector_file_name": "plan.dwg",
    "vector_file_type": "dwg",
    "vector_analysis_status": "manual_review_approved",
    "vector_manual_review_approved": True,
}


class TestVolumetricQuoteReadyPolicy(unittest.TestCase):
    def test_baseline_simulate_ready_not_quote_ready_without_vector(self) -> None:
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict={**READY_DOSSIER, "ready_for_quote": False},
            cost_blockers=[],
            quote_input=BASE_QUOTE_INPUT,
            product_spec=None,
        )
        self.assertTrue(out.simulate_ready)
        self.assertFalse(out.can_create_commercial_quote)
        self.assertFalse(out.ready_for_quote)
        self.assertIn("letters_vector_file_required", out.blockers)

    def test_mapped_layer_without_manual_review_blocked(self) -> None:
        spec = {
            "vector_file_name": "litere.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "analyzed",
            "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
        }
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=BASE_QUOTE_INPUT,
            product_spec=spec,
        )
        self.assertIn("vector_manual_review_required", out.blockers)
        self.assertFalse(out.can_create_commercial_quote)

    def test_manual_review_and_geometry_can_clear_vector_blockers(self) -> None:
        spec = {
            "vector_file_name": "litere.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "manual_review_approved",
            "vector_manual_review_approved": True,
            "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
        }
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=BASE_QUOTE_INPUT,
            product_spec=spec,
        )
        self.assertNotIn("vector_manual_review_required", out.blockers)
        self.assertTrue(out.can_create_commercial_quote)

    def test_missing_geometry_blocks_final_quote(self) -> None:
        qi = dict(BASE_QUOTE_INPUT)
        qi.pop("letter_face_area_m2")
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=qi,
            product_spec={
                "vector_file_name": "litere.svg",
                "vector_manual_review_approved": True,
                "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
            },
        )
        self.assertIn("quote_input_missing:letter_face_area_m2", out.blockers)
        self.assertFalse(out.can_create_commercial_quote)

    def test_acm_panel_blocks_final_quote(self) -> None:
        qi = {**BASE_QUOTE_INPUT, "mounting_system": "acm_panel"}
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=qi,
            product_spec={
                "vector_manual_review_approved": True,
                "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
            },
        )
        self.assertTrue(any("captured_option_requires_separate_template" in b for b in out.blockers))

    def test_oracal_missing_metadata_blocks_final_quote(self) -> None:
        qi = {**BASE_QUOTE_INPUT, "face_finish_type": "oracal_651"}
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=qi,
            product_spec={
                "vector_manual_review_approved": True,
                "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
            },
        )
        self.assertIn("production_metadata_missing:face_vinyl_color_code", out.blockers)
        self.assertFalse(out.can_create_commercial_quote)

    def test_ral_missing_when_paint_tubes_blocks_final_quote(self) -> None:
        qi = {
            **BASE_QUOTE_INPUT,
            "volume_finish": "paint_after_face_miter_bond",
        }
        qi.pop("paint_ral_code")
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=qi,
            product_spec={
                "vector_manual_review_approved": True,
                "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
                "volume_finish": "paint_after_face_miter_bond",
            },
        )
        self.assertIn("production_metadata_missing:paint_ral_code", out.blockers)
        self.assertFalse(out.can_create_commercial_quote)

    def test_stale_paint_tubes_do_not_block_stock_cant_final_quote(self) -> None:
        qi = {**BASE_QUOTE_INPUT}
        qi.pop("paint_ral_code")
        qi["volume_finish"] = "none"
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=qi,
            product_spec={
                "vector_manual_review_approved": True,
                "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
                "volume_finish": "none",
                "return_color": "white",
            },
        )
        self.assertNotIn("production_metadata_missing:paint_ral_code", out.blockers)

    def test_warning_only_needs_review_allows_commercial_quote(self) -> None:
        """Category B warnings must not hard-block when quote_input is complete."""
        readiness = {
            **READY_DOSSIER,
            "overall_status": "needs_review",
            "ready_for_quote": False,
            "technical_readiness": {
                "status": "needs_review",
                "blockers": [],
                "warnings": [
                    "vector_analysis_pending",
                    READINESS_WARNING_VARIANT_PRICING_READY,
                    READINESS_WARNING_PSU_VARIANT_PRICING_READY,
                ],
            },
            "costengine_readiness": {
                "status": "needs_review",
                "blockers": [],
                "warnings": [
                    "volumetric_profile_return_depth_required_at_quote:MAT-PROFIL-LATERAL-LITERE",
                    "volumetric_psu_wattage_required_at_quote:MAT-LED-PSU-12V",
                ],
            },
        }
        spec = {
            "vector_file_name": "litere.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "manual_review_approved",
            "vector_manual_review_approved": True,
            "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
        }
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=readiness,
            cost_blockers=[],
            quote_input=BASE_QUOTE_INPUT,
            product_spec=spec,
        )
        self.assertTrue(out.can_create_commercial_quote)
        self.assertTrue(out.ready_for_quote)
        self.assertNotIn("technical_readiness:needs_review", out.blockers)
        self.assertNotIn("ready_for_quote:false", out.blockers)
        self.assertFalse(out.requires_acknowledgement)

    def test_unacknowledged_non_satisfied_warning_requires_acknowledgement(self) -> None:
        readiness = {
            **READY_DOSSIER,
            "overall_status": "needs_review",
            "technical_readiness": {
                "status": "needs_review",
                "blockers": [],
                "warnings": ["operations_missing"],
            },
            "costengine_readiness": {"status": "ready", "blockers": [], "warnings": []},
        }
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=readiness,
            cost_blockers=[],
            quote_input=BASE_QUOTE_INPUT,
            product_spec={
                "vector_file_name": "litere.svg",
                "vector_file_type": "svg",
                "vector_analysis_status": "manual_review_approved",
                "vector_manual_review_approved": True,
                "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
            },
        )
        self.assertTrue(out.can_create_commercial_quote)
        self.assertTrue(out.requires_acknowledgement)
        self.assertIn("operations_missing", out.classified.get("acknowledgement_pending", []))

    def test_section_blocker_still_blocks_commercial_quote(self) -> None:
        readiness = {
            **READY_DOSSIER,
            "overall_status": "blocked",
            "technical_readiness": {
                "status": "blocked",
                "blockers": ["template_inactive"],
                "warnings": [],
            },
            "costengine_readiness": {"status": "ready", "blockers": [], "warnings": []},
        }
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=False,
            readiness_dict=readiness,
            cost_blockers=[],
            quote_input=BASE_QUOTE_INPUT,
            product_spec={
                "vector_manual_review_approved": True,
                "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
            },
        )
        self.assertFalse(out.can_create_commercial_quote)
        self.assertIn("template_inactive", out.blockers)

    def test_non_illuminated_without_psu_not_blocked(self) -> None:
        qi = {
            **BASE_QUOTE_INPUT,
            "illumination_type": "non_illuminated",
            "lighting_system_type": "none",
        }
        qi.pop("selected_psu_watts", None)
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=qi,
            product_spec=VECTOR_GATE_SPEC,
        )
        self.assertNotIn("quote_input_missing:selected_psu_watts", out.blockers)
        self.assertTrue(out.can_create_commercial_quote)

    def test_illuminated_without_psu_blocked(self) -> None:
        qi = {
            **BASE_QUOTE_INPUT,
            "illumination_type": "frontlit",
            "lighting_system_type": "led_modules",
        }
        qi.pop("selected_psu_watts", None)
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=qi,
            product_spec=VECTOR_GATE_SPEC,
        )
        self.assertIn("quote_input_missing:selected_psu_watts", out.blockers)
        self.assertFalse(out.can_create_commercial_quote)

    def test_illuminated_with_psu_ready(self) -> None:
        qi = {
            **BASE_QUOTE_INPUT,
            "illumination_type": "frontlit",
            "lighting_system_type": "led_modules",
            "selected_psu_watts": 100,
        }
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=qi,
            product_spec=VECTOR_GATE_SPEC,
        )
        self.assertNotIn("quote_input_missing:selected_psu_watts", out.blockers)
        self.assertTrue(out.can_create_commercial_quote)

    def test_non_volumetric_template_not_affected(self) -> None:
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-ACM-PANEL",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=BASE_QUOTE_INPUT,
        )
        self.assertIn("not_volumetric_template", out.notes)
        self.assertFalse(out.can_create_commercial_quote)

    def test_support_bars_only_blocks_letters_gate(self) -> None:
        spec = {
            "vector_file_name": "bari.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "analyzed",
            "svg_layer_mappings": {"Layer_Bare": "support_bars"},
        }
        out = evaluate_volumetric_quote_ready(
            template_code="TPL-VOLUMETRIC-LETTERS",
            template_active=True,
            readiness_dict=READY_DOSSIER,
            cost_blockers=[],
            quote_input=BASE_QUOTE_INPUT,
            product_spec=spec,
        )
        self.assertIn("vector_layer_mapping_pending", out.blockers)
        self.assertFalse(out.can_create_commercial_quote)


if __name__ == "__main__":
    unittest.main()
