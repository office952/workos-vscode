"""TPL-VOLUMETRIC-LETTERS â€” internal-only QC and quote-priced operation policy."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_active_template_scope import seed_active_template_scope  # noqa: E402
from seeds.seed_build4_templates import (  # noqa: E402
    _volumetric_letters_components,
    seed_build4_templates,
)
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    seed_volumetric_owner_confirmed_prices,
)
from seeds.seed_volumetric_workcenter_rates import (  # noqa: E402
    RETURN_PROFILE_FACE_BONDING_CODE,
    RETURN_PROFILE_MACHINE_FORMING_CODE,
    seed_volumetric_operations_and_rates,
)
from services.cost_engine_service import (  # noqa: E402
    ERR_CURRENCY_MISMATCH,
    ERR_NEEDS_QUOTE_INPUT,
    ERR_WORKCENTER_RATE_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.formula_handlers import resolve_formula  # noqa: E402
from services.pricing_registry_service import PricingRegistryService  # noqa: E402
from services.template_operation_policy import is_internal_only_operation  # noqa: E402
from services.volumetric_material_rate_resolver import (  # noqa: E402
    RESOLUTION_RESOLVED,
    TEMPLATE_PSU_CODE,
    resolve_volumetric_material_rates_with_trace,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


FULL_QUOTE_INPUT = {
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "return_material_perimeter_ml": 18.0,
    "letter_count": 9,
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
    "psu_watts": 100,
    "led_module_count": 180,
    "mounting_template_area_m2": 2.88,
    "paint_tube_count": 3,
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
    "mounting_template_enabled": True,
    "back_bevel_enabled": False,
}


def _template_payload() -> dict:
    return {
        "template_code": "TPL-VOLUMETRIC-LETTERS",
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


def _qc_op_from_seed() -> dict:
    for comp in _volumetric_letters_components():
        for op in comp.get("operations") or []:
            if op.get("code") == "qc_letters":
                return op
    raise AssertionError("qc_letters not found in volumetric seed")


class TestTemplateOperationPolicy(unittest.TestCase):
    def test_qc_letters_marked_internal_only_in_seed(self) -> None:
        qc = _qc_op_from_seed()
        self.assertTrue(is_internal_only_operation(qc))
        self.assertFalse(qc.get("quote_priced", True))
        self.assertTrue(qc.get("duration_calibration_only"))

    def test_non_qc_operation_not_internal_only(self) -> None:
        for comp in _volumetric_letters_components():
            for op in comp.get("operations") or []:
                if op.get("code") == "side_forming":
                    self.assertFalse(is_internal_only_operation(op))
                    return
        self.fail("side_forming not found")


class TestQcInternalOnlyCostEngine(unittest.TestCase):
    def test_qc_skipped_from_operation_totals(self) -> None:
        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates={
                RETURN_PROFILE_MACHINE_FORMING_CODE: {
                    "rate_basis": "per_linear_meter",
                    "rate_per_linear_meter": 5.0,
                },
            },
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(_template_payload(), ctx)
        qc = _op_by_code(out, "qc_letters")
        self.assertIsNotNone(qc)
        self.assertTrue(qc.get("internal_only"))
        self.assertEqual(qc.get("line_total"), 0.0)
        self.assertEqual(qc.get("rate_basis"), "internal_only")
        self.assertAlmostEqual(qc.get("estimated_minutes"), 15.0)

    def test_qc_missing_rate_does_not_block(self) -> None:
        ctx = ComponentCostContext(
            material_rates={"MAT-ACP-FATA-LITERE": 16.0},
            workcenter_rates={},
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(_template_payload(), ctx)
        qc_errors = [
            e
            for e in out.get("errors") or []
            if e.get("kind") == ERR_WORKCENTER_RATE_MISSING
            and "workcenter='QC_INSPECTION'" in str(e.get("detail") or "")
        ]
        self.assertEqual(qc_errors, [])

    def test_non_qc_missing_workcenter_still_blocks(self) -> None:
        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates={},
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(_template_payload(), ctx)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_WORKCENTER_RATE_MISSING, kinds)
        assembly_errors = [
            e
            for e in out.get("errors") or []
            if e.get("kind") == ERR_WORKCENTER_RATE_MISSING
            and "workcenter='ASSEMBLY'" in str(e.get("detail") or "")
        ]
        self.assertEqual(assembly_errors, [])

    def test_assembly_not_quote_priced(self) -> None:
        for comp in _volumetric_letters_components():
            for op in comp.get("operations") or []:
                if op.get("code") == "assembly_letters":
                    self.assertFalse(op.get("quote_priced", True))
                    return
        self.fail("assembly_letters not found")

    def test_formula_missing_input_does_not_silently_zero(self) -> None:
        res = resolve_formula(
            "led_per_letter",
            {"module_length_mm": 75, "module_gap_mm": 25},
            {},
        )
        self.assertFalse(res.resolved)
        self.assertIsNone(res.value)

        ctx = ComponentCostContext(
            material_rates={},
            workcenter_rates={
                RETURN_PROFILE_MACHINE_FORMING_CODE: {
                    "rate_basis": "per_linear_meter",
                    "rate_per_linear_meter": 5.0,
                },
            },
            quantity=1,
            quote_input={},
        )
        out = build_execution_layers_from_components(_template_payload(), ctx)
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_NEEDS_QUOTE_INPUT, kinds)


class TestProduct001VolumetricIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="volumetric_qc_testdb_")
        cls.db_fixture.setup()
        _run(cls._seed())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager

        codes = [
            ("MAT-ACP-FATA-LITERE", "mp"),
            ("MAT-SPATE-PVC-LITERE", "mp"),
            ("MAT-LED-MODULE", "buc"),
            ("MAT-SABLON-MONTAJ", "mp"),
            ("MAT-VOPSEA-RAL", "set"),
            ("MAT-CONSUMABILE-MONTAJ", "set"),
            ("MAT-PROFIL-LATERAL-LITERE", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-60MM", "ml"),
            ("MAT-LED-PSU-12V", "buc"),
            ("MAT-LED-PSU-12V-100W", "buc"),
        ]
        async with db_manager.async_session_maker() as session:
            for code, unit in codes:
                if (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.code == code)
                    )
                ).scalar_one_or_none():
                    continue
                session.add(
                    Inventory_materials(
                        code=code,
                        name=code,
                        unit=unit,
                        category="test",
                        status="missing_price",
                    )
                )
            await session.commit()
        await seed_build4_templates()
        await seed_volumetric_owner_confirmed_prices()
        await seed_volumetric_operations_and_rates()
        await seed_active_template_scope()

    def test_product_001_no_currency_mismatch(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import list_inventory_materials_admin
        from services.workcenter_rates_service import load_workcenter_rate_dict

        async def _go():
            async with db_manager.async_session_maker() as session:
                registry = await list_inventory_materials_admin(session)
                rates = {}
                currencies = {}
                for row in registry:
                    if str(row.get("status")) == "active" and row.get("unit_cost"):
                        rates[row["code"]] = float(row["unit_cost"])
                        currencies[row["code"]] = str(row.get("currency") or "EUR")
                wc = await load_workcenter_rate_dict(session)
                resolved, _ = resolve_volumetric_material_rates_with_trace(
                    rates,
                    FULL_QUOTE_INPUT,
                    template_code="TPL-VOLUMETRIC-LETTERS",
                )
                return build_execution_layers_from_components(
                    _template_payload(),
                    ComponentCostContext(
                        material_rates=resolved,
                        material_currencies=currencies,
                        workcenter_rates=wc,
                        base_currency="EUR",
                        quantity=1,
                        quote_input=dict(FULL_QUOTE_INPUT),
                    ),
                )

        out = _run(_go())
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertNotIn(ERR_CURRENCY_MISMATCH, kinds)

    def test_product_001_no_qc_blocker(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import list_inventory_materials_admin
        from services.workcenter_rates_service import load_workcenter_rate_dict

        async def _go():
            async with db_manager.async_session_maker() as session:
                registry = await list_inventory_materials_admin(session)
                rates = {}
                for row in registry:
                    if str(row.get("status")) == "active" and row.get("unit_cost"):
                        rates[row["code"]] = float(row["unit_cost"])
                wc = await load_workcenter_rate_dict(session)
                resolved, _ = resolve_volumetric_material_rates_with_trace(
                    rates,
                    FULL_QUOTE_INPUT,
                    template_code="TPL-VOLUMETRIC-LETTERS",
                )
                return build_execution_layers_from_components(
                    _template_payload(),
                    ComponentCostContext(
                        material_rates=resolved,
                        workcenter_rates=wc,
                        quantity=1,
                        quote_input=dict(FULL_QUOTE_INPUT),
                    ),
                )

        out = _run(_go())
        qc_errors = [
            e
            for e in out.get("errors") or []
            if e.get("kind") == ERR_WORKCENTER_RATE_MISSING
            and "workcenter='QC_INSPECTION'" in str(e.get("detail") or "")
        ]
        self.assertEqual(qc_errors, [])
        qc = _op_by_code(out, "qc_letters")
        self.assertIsNotNone(qc)
        self.assertTrue(qc.get("internal_only"))

    def test_led_count_180_profile_60mm_psu_16(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import list_inventory_materials_admin

        async def _rates():
            async with db_manager.async_session_maker() as session:
                registry = await list_inventory_materials_admin(session)
            rates = {}
            for row in registry:
                if str(row.get("status")) == "active" and row.get("unit_cost"):
                    rates[row["code"]] = float(row["unit_cost"])
            return rates

        rates = _run(_rates())
        resolved, trace = resolve_volumetric_material_rates_with_trace(
            rates,
            FULL_QUOTE_INPUT,
            template_code="TPL-VOLUMETRIC-LETTERS",
        )
        self.assertEqual(trace.profile_lateral.resolution_status, RESOLUTION_RESOLVED)
        self.assertEqual(trace.profile_lateral.source_code, "MAT-PROFIL-LATERAL-LITERE-60MM")
        self.assertEqual(resolved["MAT-PROFIL-LATERAL-LITERE"], 3.0)
        self.assertEqual(trace.led_psu_12v.resolution_status, RESOLUTION_RESOLVED)
        self.assertEqual(trace.led_psu_12v.source_code, "MAT-LED-PSU-12V-100W")
        self.assertEqual(resolved[TEMPLATE_PSU_CODE], 16.0)

        ctx = ComponentCostContext(
            material_rates=resolved,
            workcenter_rates={
                RETURN_PROFILE_MACHINE_FORMING_CODE: {
                    "rate_basis": "per_linear_meter",
                    "rate_per_linear_meter": 5.0,
                },
                RETURN_PROFILE_FACE_BONDING_CODE: {
                    "rate_basis": "per_linear_meter",
                    "rate_per_linear_meter": 5.0,
                },
            },
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(_template_payload(), ctx)
        forming = _op_by_code(out, "side_forming")
        bonding = _op_by_code(out, "return_face_bonding")
        self.assertAlmostEqual(forming["line_total"], 90.0)
        self.assertAlmostEqual(bonding["line_total"], 90.0)

        led_mat = None
        for comp in out.get("components") or []:
            for md in comp.get("materials_detail") or []:
                if md.get("material_code") == "MAT-LED-MODULE":
                    led_mat = md
        self.assertIsNotNone(led_mat)
        self.assertEqual(led_mat["quantity"], 180.0)

    def test_pricing_registry_excludes_internal_only_qc(self) -> None:
        async def _go():
            async with self.db_fixture.session_maker() as session:
                svc = PricingRegistryService(session)
                reg = await svc.build_registry(
                    template_filter="TPL-VOLUMETRIC-LETTERS"
                )
                return reg

        reg = _run(_go())
        codes = {i["pricing_code"] for i in reg["items"]}
        self.assertNotIn("QC_INSPECTION", codes)
        usage = reg["template_usage"][0]
        self.assertNotIn("QC_INSPECTION", usage.get("workcenter_codes") or [])


if __name__ == "__main__":
    unittest.main()
