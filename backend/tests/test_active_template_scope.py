"""Active template scope — only TPL-VOLUMETRIC-LETTERS is owner-valid for quotes."""

from __future__ import annotations

import asyncio
import unittest

from sqlalchemy import select

from models.product_templates import Product_templates
from seeds.seed_active_template_scope import seed_active_template_scope
from seeds.seed_build4_templates import seed_build4_templates
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
from services.active_template_scope import (
    OWNER_VALID_ACTIVE_TEMPLATE_CODE,
    is_owner_valid_active_template,
    load_quote_active_template_codes,
    normalize_template_code,
    template_active_for_quote,
)
from services.pricing_registry_service import PricingRegistryService
from services.svg_layer_analysis_service import SvgLayerAnalysisService
from services.svg_layer_template_mapping import map_svg_layer_to_template
from tests._db_fixture import IsolatedDBFixture


LOGO_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO_v1"


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestActiveTemplateScopeSeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture()
        cls.db_fixture.setup()
        _run(seed_build4_templates())
        _run(seed_tpl_volumetric_logo_v1())
        _run(seed_active_template_scope())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    def test_only_volumetric_active_in_db(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                rows = (await session.execute(select(Product_templates))).scalars().all()
                active_codes = sorted(
                    normalize_template_code(r.template_code)
                    for r in rows
                    if r.active is not False and r.template_code
                )
                inactive_count = sum(1 for r in rows if r.active is False)
                return active_codes, inactive_count

        active_codes, inactive_count = _run(_go())
        self.assertEqual(active_codes, [])
        self.assertGreater(inactive_count, 0)

    def test_load_quote_active_template_codes(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                return await load_quote_active_template_codes(session)

        self.assertEqual(_run(_go()), [])

    def test_pricing_registry_only_owner_valid_active(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                reg = await PricingRegistryService(session).build_registry()
                return [u["template_code"] for u in reg.get("template_usage") or []]

        usage_codes = _run(_go())
        self.assertEqual(usage_codes, [])

    def test_inactive_template_not_active_for_quote(self) -> None:
        self.assertFalse(
            template_active_for_quote(
                "TPL-BANNER-STANDARD", db_active=False
            )
        )
        self.assertFalse(
            template_active_for_quote(
                "TPL-ACM-CASSETTED-PANEL", db_active=True
            )
        )
        self.assertTrue(
            template_active_for_quote(
                OWNER_VALID_ACTIVE_TEMPLATE_CODE, db_active=True
            )
        )
        self.assertFalse(template_active_for_quote(LOGO_TEMPLATE_CODE, db_active=True))

    def test_svg_inactive_template_reports_blockers(self) -> None:
        m = map_svg_layer_to_template(
            "TPL-ACM-CASSETTED-PANEL",
            active_template_codes=[OWNER_VALID_ACTIVE_TEMPLATE_CODE],
        )
        self.assertEqual(m.mapping_status, "mapped")
        self.assertEqual(m.mapped_template_code, "TPL-ACM-CASSETTED-PANEL")
        self.assertIn("template_inactive", m.blockers)
        self.assertIn("template_not_active_for_quote", m.blockers)

    def test_svg_volumetric_active_no_inactive_blockers(self) -> None:
        m = map_svg_layer_to_template(
            OWNER_VALID_ACTIVE_TEMPLATE_CODE,
            known_template_codes=[OWNER_VALID_ACTIVE_TEMPLATE_CODE],
            active_template_codes=[OWNER_VALID_ACTIVE_TEMPLATE_CODE],
        )
        self.assertEqual(m.blockers, ())

    def test_svg_analysis_excludes_inactive_from_calculable(self) -> None:
        svg = """
        <svg width="100mm" height="100mm" viewBox="0 0 100 100"
          xmlns="http://www.w3.org/2000/svg"
          xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
          <g inkscape:groupmode="layer" inkscape:label="TPL-VOLUMETRIC-LETTERS" id="v">
            <rect x="0" y="0" width="100" height="100"/>
          </g>
          <g inkscape:groupmode="layer" inkscape:label="TPL-ACM-CASSETTED-PANEL" id="a">
            <rect x="0" y="0" width="100" height="100"/>
          </g>
        </svg>
        """.strip()
        result = SvgLayerAnalysisService.analyze(
            svg,
            active_template_codes=["TPL-VOLUMETRIC-LETTERS"],
        )
        by_name = {row.svg_layer_name: row for row in result.layers}
        self.assertNotIn("template_not_active_for_quote", by_name["TPL-VOLUMETRIC-LETTERS"].blockers)
        self.assertIn("template_not_active_for_quote", by_name["TPL-ACM-CASSETTED-PANEL"].blockers)
        self.assertEqual(result.summary["layers_calculable_preliminary"], 1)


class TestOwnerValidHelpers(unittest.TestCase):
    def test_is_owner_valid_active_template(self) -> None:
        self.assertTrue(is_owner_valid_active_template(OWNER_VALID_ACTIVE_TEMPLATE_CODE.lower()))
        self.assertFalse(is_owner_valid_active_template("tpl-volumetric-letters"))
        self.assertFalse(is_owner_valid_active_template("tpl-volumetric-logo"))
        self.assertFalse(is_owner_valid_active_template("TPL-BANNER-STANDARD"))
