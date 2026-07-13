"""Template-driven Pricing Registry aggregation (read-only).

Interim technical debt: material acquisition costs live in inventory_materials
and operation rates in workcenter_rates — CostEngine reads via
load_material_cost_dict / load_workcenter_rate_dict. This service exposes the
operator-facing Pricing Registry view without duplicating price storage.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.commercial_markup_policies import Commercial_markup_policies
from models.inventory_materials import Inventory_materials
from models.product_templates import Product_templates
from models.workcenter_rates import Workcenter_rates
from seeds.seed_intake_v6_unified_pricing import V6_MATERIAL_PRICES, V6_WORKCENTER_RATES
from services.acm_bond_material_rate_resolver import ACM_THICKNESS_MM_TO_VARIANT_CODE
from services.inventory_materials_admin_service import load_material_cost_dict
from services.product_readiness_service import ProductReadinessService
from services.volumetric_material_rate_resolver import (
    PROFILE_DEPTH_MM_TO_VARIANT_CODE,
    PSU_WATTS_TO_VARIANT_CODE,
)
from services.active_template_scope import is_owner_valid_active_template
from services.workcenter_rates_service import load_workcenter_rate_dict

# Operator-facing category taxonomy (Pricing Registry, not Inventory stock view)
REGISTRY_CATEGORIES = (
    "Plăci",
    "Role / materiale flexibile",
    "Profile / canturi",
    "LED / electrice",
    "Consumabile",
    "Lăcătușerie / debitare metale",
    "Operații / Rate",
    "Adaos comercial",
    "Verificare",
)

METAL_PREMOUNT_STRUCTURE_TEMPLATE_CODE = "TPL-METAL-PREMOUNT-STRUCTURE_v1"
METAL_PREMOUNT_WORKCENTER_CODE = "WC_METAL_FAB"
METALWORKING_REGISTRY_CATEGORY = "Lăcătușerie / debitare metale"

TEMPLATE_MATERIAL_VARIANT_EXPANSION: Dict[str, Dict[str, List[str]]] = {
    "TPL-VOLUMETRIC-LETTERS_v2": {
        "MAT-PROFIL-LATERAL-LITERE": sorted(PROFILE_DEPTH_MM_TO_VARIANT_CODE.values()),
        "MAT-LED-PSU-12V": sorted(PSU_WATTS_TO_VARIANT_CODE.values()),
    },
    "TPL-ACM-CASSETTED-PANEL": {
        "MAT-ACM-BOND-PANEL": sorted(ACM_THICKNESS_MM_TO_VARIANT_CODE.values()),
    },
    "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1": {
        "MAT-ACM-BOND-PANEL": ["MAT-ACM-BOND-3MM"],
    },
    "TPL-CUT-ACM-LETTERS": {
        "MAT-ACM-BOND-PANEL": sorted(ACM_THICKNESS_MM_TO_VARIANT_CODE.values()),
    },
}

PRODUCT_001_ALIASES: Dict[str, str] = {
    "Product 001": "TPL-VOLUMETRIC-LETTERS_v2",
    "TPL-VOLUMETRIC-LETTERS": "TPL-VOLUMETRIC-LETTERS_v2",
}
V6_ALIGNED_TEMPLATE_CODES: Set[str] = {"TPL-VOLUMETRIC-LETTERS_v2"}
PREMOUNT_STRUCTURE_MATERIAL_CODES: Set[str] = {
    "MAT-PREMOUNT-BAR-ALUMINUM",
    "MAT-PREMOUNT-BAR-STEEL",
}
V6_REQUIRED_MATERIAL_CODES: Set[str] = {
    item["code"] for item in V6_MATERIAL_PRICES
} - PREMOUNT_STRUCTURE_MATERIAL_CODES
PREMOUNT_STRUCTURE_WORKCENTER_CODES: Set[str] = {"METAL_FAB", "WC_METAL_FAB"}
V6_REQUIRED_WORKCENTER_CODES: Set[str] = {
    item["code"] for item in V6_WORKCENTER_RATES
} - PREMOUNT_STRUCTURE_WORKCENTER_CODES


def _workcenter_registry_display(
    *,
    wc_code: str,
    row: Workcenter_rates | None,
    used_by_templates: List[str],
) -> tuple[str, str]:
    if (
        wc_code == METAL_PREMOUNT_WORKCENTER_CODE
        and used_by_templates == [METAL_PREMOUNT_STRUCTURE_TEMPLATE_CODE]
    ):
        return "Servicii debitare metale — lăcătușerie", METALWORKING_REGISTRY_CATEGORY
    return getattr(row, "label", None) or wc_code, "Operații / Rate"


def _parse_json(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _extract_workcenter_codes_from_components(components: Any) -> Set[str]:
    from services.template_operation_policy import is_quote_priced_operation

    codes: Set[str] = set()
    if not isinstance(components, list):
        return codes
    for component in components:
        if not isinstance(component, dict):
            continue
        for op in component.get("operations") or []:
            if isinstance(op, dict) and is_quote_priced_operation(op):
                wc = str(op.get("workcenter") or "").strip()
                if wc:
                    codes.add(wc)
    return codes


def _expand_material_codes_for_template(
    template_code: str, material_codes: Set[str]
) -> Set[str]:
    expanded = set(material_codes)
    variant_map = TEMPLATE_MATERIAL_VARIANT_EXPANSION.get(template_code, {})
    for base_code, variants in variant_map.items():
        if base_code in material_codes:
            expanded.discard(base_code)
            expanded.update(variants)
    return expanded


def infer_registry_category(
    *,
    pricing_code: str,
    pricing_kind: str,
    inventory_category: str | None = None,
    display_name: str | None = None,
) -> str:
    code = pricing_code.upper()
    name = (display_name or "").lower()

    if pricing_kind in {"operation_rate", "workcenter_rate", "service"}:
        return "Operații / Rate"

    if "PROFIL-LATERAL" in code or "profil" in name and "lateral" in name:
        return "Profile / canturi"
    if "LED" in code or "PSU" in code:
        return "LED / electrice"
    if any(
        k in code
        for k in (
            "ACM",
            "ACP",
            "BOND",
            "DIBOND",
            "PLEXI",
            "FOREX",
            "PVC",
            "SPATE",
            "SABLON",
            "PANOU",
        )
    ):
        return "Plăci"
    if any(k in code for k in ("VOPSEA", "CONSUMABILE", "SURUB", "ADEZIV")):
        return "Consumabile"
    if any(k in code for k in ("BANNER", "VINYL", "MESH", "FOLIE", "PRINT")):
        return "Role / materiale flexibile"

    if inventory_category:
        cat = inventory_category.lower()
        if "panou" in cat or "compozit" in cat or "plexiglas" in cat:
            return "Plăci"
        if "profil" in cat:
            return "Profile / canturi"
        if "led" in cat or "iluminat" in cat:
            return "LED / electrice"
        if "consum" in cat:
            return "Consumabile"

    return "Plăci" if pricing_kind == "material" else "Operații / Rate"


def map_confidence(
    *,
    source_review_status: str | None,
    status: str | None,
    has_price: bool,
) -> str:
    srs = str(source_review_status or "").strip().lower()
    st = str(status or "").strip().lower()

    if not has_price or st == "missing_price":
        return "missing"
    if srs == "accepted_override":
        return "owner_confirmed"
    if srs in {"needs_review", "pending"} or st == "needs_owner_input":
        return "estimated"
    if srs == "accepted":
        return "owner_confirmed"
    if st == "active" and has_price:
        return "owner_confirmed"
    return "missing"


def map_registry_status(
    *,
    row_status: str | None,
    has_price: bool,
    source_review_status: str | None,
) -> str:
    st = str(row_status or "").strip().lower()
    srs = str(source_review_status or "").strip().lower()
    if not has_price or st == "missing_price":
        return "missing_price"
    if srs in {"needs_review", "pending"} or st == "needs_owner_input":
        return "needs_review"
    if st == "archived":
        return "archived"
    if st == "active" and has_price:
        return "active"
    return "needs_review"


class PricingRegistryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_registry(
        self,
        *,
        template_filter: str | None = None,
        include_all_inventory: bool = False,
    ) -> Dict[str, Any]:
        templates = (
            await self.db.execute(
                select(Product_templates).where(Product_templates.active.is_(True))
            )
        ).scalars().all()
        templates = [
            tpl
            for tpl in templates
            if is_owner_valid_active_template(tpl.template_code)
        ]

        template_usage: Dict[str, Dict[str, Set[str]]] = {}
        all_material_codes: Set[str] = set()
        all_workcenter_codes: Set[str] = set()

        for tpl in templates:
            code = str(tpl.template_code or "").strip()
            if not code:
                continue

            components = _parse_json(tpl.components_json)
            flat_materials = _parse_json(tpl.required_materials_json)
            flat_operations = _parse_json(tpl.operations_json)

            mat_codes = ProductReadinessService._extract_material_codes(flat_materials)
            mat_codes |= ProductReadinessService._extract_material_codes_from_components(
                components
            )
            mat_codes = _expand_material_codes_for_template(code, mat_codes)
            if code in V6_ALIGNED_TEMPLATE_CODES:
                mat_codes |= V6_REQUIRED_MATERIAL_CODES

            wc_codes = ProductReadinessService._extract_workcenter_codes(flat_operations)
            wc_codes |= _extract_workcenter_codes_from_components(components)
            if code in V6_ALIGNED_TEMPLATE_CODES:
                wc_codes |= V6_REQUIRED_WORKCENTER_CODES

            template_usage[code] = {
                "material_codes": mat_codes,
                "workcenter_codes": wc_codes,
            }
            all_material_codes |= mat_codes
            all_workcenter_codes |= wc_codes

        if template_filter:
            resolved = PRODUCT_001_ALIASES.get(template_filter, template_filter)
            if resolved in template_usage:
                usage = template_usage[resolved]
                all_material_codes = set(usage["material_codes"])
                all_workcenter_codes = set(usage["workcenter_codes"])
                template_usage = {resolved: usage}
            else:
                all_material_codes = set()
                all_workcenter_codes = set()
                template_usage = {}

        material_rows: Dict[str, Inventory_materials] = {}
        if all_material_codes or include_all_inventory:
            query = select(Inventory_materials)
            if not include_all_inventory and all_material_codes:
                query = query.where(Inventory_materials.code.in_(sorted(all_material_codes)))
            rows = (await self.db.execute(query)).scalars().all()
            for row in rows:
                material_rows[row.code] = row
            # Ensure variant rows appear even if not directly on template JSON
            if not include_all_inventory:
                missing_variant_codes: Set[str] = set()
                for code in all_material_codes:
                    for tpl_code, usage in template_usage.items():
                        for variant_list in TEMPLATE_MATERIAL_VARIANT_EXPANSION.get(
                            tpl_code, {}
                        ).values():
                            if code in variant_list or any(
                                v in all_material_codes for v in variant_list
                            ):
                                missing_variant_codes.update(variant_list)
                extra_codes = missing_variant_codes - set(material_rows.keys())
                if extra_codes:
                    extra_rows = (
                        await self.db.execute(
                            select(Inventory_materials).where(
                                Inventory_materials.code.in_(sorted(extra_codes))
                            )
                        )
                    ).scalars().all()
                    for row in extra_rows:
                        material_rows[row.code] = row
                        all_material_codes.add(row.code)

        workcenter_rows: Dict[str, Workcenter_rates] = {}
        if all_workcenter_codes:
            wc_result = await self.db.execute(
                select(Workcenter_rates).where(
                    Workcenter_rates.code.in_(sorted(all_workcenter_codes))
                )
            )
            for row in wc_result.scalars().all():
                workcenter_rows[row.code] = row

        cost_engine_materials = await load_material_cost_dict(self.db)
        cost_engine_workcenters = await load_workcenter_rate_dict(self.db)

        used_by_material: Dict[str, List[str]] = {}
        used_by_workcenter: Dict[str, List[str]] = {}
        for tpl_code, usage in template_usage.items():
            for mc in usage["material_codes"]:
                used_by_material.setdefault(mc, []).append(tpl_code)
            for wc in usage["workcenter_codes"]:
                used_by_workcenter.setdefault(wc, []).append(tpl_code)

        items: List[Dict[str, Any]] = []

        for mat_code in sorted(all_material_codes):
            row = material_rows.get(mat_code)
            has_price = (
                row is not None
                and row.unit_cost is not None
                and float(row.unit_cost) > 0
            )
            confidence = map_confidence(
                source_review_status=getattr(row, "source_review_status", None),
                status=getattr(row, "status", None),
                has_price=has_price,
            )
            status = map_registry_status(
                row_status=getattr(row, "status", None),
                has_price=has_price,
                source_review_status=getattr(row, "source_review_status", None),
            )
            ce_rate = cost_engine_materials.get(mat_code)
            items.append(
                {
                    "pricing_code": mat_code,
                    "display_name": row.name if row else mat_code,
                    "pricing_kind": "material",
                    "registry_category": infer_registry_category(
                        pricing_code=mat_code,
                        pricing_kind="material",
                        inventory_category=getattr(row, "category", None),
                        display_name=getattr(row, "name", None),
                    ),
                    "unit": getattr(row, "unit", None) or "buc",
                    "base_cost": float(row.unit_cost) if has_price else None,
                    "currency": getattr(row, "currency", None),
                    "vat_percent": getattr(row, "vat_percent", None),
                    "status": status,
                    "confidence": confidence,
                    "source_notes": getattr(row, "source_notes", None),
                    "used_by_templates": sorted(used_by_material.get(mat_code, [])),
                    "affects_quote_calculation": True,
                    "technical_source": "inventory_materials",
                    "cost_engine_rate": ce_rate,
                    "cost_engine_rate_match": (
                        ce_rate is not None
                        and has_price
                        and abs(float(ce_rate) - float(row.unit_cost)) < 1e-9
                    ),
                    "editable": True,
                }
            )

        for wc_code in sorted(all_workcenter_codes):
            row = workcenter_rows.get(wc_code)
            basis = (getattr(row, "rate_basis", None) or "per_hour") if row else "per_hour"
            rate_val = None
            currency = getattr(row, "currency", None) or "RON" if row else "RON"
            rate_unit = f"{currency}/h"
            if row:
                if basis == "per_hour" and row.rate_per_hour:
                    rate_val = float(row.rate_per_hour)
                    rate_unit = f"{currency}/h"
                elif basis == "per_linear_meter" and row.rate_per_linear_meter:
                    rate_val = float(row.rate_per_linear_meter)
                    rate_unit = f"{currency}/ml"
                elif basis == "per_piece" and row.rate_per_linear_meter:
                    rate_val = float(row.rate_per_linear_meter)
                    rate_unit = f"{currency}/buc"
                elif basis == "per_square_meter" and row.rate_per_linear_meter:
                    rate_val = float(row.rate_per_linear_meter)
                    rate_unit = f"{currency}/mp"

            ce_spec = cost_engine_workcenters.get(wc_code)
            ce_rate = None
            if isinstance(ce_spec, dict):
                ce_rate = ce_spec.get("rate_per_linear_meter") or ce_spec.get(
                    "rate_per_hour"
                )
            elif isinstance(ce_spec, (int, float)):
                ce_rate = float(ce_spec)

            has_rate = rate_val is not None and rate_val > 0
            used_by_templates = sorted(used_by_workcenter.get(wc_code, []))
            display_name, registry_category = _workcenter_registry_display(
                wc_code=wc_code,
                row=row,
                used_by_templates=used_by_templates,
            )
            items.append(
                {
                    "pricing_code": wc_code,
                    "display_name": display_name,
                    "pricing_kind": "operation_rate",
                    "registry_category": registry_category,
                    "unit": rate_unit,
                    "base_cost": rate_val,
                    "currency": getattr(row, "currency", None),
                    "vat_percent": None,
                    "status": "active" if has_rate else "missing_price",
                    "confidence": "owner_confirmed" if has_rate else "missing",
                    "source_notes": getattr(row, "notes", None),
                    "used_by_templates": used_by_templates,
                    "affects_quote_calculation": True,
                    "technical_source": "workcenter_rates",
                    "cost_engine_rate": ce_rate,
                    "cost_engine_rate_match": (
                        ce_rate is not None
                        and has_rate
                        and abs(float(ce_rate) - float(rate_val)) < 1e-9
                    ),
                    "editable": True,
                    "rate_basis": basis,
                }
            )

        markup_rows = (
            await self.db.execute(select(Commercial_markup_policies))
        ).scalars().all()
        markup_items: List[Dict[str, Any]] = []
        for pol in markup_rows:
            markup_items.append(
                {
                    "pricing_code": f"MARKUP-{pol.id}",
                    "display_name": pol.name or f"Policy #{pol.id}",
                    "pricing_kind": "markup_rule",
                    "registry_category": "Adaos comercial",
                    "unit": pol.markup_type or "percent",
                    "base_cost": pol.markup_percent or pol.markup_fixed,
                    "currency": pol.currency,
                    "status": str(pol.status or "active"),
                    "confidence": "owner_confirmed",
                    "scope_type": pol.scope_type,
                    "scope_value": pol.scope_value,
                    "used_by_templates": [],
                    "affects_quote_calculation": True,
                    "technical_source": "commercial_markup_policies",
                    "editable": False,
                }
            )

        owner_confirmed = sum(1 for i in items if i["confidence"] == "owner_confirmed")
        needs_review = sum(1 for i in items if i["status"] == "needs_review")
        missing_price = sum(1 for i in items if i["status"] == "missing_price")

        return {
            "summary": {
                "templates_active": len(template_usage),
                "items_template_used": len(items),
                "materials_count": sum(1 for i in items if i["pricing_kind"] == "material"),
                "rates_count": sum(
                    1 for i in items if i["pricing_kind"] == "operation_rate"
                ),
                "markup_rules_count": len(markup_items),
                "owner_confirmed": owner_confirmed,
                "needs_review": needs_review,
                "missing_price": missing_price,
            },
            "template_usage": [
                {
                    "template_code": tc,
                    "material_codes": sorted(u["material_codes"]),
                    "workcenter_codes": sorted(u["workcenter_codes"]),
                }
                for tc, u in sorted(template_usage.items())
            ],
            "items": items,
            "markup_policies": markup_items,
            "registry_categories": list(REGISTRY_CATEGORIES),
            "technical_debt_note": (
                "inventory_materials este folosit tehnic ca registru de prețuri materiale "
                "pentru CostEngine; workcenter_rates pentru operații. Pricing UI este "
                "registrul operator-facing pentru calculul de ofertă — nu sursa Inventory."
            ),
        }
