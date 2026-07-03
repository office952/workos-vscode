from __future__ import annotations

import asyncio
import unittest

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from dependencies.auth import get_current_user
from routers.vector_assets import router as vector_assets_router
from schemas.auth import UserResponse
from services.svg_layer_analysis_service import SvgLayerAnalysisService
from services.svg_layer_template_mapping import map_svg_layer_to_template
from tests._db_fixture import IsolatedDBFixture


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


MULTI_LAYER_SVG = """
<svg width="2880mm" height="1000mm" viewBox="0 0 2880 1000"
  xmlns="http://www.w3.org/2000/svg"
  xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
  <g inkscape:groupmode="layer" inkscape:label="TPL-VOLUMETRIC-LETTERS" id="layer-vol">
    <rect x="0" y="0" width="2880" height="1000"/>
  </g>
  <g inkscape:groupmode="layer" inkscape:label="TPL-ACM-CASSETTED-PANEL" id="layer-acm">
    <rect x="0" y="0" width="2880" height="1000"/>
  </g>
  <g inkscape:groupmode="layer" inkscape:label="TPL-CUT-ACM-LETTERS" id="layer-cut">
    <rect x="0" y="0" width="500" height="200"/>
  </g>
  <g inkscape:groupmode="layer" inkscape:label="litere volumetrice" id="layer-alias">
    <rect x="0" y="0" width="100" height="100"/>
  </g>
</svg>
""".strip()


class TestSvgLayerTemplateMapping(unittest.TestCase):
    def test_exact_template_code_maps_directly(self) -> None:
        m = map_svg_layer_to_template("TPL-VOLUMETRIC-LETTERS")
        self.assertEqual(m.mapping_status, "mapped")
        self.assertEqual(m.mapped_template_code, "TPL-VOLUMETRIC-LETTERS")

    def test_alias_is_ambiguous_not_canonical(self) -> None:
        m = map_svg_layer_to_template("litere volumetrice")
        self.assertEqual(m.mapping_status, "ambiguous")
        self.assertIsNone(m.mapped_template_code)
        self.assertEqual(m.suggested_template_code, "TPL-VOLUMETRIC-LETTERS")

    def test_acm_casetted_maps_when_in_known_codes(self) -> None:
        m = map_svg_layer_to_template("TPL-ACM-CASSETTED-PANEL")
        self.assertEqual(m.mapping_status, "mapped")
        self.assertEqual(m.mapped_template_code, "TPL-ACM-CASSETTED-PANEL")

    def test_unknown_tpl_prefix_is_template_missing(self) -> None:
        m = map_svg_layer_to_template("TPL-UNKNOWN-FUTURE")
        self.assertEqual(m.mapping_status, "unmapped")
        self.assertIn("template_missing_for_svg_layer", m.blockers)


class TestSvgLayerAnalysisService(unittest.TestCase):
    def test_analyze_multi_layer_svg(self) -> None:
        result = SvgLayerAnalysisService.analyze(MULTI_LAYER_SVG)
        self.assertEqual(result.parse_status, "parsed")
        self.assertEqual(result.summary["layers_found"], 4)
        by_name = {row.svg_layer_name: row for row in result.layers}
        vol = by_name["TPL-VOLUMETRIC-LETTERS"]
        self.assertEqual(vol.mapping_status, "mapped")
        self.assertEqual(vol.mapped_template_code, "TPL-VOLUMETRIC-LETTERS")
        self.assertAlmostEqual(
            float(vol.quote_input_suggestions.get("letter_face_area_m2") or 0),
            2.88,
            places=2,
        )
        acm = by_name["TPL-ACM-CASSETTED-PANEL"]
        self.assertEqual(acm.mapping_status, "mapped")
        self.assertEqual(acm.mapped_template_code, "TPL-ACM-CASSETTED-PANEL")
        cut = by_name["TPL-CUT-ACM-LETTERS"]
        self.assertEqual(cut.mapping_status, "mapped")
        alias = by_name["litere volumetrice"]
        self.assertEqual(alias.mapping_status, "ambiguous")


class TestSvgLayerAnalysisEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="svg_layer_analysis_testdb_")
        cls.db_fixture.setup()

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="svg@example.com",
                name="SVG Tester",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(vector_assets_router)
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://test")

    def test_analyze_layers_endpoint(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.post(
                    "/api/v1/vector-assets/analyze-layers",
                    json={"svg_text": MULTI_LAYER_SVG},
                )
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["parse_status"], "parsed")
        self.assertEqual(body["summary"]["layers_found"], 4)
