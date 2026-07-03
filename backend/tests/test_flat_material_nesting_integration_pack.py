"""Flat material nesting integration pack — profile resolver, Forex, summary, offcut."""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.flat_material_nesting_summary_service import build_flat_material_nesting_summary  # noqa: E402
from services.flat_material_offcut_foundation import (  # noqa: E402
    INVENTORY_INTAKE_STATUS,
    normalize_offcut_measurement_payload,
    sheet_nesting_requires_offcut_measurement,
    validate_offcut_measurement_payload,
)
from services.flat_material_profile_resolver import (  # noqa: E402
    SOURCE_DEFAULT_INTERNAL,
    SOURCE_MATERIAL_REGISTRY,
    SOURCE_QUOTE_INPUT,
    resolve_sheet_material_profile,
)
from services.volumetric_face_vinyl_service import build_face_vinyl_handoff_for_quote  # noqa: E402
from services.volumetric_forex_backing_nesting_service import (  # noqa: E402
    build_forex_backing_nesting_for_quote,
)
from services.volumetric_plexiglass_face_nesting_service import (  # noqa: E402
    build_plexiglass_face_nesting_for_quote,
    resolve_plexiglass_face_profile,
)
from tests.test_volumetric_finish_mounting_pricing import BASE_QUOTE_INPUT  # noqa: E402

_FOUR_BOXES = [
    {"piece_id": f"L{i}", "width_mm": 600, "height_mm": 400, "source": "svg_layer_mapped"}
    for i in range(1, 5)
]

_MINIMAL_QI = {
    "face_finish_type": "oracal_651",
    "face_vinyl_roll_width_mm": 1260,
    "face_vinyl_color_code": "651-020",
}

_FACE_VINYL_QI = {**BASE_QUOTE_INPUT, **_MINIMAL_QI}

_ROLL_FORBIDDEN = (
    "nested_roll_length_m",
    "recommended_roll_length_m",
    "material_width_m",
    "roll_width_mm",
)


def _serialize_wrapper(**kwargs) -> dict:
    from routers.quotes import _serialize_quote_line_items

    snapshot = {
        "status": "priced",
        "price": {"net": 100.0, "gross": 119.0, "final": 119.0},
        "pricing": {"margin_pct": 0, "discount_pct": 0, "vat_pct": 19},
    }
    return json.loads(_serialize_quote_line_items(snapshot, **kwargs))


def _assert_no_roll_fields(obj: dict, path: str = "") -> None:
    for key, value in obj.items():
        full = f"{path}.{key}" if path else key
        assert key not in _ROLL_FORBIDDEN, f"unexpected roll field at {full}"
        if isinstance(value, dict):
            _assert_no_roll_fields(value, full)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _assert_no_roll_fields(item, full)


class TestSheetProfileResolver(unittest.TestCase):
    def test_quote_input_override(self) -> None:
        qi = {"plexiglass_sheet_width_mm": 3000, "plexiglass_sheet_height_mm": 2000}
        res = resolve_sheet_material_profile(
            "PLEXI_FACE_3MM",
            quote_input=qi,
            role="plexiglass_face",
        )
        self.assertEqual(res.source, SOURCE_QUOTE_INPUT)
        self.assertFalse(res.is_default_fallback)
        self.assertEqual(res.sheet_width_mm, 3000)

    def test_registry_row_used(self) -> None:
        row = {
            "code": "MAT-PLEXI-TRANSP-3MM",
            "name": "Plexiglas transparent 3mm",
            "sheet_width": 3050,
            "sheet_height": 2030,
            "usable_width": 3000,
            "usable_height": 1980,
            "sheet_thickness": 3,
        }
        res = resolve_sheet_material_profile(
            "PLEXI_FACE_3MM",
            role="plexiglass_face",
            registry_row=row,
        )
        self.assertEqual(res.source, SOURCE_MATERIAL_REGISTRY)
        self.assertFalse(res.is_default_fallback)
        self.assertEqual(res.usable_width_mm, 3000)

    def test_default_fallback_warning(self) -> None:
        res = resolve_sheet_material_profile("PLEXI_FACE_3MM", role="plexiglass_face")
        self.assertTrue(res.is_default_fallback)
        self.assertEqual(res.source, SOURCE_DEFAULT_INTERNAL)
        self.assertIn("missing_sheet_profile_in_registry", res.warnings)


class TestPlexiglassRemainingFields(unittest.TestCase):
    def test_remaining_not_waste_primary(self) -> None:
        block = build_plexiglass_face_nesting_for_quote(
            _FACE_VINYL_QI,
            product_spec={"letter_bounding_boxes": _FOUR_BOXES},
        )
        nesting = block["nesting"]
        self.assertIn("remaining_area_m2", nesting)
        self.assertIn("remaining_percent", nesting)
        self.assertEqual(nesting["remaining_policy"], "estimated_sheet_remainder_reusable")
        self.assertAlmostEqual(nesting["remaining_area_m2"], nesting["waste_area_m2"], places=6)
        self.assertIsNone(nesting.get("nested_roll_length_m"))
        _assert_no_roll_fields(block)

    def test_profile_source_in_material(self) -> None:
        block = build_plexiglass_face_nesting_for_quote(
            _FACE_VINYL_QI,
            product_spec={"letter_bounding_boxes": _FOUR_BOXES},
        )
        self.assertIn("source", block["material"])
        self.assertIn("is_default_fallback", block["material"])


class TestForexBackingNesting(unittest.TestCase):
    def test_enabled_sheet_nesting(self) -> None:
        block = build_forex_backing_nesting_for_quote(
            _FACE_VINYL_QI,
            product_spec={"letter_bounding_boxes": _FOUR_BOXES},
        )
        self.assertTrue(block["enabled"])
        self.assertEqual(block["material"]["material_type"], "sheet")
        self.assertEqual(block["material"]["material_code"], "FOREX_BACKING_10MM")
        nesting = block["nesting"]
        self.assertEqual(nesting["method"], "sheet_rectangular")
        self.assertEqual(nesting["sheets_used"], 1)
        self.assertAlmostEqual(nesting["used_piece_bbox_area_m2"], 0.96, places=3)
        self.assertIn("remaining_area_m2", nesting)
        self.assertEqual(
            block["geometry"]["geometry_assumption"],
            "same_as_letter_face_bbox",
        )
        _assert_no_roll_fields(block)


class TestTripleHandoffQuote(unittest.TestCase):
    def test_vinyl_plexi_forex_separate(self) -> None:
        spec = {"letter_bounding_boxes": _FOUR_BOXES}
        vinyl = build_face_vinyl_handoff_for_quote(_FACE_VINYL_QI, product_spec=spec)
        plexi = build_plexiglass_face_nesting_for_quote(_FACE_VINYL_QI, product_spec=spec)
        forex = build_forex_backing_nesting_for_quote(_FACE_VINYL_QI, product_spec=spec)
        summary = build_flat_material_nesting_summary(
            face_vinyl_handoff=vinyl,
            plexiglass_face_nesting=plexi,
            forex_backing_nesting=forex,
        )

        wrapper = _serialize_wrapper(
            quote_input=_FACE_VINYL_QI,
            product_spec_json=spec,
            face_vinyl_handoff=vinyl,
            plexiglass_face_nesting=plexi,
            forex_backing_nesting=forex,
            flat_material_nesting_summary=summary,
            real_offcut_measurement_required=True,
        )
        self.assertIn("face_vinyl_handoff", wrapper)
        self.assertIn("plexiglass_face_nesting", wrapper)
        self.assertIn("forex_backing_nesting", wrapper)
        self.assertNotIn("forex_backing_nesting", wrapper["plexiglass_face_nesting"])

        v_nest = wrapper["face_vinyl_handoff"]["nesting"]
        self.assertIsNotNone(v_nest.get("nested_roll_length_m"))
        for sheet_key in ("plexiglass_face_nesting", "forex_backing_nesting"):
            _assert_no_roll_fields(wrapper[sheet_key])
            self.assertIsNotNone(wrapper[sheet_key]["nesting"].get("sheets_used"))

        self.assertEqual(len(summary["roll_materials"]), 1)
        self.assertEqual(len(summary["sheet_materials"]), 2)
        self.assertTrue(summary["real_offcut_measurement_required"])


class TestOrderHandoffPreservation(unittest.TestCase):
    def test_extract_keys(self) -> None:
        spec = {"letter_bounding_boxes": _FOUR_BOXES}
        plexi = build_plexiglass_face_nesting_for_quote(_FACE_VINYL_QI, product_spec=spec)
        forex = build_forex_backing_nesting_for_quote(_FACE_VINYL_QI, product_spec=spec)
        wrapper = _serialize_wrapper(
            quote_input=_FACE_VINYL_QI,
            plexiglass_face_nesting=plexi,
            forex_backing_nesting=forex,
        )
        handoff = {
            k: wrapper[k]
            for k in (
                "face_vinyl_handoff",
                "plexiglass_face_nesting",
                "forex_backing_nesting",
            )
            if k in wrapper
        }
        self.assertIn("plexiglass_face_nesting", handoff)
        self.assertIn("forex_backing_nesting", handoff)


class TestSummaryTerminology(unittest.TestCase):
    def test_summary_has_remaining_fields(self) -> None:
        spec = {"letter_bounding_boxes": _FOUR_BOXES}
        summary = build_flat_material_nesting_summary(
            plexiglass_face_nesting=build_plexiglass_face_nesting_for_quote(
                _FACE_VINYL_QI,
                product_spec=spec,
            ),
            forex_backing_nesting=build_forex_backing_nesting_for_quote(
                _FACE_VINYL_QI,
                product_spec=spec,
            ),
        )
        for entry in summary["sheet_materials"]:
            if entry.get("enabled"):
                self.assertIn("remaining_area_m2", entry)
                self.assertIn("remaining_percent", entry)
                self.assertTrue(entry["real_offcut_measurement_required"])

    def test_sheet_source_selection_foundation_metadata(self) -> None:
        spec = {"letter_bounding_boxes": _FOUR_BOXES}
        summary = build_flat_material_nesting_summary(
            face_vinyl_handoff=build_face_vinyl_handoff_for_quote(
                _FACE_VINYL_QI,
                product_spec=spec,
            ),
            plexiglass_face_nesting=build_plexiglass_face_nesting_for_quote(
                _FACE_VINYL_QI,
                product_spec=spec,
            ),
            forex_backing_nesting=build_forex_backing_nesting_for_quote(
                _FACE_VINYL_QI,
                product_spec=spec,
            ),
        )
        selections = summary.get("sheet_source_selection") or []
        self.assertGreaterEqual(len(selections), 1)
        plexi = next(row for row in selections if row.get("role") == "plexiglass_face")
        self.assertEqual(plexi["status"], "foundation_only")
        self.assertFalse(plexi["inventory_offcuts_available"])
        self.assertEqual(plexi["current_estimate_basis"], "new_sheet_profile")


class TestOffcutFoundation(unittest.TestCase):
    def test_required_when_sheet_nesting_enabled(self) -> None:
        block = build_plexiglass_face_nesting_for_quote(
            _FACE_VINYL_QI,
            product_spec={"letter_bounding_boxes": _FOUR_BOXES},
        )
        self.assertTrue(sheet_nesting_requires_offcut_measurement(block))

    def test_not_required_vinyl_only(self) -> None:
        vinyl = build_face_vinyl_handoff_for_quote(
            _FACE_VINYL_QI,
            product_spec={"letter_bounding_boxes": _FOUR_BOXES},
        )
        self.assertFalse(sheet_nesting_requires_offcut_measurement(vinyl))

    def test_offcut_payload_contract(self) -> None:
        payload = {
            "order_id": 123,
            "task_id": "T-001",
            "material_code": "PLEXI_FACE_3MM",
            "source_nesting_role": "plexiglass_face",
            "offcuts": [{"width_mm": 1200, "height_mm": 700, "quantity": 1}],
        }
        ok, errors = validate_offcut_measurement_payload(payload)
        self.assertTrue(ok)
        self.assertEqual(errors, [])
        normalized = normalize_offcut_measurement_payload(payload)
        self.assertAlmostEqual(normalized["offcuts"][0]["area_m2"], 0.84, places=3)

    def test_inventory_deferred_marker(self) -> None:
        self.assertEqual(INVENTORY_INTAKE_STATUS, "deferred")


class TestResolvePlexiglassProfileCompat(unittest.TestCase):
    def test_default_profile_marked_internal(self) -> None:
        profile, source, display, is_fallback = resolve_plexiglass_face_profile(
            _FACE_VINYL_QI,
            {},
        )
        self.assertEqual(source, SOURCE_DEFAULT_INTERNAL)
        self.assertTrue(is_fallback)
        self.assertEqual(profile.sheet_width_mm, 3050)
        self.assertIn("mm", display)


if __name__ == "__main__":
    unittest.main()
