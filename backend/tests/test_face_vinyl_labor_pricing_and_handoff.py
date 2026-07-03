"""Face vinyl application labor (rate 5 EUR/mp; labor line EUR), handoff, and plan injection."""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_models.product_contracts import (  # noqa: E402
    CostResult,
    CostValidation,
    ProductDefinition,
    ProductDimensions,
    ProductLayer,
    ProductMaterial,
    ProductProcess,
    QuoteCalculationSnapshot,
    QuotePrice,
    QuotePricing,
)
from services.execution_plan_service import ExecutionPlanService  # noqa: E402
from services.order_execution_snapshot_mapper import (  # noqa: E402
    normalize_product_definition_for_execution,
)
from services.order_snapshot_service import OrderSnapshotService  # noqa: E402
from services.volumetric_conditional_plan_tasks_service import (  # noqa: E402
    apply_volumetric_conditional_plan_from_snapshot,
    ensure_face_vinyl_plan_task_when_required,
)
from services.volumetric_execution_dispatch import (  # noqa: E402
    enrich_operation_time_index_from_breakdown,
)
from services.volumetric_face_vinyl_service import (  # noqa: E402
    FACE_VINYL_DISPLAY_NAME,
    FACE_VINYL_PROCESS_ID,
    resolve_face_vinyl_used_sqm,
)
from tests.test_volumetric_finish_mounting_pricing import (  # noqa: E402
    BASE_QUOTE_INPUT,
    TestVolumetricFinishMountingPricing,
    _op_by_code,
)


FACE_VINYL_NESTING_INPUT = {
    **BASE_QUOTE_INPUT,
    "face_finish_type": "oracal_651",
    "face_vinyl_roll_width_mm": 1260,
    "face_vinyl_color_code": "651-020",
}


def _extract_execution_handoff(wrapper: dict) -> dict:
    """Mirror orders/from-quote wrapper extraction."""
    handoff: dict = {}
    for key in (
        "quote_input",
        "product_spec_json",
        "delivery_type",
        "face_vinyl_handoff",
    ):
        value = wrapper.get(key)
        if value is not None:
            handoff[key] = value
    return handoff


def _serialize_wrapper(**kwargs) -> dict:
    from routers.quotes import _serialize_quote_line_items

    snapshot = {
        "status": "priced",
        "price": {"net": 100.0, "gross": 119.0, "final": 119.0},
        "pricing": {"margin_pct": 0, "discount_pct": 0, "vat_pct": 19},
    }
    raw = _serialize_quote_line_items(snapshot, **kwargs)
    return json.loads(raw)


class TestFaceVinylUsedSqmResolution(unittest.TestCase):
    def test_nesting_preferred_over_face_area(self) -> None:
        res = resolve_face_vinyl_used_sqm(FACE_VINYL_NESTING_INPUT)
        self.assertEqual(res.source, "nesting")
        self.assertTrue(res.fallback_weak_estimate)
        self.assertAlmostEqual(res.recommended_roll_length_m or 0, 5.28, places=2)
        self.assertAlmostEqual(res.material_width_m or 0, 1.26, places=2)
        expected = round(5.28 * 1.26, 4)
        self.assertAlmostEqual(res.value or 0, expected, places=2)

    def test_fallback_when_roll_width_missing(self) -> None:
        qi = {**BASE_QUOTE_INPUT, "face_finish_type": "oracal_651"}
        res = resolve_face_vinyl_used_sqm(qi)
        self.assertEqual(res.source, "fallback_face_area")
        self.assertTrue(res.fallback_weak_estimate)
        self.assertAlmostEqual(res.value or 0, round(2.88 * 1.10, 6), places=4)

    def test_none_when_face_vinyl_not_selected(self) -> None:
        res = resolve_face_vinyl_used_sqm(BASE_QUOTE_INPUT)
        self.assertIsNone(res.value)
        self.assertEqual(res.source, "none")


class TestFaceVinylLaborPricing(TestVolumetricFinishMountingPricing):
    def test_nesting_quantity_and_labor_rate(self) -> None:
        out = self._build(FACE_VINYL_NESTING_INPUT)
        op = _op_by_code(out, "vinyl_application")
        self.assertIsNotNone(op)
        used_sqm = round(5.28 * 1.26, 4)
        self.assertAlmostEqual(op["line_total"], round(used_sqm * 5, 4), places=2)
        breakdown = op.get("formula_breakdown") or {}
        self.assertEqual(breakdown.get("quantity_source"), "nesting")
        self.assertTrue(breakdown.get("fallback_weak_estimate"))

    def test_no_face_vinyl_skips_labor_line(self) -> None:
        out = self._build(BASE_QUOTE_INPUT)
        op = _op_by_code(out, "vinyl_application")
        self.assertIsNotNone(op)
        self.assertEqual(op.get("skipped"), True)
        self.assertEqual(op.get("line_total"), 0.0)


class TestQuoteOrderHandoffSerialization(unittest.TestCase):
    def test_wrapper_persists_execution_fields(self) -> None:
        quote_input = dict(FACE_VINYL_NESTING_INPUT)
        product_spec = {"face_vinyl_roll_width_mm": 1260}
        handoff = {
            "face_vinyl_used_sqm": 6.65,
            "quantity_source": "nesting",
        }
        wrapper = _serialize_wrapper(
            quote_input=quote_input,
            product_spec_json=product_spec,
            delivery_type="delivery_install",
            face_vinyl_handoff=handoff,
        )
        self.assertIn("quote_input", wrapper)
        self.assertIn("product_spec_json", wrapper)
        self.assertEqual(wrapper["delivery_type"], "delivery_install")
        self.assertEqual(wrapper["face_vinyl_handoff"]["quantity_source"], "nesting")

    def test_order_snapshot_merge_carries_handoff(self) -> None:
        wrapper = _serialize_wrapper(
            quote_input=dict(FACE_VINYL_NESTING_INPUT),
            delivery_type="pickup",
            face_vinyl_handoff={"face_vinyl_used_sqm": 6.65},
        )
        handoff = _extract_execution_handoff(wrapper)
        snap = QuoteCalculationSnapshot(
            product_definition=ProductDefinition(
                product_id="TPL-VOLUMETRIC-LETTERS",
                product_type="Litere volumetrice",
                quantity=1,
                dimensions=ProductDimensions(width_mm=4800, height_mm=600, depth_mm=60),
                layers=[
                    ProductLayer(
                        layer_id="layer_1",
                        layer_type="structure",
                        material=ProductMaterial(material_id="MAT", name="Face", unit="sqm"),
                        thickness_mm=3,
                        finish="",
                        components=[],
                        processes=[
                            ProductProcess(
                                process_id="assembly_letters",
                                type="assembly",
                                machine_type="WC",
                                estimated_time_minutes=60.0,
                            )
                        ],
                    )
                ],
            ),
            cost_result=CostResult(
                is_valid=True,
                currency="EUR",
                materials_cost=0.0,
                labour_cost=0.0,
                machine_cost=0.0,
                external_cost=0.0,
                overhead_cost=0.0,
                total_cost=0.0,
                estimated_time_minutes=60.0,
                breakdown=[],
                validation=CostValidation(),
            ),
            pricing=QuotePricing(margin_pct=0, discount_pct=0, vat_pct=19),
            price=QuotePrice(net=100, gross=119, final=119),
            status="priced",
        )
        order = OrderSnapshotService().create_from_quote(snap)
        order_dict = order.to_dict()
        for key, value in handoff.items():
            order_dict[key] = value
        self.assertEqual(order_dict["delivery_type"], "pickup")
        self.assertIn("quote_input", order_dict)
        self.assertEqual(order_dict["face_vinyl_handoff"]["face_vinyl_used_sqm"], 6.65)


class TestFaceVinylPlanInjection(unittest.TestCase):
    def test_enrich_minutes_from_priced_breakdown(self) -> None:
        breakdown = [
            {
                "component_id": "letters",
                "operations_detail": [
                    {
                        "code": "vinyl_application",
                        "estimated_minutes": 0.0,
                        "hours": 0.0,
                        "line_total": 33.26,
                    }
                ],
            }
        ]
        index = enrich_operation_time_index_from_breakdown({}, breakdown)
        self.assertGreater(index.get("vinyl_application", 0), 0)

    def test_inject_vinyl_task_when_missing_from_zero_min_plan(self) -> None:
        snap = QuoteCalculationSnapshot(
            product_definition=ProductDefinition(
                product_id="TPL-VOLUMETRIC-LETTERS",
                product_type="Litere volumetrice",
                quantity=1,
                dimensions=ProductDimensions(width_mm=4800, height_mm=600, depth_mm=60),
                layers=[
                    ProductLayer(
                        layer_id="layer_1",
                        layer_type="structure",
                        material=ProductMaterial(material_id="MAT", name="Face", unit="sqm"),
                        thickness_mm=3,
                        finish="",
                        components=[],
                        processes=[
                            ProductProcess(
                                process_id="face_cnc_cut",
                                type="cnc",
                                machine_type="WC",
                                estimated_time_minutes=30.0,
                            ),
                            ProductProcess(
                                process_id=FACE_VINYL_PROCESS_ID,
                                type="vinyl_application",
                                machine_type="WC",
                                estimated_time_minutes=0.0,
                            ),
                            ProductProcess(
                                process_id="assembly_letters",
                                type="assembly",
                                machine_type="WC",
                                estimated_time_minutes=60.0,
                            ),
                        ],
                    )
                ],
            ),
            cost_result=CostResult(
                is_valid=True,
                currency="EUR",
                materials_cost=0.0,
                labour_cost=0.0,
                machine_cost=0.0,
                external_cost=0.0,
                overhead_cost=0.0,
                total_cost=0.0,
                estimated_time_minutes=90.0,
                breakdown=[],
                validation=CostValidation(),
            ),
            pricing=QuotePricing(margin_pct=0, discount_pct=0, vat_pct=19),
            price=QuotePrice(net=100, gross=119, final=119),
            status="priced",
        )
        breakdown: list = []
        pd = normalize_product_definition_for_execution(
            snap.product_definition,
            component_breakdown=breakdown,
        )
        order_dict = snap.to_dict()
        order_dict["product_definition"] = pd.to_dict()

        class _Row:
            id = 1
            code = "ORD-TEST"
            snapshot_version = 1
            snapshot_line_items = json.dumps(order_dict)

        dto = ExecutionPlanService().from_order(_Row())
        task_dicts = [t.to_dict() for t in dto.tasks]
        self.assertNotIn(
            FACE_VINYL_PROCESS_ID,
            [t.get("process_id") for t in task_dicts],
        )

        snapshot = {
            "quote_input": FACE_VINYL_NESTING_INPUT,
            "face_vinyl_handoff": {"face_vinyl_used_sqm": 6.65},
        }
        tasks, action = ensure_face_vinyl_plan_task_when_required(
            task_dicts,
            quote_input=FACE_VINYL_NESTING_INPUT,
            snapshot=snapshot,
        )
        self.assertEqual(action, "injected")
        vinyl = next(t for t in tasks if t.get("process_id") == FACE_VINYL_PROCESS_ID)
        self.assertEqual(vinyl["display_name"], FACE_VINYL_DISPLAY_NAME)
        self.assertGreater(vinyl["estimated_time_minutes"], 0)

    def test_conditional_plan_injects_colantare_for_face_vinyl(self) -> None:
        tasks = [
            {"task_id": "T-001", "process_id": "face_cnc_cut", "estimated_time_minutes": 20},
            {"task_id": "T-002", "process_id": "assembly_letters", "estimated_time_minutes": 60},
        ]
        snapshot = {
            "quote_input": FACE_VINYL_NESTING_INPUT,
            "product_definition": {"product_id": "TPL-VOLUMETRIC-LETTERS"},
        }
        updated, summary = apply_volumetric_conditional_plan_from_snapshot(
            tasks,
            snapshot,
            set_face_vinyl_instructions=False,
        )
        pids = [t.get("process_id") for t in updated if isinstance(t, dict)]
        self.assertIn(FACE_VINYL_PROCESS_ID, pids)
        self.assertIn(summary["face_vinyl_action"], {"injected_missing_task", "updated"})

    def test_no_colantare_without_face_vinyl(self) -> None:
        tasks = [
            {"task_id": "T-001", "process_id": FACE_VINYL_PROCESS_ID, "estimated_time_minutes": 15},
            {"task_id": "T-002", "process_id": "assembly_letters", "estimated_time_minutes": 60},
        ]
        snapshot = {
            "quote_input": BASE_QUOTE_INPUT,
            "product_definition": {"product_id": "TPL-VOLUMETRIC-LETTERS"},
        }
        updated, summary = apply_volumetric_conditional_plan_from_snapshot(
            tasks,
            snapshot,
            set_face_vinyl_instructions=False,
        )
        pids = [t.get("process_id") for t in updated if isinstance(t, dict)]
        self.assertNotIn(FACE_VINYL_PROCESS_ID, pids)
        self.assertEqual(summary["face_vinyl_action"], "filtered_no_face_vinyl")


if __name__ == "__main__":
    unittest.main()
