"""PRODUCT_PRICE_BREAKDOWN_V1 — adapter over CPP + EIC + pricing recipe.

Does not recalculate commercial or internal totals. Projects authoritative lines
into an operator-readable desfășurător.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.product_price_breakdown import (
    PriceBreakdownCalibrationHook,
    PriceBreakdownGroupTotal,
    PriceBreakdownLine,
    PriceBreakdownTotals,
    ProductPriceBreakdownResponse,
)
from schemas.volum_aluminiu_separate_calc_preview import (
    VolumAluminiuSeparateCalcPreviewRequest,
)
from services.commercial_price_proposal_service import CommercialPriceProposalService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.product_price_breakdown_fixtures import resolve_fixture
from services.template_architecture_scope import VOLUM_ALUMINUM_TEMPLATE_CODE
from services.template_pricing_recipe_service import TemplatePricingRecipeService
from services.volum_aluminiu_separate_calc_preview_service import (
    VolumAluminiuSeparateCalcPreviewService,
)


def _fmt_formula(
    quantity: Any,
    unit: Any,
    rate: Any,
    currency: Any,
) -> str:
    q = quantity if quantity is not None else "?"
    u = unit or "u"
    r = rate if rate is not None else "?"
    c = currency or ""
    return f"{q} {u} × {r} {c}/{u}".strip()


def _group_for_eic_line_type(line_type: str) -> str:
    mapping = {
        "material": "material",
        "operation": "machine",
        "consumable": "service",
        "overhead": "adjustment",
        "capacity_hint": "adjustment",
    }
    return mapping.get(line_type, "internal")


def _group_for_cpp_basis(basis: str, code: str) -> str:
    code_u = (code or "").upper()
    if "AMBAL" in code_u or "PACK" in code_u:
        return "service"
    if "LED" in code_u or "ELECTRIC" in code_u or "MONTAJ" in code_u or "ASAMB" in code_u:
        return "labor"
    if basis in {"m2", "ml"} and ("CNC" in code_u or "DEBIT" in code_u or "V_GROOVE" in code_u or "VG" in code_u):
        return "machine"
    if basis in {"fixed", "minimum", "complexity"}:
        return "adjustment"
    return "commercial"


class ProductPriceBreakdownService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build(
        self,
        template_code: str,
        *,
        workspace_id: Optional[str] = None,
        quote_input: Optional[dict[str, Any]] = None,
        currency: str = "RON",
        fixture_id: Optional[str] = None,
    ) -> ProductPriceBreakdownResponse:
        resolved_fixture, fixture_qi, fixture_label, declared = resolve_fixture(
            template_code, fixture_id
        )
        # Prefer declared mixed-case catalog key (rules/EIC/CPP membership is case-sensitive).
        code = declared or (template_code or "").strip()
        qi = quote_input if quote_input is not None else fixture_qi
        config_id = workspace_id or resolved_fixture or "adhoc_quote_input"

        recipe = await TemplatePricingRecipeService(self.db).build_recipe(code)
        ai_rows = [d.model_dump() for d in (recipe.ai_decisions if recipe else [])]
        ops_ready = (
            getattr(recipe.readiness, "activation_status", None) if recipe else None
        )
        acm_treat = None
        if recipe and recipe.acm_acceptance and recipe.acm_acceptance.applies:
            acm_treat = not bool(
                recipe.acm_acceptance.treatment_commercial_lines_allowed
            )

        lines: list[PriceBreakdownLine] = []
        warnings: list[str] = []
        blockers: list[str] = []
        cpp = None
        eic = None
        cpp_codes: list[str] = []
        eic_codes: list[str] = []

        # --- Volum Aluminiu child: authoritative separate-calc slice (not root CPP) ---
        if code == VOLUM_ALUMINUM_TEMPLATE_CODE:
            va = VolumAluminiuSeparateCalcPreviewService(self.db).build_preview(
                code,
                VolumAluminiuSeparateCalcPreviewRequest(
                    payload=qi or {},
                    currency=currency,
                ),
            )
            warnings.extend(list(va.warnings or []))
            blockers.extend(list(va.blockers or []))
            if va.publication_blocked:
                warnings.append(
                    "Volum Aluminiu: copil activ — publicație root blocată (corect)."
                )
            commercial = va.commercial if isinstance(va.commercial, dict) else None
            internal = va.internal_cost if isinstance(va.internal_cost, dict) else None
            if commercial and commercial.get("ok"):
                cpp_codes.append(str(commercial.get("line_code") or ""))
                qty = commercial.get("quantity")
                rate = commercial.get("unit_price")
                unit = commercial.get("unit") or "ml"
                lines.append(
                    PriceBreakdownLine(
                        line_id=f"{code}::commercial::{commercial.get('line_code')}",
                        line_group="machine",
                        resource_code=str(commercial.get("line_code") or ""),
                        display_name=str(commercial.get("label") or "Modelare cant"),
                        quantity_key="confirmed_perimeter_m",
                        formula_display=_fmt_formula(qty, unit, rate, currency),
                        quantity=float(qty) if qty is not None else None,
                        unit=unit,
                        base_value=float(rate) if rate is not None else None,
                        currency=str(commercial.get("currency") or currency),
                        source_type="documented_commercial",
                        source_id=str(commercial.get("pricing_rule_code") or ""),
                        commercial_value=float(commercial["line_total"])
                        if commercial.get("line_total") is not None
                        else None,
                        cpp_line=str(commercial.get("line_code") or ""),
                        warning="Componentă copil — nu produs root",
                    )
                )
            if internal and internal.get("ok"):
                eic_codes.append(str(internal.get("line_code") or ""))
                qty = internal.get("quantity")
                rate = internal.get("unit_cost")
                unit = internal.get("unit") or "ml"
                lines.append(
                    PriceBreakdownLine(
                        line_id=f"{code}::internal::{internal.get('line_code')}",
                        line_group="machine",
                        resource_code=str(internal.get("line_code") or ""),
                        display_name=str(internal.get("label") or "Modelare cant (intern)"),
                        quantity_key="confirmed_perimeter_m",
                        formula_display=_fmt_formula(qty, unit, rate, currency),
                        quantity=float(qty) if qty is not None else None,
                        unit=unit,
                        base_value=float(rate) if rate is not None else None,
                        currency=currency,
                        source_type="catalog",
                        source_id=str(internal.get("rule_code") or ""),
                        internal_cost=float(internal["line_total"])
                        if internal.get("line_total") is not None
                        else None,
                        eic_rule=str(internal.get("rule_code") or ""),
                    )
                )
            # AI + material gaps still projected below; skip root CPP/EIC for child.
        else:
            cpp = await CommercialPriceProposalService(self.db).build_preview(
                code,
                workspace_id=workspace_id,
                quote_input=qi,
                currency=currency,
            )
            eic = await EstimatedInternalCostService(self.db).build_preview(
                code,
                workspace_id=workspace_id,
                quote_input=qi,
                currency=currency,
            )
            if cpp is None:
                warnings.append(
                    "CPP indisponibil pentru această configurație "
                    "(Product Definition lipsă sau template fără reguli comerciale)."
                )
            if eic is None:
                warnings.append(
                    "EIC indisponibil pentru această configurație "
                    "(Product Definition lipsă sau template fără reguli interne)."
                )

        # --- Commercial lines (CPP authority) ---
        if cpp is not None:
            for line in cpp.commercial_price_lines:
                cpp_codes.append(line.code)
                group = _group_for_cpp_basis(str(line.basis_type), line.code)
                warn = "; ".join(line.warnings) if line.warnings else None
                lines.append(
                    PriceBreakdownLine(
                        line_id=f"{code}::commercial::{line.code}",
                        line_group=group,  # type: ignore[arg-type]
                        resource_code=line.code,
                        display_name=line.label,
                        quantity_key=None,
                        formula_display=_fmt_formula(
                            line.quantity,
                            line.unit,
                            line.commercial_unit_price,
                            line.cpp_currency or cpp.currency,
                        ),
                        quantity=float(line.quantity)
                        if line.quantity is not None
                        else None,
                        unit=line.unit,
                        base_value=line.commercial_unit_price,
                        currency=line.cpp_currency or cpp.currency,
                        source_type="documented_commercial"
                        if "documented" in (line.source or "")
                        else "catalog",
                        source_id=line.pricing_rule_code or line.registry_pricing_code,
                        commercial_value=line.subtotal,
                        cpp_line=line.code,
                        warning=warn,
                        confidence="medium",
                    )
                )
            for b in cpp.commercial_blockers:
                blockers.append(f"{b.code}: {b.message}")
            warnings.extend(list(cpp.warnings or []))
            for m in cpp.minimums_applied:
                lines.append(
                    PriceBreakdownLine(
                        line_id=f"{code}::adjustment::min::{m.code}",
                        line_group="adjustment",
                        resource_code=m.code,
                        display_name=m.label,
                        formula_display=m.detail or "minimum aplicat",
                        source_type="catalog",
                        source_id=m.code,
                        commercial_value=None,
                        warning=None,
                    )
                )

        # --- Internal lines (EIC authority) ---
        if eic is not None:
            all_internal = (
                list(eic.estimated_material_lines)
                + list(eic.estimated_operation_lines)
                + list(eic.estimated_consumable_lines)
                + list(eic.estimated_overhead_lines)
            )
            for line in all_internal:
                eic_codes.append(line.code)
                group = _group_for_eic_line_type(str(line.line_type))
                source_type = "inventory" if line.line_type == "material" else "catalog"
                if line.basis_type == "inventory_unit_cost":
                    source_type = "inventory"
                warn = None
                if line.internal_unit_cost is None and line.line_type == "material":
                    warn = "Preț material lipsă"
                if line.warnings:
                    warn = "; ".join(
                        ([warn] if warn else []) + list(line.warnings)
                    )
                lines.append(
                    PriceBreakdownLine(
                        line_id=f"{code}::internal::{line.code}",
                        line_group=group,  # type: ignore[arg-type]
                        resource_code=line.code,
                        display_name=line.label,
                        formula_display=_fmt_formula(
                            line.quantity,
                            line.unit,
                            line.internal_unit_cost,
                            eic.currency,
                        ),
                        quantity=float(line.quantity)
                        if line.quantity is not None
                        else None,
                        unit=line.unit,
                        base_value=line.internal_unit_cost,
                        currency=eic.currency,
                        source_type=source_type,  # type: ignore[arg-type]
                        source_id=line.rule_code,
                        internal_cost=line.subtotal,
                        eic_rule=line.rule_code,
                        warning=warn,
                    )
                )
            for b in eic.internal_blockers:
                blockers.append(f"{b.code}: {b.message}")
            warnings.extend(list(eic.warnings or []))

        # --- AI decisions (from recipe; contribution note only) ---
        for d in ai_rows:
            did = str(d.get("decision_id") or "")
            lines.append(
                PriceBreakdownLine(
                    line_id=f"{code}::ai::{did}",
                    line_group="ai_decision",
                    resource_code=str(d.get("target_code") or did),
                    display_name=str(d.get("display_name_ro") or did),
                    quantity_key=d.get("quantity_key"),
                    formula_display=str(d.get("formula") or ""),
                    quantity=None,
                    unit=d.get("unit"),
                    base_value=d.get("resolved_value"),
                    currency=d.get("currency") or currency,
                    source_type="AI_DECISION",
                    source_id=did,
                    configurable=bool(d.get("configurable", True)),
                    confidence=d.get("confidence"),
                    rationale_ro=d.get("rationale_ro"),
                    ai_decision_id=did,
                    warning="Valoare AI activă"
                    if d.get("decision_source") == "AI_DECISION"
                    else None,
                )
            )

        # Recipe materials missing price (structural visibility)
        if recipe is not None:
            for item in recipe.recipe:
                if item.recipe_kind != "material":
                    continue
                if item.status == "missing" or item.current_value is None:
                    lines.append(
                        PriceBreakdownLine(
                            line_id=f"{code}::material_gap::{item.stable_code}",
                            line_group="material",
                            resource_code=item.catalog_code or item.stable_code,
                            display_name=item.operator_name,
                            formula_display="Preț material lipsă — vizibil, fără inventare AI",
                            unit=item.unit,
                            base_value=None,
                            currency=item.currency,
                            source_type="inventory",
                            source_id=item.catalog_code,
                            warning="Preț material lipsă",
                            configurable=False,
                        )
                    )

        # Group totals
        group_internal: dict[str, float] = defaultdict(float)
        group_commercial: dict[str, float] = defaultdict(float)
        group_count: dict[str, int] = defaultdict(int)
        for line in lines:
            group_count[line.line_group] += 1
            if line.internal_cost is not None:
                group_internal[line.line_group] += float(line.internal_cost)
            if line.commercial_value is not None:
                group_commercial[line.line_group] += float(line.commercial_value)

        group_totals = [
            PriceBreakdownGroupTotal(
                line_group=g,  # type: ignore[arg-type]
                line_count=group_count[g],
                internal_subtotal=group_internal.get(g),
                commercial_subtotal=group_commercial.get(g),
                currency=currency,
            )
            for g in sorted(group_count.keys())
        ]

        commercial_sum = sum(
            float(l.commercial_value)
            for l in lines
            if l.commercial_value is not None and l.line_group != "ai_decision"
        )
        internal_sum = sum(
            float(l.internal_cost)
            for l in lines
            if l.internal_cost is not None and l.line_group != "ai_decision"
        )
        cpp_total = cpp.commercial_total if cpp else (
            commercial_sum if code == VOLUM_ALUMINUM_TEMPLATE_CODE and commercial_sum else None
        )
        eic_total = eic.estimated_total_internal_cost if eic else (
            internal_sum if code == VOLUM_ALUMINUM_TEMPLATE_CODE and internal_sum else None
        )

        def _close(a: Optional[float], b: Optional[float]) -> bool:
            if a is None or b is None:
                return False
            return abs(float(a) - float(b)) < 0.05

        totals = PriceBreakdownTotals(
            material_internal=eic.estimated_material_cost if eic else None,
            machine_internal=(
                eic.estimated_operation_cost
                if eic
                else (group_internal.get("machine") if code == VOLUM_ALUMINUM_TEMPLATE_CODE else None)
            ),
            labor_internal=None,
            service_internal=None,
            consumables_internal=eic.estimated_consumables_cost if eic else None,
            overhead_internal=eic.estimated_overhead_cost if eic else None,
            ai_contribution_note_ro=(
                f"{len(ai_rows)} decizii AI configurabile vizibile — "
                "contribuția comercială trece prin liniile CPP/EIC mapate, nu ca total paralel."
                if ai_rows
                else None
            ),
            internal_total=eic_total,
            commercial_subtotal=(
                cpp.subtotal_commercial
                if cpp
                else (commercial_sum if code == VOLUM_ALUMINUM_TEMPLATE_CODE else None)
            ),
            commercial_total=cpp_total,
            currency=(cpp.currency if cpp else None)
            or (eic.currency if eic else None)
            or currency,
            cpp_total_matches=_close(commercial_sum, cpp_total)
            if cpp_total is not None
            else True,
            eic_total_matches=_close(internal_sum, eic_total)
            if eic_total is not None
            else True,
            no_duplicate_commercial_codes=len(cpp_codes) == len(set(c for c in cpp_codes if c)),
            no_duplicate_internal_codes=len(eic_codes) == len(set(c for c in eic_codes if c)),
        )

        calibration: list[PriceBreakdownCalibrationHook] = []
        if eic is not None:
            for hint in eic.capacity_hints:
                calibration.append(
                    PriceBreakdownCalibrationHook(
                        line_code=hint.code,
                        estimated_minutes=hint.estimated_minutes,
                        purpose=hint.purpose,
                        excluded_from_total=bool(hint.excluded_from_total),
                    )
                )

        if not qi and not workspace_id:
            warnings.append(
                "Nicio configurație — folosiți fixture demo sau workspace_id / quote_input."
            )

        cfg_summary: dict[str, Any] = {
            "fixture_id": resolved_fixture,
            "fixture_label_ro": fixture_label,
            "workspace_id": workspace_id,
            "has_quote_input": qi is not None,
        }
        if qi and isinstance(qi.get("quote_geometry"), dict):
            cfg_summary["quote_geometry"] = qi["quote_geometry"]
        if qi and isinstance(qi.get("finish_setup"), dict):
            fs = qi["finish_setup"]
            cfg_summary["illuminated"] = fs.get("illuminated")
            cfg_summary["letter_led_module_count"] = fs.get("letter_led_module_count")
            cfg_summary["applied_content"] = fs.get("applied_content")

        return ProductPriceBreakdownResponse(
            template_code=code,
            configuration_id=config_id,
            fixture_id=resolved_fixture,
            currency=totals.currency,
            publication_status=None,
            operational_readiness=ops_ready,
            uses_ai_defaults=bool(ai_rows),
            configuration_summary=cfg_summary,
            lines=lines,
            group_totals=group_totals,
            totals=totals,
            ai_decisions=ai_rows,
            calibration_hooks=calibration,
            cpp_status=cpp.status if cpp else None,
            eic_status=eic.status if eic else None,
            warnings=sorted(set(warnings))[:40],
            blockers=sorted(set(blockers))[:40],
            eic_provenance=[p.model_dump() for p in (eic.provenance if eic else [])],
            cpp_provenance=[p.model_dump() for p in (cpp.provenance if cpp else [])],
            acm_treatments_blocked=acm_treat,
        )
