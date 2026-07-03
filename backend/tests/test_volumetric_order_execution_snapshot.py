"""
BUILD-EXECUTION-SNAPSHOT-FROM-VOLUMETRIC-QUOTE — contract tests.

Proves quote-derived volumetric orders carry canonical execution process types
and pass the execution plan gate / plan generation without weakening validation.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from data_models.product_contracts import (  # noqa: E402
    CostResult,
    CostValidation,
    OrderFinalPrice,
    ProductDefinition,
    ProductDimensions,
    ProductLayer,
    ProductMaterial,
    ProductProcess,
    QuoteCalculationSnapshot,
    QuotePrice,
    QuotePricing,
)
from services.execution_plan_gate_service import (  # noqa: E402
    CANONICAL_TASK_TYPES,
    RegistrySnapshot,
    evaluate_gate,
)
from services.execution_plan_service import ExecutionPlanService  # noqa: E402
from services.order_execution_snapshot_mapper import (  # noqa: E402
    normalize_product_definition_for_execution,
    resolve_canonical_task_type,
)
from services.order_snapshot_service import OrderSnapshotService  # noqa: E402
from tests.test_execution_flow import _complete_snapshot_dict  # noqa: E402


def _volumetric_quote_layers_noncanonical() -> list:
    """Mimics ProductSystem _build_layers output for TPL-VOLUMETRIC-LETTERS."""
    ops = [
        ("vector_prep", "prepress", 0.0),
        ("face_cnc_cut", "cnc", 0.0),
        ("vinyl_application", "vinyl_application", 0.0),
        ("side_forming", "return_profile_machine_forming", 0.0),
        ("return_face_bonding", "return_profile_face_bonding", 0.0),
        ("back_cut", "cnc", 0.0),
        ("led_install_letters", "assembly", 0.0),
        ("electrical_letters", "wiring", 0.0),
        ("mounting_template_cnc_cut", "cnc", 0.0),
        ("painting", "painting", 0.0),
        ("assembly_letters", "assembly", 60.0),
        ("qc_letters", "qc_inspection", 15.0),
        ("packaging_letters", "packaging", 0.0),
    ]
    return [
        ProductLayer(
            layer_id="layer_1",
            layer_type="structure",
            material=ProductMaterial(material_id="MAT-ACP-FATA-LITERE", name="Face", unit="sqm"),
            thickness_mm=3,
            finish="",
            components=[],
            processes=[
                ProductProcess(
                    process_id=code,
                    type=legacy,
                    machine_type="WC",
                    estimated_time_minutes=mins,
                )
                for code, legacy, mins in ops
            ],
        )
    ]


def _volumetric_component_breakdown() -> list:
    ops = [
        ("vector_prep", 0.0, 0.0, 18.0),
        ("face_cnc_cut", 0.0, 0.75, 40.0),
        ("vinyl_application", 0.0, 0.0, 12.0),
        ("side_forming", 0.0, 0.5, 22.0),
        ("return_face_bonding", 0.0, 0.4, 18.0),
        ("back_cut", 0.0, 0.6, 30.0),
        ("led_install_letters", 0.0, 0.5, 25.0),
        ("electrical_letters", 0.0, 0.3, 15.0),
        ("mounting_template_cnc_cut", 0.0, 0.4, 20.0),
        ("assembly_letters", 60.0, 1.0, 120.0),
        ("qc_letters", 15.0, 0.25, 0.0),
        ("packaging_letters", 0.0, 0.0, 8.0),
    ]
    return [
        {
            "component_id": "letters",
            "operations_detail": [
                {
                    "code": code,
                    "estimated_minutes": mins,
                    "hours": hours,
                    "line_total": line_total,
                }
                for code, mins, hours, line_total in ops
            ],
        }
    ]


def _volumetric_priced_quote_snapshot() -> QuoteCalculationSnapshot:
    return QuoteCalculationSnapshot(
        product_definition=ProductDefinition(
            product_id="TPL-VOLUMETRIC-LETTERS",
            product_type="Litere volumetrice",
            quantity=1,
            dimensions=ProductDimensions(width_mm=4800, height_mm=600, depth_mm=60),
            layers=_volumetric_quote_layers_noncanonical(),
        ),
        cost_result=CostResult(
            is_valid=True,
            currency="RON",
            materials_cost=400.0,
            labour_cost=300.0,
            machine_cost=200.0,
            external_cost=0.0,
            overhead_cost=50.0,
            total_cost=950.0,
            estimated_time_minutes=75.0,
            breakdown=[],
            validation=CostValidation(),
        ),
        pricing=QuotePricing(margin_pct=20, discount_pct=0, vat_pct=19),
        price=QuotePrice(net=1000, gross=1190, final=1190),
        status="priced",
    )


class _FakeOrderRow:
    def __init__(self, order_id: int, code: str, snapshot_dict: dict):
        self.id = order_id
        self.code = code
        self.snapshot_version = 1
        self.snapshot_line_items = json.dumps(snapshot_dict)


class TestVolumetricOperationCanonicalMapping(unittest.TestCase):
    def test_volumetric_operation_codes_map_to_canonical_enum(self):
        cases = [
            ("vector_prep", "prepress", "file_preparation"),
            ("face_cnc_cut", "cnc", "cnc_routing"),
            ("return_face_bonding", "return_profile_face_bonding", "volumetric_letter_assembly"),
            ("assembly_letters", "assembly", "volumetric_letter_assembly"),
            ("qc_letters", "qc_inspection", "quality_control"),
            ("electrical_letters", "wiring", "led_wiring"),
        ]
        for code, legacy, expected in cases:
            with self.subTest(code=code):
                self.assertEqual(
                    resolve_canonical_task_type(process_id=code, legacy_type=legacy),
                    expected,
                )
                self.assertIn(expected, CANONICAL_TASK_TYPES)

    def test_unknown_template_operation_stays_unmappable(self):
        self.assertIsNone(
            resolve_canonical_task_type(process_id="unsupported_op", legacy_type="mystery")
        )


class TestVolumetricOrderSnapshotNormalization(unittest.TestCase):
    def test_normalized_layers_use_only_canonical_task_types(self):
        snap = _volumetric_priced_quote_snapshot()
        pd = normalize_product_definition_for_execution(
            snap.product_definition,
            component_breakdown=_volumetric_component_breakdown(),
        )
        types = {p.type for layer in pd.layers for p in layer.processes}
        self.assertTrue(types.issubset(CANONICAL_TASK_TYPES), types)

    def test_order_snapshot_service_applies_normalization(self):
        snap = _volumetric_priced_quote_snapshot()
        order = OrderSnapshotService().create_from_quote(
            snap,
            component_breakdown=_volumetric_component_breakdown(),
        )
        types = {
            p.type
            for layer in order.product_definition.layers
            for p in layer.processes
        }
        self.assertTrue(types.issubset(CANONICAL_TASK_TYPES), types)

    def test_gate_accepts_normalized_volumetric_order_snapshot(self):
        snap = _volumetric_priced_quote_snapshot()
        order = OrderSnapshotService().create_from_quote(
            snap,
            component_breakdown=_volumetric_component_breakdown(),
        )
        snapshot_dict = order.to_dict()
        snapshot_dict["order_id"] = 42
        row = _FakeOrderRow(42, "ORD-VOL-TEST", snapshot_dict)
        registries = RegistrySnapshot(
            skills=None,
            workcenters=None,
            roles=None,
            product_system_available=False,
            materials_registry_available=False,
            machines_registry_available=False,
        )
        evaluation = evaluate_gate(row, registries, plan_already_exists=False)
        blk08 = [b for b in evaluation.blockers if b.get("code") == "BLK-08"]
        self.assertEqual(blk08, [], evaluation.blockers)
        self.assertTrue(evaluation.can_generate, evaluation.blockers)

    def test_plan_service_generates_tasks_from_normalized_snapshot(self):
        snap = _volumetric_priced_quote_snapshot()
        order = OrderSnapshotService().create_from_quote(
            snap,
            component_breakdown=_volumetric_component_breakdown(),
        )
        snapshot_dict = order.to_dict()
        row = _FakeOrderRow(99, "ORD-VOL-PLAN", snapshot_dict)
        plan = ExecutionPlanService().from_order(row)
        self.assertGreaterEqual(len(plan.tasks), 10)
        display_names = [t.display_name or t.name for t in plan.tasks]
        self.assertTrue(any("Debitare față" in n for n in display_names))
        self.assertTrue(any("Verificare finală" in n for n in display_names))
        for task in plan.tasks:
            self.assertIn(task.process_type, CANONICAL_TASK_TYPES | {"produce_order"})

    def test_existing_canonical_fixture_snapshot_unchanged(self):
        """Regression: O-E2E-SPRINT33 / test_execution_flow canonical types."""
        raw = _complete_snapshot_dict()
        pd_raw = raw["product_definition"]
        layer = pd_raw["layers"][0]
        pd = ProductDefinition(
            product_id=pd_raw["product_id"],
            product_type=pd_raw["product_type"],
            quantity=pd_raw["quantity"],
            dimensions=ProductDimensions(**pd_raw["dimensions"]),
            layers=[
                ProductLayer(
                    layer_id=layer["layer_id"],
                    layer_type=layer["layer_type"],
                    material=ProductMaterial(**layer["material"]),
                    thickness_mm=layer["thickness_mm"],
                    finish=layer.get("finish", ""),
                    components=[],
                    processes=[
                        ProductProcess(**p) for p in layer["processes"]
                    ],
                )
            ],
        )
        normalized = normalize_product_definition_for_execution(pd)
        before = {
            (layer.layer_id, p.process_id, p.type)
            for layer in pd.layers
            for p in layer.processes
        }
        after = {
            (layer.layer_id, p.process_id, p.type)
            for layer in normalized.layers
            for p in layer.processes
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
