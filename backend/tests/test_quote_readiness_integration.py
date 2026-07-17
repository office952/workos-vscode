"""Legacy /price retirement — readiness gates on legacy price path are obsolete."""

from __future__ import annotations

from fastapi.testclient import TestClient

from dependencies.auth import get_current_user
from main import app
from schemas.auth import UserResponse
from services.legacy_quote_price_retirement import LEGACY_QUOTE_PRICE_RETIRED_ERROR


def test_legacy_quote_price_retired_before_readiness_gate():
    async def _user():
        return UserResponse(id="u1", email="t@t.local", name="T", role="admin")

    app.dependency_overrides[get_current_user] = _user
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/v1/entities/quotes/price",
            json={
                "client_name": "X",
                "product_template": {"id": 1, "template_code": "TPL-X"},
                "user_config": {"quantity": 1},
                "pricing": {"margin_pct": 10, "vat_pct": 19, "discount_pct": 0},
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert resp.status_code == 410
    assert resp.json()["detail"]["error"] == LEGACY_QUOTE_PRICE_RETIRED_ERROR
    assert resp.json()["detail"]["financial_write"] is False
