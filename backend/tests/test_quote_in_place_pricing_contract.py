from __future__ import annotations

import json
import os
import sys
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

from models.intake_requests import Intake_requests  # noqa: E402,F401
from models.orders import Orders  # noqa: E402,F401
from models.product_families import Product_families  # noqa: E402,F401
from models.product_templates import Product_templates  # noqa: E402,F401
from models.quotes import Quotes  # noqa: E402,F401

from routers.intake_requests import router as intake_router  # noqa: E402
from routers.orders import router as orders_router  # noqa: E402
from routers.quotes import router as quotes_router  # noqa: E402
from services.cost_engine_service import CostEngineWithMaterialRates  # noqa: E402
from services.cost_engine_service import CostEngineService  # noqa: E402
import services.quote_orchestrator as quote_orchestrator_module  # noqa: E402
from services.product_readiness_service import (  # noqa: E402
    ProductReadinessResult,
    ProductReadinessService,
    ReadinessPolicy,
    ReadinessSection,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _sample_template_complete() -> dict:
    return {
        "id": 1,
        "template_code": "TOTEM-STD",
        "family_id": "print",
        "family_name": "Print",
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


class TestQuoteInPlacePricingContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_quote_in_place_")
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
        cls.app.include_router(intake_router)
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
        self.db.reset_tables([Orders, Quotes, Intake_requests, Product_families, Product_templates])

        async def _seed_family() -> None:
            async with self.db.session_maker() as session:
                session.add(
                    Product_families(
                        family_id="print",
                        label="Print",
                        category="indoor",
                        active=True,
                        description="Print products",
                    )
                )
                await session.commit()

        self.db.run(_seed_family())

    def test_in_place_pricing_keeps_quote_identity_and_intake_linkage(self) -> None:
        intake_payload = {
            "code": "WI-INPLACE-001",
            "client_name": "InPlace Client",
            "contact_person": "Alex Marin",
            "product_family": "print",
            "description": "Produs test in-place pricing",
            "dimensions": "1000x3000x300",
            "quantity": 2,
            "status": "ready_for_quote",
            "assigned_to": "sales1",
            "priority": "medium",
            "delivery_type": "standard",
        }
        intake_resp = self.client.post("/api/v1/entities/intake_requests", json=intake_payload)
        self.assertEqual(intake_resp.status_code, 201, msg=intake_resp.text)
        intake_id = intake_resp.json()["id"]

        from_intake_resp = self.client.post(f"/api/v1/entities/quotes/from-intake/{intake_id}")
        self.assertEqual(from_intake_resp.status_code, 201, msg=from_intake_resp.text)
        draft_quote_id = from_intake_resp.json()["quote_id"]

        original_orch_init = quote_orchestrator_module.QuoteOrchestrator.__init__
        original_readiness_eval = ProductReadinessService.evaluate

        def _patched_orch_init(self, product_service=None, cost_engine=None, **kwargs):
            original_orch_init(
                self,
                product_service=product_service,
                cost_engine=cost_engine or CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
                **kwargs,
            )

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

        async def _mocked_evaluate(self, template_id: int, **kwargs):
            return readiness_obj

        quote_orchestrator_module.QuoteOrchestrator.__init__ = _patched_orch_init
        ProductReadinessService.evaluate = _mocked_evaluate
        try:
            price_resp = self.client.post(
                f"/api/v1/entities/quotes/{draft_quote_id}/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19},
                    "client_name": "InPlace Client",
                },
            )
        finally:
            quote_orchestrator_module.QuoteOrchestrator.__init__ = original_orch_init
            ProductReadinessService.evaluate = original_readiness_eval

        self.assertEqual(price_resp.status_code, 200, msg=price_resp.text)
        price_data = price_resp.json()
        self.assertEqual(price_data["quote_id"], draft_quote_id)
        self.assertEqual(price_data["snapshot"]["status"], "priced")

        quote_get_resp = self.client.get(f"/api/v1/entities/quotes/{draft_quote_id}")
        self.assertEqual(quote_get_resp.status_code, 200, msg=quote_get_resp.text)
        quote_row = quote_get_resp.json()
        self.assertEqual(quote_row["id"], draft_quote_id)
        self.assertEqual(quote_row["status"], "priced")
        self.assertEqual(quote_row["intake_id"], intake_id)
        self.assertIsNotNone(quote_row.get("line_items"))

        order_resp = self.client.post(f"/api/v1/entities/orders/from-quote/{draft_quote_id}")
        self.assertEqual(order_resp.status_code, 201, msg=order_resp.text)
        order_data = order_resp.json()
        self.assertIn("order_id", order_data)

        rollback_resp = self.client.put(
            f"/api/v1/entities/quotes/{draft_quote_id}",
            json={"status": "draft"},
        )
        self.assertEqual(rollback_resp.status_code, 422, msg=rollback_resp.text)

    def test_sent_quote_revision_increments_version_and_archives_history(self) -> None:
        revision_source = {
            "product_template": _sample_template_complete(),
            "user_config": _sample_user_config(),
            "pricing": {"margin_pct": 25, "vat_pct": 19, "discount_pct": 0},
        }
        prior_wrapper = {
            "line_items": {"status": "priced", "price": {"net": 100, "gross": 119}},
            "revision_source": revision_source,
        }
        quote_payload = {
            "code": "Q-REV-SENT-001",
            "client_name": "Revision Client",
            "status": "sent",
            "version": 2,
            "line_items": json.dumps(prior_wrapper),
            "subtotal": 100.0,
            "grand_total": 119.0,
            "margin_pct": 25.0,
            "discount_pct": 0.0,
            "vat": 19.0,
            "total_before_vat": 100.0,
        }
        create_resp = self.client.post("/api/v1/entities/quotes", json=quote_payload)
        self.assertEqual(create_resp.status_code, 201, msg=create_resp.text)
        quote_id = create_resp.json()["id"]

        original_orch_init = quote_orchestrator_module.QuoteOrchestrator.__init__
        original_readiness_eval = ProductReadinessService.evaluate

        def _patched_orch_init(self, product_service=None, cost_engine=None, **kwargs):
            original_orch_init(
                self,
                product_service=product_service,
                cost_engine=cost_engine or CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
                **kwargs,
            )

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

        async def _mocked_evaluate(self, template_id: int, **kwargs):
            return readiness_obj

        quote_orchestrator_module.QuoteOrchestrator.__init__ = _patched_orch_init
        ProductReadinessService.evaluate = _mocked_evaluate
        try:
            resp = self.client.post(
                f"/api/v1/entities/quotes/{quote_id}/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19, "discount_pct": 10},
                    "client_name": "Revision Client",
                },
            )
        finally:
            quote_orchestrator_module.QuoteOrchestrator.__init__ = original_orch_init
            ProductReadinessService.evaluate = original_readiness_eval

        self.assertEqual(resp.status_code, 200, msg=resp.text)
        data = resp.json()
        self.assertTrue(data.get("revised"))
        self.assertEqual(data.get("quote_version"), 3)

        quote_get_resp = self.client.get(f"/api/v1/entities/quotes/{quote_id}")
        self.assertEqual(quote_get_resp.status_code, 200, msg=quote_get_resp.text)
        quote_row = quote_get_resp.json()
        self.assertEqual(quote_row["status"], "priced")
        self.assertEqual(quote_row["version"], 3)
        self.assertEqual(float(quote_row["discount_pct"]), 10.0)

        wrapper = json.loads(quote_row["line_items"])
        self.assertIsInstance(wrapper.get("revision_history"), list)
        self.assertEqual(len(wrapper["revision_history"]), 1)
        self.assertEqual(wrapper["revision_history"][0]["version"], 2)

    def test_revision_rejects_terminal_accepted_quote(self) -> None:
        quote_payload = {
            "code": "Q-REV-ACCEPT-001",
            "client_name": "Accepted",
            "status": "accepted",
            "version": 1,
            "line_items": json.dumps({"test": True}),
            "subtotal": 10.0,
            "grand_total": 11.9,
            "margin_pct": 20.0,
            "discount_pct": 0.0,
            "vat": 19.0,
            "total_before_vat": 10.0,
        }
        create_resp = self.client.post("/api/v1/entities/quotes", json=quote_payload)
        self.assertEqual(create_resp.status_code, 201, msg=create_resp.text)
        quote_id = create_resp.json()["id"]

        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/price",
            json={
                "product_template": _sample_template_complete(),
                "user_config": _sample_user_config(),
                "pricing": {"margin_pct": 25, "vat_pct": 19, "discount_pct": 5},
                "client_name": "Accepted",
            },
        )
        self.assertEqual(resp.status_code, 422, msg=resp.text)
        detail = resp.json().get("detail", {})
        self.assertEqual(detail.get("error"), "quote_not_eligible_for_revision")

    def test_revision_rejects_excessive_discount(self) -> None:
        quote_payload = {
            "code": "Q-REV-DISC-001",
            "client_name": "Discount",
            "status": "priced",
            "version": 1,
            "line_items": json.dumps({"test": True}),
            "subtotal": 10.0,
            "grand_total": 11.9,
            "margin_pct": 20.0,
            "discount_pct": 0.0,
            "vat": 19.0,
            "total_before_vat": 10.0,
        }
        create_resp = self.client.post("/api/v1/entities/quotes", json=quote_payload)
        self.assertEqual(create_resp.status_code, 201, msg=create_resp.text)
        quote_id = create_resp.json()["id"]

        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/price",
            json={
                "product_template": _sample_template_complete(),
                "user_config": _sample_user_config(),
                "pricing": {"margin_pct": 25, "vat_pct": 19, "discount_pct": 75},
                "client_name": "Discount",
            },
        )
        self.assertEqual(resp.status_code, 422, msg=resp.text)
        detail = resp.json().get("detail", {})
        self.assertEqual(detail.get("error"), "invalid_discount")

    def test_legacy_snapshot_revision_reconstructs_source_on_demand(self) -> None:
        async def _seed_template() -> int:
            async with self.db.session_maker() as session:
                tpl = Product_templates(
                    template_code="TOTEM-STD",
                    family_id="print",
                    family_name="Print",
                    components_json=json.dumps(["Cadru metalic"]),
                    operations_json=json.dumps(
                        [
                            {
                                "code": "ASM",
                                "name": "Asamblare",
                                "workcenter": "assembly",
                                "estimatedMinutes": 60,
                                "sequence": 1,
                            }
                        ]
                    ),
                    required_materials_json=json.dumps(
                        [{"materialCode": "MAT-ACP-3", "name": "ACP", "quantity": 2, "unit": "sqm"}]
                    ),
                    active=True,
                )
                session.add(tpl)
                await session.commit()
                await session.refresh(tpl)
                return int(tpl.id)

        template_id = self.db.run(_seed_template())
        legacy_snapshot = {
            "template_id": template_id,
            "product_definition": {
                "product_id": "TOTEM-STD",
                "quantity": 2,
                "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300},
            },
            "pricing": {"margin_pct": 25.0, "discount_pct": 0.0, "vat_pct": 19.0},
            "cost_result": {"total_cost": 80.0, "breakdown": []},
            "price": {"net": 100.0, "gross": 119.0},
            "status": "priced",
            "blocked_reasons": [],
        }
        quote_payload = {
            "code": "Q-LEGACY-REV-001",
            "client_name": "Legacy Client",
            "status": "sent",
            "version": 1,
            "line_items": json.dumps({"line_items": legacy_snapshot}),
            "subtotal": 100.0,
            "grand_total": 119.0,
            "margin_pct": 25.0,
            "discount_pct": 0.0,
            "vat": 19.0,
            "total_before_vat": 100.0,
        }
        create_resp = self.client.post("/api/v1/entities/quotes", json=quote_payload)
        self.assertEqual(create_resp.status_code, 201, msg=create_resp.text)
        quote_id = create_resp.json()["id"]

        original_orch_init = quote_orchestrator_module.QuoteOrchestrator.__init__
        original_readiness_eval = ProductReadinessService.evaluate

        def _patched_orch_init(self, product_service=None, cost_engine=None, **kwargs):
            original_orch_init(
                self,
                product_service=product_service,
                cost_engine=cost_engine or CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
                **kwargs,
            )

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

        async def _mocked_evaluate(self, template_id: int, **kwargs):
            return readiness_obj

        quote_orchestrator_module.QuoteOrchestrator.__init__ = _patched_orch_init
        ProductReadinessService.evaluate = _mocked_evaluate
        try:
            resp = self.client.post(
                f"/api/v1/entities/quotes/{quote_id}/price",
                json={
                    "pricing": {"margin_pct": 25, "vat_pct": 19, "discount_pct": 10},
                    "client_name": "Legacy Client",
                },
            )
        finally:
            quote_orchestrator_module.QuoteOrchestrator.__init__ = original_orch_init
            ProductReadinessService.evaluate = original_readiness_eval

        self.assertEqual(resp.status_code, 200, msg=resp.text)
        data = resp.json()
        self.assertTrue(data.get("revised"))
        self.assertTrue(data.get("legacy_reconstructed"))
        self.assertEqual(data.get("quote_version"), 2)

        quote_get_resp = self.client.get(f"/api/v1/entities/quotes/{quote_id}")
        wrapper = json.loads(quote_get_resp.json()["line_items"])
        self.assertIn("revision_source", wrapper)
        self.assertTrue(wrapper["revision_source"].get("legacy_reconstructed"))

    def test_legacy_flat_line_items_returns_controlled_error(self) -> None:
        quote_payload = {
            "code": "Q-LEGACY-FLAT-001",
            "client_name": "Flat Legacy",
            "status": "priced",
            "version": 1,
            "line_items": json.dumps(
                [{"description": "Linie veche", "quantity": 1, "unit_price": 10, "total": 10}]
            ),
            "subtotal": 10.0,
            "grand_total": 11.9,
            "margin_pct": 20.0,
            "discount_pct": 0.0,
            "vat": 19.0,
            "total_before_vat": 10.0,
        }
        create_resp = self.client.post("/api/v1/entities/quotes", json=quote_payload)
        self.assertEqual(create_resp.status_code, 201, msg=create_resp.text)
        quote_id = create_resp.json()["id"]

        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/price",
            json={"pricing": {"margin_pct": 20, "vat_pct": 19, "discount_pct": 5}},
        )
        self.assertEqual(resp.status_code, 422, msg=resp.text)
        detail = resp.json().get("detail", {})
        self.assertEqual(detail.get("error"), "legacy_revision_source_missing")

    def test_cost_invalid_blocks_create_and_in_place_with_same_contract(self) -> None:
        async def _seed_draft_quote() -> int:
            async with self.db.session_maker() as session:
                quote = Quotes(
                    code="Q-COST-BLOCK-001",
                    client_name="Blocked Client",
                    status="draft",
                    version=1,
                    line_items=json.dumps({"draft": True}),
                    subtotal=0.0,
                    grand_total=0.0,
                    margin_pct=0.0,
                    discount_pct=0.0,
                    vat=19.0,
                    total_before_vat=0.0,
                )
                session.add(quote)
                await session.commit()
                await session.refresh(quote)
                return int(quote.id)

        async def _count_quotes() -> int:
            async with self.db.session_maker() as session:
                total = await session.scalar(select(func.count(Quotes.id)))
                return int(total or 0)

        draft_quote_id = self.db.run(_seed_draft_quote())
        before_count = self.db.run(_count_quotes())

        original_orch_init = quote_orchestrator_module.QuoteOrchestrator.__init__
        original_readiness_eval = ProductReadinessService.evaluate

        def _patched_orch_init(self, product_service=None, cost_engine=None, **kwargs):
            original_orch_init(
                self,
                product_service=product_service,
                cost_engine=cost_engine or CostEngineService(),
                **kwargs,
            )

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

        async def _mocked_evaluate(self, template_id: int, **kwargs):
            return readiness_obj

        quote_orchestrator_module.QuoteOrchestrator.__init__ = _patched_orch_init
        ProductReadinessService.evaluate = _mocked_evaluate
        try:
            create_resp = self.client.post(
                "/api/v1/entities/quotes/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19},
                    "client_name": "Blocked Create",
                },
            )
            self.assertEqual(create_resp.status_code, 422, msg=create_resp.text)
            create_detail = create_resp.json().get("detail", {})
            self.assertEqual(create_detail.get("status"), "blocked")
            self.assertTrue(
                any(str(r).startswith("cost_invalid:") for r in create_detail.get("blocked_reasons", [])),
                msg=f"expected cost_invalid reasons, got {create_detail}",
            )

            in_place_resp = self.client.post(
                f"/api/v1/entities/quotes/{draft_quote_id}/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19},
                    "client_name": "Blocked In Place",
                },
            )
            self.assertEqual(in_place_resp.status_code, 422, msg=in_place_resp.text)
            in_place_detail = in_place_resp.json().get("detail", {})
            self.assertEqual(in_place_detail.get("status"), "blocked")
            self.assertTrue(
                any(str(r).startswith("cost_invalid:") for r in in_place_detail.get("blocked_reasons", [])),
                msg=f"expected cost_invalid reasons, got {in_place_detail}",
            )
        finally:
            quote_orchestrator_module.QuoteOrchestrator.__init__ = original_orch_init
            ProductReadinessService.evaluate = original_readiness_eval

        after_count = self.db.run(_count_quotes())
        self.assertEqual(before_count, after_count)

        quote_get_resp = self.client.get(f"/api/v1/entities/quotes/{draft_quote_id}")
        self.assertEqual(quote_get_resp.status_code, 200, msg=quote_get_resp.text)
        quote_row = quote_get_resp.json()
        self.assertEqual(quote_row.get("status"), "draft")

    def test_create_and_in_place_success_persist_equivalent_snapshot_shape(self) -> None:
        intake_payload = {
            "code": "WI-SHAPE-001",
            "client_name": "Shape Client",
            "contact_person": "Ioana Pop",
            "product_family": "print",
            "description": "Parity snapshot shape",
            "dimensions": "1000x3000x300",
            "quantity": 2,
            "status": "ready_for_quote",
            "assigned_to": "sales1",
            "priority": "medium",
            "delivery_type": "standard",
        }
        intake_resp = self.client.post("/api/v1/entities/intake_requests", json=intake_payload)
        self.assertEqual(intake_resp.status_code, 201, msg=intake_resp.text)
        intake_id = intake_resp.json()["id"]

        draft_resp = self.client.post(f"/api/v1/entities/quotes/from-intake/{intake_id}")
        self.assertEqual(draft_resp.status_code, 201, msg=draft_resp.text)
        draft_quote_id = draft_resp.json()["quote_id"]

        original_orch_init = quote_orchestrator_module.QuoteOrchestrator.__init__
        original_readiness_eval = ProductReadinessService.evaluate

        def _patched_orch_init(self, product_service=None, cost_engine=None, **kwargs):
            original_orch_init(
                self,
                product_service=product_service,
                cost_engine=cost_engine or CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
                **kwargs,
            )

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

        async def _mocked_evaluate(self, template_id: int, **kwargs):
            return readiness_obj

        def _extract_snapshot_dict(raw_line_items: str) -> dict:
            payload = json.loads(raw_line_items)
            if isinstance(payload, dict) and isinstance(payload.get("line_items"), dict):
                return payload["line_items"]
            return payload

        quote_orchestrator_module.QuoteOrchestrator.__init__ = _patched_orch_init
        ProductReadinessService.evaluate = _mocked_evaluate
        try:
            create_resp = self.client.post(
                "/api/v1/entities/quotes/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19},
                    "client_name": "Shape Client",
                },
            )
            self.assertEqual(create_resp.status_code, 201, msg=create_resp.text)
            created_quote_id = create_resp.json()["quote_id"]

            in_place_resp = self.client.post(
                f"/api/v1/entities/quotes/{draft_quote_id}/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19},
                    "client_name": "Shape Client",
                },
            )
            self.assertEqual(in_place_resp.status_code, 200, msg=in_place_resp.text)
        finally:
            quote_orchestrator_module.QuoteOrchestrator.__init__ = original_orch_init
            ProductReadinessService.evaluate = original_readiness_eval

        created_quote_get = self.client.get(f"/api/v1/entities/quotes/{created_quote_id}")
        self.assertEqual(created_quote_get.status_code, 200, msg=created_quote_get.text)
        created_quote_row = created_quote_get.json()

        in_place_quote_get = self.client.get(f"/api/v1/entities/quotes/{draft_quote_id}")
        self.assertEqual(in_place_quote_get.status_code, 200, msg=in_place_quote_get.text)
        in_place_quote_row = in_place_quote_get.json()

        self.assertEqual(in_place_quote_row.get("intake_id"), intake_id)
        self.assertEqual(in_place_quote_row.get("status"), "priced")
        self.assertEqual(created_quote_row.get("status"), "priced")

        created_snapshot = _extract_snapshot_dict(created_quote_row.get("line_items") or "{}")
        in_place_snapshot = _extract_snapshot_dict(in_place_quote_row.get("line_items") or "{}")

        self.assertEqual(set(created_snapshot.keys()), set(in_place_snapshot.keys()))
        self.assertEqual(created_snapshot.get("status"), "priced")
        self.assertEqual(in_place_snapshot.get("status"), "priced")
        self.assertEqual(created_snapshot.get("blocked_reasons"), [])
        self.assertEqual(in_place_snapshot.get("blocked_reasons"), [])

        created_warnings = (
            ((created_snapshot.get("cost_result") or {}).get("validation") or {}).get("warnings")
        )
        in_place_warnings = (
            ((in_place_snapshot.get("cost_result") or {}).get("validation") or {}).get("warnings")
        )
        self.assertIsInstance(created_warnings, list)
        self.assertIsInstance(in_place_warnings, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
