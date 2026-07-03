"""POST /quotes/price — persist intake linkage when intake_id is provided."""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import quotes as quotes_router


@dataclass
class _Pricing:
    margin_pct: float = 20.0
    discount_pct: float = 0.0
    vat_pct: float = 19.0


@dataclass
class _Price:
    net: float = 100.0
    gross: float = 119.0
    final: float = 119.0


@dataclass
class _CostResult:
    total_cost: float = 80.0
    breakdown: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class _ProductDef:
    code: str = "PROD-TEST"
    name: str = "Test Product"


@dataclass
class _FakeSnapshot:
    status: str = "priced"
    blocked_reasons: List[str] = field(default_factory=list)
    price: _Price = field(default_factory=_Price)
    pricing: _Pricing = field(default_factory=_Pricing)
    cost_result: _CostResult = field(default_factory=_CostResult)
    product_definition: _ProductDef = field(default_factory=_ProductDef)
    template_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "blocked_reasons": self.blocked_reasons,
            "price": {
                "net": self.price.net,
                "gross": self.price.gross,
                "final": self.price.final,
            },
            "pricing": {
                "margin_pct": self.pricing.margin_pct,
                "discount_pct": self.pricing.discount_pct,
                "vat_pct": self.pricing.vat_pct,
            },
            "cost_result": {
                "total_cost": self.cost_result.total_cost,
                "breakdown": self.cost_result.breakdown,
            },
            "product_definition": {
                "code": self.product_definition.code,
                "name": self.product_definition.name,
            },
        }


@dataclass
class _FakeIntake:
    id: int = 42
    code: str = "WI-E2E-LINK-001"
    client_id: int = 7
    client_name: str = "Linkage Client"
    contact_person: str = "Linkage Contact"


class _Captured:
    last_payload: Optional[Dict[str, Any]] = None
    last_created: Optional[Any] = None

    def reset(self) -> None:
        self.last_payload = None
        self.last_created = None


_captured = _Captured()


async def _fake_create(self, data: Dict[str, Any]) -> Any:
    _captured.last_payload = dict(data)

    class _QuoteRow:
        pass

    row = _QuoteRow()
    row.id = 9001
    row.code = data.get("code", "Q-LINK-TEST")
    row.version = data.get("version", 1)
    _captured.last_created = row
    return row


def _build_app() -> FastAPI:
    from core.database import get_db
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse

    app = FastAPI()
    app.include_router(quotes_router.router)

    async def _fake_db():
        yield AsyncMock()

    async def _fake_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test User",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_current_user] = _fake_user
    return app


_PRICE_URL = "/api/v1/entities/quotes/price"


def _post_price(app: FastAPI, *, intake_id: Optional[int] = None) -> Any:
    snap = _FakeSnapshot()
    mock_orchestrator = AsyncMock()
    mock_orchestrator.build_snapshot = lambda **kwargs: snap

    fake_intake = _FakeIntake()

    with patch.object(
        quotes_router.QuoteOrchestrator,
        "create_with_registry",
        new=AsyncMock(return_value=mock_orchestrator),
    ), patch.object(
        quotes_router.QuotesService,
        "create",
        new=_fake_create,
    ), patch.object(
        quotes_router,
        "_intake_linkage_fields_for_quote",
        new=AsyncMock(
            return_value={
                "intake_id": fake_intake.id,
                "intake_code": fake_intake.code,
                "client_id": fake_intake.client_id,
                "contact_person": fake_intake.contact_person,
                "_intake_client_name": fake_intake.client_name,
            }
        )
        if intake_id is not None
        else AsyncMock(return_value={}),
    ):
        client = TestClient(app)
        body: Dict[str, Any] = {
            "client_name": "ACME SRL",
            "code": "Q-LINK-TEST",
            "product_template": {"code": "PROD-TEST"},
            "user_config": {},
            "pricing": {"margin_pct": 20, "discount_pct": 0, "vat_pct": 19},
        }
        if intake_id is not None:
            body["intake_id"] = intake_id
        return client.post(_PRICE_URL, json=body)


class TestQuotePriceIntakeLinkage(unittest.TestCase):
    def setUp(self) -> None:
        _captured.reset()

    def test_price_without_intake_id_omits_linkage_fields(self) -> None:
        app = _build_app()
        resp = _post_price(app)
        self.assertEqual(resp.status_code, 201, resp.text)
        payload = _captured.last_payload or {}
        self.assertNotIn("intake_id", payload)
        self.assertNotIn("intake_code", payload)
        body = resp.json()
        self.assertEqual(body["quote_id"], 9001)
        self.assertEqual(body["quote_code"], "Q-LINK-TEST")

    def test_price_with_intake_id_persists_linkage_fields(self) -> None:
        app = _build_app()
        resp = _post_price(app, intake_id=42)
        self.assertEqual(resp.status_code, 201, resp.text)
        payload = _captured.last_payload or {}
        self.assertEqual(payload.get("intake_id"), 42)
        self.assertEqual(payload.get("intake_code"), "WI-E2E-LINK-001")
        self.assertEqual(payload.get("client_id"), 7)
        self.assertEqual(payload.get("contact_person"), "Linkage Contact")
        self.assertEqual(payload.get("client_name"), "ACME SRL")
        self.assertEqual(payload.get("subtotal"), 100.0)
        self.assertEqual(payload.get("grand_total"), 119.0)
        body = resp.json()
        self.assertEqual(body["quote_code"], "Q-LINK-TEST")
        self.assertIn("snapshot", body)

    def test_price_uses_intake_client_name_when_payload_unknown(self) -> None:
        app = _build_app()
        snap = _FakeSnapshot()
        mock_orchestrator = AsyncMock()
        mock_orchestrator.build_snapshot = lambda **kwargs: snap

        with patch.object(
            quotes_router.QuoteOrchestrator,
            "create_with_registry",
            new=AsyncMock(return_value=mock_orchestrator),
        ), patch.object(
            quotes_router.QuotesService,
            "create",
            new=_fake_create,
        ), patch.object(
            quotes_router,
            "_intake_linkage_fields_for_quote",
            new=AsyncMock(
                return_value={
                    "intake_id": 42,
                    "intake_code": "WI-E2E-LINK-001",
                    "client_id": 7,
                    "contact_person": "Linkage Contact",
                    "_intake_client_name": "Linkage Client",
                }
            ),
        ):
            client = TestClient(app)
            resp = client.post(
                _PRICE_URL,
                json={
                    "client_name": "Unknown Client",
                    "code": "Q-LINK-UNKNOWN",
                    "product_template": {"code": "PROD-TEST"},
                    "user_config": {},
                    "pricing": {"margin_pct": 20, "discount_pct": 0, "vat_pct": 19},
                    "intake_id": 42,
                },
            )

        self.assertEqual(resp.status_code, 201, resp.text)
        payload = _captured.last_payload or {}
        self.assertEqual(payload.get("client_name"), "Linkage Client")


if __name__ == "__main__":
    unittest.main()
