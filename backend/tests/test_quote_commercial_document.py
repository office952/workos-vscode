"""
BUILD 5 — Tests for Quote Commercial Document endpoint and service.

Coverage:
  - Document endpoint returns stable shape
  - Document uses quote snapshot totals (never recalculates CostEngine)
  - Document includes readiness snapshot if present
  - Historical quote missing readiness returns explicit null/legacy state
  - Mesh quote includes externalization note
  - Lightbox quote includes LED/electrical section
  - TVA remains respected from backend data
  - Quote not found returns 404
  - Document generation does not mutate quote/order
  - Product-specific text blocks are correct for each BUILD 4 template
  - Export endpoint returns HTML
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport
from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_quote_obj(
    id: int = 1,
    code: str = "QT-2025-001",
    status: str = "priced",
    client_name: str = "Test Client SRL",
    contact_person: str = "Ion Popescu",
    line_items: str | None = None,
    subtotal: float = 1000.0,
    discount: float = 0.0,
    discount_pct: float = 0.0,
    total_before_vat: float = 1000.0,
    vat: float = 21.0,
    grand_total: float = 1210.0,
    margin_pct: float = 35.0,
    version: int = 1,
    valid_until: str = "2025-06-30",
    notes: str | None = None,
    assigned_to: str | None = None,
    intake_code: str | None = "INT-001",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
):
    """Create a mock quote object."""
    obj = MagicMock()
    obj.id = id
    obj.code = code
    obj.status = status
    obj.client_name = client_name
    obj.contact_person = contact_person
    obj.line_items = line_items
    obj.subtotal = subtotal
    obj.discount = discount
    obj.discount_pct = discount_pct
    obj.total_before_vat = total_before_vat
    obj.vat = vat
    obj.grand_total = grand_total
    obj.margin_pct = margin_pct
    obj.version = version
    obj.valid_until = valid_until
    obj.notes = notes
    obj.assigned_to = assigned_to
    obj.intake_code = intake_code
    obj.created_at = created_at or datetime(2025, 5, 15, 10, 0, 0)
    obj.updated_at = updated_at or datetime(2025, 5, 15, 10, 0, 0)
    return obj


def _eur_volumetric_snapshot_payload() -> dict:
    """Canonical snapshot priced in EUR — mirrors volumetric CostEngine output."""
    return {
        "product_definition": {
            "template_code": "TPL-VOLUMETRIC-LETTERS",
            "code": "TPL-VOLUMETRIC-LETTERS",
            "name": "Litere volumetrice",
            "family": "litere_volumetrice",
            "description": "Litere volumetrice",
            "externalized": False,
        },
        "readiness_result": {
            "ready_for_quote": True,
            "overall_status": "ready",
            "warnings": [],
            "blockers": [],
        },
        "cost_result": {
            "currency": "EUR",
            "total_cost": 640.0,
            "breakdown": [],
        },
        "pricing": {"margin_pct": 30.0, "discount_pct": 0.0, "vat_pct": 19.0},
        "price": {"net": 1103.64, "gross": 1103.64, "final": 1103.64},
        "status": "priced",
    }


def _eur_volumetric_line_items(exchange_rate: float | None = None):
    payload = _eur_volumetric_snapshot_payload()
    if exchange_rate is not None:
        return json.dumps({"line_items": payload, "exchange_rate": exchange_rate})
    return json.dumps(payload)


def _eur_volumetric_shape_b_line_items(exchange_rate: float | None = None):
    """Shape B wrapper with component_breakdown — real volumetric persist path."""
    wrapper: dict = {
        "line_items": _eur_volumetric_snapshot_payload(),
        "component_breakdown": [
            {
                "component_id": "face_panel",
                "name": "Față litere",
                "material_cost": 500.0,
                "operation_cost": 150.0,
                "total_component_cost": 650.0,
            },
            {
                "component_id": "returns",
                "name": "Retururi",
                "material_cost": 200.0,
                "operation_cost": 80.0,
                "total_component_cost": 280.0,
            },
        ],
    }
    if exchange_rate is not None:
        wrapper["exchange_rate"] = exchange_rate
    return json.dumps(wrapper)


def _banner_line_items():
    """Line items JSON with banner template and readiness snapshot."""
    return json.dumps({
        "product_definition": {
            "template_code": "TPL-BANNER-STANDARD",
            "code": "TPL-BANNER-STANDARD",
            "name": "Banner publicitar",
            "family": "BANNER",
            "description": "Banner publicitar PVC format mare",
            "externalized": False,
        },
        "readiness_result": {
            "ready_for_quote": True,
            "overall_status": "ready",
            "warnings": ["Roll width 1350mm selected — verify stock"],
            "blockers": [],
        },
        "cost_result": {
            "breakdown": [
                {"name": "Material PVC", "type": "material", "quantity": 1, "unit_cost": 250.0, "total": 250.0},
                {"name": "Imprimare", "type": "operation", "quantity": 1, "unit_cost": 400.0, "total": 400.0},
                {"name": "Tiv + Capse", "type": "finishing", "quantity": 1, "unit_cost": 150.0, "total": 150.0},
            ]
        },
    })


def _mesh_line_items():
    """Line items JSON with mesh externalized template."""
    return json.dumps({
        "product_definition": {
            "template_code": "TPL-MESH-EXTERNALIZED",
            "code": "TPL-MESH-EXTERNALIZED",
            "name": "Mesh publicitar",
            "family": "MESH",
            "description": "Mesh perforat externalizat",
            "externalized": True,
        },
        "readiness_result": {
            "ready_for_quote": True,
            "overall_status": "ready_with_warnings",
            "warnings": ["Externalized — supplier confirmation required"],
            "blockers": [],
        },
    })


def _lightbox_line_items():
    """Line items JSON with lightbox template."""
    return json.dumps({
        "product_definition": {
            "template_code": "TPL-LIGHTBOX-STANDARD",
            "code": "TPL-LIGHTBOX-STANDARD",
            "name": "Casetă luminoasă",
            "family": "LIGHTBOX",
            "description": "Casetă luminoasă cu LED",
            "externalized": False,
        },
        "readiness_result": {
            "ready_for_quote": True,
            "overall_status": "ready",
            "warnings": [],
            "blockers": [],
        },
    })


def _legacy_line_items():
    """Legacy flat line items (no product_definition)."""
    return json.dumps([
        {"description": "Serviciu design", "productCode": "SRV-001", "quantity": 1, "unitPrice": 500, "total": 500},
        {"description": "Material", "productCode": "MAT-001", "quantity": 2, "unitPrice": 250, "total": 500},
    ])


def _no_readiness_line_items():
    """Line items with product_definition but no readiness_result."""
    return json.dumps({
        "product_definition": {
            "template_code": "TPL-PLEXI-PLATE",
            "code": "TPL-PLEXI-PLATE",
            "name": "Placă plexiglass",
            "family": "PLEXI",
            "description": "Placă plexiglass personalizată",
            "externalized": False,
        },
    })


# ---------------------------------------------------------------------------
# Auth override
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def override_auth():
    """Override auth dependency for all tests."""
    from dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "test@test.com"}
    yield
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# Tests — Document Endpoint
# ---------------------------------------------------------------------------

class TestQuoteCommercialDocumentEndpoint:
    """Tests for GET /api/v1/entities/quotes/{id}/commercial-document"""

    @pytest.mark.asyncio
    async def test_returns_stable_shape_for_banner(self):
        """Document endpoint returns stable DTO shape with all expected keys."""
        quote = _make_quote_obj(line_items=_banner_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            assert resp.status_code == 200
            data = resp.json()

            # Verify top-level keys
            assert "quote_id" in data
            assert "quote_code" in data
            assert "status" in data
            assert "client" in data
            assert "commercial" in data
            assert "product_summary" in data
            assert "product_text" in data
            assert "line_items" in data
            assert "totals" in data
            assert "readiness" in data
            assert "document" in data
            assert "metadata" in data

            # Verify document source is backend
            assert data["document"]["source"] == "backend"
            assert data["document"]["title"] == "Ofertă comercială"

    @pytest.mark.asyncio
    async def test_uses_quote_snapshot_totals(self):
        """Document uses existing quote totals, never recalculates."""
        quote = _make_quote_obj(
            line_items=_banner_line_items(),
            subtotal=800.0,
            discount=50.0,
            discount_pct=5.0,
            total_before_vat=750.0,
            grand_total=892.5,
            margin_pct=40.0,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            totals = data["totals"]
            assert totals["subtotal"] == 800.0
            assert totals["discount"] == 50.0
            assert totals["discount_pct"] == 5.0
            assert totals["total_before_vat"] == 750.0
            assert totals["grand_total"] == 892.5
            assert totals["margin_pct"] == 40.0

    @pytest.mark.asyncio
    async def test_includes_readiness_snapshot(self):
        """Document includes readiness from snapshot, not live recalculation."""
        quote = _make_quote_obj(line_items=_banner_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            readiness = data["readiness"]
            assert readiness["source"] == "snapshot"
            assert readiness["ready_for_quote"] is True
            assert readiness["overall_status"] == "ready"
            assert len(readiness["warnings"]) == 1
            assert "Roll width" in readiness["warnings"][0]

    @pytest.mark.asyncio
    async def test_historical_missing_readiness_returns_explicit_state(self):
        """Historical quote without readiness returns explicit unavailable state."""
        quote = _make_quote_obj(line_items=_no_readiness_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            readiness = data["readiness"]
            assert readiness["source"] == "not_captured"
            assert readiness["ready_for_quote"] is None

    @pytest.mark.asyncio
    async def test_mesh_includes_externalization_note(self):
        """Mesh quote includes externalization note in product_text."""
        quote = _make_quote_obj(line_items=_mesh_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            product_text = data["product_text"]
            assert product_text["externalization_note"] is not None
            assert "EXTERNALIZARE" in product_text["externalization_note"]
            assert "furnizor extern" in product_text["externalization_note"]

            # Also check document sections include externalization
            sections = data["document"]["sections"]
            section_ids = [s["id"] for s in sections]
            assert "externalization" in section_ids

    @pytest.mark.asyncio
    async def test_lightbox_includes_led_electrical_info(self):
        """Lightbox quote includes LED/electrical information."""
        quote = _make_quote_obj(line_items=_lightbox_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            product_text = data["product_text"]
            assert "LED" in (product_text.get("technical_description") or "")
            assert "electric" in (product_text.get("production_assumptions") or "").lower()

    @pytest.mark.asyncio
    async def test_tva_respected_from_backend(self):
        """TVA is calculated from quote snapshot / vat_pct column, not live Settings."""
        quote = _make_quote_obj(
            line_items=_banner_line_items(),
            total_before_vat=1000.0,
            vat=19.0,
            grand_total=1190.0,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            assert data["totals"]["tva"] == 190.0
            assert data["commercial"]["tva_percent"] == 19

    @pytest.mark.asyncio
    async def test_quote_not_found_returns_404(self):
        """Non-existent quote returns 404."""
        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/999/commercial-document")

            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_document_does_not_mutate_quote(self):
        """Document generation does not call any mutation methods."""
        quote = _make_quote_obj(line_items=_banner_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            assert resp.status_code == 200
            # Verify no mutation methods were called
            instance.update.assert_not_called() if hasattr(instance, 'update') else None
            instance.delete.assert_not_called() if hasattr(instance, 'delete') else None

    @pytest.mark.asyncio
    async def test_legacy_flat_line_items_handled(self):
        """Legacy quotes with flat line items are handled gracefully."""
        quote = _make_quote_obj(line_items=_legacy_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            assert resp.status_code == 200
            assert len(data["line_items"]) == 2
            assert data["line_items"][0]["description"] == "Serviciu design"
            assert data["line_items"][0]["type"] == "legacy"

    @pytest.mark.asyncio
    async def test_commercial_terms_defaults(self):
        """Commercial terms use backend defaults (validity_days derived from quote dates)."""
        # Use a quote with no valid_until so defaults apply
        quote = _make_quote_obj(line_items=_banner_line_items(), valid_until=None)

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            commercial = data["commercial"]
            assert commercial["currency"] == "RON"
            assert commercial["tva_percent"] == 21
            assert commercial["validity_days"] == 15  # default when no valid_until
            assert commercial["payment_terms"] is not None
            assert commercial["delivery_terms"] is not None
            assert commercial["warranty_terms"] is not None

    @pytest.mark.asyncio
    async def test_eur_shape_b_component_breakdown_preserves_currency(self):
        """Shape B (component_breakdown wrapper) must keep EUR on commercial document."""
        quote = _make_quote_obj(
            line_items=_eur_volumetric_shape_b_line_items(),
            subtotal=1103.64,
            total_before_vat=1103.64,
            vat=209.69,
            grand_total=1103.64,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            assert resp.status_code == 200
            assert data["commercial"]["currency"] == "EUR"
            assert data["totals"]["currency"] == "EUR"
            assert data["totals"]["grand_total"] == 1103.64

    @pytest.mark.asyncio
    async def test_eur_shape_b_export_html_shows_eur(self):
        """HTML export from Shape B EUR quote must not label totals as RON."""
        quote = _make_quote_obj(
            line_items=_eur_volumetric_shape_b_line_items(),
            subtotal=1103.64,
            total_before_vat=1103.64,
            vat=209.69,
            grand_total=1103.64,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document/export")

            assert resp.status_code == 200
            content = resp.text
            assert "1.103,64 EUR" in content or "1103.64 EUR" in content
            assert "1.103,64 RON" not in content
            assert "Monedă:</strong> EUR" in content

    @pytest.mark.asyncio
    async def test_eur_snapshot_preserves_currency_without_exchange_rate(self):
        """768 EUR must not become 768 RON when no FX snapshot exists."""
        quote = _make_quote_obj(
            line_items=_eur_volumetric_line_items(),
            subtotal=768.0,
            total_before_vat=768.0,
            vat=145.92,
            grand_total=913.92,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            assert resp.status_code == 200
            assert data["commercial"]["currency"] == "EUR"
            assert data["totals"]["currency"] == "EUR"
            assert data["totals"]["grand_total"] == 913.92
            assert "exchange_rate" not in data["commercial"]

    @pytest.mark.asyncio
    async def test_eur_snapshot_converts_when_exchange_rate_present(self):
        """Explicit exchange_rate converts presentation to RON without inventing FX."""
        quote = _make_quote_obj(
            line_items=_eur_volumetric_line_items(exchange_rate=5.0),
            subtotal=768.0,
            total_before_vat=768.0,
            vat=145.92,
            grand_total=913.92,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            assert resp.status_code == 200
            assert data["commercial"]["currency"] == "RON"
            assert data["commercial"]["source_currency"] == "EUR"
            assert data["commercial"]["exchange_rate"] == 5.0
            assert data["totals"]["currency"] == "RON"
            assert data["totals"]["grand_total"] == 4569.6
            source = data["totals"]["source_amounts"]
            assert source["currency"] == "EUR"
            assert source["grand_total"] == 913.92

    @pytest.mark.asyncio
    async def test_eur_export_html_shows_eur_not_lei(self):
        """HTML export must label totals with EUR when snapshot currency is EUR."""
        quote = _make_quote_obj(
            line_items=_eur_volumetric_line_items(),
            subtotal=768.0,
            total_before_vat=768.0,
            vat=145.92,
            grand_total=768.0,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document/export")

            assert resp.status_code == 200
            content = resp.text
            assert "768.00 EUR" in content or "768,00 EUR" in content
            assert "768.00 RON" not in content
            assert "768 lei" not in content.lower()


class TestQuoteCommercialDocumentExport:
    """Tests for GET /api/v1/entities/quotes/{id}/commercial-document/export"""

    @pytest.mark.asyncio
    async def test_export_returns_html(self):
        """Export endpoint returns valid HTML content."""
        quote = _make_quote_obj(line_items=_banner_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document/export")

            assert resp.status_code == 200
            assert "text/html" in resp.headers.get("content-type", "")
            content = resp.text
            assert "<!DOCTYPE html>" in content
            assert "OFERTĂ COMERCIALĂ" in content
            assert "QT-2025-001" in content

    @pytest.mark.asyncio
    async def test_export_includes_content_disposition(self):
        """Export includes download filename header."""
        quote = _make_quote_obj(line_items=_banner_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document/export")

            assert "content-disposition" in resp.headers
            assert "oferta_QT-2025-001.html" in resp.headers["content-disposition"]

    @pytest.mark.asyncio
    async def test_export_not_found_returns_404(self):
        """Export for non-existent quote returns 404."""
        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/999/commercial-document/export")

            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_export_mesh_shows_externalization(self):
        """Mesh export HTML includes externalization warning."""
        quote = _make_quote_obj(line_items=_mesh_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document/export")

            assert resp.status_code == 200
            content = resp.text
            assert "Externalizare" in content or "EXTERNALIZARE" in content


class TestProductCommercialTextBlocks:
    """Tests for product-specific commercial text blocks."""

    @pytest.mark.asyncio
    async def test_banner_text_blocks(self):
        """Banner template has correct commercial text."""
        quote = _make_quote_obj(line_items=_banner_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            pt = data["product_text"]
            assert "Banner publicitar" in pt["client_title"]
            assert "PVC" in pt["technical_description"]
            assert "1100" in pt["technical_description"] or "1350" in pt["technical_description"]
            assert pt["externalization_note"] is None

    @pytest.mark.asyncio
    async def test_mesh_text_blocks(self):
        """Mesh template has externalization text."""
        quote = _make_quote_obj(line_items=_mesh_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            pt = data["product_text"]
            assert "externalizat" in pt["client_title"].lower() or "externalizat" in pt["short_description"].lower()
            assert pt["externalization_note"] is not None
            assert "furnizor extern" in pt["externalization_note"].lower()

    @pytest.mark.asyncio
    async def test_lightbox_text_blocks(self):
        """Lightbox template has LED/electrical text."""
        quote = _make_quote_obj(line_items=_lightbox_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            pt = data["product_text"]
            assert "LED" in pt["client_title"] or "luminoas" in pt["client_title"].lower()
            assert "LED" in pt["materials_summary"]
            assert pt["externalization_note"] is None

    @pytest.mark.asyncio
    async def test_unknown_template_returns_generic_text(self):
        """Unknown template code returns generic commercial text."""
        line_items = json.dumps({
            "product_definition": {
                "template_code": "TPL-UNKNOWN-PRODUCT",
                "name": "Unknown",
                "family": "OTHER",
            },
        })
        quote = _make_quote_obj(line_items=line_items)

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            pt = data["product_text"]
            assert pt["client_title"] == "Produs personalizat"

    @pytest.mark.asyncio
    async def test_vinyl_text_blocks(self):
        """Vinyl sticker template has correct text."""
        line_items = json.dumps({
            "product_definition": {
                "template_code": "TPL-VINYL-STICKER",
                "name": "Autocolant",
                "family": "VINYL",
            },
        })
        quote = _make_quote_obj(line_items=line_items)

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            pt = data["product_text"]
            assert "Autocolant" in pt["client_title"] or "Sticker" in pt["client_title"]
            assert "vinyl" in pt["materials_summary"].lower()
            assert "laminare" in pt["optional_finishes"].lower()

    @pytest.mark.asyncio
    async def test_volumetric_letters_text_blocks(self):
        """Volumetric letters template has correct text."""
        line_items = json.dumps({
            "product_definition": {
                "template_code": "TPL-VOLUMETRIC-LETTERS",
                "name": "Litere volumetrice",
                "family": "LETTERS",
            },
        })
        quote = _make_quote_obj(line_items=line_items)

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            pt = data["product_text"]
            assert "Litere" in pt["client_title"] or "volumetric" in pt["client_title"].lower()
            assert "vector" in pt["production_assumptions"].lower()

    @pytest.mark.asyncio
    async def test_plexi_text_blocks(self):
        """Plexiglass template has correct text."""
        quote = _make_quote_obj(line_items=_no_readiness_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            pt = data["product_text"]
            assert "plexiglass" in pt["client_title"].lower() or "Plac" in pt["client_title"]
            assert "CNC" in pt["technical_description"] or "laser" in pt["technical_description"]


class TestQuoteOrderProtection:
    """Tests confirming Quote -> Order gates remain intact."""

    @pytest.mark.asyncio
    async def test_commercial_document_does_not_change_quote_status(self):
        """Fetching commercial document does not change quote status."""
        quote = _make_quote_obj(status="draft", line_items=_banner_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "draft"
            # No status update called
            assert not any(
                call[0] == "update_status"
                for call in instance.method_calls
                if hasattr(call, '__getitem__')
            )

    @pytest.mark.asyncio
    async def test_null_line_items_handled_gracefully(self):
        """Quote with null line_items uses single-line fallback aligned to subtotal."""
        quote = _make_quote_obj(line_items=None, total_before_vat=1000.0, grand_total=1210.0)

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            assert resp.status_code == 200
            data = resp.json()
            assert len(data["line_items"]) == 1
            assert data["line_items"][0]["total"] == 1000.0
            assert data["readiness"]["source"] == "unavailable"


class TestClientFacingLineItemConsistency:
    """Commercial document line items must sum to subtotal_without_vat."""

    def _line_sum(self, items: list) -> float:
        return round(sum(float(i.get("total") or 0) for i in items), 2)

    @pytest.mark.asyncio
    async def test_visible_lines_sum_equals_subtotal_without_vat(self):
        quote = _make_quote_obj(
            line_items=_eur_volumetric_shape_b_line_items(),
            total_before_vat=1103.64,
            vat=209.69,
            grand_total=1103.64,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            items = data["line_items"]
            subtotal = data["totals"]["total_before_vat"]
            assert self._line_sum(items) == subtotal

    @pytest.mark.asyncio
    async def test_mismatched_breakdown_uses_single_line_fallback(self):
        quote = _make_quote_obj(
            line_items=_eur_volumetric_shape_b_line_items(),
            total_before_vat=1103.64,
            vat=209.69,
            grand_total=1103.64,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            assert len(data["line_items"]) == 1
            assert data["line_items"][0]["description"] == (
                "Litere volumetrice luminoase conform specificațiilor"
            )
            assert data["line_items"][0]["type"] == "commercial_summary"

    @pytest.mark.asyncio
    async def test_zero_value_lines_hidden(self):
        wrapper = json.loads(_eur_volumetric_shape_b_line_items())
        wrapper["component_breakdown"].append(
            {
                "component_id": "layer_13",
                "name": "layer_13",
                "material_cost": 0,
                "operation_cost": 0,
                "total_component_cost": 0,
            }
        )
        quote = _make_quote_obj(
            line_items=json.dumps(wrapper),
            total_before_vat=1103.64,
            grand_total=1103.64,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            for item in data["line_items"]:
                assert float(item["total"]) > 0
            assert "layer_13" not in json.dumps(data["line_items"]).lower()

    @pytest.mark.asyncio
    async def test_total_equals_subtotal_plus_tva(self):
        quote = _make_quote_obj(
            line_items=_banner_line_items(),
            total_before_vat=1000.0,
            vat=21.0,
            grand_total=1210.0,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            totals = resp.json()["totals"]
            assert round(totals["total_before_vat"] + totals["tva"], 2) == round(
                totals["grand_total"], 2
            )

    @pytest.mark.asyncio
    async def test_validity_display_without_em_dash_when_missing_date(self):
        quote = _make_quote_obj(line_items=_banner_line_items(), valid_until=None)

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            commercial = resp.json()["commercial"]
            assert commercial["validity_display"] == "15 zile de la emitere"
            assert "până la —" not in commercial["validity_display"]

    @pytest.mark.asyncio
    async def test_export_html_no_pana_la_em_dash(self):
        quote = _make_quote_obj(line_items=_banner_line_items(), valid_until=None)

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document/export")

            content = resp.text
            assert "până la —" not in content
            assert "15 zile de la emitere" in content

    @pytest.mark.asyncio
    async def test_volumetric_no_cnc_laser_in_client_document(self):
        line_items = json.dumps(
            {
                "product_definition": {
                    "template_code": "TPL-VOLUMETRIC-LETTERS",
                    "name": "Litere volumetrice",
                },
                "cost_result": {"currency": "EUR"},
            }
        )
        quote = _make_quote_obj(line_items=line_items, total_before_vat=500.0, grand_total=595.0)

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                doc_resp = await client.get("/api/v1/entities/quotes/1/commercial-document")
                export_resp = await client.get(
                    "/api/v1/entities/quotes/1/commercial-document/export"
                )

            doc = doc_resp.json()
            export = export_resp.text
            blob = json.dumps(doc) + export
            assert "CNC/laser" not in blob
            assert "CNC" not in blob
            assert "laser" not in blob.lower()

    @pytest.mark.asyncio
    async def test_no_internal_layer_ids_in_line_items(self):
        quote = _make_quote_obj(
            line_items=_eur_volumetric_shape_b_line_items(),
            total_before_vat=1103.64,
            grand_total=1103.64,
        )

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            items_blob = json.dumps(resp.json()["line_items"]).lower()
            assert "layer_" not in items_blob
            assert "face_panel" not in items_blob
            assert "product_code" not in items_blob

    @pytest.mark.asyncio
    async def test_banner_breakdown_mismatch_uses_fallback(self):
        """Banner cost breakdown (900) vs quote subtotal (1000) → single client line."""
        quote = _make_quote_obj(line_items=_banner_line_items())

        with patch("services.quote_document_service.QuotesService") as MockQS:
            instance = MockQS.return_value
            instance.get_by_id = AsyncMock(return_value=quote)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/entities/quotes/1/commercial-document")

            data = resp.json()
            assert len(data["line_items"]) == 1
            assert data["line_items"][0]["total"] == data["totals"]["total_before_vat"]