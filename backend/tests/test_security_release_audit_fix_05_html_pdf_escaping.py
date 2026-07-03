from __future__ import annotations

import json
from datetime import datetime

import pytest

from routers.quote_documents import _render_document_html
from services.html_safety import escape_html_attr, escape_html_text
from services.quote_output_snapshot_service import QuoteOutputSnapshotService
from services.quote_pdf_service import QuotePdfService
from models.quote_output_snapshots import QuoteOutputSnapshot


class MockResult:
    def __init__(self, obj):
        self._obj = obj

    def scalar_one_or_none(self):
        return self._obj


class MockDBSession:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    async def execute(self, _query):
        return MockResult(self.snapshot)


def _minimal_export_doc() -> dict:
    return {
        "quote_code": "QT-2026-900",
        "version": 1,
        "client": {
            "name": "Client Test",
            "contact_person": "Contact Test",
        },
        "commercial": {
            "currency": "RON",
            "tva_percent": 19,
            "validity_days": 15,
            "payment_terms": "Avans 50%",
            "delivery_terms": "Livrare",
            "warranty_terms": "24 luni",
        },
        "product_summary": {
            "product_name": "Produs",
            "description": "Descriere produs",
        },
        "product_text": {
            "client_title": "Titlu produs",
            "short_description": "Descriere scurta",
            "technical_description": "Descriere tehnica",
            "materials_summary": "Material",
            "operations_summary": "Operatie",
            "included_finishes": "Finisaj inclus",
            "optional_finishes": "Finisaj optional",
            "production_assumptions": "Asumptii",
            "externalization_note": None,
            "limitations": None,
        },
        "line_items": [
            {
                "description": "Linie normala",
                "quantity": 1,
                "unit_price": 100,
                "total": 100,
            }
        ],
        "totals": {
            "subtotal": 100,
            "discount": 0,
            "discount_pct": 0,
            "total_before_vat": 100,
            "tva": 19,
            "grand_total": 119,
            "currency": "RON",
        },
        "metadata": {
            "created_at": "2026-05-29T10:00:00",
            "valid_until": "2026-06-30",
            "notes": None,
        },
        "readiness": {
            "warnings": [],
            "blockers": [],
        },
        "document": {
            "generated_at": "2026-05-29T10:00:00",
        },
    }


class TestHtmlSafetyHelpers:
    def test_escape_html_text_escapes_script(self):
        raw = "<script>alert(1)</script>"
        escaped = escape_html_text(raw)
        assert escaped == "&lt;script&gt;alert(1)&lt;/script&gt;"

    def test_escape_html_text_escapes_critical_chars(self):
        raw = "&<>\"'"
        escaped = escape_html_text(raw)
        assert escaped == "&amp;&lt;&gt;&quot;&#x27;"

    def test_escape_html_text_none_to_empty(self):
        assert escape_html_text(None) == ""

    def test_escape_html_text_preserves_romanian_unicode(self):
        raw = "Client s, t, a, i, Oferta lucrari"
        escaped = escape_html_text(raw)
        assert "Client" in escaped
        assert "Oferta" in escaped

    def test_escape_html_attr_escapes_attr_payload(self):
        raw = '\"><script>alert(1)</script>'
        escaped = escape_html_attr(raw)
        assert "&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;" == escaped


class TestQuoteHtmlExportEscaping:
    def test_quote_html_export_escapes_malicious_dynamic_fields(self):
        doc = _minimal_export_doc()
        payload = '<script>alert(1)</script><img src=x onerror=alert(1)><a href="javascript:alert(1)">click</a>'
        doc["client"]["name"] = payload
        doc["metadata"]["notes"] = payload
        doc["line_items"][0]["description"] = payload

        html = _render_document_html(doc)

        assert "<script>alert(1)</script>" not in html
        assert "<img src=x onerror=alert(1)>" not in html
        assert '<a href="javascript:alert(1)">click</a>' not in html

        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
        assert "&lt;img src=x onerror=alert(1)&gt;" in html
        assert "&lt;a href=&quot;javascript:alert(1)&quot;&gt;click&lt;/a&gt;" in html

    def test_quote_html_export_keeps_normal_text_visible(self):
        doc = _minimal_export_doc()
        doc["client"]["name"] = "Client test normal"
        html = _render_document_html(doc)
        assert "Client test normal" in html


class TestQuotePdfEscaping:
    def test_pdf_html_escapes_malicious_line_item_description(self):
        service = QuotePdfService.__new__(QuotePdfService)
        doc = _minimal_export_doc()
        doc["line_items"][0]["description"] = '<img src=x onerror=alert(1)>'
        doc["product_text"]["short_description"] = '\"><script>alert(1)</script>'

        html = service._render_pdf_html(doc)

        assert "<img src=x onerror=alert(1)>" not in html
        assert '\"><script>alert(1)</script>' not in html

        assert "&lt;img src=x onerror=alert(1)&gt;" in html
        assert "&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;" in html

    def test_pdf_html_keeps_romanian_text_readable(self):
        service = QuotePdfService.__new__(QuotePdfService)
        doc = _minimal_export_doc()
        doc["client"]["name"] = "Client oferta lucrari"
        html = service._render_pdf_html(doc)
        assert "Client oferta lucrari" in html


class TestQuoteOutputSnapshotExportEscaping:
    @pytest.mark.asyncio
    async def test_snapshot_export_escapes_rendered_text(self):
        snapshot = QuoteOutputSnapshot(
            id=1,
            quote_id=1,
            quote_code="Q-2026-001",
            snapshot_code="QDOC-2026-0001",
            snapshot_type="quote_output_candidate",
            status="draft",
            version=1,
            source_template_id=1,
            source_template_code="TPL-1",
            source_dossier_id=1,
            rendered_sections_json=json.dumps(
                [
                    {
                        "title": "Sectiune",
                        "rendered_text": "<script>alert(1)</script>",
                        "warnings": ["<img src=x onerror=alert(1)>"],
                        "blockers": ["<a href=\"javascript:alert(1)\">click</a>"],
                    }
                ]
            ),
            commercial_summary_json=json.dumps({"subtotal": 100.0, "vat": 19.0, "total": 119.0, "currency": "RON"}),
            warnings_json=json.dumps(["\"><script>alert(1)</script>"]),
            blockers_json=json.dumps([]),
            variables_used_json=json.dumps({}),
            trace_json=json.dumps({"quote_mutated": False, "order_mutated": False}),
            content_hash="abc123def456abc123def456abc123de",
            created_by="user@test.com",
            created_at=datetime(2026, 5, 29, 10, 0, 0),
            updated_at=datetime(2026, 5, 29, 10, 0, 0),
        )

        service = QuoteOutputSnapshotService(MockDBSession(snapshot))
        html = await service.export_html(1, 1)

        assert html is not None
        assert "<script>alert(1)</script>" not in html
        assert "<img src=x onerror=alert(1)>" not in html
        assert '<a href="javascript:alert(1)">click</a>' not in html

        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
        assert "&lt;img src=x onerror=alert(1)&gt;" in html
        assert "&lt;a href=&quot;javascript:alert(1)&quot;&gt;click&lt;/a&gt;" in html

    @pytest.mark.asyncio
    async def test_snapshot_export_keeps_normal_text_visible(self):
        snapshot = QuoteOutputSnapshot(
            id=1,
            quote_id=1,
            quote_code="Q-2026-001",
            snapshot_code="QDOC-2026-0001",
            snapshot_type="quote_output_candidate",
            status="draft",
            version=1,
            source_template_id=1,
            source_template_code="TPL-1",
            source_dossier_id=1,
            rendered_sections_json=json.dumps(
                [
                    {
                        "title": "Sectiune",
                        "rendered_text": "Client oferta lucrari",
                        "warnings": [],
                        "blockers": [],
                    }
                ]
            ),
            commercial_summary_json=json.dumps({"subtotal": 100.0, "vat": 19.0, "total": 119.0, "currency": "RON"}),
            warnings_json=json.dumps([]),
            blockers_json=json.dumps([]),
            variables_used_json=json.dumps({}),
            trace_json=json.dumps({"quote_mutated": False, "order_mutated": False}),
            content_hash="abc123def456abc123def456abc123de",
            created_by="user@test.com",
            created_at=datetime(2026, 5, 29, 10, 0, 0),
            updated_at=datetime(2026, 5, 29, 10, 0, 0),
        )

        service = QuoteOutputSnapshotService(MockDBSession(snapshot))
        html = await service.export_html(1, 1)
        assert html is not None
        assert "Client oferta lucrari" in html
