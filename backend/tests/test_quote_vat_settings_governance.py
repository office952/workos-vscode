"""Quote VAT governance — Settings override, snapshot, document, legacy 0-safe."""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from data_models.product_contracts import QuotePricing
from main import app
from models.company_commercial_settings import CompanyCommercialSettings
from routers.quotes import _apply_settings_vat_to_pricing
from services.company_commercial_settings_service import DEFAULT_VAT_PCT
from services.quote_document_service import QuoteDocumentService
from services.quote_legacy_revision import _legacy_quote_vat_pct


def _make_quote_obj(
    line_items: str | None = None,
    total_before_vat: float = 1000.0,
    vat: float = 21.0,
    grand_total: float = 1210.0,
):
    obj = MagicMock()
    obj.id = 1
    obj.code = "QT-VAT-001"
    obj.status = "priced"
    obj.client_name = "VAT Client"
    obj.contact_person = None
    obj.line_items = line_items
    obj.subtotal = total_before_vat
    obj.discount = 0.0
    obj.discount_pct = 0.0
    obj.total_before_vat = total_before_vat
    obj.vat = vat
    obj.grand_total = grand_total
    obj.margin_pct = 30.0
    obj.version = 1
    obj.valid_until = "2025-06-30"
    obj.notes = None
    obj.assigned_to = None
    obj.intake_code = None
    obj.created_at = datetime(2025, 5, 15, 10, 0, 0)
    obj.updated_at = datetime(2025, 5, 15, 10, 0, 0)
    return obj


def _snapshot_dict(vat_pct: float) -> dict:
    return {
        "product_definition": {
            "template_code": "TPL-BANNER-STANDARD",
            "code": "TPL-BANNER-STANDARD",
            "name": "Banner",
            "family": "BANNER",
        },
        "pricing": {"margin_pct": 30.0, "discount_pct": 0.0, "vat_pct": vat_pct},
        "cost_result": {"breakdown": []},
    }


def _snapshot_with_vat(vat_pct: float) -> str:
    return json.dumps(_snapshot_dict(vat_pct))


def test_resolve_vat_percent_from_snapshot_zero():
    quote = _make_quote_obj(vat=21.0)
    pct = QuoteDocumentService._resolve_quote_vat_percent(quote, _snapshot_dict(0.0))
    assert pct == 0.0


def test_resolve_vat_percent_from_quote_when_no_snapshot():
    quote = _make_quote_obj(vat=19.0)
    pct = QuoteDocumentService._resolve_quote_vat_percent(quote, None)
    assert pct == 19.0


def test_resolve_vat_percent_default_when_missing():
    quote = _make_quote_obj(vat=None)
    pct = QuoteDocumentService._resolve_quote_vat_percent(quote, None)
    assert pct == float(DEFAULT_VAT_PCT)


def test_document_totals_zero_vat(db_session):
    quote = _make_quote_obj(
        line_items=_snapshot_with_vat(0.0),
        total_before_vat=1000.0,
        vat=0.0,
        grand_total=1000.0,
    )
    svc = QuoteDocumentService(db_session)
    totals = svc._build_document_totals(
        quote,
        commercial_terms={"tva_percent": 0.0, "currency": "RON"},
        source_currency=None,
        exchange_rate=None,
    )
    assert totals["tva"] == 0.0


def test_document_totals_21_vat(db_session):
    quote = _make_quote_obj(
        total_before_vat=1000.0,
        vat=21.0,
        grand_total=1210.0,
    )
    svc = QuoteDocumentService(db_session)
    totals = svc._build_document_totals(
        quote,
        commercial_terms={"tva_percent": 21.0, "currency": "RON"},
        source_currency=None,
        exchange_rate=None,
    )
    assert totals["tva"] == 210.0


def test_legacy_quote_vat_pct_preserves_zero():
    quote = MagicMock()
    quote.vat = 0.0
    assert _legacy_quote_vat_pct(quote) == 0.0


def test_legacy_quote_vat_pct_none_uses_default():
    quote = MagicMock()
    quote.vat = None
    assert _legacy_quote_vat_pct(quote) == float(DEFAULT_VAT_PCT)


@pytest.mark.asyncio
async def test_price_endpoint_overrides_request_vat_with_settings(db_session):
    """Request vat_pct 19 ignored when settings VAT is 0."""
    row = CompanyCommercialSettings(default_vat_pct=0.0)
    db_session.add(row)
    await db_session.commit()

    pricing = QuotePricing(margin_pct=25, vat_pct=19, discount_pct=0)
    await _apply_settings_vat_to_pricing(db_session, pricing)
    assert pricing.vat_pct == 0.0


@pytest.mark.asyncio
async def test_commercial_document_endpoint_vat_from_snapshot():
    quote = _make_quote_obj(
        line_items=_snapshot_with_vat(21.0),
        total_before_vat=1000.0,
        vat=21.0,
    )

    with patch("services.quote_document_service.QuotesService") as MockQS:
        instance = MockQS.return_value
        instance.get_by_id = AsyncMock(return_value=quote)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

        data = resp.json()
        assert data["commercial"]["tva_percent"] == 21.0
        assert data["totals"]["tva"] == 210.0


@pytest.mark.asyncio
async def test_snapshot_vat_persists_after_settings_change(db_session):
    """Document resolution uses snapshot, not live settings row."""
    row = CompanyCommercialSettings(default_vat_pct=21.0)
    db_session.add(row)
    await db_session.commit()

    quote = _make_quote_obj(vat=0.0)
    assert QuoteDocumentService._resolve_quote_vat_percent(quote, _snapshot_dict(0.0)) == 0.0

    row.default_vat_pct = 21.0
    await db_session.commit()
    assert QuoteDocumentService._resolve_quote_vat_percent(quote, _snapshot_dict(0.0)) == 0.0
