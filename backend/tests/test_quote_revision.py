"""POST /quotes/{id}/price — commercial revision workflow."""

from __future__ import annotations

import json
import os
import sys
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

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

from routers.quotes import router as quotes_router  # noqa: E402
from services.cost_engine_service import CostEngineWithMaterialRates  # noqa: E402
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
                }
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


def _readiness_obj() -> ProductReadinessResult:
    return ProductReadinessResult(
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


class TestQuoteRevision(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_quote_revision_")
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

    def _post_revision(self, quote_id: int, *, discount_pct: float = 10.0):
        original_orch_init = quote_orchestrator_module.QuoteOrchestrator.__init__
        original_readiness_eval = ProductReadinessService.evaluate

        def _patched_orch_init(self, product_service=None, cost_engine=None, **kwargs):
            original_orch_init(
                self,
                product_service=product_service,
                cost_engine=cost_engine or CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
                **kwargs,
            )

        async def _mocked_evaluate(self, template_id: int, **kwargs):
            return _readiness_obj()

        quote_orchestrator_module.QuoteOrchestrator.__init__ = _patched_orch_init
        ProductReadinessService.evaluate = _mocked_evaluate
        try:
            return self.client.post(
                f"/api/v1/entities/quotes/{quote_id}/price",
                json={
                    "product_template": _sample_template_complete(),
                    "user_config": _sample_user_config(),
                    "pricing": {"margin_pct": 25, "vat_pct": 19, "discount_pct": discount_pct},
                    "client_name": "Revision Client",
                },
            )
        finally:
            quote_orchestrator_module.QuoteOrchestrator.__init__ = original_orch_init
            ProductReadinessService.evaluate = original_readiness_eval

    def test_priced_quote_revision_increments_version_and_archives_v1(self) -> None:
        revision_source = {
            "product_template": _sample_template_complete(),
            "user_config": _sample_user_config(),
            "pricing": {"margin_pct": 25, "vat_pct": 19, "discount_pct": 0},
        }
        create_resp = self.client.post(
            "/api/v1/entities/quotes",
            json={
                "code": "Q-REV-PRICED-001",
                "client_name": "Revision Client",
                "status": "priced",
                "version": 1,
                "line_items": json.dumps(
                    {
                        "line_items": {"status": "priced", "price": {"net": 100, "gross": 119}},
                        "revision_source": revision_source,
                    }
                ),
                "subtotal": 100.0,
                "grand_total": 119.0,
                "margin_pct": 25.0,
                "discount_pct": 0.0,
                "vat": 19.0,
                "total_before_vat": 100.0,
            },
        )
        self.assertEqual(create_resp.status_code, 201, create_resp.text)
        quote_id = create_resp.json()["id"]

        resp = self._post_revision(quote_id, discount_pct=8)
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertTrue(data.get("revised"))
        self.assertEqual(data.get("quote_version"), 2)

        row = self.client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        self.assertEqual(row["status"], "priced")
        self.assertEqual(row["version"], 2)
        self.assertEqual(float(row["discount_pct"]), 8.0)
        wrapper = json.loads(row["line_items"])
        self.assertEqual(len(wrapper["revision_history"]), 1)
        self.assertEqual(wrapper["revision_history"][0]["version"], 1)

    def test_sent_quote_revision_preserves_commercial_delivery_log(self) -> None:
        send_log_entry = {
            "id": "log-1",
            "event_type": "quote_send_assisted",
            "channel": "email_manual",
            "sent_at": "2026-06-01T10:00:00Z",
            "quote_version": 2,
            "recipient": "client@example.com",
        }
        revision_source = {
            "product_template": _sample_template_complete(),
            "user_config": _sample_user_config(),
            "pricing": {"margin_pct": 25, "vat_pct": 19, "discount_pct": 0},
        }
        prior_wrapper = {
            "line_items": {"status": "priced", "price": {"net": 100, "gross": 119}},
            "revision_source": revision_source,
            "commercial_delivery_log": [send_log_entry],
        }
        create_resp = self.client.post(
            "/api/v1/entities/quotes",
            json={
                "code": "Q-REV-SENDLOG-001",
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
            },
        )
        self.assertEqual(create_resp.status_code, 201, create_resp.text)
        quote_id = create_resp.json()["id"]

        resp = self._post_revision(quote_id, discount_pct=5)
        self.assertEqual(resp.status_code, 200, resp.text)
        row = self.client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        wrapper = json.loads(row["line_items"])
        self.assertEqual(len(wrapper["commercial_delivery_log"]), 1)
        self.assertEqual(wrapper["commercial_delivery_log"][0]["quote_version"], 2)
        self.assertEqual(row["status"], "priced")
        self.assertEqual(row["version"], 3)

    def test_accepted_quote_cannot_be_revised(self) -> None:
        create_resp = self.client.post(
            "/api/v1/entities/quotes",
            json={
                "code": "Q-REV-ACC-001",
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
            },
        )
        quote_id = create_resp.json()["id"]
        resp = self._post_revision(quote_id)
        self.assertEqual(resp.status_code, 422, resp.text)
        self.assertEqual(resp.json()["detail"]["error"], "quote_not_eligible_for_revision")

    def test_invalid_discount_rejected(self) -> None:
        create_resp = self.client.post(
            "/api/v1/entities/quotes",
            json={
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
            },
        )
        quote_id = create_resp.json()["id"]
        resp = self._post_revision(quote_id, discount_pct=75)
        self.assertEqual(resp.status_code, 422, resp.text)
        self.assertEqual(resp.json()["detail"]["error"], "invalid_discount")

    def test_intake_linkage_preserved_after_revision(self) -> None:
        revision_source = {
            "product_template": _sample_template_complete(),
            "user_config": _sample_user_config(),
            "pricing": {"margin_pct": 25, "vat_pct": 19, "discount_pct": 0},
        }
        create_resp = self.client.post(
            "/api/v1/entities/quotes",
            json={
                "code": "Q-REV-LINK-001",
                "client_name": "Link Client",
                "status": "priced",
                "version": 1,
                "intake_id": 42,
                "intake_code": "WI-REV-LINK-001",
                "contact_person": "Alex",
                "line_items": json.dumps(
                    {
                        "line_items": {"status": "priced", "price": {"net": 100, "gross": 119}},
                        "revision_source": revision_source,
                    }
                ),
                "subtotal": 100.0,
                "grand_total": 119.0,
                "margin_pct": 25.0,
                "discount_pct": 0.0,
                "vat": 19.0,
                "total_before_vat": 100.0,
            },
        )
        self.assertEqual(create_resp.status_code, 201, create_resp.text)
        quote_id = create_resp.json()["id"]
        resp = self._post_revision(quote_id, discount_pct=12)
        self.assertEqual(resp.status_code, 200, resp.text)
        row = self.client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        self.assertEqual(row["intake_id"], 42)
        self.assertEqual(row["intake_code"], "WI-REV-LINK-001")


if __name__ == "__main__":
    unittest.main(verbosity=2)
