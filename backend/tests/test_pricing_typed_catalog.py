"""Pricing Foundation V1 — typed catalog classification + rate-basis mismatch."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.pricing_typed_catalog import (  # noqa: E402
    RATE_BASIS_MISMATCH_FLAG,
    classify_workcenter_typed_catalog,
    detect_rate_basis_mismatch,
    enrich_workcenter_item,
    machine_family_for_code,
)


class TestTypedCatalogClassification(unittest.TestCase):
    def test_machine_cnc_mechanical(self) -> None:
        self.assertEqual(classify_workcenter_typed_catalog("CNC_ROUTER"), "machine_operation")
        self.assertEqual(classify_workcenter_typed_catalog("ACM_V_GROOVE"), "machine_operation")
        self.assertEqual(machine_family_for_code("CNC_ROUTER"), "cnc_mechanical")

    def test_machine_cnc_laser(self) -> None:
        self.assertEqual(classify_workcenter_typed_catalog("LASER_CUTTING"), "machine_operation")
        self.assertEqual(machine_family_for_code("LASER_CUTTING"), "cnc_laser")

    def test_labor_and_service(self) -> None:
        self.assertEqual(
            classify_workcenter_typed_catalog("FACE_VINYL_APPLICATION_LABOR"), "labor"
        )
        self.assertEqual(classify_workcenter_typed_catalog("LAMINATION"), "service")
        self.assertEqual(
            classify_workcenter_typed_catalog("SITE_INSTALLATION_STANDARD"), "service"
        )

    def test_unknown_fallback(self) -> None:
        self.assertEqual(classify_workcenter_typed_catalog("SOME_FUTURE_CODE"), "unknown")


class TestRateBasisMismatch(unittest.TestCase):
    def test_per_square_meter_with_linear_value(self) -> None:
        flags = detect_rate_basis_mismatch(
            rate_basis="per_square_meter",
            rate_per_hour=None,
            rate_per_linear_meter=15.0,
        )
        self.assertEqual(flags, [RATE_BASIS_MISMATCH_FLAG])

    def test_per_piece_with_linear_value(self) -> None:
        flags = detect_rate_basis_mismatch(
            rate_basis="per_piece",
            rate_per_hour=None,
            rate_per_linear_meter=200.0,
        )
        self.assertEqual(flags, [RATE_BASIS_MISMATCH_FLAG])

    def test_aligned_linear_ok(self) -> None:
        flags = detect_rate_basis_mismatch(
            rate_basis="per_linear_meter",
            rate_per_hour=None,
            rate_per_linear_meter=1.5,
        )
        self.assertEqual(flags, [])

    def test_hour_basis_with_linear_only(self) -> None:
        flags = detect_rate_basis_mismatch(
            rate_basis="per_hour",
            rate_per_hour=None,
            rate_per_linear_meter=10.0,
        )
        self.assertEqual(flags, [RATE_BASIS_MISMATCH_FLAG])

    def test_enrich_preserves_base_cost(self) -> None:
        item = enrich_workcenter_item(
            {
                "pricing_code": "ACM_BOXED_ASSEMBLY",
                "pricing_kind": "operation_rate",
                "base_cost": 15.0,
            },
            rate_basis="per_square_meter",
            rate_per_hour=None,
            rate_per_linear_meter=15.0,
        )
        self.assertEqual(item["base_cost"], 15.0)
        self.assertEqual(item["typed_catalog"], "labor")
        self.assertIn(RATE_BASIS_MISMATCH_FLAG, item["data_quality_flags"])


if __name__ == "__main__":
    unittest.main()
