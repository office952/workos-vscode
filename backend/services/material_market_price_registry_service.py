"""MATERIAL_MARKET_PRICE_REGISTRY_V1 — Inventory purchase truth read-model.

No invented prices. No Alembic. AI freshness thresholds are policy only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_material_price_history import Inventory_material_price_history
from models.inventory_materials import Inventory_materials
from models.product_templates import Product_templates
from models.suppliers import Suppliers
from schemas.material_market_price_registry import (
    MaterialMarketPriceRecord,
    MaterialMarketPriceRegistryResponse,
    MaterialMarketPriceSummary,
    MaterialPriceHistoryPoint,
    MaterialPriceNormalization,
)
from services.product_readiness_service import ProductReadinessService

SOURCE_PRECEDENCE = [
    "MEASURED_LANDED_COST",
    "PURCHASE_INVOICE",
    "SUPPLIER_OFFER",
    "OWNER_CONFIRMED",
    "SUPPLIER_CATALOG",
    "TEMPORARY_AI_FALLBACK",
    "LEGACY",
    "MISSING",
]

# Freshness thresholds — AI_DECISION policy constants (not price truth).
FRESHNESS_REVIEW_DAYS: dict[str, int] = {
    "SUPPLIER_OFFER": 30,
    "PURCHASE_INVOICE": 60,
    "SUPPLIER_CATALOG": 90,
    "OWNER_CONFIRMED": 90,
    "MEASURED_LANDED_COST": 90,
    "LEGACY": 90,
    "TEMPORARY_AI_FALLBACK": 14,
}

CRITICAL_VL_GAPS = frozenset(
    {
        "MAT-ADEZIV-CANT-LITERE",
        "MAT-CABLU-MYYUP-2X075",
        "MAT-CABLU-MYYUP-2X15",
        "SVC-LAMINATION-SERVICE",
    }
)


def _iso(dt: Any) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def classify_source_type(row: Inventory_materials) -> str:
    """Deterministic source classification from existing Inventory fields."""
    if row.unit_cost is None:
        return "MISSING"
    blob = " ".join(
        str(x or "").lower()
        for x in (
            row.source_name,
            row.source_notes,
            row.source_review_status,
            row.source_url,
        )
    )
    if any(t in blob for t in ("landed", "measured", "achizitie masurata")):
        return "MEASURED_LANDED_COST"
    if any(t in blob for t in ("invoice", "factura", "oc ", "purchase order", "comanda")):
        return "PURCHASE_INVOICE"
    if any(t in blob for t in ("offer", "oferta", "quotation", "cotatie")):
        return "SUPPLIER_OFFER"
    review = str(row.source_review_status or "").strip().lower()
    if review in {"owner_confirmed", "confirmed", "verified"}:
        return "OWNER_CONFIRMED"
    if any(t in blob for t in ("catalog", "listino", "supplier catalog")):
        return "SUPPLIER_CATALOG"
    if "ai" in blob and "fallback" in blob:
        return "TEMPORARY_AI_FALLBACK"
    if row.source_name or row.source_checked_at or row.supplier_id or row.supplier:
        return "OWNER_CONFIRMED" if review else "LEGACY"
    return "LEGACY"


def compute_freshness(
    *,
    source_type: str,
    source_date: Optional[datetime],
) -> tuple[str, Optional[str]]:
    if source_type == "MISSING":
        return "UNKNOWN_DATE", "Fără preț — freshness nu se aplică."
    if source_date is None:
        return "UNKNOWN_DATE", "Dată sursă necunoscută — review necesar."
    ref = source_date
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    age_days = (_now() - ref).total_seconds() / 86400.0
    review_after = FRESHNESS_REVIEW_DAYS.get(source_type, 90)
    policy = (
        f"Politică freshness AI_DECISION (configurabilă): review după {review_after} zile "
        f"pentru {source_type}. Nu este preț."
    )
    if age_days <= review_after * 0.7:
        return "CURRENT", policy
    if age_days <= review_after:
        return "REVIEW_SOON", policy
    if age_days <= review_after * 2:
        return "STALE", policy
    return "EXPIRED", policy


def build_normalization(row: Inventory_materials) -> MaterialPriceNormalization:
    raw_unit = (row.unit or "").strip() or None
    raw_price = float(row.unit_cost) if row.unit_cost is not None else None
    currency = row.currency
    w = row.usable_width or row.sheet_width
    h = row.usable_height or row.sheet_height
    unit_l = (raw_unit or "").lower()
    area = None
    if w and h and float(w) > 0 and float(h) > 0:
        # Prefer mm; if values look like meters (< 50), treat as m.
        wf, hf = float(w), float(h)
        if wf > 50 and hf > 50:
            area = round((wf / 1000.0) * (hf / 1000.0), 6)
            dim_label = f"{wf:.0f} × {hf:.0f} mm"
        else:
            area = round(wf * hf, 6)
            dim_label = f"{wf} × {hf} m"
    else:
        dim_label = None

    # Already normalized units — identity
    if unit_l in {"mp", "m2", "m²"}:
        formula = None
        if area and raw_price is not None:
            formula = (
                f"{dim_label} = {area} mp · cost declarat {raw_price} {currency or ''}/mp"
                if dim_label
                else f"{raw_price} {currency or ''}/mp (unitate deja normalizată)"
            )
        return MaterialPriceNormalization(
            raw_unit=raw_unit,
            raw_price=raw_price,
            currency=currency,
            normalized_unit="mp",
            normalized_price=raw_price,
            sheet_width_mm=float(w) if w and float(w) > 50 else None,
            sheet_height_mm=float(h) if h and float(h) > 50 else None,
            sheet_area_m2=area,
            formula_display=formula or (f"{raw_price} {currency or ''}/mp" if raw_price is not None else None),
            conversion_applied=False,
            note_ro="Unitatea inventar este deja mp — fără conversie.",
        )

    if unit_l in {"ml", "m", "buc", "kg", "set", "modul", "role"}:
        return MaterialPriceNormalization(
            raw_unit=raw_unit,
            raw_price=raw_price,
            currency=currency,
            normalized_unit=raw_unit,
            normalized_price=raw_price,
            formula_display=(
                f"{raw_price} {currency or ''}/{raw_unit}" if raw_price is not None else None
            ),
            conversion_applied=False,
            note_ro="Unitate canonică — fără conversie sheet→mp.",
        )

    # sheet / placa → mp when dimensions known
    if unit_l in {"sheet", "placa", "placă", "pcs", "buc_placa"} and area and raw_price is not None:
        norm = round(float(raw_price) / area, 4)
        formula = (
            f"{dim_label} = {area} mp\n"
            f"{raw_price} {currency or ''}/sheet ÷ {area} mp = {norm} {currency or ''}/mp"
        )
        return MaterialPriceNormalization(
            raw_unit=raw_unit,
            raw_price=raw_price,
            currency=currency,
            normalized_unit="mp",
            normalized_price=norm,
            sheet_width_mm=float(w) if w else None,
            sheet_height_mm=float(h) if h else None,
            sheet_area_m2=area,
            formula_display=formula,
            conversion_applied=True,
            note_ro="Conversie sheet→mp din dimensiuni Inventory.",
        )

    return MaterialPriceNormalization(
        raw_unit=raw_unit,
        raw_price=raw_price,
        currency=currency,
        normalized_unit=raw_unit,
        normalized_price=raw_price,
        sheet_area_m2=area,
        formula_display=(
            f"{raw_price} {currency or ''}/{raw_unit or '?'}" if raw_price is not None else None
        ),
        conversion_applied=False,
        note_ro=(
            "Conversie nedeterminată — dimensiuni lipsă sau unitate necunoscută."
            if raw_price is not None and unit_l in {"sheet", "placa", "placă"}
            else None
        ),
    )


def _variant_label(row: Inventory_materials) -> Optional[str]:
    parts = []
    if row.sheet_thickness is not None:
        parts.append(f"{row.sheet_thickness}{row.sheet_thickness_unit or 'mm'}")
    if row.subcategory:
        parts.append(str(row.subcategory))
    return " / ".join(parts) if parts else None


class MaterialMarketPriceRegistryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _template_material_usage(self) -> dict[str, list[str]]:
        result = await self.db.execute(select(Product_templates))
        usage: dict[str, list[str]] = {}
        for tpl in result.scalars().all():
            code = str(getattr(tpl, "template_code", "") or "")
            if not code:
                continue
            flat = ProductReadinessService._parse_json(
                getattr(tpl, "required_materials_json", None)
            )
            components = ProductReadinessService._parse_json(
                getattr(tpl, "components_json", None)
            )
            mats = ProductReadinessService._extract_material_codes(flat)
            mats |= ProductReadinessService._extract_material_codes_from_components(
                components
            )
            for m in mats:
                usage.setdefault(str(m), []).append(code)
        return usage

    async def build_registry(
        self,
        *,
        material_code: Optional[str] = None,
        include_history: bool = True,
        active_templates_only: bool = False,
    ) -> MaterialMarketPriceRegistryResponse:
        usage = await self._template_material_usage()
        q = select(Inventory_materials)
        if material_code:
            q = q.where(Inventory_materials.code == material_code)
        rows = list((await self.db.execute(q)).scalars().all())

        supplier_ids = {r.supplier_id for r in rows if r.supplier_id}
        suppliers: dict[int, Suppliers] = {}
        if supplier_ids:
            srows = (
                await self.db.execute(
                    select(Suppliers).where(Suppliers.id.in_(sorted(supplier_ids)))
                )
            ).scalars().all()
            suppliers = {int(s.id): s for s in srows}

        history_by_material: dict[int, list[Inventory_material_price_history]] = {}
        if include_history and rows:
            ids = [int(r.id) for r in rows]
            hrows = (
                await self.db.execute(
                    select(Inventory_material_price_history)
                    .where(Inventory_material_price_history.material_id.in_(ids))
                    .order_by(Inventory_material_price_history.changed_at.desc())
                )
            ).scalars().all()
            for h in hrows:
                history_by_material.setdefault(int(h.material_id), []).append(h)

        items: list[MaterialMarketPriceRecord] = []
        critical_missing: list[str] = []
        warnings: list[str] = []

        for row in sorted(rows, key=lambda r: str(r.code or "")):
            if active_templates_only and str(row.code) not in usage:
                continue
            source_type = classify_source_type(row)
            source_dt = row.source_checked_at or row.valid_from
            freshness, freshness_policy = compute_freshness(
                source_type=source_type, source_date=source_dt
            )
            norm = build_normalization(row)
            supplier = suppliers.get(int(row.supplier_id)) if row.supplier_id else None
            templates = sorted(set(usage.get(str(row.code), [])))
            missing = row.unit_cost is None or source_type == "MISSING"
            blocker = "Pret material lipsa" if missing else None
            if missing and (
                str(row.code) in CRITICAL_VL_GAPS or any("VOLUMETRIC" in t for t in templates)
            ):
                if str(row.code) not in critical_missing:
                    critical_missing.append(str(row.code))

            hist_pts: list[MaterialPriceHistoryPoint] = []
            for h in history_by_material.get(int(row.id), [])[:12]:
                hist_pts.append(
                    MaterialPriceHistoryPoint(
                        history_id=int(h.id),
                        unit_cost=h.unit_cost,
                        currency=h.currency,
                        vat_percent=h.vat_percent,
                        valid_from=_iso(h.valid_from),
                        changed_at=_iso(h.changed_at),
                        changed_by=h.changed_by,
                        change_reason=h.change_reason,
                        snapshot_source=h.snapshot_source,
                    )
                )

            confidence: str = "medium"
            if source_type in {"MEASURED_LANDED_COST", "PURCHASE_INVOICE", "OWNER_CONFIRMED"}:
                confidence = "high"
            elif missing or freshness in {"STALE", "EXPIRED", "UNKNOWN_DATE"}:
                confidence = "low"

            warn = None
            if freshness in {"STALE", "EXPIRED"}:
                warn = f"Sursa {freshness.lower()}"
            if norm.note_ro and "nedeterminată" in norm.note_ro:
                warn = (warn + "; " if warn else "") + norm.note_ro

            items.append(
                MaterialMarketPriceRecord(
                    material_code=str(row.code),
                    display_name=str(row.name or row.code),
                    category=row.category,
                    subcategory=row.subcategory,
                    variant=_variant_label(row),
                    inventory_status=row.status,
                    stock_current=row.stock_current,
                    supplier_id=int(row.supplier_id) if row.supplier_id else None,
                    supplier_name=(
                        str(supplier.name)
                        if supplier is not None
                        else (row.supplier or None)
                    ),
                    supplier_sku=None,
                    source_type=source_type,  # type: ignore[arg-type]
                    source_name=row.source_name,
                    source_url=row.source_url,
                    source_date=_iso(source_dt),
                    source_notes=row.source_notes,
                    source_review_status=row.source_review_status,
                    effective_from=_iso(row.valid_from),
                    raw_unit=row.unit,
                    raw_price=float(row.unit_cost) if row.unit_cost is not None else None,
                    currency=row.currency,
                    vat_percent=row.vat_percent,
                    vat_included=False,
                    landed_cost=None,
                    normalization=norm,
                    preferred=True,
                    freshness=freshness,  # type: ignore[arg-type]
                    freshness_policy_ro=freshness_policy,
                    confidence=confidence,  # type: ignore[arg-type]
                    temporary_ai_fallback=source_type == "TEMPORARY_AI_FALLBACK",
                    canonical=source_type != "TEMPORARY_AI_FALLBACK" and not missing,
                    blocker=blocker,
                    warning=warn,
                    active_templates=templates,
                    history=hist_pts,
                    inventory_href=f"/inventory?material={row.code}",
                    pricing_href="/inventory/pricing",
                )
            )

        summary = MaterialMarketPriceSummary(
            total=len(items),
            priced=sum(1 for i in items if i.raw_price is not None),
            missing=sum(1 for i in items if i.raw_price is None),
            stale=sum(1 for i in items if i.freshness in {"STALE", "EXPIRED"}),
            review_soon=sum(1 for i in items if i.freshness == "REVIEW_SOON"),
            unknown_date=sum(1 for i in items if i.freshness == "UNKNOWN_DATE"),
            with_supplier=sum(1 for i in items if i.supplier_id or i.supplier_name),
            active_template_critical_missing=len(critical_missing),
            temporary_ai_fallback=sum(1 for i in items if i.temporary_ai_fallback),
        )
        if critical_missing:
            warnings.append(
                "Materiale active fără preț de achiziție: " + ", ".join(critical_missing)
            )
        warnings.append(
            "V1 nu creează prețuri AI pentru materiale. Fallback temporar rezervat, neaplicat automat."
        )

        return MaterialMarketPriceRegistryResponse(
            source_precedence=list(SOURCE_PRECEDENCE),
            freshness_policy={
                "kind": "AI_DECISION",
                "configurable": True,
                "canonical_price": False,
                "review_after_days": dict(FRESHNESS_REVIEW_DAYS),
            },
            summary=summary,
            items=items,
            critical_missing=critical_missing,
            warnings=warnings,
        )

    async def get_material(self, material_code: str) -> Optional[MaterialMarketPriceRecord]:
        reg = await self.build_registry(material_code=material_code, include_history=True)
        return reg.items[0] if reg.items else None
