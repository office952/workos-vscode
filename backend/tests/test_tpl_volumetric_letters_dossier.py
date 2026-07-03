"""TPL-VOLUMETRIC-LETTERS — blueprint dossier seed and readiness integration."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from seeds.seed_active_template_scope import seed_active_template_scope  # noqa: E402
from seeds.seed_build4_templates import seed_build4_templates  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    seed_volumetric_owner_confirmed_prices,
)
from seeds.seed_volumetric_workcenter_rates import (  # noqa: E402
    seed_volumetric_operations_and_rates,
)
from seeds.seed_tpl_volumetric_letters_dossier import (  # noqa: E402
    TEMPLATE_CODE,
    seed_tpl_volumetric_letters_dossier,
    _variants,
    _task_rules,
    _output_blocks,
    _quote_readiness,
)
from services.product_readiness_service import ProductReadinessService  # noqa: E402
from services.product_system_cost_simulation_service import (  # noqa: E402
    ProductSystemCostSimulationService,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

from models.inventory_materials import Inventory_materials  # noqa: E402
from models.product_blueprint_dossier import ProductBlueprintDossier  # noqa: E402
from models.product_templates import Product_templates  # noqa: E402
from sqlalchemy import func, select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


BASE_QUOTE_INPUT = {
    "width_mm": 4800,
    "height_mm": 600,
    "depth_mm": 60,
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
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


class TestVolumetricLettersDossierSeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="vol_dossier_")
        cls.db_fixture.setup()
        _run(cls._seed_templates())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed_templates(cls) -> None:
        from core.database import db_manager

        codes = [
            ("MAT-ACP-FATA-LITERE", "mp"),
            ("MAT-SPATE-PVC-LITERE", "mp"),
            ("MAT-LED-MODULE", "buc"),
            ("MAT-SABLON-MONTAJ", "mp"),
            ("MAT-VOPSEA-RAL", "buc"),
            ("MAT-CONSUMABILE-MONTAJ", "set"),
            ("MAT-PROFIL-LATERAL-LITERE", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-30MM", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-60MM", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-80MM", "ml"),
            ("MAT-PROFIL-LATERAL-LITERE-100MM", "ml"),
            ("MAT-LED-PSU-12V", "buc"),
            ("MAT-LED-PSU-12V-60W", "buc"),
            ("MAT-LED-PSU-12V-100W", "buc"),
            ("MAT-LED-PSU-12V-160W", "buc"),
            ("MAT-LED-PSU-12V-200W", "buc"),
            ("MAT-ORACAL-651", "mp"),
            ("MAT-VINYL-PRINT", "mp"),
            ("MAT-VINYL-PRINT-LAMINATED", "mp"),
            ("MAT-PREMOUNT-BAR-STEEL", "ml"),
            ("MAT-PREMOUNT-BAR-ALUMINUM", "ml"),
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

    async def _tpl_id(self) -> int:
        from core.database import db_manager

        async with db_manager.async_session_maker() as session:
            tpl = (
                await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == TEMPLATE_CODE
                    )
                )
            ).scalar_one()
            return int(tpl.id)

    def test_seed_creates_dossier_row(self) -> None:
        result = _run(seed_tpl_volumetric_letters_dossier())
        self.assertIn(result["action"], {"created", "updated"})
        self.assertIsNotNone(result["dossier_id"])

        async def _check():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                tpl_id = await self._tpl_id()
                row = (
                    await session.execute(
                        select(ProductBlueprintDossier).where(
                            ProductBlueprintDossier.template_id == tpl_id
                        )
                    )
                ).scalar_one_or_none()
                self.assertIsNotNone(row)
                self.assertEqual(row.template_code, TEMPLATE_CODE)
                self.assertEqual(row.status, "approved")

        _run(_check())

    def test_seed_is_idempotent(self) -> None:
        first = _run(seed_tpl_volumetric_letters_dossier())
        second = _run(seed_tpl_volumetric_letters_dossier())
        self.assertEqual(first["dossier_id"], second["dossier_id"])
        self.assertEqual(second["action"], "updated")

        async def _count():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                tpl_id = await self._tpl_id()
                count = (
                    await session.execute(
                        select(func.count(ProductBlueprintDossier.id)).where(
                            ProductBlueprintDossier.template_id == tpl_id
                        )
                    )
                ).scalar_one()
                return int(count or 0)

        self.assertEqual(_run(_count()), 1)

    def test_dossier_documents_allowed_options(self) -> None:
        _run(seed_tpl_volumetric_letters_dossier())
        keys = {v["variant_key"] for v in _variants()}
        for expected in (
            "back_bevel_enabled",
            "face_finish_type",
            "mounting_template_enabled",
            "mounting_system",
            "mounting_bar_profile",
        ):
            self.assertIn(expected, keys)

        rules = _task_rules()["rules"]
        rule_names = {r["task_name"] for r in rules}
        self.assertIn("vector_file_verification", rule_names)
        self.assertIn("cnc_back_cut", rule_names)
        self.assertIn("vinyl_application", rule_names)
        self.assertIn("premount_bars", rule_names)
        self.assertIn("acm_panel_separate_template", rule_names)
        self.assertIn("qc_internal_check", rule_names)
        sequences = [r["sequence"] for r in rules]
        self.assertEqual(sequences, sorted(sequences))
        packaging = next(r for r in rules if r["task_name"] == "packaging")
        qc = next(r for r in rules if r["task_name"] == "qc_internal_check")
        self.assertLess(qc["sequence"], packaging["sequence"])

        blocks = _output_blocks()["blocks"]
        block_ids = {b["block_id"] for b in blocks}
        self.assertIn("mounting_options", block_ids)
        self.assertTrue(_output_blocks().get("short_description"))

    def test_dossier_documents_vector_file_policy(self) -> None:
        _run(seed_tpl_volumetric_letters_dossier())
        qr = _quote_readiness()
        self.assertTrue(qr.get("final_quote_requires_vector_file"))
        self.assertIn("DWG", qr.get("vector_accepted_formats", []))
        self.assertIn("DXF", qr.get("vector_accepted_formats", []))
        self.assertIn("SVG", qr.get("vector_accepted_formats", []))
        policy = qr.get("vector_analysis_policy") or {}
        self.assertEqual(policy.get("dwg"), "attached_source_only_no_auto_analysis")
        self.assertFalse(policy.get("geometry_from_unparsed_file"))

    def test_readiness_dossier_warnings_cleared(self) -> None:
        _run(seed_tpl_volumetric_letters_dossier())

        async def _go():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                tpl_id = await self._tpl_id()
                result = await ProductReadinessService(session).evaluate(tpl_id)
                tech = result.technical_readiness.warnings
                cost = result.costengine_readiness.warnings
                doc = result.document_output_readiness.warnings
                exec_w = result.execution_preparation_readiness.warnings
                return tech, cost, doc, exec_w, result.ready_for_quote

        tech, cost, doc, exec_w, ready = _run(_go())

        async def _blockers():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                tpl_id = await self._tpl_id()
                result = await ProductReadinessService(session).evaluate(tpl_id)
                return result.technical_readiness.blockers

        tech_blockers = _run(_blockers())

        self.assertNotIn("blueprint_dossier_missing", tech)
        self.assertNotIn("blueprint_deprecated", tech_blockers)
        self.assertNotIn("costengine_mapping_missing_no_dossier", cost)
        self.assertNotIn("output_blocks_missing", doc)
        self.assertNotIn("task_rules_missing", exec_w)
        self.assertIn("letters_vector_file_required", tech)
        self.assertFalse(ready)

    def test_seed_repairs_deprecated_status_to_approved(self) -> None:
        async def _deprecate_then_seed():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                tpl_id = await self._tpl_id()
                row = (
                    await session.execute(
                        select(ProductBlueprintDossier).where(
                            ProductBlueprintDossier.template_id == tpl_id
                        )
                    )
                ).scalar_one()
                row.status = "deprecated"
                await session.commit()

            result = await seed_tpl_volumetric_letters_dossier()
            self.assertTrue(result.get("status_repaired_from_deprecated"))
            self.assertEqual(result.get("status"), "approved")

            async with db_manager.async_session_maker() as session:
                row = (
                    await session.execute(
                        select(ProductBlueprintDossier).where(
                            ProductBlueprintDossier.template_id == tpl_id
                        )
                    )
                ).scalar_one()
                readiness = await ProductReadinessService(session).evaluate(tpl_id)
                return (
                    row.status,
                    readiness.technical_readiness.blockers,
                    readiness.ready_for_quote,
                )

        status, blockers, ready = _run(_deprecate_then_seed())
        self.assertEqual(status, "approved")
        self.assertNotIn("blueprint_deprecated", blockers)
        self.assertFalse(ready)

    def test_simulate_cost_unchanged_after_dossier(self) -> None:
        async def _simulate():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                tpl_id = await self._tpl_id()
                svc = ProductSystemCostSimulationService(session)
                r = await svc.simulate(
                    template_id=tpl_id,
                    quantity=1,
                    quote_input=dict(BASE_QUOTE_INPUT),
                )
                cr = r.cost_result or {}
                return (
                    round(float(cr.get("total_cost") or 0), 2),
                    r.status,
                    r.persisted,
                    cr.get("is_valid"),
                )

        before_total, before_status, before_persisted, before_valid = _run(_simulate())
        _run(seed_tpl_volumetric_letters_dossier())
        after_total, after_status, after_persisted, after_valid = _run(_simulate())

        self.assertAlmostEqual(before_total, after_total, places=2)
        self.assertAlmostEqual(after_total, 844.41, places=2)
        self.assertEqual(before_status, "simulated")
        self.assertEqual(after_status, "simulated")
        self.assertFalse(before_persisted)
        self.assertFalse(after_persisted)
        self.assertTrue(before_valid)
        self.assertTrue(after_valid)

    def test_archived_templates_not_touched(self) -> None:
        async def _archived_count():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                return (
                    await session.execute(
                        select(func.count(Product_templates.id)).where(
                            Product_templates.active.is_(False)
                        )
                    )
                ).scalar_one()

        before = _run(_archived_count())
        _run(seed_tpl_volumetric_letters_dossier())
        after = _run(_archived_count())
        self.assertEqual(before, after)
        self.assertGreater(int(after or 0), 0)


if __name__ == "__main__":
    unittest.main()
