"""Legacy /price retirement — intake linkage via legacy price is no longer active."""

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


class TestQuotePriceIntakeLinkageRetired(unittest.TestCase):
    def test_legacy_price_with_intake_id_is_retired(self) -> None:
        app = FastAPI()
        app.include_router(quotes_router.router)

        async def _user():
            return UserResponse(
                id="u1", email="t@t.local", name="T", role="admin"
            )

        app.dependency_overrides[get_current_user] = _user
        create = AsyncMock()
        with patch.object(QuotesService, "create", new=create):
            resp = TestClient(app).post(
                "/api/v1/entities/quotes/price",
                json={
                    "client_name": "X",
                    "intake_id": 99,
                    "product_template": {"id": 1},
                    "user_config": {"quantity": 1},
                    "pricing": {"margin_pct": 10, "vat_pct": 19, "discount_pct": 0},
                },
            )
        self.assertEqual(resp.status_code, 410)
        self.assertEqual(resp.json()["detail"]["error"], LEGACY_QUOTE_PRICE_RETIRED_ERROR)
        create.assert_not_called()
