import asyncio
import json
import unittest

from sqlalchemy import select

import models  # noqa: F401
from core.database import db_manager
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from scripts.seed_sync_all import SEED_PIPELINE
from seeds.seed_tpl_letters_component_first_v1 import (
    ALL_TEMPLATE_CODES,
    BACK_TEMPLATE_CODE,
    COMPOSER_TEMPLATE_CODE,
    FACE_TEMPLATE_CODE,
    FINISH_TEMPLATE_CODE,
    LED_TEMPLATE_CODE,
    MOUNTING_TEMPLATE_CODE,
    RETURN_CANT_TEMPLATE_CODE,
    build_letters_component_first_payloads,
    seed_tpl_letters_component_first_v1,
)
from services.product_template_availability_service import ProductTemplateAvailabilityService
from tests._db_fixture import IsolatedDBFixture


def _loads(raw: str | None):
    return json.loads(raw or "null")


class TestSeedTplLettersComponentFirstV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="letters_component_first_")
        cls.db_fixture.setup()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    def setUp(self) -> None:
        self.db_fixture.patch_global_db_manager()
        self.db_fixture.reset_tables([ProductTemplateModuleLink, Product_templates])

    def _run(self, coro):
        return self.db_fixture.run(coro)

    def test_payloads_are_inert_and_complete(self) -> None:
        payloads = build_letters_component_first_payloads()

        self.assertEqual(len(payloads), 7)
        self.assertEqual([payload["template_code"] for payload in payloads], ALL_TEMPLATE_CODES)

        composer = payloads[0]
        self.assertFalse(composer["active"])
        self.assertEqual(_loads(composer["operations_json"]), [])
        self.assertEqual(_loads(composer["required_materials_json"]), [])
        self.assertEqual(len(_loads(composer["components_json"])), 6)

        composer_notes = _loads(composer["notes"])
        self.assertFalse(composer_notes["offerable"])
        self.assertFalse(composer_notes["work_intake_exposed"])
        self.assertFalse(composer_notes["pricing_active"])
        self.assertFalse(composer_notes["product_definition_active"])
        self.assertEqual(len(composer_notes["component_dependency_graph"]), 8)

        by_code = {payload["template_code"]: payload for payload in payloads}
        self.assertEqual(
            _loads(by_code[FACE_TEMPLATE_CODE]["components_json"])[0]["target_product_truth_path"],
            "components.face.instances[]",
        )
        self.assertEqual(
            _loads(by_code[BACK_TEMPLATE_CODE]["components_json"])[0]["target_product_truth_path"],
            "components.back.instances[]",
        )
        self.assertEqual(
            _loads(by_code[RETURN_CANT_TEMPLATE_CODE]["components_json"])[0]["target_product_truth_path"],
            "components.return_cant.instances[]",
        )
        self.assertEqual(
            _loads(by_code[LED_TEMPLATE_CODE]["components_json"])[0]["target_product_truth_path"],
            "components.led.instances[]",
        )
        self.assertEqual(
            _loads(by_code[FINISH_TEMPLATE_CODE]["components_json"])[0]["target_product_truth_path"],
            "components.finish.instances[]",
        )
        self.assertEqual(
            _loads(by_code[MOUNTING_TEMPLATE_CODE]["components_json"])[0]["target_product_truth_path"],
            "components.mounting.instances[]",
        )

    def test_seed_is_idempotent_inactive_and_not_offerable(self) -> None:
        async def _scenario():
            first = await seed_tpl_letters_component_first_v1()
            second = await seed_tpl_letters_component_first_v1()
            async with db_manager.async_session_maker() as session:
                rows = (
                    await session.execute(
                        select(Product_templates).where(Product_templates.template_code.in_(ALL_TEMPLATE_CODES))
                    )
                ).scalars().all()
                link_count = (
                    await session.execute(
                        select(ProductTemplateModuleLink).where(
                            ProductTemplateModuleLink.parent_template_code == COMPOSER_TEMPLATE_CODE
                        )
                    )
                ).scalars().all()
                availability = await ProductTemplateAvailabilityService(session).list_availability(
                    offerable_only=False,
                    include_runtime_modules=True,
                    include_archived=True,
                )
            composer_item = next(item for item in availability.items if item.template_code == COMPOSER_TEMPLATE_CODE)
            return first, second, rows, link_count, composer_item

        first, second, rows, link_rows, composer_item = self._run(_scenario())

        self.assertEqual(first["created_templates"], 7)
        self.assertEqual(second["created_templates"], 0)
        self.assertEqual(second["updated_templates"], 7)
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row.active is False for row in rows))
        self.assertEqual(len(link_rows), 0)
        self.assertFalse(composer_item.quote_offerable)
        self.assertFalse(composer_item.runtime_module)
        self.assertEqual(composer_item.status, "archived")

        for row in rows:
            self.assertEqual(_loads(row.operations_json), [])
            self.assertEqual(_loads(row.required_materials_json), [])
            notes = _loads(row.notes)
            self.assertFalse(notes["offerable"])
            self.assertFalse(notes["work_intake_exposed"])
            self.assertFalse(notes["pricing_active"])
            self.assertFalse(notes["product_definition_active"])

    def test_seed_does_not_touch_old_letters_or_live_seed_pipeline(self) -> None:
        async def _insert_old_template():
            async with db_manager.async_session_maker() as session:
                session.add(
                    Product_templates(
                        template_code="TPL-VOLUMETRIC-LETTERS_v2",
                        family_id="legacy_family",
                        family_name="Legacy Letters",
                        description="sentinel legacy row",
                        components_json=json.dumps([{"component_id": "legacy"}], ensure_ascii=False),
                        operations_json=json.dumps([{"code": "LEGACY_OP"}], ensure_ascii=False),
                        required_materials_json=json.dumps([{"materialCode": "MAT-LEGACY"}], ensure_ascii=False),
                        estimated_hours=12.5,
                        base_labor_rate=91.0,
                        base_margin_pct=17.0,
                        active=True,
                        notes="legacy sentinel notes",
                    )
                )
                await session.commit()

        async def _load_old_template():
            async with db_manager.async_session_maker() as session:
                row = (
                    await session.execute(
                        select(Product_templates).where(Product_templates.template_code == "TPL-VOLUMETRIC-LETTERS_v2")
                    )
                ).scalar_one()
                return {
                    "description": row.description,
                    "components_json": row.components_json,
                    "operations_json": row.operations_json,
                    "required_materials_json": row.required_materials_json,
                    "estimated_hours": row.estimated_hours,
                    "base_labor_rate": row.base_labor_rate,
                    "base_margin_pct": row.base_margin_pct,
                    "active": row.active,
                    "notes": row.notes,
                }

        self._run(_insert_old_template())
        before = self._run(_load_old_template())
        self._run(seed_tpl_letters_component_first_v1())
        after = self._run(_load_old_template())

        self.assertEqual(before, after)
        self.assertFalse(any(name == "tpl_letters_component_first_v1" for name, _fn in SEED_PIPELINE))
        self.assertFalse(
            any(
                getattr(seed_fn, "__name__", "") == "seed_tpl_letters_component_first_v1"
                for _name, seed_fn in SEED_PIPELINE
            )
        )


if __name__ == "__main__":
    unittest.main()