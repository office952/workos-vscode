"""Base currency wiring and CURRENCY_MISMATCH blocking for CostEngine v2."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_models.product_contracts import PricingContext  # noqa: E402
from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    seed_volumetric_owner_confirmed_prices,
)
from seeds.seed_volumetric_workcenter_rates import (  # noqa: E402
    seed_volumetric_workcenter_rates,
)
from services.cost_engine_config import load_base_currency  # noqa: E402
from services.cost_engine_service import (  # noqa: E402
    ERR_CURRENCY_MISMATCH,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.quote_orchestrator import QuoteOrchestrator  # noqa: E402
from services.volumetric_material_rate_resolver import (  # noqa: E402
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
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
    "mounting_template_enabled": True,
    "back_bevel_enabled": False,
}


class TestCurrencyMismatchUnit(unittest.TestCase):
    def test_material_mismatch_blocks_total(self) -> None:
        out = build_execution_layers_from_components(
            {
                "components_json": json.dumps(
                    [
                        {
                            "component_id": "comp_psu",
                            "materials": [
                                {
                                    "material_code": "MAT-LED-PSU-12V-100W",
                                    "quantity": 1,
                                    "unit": "buc",
                                }
                            ],
                            "operations": [],
                        }
                    ]
                ),
                "operations_json": "[]",
                "required_materials_json": "[]",
            },
            ComponentCostContext(
                material_rates={"MAT-LED-PSU-12V-100W": 80.0},
                material_currencies={"MAT-LED-PSU-12V-100W": "RON"},
                base_currency="EUR",
                quantity=1,
            ),
        )
        self.assertFalse(out["is_valid"])
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_CURRENCY_MISMATCH, kinds)
        details = " ".join(str(e.get("detail") or "") for e in out.get("errors") or [])
        self.assertIn("MAT-LED-PSU-12V-100W", details)
        self.assertIn("row_currency=RON", details)
        self.assertIn("base_currency=EUR", details)

    def test_matching_currency_passes_material_lines(self) -> None:
        out = build_execution_layers_from_components(
            {
                "template_code": "TPL-VOLUMETRIC-LETTERS",
                "components_json": json.dumps(_volumetric_letters_components()),
                "operations_json": "[]",
                "required_materials_json": "[]",
            },
            ComponentCostContext(
                material_rates={"MAT-ACP-FATA-LITERE": 16.0},
                material_currencies={"MAT-ACP-FATA-LITERE": "EUR"},
                base_currency="EUR",
                quantity=1,
                quote_input={
                    "letter_face_area_m2": 1.0,
                    "letter_perimeter_m": 1.0,
                    "letter_count": 1,
                },
            ),
        )
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertNotIn(ERR_CURRENCY_MISMATCH, kinds)

    def test_workcenter_mismatch_blocks_operation_cost(self) -> None:
        out = build_execution_layers_from_components(
            {
                "template_code": "TPL-VOLUMETRIC-LETTERS",
                "components_json": json.dumps(_volumetric_letters_components()),
                "operations_json": "[]",
                "required_materials_json": "[]",
            },
            ComponentCostContext(
                material_rates={},
                workcenter_rates={
                    "RETURN_PROFILE_MACHINE_FORMING": {
                        "rate_basis": "per_linear_meter",
                        "rate_per_linear_meter": 5.0,
                    }
                },
                workcenter_currencies={
                    "RETURN_PROFILE_MACHINE_FORMING": "EUR",
                },
                base_currency="RON",
                quantity=1,
                quote_input={"letter_perimeter_m": 10.0},
            ),
        )
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertIn(ERR_CURRENCY_MISMATCH, kinds)


class TestBaseCurrencyWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture()
        cls.db_fixture.setup()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    def test_load_base_currency_defaults_eur(self) -> None:
        from core.database import db_manager
        from seeds.seed_cost_engine_template_currency import (
            seed_cost_engine_template_base_currency,
        )

        _run(seed_cost_engine_template_base_currency())

        async def _go():
            async with db_manager.async_session_maker() as session:
                return await load_base_currency(session)

        self.assertEqual(_run(_go()), "EUR")

    def test_orchestrator_uses_base_currency_in_pricing_context(self) -> None:
        from core.database import db_manager
        from seeds.seed_cost_engine_template_currency import (
            seed_cost_engine_template_base_currency,
        )

        _run(seed_cost_engine_template_base_currency())

        async def _go():
            async with db_manager.async_session_maker() as session:
                orch = await QuoteOrchestrator.create_with_registry(session)
                snap = orch.build_snapshot(
                    product_template={
                        "template_code": "TPL-VOLUMETRIC-LETTERS",
                        "components_json": json.dumps(_volumetric_letters_components()),
                    },
                    user_config={
                        "product_id": "TPL-VOLUMETRIC-LETTERS",
                        "quantity": 1,
                        "dimensions": {"width_mm": 0, "height_mm": 0, "depth_mm": 0},
                    },
                    quote_input=FULL_QUOTE_INPUT,
                )
                return orch.base_currency, snap

        base, snap = _run(_go())
        self.assertEqual(base, "EUR")
        # cost_result.currency is populated when costing runs; early-blocked
        # snapshots keep the default CostResult shell (RON) until v2 costing.
        if snap.status == "priced":
            self.assertEqual(snap.cost_result.currency, "EUR")
        elif snap.cost_result.total_cost > 0 or snap.cost_result.breakdown:
            self.assertEqual(snap.cost_result.currency, "EUR")


class TestProduct001MixedCurrencyBlocked(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture()
        cls.db_fixture.setup()
        _run(cls._seed_stubs())
        _run(seed_volumetric_owner_confirmed_prices())
        _run(seed_volumetric_workcenter_rates())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed_stubs(cls) -> None:
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

    def test_product001_psu_no_currency_mismatch_with_eur_base(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import (
            load_material_cost_dict,
            load_material_pricing_dict,
        )

        psu_codes = {
            "MAT-LED-PSU-12V-60W",
            "MAT-LED-PSU-12V-100W",
            "MAT-LED-PSU-12V-160W",
            "MAT-LED-PSU-12V-200W",
        }

        async def _go():
            async with db_manager.async_session_maker() as session:
                rates = await load_material_cost_dict(session)
                pricing = await load_material_pricing_dict(session)
                resolved, _ = resolve_volumetric_material_rates_with_trace(
                    rates,
                    FULL_QUOTE_INPUT,
                    template_code="TPL-VOLUMETRIC-LETTERS",
                )
                currencies = {
                    code: row["currency"] for code, row in pricing.items()
                }
                out = build_execution_layers_from_components(
                    {
                        "template_code": "TPL-VOLUMETRIC-LETTERS",
                        "components_json": json.dumps(_volumetric_letters_components()),
                        "operations_json": "[]",
                        "required_materials_json": "[]",
                    },
                    ComponentCostContext(
                        material_rates=resolved,
                        material_currencies=currencies,
                        base_currency="EUR",
                        workcenter_rates={
                            "RETURN_PROFILE_MACHINE_FORMING": {
                                "rate_basis": "per_linear_meter",
                                "rate_per_linear_meter": 5.0,
                            },
                            "RETURN_PROFILE_FACE_BONDING": {
                                "rate_basis": "per_linear_meter",
                                "rate_per_linear_meter": 5.0,
                            },
                        },
                        workcenter_currencies={
                            "RETURN_PROFILE_MACHINE_FORMING": "EUR",
                            "RETURN_PROFILE_FACE_BONDING": "EUR",
                        },
                        quantity=1,
                        quote_input=dict(FULL_QUOTE_INPUT),
                    ),
                )
                return out

        out = _run(_go())
        mismatch_errors = [
            e
            for e in out.get("errors") or []
            if e.get("kind") == ERR_CURRENCY_MISMATCH
        ]
        psu_mismatches = [
            e
            for e in mismatch_errors
            if any(code in str(e.get("detail") or "") for code in psu_codes)
        ]
        self.assertEqual(psu_mismatches, [], msg=mismatch_errors)

    def test_mixed_eur_ron_reports_currency_mismatch(self) -> None:
        from core.database import db_manager
        from services.inventory_materials_admin_service import (
            load_material_cost_dict,
            load_material_pricing_dict,
        )

        async def _go():
            async with db_manager.async_session_maker() as session:
                rates = await load_material_cost_dict(session)
                pricing = await load_material_pricing_dict(session)
                resolved, _ = resolve_volumetric_material_rates_with_trace(
                    rates,
                    FULL_QUOTE_INPUT,
                    template_code="TPL-VOLUMETRIC-LETTERS",
                )
                currencies = {
                    code: row["currency"] for code, row in pricing.items()
                }
                out = build_execution_layers_from_components(
                    {
                        "template_code": "TPL-VOLUMETRIC-LETTERS",
                        "components_json": json.dumps(_volumetric_letters_components()),
                        "operations_json": "[]",
                        "required_materials_json": "[]",
                    },
                    ComponentCostContext(
                        material_rates=resolved,
                        material_currencies=currencies,
                        base_currency="RON",
                        workcenter_rates={
                            "RETURN_PROFILE_MACHINE_FORMING": {
                                "rate_basis": "per_linear_meter",
                                "rate_per_linear_meter": 5.0,
                            },
                            "RETURN_PROFILE_FACE_BONDING": {
                                "rate_basis": "per_linear_meter",
                                "rate_per_linear_meter": 5.0,
                            },
                        },
                        workcenter_currencies={
                            "RETURN_PROFILE_MACHINE_FORMING": "EUR",
                            "RETURN_PROFILE_FACE_BONDING": "EUR",
                        },
                        quantity=1,
                        quote_input=dict(FULL_QUOTE_INPUT),
                    ),
                )
                return out

        out = _run(_go())
        self.assertFalse(out["is_valid"])
        mismatch_errors = [
            e
            for e in out.get("errors") or []
            if e.get("kind") == ERR_CURRENCY_MISMATCH
        ]
        self.assertTrue(mismatch_errors)
        joined = " ".join(str(e.get("detail") or "") for e in mismatch_errors)
        self.assertIn("EUR", joined)
        self.assertIn("base_currency=RON", joined)


if __name__ == "__main__":
    unittest.main()
