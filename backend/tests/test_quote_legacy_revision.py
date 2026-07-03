"""Tests for on-demand legacy revision source reconstruction."""

from __future__ import annotations

import json
import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.quote_legacy_revision import (  # noqa: E402
    build_legacy_revision_source_from_snapshot,
    collect_template_quote_input_keys,
    extract_snapshot_from_line_items,
)


def _simple_template() -> dict:
    return {
        "id": 1,
        "template_code": "TOTEM-STD",
        "components_json": json.dumps(["Cadru"]),
        "operations_json": json.dumps(
            [{"code": "ASM", "name": "Asamblare", "estimatedMinutes": 30}]
        ),
        "required_materials_json": json.dumps([]),
        "active": True,
    }


def _legacy_snapshot(template_id: int = 1) -> dict:
    return {
        "template_id": template_id,
        "product_definition": {
            "product_id": "TOTEM-STD",
            "quantity": 2,
            "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300},
        },
        "pricing": {"margin_pct": 25.0, "discount_pct": 0.0, "vat_pct": 19.0},
        "cost_result": {"total_cost": 80.0, "breakdown": []},
        "price": {"net": 100.0, "gross": 119.0},
        "status": "priced",
    }


class TestQuoteLegacyRevisionHelpers(unittest.TestCase):
    def test_extract_snapshot_from_wrapper_without_revision_source(self) -> None:
        raw = json.dumps({"line_items": _legacy_snapshot()})
        snap = extract_snapshot_from_line_items(raw)
        self.assertIsNotNone(snap)
        self.assertEqual(snap["template_id"], 1)

    def test_reconstructs_simple_legacy_snapshot(self) -> None:
        result = build_legacy_revision_source_from_snapshot(
            snapshot=_legacy_snapshot(),
            product_template=_simple_template(),
            margin_pct=25,
            discount_pct=0,
            vat_pct=19,
        )
        self.assertTrue(result.ok)
        self.assertTrue(result.legacy_reconstructed)
        self.assertIn("product_template", result.source or {})
        self.assertIn("user_config", result.source or {})
        self.assertEqual(result.source["user_config"]["quantity"], 2)

    def test_blocks_when_template_requires_quote_input(self) -> None:
        tpl = _simple_template()
        tpl["operations_json"] = json.dumps(
            [
                {
                    "code": "PAINT",
                    "requires_quote_input": ["paint_tube_count"],
                }
            ]
        )
        result = build_legacy_revision_source_from_snapshot(
            snapshot=_legacy_snapshot(),
            product_template=tpl,
            margin_pct=25,
            discount_pct=0,
            vat_pct=19,
        )
        self.assertFalse(result.ok)
        self.assertIn("quote_input", result.missing_fields)

    def test_blocks_when_dimensions_missing(self) -> None:
        snap = _legacy_snapshot()
        snap["product_definition"]["dimensions"] = {}
        result = build_legacy_revision_source_from_snapshot(
            snapshot=snap,
            product_template=_simple_template(),
            margin_pct=25,
            discount_pct=0,
            vat_pct=19,
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("dimensions" in f for f in result.missing_fields))

    def test_collect_template_quote_input_keys(self) -> None:
        tpl = _simple_template()
        tpl["operations_json"] = json.dumps(
            [{"requires_quote_input": ["led_count", "depth_mm"]}]
        )
        keys = collect_template_quote_input_keys(tpl)
        self.assertEqual(keys, {"led_count", "depth_mm"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
