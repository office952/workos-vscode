from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.company_commercial_settings_service import get_default_vat_pct

from models.inventory_materials import Inventory_materials
from services.commercial_markup_policy_service import resolve_applicable_markup_policy
from services.inventory_materials_governance import (
    INTELLIGENCE_POLICY,
    get_canonical_category,
    infer_recommended_subcategory,
)


VALID_SOURCE_REVIEW_OK = {"reviewed", "accepted_override"}


def _issue(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def _is_source_stale(source_checked_at: Optional[datetime], stale_days: int) -> bool:
    if source_checked_at is None:
        return True
    now = datetime.now(source_checked_at.tzinfo) if source_checked_at.tzinfo else datetime.now()
    return (now - source_checked_at) > timedelta(days=stale_days)


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class PricingPreviewComputation:
    material_code: str
    material_name: Optional[str]
    material_status: Optional[str]
    quantity: float
    unit: Optional[str]
    currency: Optional[str]
    unit_cost: Optional[float]
    base_cost_total: Optional[float]
    applied_markup_policy: Optional[Dict[str, Any]]
    markup_amount: Optional[float]
    commercial_unit_price_ex_vat: Optional[float]
    commercial_total_ex_vat: Optional[float]
    vat_percent: Optional[float]
    vat_amount: Optional[float]
    commercial_total_inc_vat: Optional[float]
    warnings: List[Dict[str, str]]
    blockers: List[Dict[str, str]]
    no_write_guarantee: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_code": self.material_code,
            "material_name": self.material_name,
            "material_status": self.material_status,
            "quantity": self.quantity,
            "unit": self.unit,
            "currency": self.currency,
            "unit_cost": self.unit_cost,
            "base_cost_total": self.base_cost_total,
            "applied_markup_policy": self.applied_markup_policy,
            "markup_amount": self.markup_amount,
            "commercial_unit_price_ex_vat": self.commercial_unit_price_ex_vat,
            "commercial_total_ex_vat": self.commercial_total_ex_vat,
            "vat_percent": self.vat_percent,
            "vat_amount": self.vat_amount,
            "commercial_total_inc_vat": self.commercial_total_inc_vat,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "no_write_guarantee": self.no_write_guarantee,
        }


class ProductSystemPricingPreviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def preview(
        self,
        *,
        material_code: str,
        quantity: float = 1.0,
        vat_percent: Optional[float] = None,
        include_vat: bool = True,
        requested_scope: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        row = (
            await self.db.execute(
                select(Inventory_materials).where(Inventory_materials.code == material_code)
            )
        ).scalar_one_or_none()

        warnings: List[Dict[str, str]] = []
        blockers: List[Dict[str, str]] = []

        if row is None:
            blockers.append(_issue("material_not_found", f"inventory_material '{material_code}' not found"))
            return PricingPreviewComputation(
                material_code=material_code,
                material_name=None,
                material_status=None,
                quantity=quantity,
                unit=None,
                currency=None,
                unit_cost=None,
                base_cost_total=None,
                applied_markup_policy=None,
                markup_amount=None,
                commercial_unit_price_ex_vat=None,
                commercial_total_ex_vat=None,
                vat_percent=None,
                vat_amount=None,
                commercial_total_inc_vat=None,
                warnings=warnings,
                blockers=blockers,
            ).to_dict()

        qty = _safe_float(quantity)
        if qty is None or qty <= 0:
            blockers.append(_issue("quantity_invalid", "quantity must be greater than zero"))
            qty = float(quantity) if _safe_float(quantity) is not None else 0.0

        status = (row.status or "").strip().lower()
        if status == "archived":
            warnings.append(_issue("material_archived", "Material is archived"))
        elif status != "active":
            warnings.append(_issue("material_inactive", "Material is not active"))

        unit = (row.unit or "").strip() or None
        if unit is None:
            warnings.append(_issue("material_missing_unit", "Material is missing unit"))

        unit_cost = _safe_float(row.unit_cost)
        if unit_cost is None or unit_cost <= 0:
            blockers.append(_issue("material_missing_unit_cost", "Material is missing unit_cost"))

        currency = (row.currency or "").strip() or None
        if currency is None:
            warnings.append(_issue("material_missing_currency", "Material is missing currency"))

        canonical_category = get_canonical_category(row.category)
        if row.category and canonical_category != row.category:
            warnings.append(
                _issue(
                    "category_not_canonical",
                    f"Category '{row.category}' normalizes to '{canonical_category or 'unmapped'}'",
                )
            )
        if not str(row.subcategory or "").strip():
            warnings.append(_issue("subcategory_missing", "Material is missing subcategory"))
        else:
            suggested_subcategory = infer_recommended_subcategory(
                code=row.code,
                name=row.name,
                category=row.category,
                canonical_category=canonical_category,
            )
            if suggested_subcategory and row.subcategory != suggested_subcategory:
                warnings.append(
                    _issue(
                        "subcategory_not_canonical",
                        f"Subcategory '{row.subcategory}' differs from recommended '{suggested_subcategory}'",
                    )
                )

        source_status = (row.source_review_status or "missing").strip().lower()
        if source_status not in VALID_SOURCE_REVIEW_OK:
            warnings.append(
                _issue("source_review_missing", f"Source review status is '{source_status}'")
            )
        if _is_source_stale(row.source_checked_at, INTELLIGENCE_POLICY["stale_source_days"]):
            warnings.append(_issue("source_review_stale", "Source review is stale"))

        if warnings and any(code in {"category_not_canonical", "subcategory_missing", "source_review_missing", "source_review_stale"} for code in [warning["code"] for warning in warnings]):
            warnings.append(
                _issue(
                    "productsystem_gate_not_ready",
                    "ProductSystem gate is informational-only and not ready for this material",
                )
            )

        # Company Settings is canonical for quote VAT; ignore request vat_percent.
        resolved_vat_percent = await get_default_vat_pct(self.db)
        if resolved_vat_percent is None:
            resolved_vat_percent = _safe_float(row.vat_percent)
            if resolved_vat_percent is None:
                warnings.append(_issue("vat_missing", "VAT percent is missing"))

        policy = await resolve_applicable_markup_policy(self.db, material=row)
        if policy is None:
            warnings.append(_issue("no_markup_policy", "No active commercial markup policy matches this material"))

        base_cost_total = unit_cost * qty if unit_cost is not None else None

        markup_amount = None
        commercial_unit_price_ex_vat = None
        commercial_total_ex_vat = None
        applied_policy: Optional[Dict[str, Any]] = None

        if unit_cost is not None:
            markup_amount = 0.0
            if policy is not None:
                if policy.markup_type in {"percent", "hybrid"}:
                    markup_amount += unit_cost * float(policy.markup_percent or 0.0) / 100.0
                if policy.markup_type in {"fixed", "hybrid"}:
                    markup_amount += float(policy.markup_fixed or 0.0)
                if policy.min_margin_amount is not None:
                    markup_amount = max(markup_amount, float(policy.min_margin_amount))
                if policy.currency and currency and policy.currency != currency:
                    warnings.append(
                        _issue(
                            "currency_mismatch",
                            f"Policy currency '{policy.currency}' differs from material currency '{currency}'",
                        )
                    )

                applied_policy = {
                    "policy_id": policy.id,
                    "scope_type": policy.scope_type,
                    "scope_value": policy.scope_value,
                    "markup_type": policy.markup_type,
                    "markup_percent": policy.markup_percent,
                    "markup_fixed": policy.markup_fixed,
                    "priority": policy.priority,
                    "currency": policy.currency,
                    "rounding_mode": policy.rounding_mode,
                    "applies_to": policy.applies_to,
                    "status": policy.status,
                }
            commercial_unit_price_ex_vat = unit_cost + markup_amount
            commercial_total_ex_vat = commercial_unit_price_ex_vat * qty

        vat_amount = None
        commercial_total_inc_vat = None
        if commercial_total_ex_vat is not None:
            if include_vat and resolved_vat_percent is not None:
                vat_amount = commercial_total_ex_vat * resolved_vat_percent / 100.0
                commercial_total_inc_vat = commercial_total_ex_vat + vat_amount
            else:
                vat_amount = 0.0 if include_vat else 0.0
                commercial_total_inc_vat = commercial_total_ex_vat

        if requested_scope:
            warnings.append(_issue("requested_scope_ignored", f"Requested scope '{requested_scope}' is informational only"))
        if notes:
            warnings.append(_issue("notes_received", "Preview notes were received"))

        return PricingPreviewComputation(
            material_code=row.code,
            material_name=row.name,
            material_status=row.status,
            quantity=qty,
            unit=unit,
            currency=currency,
            unit_cost=unit_cost,
            base_cost_total=base_cost_total,
            applied_markup_policy=applied_policy,
            markup_amount=markup_amount,
            commercial_unit_price_ex_vat=commercial_unit_price_ex_vat,
            commercial_total_ex_vat=commercial_total_ex_vat,
            vat_percent=resolved_vat_percent,
            vat_amount=vat_amount,
            commercial_total_inc_vat=commercial_total_inc_vat,
            warnings=warnings,
            blockers=blockers,
        ).to_dict()