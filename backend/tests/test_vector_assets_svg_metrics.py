from __future__ import annotations

import asyncio
import unittest

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from tests._db_fixture import IsolatedDBFixture

from dependencies.auth import get_current_user
from models.vector_assets import Vector_assets
from routers.vector_assets import router as vector_assets_router
from schemas.auth import UserResponse


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


VALID_RECT_SVG = """
<svg width=\"100mm\" height=\"50mm\" viewBox=\"0 0 100 50\" xmlns=\"http://www.w3.org/2000/svg\">
  <rect x=\"0\" y=\"0\" width=\"100\" height=\"50\" />
</svg>
""".strip()

INVALID_XML_SVG = "<svg><rect width='10'></svg>"


class TestVectorAssetsSvgMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="vector_assets_testdb_")
        cls.db_fixture.setup()

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="vector@example.com",
                name="Vector Tester",
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

    def test_preview_valid_rect_svg_returns_parsed_metrics(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.post("/api/v1/vector-assets/preview-metrics", json={"svg_text": VALID_RECT_SVG})
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["parse_status"], "parsed")
        self.assertAlmostEqual(float(body["metrics"]["bbox_w_mm"]), 100.0, places=4)
        self.assertAlmostEqual(float(body["metrics"]["bbox_h_mm"]), 50.0, places=4)
        self.assertAlmostEqual(float(body["metrics"]["area_mm2_approx"]), 5000.0, places=4)
        self.assertAlmostEqual(float(body["metrics"]["perimeter_mm_approx"]), 300.0, places=4)

    def test_preview_invalid_xml_fail_closed(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.post("/api/v1/vector-assets/preview-metrics", json={"svg_text": INVALID_XML_SVG})
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["parse_status"], "failed")
        self.assertEqual(body["error_code"], "invalid_xml")

    def test_preview_does_not_persist_asset(self) -> None:
        async def _go():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                before = (await session.execute(select(func.count(Vector_assets.id)))).scalar_one()

            async with self._client() as c:
                response = await c.post("/api/v1/vector-assets/preview-metrics", json={"svg_text": VALID_RECT_SVG})

            async with db_manager.async_session_maker() as session:
                after = (await session.execute(select(func.count(Vector_assets.id)))).scalar_one()

            return response.status_code, before, after

        status_code, before, after = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(before, after)

    def test_register_from_storage_persists_parsed_asset(self) -> None:
        async def _go():
            from core.database import db_manager

            payload = {
                "bucket_name": "vector-assets",
                "object_key": "intake/100/sample.svg",
                "original_filename": "sample.svg",
                "content_type_reported": "image/svg+xml",
                "file_size_bytes": len(VALID_RECT_SVG.encode("utf-8")),
                "owner_type": "standalone",
                "owner_id": None,
                "source_format": "svg",
                "svg_text_dev": VALID_RECT_SVG,
            }

            async with self._client() as c:
                response = await c.post("/api/v1/vector-assets/register-from-storage", json=payload)
                body = response.json()

            asset_id = int(body["asset"]["id"])
            async with db_manager.async_session_maker() as session:
                row = (await session.execute(select(Vector_assets).where(Vector_assets.id == asset_id))).scalar_one()

            return response.status_code, body, row

        status_code, body, row = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["asset"]["parse_status"], "parsed")
        self.assertEqual(row.source_format, "svg")
        self.assertIsNotNone(row.content_sha256)

    def test_get_asset_read_only(self) -> None:
        async def _go():
            payload = {
                "bucket_name": "vector-assets",
                "object_key": "intake/200/readonly.svg",
                "original_filename": "readonly.svg",
                "content_type_reported": "image/svg+xml",
                "file_size_bytes": len(VALID_RECT_SVG.encode("utf-8")),
                "owner_type": "standalone",
                "source_format": "svg",
                "svg_text_dev": VALID_RECT_SVG,
            }
            async with self._client() as c:
                created = await c.post("/api/v1/vector-assets/register-from-storage", json=payload)
                asset_id = created.json()["asset"]["id"]
                fetched = await c.get(f"/api/v1/vector-assets/{asset_id}")
                return fetched.status_code, fetched.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["source_format"], "svg")
        self.assertEqual(body["object_key"], "intake/200/readonly.svg")
