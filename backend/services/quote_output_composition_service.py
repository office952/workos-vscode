"""
BUILD 9 — Quote Output Composition Preview Service.

Composes a read-only preview of the quote's output blocks composition.
Combines:
  - Quote data (read-only)
  - QuoteCommercialDocument reference (read-only)
  - Output Blocks render preview (from Build 8)
  - ProductTemplate / BlueprintDossier link (read-only)
  - Readiness / warnings (read-only)

Rules:
  - Read-only — no persist, no mutation, no side effects
  - No Quote creation/modification
  - No Order creation/modification
  - No ProductTemplate mutation
  - No BlueprintDossier mutation
  - No CostEngine formula calculation
  - No Quote -> Order gate change
  - No document snapshot created
  - No final contract generation
  - No email/send action
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.quotes import Quotes
from models.product_templates import Product_templates
from models.product_blueprint_dossier import ProductBlueprintDossier
from services.output_blocks_renderer_service import OutputBlocksRendererService
from services.quote_document_service import QuoteDocumentService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class QuoteOutputCompositionResult:
    """Structured result from quote output composition preview."""

    def __init__(
        self,
        *,
        persisted: bool = False,
        quote_id: Optional[int] = None,
        quote_code: str = "",
        composition_type: str = "quote_output_preview",
        source: Optional[Dict[str, str]] = None,
        template_link: Optional[Dict[str, Any]] = None,
        sections: Optional[List[Dict[str, Any]]] = None,
        commercial_summary: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        blockers: Optional[List[str]] = None,
        trace: Optional[Dict[str, Any]] = None,
    ):
        self.persisted = persisted
        self.quote_id = quote_id
        self.quote_code = quote_code
        self.composition_type = composition_type
        self.source = source or {
            "quote": "read_only",
            "commercial_document": "read_only",
            "output_blocks": "render_preview",
            "product_template": "read_only",
            "blueprint_dossier": "read_only",
        }
        self.template_link = template_link or {"status": "missing"}
        self.sections = sections or []
        self.commercial_summary = commercial_summary or {
            "subtotal": 0,
            "vat": 0,
            "total": 0,
            "currency": "RON",
        }
        self.warnings = warnings or []
        self.blockers = blockers or []
        self.trace = trace or {
            "no_persist": True,
            "changed_entities": [],
            "no_quote_mutation": True,
            "no_order_mutation": True,
            "no_snapshot_created": True,
            "not_client_final": True,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persisted": self.persisted,
            "quote_id": self.quote_id,
            "quote_code": self.quote_code,
            "composition_type": self.composition_type,
            "source": self.source,
            "template_link": self.template_link,
            "sections": self.sections,
            "commercial_summary": self.commercial_summary,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "trace": self.trace,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class QuoteOutputCompositionService:
    """Composes quote output preview — read-only, no persist."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _parse_line_items_root(raw_line_items: Any) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Return (parsed_root, snapshot_data) from quote.line_items JSON."""
        if not raw_line_items:
            return None, None
        try:
            parsed = json.loads(raw_line_items) if isinstance(raw_line_items, str) else raw_line_items
        except (json.JSONDecodeError, TypeError):
            return None, None

        if isinstance(parsed, dict):
            inner_snapshot = parsed.get("line_items")
            if isinstance(inner_snapshot, dict) and (
                "product_definition" in inner_snapshot or "cost_result" in inner_snapshot
            ):
                return parsed, inner_snapshot
            if "product_definition" in parsed or "cost_result" in parsed:
                return parsed, parsed
            return parsed, None

        return None, None

    @classmethod
    def _build_commercial_summary(cls, quote_obj: Any) -> Dict[str, Any]:
        """Mirror quote totals; currency from snapshot (no invented FX)."""
        parsed_root, snapshot_data = cls._parse_line_items_root(quote_obj.line_items)
        source_currency = QuoteDocumentService._extract_snapshot_currency(snapshot_data)
        exchange_rate = QuoteDocumentService._extract_exchange_rate(parsed_root)

        subtotal = float(quote_obj.subtotal or 0)
        vat = float(quote_obj.vat or 0)
        total = float(quote_obj.grand_total or 0)
        currency = source_currency or "RON"

        summary: Dict[str, Any] = {
            "subtotal": subtotal,
            "vat": vat,
            "total": total,
            "currency": currency,
        }

        if exchange_rate is not None and source_currency and source_currency != "RON":
            factor = exchange_rate
            summary["subtotal"] = round(subtotal * factor, 2)
            summary["vat"] = round(vat * factor, 2)
            summary["total"] = round(total * factor, 2)
            summary["currency"] = "RON"
            summary["source_currency"] = source_currency
            summary["exchange_rate"] = exchange_rate
            summary["source_amounts"] = {
                "subtotal": subtotal,
                "vat": vat,
                "total": total,
                "currency": source_currency,
            }

        return summary

    async def compose_preview(self, quote_id: int) -> QuoteOutputCompositionResult:
        """Build a composition preview for the given quote.

        Read-only. No persist. No mutation.
        """
        warnings: List[str] = []
        blockers: List[str] = []

        # --- Load quote read-only ---
        query = select(Quotes).where(Quotes.id == quote_id)
        result = await self.db.execute(query)
        quote_obj = result.scalar_one_or_none()

        if not quote_obj:
            return QuoteOutputCompositionResult(
                quote_id=quote_id,
                blockers=["quote_not_found"],
            )

        quote_code = quote_obj.code or ""
        client_name = quote_obj.client_name or ""

        # --- Extract commercial summary (read-only from quote) ---
        commercial_summary = self._build_commercial_summary(quote_obj)

        # --- Find template link ---
        template_id = None
        template_code = None
        dossier_id = None

        parsed_root, snapshot_data = self._parse_line_items_root(quote_obj.line_items)
        if snapshot_data and isinstance(snapshot_data, dict):
            product_def = snapshot_data.get("product_definition")
            if isinstance(product_def, dict):
                template_code = product_def.get("template_code") or product_def.get("code")

        # Legacy flat line_items array
        if quote_obj.line_items and not template_code:
            try:
                raw_items = quote_obj.line_items
                items = json.loads(raw_items) if isinstance(raw_items, str) else raw_items
                if isinstance(items, list) and items:
                    first_item = items[0] if isinstance(items[0], dict) else {}
                    template_id = first_item.get("template_id")
                    template_code = first_item.get("template_code")
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass

        # --- Build template_link status ---
        template_link: Dict[str, Any]
        template_obj = None
        dossier_obj = None

        if template_id:
            # Load template
            tpl_query = select(Product_templates).where(Product_templates.id == int(template_id))
            tpl_result = await self.db.execute(tpl_query)
            template_obj = tpl_result.scalar_one_or_none()

            if template_obj:
                template_code = template_obj.template_code
                # Load dossier
                dos_query = select(ProductBlueprintDossier).where(
                    ProductBlueprintDossier.template_id == int(template_id)
                )
                dos_result = await self.db.execute(dos_query)
                dossier_obj = dos_result.scalar_one_or_none()

                if dossier_obj:
                    dossier_id = dossier_obj.id
                    template_link = {
                        "status": "linked",
                        "template_id": int(template_id),
                        "template_code": template_code,
                        "dossier_id": dossier_id,
                    }
                else:
                    template_link = {
                        "status": "dossier_missing",
                        "template_id": int(template_id),
                        "template_code": template_code,
                        "dossier_id": None,
                    }
                    blockers.append("dossier_missing_for_linked_template")
            else:
                template_link = {
                    "status": "template_not_found",
                    "template_id": template_id,
                    "template_code": template_code,
                    "dossier_id": None,
                }
                warnings.append("template_referenced_but_not_found")
        else:
            template_link = {"status": "missing"}
            warnings.append("template_link_missing: quote has no linked product template")

        # --- Render output blocks if dossier exists ---
        sections: List[Dict[str, Any]] = []

        if dossier_obj and dossier_obj.output_blocks_json:
            # Build quote context
            quote_context = {
                "quote_id": quote_id,
                "client_name": client_name,
                "quantity": 1,
                "dimensions": {},
                "selected_options": {},
            }

            renderer = OutputBlocksRendererService(self.db)
            render_result = await renderer.render_preview(
                template_id=int(template_id) if template_id else None,
                dossier_id=dossier_id,
                document_type="offer",
                audience="client",
                quote_context=quote_context,
                render_mode="preview",
            )

            # Convert rendered blocks to sections
            for block in render_result.blocks:
                section = {
                    "section_id": block.get("block_id", ""),
                    "title": block.get("title", ""),
                    "source": "output_blocks",
                    "rendered_text": block.get("rendered_text", ""),
                    "warnings": block.get("warnings", []),
                    "blockers": block.get("blockers", []),
                }
                sections.append(section)

            # Propagate renderer warnings/blockers
            warnings.extend(render_result.warnings)
            blockers.extend(render_result.blockers)

        elif dossier_obj and not dossier_obj.output_blocks_json:
            warnings.append("output_blocks_json is empty in dossier")
        elif not dossier_obj and template_id:
            # Already reported as blocker above
            pass

        return QuoteOutputCompositionResult(
            quote_id=quote_id,
            quote_code=quote_code,
            template_link=template_link,
            sections=sections,
            commercial_summary=commercial_summary,
            warnings=warnings,
            blockers=blockers,
        )

    def render_composition_html(self, composition: Dict[str, Any]) -> str:
        """Render composition preview as HTML with mandatory disclaimer.

        This is PREVIEW ONLY — not saved, not sent, not an accepted order snapshot.
        """
        quote_code = composition.get("quote_code", "")
        template_link = composition.get("template_link", {})
        sections = composition.get("sections", [])
        commercial_summary = composition.get("commercial_summary", {})
        warnings = composition.get("warnings", [])
        blockers = composition.get("blockers", [])
        trace = composition.get("trace", {})

        # Build sections HTML
        sections_html = ""
        for section in sections:
            section_warnings = section.get("warnings", [])
            section_blockers = section.get("blockers", [])
            warn_html = ""
            if section_warnings:
                warn_items = "".join(f"<li style='color:#d97706;'>{w}</li>" for w in section_warnings)
                warn_html = f"<ul style='margin:4px 0 0 16px;font-size:12px;'>{warn_items}</ul>"
            if section_blockers:
                block_items = "".join(f"<li style='color:#dc2626;'>{b}</li>" for b in section_blockers)
                warn_html += f"<ul style='margin:4px 0 0 16px;font-size:12px;'>{block_items}</ul>"

            sections_html += f"""
            <div style="margin-bottom:16px;padding:12px 16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;">
                <h3 style="margin:0 0 8px 0;font-size:14px;color:#1e40af;">{section.get('title', 'Section')}</h3>
                <p style="margin:0;font-size:13px;color:#374151;white-space:pre-wrap;">{section.get('rendered_text', '')}</p>
                {warn_html}
            </div>"""

        # Warnings/blockers section
        issues_html = ""
        if warnings or blockers:
            items = ""
            for w in warnings:
                items += f"<li style='color:#d97706;'>⚠️ {w}</li>"
            for b in blockers:
                items += f"<li style='color:#dc2626;'>🚫 {b}</li>"
            issues_html = f"""
            <div style="margin-top:16px;padding:12px 16px;background:#fef2f2;border:1px solid #fca5a5;border-radius:6px;">
                <strong>Warnings / Blockers:</strong>
                <ul style="margin:8px 0 0 16px;">{items}</ul>
            </div>"""

        # Trace section
        trace_html = f"""
        <div style="margin-top:16px;padding:8px 12px;background:#f1f5f9;border:1px solid #cbd5e1;border-radius:4px;font-size:11px;color:#64748b;">
            <strong>Trace:</strong> no_persist={trace.get('no_persist', True)},
            changed_entities={trace.get('changed_entities', [])},
            no_quote_mutation={trace.get('no_quote_mutation', True)},
            no_order_mutation={trace.get('no_order_mutation', True)},
            no_snapshot_created={trace.get('no_snapshot_created', True)}
        </div>"""

        html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Output Composition Preview — {quote_code}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 32px;
            color: #1f2937;
            line-height: 1.5;
        }}
        .disclaimer {{
            background: #fef3c7;
            border: 2px solid #f59e0b;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 24px;
            text-align: center;
            font-weight: 700;
            color: #92400e;
        }}
        .header {{
            border-bottom: 3px solid #2563eb;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .header h1 {{
            font-size: 20px;
            color: #1e40af;
            margin: 0;
        }}
        .meta {{
            font-size: 13px;
            color: #6b7280;
            margin-top: 8px;
        }}
        .commercial {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            padding: 12px 16px;
            margin-top: 16px;
        }}
        .commercial h3 {{
            margin: 0 0 8px 0;
            font-size: 14px;
            color: #1e40af;
        }}
        @media print {{
            body {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="disclaimer">
        PREVIEW ONLY. This output is not saved to the quote, not sent to the client, and not part of any accepted order snapshot.
    </div>

    <div class="header">
        <h1>Output Composition Preview</h1>
        <div class="meta">
            <p><strong>Quote:</strong> {quote_code}</p>
            <p><strong>Template:</strong> {template_link.get('template_code', 'N/A')} (status: {template_link.get('status', 'unknown')})</p>
            {f"<p><strong>Dossier ID:</strong> {template_link.get('dossier_id', 'N/A')}</p>" if template_link.get('dossier_id') else ""}
        </div>
    </div>

    <h2 style="font-size:16px;color:#1e40af;border-bottom:1px solid #dbeafe;padding-bottom:6px;">Rendered Sections</h2>
    {sections_html if sections_html else '<p style="color:#6b7280;font-style:italic;">No output blocks rendered.</p>'}

    <div class="commercial">
        <h3>Commercial Summary (read-only)</h3>
        <p style="margin:4px 0;font-size:13px;">Subtotal: {commercial_summary.get('subtotal', 0):,.2f} {commercial_summary.get('currency', 'RON')}</p>
        <p style="margin:4px 0;font-size:13px;">TVA: {commercial_summary.get('vat', 0):,.2f} {commercial_summary.get('currency', 'RON')}</p>
        <p style="margin:4px 0;font-size:13px;font-weight:700;">Total: {commercial_summary.get('total', 0):,.2f} {commercial_summary.get('currency', 'RON')}</p>
    </div>

    {issues_html}
    {trace_html}

    <div style="margin-top:32px;padding-top:12px;border-top:1px solid #e5e7eb;font-size:11px;color:#9ca3af;text-align:center;">
        PREVIEW ONLY — Not a final document. Not saved. Not sent. Not an order snapshot.
    </div>
</body>
</html>"""
        return html