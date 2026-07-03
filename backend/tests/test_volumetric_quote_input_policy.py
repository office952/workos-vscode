"""TPL-VOLUMETRIC-LETTERS — captured-but-unpriced quote_input warnings."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.volumetric_quote_input_policy import (  # noqa: E402
    WARNING_ACM_SEPARATE_TEMPLATE,
    WARNING_MOUNTING_BAR_PROFILE_PRICE_MISSING,
    WARNING_MOUNTING_LABOR_NOT_PRICED,
    WARNING_ORACAL_8500_PRICED_AS_651,
    WARNING_PRODUCTION_METADATA_MISSING,
    collect_volumetric_captured_unpriced_warnings,
    normalize_face_finish_type,
    normalize_mounting_bar_profile,
    normalize_mounting_system,
    normalize_mounting_template_enabled,
)


class TestVolumetricQuoteInputPolicy(unittest.TestCase):
    def test_defaults_emit_no_warnings(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {
                "face_finish_type": "none",
                "mounting_system": "direct_wall",
                "mounting_template_enabled": True,
            },
        )
        self.assertEqual(warnings, [])

    def test_steel_priced_profile_labor_warning_only(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "30x30x1.5",
            },
        )
        self.assertEqual(
            warnings,
            [f"{WARNING_MOUNTING_LABOR_NOT_PRICED}:mounting_system=steel_bars"],
        )

    def test_unknown_steel_profile_price_missing(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "40x40x2",
            },
        )
        self.assertEqual(
            warnings,
            [f"{WARNING_MOUNTING_BAR_PROFILE_PRICE_MISSING}:steel:40x40x2"],
        )

    def test_acm_panel_separate_template_warning(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {"mounting_system": "acm_panel"},
        )
        self.assertEqual(
            warnings,
            [f"{WARNING_ACM_SEPARATE_TEMPLATE}:mounting_system=acm_panel"],
        )

    def test_oracal_metadata_warnings_when_finish_selected(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {"face_finish_type": "oracal_651"},
        )
        self.assertIn(
            f"{WARNING_PRODUCTION_METADATA_MISSING}:face_vinyl_color_code",
            warnings,
        )
        self.assertIn(
            f"{WARNING_PRODUCTION_METADATA_MISSING}:face_vinyl_roll_width_mm",
            warnings,
        )

    def test_oracal_8500_subtype_warning(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {
                "face_finish_type": "oracal_651",
                "face_finish_subtype": "oracal_8500",
                "face_vinyl_color_code": "731",
                "face_vinyl_roll_width_mm": 1000,
            },
        )
        self.assertIn(WARNING_ORACAL_8500_PRICED_AS_651, warnings)

    def test_paint_ral_warning_when_tubes_present_and_paint_mode(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {
                "face_finish_type": "none",
                "paint_tube_count": 3,
                "volume_finish": "paint_after_face_miter_bond",
            },
        )
        self.assertIn(
            f"{WARNING_PRODUCTION_METADATA_MISSING}:paint_ral_code",
            warnings,
        )

    def test_no_paint_ral_warning_for_stock_cant_with_stale_tubes(self) -> None:
        warnings = collect_volumetric_captured_unpriced_warnings(
            "TPL-VOLUMETRIC-LETTERS",
            {"face_finish_type": "none", "paint_tube_count": 3, "volume_finish": "none"},
        )
        self.assertNotIn(
            f"{WARNING_PRODUCTION_METADATA_MISSING}:paint_ral_code",
            warnings,
        )

    def test_normalizers(self) -> None:
        self.assertEqual(normalize_mounting_bar_profile("30X30X1.5"), "30x30x1.5")
        self.assertEqual(normalize_face_finish_type(None), "none")
        self.assertEqual(normalize_mounting_system("forex_template"), "direct_wall")
        self.assertTrue(normalize_mounting_template_enabled(None))


if __name__ == "__main__":
    unittest.main()
