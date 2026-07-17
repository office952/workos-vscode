"""Legacy in-place /{id}/price revision is retired."""

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


class TestQuoteRevisionRetired(unittest.TestCase):
    def test_inplace_price_returns_410(self) -> None:
        app = FastAPI()
        app.include_router(quotes_router.router)

        async def _user():
            return UserResponse(id="u1", email="t@t.local", name="T", role="admin")

        app.dependency_overrides[get_current_user] = _user
        update = AsyncMock()
        with patch.object(QuotesService, "update", new=update):
            resp = TestClient(app).post(
                "/api/v1/entities/quotes/9/price",
                json={
                    "client_name": "X",
                    "product_template": {"id": 1},
                    "user_config": {"quantity": 1},
                    "pricing": {"margin_pct": 10, "vat_pct": 19, "discount_pct": 5},
                },
            )
        self.assertEqual(resp.status_code, 410)
        self.assertEqual(resp.json()["detail"]["error"], LEGACY_QUOTE_PRICE_RETIRED_ERROR)
        update.assert_not_called()
