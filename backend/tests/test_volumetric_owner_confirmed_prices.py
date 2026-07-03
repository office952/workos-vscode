"""Product 001 — owner-confirmed volumetric material registry prices."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    OWNER_CONFIRMED_ACTIVATED_CODES,
    OWNER_CONFIRMED_NOT_ACTIVATED,
    ESTIMATED_PRELIMINARY_ACTIVATED_CODES,
    OWNER_CONFIRMED_PROFILE_DEPTH_PRICES,
    OWNER_CONFIRMED_PSU_WATTAGE_PRICES,
    OWNER_CONFIRMED_VOLUMETRIC_PRICES,
    PRELIMINARY_COSTING_ALIAS_CODES,
    PROFILE_DEPTH_VARIANT_CODES,
    PSU_WATTAGE_VARIANT_CODES,
    TEMPLATE_PROFILE_CODE,
    TEMPLATE_PSU_CODE,
    VOLUMETRIC_TEMPLATE_MATERIAL_CODES,
    seed_volumetric_owner_confirmed_prices,
)
from services.volumetric_material_rate_resolver import (  # noqa: E402
    resolve_volumetric_material_rates,
)
from services.cost_engine_service import (  # noqa: E402
    ERR_FORMULA_UNKNOWN,
    ERR_MATERIAL_RATE_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.inventory_materials_admin_service import (  # noqa: E402
    get_inventory_material_by_code,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

from models.inventory_material_price_history import (  # noqa: E402
    Inventory_material_price_history,
)
from models.inventory_materials import Inventory_materials  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _template_from_components(components: list) -> dict:
    return {
        "template_code": "TPL-VOLUMETRIC-LETTERS",
        "components_json": json.dumps(components),
        "operations_json": json.dumps([]),
        "required_materials_json": json.dumps([]),
    }


FULL_QUOTE_INPUT = {
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "letter_count": 9,
    "led_module_count": 27,
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
    "mounting_template_area_m2": 2.88,
    "led_module_count": 180,
}


class TestVolumetricOwnerConfirmedPrices(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture()
        cls.db_fixture.setup()
        _run(cls._seed_materials())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    def setUp(self) -> None:
        _run(seed_volumetric_owner_confirmed_prices())

    @classmethod
    async def _seed_materials(cls) -> None:
        from core.database import db_manager

        stubs = [
            ("MAT-ACP-FATA-LITERE", "ACP / aluminiu față litere", "mp"),
            ("MAT-PROFIL-LATERAL-LITERE", "Profil lateral litere", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-30MM", "Return 30mm", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-60MM", "Return 60mm", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-80MM", "Return 80mm", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-100MM", "Return 100mm", "ml"),
            ("MAT-SPATE-PVC-LITERE", "Forex 10 mm spate litere", "mp"),
            ("MAT-LED-MODULE", "Modul LED", "buc"),
            ("MAT-LED-PSU-12V", "Sursa LED 12V", "buc"),
            ("MAT-LED-PSU-12V-60W", "PSU 60W", "buc"),
            ("MAT-LED-PSU-12V-100W", "PSU 100W", "buc"),
            ("MAT-LED-PSU-12V-160W", "PSU 160W", "buc"),
            ("MAT-LED-PSU-12V-200W", "PSU 200W", "buc"),
            ("MAT-VOPSEA-RAL", "Vopsea RAL spray", "buc"),
            ("MAT-SABLON-MONTAJ", "Șablon montaj", "buc"),
            ("MAT-CONSUMABILE-MONTAJ", "Consumabile montaj", "set"),
        ]
        async with db_manager.async_session_maker() as session:
            for code, name, unit in stubs:
                existing = (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.code == code)
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    continue
                session.add(
                    Inventory_materials(
                        code=code,
                        name=name,
                        unit=unit,
                        category="test_volumetric",
                        unit_cost=None,
                        status="missing_price",
                    )
                )
            await session.commit()

    def test_seed_idempotent(self) -> None:
        first = _run(seed_volumetric_owner_confirmed_prices())
        second = _run(seed_volumetric_owner_confirmed_prices())
        self.assertGreaterEqual(first["skipped"], len(OWNER_CONFIRMED_VOLUMETRIC_PRICES))
        self.assertEqual(second["patched"], 0)
        self.assertGreaterEqual(second["skipped"], len(OWNER_CONFIRMED_VOLUMETRIC_PRICES))

    def test_activated_rows_have_governance_fields(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                rows = []
                for spec in OWNER_CONFIRMED_VOLUMETRIC_PRICES:
                    row = await get_inventory_material_by_code(session, spec["code"])
                    assert row is not None
                    rows.append(row)
                return rows

        rows = _run(_go())
        for spec, row in zip(OWNER_CONFIRMED_VOLUMETRIC_PRICES, rows):
            self.assertEqual(row["status"], "active")
            self.assertEqual(row["unit_cost"], spec["unit_cost"])
            self.assertEqual(row["currency"], spec["currency"])
            self.assertIsNotNone(row["vat_percent"])
            self.assertIsNotNone(row["valid_from"])
            self.assertEqual(row["source_review_status"], "accepted_override")
            self.assertIn("Owner-confirmed", row["source_notes"])

    def test_price_history_written_for_activated(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                counts = {}
                for spec in OWNER_CONFIRMED_VOLUMETRIC_PRICES:
                    mat = (
                        await session.execute(
                            select(Inventory_materials).where(
                                Inventory_materials.code == spec["code"]
                            )
                        )
                    ).scalar_one_or_none()
                    self.assertIsNotNone(mat)
                    n = (
                        await session.execute(
                            select(Inventory_material_price_history).where(
                                Inventory_material_price_history.material_id == mat.id
                            )
                        )
                    ).scalars().all()
                    counts[spec["code"]] = len(n)
                return counts

        counts = _run(_go())
        for code, n in counts.items():
            self.assertGreaterEqual(n, 1, f"{code} should have price history")

    def test_not_activated_codes_remain_without_owner_price(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                out = {}
                for code in OWNER_CONFIRMED_NOT_ACTIVATED:
                    row = await get_inventory_material_by_code(session, code)
                    out[code] = row
                return out

        rows = _run(_go())
        for code in OWNER_CONFIRMED_NOT_ACTIVATED:
            row = rows[code]
            self.assertIsNotNone(row)
            self.assertNotEqual(row.get("status"), "active")
            self.assertTrue(
                row.get("unit_cost") is None or row.get("unit_cost") <= 0,
                code,
            )

    def test_cost_engine_blockers_reduce_for_activated_only(self) -> None:
        components = _volumetric_letters_components()
        rates = {
            spec["code"]: spec["unit_cost"]
            for spec in (
                OWNER_CONFIRMED_VOLUMETRIC_PRICES
                + OWNER_CONFIRMED_PROFILE_DEPTH_PRICES
                + OWNER_CONFIRMED_PSU_WATTAGE_PRICES
                + [
                    {"code": "MAT-CONSUMABILE-MONTAJ", "unit_cost": 5.0},
                ]
            )
        }
        rates = resolve_volumetric_material_rates(rates, FULL_QUOTE_INPUT)
        ctx = ComponentCostContext(
            material_rates=rates,
            workcenter_rates={
                "CNC_ROUTER": 90.0,
                "LASER_CUTTING": 90.0,
                "ASSEMBLY": 80.0,
                "LED_ASSEMBLY": 60.0,
                "ELECTRICAL_WIRING": 60.0,
                "PAINTING": 70.0,
                "QC_INSPECTION": 50.0,
                "PACKAGING": 40.0,
                "PREPRESS": 50.0,
            },
            quantity=1,
            quote_input=dict(FULL_QUOTE_INPUT),
        )
        out = build_execution_layers_from_components(
            _template_from_components(components), ctx
        )
        kinds = {e.get("kind") for e in out.get("errors") or []}
        self.assertNotIn(ERR_FORMULA_UNKNOWN, kinds)
        missing_codes: set[str] = set()
        for e in out.get("errors") or []:
            if e.get("kind") != ERR_MATERIAL_RATE_MISSING:
                continue
            detail = str(e.get("detail") or "")
            for code in VOLUMETRIC_TEMPLATE_MATERIAL_CODES:
                if code in detail:
                    missing_codes.add(code)
        for code in OWNER_CONFIRMED_ACTIVATED_CODES:
            if code in PROFILE_DEPTH_VARIANT_CODES or code in PSU_WATTAGE_VARIANT_CODES:
                continue
            self.assertNotIn(code, missing_codes, f"{code} should have a rate")
        self.assertNotIn(
            TEMPLATE_PROFILE_CODE,
            missing_codes,
            "profile alias should supply template code when return_depth_mm set",
        )
        self.assertNotIn(
            TEMPLATE_PSU_CODE,
            missing_codes,
            "PSU alias should supply template code when selected_psu_watts set",
        )
        for code in PRELIMINARY_COSTING_ALIAS_CODES:
            self.assertNotIn(
                code,
                missing_codes,
                f"{code} resolved via quote_input alias",
            )
        for code in ESTIMATED_PRELIMINARY_ACTIVATED_CODES:
            self.assertNotIn(code, missing_codes)

    def test_template_material_code_coverage(self) -> None:
        components = _volumetric_letters_components()
        found = set()
        for comp in components:
            for line in comp.get("materials") or []:
                mc = line.get("material_code")
                if mc:
                    found.add(mc)
        for code in VOLUMETRIC_TEMPLATE_MATERIAL_CODES:
            self.assertIn(code, found)
        self.assertEqual(set(VOLUMETRIC_TEMPLATE_MATERIAL_CODES), found)
        self.assertTrue(PROFILE_DEPTH_VARIANT_CODES.isdisjoint(found))
        self.assertEqual(
            OWNER_CONFIRMED_ACTIVATED_CODES & found,
            {
                "MAT-ACP-FATA-LITERE",
                "MAT-SPATE-PVC-LITERE",
                "MAT-LED-MODULE",
                "MAT-SABLON-MONTAJ",
                "MAT-VOPSEA-RAL",
            },
        )


if __name__ == "__main__":
    unittest.main()
