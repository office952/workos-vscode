"""Unit tests for volumetric execution dispatch helpers."""

from __future__ import annotations

import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.volumetric_execution_dispatch import (  # noqa: E402
    enrich_operation_time_index_from_breakdown,
    extract_order_snapshot_context,
    resolve_execution_task_display_name,
)


class TestVolumetricExecutionDispatch(unittest.TestCase):
    def test_romanian_display_labels_for_volumetric_process_ids(self) -> None:
        self.assertEqual(
            resolve_execution_task_display_name(
                process_id="face_cnc_cut",
                process_type="cnc_routing",
                product_id="TPL-VOLUMETRIC-LETTERS",
            ),
            "Debitare față plexiglas (inclusiv șanfren)",
        )
        self.assertEqual(
            resolve_execution_task_display_name(
                process_id="qc_letters",
                process_type="quality_control",
            ),
            "Verificare finală lucrare",
        )

    def test_enrich_operation_time_index_from_priced_breakdown_line_total(self) -> None:
        breakdown = [
            {
                "component_id": "letters",
                "operations_detail": [
                    {"code": "vector_prep", "estimated_minutes": 0.0, "hours": 0.0, "line_total": 18.0},
                    {"code": "face_cnc_cut", "estimated_minutes": 0.0, "hours": 0.5, "line_total": 40.0},
                ],
            }
        ]
        index = enrich_operation_time_index_from_breakdown({}, breakdown)
        self.assertGreater(index.get("vector_prep", 0), 0)
        self.assertEqual(index.get("face_cnc_cut"), 30.0)

    def test_extract_order_snapshot_context_from_dict_snapshot(self) -> None:
        ctx = extract_order_snapshot_context(
            {
                "product_definition": {
                    "product_id": "TPL-VOLUMETRIC-LETTERS",
                    "product_type": "Litere volumetrice",
                    "layers": [
                        {
                            "layer_id": "layer_1",
                            "material": {"name": "Plexi 3mm"},
                            "finish": "mat",
                            "thickness_mm": 3,
                            "processes": [],
                        }
                    ],
                }
            },
            client_name="Client X",
            quote_code="Q-001",
            intake_code="WI-001",
        )
        self.assertEqual(ctx["client"], "Client X")
        self.assertEqual(ctx["product_template"], "TPL-VOLUMETRIC-LETTERS")
        self.assertEqual(ctx["quote_code"], "Q-001")
        self.assertEqual(ctx["intake_code"], "WI-001")
        self.assertTrue(ctx["work_intake_v2"])
        self.assertEqual(ctx["layer_context"][0]["material"], "Plexi 3mm")


if __name__ == "__main__":
    unittest.main()
