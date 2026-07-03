from __future__ import annotations

import asyncio
import json
import unittest

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from tests._db_fixture import IsolatedDBFixture

from dependencies.auth import get_current_user
from models.inventory_material_price_history import Inventory_material_price_history
from models.inventory_materials import Inventory_materials
from models.order_output_snapshot_references import OrderOutputSnapshotReference
from models.orders import Orders
from models.quote_output_snapshots import QuoteOutputSnapshot
from models.quotes import Quotes
from models.vector_assets import Vector_assets
from routers.vector_assets import router as vector_assets_router
from schemas.auth import UserResponse


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestVectorAssetsSheetFitPreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="vector_assets_fit_testdb_")
        cls.db_fixture.setup()

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="vector-fit@example.com",
                name="Vector Fit Tester",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(vector_assets_router)
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user

        _run(cls._seed())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager

        async with db_manager.async_session_maker() as session:
            mat_fit = Inventory_materials(
                code="MAT-FIT-RECT",
                name="Material fit direct",
                category="rigid",
                unit="mp",
                status="active",
                unit_cost=10.0,
                sheet_format_type="sheet",
                sheet_width=120.0,
                sheet_height=80.0,
                sheet_unit="mm",
                usable_width=120.0,
                usable_height=80.0,
                format_source="manual",
                format_verified=True,
            )
            mat_rotate = Inventory_materials(
                code="MAT-FIT-ROTATE",
                name="Material fit rotate",
                category="rigid",
                unit="mp",
                status="active",
                unit_cost=10.0,
                sheet_format_type="sheet",
                sheet_width=70.0,
                sheet_height=100.0,
                sheet_unit="mm",
                usable_width=70.0,
                usable_height=100.0,
                format_source="manual",
                format_verified=True,
            )
            mat_not_fit = Inventory_materials(
                code="MAT-NOT-FIT",
                name="Material no fit",
                category="rigid",
                unit="mp",
                status="active",
                unit_cost=10.0,
                sheet_format_type="sheet",
                sheet_width=60.0,
                sheet_height=60.0,
                sheet_unit="mm",
                usable_width=60.0,
                usable_height=60.0,
                format_source="manual",
                format_verified=True,
            )

            session.add_all([mat_fit, mat_rotate, mat_not_fit])
            await session.flush()

            asset_parsed = Vector_assets(
                asset_code="VAS-FIT-001",
                owner_type="standalone",
                original_filename="fit.svg",
                bucket_name="vector-assets",
                object_key="fit/001.svg",
                source_format="svg",
                parse_status="parsed",
                parse_warnings_json="[]",
                bbox_w_mm=100.0,
                bbox_h_mm=70.0,
                area_mm2_approx=7000.0,
                perimeter_mm_approx=340.0,
                metrics_version="v1",
                file_size_bytes=100,
            )
            asset_failed = Vector_assets(
                asset_code="VAS-FIT-FAILED",
                owner_type="standalone",
                original_filename="failed.svg",
                bucket_name="vector-assets",
                object_key="fit/failed.svg",
                source_format="svg",
                parse_status="failed",
                parse_warnings_json=json.dumps(["invalid_xml"]),
                parse_error_code="invalid_xml",
                parse_error_detail="broken",
                metrics_version="v1",
                file_size_bytes=100,
            )
            asset_missing_bbox = Vector_assets(
                asset_code="VAS-FIT-NOBBOX",
                owner_type="standalone",
                original_filename="nobbox.svg",
                bucket_name="vector-assets",
                object_key="fit/nobbox.svg",
                source_format="svg",
                parse_status="parsed",
                parse_warnings_json="[]",
                bbox_w_mm=None,
                bbox_h_mm=None,
                metrics_version="v1",
                file_size_bytes=100,
            )

            session.add_all([asset_parsed, asset_failed, asset_missing_bbox])
            await session.commit()

            cls.material_fit_id = mat_fit.id
            cls.material_rotate_id = mat_rotate.id
            cls.material_not_fit_id = mat_not_fit.id
            cls.asset_parsed_id = asset_parsed.id
            cls.asset_failed_id = asset_failed.id
            cls.asset_missing_bbox_id = asset_missing_bbox.id

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://test")

    def test_parsed_asset_fits_without_rotation(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get(
                    f"/api/v1/vector-assets/{self.asset_parsed_id}/sheet-fit-preview",
                    params={"material_id": self.material_fit_id},
                )
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["fit_status"], "fits")
        self.assertTrue(body["fits_without_rotation"])
        self.assertFalse(body["fits_with_rotation"])
        self.assertEqual(body["recommended_rotation"], "none")

    def test_parsed_asset_fits_only_with_rotation(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get(
                    f"/api/v1/vector-assets/{self.asset_parsed_id}/sheet-fit-preview",
                    params={"material_id": self.material_rotate_id},
                )
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["fit_status"], "fits_rotated")
        self.assertFalse(body["fits_without_rotation"])
        self.assertTrue(body["fits_with_rotation"])
        self.assertEqual(body["recommended_rotation"], "rotate_90")

    def test_parsed_asset_does_not_fit(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get(
                    f"/api/v1/vector-assets/{self.asset_parsed_id}/sheet-fit-preview",
                    params={"material_id": self.material_not_fit_id},
                )
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["fit_status"], "not_fit")
        self.assertEqual(body["recommended_rotation"], "not_fit")

    def test_failed_asset_returns_cannot_evaluate(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get(
                    f"/api/v1/vector-assets/{self.asset_failed_id}/sheet-fit-preview",
                    params={"material_id": self.material_fit_id},
                )
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["fit_status"], "cannot_evaluate")
        self.assertEqual(body["recommended_rotation"], "cannot_evaluate")

    def test_missing_bbox_returns_cannot_evaluate(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get(
                    f"/api/v1/vector-assets/{self.asset_missing_bbox_id}/sheet-fit-preview",
                    params={"material_id": self.material_fit_id},
                )
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(body["fit_status"], "cannot_evaluate")
        self.assertIn("bbox", body["fit_reason"].lower())

    def test_invalid_material_id_returns_404(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get(
                    f"/api/v1/vector-assets/{self.asset_parsed_id}/sheet-fit-preview",
                    params={"material_id": 999999},
                )
                return r.status_code, r.json()

        status_code, body = _run(_go())
        self.assertEqual(status_code, 404)
        self.assertIn("inventory material not found", str(body))

    def test_preview_does_not_modify_vector_asset(self) -> None:
        async def _go():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                before = (
                    await session.execute(select(Vector_assets).where(Vector_assets.id == self.asset_parsed_id))
                ).scalar_one()
                before_hash = (
                    before.parse_status,
                    before.bbox_w_mm,
                    before.bbox_h_mm,
                    before.updated_at,
                )

            async with self._client() as c:
                response = await c.get(
                    f"/api/v1/vector-assets/{self.asset_parsed_id}/sheet-fit-preview",
                    params={"material_id": self.material_fit_id},
                )

            async with db_manager.async_session_maker() as session:
                after = (
                    await session.execute(select(Vector_assets).where(Vector_assets.id == self.asset_parsed_id))
                ).scalar_one()
                after_hash = (
                    after.parse_status,
                    after.bbox_w_mm,
                    after.bbox_h_mm,
                    after.updated_at,
                )

            return response.status_code, before_hash, after_hash

        status_code, before_hash, after_hash = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(before_hash, after_hash)

    def test_preview_does_not_modify_inventory_material(self) -> None:
        async def _go():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                before_material = (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.id == self.material_fit_id)
                    )
                ).scalar_one()
                before_hash = (
                    before_material.unit_cost,
                    before_material.stock_current,
                    before_material.updated_at,
                )
                price_history_before = (
                    await session.execute(select(func.count()).select_from(Inventory_material_price_history))
                ).scalar_one()

            async with self._client() as c:
                response = await c.get(
                    f"/api/v1/vector-assets/{self.asset_parsed_id}/sheet-fit-preview",
                    params={"material_id": self.material_fit_id},
                )

            async with db_manager.async_session_maker() as session:
                after_material = (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.id == self.material_fit_id)
                    )
                ).scalar_one()
                after_hash = (
                    after_material.unit_cost,
                    after_material.stock_current,
                    after_material.updated_at,
                )
                price_history_after = (
                    await session.execute(select(func.count()).select_from(Inventory_material_price_history))
                ).scalar_one()

            return response.status_code, before_hash, after_hash, price_history_before, price_history_after

        status_code, before_hash, after_hash, ph_before, ph_after = _run(_go())
        self.assertEqual(status_code, 200)
        self.assertEqual(before_hash, after_hash)
        self.assertEqual(ph_before, ph_after)

    def test_no_forbidden_side_effects(self) -> None:
        async def _go():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                quotes_before = (await session.execute(select(func.count()).select_from(Quotes))).scalar_one()
                orders_before = (await session.execute(select(func.count()).select_from(Orders))).scalar_one()
                quote_snap_before = (
                    await session.execute(select(func.count()).select_from(QuoteOutputSnapshot))
                ).scalar_one()
                order_snap_before = (
                    await session.execute(select(func.count()).select_from(OrderOutputSnapshotReference))
                ).scalar_one()

            async with self._client() as c:
                response = await c.get(
                    f"/api/v1/vector-assets/{self.asset_parsed_id}/sheet-fit-preview",
                    params={"material_id": self.material_fit_id},
                )

            async with db_manager.async_session_maker() as session:
                quotes_after = (await session.execute(select(func.count()).select_from(Quotes))).scalar_one()
                orders_after = (await session.execute(select(func.count()).select_from(Orders))).scalar_one()
                quote_snap_after = (
                    await session.execute(select(func.count()).select_from(QuoteOutputSnapshot))
                ).scalar_one()
                order_snap_after = (
                    await session.execute(select(func.count()).select_from(OrderOutputSnapshotReference))
                ).scalar_one()

            return (
                response.status_code,
                quotes_before,
                quotes_after,
                orders_before,
                orders_after,
                quote_snap_before,
                quote_snap_after,
                order_snap_before,
                order_snap_after,
            )

        (
            status_code,
            quotes_before,
            quotes_after,
            orders_before,
            orders_after,
            quote_snap_before,
            quote_snap_after,
            order_snap_before,
            order_snap_after,
        ) = _run(_go())

        self.assertEqual(status_code, 200)
        self.assertEqual(quotes_before, quotes_after)
        self.assertEqual(orders_before, orders_after)
        self.assertEqual(quote_snap_before, quote_snap_after)
        self.assertEqual(order_snap_before, order_snap_after)
