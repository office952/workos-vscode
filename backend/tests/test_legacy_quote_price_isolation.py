"""Legacy POST /entities/quotes/price isolation — no commercial result, no write."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from dependencies.auth import get_current_user
from main import app
from schemas.auth import UserResponse
from services.legacy_quote_price_retirement import LEGACY_QUOTE_PRICE_RETIRED_ERROR
from services.quotes import QuotesService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def _client() -> TestClient:
    async def _user():
        return UserResponse(
            id="legacy-isolation-user",
            email="legacy-isolation@test.local",
            name="Legacy Isolation",
            role="admin",
        )

    app.dependency_overrides[get_current_user] = _user
    return TestClient(app)


def _clear() -> None:
    app.dependency_overrides.pop(get_current_user, None)


def test_legacy_create_price_returns_410_without_write():
    client = _client()
    create_calls: list = []

    async def _fake_create(self, data):  # noqa: ANN001
        create_calls.append(data)
        raise AssertionError("QuotesService.create must not be called")

    try:
        with patch.object(QuotesService, "create", new=_fake_create):
            resp = client.post(
                "/api/v1/entities/quotes/price",
                json={
                    "client_name": "Isolation Co",
                    "product_template": {"id": 1, "template_code": "TPL-X"},
                    "user_config": {"quantity": 1},
                    "pricing": {"margin_pct": 20, "discount_pct": 0, "vat_pct": 19},
                },
            )
    finally:
        _clear()

    assert resp.status_code == 410, resp.text
    detail = resp.json()["detail"]
    assert detail["error"] == LEGACY_QUOTE_PRICE_RETIRED_ERROR
    assert detail["calculation_performed"] is False
    assert detail["financial_write"] is False
    assert "quote_id" not in detail
    assert "snapshot" not in detail
    assert create_calls == []


def test_legacy_inplace_price_returns_410_without_write():
    client = _client()
    update_calls: list = []

    async def _fake_update(self, *args, **kwargs):  # noqa: ANN001
        update_calls.append((args, kwargs))
        raise AssertionError("QuotesService.update must not be called")

    try:
        with patch.object(QuotesService, "update", new=_fake_update):
            resp = client.post(
                "/api/v1/entities/quotes/42/price",
                json={
                    "client_name": "Isolation Co",
                    "product_template": {"id": 1, "template_code": "TPL-X"},
                    "user_config": {"quantity": 1},
                    "pricing": {"margin_pct": 20, "discount_pct": 0, "vat_pct": 19},
                },
            )
    finally:
        _clear()

    assert resp.status_code == 410, resp.text
    detail = resp.json()["detail"]
    assert detail["error"] == LEGACY_QUOTE_PRICE_RETIRED_ERROR
    assert detail["financial_write"] is False
    assert update_calls == []


def test_legacy_price_routes_excluded_from_openapi():
    schema = app.openapi()
    paths = schema.get("paths") or {}
    assert "/api/v1/entities/quotes/price" not in paths
    for path, methods in paths.items():
        if path.rstrip("/").endswith("/price") and "/entities/quotes" in path:
            assert "post" not in methods, path


def test_retired_handlers_ast_have_no_orchestrator_call():
    src = (
        Path(__file__).resolve().parents[1] / "routers" / "quotes.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name in {
            "price_quote",
            "price_existing_draft_quote",
        }:
            segment = ast.get_source_segment(src, node) or ""
            assert "raise_legacy_quote_price_retired" in segment
            assert "build_snapshot" not in segment
            assert "create_with_registry" not in segment


@pytest.mark.asyncio
async def test_cpp_still_available_after_legacy_isolation(volumetric_v2_db):
    """Active 7G engine must remain callable (regression guard)."""
    from services.commercial_price_proposal_service import CommercialPriceProposalService
    from tests.test_commercial_price_proposal_preview import _full_quote_input

    preview = await CommercialPriceProposalService(volumetric_v2_db).build_preview(
        "TPL-VOLUMETRIC-LETTERS_v2",
        quote_input=_full_quote_input(),
    )
    assert preview is not None
    assert preview.commercial_total is not None
    assert preview.commercial_total > 0
