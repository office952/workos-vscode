"""Legacy quote /price retirement — prior breakdown-persist coverage is archived.

The active commercial write path is Intake V6 priced-quote/write → 7G.
POST /entities/quotes/price returns HTTP 410 and must not persist.
"""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import routers.quotes as quotes_router
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from services.legacy_quote_price_retirement import LEGACY_QUOTE_PRICE_RETIRED_ERROR
from services.quotes import QuotesService


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(quotes_router.router)

    async def _fake_user():
        return UserResponse(
            id="breakdown-retire-user",
            email="retire@test.local",
            name="Retire",
            role="admin",
        )

    app.dependency_overrides[get_current_user] = _fake_user
    return app


class TestLegacyQuotePriceRetired(unittest.TestCase):
    def test_price_endpoint_returns_410_and_skips_create(self) -> None:
        create = AsyncMock()
        app = _build_app()
        with patch.object(QuotesService, "create", new=create):
            client = TestClient(app)
            resp = client.post(
                "/api/v1/entities/quotes/price",
                json={
                    "client_name": "ACME SRL",
                    "product_template": {"code": "PROD-TEST"},
                    "user_config": {},
                    "pricing": {"margin_pct": 20, "discount_pct": 0, "vat_pct": 19},
                },
            )
        self.assertEqual(resp.status_code, 410, resp.text)
        detail = resp.json()["detail"]
        self.assertEqual(detail["error"], LEGACY_QUOTE_PRICE_RETIRED_ERROR)
        self.assertFalse(detail["financial_write"])
        create.assert_not_called()
