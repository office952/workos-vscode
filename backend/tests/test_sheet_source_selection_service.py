"""Sheet source selection foundation tests — no inventory writes."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.sheet_source_selection_service import (  # noqa: E402
    build_sheet_source_candidates,
    build_sheet_source_selection_summary,
    select_sheet_sources_for_pieces,
)


class TestSheetSourceSelectionService(unittest.TestCase):
    def test_fallback_new_sheet_when_no_offcuts(self) -> None:
        summary = build_sheet_source_selection_summary(
            material_code="PLEXI_FACE_3MM",
            thickness_mm=3.0,
            pieces=[{"width_mm": 480, "height_mm": 380}],
            material_profile={"sheet_width_mm": 3050, "sheet_height_mm": 2030, "source": "material_profile"},
        )
        self.assertEqual(summary["status"], "foundation_only")
        self.assertFalse(summary["inventory_offcuts_available"])
        self.assertEqual(summary["current_estimate_basis"], "new_sheet_profile")
        self.assertEqual(summary["inventory_integration_status"], "deferred")
        self.assertTrue(any(c["source_type"] == "new_sheet" for c in summary["source_candidates"]))

    def test_selects_offcut_when_mock_fits(self) -> None:
        pieces = [{"width_mm": 400, "height_mm": 300}]
        candidates = build_sheet_source_candidates(
            material_code="PLEXI_FACE_3MM",
            thickness_mm=3.0,
            inventory_offcuts=[
                {
                    "inventory_item_id": "OFFCUT-001",
                    "material_code": "PLEXI_FACE_3MM",
                    "width_mm": 1300,
                    "height_mm": 850,
                    "thickness_mm": 3,
                    "condition": "usable",
                    "location": "raft plexiglas",
                }
            ],
            material_profile={"sheet_width_mm": 3050, "sheet_height_mm": 2030},
        )
        selection = select_sheet_sources_for_pieces(pieces, candidates)
        self.assertTrue(selection["inventory_offcuts_available"])
        self.assertEqual(selection["current_estimate_basis"], "inventory_offcut")
        self.assertEqual(selection["selected_sources"][0]["source_type"], "inventory_offcut")

    def test_new_sheet_when_offcut_insufficient(self) -> None:
        pieces = [{"width_mm": 2000, "height_mm": 1500}]
        candidates = build_sheet_source_candidates(
            material_code="PLEXI_FACE_3MM",
            thickness_mm=3.0,
            inventory_offcuts=[
                {"inventory_item_id": "OFFCUT-001", "width_mm": 1300, "height_mm": 850}
            ],
            material_profile={"sheet_width_mm": 3050, "sheet_height_mm": 2030},
        )
        selection = select_sheet_sources_for_pieces(pieces, candidates)
        self.assertEqual(selection["selected_sources"][-1]["source_type"], "new_sheet")


if __name__ == "__main__":
    unittest.main()
