from __future__ import annotations

import json
import os
import sys
import unittest
from types import SimpleNamespace

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.execution_plan_gate_service import CANONICAL_TASK_TYPES, RegistrySnapshot, evaluate_gate  # noqa: E402
from services.execution_plan_service import ExecutionPlanService  # noqa: E402
from services.intake_v6_quote_to_order_service import (  # noqa: E402
    _build_v6_order_snapshot_payload,
    _extract_quote_snapshot_for_order,
)


def _quote_wrapper_with_canonical_snapshot() -> str:
    return json.dumps(
        {
            "line_items": {
                "product_definition": {
                    "product_id": "TPL-VOLUMETRIC-LETTERS_v2",
                    "product_type": "Litere volumetrice",
                    "quantity": 10,
                    "dimensions": {"width_mm": 4800, "height_mm": 600, "depth_mm": 60},
                    "layers": [
                        {
                            "layer_id": "layer_1",
                            "layer_type": "structure",
                            "material": {"material_id": "MAT-1", "name": "Material", "unit": "sqm"},
                            "thickness_mm": 3,
                            "finish": "",
                            "components": [],
                            "processes": [
                                {
                                    "process_id": "vector_prep",
                                    "type": "prepress",
                                    "machine_type": "PREPRESS",
                                    "estimated_time_minutes": 18,
                                },
                                {
                                    "process_id": "assembly_letters",
                                    "type": "assembly",
                                    "machine_type": "ASSEMBLY",
                                    "estimated_time_minutes": 600,
                                },
                            ],
                        }
                    ],
                },
                "cost_result": {
                    "is_valid": True,
                    "currency": "EUR",
                    "materials_cost": 100,
                    "labour_cost": 200,
                    "machine_cost": 50,
                    "external_cost": 0,
                    "overhead_cost": 10,
                    "total_cost": 360,
                    "estimated_time_minutes": 750,
                    "breakdown": [],
                    "validation": {"missing_cost_data": [], "warnings": []},
                },
                "pricing": {"margin_pct": 25, "discount_pct": 0, "vat_pct": 19},
                "price": {"net": 1000, "gross": 1190, "final": 1190},
                "status": "priced",
                "blocked_reasons": [],
                "template_id": 7,
                "readiness_result": {},
            },
            "revision_source": {
                "legacy_reconstructed": True,
            },
            "quote_input": {"vector_file": "demo.svg"},
        }
    )


class TestIntakeV6OrderSnapshotPayload(unittest.TestCase):
    def test_extract_quote_snapshot_accepts_wrapper_with_revision_source(self):
        quote = SimpleNamespace(line_items=_quote_wrapper_with_canonical_snapshot())

        snapshot = _extract_quote_snapshot_for_order(quote)

        self.assertIsInstance(snapshot, dict)
        self.assertIn("product_definition", snapshot)
        self.assertIn("cost_result", snapshot)
        self.assertEqual(snapshot["product_definition"]["product_id"], "TPL-VOLUMETRIC-LETTERS_v2")

    def test_build_v6_order_snapshot_payload_normalizes_process_types(self):
        quote = SimpleNamespace(
            id=14,
            code="Q-V6-IV6-TEST",
            intake_code="IV6-TEST",
            line_items=_quote_wrapper_with_canonical_snapshot(),
        )
        linkage = {
            "source_workspace_id": "workspace-123",
            "source_workspace_code": "IV6-TEST",
            "snapshot": {
                "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                "workspace_payload_snapshot": {"product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS_v2"}},
                "quote_input_payload": {"vector_file": "demo.svg"},
            },
        }

        payload = _build_v6_order_snapshot_payload(
            quote,
            linkage,
            currency_handoff={"base_currency": "RON", "commercial_currency": "EUR"},
            final_price={"net": 1000, "gross": 1190, "commercial_currency": "EUR"},
            handoff_snapshots={},
            workspace_hash="hash-123",
        )

        self.assertIn("product_definition", payload)
        self.assertIn("cost_result", payload)
        self.assertEqual(payload["source_module"], "intake_v6")
        self.assertEqual(payload["template_code"], "TPL-VOLUMETRIC-LETTERS_v2")

        process_types = {
            process["type"]
            for layer in payload["product_definition"]["layers"]
            for process in layer["processes"]
        }
        self.assertTrue(process_types.issubset(CANONICAL_TASK_TYPES), process_types)
        self.assertIn("file_preparation", process_types)
        self.assertIn("volumetric_letter_assembly", process_types)

    def test_built_v6_order_snapshot_passes_gate_and_generates_plan(self):
        quote = SimpleNamespace(
            id=14,
            code="Q-V6-IV6-TEST",
            intake_code="IV6-TEST",
            line_items=_quote_wrapper_with_canonical_snapshot(),
        )
        linkage = {
            "source_workspace_id": "workspace-123",
            "source_workspace_code": "IV6-TEST",
            "snapshot": {
                "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                "workspace_payload_snapshot": {"product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS_v2"}},
                "quote_input_payload": {"vector_file": "demo.svg"},
            },
        }

        payload = _build_v6_order_snapshot_payload(
            quote,
            linkage,
            currency_handoff={"base_currency": "RON", "commercial_currency": "EUR"},
            final_price={"net": 1000, "gross": 1190, "commercial_currency": "EUR"},
            handoff_snapshots={},
            workspace_hash="hash-123",
        )
        payload["order_id"] = 77
        row = SimpleNamespace(
            id=77,
            code="ORD-IV6-TEST",
            snapshot_version=1,
            snapshot_line_items=json.dumps(payload),
        )
        registries = RegistrySnapshot(
            skills=None,
            workcenters=None,
            roles=None,
            product_system_available=False,
            materials_registry_available=False,
            machines_registry_available=False,
        )

        evaluation = evaluate_gate(row, registries, plan_already_exists=False)

        self.assertTrue(evaluation.can_generate, evaluation.blockers)
        self.assertEqual([], [b for b in evaluation.blockers if b.get("code") == "BLK-08"])

        plan = ExecutionPlanService().from_order(row)
        self.assertGreater(len(plan.tasks), 0)
        self.assertTrue(all(task.process_type in CANONICAL_TASK_TYPES | {"produce_order"} for task in plan.tasks))


if __name__ == "__main__":
    unittest.main()