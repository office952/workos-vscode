from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from tests._db_fixture import IsolatedDBFixture

from dependencies.auth import get_current_user
from models.orders import Orders
from models.quotes import Quotes
from models.vector_assets import Vector_assets
from routers.vector_assets import router as vector_assets_router
from schemas.auth import UserResponse


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


VALID_SVG = "<svg width='10mm' height='10mm' xmlns='http://www.w3.org/2000/svg'><rect x='0' y='0' width='10' height='10' /></svg>"
UNSUPPORTED_TAG_SVG = "<svg width='10' height='10' xmlns='http://www.w3.org/2000/svg'><path d='M0 0 L10 10' /></svg>"
OVERSIZE_SVG = "<svg>" + (" " * 500100) + "</svg>"


class TestVectorAssetsSecurityLimits(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="vector_assets_sec_testdb_")
        cls.db_fixture.setup()

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="vector-sec@example.com",
                name="Vector Security",
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

    def test_non_svg_extension_rejected(self) -> None:
        payload = {
            "bucket_name": "vector-assets",
            "object_key": "intake/100/sample.pdf",
            "original_filename": "sample.pdf",
            "content_type_reported": "application/pdf",
            "owner_type": "standalone",
            "source_format": "svg",
            "svg_text_dev": VALID_SVG,
        }

        async def _go():
            async with self._client() as c:
                r = await c.post("/api/v1/vector-assets/register-from-storage", json=payload)
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 422)
        self.assertIn(".svg", str(body))

    def test_preview_oversize_svg_rejected(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.post("/api/v1/vector-assets/preview-metrics", json={"svg_text": OVERSIZE_SVG})
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 422)
        self.assertIn("max_length", str(body))

    def test_simple_path_returns_metrics_not_unsupported(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.post("/api/v1/vector-assets/preview-metrics", json={"svg_text": UNSUPPORTED_TAG_SVG})
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["parse_status"], "parsed")
        self.assertNotIn("unsupported_path", body["warnings"])
        self.assertGreater(float(body["metrics"]["perimeter_mm_approx"]), 0)

    def test_empty_path_falls_back_to_viewbox_without_invented_perimeter(self) -> None:
        svg = "<svg viewBox='0 0 10 10' xmlns='http://www.w3.org/2000/svg'><path d=''/></svg>"

        async def _go():
            async with self._client() as c:
                r = await c.post("/api/v1/vector-assets/preview-metrics", json={"svg_text": svg})
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["parse_status"], "parsed")
        self.assertIn("viewbox_bbox_fallback", body["warnings"])
        self.assertIsNone(body["metrics"]["perimeter_mm_approx"])

    def test_object_key_validation_reused(self) -> None:
        payload = {
            "bucket_name": "vector-assets",
            "object_key": "../secret.svg",
            "original_filename": "secret.svg",
            "content_type_reported": "image/svg+xml",
            "owner_type": "standalone",
            "source_format": "svg",
            "svg_text_dev": VALID_SVG,
        }

        async def _go():
            async with self._client() as c:
                r = await c.post("/api/v1/vector-assets/register-from-storage", json=payload)
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 422)
        self.assertIn("Invalid storage object key", str(body))

    def test_forbidden_domain_tables_not_modified(self) -> None:
        async def _go():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                quote_before = (await session.execute(select(func.count()).select_from(Quotes))).scalar_one()
                order_before = (await session.execute(select(func.count()).select_from(Orders))).scalar_one()

            payload = {
                "bucket_name": "vector-assets",
                "object_key": "intake/500/domain-guard.svg",
                "original_filename": "domain-guard.svg",
                "content_type_reported": "image/svg+xml",
                "owner_type": "standalone",
                "source_format": "svg",
                "svg_text_dev": VALID_SVG,
            }

            async with self._client() as c:
                response = await c.post("/api/v1/vector-assets/register-from-storage", json=payload)

            async with db_manager.async_session_maker() as session:
                quote_after = (await session.execute(select(func.count()).select_from(Quotes))).scalar_one()
                order_after = (await session.execute(select(func.count()).select_from(Orders))).scalar_one()
                vector_count = (await session.execute(select(func.count(Vector_assets.id)))).scalar_one()

            return response.status_code, quote_before, quote_after, order_before, order_after, vector_count

        status_code, quote_before, quote_after, order_before, order_after, vector_count = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(quote_before, quote_after)
        self.assertEqual(order_before, order_after)
        self.assertGreaterEqual(vector_count, 1)

    def test_migration_head_file_is_s40(self) -> None:
        migration = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "s40_vector_asset_registry_svg_metrics.py"
        self.assertTrue(migration.exists())
        text = migration.read_text(encoding="utf-8")
        self.assertIn('revision = "s40_vector_asset_registry_svg_metrics"', text)
        self.assertIn('down_revision = "s39_commercial_markup_policies_foundation"', text)
