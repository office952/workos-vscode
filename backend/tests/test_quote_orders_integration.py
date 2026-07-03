"""
Integration tests for canonical Quote and Order endpoints.

Tests the WorkOS foundation flow:
  POST /api/v1/entities/quotes/price
  POST /api/v1/entities/orders/from-quote/{quote_id}

Rules verified:
  1. Quote priced with valid template and material rates -> 201 with grand_total > 0.
  2. Empty product_template -> 422 with blocked_reasons containing 'product_invalid:*'.
  3. Material without unit_cost -> 422 with blocked_reasons containing 'cost_invalid:*'.
  4. Order from priced quote -> 201 with snapshot, locked.
  5. Order from blocked quote is rejected (prior price call is rejected; cannot even attempt).
  6. Order snapshot is immutable after creation (mutating quote DB row does not change order).
"""

from __future__ import annotations

import json
import os
import sys
import unittest

# Ensure backend root on sys.path so imports resolve
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

# Ensure ORM models are imported so Base.metadata knows them
from models.quotes import Quotes  # noqa: E402,F401
from models.orders import Orders  # noqa: E402,F401

from routers.quotes import router as quotes_router  # noqa: E402
from routers.orders import router as orders_router  # noqa: E402
from services.cost_engine_service import CostEngineWithMaterialRates  # noqa: E402
import services.quote_orchestrator as quote_orchestrator_module  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _sample_template_complete() -> dict:
    return {
        "template_code": "TOTEM-STD",
        "family_id": "totemuri_pyloni",
        "family_name": "Totemuri / Pyloni",
        "components_json": json.dumps(["Cadru metalic", "LED RGB"]),
        "operations_json": json.dumps(
            [
                {
                    "code": "CNC_CUT",
                    "name": "Debitare",
                    "workcenter": "CNC",
                    "estimatedMinutes": 30,
                    "sequence": 1,
                },
                {
                    "code": "ASM",
                    "name": "Asamblare",
                    "workcenter": "assembly",
                    "estimatedMinutes": 60,
                    "sequence": 2,
                },
            ]
        ),
        "required_materials_json": json.dumps(
            [{"materialCode": "MAT-ACP-3", "name": "ACP 3mm alb", "quantity": 2, "unit": "sqm"}]
        ),
        "estimated_hours": 1.5,
        "base_labor_rate": 80,
        "base_margin_pct": 25,
        "active": True,
    }


def _sample_user_config() -> dict:
    return {"quantity": 2, "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300}}


class QuoteOrdersIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_quotes_")
        cls.db.setup()

        async def _override_get_db():
            async with cls.db.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="test@example.com",
                name="Test Admin",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(quotes_router)
        cls.app.include_router(orders_router)
        cls.app.dependency_overrides[get_db] = _override_get_db
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.client.close()
        except Exception:
            pass
        cls.db.teardown()

    def setUp(self) -> None:
        # Reset between tests for full isolation
        self.db.reset_tables([Orders, Quotes])

    # -- Test 1: priced quote with valid config and material rates --
    def test_quote_priced_with_valid_config(self) -> None:
        original_init = quote_orchestrator_module.QuoteOrchestrator.__init__

        def patched_init(self, product_service=None, cost_engine=None, **kwargs):
            original_init(
                self,
                product_service=product_service,
                cost_engine=cost_engine or CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
                **kwargs,
            )

        quote_orchestrator_module.QuoteOrchestrator.__init__ = patched_init
        try:
            resp = self.client.post(
                "/api/v1/entities/quotes/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19},
                    "client_name": "ACME SRL",
                },
            )
        finally:
            quote_orchestrator_module.QuoteOrchestrator.__init__ = original_init

        self.assertEqual(resp.status_code, 201, msg=f"body={resp.text}")
        data = resp.json()
        self.assertIn("quote_id", data)
        self.assertIn("snapshot", data)
        self.assertEqual(data["snapshot"]["status"], "priced")
        self.assertGreater(data["snapshot"]["price"]["gross"], 0)

    # -- Test 2: blocked because product_template is empty/None --
    def test_quote_blocked_invalid_product(self) -> None:
        resp = self.client.post(
            "/api/v1/entities/quotes/price",
            json={
                "product_template": None,
                "user_config": {"quantity": 1},
                "pricing": {"margin_pct": 20, "vat_pct": 19},
            },
        )
        self.assertEqual(resp.status_code, 422, msg=f"body={resp.text}")
        detail = resp.json().get("detail", {})
        self.assertEqual(detail.get("status"), "blocked")
        reasons = detail.get("blocked_reasons") or []
        self.assertTrue(
            any(str(r).startswith("product_invalid:") for r in reasons),
            msg=f"expected product_invalid:* reason, got {reasons}",
        )

    # -- Test 3: blocked because material unit_cost is missing --
    def test_quote_blocked_invalid_cost(self) -> None:
        resp = self.client.post(
            "/api/v1/entities/quotes/price",
            json={
                "product_template": _sample_template_complete(),
                "user_config": _sample_user_config(),
                "pricing": {"margin_pct": 20, "vat_pct": 19},
            },
        )
        self.assertEqual(resp.status_code, 422, msg=f"body={resp.text}")
        detail = resp.json().get("detail", {})
        self.assertEqual(detail.get("status"), "blocked")
        reasons = detail.get("blocked_reasons") or []
        self.assertTrue(
            any(str(r).startswith("cost_invalid:") for r in reasons),
            msg=f"expected cost_invalid:* reason, got {reasons}",
        )

    # -- Test 4: order from priced quote --
    def test_order_from_priced_quote(self) -> None:
        from services.product_readiness_service import (
            ProductReadinessService, ProductReadinessResult, ReadinessSection, ReadinessPolicy
        )
        
        original_init = quote_orchestrator_module.QuoteOrchestrator.__init__

        def patched_init(self, product_service=None, cost_engine=None, **kwargs):
            original_init(
                self,
                product_service=product_service,
                cost_engine=cost_engine or CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
                **kwargs,
            )

        # Mock ProductReadinessService to return ready state
        readiness_obj = ProductReadinessResult(
            entity_type="blueprint",
            entity_id="blueprint:1",
            blueprint_id="template:1",
            overall_status="ready",
            ready_for_quote=True,
            technical_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            costengine_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            document_output_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            visual_prompt_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            execution_preparation_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            policy=ReadinessPolicy(),
            source="backend",
            contract_version="2026-05-15",
        )
        
        original_evaluate = ProductReadinessService.evaluate
        async def mocked_evaluate(self, template_id: int, **kwargs):
            return readiness_obj
        ProductReadinessService.evaluate = mocked_evaluate
        
        quote_orchestrator_module.QuoteOrchestrator.__init__ = patched_init
        try:
            q_resp = self.client.post(
                "/api/v1/entities/quotes/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19},
                    "client_name": "ACME SRL",
                },
            )
        finally:
            quote_orchestrator_module.QuoteOrchestrator.__init__ = original_init
            ProductReadinessService.evaluate = original_evaluate

        self.assertEqual(q_resp.status_code, 201, msg=f"body={q_resp.text}")
        quote_id = q_resp.json()["quote_id"]

        o_resp = self.client.post(f"/api/v1/entities/orders/from-quote/{quote_id}")
        self.assertEqual(o_resp.status_code, 201, msg=f"body={o_resp.text}")
        data = o_resp.json()
        self.assertIn("order_id", data)
        self.assertIn("snapshot", data)
        self.assertEqual(data["snapshot"].get("order_id"), data["order_id"])
        self.assertIsInstance(data["snapshot"].get("order_id"), int)
        self.assertTrue(data["snapshot"]["is_locked"])
        self.assertGreater(data["snapshot"]["final_price"]["gross"], 0)

        list_resp = self.client.get(f"/api/v1/entities/orders?code={data['order_code']}&limit=1")
        self.assertEqual(list_resp.status_code, 200, msg=list_resp.text)
        items = list_resp.json().get("items", [])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].get("payment_status"), "pending")

    # -- Test 5: order rejects blocked quote --
    def test_order_rejects_blocked_quote(self) -> None:
        async def _insert_blocked_quote() -> int:
            async with self.db.session_maker() as session:
                q = Quotes(
                    code="Q-BLOCKED-TEST",
                    client_name="X",
                    status="blocked",
                    version=1,
                    line_items=None,
                )
                session.add(q)
                await session.commit()
                await session.refresh(q)
                return q.id

        quote_id = self.db.run(_insert_blocked_quote())

        resp = self.client.post(f"/api/v1/entities/orders/from-quote/{quote_id}")
        self.assertEqual(resp.status_code, 422, msg=f"body={resp.text}")
        detail = resp.json().get("detail", {})
        self.assertEqual(detail.get("error"), "quote_not_priced")

    # -- Test 6: order snapshot immutable after creation --
    def test_order_snapshot_immutable(self) -> None:
        from services.product_readiness_service import (
            ProductReadinessService, ProductReadinessResult, ReadinessSection, ReadinessPolicy
        )
        
        original_init = quote_orchestrator_module.QuoteOrchestrator.__init__

        def patched_init(self, product_service=None, cost_engine=None, **kwargs):
            original_init(
                self,
                product_service=product_service,
                cost_engine=cost_engine or CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
                **kwargs,
            )

        # Mock ProductReadinessService to return ready state
        readiness_obj = ProductReadinessResult(
            entity_type="blueprint",
            entity_id="blueprint:1",
            blueprint_id="template:1",
            overall_status="ready",
            ready_for_quote=True,
            technical_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            costengine_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            document_output_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            visual_prompt_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            execution_preparation_readiness=ReadinessSection(status="ready", blockers=[], warnings=[]),
            policy=ReadinessPolicy(),
            source="backend",
            contract_version="2026-05-15",
        )
        
        original_evaluate = ProductReadinessService.evaluate
        async def mocked_evaluate(self, template_id: int, **kwargs):
            return readiness_obj
        ProductReadinessService.evaluate = mocked_evaluate

        quote_orchestrator_module.QuoteOrchestrator.__init__ = patched_init
        try:
            q_resp = self.client.post(
                "/api/v1/entities/quotes/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19},
                    "client_name": "ACME SRL",
                },
            )
        finally:
            quote_orchestrator_module.QuoteOrchestrator.__init__ = original_init
            ProductReadinessService.evaluate = original_evaluate

        self.assertEqual(q_resp.status_code, 201)
        quote_id = q_resp.json()["quote_id"]

        o_resp = self.client.post(f"/api/v1/entities/orders/from-quote/{quote_id}")
        self.assertEqual(o_resp.status_code, 201)
        order_id = o_resp.json()["order_id"]
        original_snapshot = o_resp.json()["snapshot"]
        original_gross = original_snapshot["final_price"]["gross"]

        async def _mutate_quote() -> None:
            async with self.db.session_maker() as session:
                q = await session.get(Quotes, quote_id)
                q.line_items = json.dumps({"mutated": True})
                q.grand_total = 999999.99
                await session.commit()

        self.db.run(_mutate_quote())

        async def _read_order() -> dict:
            async with self.db.session_maker() as session:
                o = await session.get(Orders, order_id)
                return {
                    "total_amount": o.total_amount,
                    "snapshot_line_items": o.snapshot_line_items,
                }

        order_row = self.db.run(_read_order())
        self.assertAlmostEqual(float(order_row["total_amount"]), float(original_gross), places=2)
        persisted_snapshot = json.loads(order_row["snapshot_line_items"])
        self.assertEqual(persisted_snapshot.get("order_id"), order_id)
        self.assertIsInstance(persisted_snapshot.get("order_id"), int)
        self.assertTrue(persisted_snapshot.get("is_locked"))
        self.assertAlmostEqual(
            float(persisted_snapshot["final_price"]["gross"]),
            float(original_gross),
            places=2,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)