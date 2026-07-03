"""TPL-VOLUMETRIC-LETTERS — return labor + sablon CNC operation costing."""

from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from seeds.seed_volumetric_workcenter_rates import (  # noqa: E402
    RETURN_PROFILE_FACE_BONDING_CODE,
    RETURN_PROFILE_MACHINE_FORMING_CODE,
    OWNER_VOLUMETRIC_LABOR_WORKCENTERS,
)
from services.cost_engine_service import (  # noqa: E402
    ERR_NEEDS_QUOTE_INPUT,
    ERR_WORKCENTER_LINEAR_METER_QUANTITY_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.formula_handlers import resolve_formula  # noqa: E402


FULL_QUOTE_INPUT = {
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "return_material_perimeter_ml": 20.0,
    "letter_count": 9,
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
    "mounting_template_area_m2": 2.88,
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
    "mounting_template_enabled": True,
    "back_bevel_enabled": False,
}

LABOR_WC_RATES = {
    RETURN_PROFILE_MACHINE_FORMING_CODE: {
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 5.0,
    },
    RETURN_PROFILE_FACE_BONDING_CODE: {
        "rate_basis": "per_linear_meter",
        "rate_per_linear_meter": 5.0,
    },
    "CNC_ROUTER": 90.0,
    "LASER_CUTTING": 90.0,
    "LED_ASSEMBLY": 60.0,
    "ELECTRICAL_WIRING": 60.0,
    "PAINTING": 70.0,
    "QC_INSPECTION": 50.0,
    "PACKAGING": 40.0,
    "PREPRESS": 50.0,
}


def _template() -> dict:
    return {
        "components_json": json.dumps(_volumetric_letters_components()),
        "operations_json": "[]",
        "required_materials_json": "[]",
    }


def _op_by_code(out: dict, code: str) -> dict | None:
    for comp in out.get("components") or []:
        for op in comp.get("operations_detail") or []:
            if op.get("code") == code:
                return op
    return None


def _mat_by_code(out: dict, code: str) -> dict | None:
    for comp in out.get("components") or []:
        for mat in comp.get("materials_detail") or []:
            if mat.get("material_code") == code:
                return mat
    return None


class TestVolumetricLaborWorkcenterSeed(unittest.TestCase):
    def test_owner_labor_rates_are_per_linear_meter_eur(self):
        by_code = {r["code"]: r for r in OWNER_VOLUMETRIC_LABOR_WORKCENTERS}
        forming = by_code[RETURN_PROFILE_MACHINE_FORMING_CODE]
        bonding = by_code[RETURN_PROFILE_FACE_BONDING_CODE]
        self.assertEqual(forming["rate_per_linear_meter"], 5.0)
        self.assertEqual(bonding["rate_per_linear_meter"], 5.0)
        self.assertEqual(forming["currency"], "EUR")
        self.assertEqual(forming["rate_basis"], "per_linear_meter")


class TestVolumetricReturnLaborCosting(unittest.TestCase):
    def test_forming_and_bonding_use_perimeter_separate_from_profile_material(self):
        ctx = ComponentCostContext(
            material_rates={"MAT-PROFIL-LATERAL-LITERE": 3.0},
            workcenter_rates=LABOR_WC_RATES,
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(_template(), ctx)

        forming = _op_by_code(out, "side_forming")
        bonding = _op_by_code(out, "return_face_bonding")
        self.assertIsNotNone(forming)
        self.assertIsNotNone(bonding)
        self.assertEqual(forming["rate_basis"], "per_linear_meter")
        self.assertEqual(bonding["rate_basis"], "per_linear_meter")
        self.assertAlmostEqual(forming["linear_meters"], 18.0)
        self.assertAlmostEqual(bonding["linear_meters"], 20.0)
        self.assertAlmostEqual(forming["line_total"], 90.0)
        self.assertAlmostEqual(bonding["line_total"], 100.0)

        profile_mat = _mat_by_code(out, "MAT-PROFIL-LATERAL-LITERE")
        self.assertIsNotNone(profile_mat)
        self.assertAlmostEqual(profile_mat["unit_cost"], 3.0)
        self.assertGreater(profile_mat["line_total"], 0.0)
        self.assertNotAlmostEqual(profile_mat["line_total"], forming["line_total"])

    def test_missing_letter_perimeter_fails_return_labor(self):
        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates=LABOR_WC_RATES,
            quantity=1,
            quote_input={"letter_face_area_m2": 2.88},
        )
        out = build_execution_layers_from_components(_template(), ctx)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_NEEDS_QUOTE_INPUT, kinds)

    def test_linear_meter_workcenter_requires_quantity(self):
        ctx = ComponentCostContext(
            workcenter_rates={
                RETURN_PROFILE_MACHINE_FORMING_CODE: {
                    "rate_basis": "per_linear_meter",
                    "rate_per_linear_meter": 5.0,
                }
            },
            quantity=1,
            quote_input={},
        )
        components = [
            {
                "component_id": "c1",
                "type": "X",
                "name": "x",
                "materials": [],
                "operations": [
                    {
                        "code": "side_forming",
                        "workcenter": RETURN_PROFILE_MACHINE_FORMING_CODE,
                        "calculation_type": "static",
                        "estimated_minutes": 10,
                    }
                ],
            }
        ]
        tpl = {
            "components_json": json.dumps(components),
            "operations_json": "[]",
            "required_materials_json": "[]",
        }
        out = build_execution_layers_from_components(tpl, ctx)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_WORKCENTER_LINEAR_METER_QUANTITY_MISSING, kinds)


class TestVolumetricSablonCncOperation(unittest.TestCase):
    def test_mounting_template_cnc_operation_present(self):
        components = _volumetric_letters_components()
        finisaj = next(c for c in components if c["component_id"] == "comp_finisaj_litere")
        codes = [op["code"] for op in finisaj.get("operations") or []]
        self.assertIn("mounting_template_cnc_cut", codes)

    def test_sablon_cnc_uses_cnc_router_time_not_material_cost(self):
        ctx = ComponentCostContext(
            material_rates={"MAT-SABLON-MONTAJ": 6.0},
            workcenter_rates=LABOR_WC_RATES,
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(_template(), ctx)
        cnc = _op_by_code(out, "mounting_template_cnc_cut")
        sablon = _mat_by_code(out, "MAT-SABLON-MONTAJ")
        self.assertIsNotNone(cnc)
        self.assertIsNotNone(sablon)
        self.assertEqual(cnc["workcenter"], "CNC_ROUTER")
        self.assertEqual(cnc.get("formula_id"), "perimeter_pass_linear_meter")
        self.assertGreater(cnc["line_total"], 0.0)
        self.assertAlmostEqual(sablon["unit_cost"], 6.0)
        self.assertAlmostEqual(sablon["quantity"], 2.88)
        self.assertNotAlmostEqual(sablon["line_total"], cnc["line_total"])

    def test_letter_perimeter_formula_for_operations(self):
        res = resolve_formula("letter_perimeter", {"extra_pct": 0}, FULL_QUOTE_INPUT)
        self.assertTrue(res.resolved)
        self.assertAlmostEqual(float(res.value), 18.0)


if __name__ == "__main__":
    unittest.main()
