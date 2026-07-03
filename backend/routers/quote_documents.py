"""
BUILD 5 — Quote Commercial Document Router.

Endpoints:
  GET /api/v1/entities/quotes/{quote_id}/commercial-document
    Returns the client-facing commercial document DTO.

  GET /api/v1/entities/quotes/{quote_id}/commercial-document/export
    Returns the document as downloadable HTML.

Auth: follows existing project pattern (get_current_user dependency).
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from services.html_safety import escape_html_text
from services.quote_document_service import QuoteDocumentService, _format_validity_display

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/quotes",
    tags=["quote-documents"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/{quote_id}/commercial-document")
async def get_commercial_document(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the client-facing commercial document for a quote.

    Returns a stable DTO with all commercial information needed for
    client presentation, export, or preview.

    Does NOT recalculate CostEngine or ProductReadiness.
    Uses only existing quote/snapshot data.
    """
    service = QuoteDocumentService(db)
    document = await service.build_commercial_document(quote_id)

    if "error" in document:
        error = document["error"]
        if error == "quote_not_found":
            raise HTTPException(status_code=404, detail="Quote not found")
        raise HTTPException(status_code=500, detail=error)

    return document


@router.get("/{quote_id}/commercial-document/export", response_class=HTMLResponse)
async def export_commercial_document(
    quote_id: int,
    format: str = Query("html", description="Export format: html"),
    db: AsyncSession = Depends(get_db),
):
    """Export the commercial document as a downloadable HTML file.

    Supported formats: html (default).
    The HTML is print-ready with professional styling.
    """
    service = QuoteDocumentService(db)
    document = await service.build_commercial_document(quote_id)

    if "error" in document:
        error = document["error"]
        if error == "quote_not_found":
            raise HTTPException(status_code=404, detail="Quote not found")
        raise HTTPException(status_code=500, detail=error)

    html_content = _render_document_html(document)
    return HTMLResponse(
        content=html_content,
        headers={
            "Content-Disposition": f'attachment; filename="oferta_{document["quote_code"]}.html"',
        },
    )


def _render_document_html(doc: dict) -> str:
    """Render commercial document as professional print-ready HTML."""
    e = escape_html_text

    client = doc.get("client", {})
    commercial = doc.get("commercial", {})
    product_text = doc.get("product_text", {})
    totals = doc.get("totals", {})
    line_items = doc.get("line_items", [])
    metadata = doc.get("metadata", {})
    readiness = doc.get("readiness", {})

    # Build line items rows
    items_html = ""
    for idx, item in enumerate(line_items, 1):
        items_html += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #e5e7eb;">{e(idx)}</td>
            <td style="padding:8px;border-bottom:1px solid #e5e7eb;">{e(item.get('description', '—'))}</td>
            <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:center;">{e(item.get('quantity', 1))}</td>
            <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;">{e(_fmt_currency(item.get('unit_price', 0)))}</td>
            <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:600;">{e(_fmt_currency(item.get('total', 0)))}</td>
        </tr>"""

    # Externalization note
    ext_section = ""
    ext_note = product_text.get("externalization_note")
    if ext_note:
        ext_section = f"""
        <div style="margin-top:24px;padding:12px 16px;background:#fef3c7;border:1px solid #f59e0b;border-radius:6px;">
            <strong>⚠️ Externalizare:</strong><br/>
            {e(ext_note)}
        </div>"""

    # Readiness warnings (internal note style)
    readiness_section = ""
    warnings = readiness.get("warnings", [])
    blockers = readiness.get("blockers", [])
    if warnings or blockers:
        items_list = ""
        for w in warnings:
            w_text = w if isinstance(w, str) else str(w)
            items_list += f"<li style='color:#d97706;'>{e(w_text)}</li>"
        for b in blockers:
            b_text = b if isinstance(b, str) else str(b)
            items_list += f"<li style='color:#dc2626;'>{e(b_text)}</li>"
        readiness_section = f"""
        <div style="margin-top:16px;padding:12px 16px;background:#fef2f2;border:1px solid #fca5a5;border-radius:6px;">
            <strong>Note pregătire producție:</strong>
            <ul style="margin:8px 0 0 16px;">{items_list}</ul>
        </div>"""

    validity_display = commercial.get("validity_display")
    if not validity_display:
        validity_display = _format_validity_display(
            metadata.get("valid_until"),
            int(commercial.get("validity_days") or 15),
        )

    html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ofertă {e(doc.get('quote_code', ''))}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 32px;
            color: #1f2937;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 32px;
        }}
        .header h1 {{
            font-size: 24px;
            color: #1e40af;
            margin: 0;
        }}
        .header .meta {{
            text-align: right;
            font-size: 13px;
            color: #6b7280;
        }}
        .section {{
            margin-bottom: 24px;
        }}
        .section h2 {{
            font-size: 16px;
            color: #1e40af;
            border-bottom: 1px solid #dbeafe;
            padding-bottom: 6px;
            margin-bottom: 12px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
        }}
        th {{
            background: #eff6ff;
            padding: 10px 8px;
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
            color: #374151;
            border-bottom: 2px solid #bfdbfe;
        }}
        .totals {{
            margin-top: 16px;
            border-top: 2px solid #1e40af;
            padding-top: 12px;
        }}
        .totals .row {{
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            font-size: 14px;
        }}
        .totals .grand {{
            font-size: 18px;
            font-weight: 700;
            color: #1e40af;
            border-top: 1px solid #93c5fd;
            padding-top: 8px;
            margin-top: 8px;
        }}
        .terms {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 16px;
            font-size: 13px;
        }}
        .terms p {{
            margin: 4px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
            font-size: 11px;
            color: #9ca3af;
            text-align: center;
        }}
        @media print {{
            body {{ padding: 20px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>OFERTĂ COMERCIALĂ</h1>
            <p style="margin:4px 0;font-size:14px;color:#4b5563;">
                {e(product_text.get('client_title') or doc.get('product_summary', {}).get('product_name', 'Produs'))}
            </p>
        </div>
        <div class="meta">
            <p><strong>Cod:</strong> {e(doc.get('quote_code', '—'))}</p>
            <p><strong>Data:</strong> {e(_fmt_date(metadata.get('created_at')))}</p>
            <p><strong>Valabilitate:</strong> {e(validity_display)}</p>
            <p><strong>Versiune:</strong> {e(doc.get('version', 1))}</p>
        </div>
    </div>

    <div class="section">
        <h2>Client</h2>
        <p><strong>{e(client.get('name', '—'))}</strong></p>
        {f"<p>Contact: {e(client.get('contact_person'))}</p>" if client.get('contact_person') else ""}
    </div>

    <div class="section">
        <h2>Descriere produs</h2>
        <p>{e(product_text.get('short_description') or doc.get('product_summary', {}).get('description', '—'))}</p>
        {f"<p style='font-size:13px;color:#4b5563;margin-top:8px;'><em>{e(product_text.get('technical_description'))}</em></p>" if product_text.get('technical_description') else ""}
    </div>

    {f'''<div class="section">
        <h2>Specificații tehnice</h2>
        {f"<p><strong>Materiale:</strong> {e(product_text.get('materials_summary'))}</p>" if product_text.get('materials_summary') else ""}
        {f"<p><strong>Operații:</strong> {e(product_text.get('operations_summary'))}</p>" if product_text.get('operations_summary') else ""}
        {f"<p><strong>Finisaje incluse:</strong> {e(product_text.get('included_finishes'))}</p>" if product_text.get('included_finishes') else ""}
        {f"<p><strong>Finisaje opționale:</strong> {e(product_text.get('optional_finishes'))}</p>" if product_text.get('optional_finishes') else ""}
    </div>''' if product_text.get('materials_summary') or product_text.get('operations_summary') else ""}

    <div class="section">
        <h2>Detaliere preț</h2>
        <table>
            <thead>
                <tr>
                    <th style="width:40px;">#</th>
                    <th>Descriere</th>
                    <th style="width:60px;text-align:center;">Cant.</th>
                    <th style="width:100px;text-align:right;">Preț unit.</th>
                    <th style="width:100px;text-align:right;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <div class="totals">
            <div class="row">
                <span>Subtotal:</span>
                <span>{e(_fmt_currency(totals.get('subtotal', 0)))} {e(totals.get('currency', 'RON'))}</span>
            </div>
            {f'<div class="row"><span>Discount ({e(totals.get("discount_pct", 0))}%):</span><span>-{e(_fmt_currency(totals.get("discount", 0)))} {e(totals.get("currency", "RON"))}</span></div>' if totals.get('discount', 0) > 0 else ""}
            <div class="row">
                <span>Total fără TVA:</span>
                <span>{e(_fmt_currency(totals.get('total_before_vat', 0)))} {e(totals.get('currency', 'RON'))}</span>
            </div>
            <div class="row">
                <span>TVA ({e(commercial.get('tva_percent', 0))}%):</span>
                <span>{e(_fmt_currency(totals.get('tva', 0)))} {e(totals.get('currency', 'RON'))}</span>
            </div>
            <div class="row grand">
                <span>TOTAL:</span>
                <span>{e(_fmt_currency(totals.get('grand_total', 0)))} {e(totals.get('currency', 'RON'))}</span>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Condiții comerciale</h2>
        <div class="terms">
            <p><strong>Valabilitate ofertă:</strong> {e(validity_display)}</p>
            <p><strong>Condiții plată:</strong> {e(commercial.get('payment_terms', '—'))}</p>
            <p><strong>Condiții livrare:</strong> {e(commercial.get('delivery_terms', '—'))}</p>
            <p><strong>Garanție:</strong> {e(commercial.get('warranty_terms', '—'))}</p>
            <p><strong>Monedă:</strong> {e(commercial.get('currency', 'RON'))}</p>
        </div>
    </div>

    {f'''<div class="section">
        <h2>Observații producție</h2>
        <p>{e(product_text.get('production_assumptions', ''))}</p>
        {f"<p style='color:#92400e;'><strong>Limitări:</strong> {e(product_text.get('limitations'))}</p>" if product_text.get('limitations') else ""}
    </div>''' if product_text.get('production_assumptions') else ""}

    {ext_section}
    {readiness_section}

    {f'<div class="section"><p style="font-size:13px;color:#6b7280;"><em>Note: {e(metadata.get("notes"))}</em></p></div>' if metadata.get('notes') else ""}

    <div class="footer">
        <p>Document generat automat — {e(doc.get('quote_code', ''))} — {e(_fmt_date(doc.get('document', {}).get('generated_at')))}</p>
    </div>
</body>
</html>"""
    return html


def _fmt_currency(val) -> str:
    """Format number as Romanian currency."""
    try:
        v = float(val or 0)
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "0,00"


def _fmt_date(dt_str) -> str:
    """Format ISO datetime to Romanian date."""
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