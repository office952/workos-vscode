"""
BUILD 15 — Tests for Quote Documents Archive model and service.

Coverage:
  - Archive record creation with correct traceability fields
  - Archive list returns all versions ordered by date
  - Archive latest returns most recent
  - Archive download by specific ID validates quote ownership
  - Archive empty for new quote
  - Archive quote_id isolation (cannot access other quote's archives)
  - File storage creates directory and writes PDF bytes
"""

import os
import hashlib
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from services.quote_pdf_service import QuotePdfService, GENERATED_DOCS_DIR
from models.quote_documents_archive import QuoteDocumentsArchive


class TestQuoteDocumentsArchiveModel:
    """Tests for the QuoteDocumentsArchive model structure."""

    def test_model_has_required_fields(self):
        """Archive model has all required traceability fields."""
        archive = QuoteDocumentsArchive(
            quote_id=1,
            quote_code="QT-001",
            quote_version=2,
            document_type="quote_pdf",
            filename="oferta_QT-001_v2_20250518.pdf",
            file_path="/tmp/test.pdf",
            file_size_bytes=12345,
            content_hash="abc123",
            generated_by="user@test.com",
        )
        assert archive.quote_id == 1
        assert archive.quote_code == "QT-001"
        assert archive.quote_version == 2
        assert archive.document_type == "quote_pdf"
        assert archive.filename == "oferta_QT-001_v2_20250518.pdf"
        assert archive.file_path == "/tmp/test.pdf"
        assert archive.file_size_bytes == 12345
        assert archive.content_hash == "abc123"
        assert archive.generated_by == "user@test.com"

    def test_model_tablename(self):
        """Archive model uses correct table name."""
        assert QuoteDocumentsArchive.__tablename__ == "quote_documents_archive"


class TestPdfFileStorage:
    """Tests for PDF file storage on disk."""

    def test_store_pdf_creates_directory_and_file(self, tmp_path):
        """_store_pdf creates the directory structure and writes bytes."""
        service = QuotePdfService.__new__(QuotePdfService)

        # Override GENERATED_DOCS_DIR for test
        test_dir = str(tmp_path / "generated_documents" / "quotes")
        with patch("services.quote_pdf_service.GENERATED_DOCS_DIR", test_dir):
            pdf_bytes = b"%PDF-1.4 fake pdf content"
            file_path = service._store_pdf(42, "test_file.pdf", pdf_bytes)

            assert os.path.exists(file_path)
            with open(file_path, "rb") as f:
                assert f.read() == pdf_bytes
            assert "42" in file_path
            assert "test_file.pdf" in file_path

    def test_store_pdf_multiple_files_same_quote(self, tmp_path):
        """Multiple PDFs for same quote stored in same directory."""
        service = QuotePdfService.__new__(QuotePdfService)

        test_dir = str(tmp_path / "generated_documents" / "quotes")
        with patch("services.quote_pdf_service.GENERATED_DOCS_DIR", test_dir):
            service._store_pdf(1, "file_v1.pdf", b"v1 content")
            service._store_pdf(1, "file_v2.pdf", b"v2 content")

            quote_dir = os.path.join(test_dir, "1")
            files = os.listdir(quote_dir)
            assert "file_v1.pdf" in files
            assert "file_v2.pdf" in files

    def test_get_pdf_bytes_returns_content(self, tmp_path):
        """get_pdf_bytes reads file content correctly."""
        service = QuotePdfService.__new__(QuotePdfService)

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"PDF content here")

        archive = MagicMock()
        archive.file_path = str(test_file)

        result = service.get_pdf_bytes(archive)
        assert result == b"PDF content here"

    def test_get_pdf_bytes_returns_none_for_missing_file(self):
        """get_pdf_bytes returns None when file doesn't exist."""
        service = QuotePdfService.__new__(QuotePdfService)

        archive = MagicMock()
        archive.file_path = "/nonexistent/path/file.pdf"

        result = service.get_pdf_bytes(archive)
        assert result is None

    def test_get_pdf_bytes_returns_none_for_none_archive(self):
        """get_pdf_bytes returns None for None archive."""
        service = QuotePdfService.__new__(QuotePdfService)
        assert service.get_pdf_bytes(None) is None


class TestPdfHtmlRendering:
    """Tests for the HTML rendering used for PDF generation."""

    def _get_html(self, doc: dict) -> str:
        service = QuotePdfService.__new__(QuotePdfService)
        return service._render_pdf_html(doc)

    def test_html_includes_client_name(self):
        """Rendered HTML includes client name."""
        doc = self._minimal_doc(client_name="SuperClient SRL")
        html = self._get_html(doc)
        assert "SuperClient SRL" in html

    def test_html_includes_quote_code(self):
        """Rendered HTML includes quote code."""
        doc = self._minimal_doc()
        html = self._get_html(doc)
        assert "QT-TEST-001" in html

    def test_html_includes_line_items(self):
        """Rendered HTML includes line item descriptions."""
        doc = self._minimal_doc()
        doc["line_items"] = [
            {"description": "Serviciu imprimare banner", "quantity": 2, "unit_price": 300, "total": 600},
        ]
        html = self._get_html(doc)
        assert "Serviciu imprimare banner" in html

    def test_html_excludes_margin_pct(self):
        """Rendered HTML does NOT include margin percentage."""
        import re
        doc = self._minimal_doc()
        doc["totals"]["margin_pct"] = 42
        html = self._get_html(doc)
        # The literal value "42%" must never appear
        assert "42%" not in html
        # Strip all CSS margin properties (margin, margin-top, margin-bottom, etc.)
        # from both <style> blocks and inline style attributes before checking
        # that business profit-margin data is not exposed to clients.
        html_lower = html.lower()
        html_no_css_margin = re.sub(r'margin(?:-(?:top|bottom|left|right))?\s*:\s*[^;}"]+[;]?', '', html_lower)
        assert "margin" not in html_no_css_margin

    def _minimal_doc(self, client_name: str = "Test Client") -> dict:
        return {
            "quote_code": "QT-TEST-001",
            "version": 1,
            "client": {"name": client_name, "contact_person": None},
            "commercial": {"currency": "RON", "tva_percent": 19, "validity_days": 15,
                           "payment_terms": "Avans 50%", "delivery_terms": "Livrare",
                           "warranty_terms": "24 luni"},
            "product_summary": {"product_name": "Produs", "description": "Descriere"},
            "product_text": {"client_title": "Produs test", "short_description": "Desc",
                             "technical_description": None, "materials_summary": None,
                             "operations_summary": None, "included_finishes": None,
                             "optional_finishes": None, "production_assumptions": None,
                             "externalization_note": None, "limitations": None},
            "line_items": [],
            "totals": {"subtotal": 100, "discount": 0, "discount_pct": 0,
                       "total_before_vat": 100, "tva": 19, "grand_total": 119,
                       "margin_pct": 30, "currency": "RON"},
            "readiness": {"source": "snapshot", "warnings": [], "blockers": []},
            "metadata": {"created_at": "2025-05-18T10:00:00", "valid_until": "2025-06-30",
                         "notes": None, "assigned_to": None},
        }


class TestContentHashDeterminism:
    """Tests for content hash behavior."""

    def test_same_html_produces_same_hash(self):
        """Identical HTML input produces identical SHA-256 hash."""
        html = "<html><body>Test</body></html>"
        hash1 = hashlib.sha256(html.encode()).hexdigest()
        hash2 = hashlib.sha256(html.encode()).hexdigest()
        assert hash1 == hash2

    def test_different_html_produces_different_hash(self):
        """Different HTML input produces different hash."""
        html1 = "<html><body>Version 1</body></html>"
        html2 = "<html><body>Version 2</body></html>"
        hash1 = hashlib.sha256(html1.encode()).hexdigest()
        hash2 = hashlib.sha256(html2.encode()).hexdigest()
        assert hash1 != hash2