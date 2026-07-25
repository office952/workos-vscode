"""
BUILD 5 — Quote Commercial Document Service.

Responsibilities:
  - Build client-facing commercial quote document from existing quote/snapshot.
  - Normalize client data.
  - Format product summary with template-specific commercial text blocks.
  - Include totals from quote calculation (never recalculate).
  - Include TVA values from quote data/snapshot.
  - Include readiness summary from quote snapshot.
  - Mark historical missing fields explicitly.
  - Return stable DTO.

Must NOT:
  - Recalculate CostEngine.
  - Recalculate ProductReadiness live.
  - Mutate Quote.
  - Mutate Order.
  - Call SmartBill live.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from services.company_commercial_settings_service import DEFAULT_VAT_PCT
from services.quotes import QuotesService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Commercial terms defaults (backend-owned truth)
# ---------------------------------------------------------------------------
DEFAULT_COMMERCIAL_TERMS = {
    "currency": "RON",  # fallback when snapshot has no cost_result.currency
    "tva_percent": DEFAULT_VAT_PCT,
    "validity_days": 15,
    "payment_terms": "Plata în avans 50%, restul la livrare",
    "delivery_terms": "Livrare la adresa clientului sau ridicare din punct de lucru",
    "warranty_terms": "Garanție 24 luni conform legislației în vigoare",
}


# ---------------------------------------------------------------------------
# Product-specific commercial text blocks (BUILD 4 templates)
# ---------------------------------------------------------------------------
PRODUCT_COMMERCIAL_TEXT: Dict[str, Dict[str, Any]] = {
    "TPL-BANNER-STANDARD": {
        "client_title": "Banner publicitar PVC",
        "short_description": "Banner publicitar imprimat format mare pe material PVC de înaltă calitate.",
        "technical_description": (
            "Imprimare ecosolvent/UV pe PVC banner 440-510g/mp. "
            "Role disponibile: 1100mm, 1350mm, 1600mm. "
            "Rezoluție print: 720-1440 dpi. Rezistență UV: 2-3 ani exterior."
        ),
        "materials_summary": "PVC banner, cerneală ecosolvent/UV, bandă tiv, capse metalice",
        "operations_summary": "Pregătire fișier, imprimare format mare, tăiere, tiv termic, capsare",
        "included_finishes": "Tăiere la dimensiune, verificare calitate print",
        "optional_finishes": "Tiv termic perimetral, capse metalice la distanță configurabilă, sudură banner, margini ranforsate",
        "production_assumptions": (
            "Lățimea de imprimare este limitată de rolele disponibile (1100/1350/1600mm). "
            "Bannerele mai late necesită sudură. Mesh-ul NU se produce intern — se externalizează."
        ),
        "externalization_note": None,
        "limitations": "Dimensiune maximă fără sudură: 1600mm lățime. Mesh externalizat obligatoriu.",
    },
    "TPL-PLEXI-PLATE": {
        "client_title": "Placă plexiglass personalizată",
        "short_description": "Placă din plexiglass tăiată CNC/laser cu finisare profesională.",
        "technical_description": (
            "Plexiglass (PMMA) disponibil în variante: transparent, alb, opal, colorat. "
            "Grosimi: 3mm, 5mm, 10mm. Tăiere laser/CNC cu precizie ±0.1mm. "
            "Finisare muchii: lustruire diamant sau șlefuire mată."
        ),
        "materials_summary": "Placă plexiglass PMMA, distanțiere inox (opțional), vinyl/print (opțional)",
        "operations_summary": "Tăiere laser/CNC, finisare muchii, găurire, aplicare print/vinyl, asamblare distanțiere",
        "included_finishes": "Tăiere la dimensiune, debavurare muchii",
        "optional_finishes": "Lustruire muchii diamant, aplicare vinyl/print UV, distanțiere inox, găurire montaj",
        "production_assumptions": (
            "Grosimea plexiglass-ului influențează timpul de tăiere și costul materialului. "
            "Formele complexe necesită programare CNC suplimentară."
        ),
        "externalization_note": None,
        "limitations": "Dimensiune maximă placă: conform stoc furnizor. Forme complexe pot necesita timp suplimentar.",
    },
    "TPL-VINYL-STICKER": {
        "client_title": "Autocolant / Sticker personalizat",
        "short_description": "Autocolant imprimat pe vinyl autoadeziv de calitate profesională.",
        "technical_description": (
            "Print pe vinyl autoadeziv (calandrat sau turnat). "
            "Laminare UV opțională pentru protecție suplimentară. "
            "Tăiere contur cu plotter. Bandă transfer pentru aplicare ușoară."
        ),
        "materials_summary": "Vinyl autoadeziv, cerneală ecosolvent/UV, laminare UV (opțional), bandă transfer",
        "operations_summary": "Pregătire fișier, imprimare, laminare, tăiere contur, aplicare bandă transfer",
        "included_finishes": "Tăiere la dimensiune, verificare calitate",
        "optional_finishes": "Laminare UV mată/lucioasă, tăiere contur, bandă transfer, aplicare profesională",
        "production_assumptions": (
            "Vinyl calandrat: utilizare interior/exterior până la 3 ani. "
            "Vinyl turnat: utilizare exterior până la 7 ani. "
            "Laminarea prelungește durata de viață cu 1-2 ani."
        ),
        "externalization_note": None,
        "limitations": "Suprafața de aplicare trebuie să fie curată, uscată și netedă. Temperatura minimă aplicare: 10°C.",
    },
    "TPL-LIGHTBOX-STANDARD": {
        "client_title": "Casetă luminoasă cu LED",
        "short_description": "Casetă luminoasă profesională cu iluminare LED și cadru aluminiu.",
        "technical_description": (
            "Cadru aluminiu anodizat, față din plexiglass/policarbonat. "
            "Iluminare cu module LED SMD, surse de alimentare certificate. "
            "Disponibilă single-sided sau double-sided. IP44/IP65 pentru exterior."
        ),
        "materials_summary": "Profil aluminiu, plexiglass/policarbonat, module LED SMD, surse alimentare, panou spate",
        "operations_summary": "Debitare profil, asamblare cadru, montaj LED, cablare electrică, montaj față, testare",
        "included_finishes": "Asamblare completă, testare electrică, verificare uniformitate iluminare",
        "optional_finishes": "Vopsire RAL cadru, față dublu-strat, dimmer, senzor crepuscular",
        "production_assumptions": (
            "Alimentare electrică: 220V AC (sursa include transformator intern). "
            "Consum estimat: 40-80W/mp în funcție de densitatea LED. "
            "Durata de viață LED: >50.000 ore. Necesită priză electrică la locul montajului."
        ),
        "externalization_note": None,
        "limitations": "Necesită alimentare electrică. Montajul exterior necesită autorizație conform legislației locale.",
    },
    "TPL-VOLUMETRIC-LETTERS": {
        "client_title": "Litere volumetrice luminoase",
        "short_description": "Litere volumetrice luminoase realizate conform configurației aprobate.",
        "technical_description": (
            "Litere volumetrice: față plexiglas 3mm PMMA - opal (opțional vinyl/oracal), bordură profil aluminiu, "
            "spate Forex 10 mm. LED montat pe spate. "
            "Premontaj opțional pe structură metalică sau panou ACM casetat (suport, nu spate literă). "
            "Finisare: vopsire RAL, folie sau natural. Șablon montaj."
        ),
        "materials_summary": (
            "Plexi/acrilic față, profil aluminiu lateral, Forex 10 mm spate, "
            "LED pe spate (opțional), surse alimentare, vopsea RAL; premontaj ACM/structură separat"
        ),
        "operations_summary": (
            "Pregătire față, profil lateral, asamblare, montaj LED, vopsire, testare, șablon montaj"
        ),
        "included_finishes": "Asamblare completă, finisare muchii, șablon montaj",
        "optional_finishes": "Iluminare LED (frontlit/backlit/halo), vopsire RAL, folie decorativă",
        "production_assumptions": (
            "Necesită fișier vector (AI/EPS/PDF) pentru contur litere. "
            "Înălțimea minimă recomandată: 150mm. Adâncimea standard: 30-80mm. "
            "Iluminarea necesită alimentare electrică la locul montajului."
        ),
        "externalization_note": None,
        "limitations": "Fișier vector obligatoriu. Litere sub 100mm înălțime nu pot fi iluminate. Montaj exterior necesită autorizație.",
    },
    "TPL-MESH-EXTERNALIZED": {
        "client_title": "Mesh publicitar (producție externalizată)",
        "short_description": "Mesh publicitar perforat — producția este externalizată la furnizor specializat.",
        "technical_description": (
            "Mesh perforat 270g/mp pentru aplicații exterioare de mari dimensiuni. "
            "Imprimare la furnizor extern specializat. "
            "Intern: pregătire fișier, recepție, QC, tiv/capse opțional, ambalare."
        ),
        "materials_summary": "Mesh perforat 270g/mp (furnizor extern), bandă tiv, capse metalice",
        "operations_summary": "Pregătire fișier print, subcontractare producție, recepție QC, tiv, capsare, ambalare",
        "included_finishes": "Pregătire fișier, control calitate la recepție, ambalare",
        "optional_finishes": "Tiv termic perimetral, capse metalice",
        "production_assumptions": (
            "PRODUCȚIE EXTERNALIZATĂ — mesh-ul NU se produce intern. "
            "Termenul de livrare depinde de furnizorul extern (3-7 zile lucrătoare suplimentare). "
            "Confirmarea furnizorului este necesară înainte de lansarea comenzii."
        ),
        "externalization_note": (
            "⚠️ EXTERNALIZARE: Acest produs este realizat de un furnizor extern specializat. "
            "Termenul de producție include timpul de execuție al furnizorului. "
            "Confirmarea disponibilității și a termenului se face la plasarea comenzii."
        ),
        "limitations": "Termen dependent de furnizor extern. Necesită confirmare disponibilitate înainte de comandă.",
    },
}

VOLUMETRIC_CLIENT_LINE_DESCRIPTION = (
    "Litere volumetrice luminoase conform specificațiilor"
)
CLIENT_LINE_SUM_TOLERANCE = 0.02


def _format_validity_display(valid_until: Optional[str], validity_days: int) -> str:
    """Client-facing validity — never show bare em-dash placeholders."""
    days = int(validity_days or DEFAULT_COMMERCIAL_TERMS["validity_days"])
    if valid_until and str(valid_until).strip() and str(valid_until).strip() != "—":
        return f"{days} zile (până la {valid_until})"
    return f"{days} zile de la emitere"


def _is_zero_line_amount(amount: float) -> bool:
    return abs(amount) < 0.005


def _is_internal_client_label(text: str) -> bool:
    label = (text or "").strip().lower()
    if not label:
        return True
    if label.startswith("layer_") or label.startswith("structure"):
        return True
    if "structure id:" in label:
        return True
    if label in {"component", "cost line"}:
        return True
    return False


def _component_client_total(comp: Dict[str, Any]) -> float:
    raw_total = comp.get("total_component_cost")
    if raw_total is not None:
        try:
            return round(float(raw_total), 2)
        except (TypeError, ValueError):
            pass
    material = float(comp.get("material_cost") or 0)
    labor = float(comp.get("labor_cost") or comp.get("operation_cost") or 0)
    return round(material + labor, 2)


def _sum_line_totals(items: List[Dict[str, Any]]) -> float:
    return round(sum(float(item.get("total") or 0) for item in items), 2)


def _single_line_fallback(
    total_before_vat: float,
    template_code: Optional[str],
) -> List[Dict[str, Any]]:
    if template_code == "TPL-VOLUMETRIC-LETTERS":
        description = VOLUMETRIC_CLIENT_LINE_DESCRIPTION
    else:
        description = "Produs realizat conform specificațiilor clientului."
    amount = round(float(total_before_vat or 0), 2)
    return [
        {
            "description": description,
            "quantity": 1,
            "unit_price": amount,
            "total": amount,
            "type": "commercial_summary",
        }
    ]


def _finalize_client_line_items(
    raw_items: List[Dict[str, Any]],
    total_before_vat: float,
    template_code: Optional[str],
) -> List[Dict[str, Any]]:
    """Ensure visible client line totals equal subtotal without VAT."""
    target = round(float(total_before_vat or 0), 2)
    cleaned: List[Dict[str, Any]] = []

    for item in raw_items:
        total = round(float(item.get("total") or 0), 2)
        if _is_zero_line_amount(total):
            continue
        description = str(item.get("description") or "").strip()
        if _is_internal_client_label(description):
            continue
        cleaned.append(
            {
                "description": description,
                "quantity": item.get("quantity", 1),
                "unit_price": round(float(item.get("unit_price") or total), 2),
                "total": total,
                "type": item.get("type", "commercial"),
            }
        )

    if target <= 0 and not cleaned:
        return []

    if not cleaned:
        return _single_line_fallback(target, template_code)

    if abs(_sum_line_totals(cleaned) - target) > CLIENT_LINE_SUM_TOLERANCE:
        return _single_line_fallback(target, template_code)

    return cleaned


def _prepare_client_product_text(
    product_text: Dict[str, Any],
    template_code: Optional[str],
) -> Dict[str, Any]:
    """Sanitize product text blocks for client-facing document output."""
    prepared = dict(product_text)
    if template_code == "TPL-VOLUMETRIC-LETTERS":
        prepared["client_title"] = "Litere volumetrice luminoase"
        prepared["short_description"] = (
            "Litere volumetrice luminoase realizate conform configurației aprobate."
        )
        for key in (
            "technical_description",
            "operations_summary",
            "materials_summary",
            "included_finishes",
            "production_assumptions",
            "limitations",
        ):
            value = prepared.get(key)
            if isinstance(value, str) and value:
                sanitized = value.replace("CNC/laser", "proces specializat")
                sanitized = sanitized.replace("CNC", "debitare")
                sanitized = sanitized.replace("laser", "debitare")
                prepared[key] = sanitized
    return prepared


# ---------------------------------------------------------------------------
# Quote Document Service
# ---------------------------------------------------------------------------
class QuoteDocumentService:
    """Builds client-facing commercial quote documents from existing quote data."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._quotes_service = QuotesService(db)

    async def build_commercial_document(self, quote_id: int) -> Dict[str, Any]:
        """Build a complete commercial document for a quote.

        Returns a stable DTO suitable for client-facing display/export.
        Never recalculates CostEngine or ProductReadiness.
        """
        # 1. Fetch quote from DB
        quote = await self._quotes_service.get_by_id(quote_id)
        if not quote:
            return {"error": "quote_not_found", "quote_id": quote_id}

        # 2. Parse line_items JSON to extract snapshot and breakdown
        snapshot_data = None
        parsed_root: Optional[Dict[str, Any]] = None
        component_breakdown = None
        line_items_parsed = []
        template_code = None

        if quote.line_items:
            try:
                parsed = json.loads(quote.line_items)
                if isinstance(parsed, dict):
                    parsed_root = parsed
                    cb = parsed.get("component_breakdown")
                    if isinstance(cb, list) and len(cb) > 0:
                        component_breakdown = cb
                    snapshot_data = self._resolve_canonical_snapshot(parsed)
                elif isinstance(parsed, list):
                    # Shape A legacy — flat line items
                    line_items_parsed = parsed
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Failed to parse line_items for quote {quote_id}")

        source_currency = self._extract_snapshot_currency(snapshot_data)
        exchange_rate = self._extract_exchange_rate(parsed_root)

        # 3. Extract product info from snapshot
        product_summary = self._extract_product_summary(snapshot_data)
        if snapshot_data and isinstance(snapshot_data, dict):
            pd = snapshot_data.get("product_definition", {})
            template_code = pd.get("template_code") or pd.get("code")

        # 4. Extract readiness from snapshot
        readiness = self._extract_readiness(snapshot_data)

        snapshot_vat_pct = self._resolve_quote_vat_percent(quote, snapshot_data)

        # 5. Build commercial terms (currency + VAT snapshot from quote)
        commercial_terms = self._build_commercial_terms(
            quote,
            source_currency=source_currency,
            exchange_rate=exchange_rate,
            vat_percent=snapshot_vat_pct,
        )

        # 6. Build totals from quote (never recalculate CostEngine — currency/conversion only)
        totals = self._build_document_totals(
            quote,
            commercial_terms=commercial_terms,
            source_currency=source_currency,
            exchange_rate=exchange_rate,
        )
        # Keep commercial terms aligned with presentation totals (EUR unless explicit FX).
        commercial_terms["currency"] = totals.get(
            "currency", commercial_terms.get("currency")
        )
        commercial_terms["validity_display"] = _format_validity_display(
            commercial_terms.get("valid_until"),
            int(commercial_terms.get("validity_days") or DEFAULT_COMMERCIAL_TERMS["validity_days"]),
        )

        # 7. Build product-specific text blocks (client-facing)
        product_text = _prepare_client_product_text(
            self._get_product_commercial_text(template_code),
            template_code,
        )

        # 8. Build line items — must sum to total_before_vat for client presentation
        raw_line_items = self._build_display_line_items(
            snapshot_data, line_items_parsed, component_breakdown
        )
        display_line_items = _finalize_client_line_items(
            raw_line_items,
            totals.get("total_before_vat", 0),
            template_code,
        )

        # 9. Build document sections
        sections = self._build_document_sections(
            product_summary, product_text, display_line_items,
            totals, commercial_terms, readiness
        )

        # 10. Assemble final document
        document = {
            "quote_id": quote.id,
            "quote_code": quote.code,
            "status": quote.status,
            "version": quote.version,
            "client": {
                "name": quote.client_name or "—",
                "contact_person": quote.contact_person,
                "company": quote.client_name,
                "email": None,
                "phone": None,
                "fiscal_id": None,
                "address": None,
            },
            "commercial": commercial_terms,
            "product_summary": product_summary,
            "product_text": product_text,
            "line_items": display_line_items,
            "totals": totals,
            "readiness": readiness,
            "document": {
                "title": "Ofertă comercială",
                "sections": sections,
                "generated_at": datetime.utcnow().isoformat(),
                "source": "backend",
                "format_version": "1.0",
            },
            "metadata": {
                "created_at": quote.created_at.isoformat() if quote.created_at else None,
                "updated_at": quote.updated_at.isoformat() if quote.updated_at else None,
                "valid_until": quote.valid_until,
                "assigned_to": quote.assigned_to,
                "intake_code": quote.intake_code,
                "notes": quote.notes,
            },
        }

        return document

    def _extract_product_summary(self, snapshot_data: Optional[Dict]) -> Dict[str, Any]:
        """Extract product summary from snapshot data."""
        if not snapshot_data or not isinstance(snapshot_data, dict):
            return {
                "product_code": None,
                "product_name": "Produs nespecificat",
                "family": None,
                "description": "—",
                "technical_description": None,
                "externalized": False,
                "template_code": None,
            }

        pd = snapshot_data.get("product_definition", {})
        return {
            "product_code": pd.get("code") or pd.get("template_code"),
            "product_name": pd.get("name") or pd.get("family") or "Produs",
            "family": pd.get("family"),
            "description": pd.get("description") or "—",
            "technical_description": pd.get("technical_description"),
            "externalized": pd.get("externalized", False),
            "template_code": pd.get("template_code") or pd.get("code"),
        }

    def _extract_readiness(self, snapshot_data: Optional[Dict]) -> Dict[str, Any]:
        """Extract readiness info from snapshot. Never recalculate."""
        default = {
            "ready_for_quote": None,
            "overall_status": "unknown",
            "warnings": [],
            "blockers": [],
            "source": "snapshot",
        }

        if not snapshot_data or not isinstance(snapshot_data, dict):
            default["source"] = "unavailable"
            return default

        readiness = snapshot_data.get("readiness_result")
        if not readiness:
            default["source"] = "not_captured"
            return default

        return {
            "ready_for_quote": readiness.get("ready_for_quote"),
            "overall_status": readiness.get("overall_status", "unknown"),
            "warnings": readiness.get("warnings", []),
            "blockers": readiness.get("blockers", []),
            "source": "snapshot",
        }

    def _build_display_line_items(
        self,
        snapshot_data: Optional[Dict],
        legacy_items: List[Dict],
        component_breakdown: Optional[List[Dict]],
    ) -> List[Dict[str, Any]]:
        """Build display-ready line items from available data."""
        items = []

        # If we have component breakdown, derive line items from it
        if component_breakdown and len(component_breakdown) > 0:
            for comp in component_breakdown:
                line_total = _component_client_total(comp)
                description = comp.get("name") or comp.get("type") or "Component"
                items.append({
                    "description": description,
                    "product_code": comp.get("component_id", ""),
                    "quantity": 1,
                    "unit_price": line_total,
                    "total": line_total,
                    "type": "component",
                })
            return items

        # If we have snapshot with cost_result breakdown
        if snapshot_data and isinstance(snapshot_data, dict):
            cost_result = snapshot_data.get("cost_result", {})
            breakdown = cost_result.get("breakdown", [])
            if isinstance(breakdown, list) and len(breakdown) > 0:
                for bl in breakdown:
                    items.append({
                        "description": bl.get("name") or bl.get("type") or "Cost line",
                        "product_code": bl.get("type", ""),
                        "quantity": bl.get("quantity", 1),
                        "unit_price": bl.get("unit_cost", 0),
                        "total": bl.get("total", 0),
                        "type": "cost_breakdown",
                    })
                return items

        # Legacy flat items
        if legacy_items:
            for item in legacy_items:
                items.append({
                    "description": item.get("description", "—"),
                    "product_code": item.get("productCode", ""),
                    "quantity": item.get("quantity", 1),
                    "unit_price": item.get("unit_price") or item.get("unitPrice", 0),
                    "total": item.get("total", 0),
                    "type": "legacy",
                })
            return items

        return items

    @staticmethod
    def _normalize_currency_code(value: Any) -> Optional[str]:
        if value is None:
            return None
        code = str(value).strip().upper()
        if code == "LEI":
            return "RON"
        return code if code else None

    @staticmethod
    def _is_canonical_snapshot(obj: Any) -> bool:
        """Recognize quote snapshot payloads (Shape A/B/C and partial historical)."""
        if not obj or not isinstance(obj, dict):
            return False
        if isinstance(obj.get("product_definition"), dict):
            return True
        if "readiness_result" in obj:
            return True
        return "cost_result" in obj or "pricing" in obj or "price" in obj

    @classmethod
    def _resolve_canonical_snapshot(cls, parsed: Any) -> Optional[Dict[str, Any]]:
        """Resolve priced snapshot from Shape A/B/C line_items JSON."""
        if not parsed or not isinstance(parsed, dict):
            return None
        if cls._is_canonical_snapshot(parsed):
            return parsed
        inner = parsed.get("line_items")
        if isinstance(inner, dict) and cls._is_canonical_snapshot(inner):
            return inner
        return None

    @classmethod
    def _extract_snapshot_currency(cls, snapshot_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Read calculation currency from priced quote snapshot (cost_result.currency)."""
        if not snapshot_data or not isinstance(snapshot_data, dict):
            return None
        cost_result = snapshot_data.get("cost_result")
        if isinstance(cost_result, dict):
            currency = cls._normalize_currency_code(cost_result.get("currency"))
            if currency:
                return currency
        product_definition = snapshot_data.get("product_definition")
        if isinstance(product_definition, dict):
            pricing_context = product_definition.get("pricing_context")
            if isinstance(pricing_context, dict):
                currency = cls._normalize_currency_code(pricing_context.get("currency"))
                if currency:
                    return currency
        return None

    @staticmethod
    def _extract_exchange_rate(parsed_root: Optional[Dict[str, Any]]) -> Optional[float]:
        """Optional FX snapshot on quote wrapper — never invented."""
        if not parsed_root or not isinstance(parsed_root, dict):
            return None
        for key in ("exchange_rate", "fx_rate", "eur_ron_rate"):
            raw = parsed_root.get(key)
            if isinstance(raw, (int, float)) and not isinstance(raw, bool):
                rate = float(raw)
                if rate > 0:
                    return rate
        return None

    def _build_document_totals(
        self,
        quote: Any,
        *,
        commercial_terms: Dict[str, Any],
        source_currency: Optional[str],
        exchange_rate: Optional[float],
    ) -> Dict[str, Any]:
        """Totals mirror quote columns; convert only when explicit exchange_rate exists."""
        subtotal = float(quote.subtotal or 0)
        discount = float(quote.discount or 0)
        discount_pct = float(quote.discount_pct or 0)
        total_before_vat = float(quote.total_before_vat or 0)
        raw_tva = commercial_terms.get("tva_percent")
        tva_percent = (
            float(raw_tva)
            if raw_tva is not None
            else float(DEFAULT_VAT_PCT)
        )
        tva = round(total_before_vat * (tva_percent / 100), 2)
        grand_total = float(quote.grand_total or 0)
        margin_pct = float(quote.margin_pct or 0)

        presentation_currency = commercial_terms.get("currency") or DEFAULT_COMMERCIAL_TERMS["currency"]
        source_amounts: Optional[Dict[str, float]] = None

        src = source_currency or presentation_currency
        if exchange_rate is not None and src and src != "RON":
            presentation_currency = "RON"
            factor = exchange_rate
            subtotal = round(subtotal * factor, 2)
            discount = round(discount * factor, 2)
            total_before_vat = round(total_before_vat * factor, 2)
            tva = round(tva * factor, 2)
            grand_total = round(grand_total * factor, 2)
            source_amounts = {
                "subtotal": float(quote.subtotal or 0),
                "discount": float(quote.discount or 0),
                "total_before_vat": float(quote.total_before_vat or 0),
                "tva": round(
                    float(quote.total_before_vat or 0) * (tva_percent / 100), 2
                ),
                "grand_total": float(quote.grand_total or 0),
                "currency": src,
            }
            commercial_terms["source_currency"] = src
            commercial_terms["exchange_rate"] = exchange_rate

        totals: Dict[str, Any] = {
            "subtotal": subtotal,
            "discount": discount,
            "discount_pct": discount_pct,
            "total_before_vat": total_before_vat,
            "tva": tva,
            "grand_total": grand_total,
            "margin_pct": margin_pct,
            "currency": presentation_currency,
        }
        if source_amounts is not None:
            totals["source_amounts"] = source_amounts
        return totals

    @staticmethod
    def _resolve_quote_vat_percent(
        quote: Any, snapshot_data: Optional[Dict[str, Any]]
    ) -> float:
        """VAT % from quote snapshot — never Settings live."""
        if snapshot_data and isinstance(snapshot_data, dict):
            pricing = snapshot_data.get("pricing")
            if isinstance(pricing, dict) and pricing.get("vat_pct") is not None:
                return float(pricing["vat_pct"])
        raw = getattr(quote, "vat", None)
        if raw is not None:
            return float(raw)
        return float(DEFAULT_VAT_PCT)

    def _build_commercial_terms(
        self,
        quote: Any,
        *,
        source_currency: Optional[str] = None,
        exchange_rate: Optional[float] = None,
        vat_percent: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Build commercial terms from quote data + defaults."""
        terms = dict(DEFAULT_COMMERCIAL_TERMS)

        if vat_percent is not None:
            terms["tva_percent"] = float(vat_percent)

        if source_currency:
            terms["currency"] = source_currency
        if exchange_rate is not None and source_currency and source_currency != "RON":
            terms["currency"] = "RON"
            terms["source_currency"] = source_currency
            terms["exchange_rate"] = exchange_rate

        # Override validity from quote if available
        if quote.valid_until:
            try:
                valid_date = datetime.strptime(quote.valid_until, "%Y-%m-%d")
                created = quote.created_at or datetime.utcnow()
                if isinstance(created, str):
                    created = datetime.fromisoformat(created)
                delta = (valid_date - created).days
                if delta > 0:
                    terms["validity_days"] = delta
            except (ValueError, TypeError):
                pass

        terms["valid_until"] = quote.valid_until
        return terms

    def _get_product_commercial_text(self, template_code: Optional[str]) -> Dict[str, Any]:
        """Get product-specific commercial text blocks."""
        if template_code and template_code in PRODUCT_COMMERCIAL_TEXT:
            return PRODUCT_COMMERCIAL_TEXT[template_code]

        # Return generic/empty text for unknown templates
        return {
            "client_title": "Produs personalizat",
            "short_description": "Produs realizat conform specificațiilor clientului.",
            "technical_description": None,
            "materials_summary": None,
            "operations_summary": None,
            "included_finishes": None,
            "optional_finishes": None,
            "production_assumptions": None,
            "externalization_note": None,
            "limitations": None,
        }

    def _build_document_sections(
        self,
        product_summary: Dict,
        product_text: Dict,
        line_items: List[Dict],
        totals: Dict,
        commercial_terms: Dict,
        readiness: Dict,
    ) -> List[Dict[str, Any]]:
        """Build ordered document sections for rendering."""
        sections = []

        # Section 1: Product description
        sections.append({
            "id": "product_description",
            "title": "Descriere produs",
            "content": {
                "title": product_text.get("client_title") or product_summary.get("product_name"),
                "description": product_text.get("short_description") or product_summary.get("description"),
                "technical": product_text.get("technical_description"),
            },
        })

        # Section 2: Technical specifications
        if product_text.get("materials_summary") or product_text.get("operations_summary"):
            sections.append({
                "id": "technical_specs",
                "title": "Specificații tehnice",
                "content": {
                    "materials": product_text.get("materials_summary"),
                    "operations": product_text.get("operations_summary"),
                    "included_finishes": product_text.get("included_finishes"),
                    "optional_finishes": product_text.get("optional_finishes"),
                },
            })

        # Section 3: Line items / pricing
        sections.append({
            "id": "line_items",
            "title": "Detaliere preț",
            "content": {
                "items": line_items,
                "totals": totals,
            },
        })

        # Section 4: Commercial terms
        sections.append({
            "id": "commercial_terms",
            "title": "Condiții comerciale",
            "content": {
                "validity": commercial_terms.get("validity_display")
                or _format_validity_display(
                    commercial_terms.get("valid_until"),
                    int(commercial_terms.get("validity_days") or DEFAULT_COMMERCIAL_TERMS["validity_days"]),
                ),
                "valid_until": commercial_terms.get("valid_until"),
                "payment_terms": commercial_terms.get("payment_terms"),
                "delivery_terms": commercial_terms.get("delivery_terms"),
                "warranty_terms": commercial_terms.get("warranty_terms"),
                "currency": commercial_terms.get("currency"),
                "source_currency": commercial_terms.get("source_currency"),
                "exchange_rate": commercial_terms.get("exchange_rate"),
                "tva_percent": commercial_terms.get("tva_percent"),
            },
        })

        # Section 5: Production assumptions
        if product_text.get("production_assumptions") or product_text.get("limitations"):
            sections.append({
                "id": "production_notes",
                "title": "Observații producție",
                "content": {
                    "assumptions": product_text.get("production_assumptions"),
                    "limitations": product_text.get("limitations"),
                },
            })

        # Section 6: Externalization (if applicable)
        if product_text.get("externalization_note") or product_summary.get("externalized"):
            sections.append({
                "id": "externalization",
                "title": "Externalizare",
                "content": {
                    "note": product_text.get("externalization_note")
                    or "Acest produs include componente realizate de furnizori externi.",
                    "externalized": True,
                },
            })

        # Section 7: Readiness warnings (internal, shown as production notes)
        if readiness.get("warnings") or readiness.get("blockers"):
            sections.append({
                "id": "readiness_notes",
                "title": "Note pregătire producție",
                "content": {
                    "warnings": readiness.get("warnings", []),
                    "blockers": readiness.get("blockers", []),
                    "status": readiness.get("overall_status"),
                },
            })

        return sections