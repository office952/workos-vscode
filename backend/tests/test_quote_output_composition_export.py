"""
BUILD 9 — Tests for Quote Output Composition HTML Export.

Verifies:
  - HTML export endpoint exists
  - HTML contains preview-only disclaimer
  - HTML contains rendered sections
  - HTML contains warnings/blockers area
  - HTML does not contain raw debug JSON
  - HTML export creates no Quote
  - HTML export creates no Order
  - HTML export creates no snapshot
  - HTML export does not mutate quote/order
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.quote_output_composition_service import (
    QuoteOutputCompositionService,
    QuoteOutputCompositionResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_composition_dto():
    return {
        "persisted": False,
        "quote_id": 1,
        "quote_code": "Q-2026-EXPORT",
        "composition_type": "quote_output_preview",
        "source": {
            "quote": "read_only",
            "commercial_document": "read_only",
            "output_blocks": "render_preview",
            "product_template": "read_only",
            "blueprint_dossier": "read_only",
        },
        "template_link": {
            "status": "linked_with_dossier",
            "template_id": 1,
            "template_code": "TPL-BANNER-STANDARD",
            "dossier_id": 1,
        },
        "sections": [
            {
                "section_id": "banner-desc-01",
                "title": "Descriere Banner Publicitar",
                "source": "output_blocks",
                "rendered_text": "Banner publicitar PVC Test — imprimare ecosolvent/UV format mare.",
                "warnings": ["width_mm not resolved"],
                "blockers": [],
            },
            {
                "section_id": "banner-tech-01",
                "title": "Specificatii Tehnice Banner",
                "source": "output_blocks",
                "rendered_text": "Tip imprimare: ecosolvent/UV. Role disponibile: 1100/1350/1600mm.",
                "warnings": [],
                "blockers": [],
            },
        ],
        "commercial_summary": {
            "subtotal": 1000.0,
            "vat": 190.0,
            "total": 1190.0,
            "currency": "RON",
        },
        "warnings": ["width_mm not resolved"],
        "blockers": [],
        "trace": {
            "no_persist": True,
            "changed_entities": [],
            "no_quote_mutation": True,
            "no_order_mutation": True,
            "no_snapshot_created": True,
            "not_client_final": True,
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestQuoteOutputCompositionExport:
    """Tests for QuoteOutputCompositionService.render_composition_html."""

    def test_html_contains_preview_disclaimer(self):
        """HTML output contains PREVIEW ONLY disclaimer."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        html = service.render_composition_html(dto)

        assert "PREVIEW ONLY" in html
        assert "not saved" in html.lower() or "Not saved" in html

    def test_html_contains_rendered_sections(self):
        """HTML output contains rendered section text."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        html = service.render_composition_html(dto)

        assert "Descriere Banner Publicitar" in html
        assert "Banner publicitar PVC Test" in html
        assert "Specificatii Tehnice Banner" in html

    def test_html_contains_warnings(self):
        """HTML output contains warnings."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        html = service.render_composition_html(dto)

        assert "width_mm not resolved" in html

    def test_html_contains_commercial_summary(self):
        """HTML output contains commercial summary."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        html = service.render_composition_html(dto)

        assert "1,000.00" in html or "1000.00" in html
        assert "RON" in html

    def test_html_contains_quote_code(self):
        """HTML output contains the quote code."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        html = service.render_composition_html(dto)

        assert "Q-2026-EXPORT" in html

    def test_html_does_not_contain_raw_debug_json(self):
        """HTML output does not contain raw JSON debug dumps."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        html = service.render_composition_html(dto)

        # Should not contain full JSON structure markers
        assert '"persisted": false' not in html.lower()
        assert '"composition_type"' not in html

    def test_html_contains_trace_section(self):
        """HTML output contains trace info."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        html = service.render_composition_html(dto)

        assert "no_persist" in html
        assert "no_quote_mutation" in html

    def test_html_is_valid_html_structure(self):
        """HTML output has proper structure."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        html = service.render_composition_html(dto)

        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html
        assert "<head>" in html
        assert "<body>" in html

    def test_html_empty_sections(self):
        """HTML handles empty sections gracefully."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        dto["sections"] = []
        html = service.render_composition_html(dto)

        assert "No output blocks rendered" in html

    def test_html_with_blockers(self):
        """HTML renders blockers."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        dto["blockers"] = ["missing_dossier_link"]
        html = service.render_composition_html(dto)

        assert "missing_dossier_link" in html

    def test_render_does_not_call_db(self):
        """render_composition_html does not call db at all."""
        db = AsyncMock()
        service = QuoteOutputCompositionService(db)
        dto = _sample_composition_dto()
        service.render_composition_html(dto)

        db.execute.assert_not_called()
        db.commit.assert_not_called()
        db.add.assert_not_called()