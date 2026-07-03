"""POST /quotes/{id}/send-log — assisted delivery audit persistence."""

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
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _create_quote(client: TestClient, **overrides) -> int:
    payload = {
        "code": "Q-SENDLOG-001",
        "client_name": "Send Log Client",
        "status": "priced",
        "version": 2,
        "line_items": json.dumps(
            {
                "line_items": {
                    "status": "priced",
                    "price": {"net": 100, "gross": 119},
                    "pricing": {"margin_pct": 25, "discount_pct": 0, "vat_pct": 19},
                }
            }
        ),
        "subtotal": 100.0,
        "grand_total": 119.0,
        "margin_pct": 25.0,
        "discount_pct": 0.0,
        "vat": 19.0,
        "total_before_vat": 100.0,
    }
    payload.update(overrides)
    resp = client.post("/api/v1/entities/quotes", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestQuoteSendLog(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_quote_send_log_")
        cls.db.setup()

        async def _override_get_db():
            async with cls.db.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="operator-1",
                email="operator@example.com",
                name="Operator",
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

    def test_send_log_on_priced_moves_status_to_sent(self) -> None:
        quote_id = _create_quote(self.client, status="priced")
        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/send-log",
            json={
                "channel": "email_manual",
                "recipient": "client@example.com",
                "note": "Trimis manual din Outlook",
            },
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertTrue(data["status_changed"])
        self.assertEqual(data["status"], "sent")
        self.assertEqual(data["quote_version"], 2)
        self.assertEqual(data["log_entry"]["channel"], "email_manual")
        self.assertEqual(data["log_entry"]["quote_version"], 2)
        self.assertEqual(data["log_entry"]["actor_email"], "operator@example.com")

        row = self.client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        self.assertEqual(row["status"], "sent")
        self.assertEqual(float(row["grand_total"]), 119.0)
        wrapper = json.loads(row["line_items"])
        self.assertEqual(len(wrapper["commercial_delivery_log"]), 1)

    def test_send_log_on_draft_moves_status_to_sent(self) -> None:
        quote_id = _create_quote(
            self.client,
            code="Q-SENDLOG-DRAFT",
            status="draft",
            version=1,
            line_items=json.dumps([{"description": "Draft line", "quantity": 1}]),
        )
        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/send-log",
            json={"channel": "whatsapp", "recipient": "+40700000000"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["status"], "sent")

    def test_send_log_on_sent_adds_event_without_status_change(self) -> None:
        quote_id = _create_quote(self.client, status="sent", code="Q-SENDLOG-SENT")
        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/send-log",
            json={"channel": "print", "note": "Predare fizică birou"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertFalse(data["status_changed"])
        self.assertEqual(data["status"], "sent")

    def test_send_log_rejects_invalid_channel(self) -> None:
        quote_id = _create_quote(self.client, code="Q-SENDLOG-BAD-CH")
        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/send-log",
            json={"channel": "telegram"},
        )
        self.assertEqual(resp.status_code, 422, resp.text)
        self.assertEqual(resp.json()["detail"]["error"], "invalid_send_channel")

    def test_send_log_blocks_rejected_quote(self) -> None:
        quote_id = _create_quote(self.client, status="rejected", code="Q-SENDLOG-REJ")
        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/send-log",
            json={"channel": "email_manual"},
        )
        self.assertEqual(resp.status_code, 422, resp.text)
        self.assertEqual(resp.json()["detail"]["error"], "quote_not_eligible_for_send_log")

    def test_send_log_on_viewed_keeps_status(self) -> None:
        quote_id = _create_quote(self.client, status="viewed", code="Q-SENDLOG-VIEWED")
        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/send-log",
            json={"channel": "whatsapp", "note": "Retrimis"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertFalse(data["status_changed"])
        self.assertEqual(data["status"], "viewed")

    def test_send_log_on_negotiating_keeps_status(self) -> None:
        quote_id = _create_quote(self.client, status="negotiating", code="Q-SENDLOG-NEG")
        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/send-log",
            json={"channel": "phone"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertFalse(resp.json()["status_changed"])
        self.assertEqual(resp.json()["status"], "negotiating")

    def test_send_log_blocks_expired_quote(self) -> None:
        quote_id = _create_quote(self.client, status="expired", code="Q-SENDLOG-EXP")
        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/send-log",
            json={"channel": "email_manual"},
        )
        self.assertEqual(resp.status_code, 422, resp.text)
        self.assertEqual(resp.json()["detail"]["error"], "quote_not_eligible_for_send_log")

    def test_send_log_does_not_modify_pricing_totals(self) -> None:
        line_items = json.dumps(
            {
                "line_items": {
                    "status": "priced",
                    "price": {"net": 100, "gross": 119},
                    "revision_history": [{"version": 1, "archived_at": "2026-06-01T00:00:00Z"}],
                },
                "commercial_delivery_log": [],
            }
        )
        quote_id = _create_quote(
            self.client,
            code="Q-SENDLOG-NOPRICE",
            status="priced",
            line_items=line_items,
            subtotal=100.0,
            grand_total=119.0,
            margin_pct=25.0,
        )
        resp = self.client.post(
            f"/api/v1/entities/quotes/{quote_id}/send-log",
            json={"channel": "email_manual"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        row = self.client.get(f"/api/v1/entities/quotes/{quote_id}").json()
        self.assertEqual(float(row["grand_total"]), 119.0)
        self.assertEqual(float(row["subtotal"]), 100.0)
        wrapper = json.loads(row["line_items"])
        self.assertIn("revision_history", wrapper["line_items"])
        self.assertEqual(len(wrapper["line_items"]["revision_history"]), 1)
        self.assertEqual(len(wrapper["commercial_delivery_log"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
