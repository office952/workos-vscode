"""
BUILD 15 — Quote PDF Generation Service.

Responsibilities:
  - Convert QuoteDocumentService DTO into a client-facing PDF.
  - Store generated PDF on filesystem.
  - Create archive record in DB.
  - Enforce content filtering (no margin, profit, supplier costs, internal notes).

TVA Rules:
  - TVA amount comes from DTO totals.tva (already calculated by backend).
  - TVA percent is ONLY shown if commercial.tva_percent is present and > 0.
  - NEVER hardcode 19% or 21%.
  - If both tva amount and percent are missing → "TVA: conform legislației în vigoare".

Must NOT:
  - Recalculate CostEngine.
  - Import inventory/stock modules.
  - Import SmartBill.
  - Send emails.
  - Mutate quotes or orders.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.quote_documents_archive import QuoteDocumentsArchive
from services.html_safety import escape_html_text
from services.quote_document_service import QuoteDocumentService

logger = logging.getLogger(__name__)

# Storage base directory (relative to backend root)
GENERATED_DOCS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "generated_documents",
    "quotes",
)


class QuotePdfService:
    """Generates client-facing quote PDFs and manages the archive."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._document_service = QuoteDocumentService(db)

    async def generate_pdf(
        self,
        quote_id: int,
        generated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a PDF for the given quote and store it.

        Returns archive record dict on success, or error dict on failure.
        """
        # 1. Build the commercial document DTO
        document = await self._document_service.build_commercial_document(quote_id)
        if "error" in document:
            return document

        # 2. Render HTML for PDF (client-facing, filtered)
        html_content = self._render_pdf_html(document)

        # 3. Convert HTML to PDF bytes
        pdf_bytes = self._html_to_pdf(html_content)
        if pdf_bytes is None:
            return {"error": "pdf_generation_failed", "quote_id": quote_id}

        # 4. Compute content hash
        content_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # 5. Store PDF on filesystem
        quote_code = document.get("quote_code", f"QT-{quote_id}")
        quote_version = document.get("version", 1)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"oferta_{quote_code}_v{quote_version}_{timestamp}.pdf"

        file_path = self._store_pdf(quote_id, filename, pdf_bytes)

        # 6. Create archive record
        archive = QuoteDocumentsArchive(
            quote_id=quote_id,
            quote_code=quote_code,
            quote_version=quote_version,
            document_type="quote_pdf",
            filename=filename,
            file_path=file_path,
            file_size_bytes=len(pdf_bytes),
            content_hash=content_hash,
            generated_by=generated_by,
            source_snapshot_id=None,
            notes=None,
        )
        self.db.add(archive)
        await self.db.commit()
        await self.db.refresh(archive)

        return {
            "id": archive.id,
            "quote_id": archive.quote_id,
            "quote_code": archive.quote_code,
            "quote_version": archive.quote_version,
            "filename": archive.filename,
            "file_size_bytes": archive.file_size_bytes,
            "content_hash": archive.content_hash,
            "generated_by": archive.generated_by,
            "created_at": archive.created_at.isoformat() if archive.created_at else None,
        }

    async def get_latest(self, quote_id: int) -> Optional[QuoteDocumentsArchive]:
        """Get the most recent archive record for a quote."""
        stmt = (
            select(QuoteDocumentsArchive)
            .where(QuoteDocumentsArchive.quote_id == quote_id)
            .order_by(desc(QuoteDocumentsArchive.created_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_archive_list(self, quote_id: int) -> list:
        """Get all archive records for a quote, ordered by newest first."""
        stmt = (
            select(QuoteDocumentsArchive)
            .where(QuoteDocumentsArchive.quote_id == quote_id)
            .order_by(desc(QuoteDocumentsArchive.created_at))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_archive_by_id(
        self, quote_id: int, archive_id: int
    ) -> Optional[QuoteDocumentsArchive]:
        """Get a specific archive record, validating quote_id ownership."""
        stmt = select(QuoteDocumentsArchive).where(
            QuoteDocumentsArchive.id == archive_id,
            QuoteDocumentsArchive.quote_id == quote_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_pdf_bytes(self, archive: QuoteDocumentsArchive) -> Optional[bytes]:
        """Read PDF bytes from filesystem for a given archive record."""
        if not archive or not archive.file_path:
            return None
        if not os.path.exists(archive.file_path):
            return None
        with open(archive.file_path, "rb") as f:
            return f.read()

    # -----------------------------------------------------------------------
    # Private: PDF HTML rendering (client-facing, filtered)
    # -----------------------------------------------------------------------

    def _render_pdf_html(self, doc: Dict[str, Any]) -> str:
        """Render client-facing HTML for PDF conversion.

        CONTENT FILTERING RULES:
        - INCLUDED: client info, product description, line items, totals, commercial terms
        - EXCLUDED: margin_pct, profit, supplier costs, internal notes, assigned_to, readiness blockers
        - TVA: amount from data only, percent only if available
        """
        e = escape_html_text

        client = doc.get("client", {})
        commercial = doc.get("commercial", {})
        product_text = doc.get("product_text", {})
        totals = doc.get("totals", {})
        line_items = doc.get("line_items", [])
        metadata = doc.get("metadata", {})
        presentation_currency = (
            totals.get("currency")
            or commercial.get("currency")
            or "RON"
        )

        # Build line items table rows
        items_html = ""
        for idx, item in enumerate(line_items, 1):
            items_html += (
                f'<tr>'
                f'<td style="padding:6px 8px;border-bottom:1px solid #ddd;text-align:center;">{e(idx)}</td>'
                f'<td style="padding:6px 8px;border-bottom:1px solid #ddd;">{e(item.get("description", "—"))}</td>'
                f'<td style="padding:6px 8px;border-bottom:1px solid #ddd;text-align:center;">{e(item.get("quantity", 1))}</td>'
                f'<td style="padding:6px 8px;border-bottom:1px solid #ddd;text-align:right;">{e(self._fmt(item.get("unit_price", 0)))}</td>'
                f'<td style="padding:6px 8px;border-bottom:1px solid #ddd;text-align:right;">{e(self._fmt(item.get("total", 0)))}</td>'
                f'</tr>'
            )

        # TVA display logic — NEVER hardcode percentage
        tva_amount = totals.get("tva", 0)
        tva_percent = commercial.get("tva_percent")
        if tva_percent is not None:
            pct = float(tva_percent)
            tva_display = (
                f"TVA ({e(pct)}%): {e(self._fmt(tva_amount))} {e(presentation_currency)}"
            )
        elif tva_amount:
            tva_display = f"TVA: {e(self._fmt(tva_amount))} {e(presentation_currency)}"
        else:
            tva_display = "TVA: conform legislației în vigoare"

        # Discount row
        discount_html = ""
        if totals.get("discount", 0) > 0:
            discount_pct = totals.get("discount_pct", 0)
            discount_label = f"Discount ({discount_pct}%)" if discount_pct else "Discount"
            discount_html = (
                f'<tr><td colspan="4" style="padding:4px 8px;text-align:right;">{e(discount_label)}:</td>'
                f'<td style="padding:4px 8px;text-align:right;">-{e(self._fmt(totals.get("discount", 0)))} {e(presentation_currency)}</td></tr>'
            )

        # Externalization note
        ext_html = ""
        ext_note = product_text.get("externalization_note")
        if ext_note:
            ext_html = (
                f'<div style="margin-top:16px;padding:10px;border:1px solid #f59e0b;background:#fffbeb;">'
                f'<strong>Externalizare:</strong> {e(ext_note)}</div>'
            )

        # Technical specs section
        specs_html = ""
        if product_text.get("materials_summary") or product_text.get("operations_summary"):
            specs_parts = []
            if product_text.get("materials_summary"):
                specs_parts.append(f"<p><strong>Materiale:</strong> {e(product_text['materials_summary'])}</p>")
            if product_text.get("operations_summary"):
                specs_parts.append(f"<p><strong>Operații:</strong> {e(product_text['operations_summary'])}</p>")
            if product_text.get("included_finishes"):
                specs_parts.append(f"<p><strong>Finisaje incluse:</strong> {e(product_text['included_finishes'])}</p>")
            if product_text.get("optional_finishes"):
                specs_parts.append(f"<p><strong>Finisaje opționale:</strong> {e(product_text['optional_finishes'])}</p>")
            specs_html = f'<h2 style="font-size:14px;color:#1e40af;border-bottom:1px solid #dbeafe;padding-bottom:4px;margin-top:20px;">Specificații tehnice</h2>{"".join(specs_parts)}'

        # Production notes
        prod_notes_html = ""
        if product_text.get("production_assumptions"):
            prod_notes_html = (
                f'<h2 style="font-size:14px;color:#1e40af;border-bottom:1px solid #dbeafe;padding-bottom:4px;margin-top:20px;">Observații producție</h2>'
                f'<p>{e(product_text["production_assumptions"])}</p>'
            )
            if product_text.get("limitations"):
                prod_notes_html += f'<p style="color:#92400e;"><strong>Limitări:</strong> {e(product_text["limitations"])}</p>'

        html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8"/>
<title>Oferta {e(doc.get("quote_code", ""))}</title>
<style>
body {{
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11px;
    color: #1f2937;
    line-height: 1.4;
    margin: 30px;
}}
h1 {{
    font-size: 20px;
    color: #1e40af;
    margin: 0 0 4px 0;
}}
h2 {{
    font-size: 14px;
    color: #1e40af;
    margin-top: 20px;
    margin-bottom: 8px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
}}
th {{
    background: #eff6ff;
    padding: 8px;
    text-align: left;
    font-size: 10px;
    text-transform: uppercase;
    border-bottom: 2px solid #bfdbfe;
}}
.header-table td {{
    vertical-align: top;
    padding: 0;
}}
.totals-table td {{
    padding: 4px 8px;
}}
</style>
</head>
<body>

<table class="header-table" style="width:100%;margin-bottom:20px;border-bottom:3px solid #2563eb;padding-bottom:16px;">
<tr>
<td style="width:60%;">
<h1>OFERTĂ COMERCIALĂ</h1>
<p style="margin:2px 0;font-size:12px;color:#4b5563;">{e(product_text.get("client_title") or doc.get("product_summary", {}).get("product_name", "Produs"))}</p>
</td>
<td style="width:40%;text-align:right;font-size:11px;color:#6b7280;">
<p style="margin:2px 0;"><strong>Cod:</strong> {e(doc.get("quote_code", "—"))}</p>
<p style="margin:2px 0;"><strong>Data:</strong> {e(self._fmt_date(metadata.get("created_at")))}</p>
<p style="margin:2px 0;"><strong>Valabilitate:</strong> {e(metadata.get("valid_until") or "—")}</p>
<p style="margin:2px 0;"><strong>Versiune:</strong> {e(doc.get("version", 1))}</p>
</td>
</tr>
</table>

<h2 style="font-size:14px;color:#1e40af;border-bottom:1px solid #dbeafe;padding-bottom:4px;">Client</h2>
<p><strong>{e(client.get("name", "—"))}</strong></p>
{f"<p>Contact: {e(client.get('contact_person'))}</p>" if client.get("contact_person") else ""}

<h2 style="font-size:14px;color:#1e40af;border-bottom:1px solid #dbeafe;padding-bottom:4px;margin-top:20px;">Descriere produs</h2>
<p>{e(product_text.get("short_description") or doc.get("product_summary", {}).get("description", "—"))}</p>
{f"<p style='font-size:10px;color:#4b5563;'><em>{e(product_text.get('technical_description'))}</em></p>" if product_text.get("technical_description") else ""}

{specs_html}

<h2 style="font-size:14px;color:#1e40af;border-bottom:1px solid #dbeafe;padding-bottom:4px;margin-top:20px;">Detaliere preț</h2>
<table>
<thead>
<tr>
<th style="width:30px;text-align:center;">#</th>
<th>Descriere</th>
<th style="width:50px;text-align:center;">Cant.</th>
<th style="width:80px;text-align:right;">Preț unit.</th>
<th style="width:80px;text-align:right;">Total</th>
</tr>
</thead>
<tbody>
{items_html}
</tbody>
</table>

<table class="totals-table" style="width:100%;margin-top:12px;border-top:2px solid #1e40af;">
<tr><td colspan="4" style="text-align:right;padding:4px 8px;">Subtotal:</td>
<td style="text-align:right;padding:4px 8px;">{e(self._fmt(totals.get("subtotal", 0)))} {e(presentation_currency)}</td></tr>
{discount_html}
<tr><td colspan="4" style="text-align:right;padding:4px 8px;">Total fără TVA:</td>
<td style="text-align:right;padding:4px 8px;">{e(self._fmt(totals.get("total_before_vat", 0)))} {e(presentation_currency)}</td></tr>
<tr><td colspan="4" style="text-align:right;padding:4px 8px;">{tva_display.split(":")[0]}:</td>
<td style="text-align:right;padding:4px 8px;">{e(tva_display.split(": ", 1)[1] if ": " in tva_display else tva_display)}</td></tr>
<tr style="font-weight:bold;font-size:14px;"><td colspan="4" style="text-align:right;padding:8px;border-top:1px solid #93c5fd;">TOTAL:</td>
<td style="text-align:right;padding:8px;border-top:1px solid #93c5fd;">{e(self._fmt(totals.get("grand_total", 0)))} {e(presentation_currency)}</td></tr>
</table>

<h2 style="font-size:14px;color:#1e40af;border-bottom:1px solid #dbeafe;padding-bottom:4px;margin-top:20px;">Condiții comerciale</h2>
<div style="background:#f9fafb;border:1px solid #e5e7eb;padding:12px;font-size:11px;">
<p style="margin:3px 0;"><strong>Valabilitate ofertă:</strong> {e(commercial.get("validity_days", 15))} zile</p>
<p style="margin:3px 0;"><strong>Condiții plată:</strong> {e(commercial.get("payment_terms", "—"))}</p>
<p style="margin:3px 0;"><strong>Condiții livrare:</strong> {e(commercial.get("delivery_terms", "—"))}</p>
<p style="margin:3px 0;"><strong>Garanție:</strong> {e(commercial.get("warranty_terms", "—"))}</p>
<p style="margin:3px 0;"><strong>Monedă:</strong> {e(presentation_currency)}</p>
</div>

{prod_notes_html}
{ext_html}

<div style="margin-top:30px;padding-top:12px;border-top:1px solid #e5e7eb;font-size:9px;color:#9ca3af;text-align:center;">
Document generat automat — {e(doc.get("quote_code", ""))} — {e(self._fmt_date(datetime.utcnow().isoformat()))}
</div>

</body>
</html>"""
        return html

    def _html_to_pdf(self, html_content: str) -> Optional[bytes]:
        """Convert HTML string to PDF bytes using xhtml2pdf."""
        try:
            from xhtml2pdf import pisa

            buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=buffer)
            if pisa_status.err:
                logger.error(f"xhtml2pdf conversion errors: {pisa_status.err}")
                return None
            return buffer.getvalue()
        except ImportError:
            logger.error("xhtml2pdf not installed — cannot generate PDF")
            return None
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return None

    def _store_pdf(self, quote_id: int, filename: str, pdf_bytes: bytes) -> str:
        """Store PDF bytes on filesystem. Returns the file path."""
        quote_dir = os.path.join(GENERATED_DOCS_DIR, str(quote_id))
        os.makedirs(quote_dir, exist_ok=True)
        file_path = os.path.join(quote_dir, filename)
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        return file_path

    @staticmethod
    def _fmt(val) -> str:
        """Format number as Romanian currency string."""
        try:
            v = float(val or 0)
            return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return "0,00"

    @staticmethod
    def _fmt_date(dt_str) -> str:
        """Format ISO datetime to Romanian date string."""
        if not dt_str:
            return "—"
        try:
            if "T" in str(dt_str):
                dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(str(dt_str), "%Y-%m-%d")
            return dt.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            return str(dt_str)[:10] if dt_str else "—"