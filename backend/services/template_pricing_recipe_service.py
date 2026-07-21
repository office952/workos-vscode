"""Template Pricing Studio read model — composes catalogs + template recipe (read-only)."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.commercial_rules_volumetric_v2 import (
    LOGO_LINKED_CHILD_COMMERCIAL_RULE_TEMPLATES,
    RULES_BY_TEMPLATE,
    CommercialRuleDefinition,
)
from data.internal_cost_rules_volumetric_v2 import (
    RULES_BY_TEMPLATE as EIC_RULES_BY_TEMPLATE,
)
from models.product_templates import Product_templates
from schemas.template_pricing_recipe import (
    TEMPLATE_PRICING_RECIPE_VERSION,
    TemplateLaborRecipeItem,
    TemplateLaborRecipeSummary,
    TemplatePricingAcmAcceptance,
    TemplatePricingCppPreview,
    TemplatePricingEicPreview,
    TemplatePricingReadiness,
    TemplatePricingRecipeItem,
    TemplatePricingRecipeResponse,
    TemplatePricingSummary,
)
from services.acm_face_treatment_commercial_path_v1 import build_cpp_eic_commercial_gate
from services.pricing_registry_service import PricingRegistryService
from services.template_labor_recipe import (
    build_labor_recipes,
    merge_labor_from_pricing_recipe_items,
)
from services.template_usage_mode_policy import get_template_usage_mode_policy
from services.volum_aluminiu_component_contract import (
    IDENTITY_MAP as VOLUM_ALUMINIU_IDENTITY_MAP,
    TEMPLATE_CODE as VOLUM_ALUMINIU_TEMPLATE_CODE,
)

ACM_BOXED_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
VL_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO_TEMPLATE = "TPL-VOLUMETRIC-LOGO_v1"

_EDITABILITY_RO = "V1 este read-only — Studio compune, nu creează tarife."


def _recipe_id(template_code: str, kind: str, stable_code: str) -> str:
    return f"{template_code}::{kind}::{stable_code}"


def _source_links_for_catalog(
    *,
    catalog_code: str | None,
    typed_catalog: str | None,
    template_code: str,
) -> dict[str, str]:
    links: dict[str, str] = {}
    if not catalog_code:
        return links
    pricing_base = f"/inventory/pricing?template={template_code}"
    if typed_catalog == "material" or str(catalog_code).startswith("MAT-"):
        links["inventory"] = "/inventory"
        links["pricing_materiale"] = f"{pricing_base}&catalog=materiale"
    elif typed_catalog == "machine_operation":
        links["pricing_operatii"] = f"{pricing_base}&catalog=operatii"
    elif typed_catalog in {"labor", "service"}:
        links["pricing_manopera"] = f"{pricing_base}&catalog=manopera"
    else:
        links["pricing_registry"] = pricing_base
    return links


def _status_from_registry_item(item: dict[str, Any]) -> str:
    status = str(item.get("status") or "").lower()
    confidence = str(item.get("confidence") or "").lower()
    if status == "missing_price" or confidence == "missing" or item.get("base_cost") is None:
        return "missing"
    flags = item.get("data_quality_flags") or []
    if flags:
        return "warning"
    if status in {"inactive", "disabled"}:
        return "inactive"
    return "active"


def _kind_from_typed(typed: str | None, pricing_kind: str | None) -> str:
    if typed in {
        "material",
        "machine_operation",
        "labor",
        "service",
        "unknown",
        "markup_rule",
    }:
        if typed == "markup_rule":
            return "adjustment"
        return typed  # type: ignore[return-value]
    pk = str(pricing_kind or "")
    if pk == "material":
        return "material"
    if pk in {"operation_rate", "workcenter_rate"}:
        return "machine_operation"
    if pk == "service":
        return "service"
    return "unknown"


class TemplatePricingRecipeService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._registry = PricingRegistryService(db)

    async def build_recipe(
        self,
        template_code: str,
        *,
        workspace_id: str | None = None,
    ) -> TemplatePricingRecipeResponse | None:
        _ = workspace_id  # reserved for future payload-aware preview; unused in V1
        # DB codes may preserve mixed-case suffixes (e.g. `_v1`) while identity
        # normalization uppercases — resolve case-insensitively, keep DB code.
        result = await self._db.execute(
            select(Product_templates).where(Product_templates.template_code == template_code)
        )
        row = result.scalar_one_or_none()
        if row is None:
            result = await self._db.execute(select(Product_templates))
            candidates = list(result.scalars().all())
            needle = str(template_code or "").strip().upper()
            row = next(
                (
                    c
                    for c in candidates
                    if str(getattr(c, "template_code", "") or "").strip().upper() == needle
                ),
                None,
            )
        if row is None:
            return None

        stored_code = str(row.template_code)
        registry = await self._registry.build_registry(
            template_filter=stored_code,
            include_all_inventory=False,
        )
        registry_items = list(registry.get("items") or [])
        by_code = {
            str(it.get("pricing_code")): it
            for it in registry_items
            if it.get("pricing_code")
        }

        recipe: list[TemplatePricingRecipeItem] = []
        recipe.extend(self._items_from_registry(stored_code, registry_items))
        recipe.extend(self._items_from_commercial_rules(stored_code, by_code))
        if stored_code.upper() == LOGO_TEMPLATE.upper():
            recipe.extend(self._items_from_logo_linked(by_code))
        if stored_code.upper() == VOLUM_ALUMINIU_TEMPLATE_CODE.upper():
            recipe.extend(self._items_from_volum_aluminiu(by_code))

        # Deduplicate by recipe_item_id (prefer first — registry before commercial mirror)
        seen: set[str] = set()
        deduped: list[TemplatePricingRecipeItem] = []
        for item in recipe:
            if item.recipe_item_id in seen:
                continue
            seen.add(item.recipe_item_id)
            deduped.append(item)
        recipe = deduped

        commercial_by_catalog: dict[str, str] = {}
        for item in recipe:
            if item.recipe_kind == "commercial_line" and item.catalog_code and item.cpp_line_code:
                commercial_by_catalog[str(item.catalog_code)] = str(item.cpp_line_code)

        labor_raw = build_labor_recipes(
            template_code=stored_code,
            row=row,
            registry_by_code=by_code,
            commercial_line_by_catalog=commercial_by_catalog,
        )
        labor_raw = merge_labor_from_pricing_recipe_items(
            template_code=stored_code,
            pricing_items=recipe,
            existing=labor_raw,
        )
        labor_recipes = [TemplateLaborRecipeItem.model_validate(x) for x in labor_raw]
        labor_summary = TemplateLaborRecipeSummary(
            total=len(labor_recipes),
            technical_ready=sum(1 for r in labor_recipes if r.technical_ready),
            commercial_ready=sum(1 for r in labor_recipes if r.commercial_ready),
            missing_rate=sum(1 for r in labor_recipes if r.status == "missing"),
            warnings=sum(
                1
                for r in labor_recipes
                if r.status == "warning" or r.warnings or r.data_quality_flags
            ),
        )

        summary = self._summarize(recipe, registry)
        cpp = self._cpp_preview(stored_code, recipe)
        eic = self._eic_preview(stored_code)
        acm = self._acm_acceptance(stored_code, registry)
        readiness = self._readiness(summary, recipe, acm, labor_summary)

        blockers: list[str] = []
        warnings: list[str] = []
        for item in recipe:
            blockers.extend(item.blockers)
            warnings.extend(item.warnings)
            if item.data_quality_message_ro:
                warnings.append(item.data_quality_message_ro)
        for labor in labor_recipes:
            blockers.extend(labor.blockers)
            warnings.extend(labor.warnings)
        if acm.applies and acm.blockers:
            blockers.extend(acm.blockers)

        usage_policy = get_template_usage_mode_policy(stored_code)
        usage_mode = None
        if usage_policy is not None:
            usage_mode = (
                "root_offerable"
                if usage_policy.root_offerable
                else "linked_child"
                if usage_policy.linked_child_allowed
                else "candidate_only"
                if usage_policy.candidate_only
                else "policy_present"
            )
        return TemplatePricingRecipeResponse(
            schema_version=TEMPLATE_PRICING_RECIPE_VERSION,
            template_code=stored_code,
            template_name=getattr(row, "family_name", None) or getattr(row, "name", None),
            template_version=str(getattr(row, "version", None) or getattr(row, "template_version", None) or "")
            or None,
            lifecycle="active" if getattr(row, "active", False) else "inactive",
            usage_mode=usage_mode,
            summary=summary,
            recipe=recipe,
            labor_recipes=labor_recipes,
            labor_summary=labor_summary,
            cpp_preview=cpp,
            eic_preview=eic,
            readiness=readiness,
            acm_acceptance=acm,
            blockers=sorted(set(blockers)),
            warnings=sorted(set(warnings)),
        )

    def _items_from_registry(
        self,
        template_code: str,
        items: list[dict[str, Any]],
    ) -> list[TemplatePricingRecipeItem]:
        out: list[TemplatePricingRecipeItem] = []
        for raw in items:
            code = str(raw.get("pricing_code") or "")
            if not code:
                continue
            typed = raw.get("typed_catalog")
            kind = _kind_from_typed(
                str(typed) if typed else None,
                str(raw.get("pricing_kind") or None),
            )
            status = _status_from_registry_item(raw)
            flags = list(raw.get("data_quality_flags") or [])
            blockers: list[str] = []
            warnings: list[str] = []
            if status == "missing":
                blockers.append("MISSING_CATALOG_RATE")
            if "rate_basis_column_mismatch" in flags:
                warnings.append("RATE_BASIS_COLUMN_MISMATCH")
            cost_meaning = str(raw.get("cost_meaning") or "unknown")
            if cost_meaning not in {"purchase_cost", "reusable_rate", "commercial_documented"}:
                cost_meaning = (
                    "purchase_cost" if kind == "material" else "reusable_rate"
                )
            out.append(
                TemplatePricingRecipeItem(
                    recipe_item_id=_recipe_id(template_code, kind, code),
                    recipe_kind=kind,  # type: ignore[arg-type]
                    operator_name=str(raw.get("display_name") or code),
                    stable_code=code,
                    catalog_code=code,
                    quantity_keys=[],
                    formula_owner="product_template_components_or_operations",
                    rate_source="pricing_registry",
                    cost_or_rate=cost_meaning,  # type: ignore[arg-type]
                    cost_label_ro=raw.get("cost_label_ro"),
                    unit=raw.get("unit"),
                    current_value=raw.get("base_cost"),
                    currency=raw.get("currency"),
                    status=status,  # type: ignore[arg-type]
                    provenance=raw.get("technical_source"),
                    typed_catalog=str(typed) if typed else None,
                    machine_family=raw.get("machine_family"),
                    data_quality_flags=flags,
                    data_quality_message_ro=raw.get("data_quality_message_ro"),
                    technical_ready=True,
                    commercial_ready=status == "active",
                    blockers=blockers,
                    warnings=warnings,
                    editable=False,
                    editability_reason_ro=_EDITABILITY_RO,
                    source_links=_source_links_for_catalog(
                        catalog_code=code,
                        typed_catalog=str(typed) if typed else None,
                        template_code=template_code,
                    ),
                    legacy=False,
                    confidence="high" if status == "active" else "medium",
                )
            )
        return out

    def _items_from_commercial_rules(
        self,
        template_code: str,
        by_code: dict[str, dict[str, Any]],
    ) -> list[TemplatePricingRecipeItem]:
        rules = RULES_BY_TEMPLATE.get(template_code)
        if not rules:
            needle = str(template_code or "").upper()
            for key, value in RULES_BY_TEMPLATE.items():
                if str(key).upper() == needle:
                    rules = value
                    break
        if not rules:
            return []
        return [
            self._commercial_rule_item(template_code, rule, by_code.get(rule.registry_pricing_code or ""))
            for rule in rules
        ]

    def _items_from_logo_linked(
        self,
        by_code: dict[str, dict[str, Any]],
    ) -> list[TemplatePricingRecipeItem]:
        return [
            self._commercial_rule_item(
                LOGO_TEMPLATE,
                rule,
                by_code.get(rule.registry_pricing_code or ""),
                legacy=True,
            )
            for rule in LOGO_LINKED_CHILD_COMMERCIAL_RULE_TEMPLATES
        ]

    def _commercial_rule_item(
        self,
        template_code: str,
        rule: CommercialRuleDefinition,
        catalog: dict[str, Any] | None,
        *,
        legacy: bool = False,
    ) -> TemplatePricingRecipeItem:
        catalog_code = rule.registry_pricing_code
        typed = (catalog or {}).get("typed_catalog")
        flags = list((catalog or {}).get("data_quality_flags") or [])
        blockers: list[str] = []
        warnings: list[str] = list(rule.warnings or ())
        status = "active"
        if rule.owner_decision_required:
            status = "blocked"
            blockers.append(rule.owner_decision_code or "OWNER_DECISION_REQUIRED")
        if catalog_code and not catalog:
            # commercial documented price may still exist without registry mapping
            pass
        if catalog and _status_from_registry_item(catalog) == "missing":
            status = "missing" if status == "active" else status
            blockers.append("MISSING_CATALOG_RATE")
        if "rate_basis_column_mismatch" in flags:
            status = "warning" if status == "active" else status
            warnings.append("RATE_BASIS_COLUMN_MISMATCH")

        value = rule.documented_unit_price
        currency = rule.documented_unit_price_currency
        rate_source = "documented_commercial"
        if catalog and catalog.get("base_cost") is not None and not value:
            value = catalog.get("base_cost")
            currency = catalog.get("currency")
            rate_source = "pricing_registry"

        return TemplatePricingRecipeItem(
            recipe_item_id=_recipe_id(template_code, "commercial_line", rule.line_code),
            recipe_kind="commercial_line",
            operator_name=rule.label,
            stable_code=rule.line_code,
            catalog_code=catalog_code,
            quantity_keys=list(rule.quantity_paths),
            formula_owner=rule.source,
            applicability={
                "module_gate": rule.module_gate,
                "material_gate_path": rule.material_gate_path,
                "material_gate_value": rule.material_gate_value,
                "criticality": rule.criticality,
                "always_include": rule.always_include,
            },
            rate_source=rate_source,
            cost_or_rate="commercial_documented",
            cost_label_ro="Rată comercială documentată",
            unit=rule.unit,
            current_value=value,
            currency=currency,
            status=status,  # type: ignore[arg-type]
            provenance=rule.source,
            cpp_line_code=rule.line_code,
            cpp_pricing_rule_code=rule.pricing_rule_code,
            typed_catalog=str(typed) if typed else None,
            machine_family=(catalog or {}).get("machine_family"),
            data_quality_flags=flags,
            data_quality_message_ro=(catalog or {}).get("data_quality_message_ro"),
            technical_ready=bool(rule.quantity_paths) or rule.always_include or rule.basis_type == "set",
            commercial_ready=value is not None and status == "active",
            blockers=blockers,
            warnings=warnings,
            editable=False,
            editability_reason_ro=_EDITABILITY_RO,
            source_links=_source_links_for_catalog(
                catalog_code=catalog_code,
                typed_catalog=str(typed) if typed else None,
                template_code=template_code,
            ),
            legacy=legacy,
            confidence="high" if value is not None else "low",
        )

    def _items_from_volum_aluminiu(
        self,
        by_code: dict[str, dict[str, Any]],
    ) -> list[TemplatePricingRecipeItem]:
        _ = by_code
        aliases = VOLUM_ALUMINIU_IDENTITY_MAP.get("aliases") or {}
        commercial = aliases.get("COMMERCIAL_LINE_CODE") or aliases.get("commercial_line_code")
        # IDENTITY_MAP structure may nest differently — expose map honestly
        items: list[TemplatePricingRecipeItem] = [
            TemplatePricingRecipeItem(
                recipe_item_id=_recipe_id(
                    VOLUM_ALUMINIU_TEMPLATE_CODE, "commercial_line", "modelare_cant_aluminiu"
                ),
                recipe_kind="commercial_line",
                operator_name="Modelare cant aluminiu (component)",
                stable_code="modelare_cant_aluminiu",
                catalog_code=None,
                quantity_keys=["letter_perimeter_m"],
                formula_owner="volum_aluminiu_component_contract:IDENTITY_MAP",
                applicability={"parent_template": VL_TEMPLATE, "usage_mode": "component_only"},
                rate_source="parent_cpp_line",
                cost_or_rate="commercial_documented",
                cost_label_ro="Rată comercială (via Letters)",
                unit="ml",
                current_value=None,
                currency=None,
                status="warning",
                provenance="TPL-VOLUM-ALUMINIU_v1 is component_only — commercial line owned by parent Letters path",
                cpp_line_code="modelare_cant_aluminiu",
                technical_ready=True,
                commercial_ready=False,
                blockers=[],
                warnings=["COMPONENT_ONLY_NO_STANDALONE_COMMERCIAL_ROOT"],
                editable=False,
                editability_reason_ro=_EDITABILITY_RO,
                source_links={"pricing_registry": f"/inventory/pricing?template={VL_TEMPLATE}"},
                legacy=True,
                confidence="medium",
            )
        ]
        if commercial:
            items[0].warnings.append(f"IDENTITY_MAP_ALIAS:{commercial}")
        return items

    def _summarize(
        self,
        recipe: list[TemplatePricingRecipeItem],
        registry: dict[str, Any],
    ) -> TemplatePricingSummary:
        summary_raw = registry.get("summary") or {}
        materials = sum(1 for r in recipe if r.recipe_kind == "material")
        machines = sum(1 for r in recipe if r.recipe_kind == "machine_operation")
        labor = sum(1 for r in recipe if r.recipe_kind == "labor")
        services = sum(1 for r in recipe if r.recipe_kind == "service")
        commercial = sum(1 for r in recipe if r.recipe_kind == "commercial_line")
        return TemplatePricingSummary(
            total_items=len(recipe),
            materials=materials,
            machine_operations=machines,
            labor=labor,
            services=services,
            commercial_lines=commercial,
            resolved=sum(1 for r in recipe if r.status == "active"),
            missing=sum(1 for r in recipe if r.status == "missing"),
            blocked=sum(1 for r in recipe if r.status == "blocked"),
            warnings=sum(1 for r in recipe if r.status == "warning" or r.warnings or r.data_quality_flags),
            registry_confirmed=int(summary_raw.get("owner_confirmed") or 0),
            registry_missing_price=int(summary_raw.get("missing_price") or 0),
        )

    def _cpp_preview(
        self,
        template_code: str,
        recipe: list[TemplatePricingRecipeItem],
    ) -> TemplatePricingCppPreview:
        lines = [r.cpp_line_code for r in recipe if r.cpp_line_code]
        blocked = [r.cpp_line_code for r in recipe if r.cpp_line_code and r.status == "blocked"]
        rules = RULES_BY_TEMPLATE.get(template_code)
        if not rules:
            needle = str(template_code or "").upper()
            for key, value in RULES_BY_TEMPLATE.items():
                if str(key).upper() == needle:
                    rules = value
                    break
        if str(template_code or "").upper() == LOGO_TEMPLATE.upper():
            rules = LOGO_LINKED_CHILD_COMMERCIAL_RULE_TEMPLATES
        available = bool(rules) or bool(lines)
        return TemplatePricingCppPreview(
            available=available,
            status="structural_catalog" if available else "no_cpp_rules",
            line_codes=sorted({c for c in lines if c}),
            blocked_line_codes=sorted({c for c in blocked if c}),
            subtotal=None,
            currency=None,
        )

    def _eic_preview(self, template_code: str) -> TemplatePricingEicPreview:
        bucket = EIC_RULES_BY_TEMPLATE.get(template_code) or {}
        codes: list[str] = []
        notes: list[str] = []
        if isinstance(bucket, dict):
            for group_name, rules in bucket.items():
                notes.append(f"eic_group:{group_name}:{len(rules or ())}")
                for rule in rules or ():
                    code = (
                        getattr(rule, "line_code", None)
                        or getattr(rule, "rule_code", None)
                        or getattr(rule, "operation_code", None)
                    )
                    if code:
                        codes.append(str(code))
        if template_code == ACM_BOXED_TEMPLATE:
            notes.append(
                "ACM standalone EIC: capacity / structural hints only — not a full priced treatment path."
            )
        if template_code == VOLUM_ALUMINIU_TEMPLATE_CODE:
            notes.append(
                "Volum Aluminiu EIC resolves via parent Letters / separate-calc preview contracts."
            )
        return TemplatePricingEicPreview(
            available=bool(codes) or bool(notes),
            status="structural_catalog" if codes or notes else "no_eic_rules",
            provenance_notes=notes,
            rule_codes=sorted(set(codes)),
        )

    def _acm_acceptance(
        self,
        template_code: str,
        registry: dict[str, Any],
    ) -> TemplatePricingAcmAcceptance:
        if str(template_code or "").upper() != ACM_BOXED_TEMPLATE.upper():
            return TemplatePricingAcmAcceptance(applies=False)
        summary = registry.get("summary") or {}
        gate = build_cpp_eic_commercial_gate({"coexistence": "none"})
        # Default structural view: panel-only coexistence none still exposes gate honesty.
        # Face treatments remain blocked until owner rates — never invent.
        return TemplatePricingAcmAcceptance(
            applies=True,
            shell_registry_confirmed=int(summary.get("owner_confirmed") or 0),
            shell_registry_missing=int(summary.get("missing_price") or 0),
            treatment_commercial_lines_allowed=bool(
                gate.get("treatment_commercial_lines_allowed")
            ),
            blockers=list(gate.get("blockers") or []),
            policy_ro=(
                "Shell ACM: coverage registry confirmată. "
                "Tratamente față: treatment_commercial_lines_allowed=false până la owner rates. "
                "Nu se inventează prețuri."
            ),
        )

    def _readiness(
        self,
        summary: TemplatePricingSummary,
        recipe: list[TemplatePricingRecipeItem],
        acm: TemplatePricingAcmAcceptance,
        labor_summary: TemplateLaborRecipeSummary | None = None,
    ) -> TemplatePricingReadiness:
        technical = summary.total_items > 0 and all(
            r.technical_ready or r.recipe_kind == "commercial_line" for r in recipe
        )
        commercial = (
            summary.missing == 0
            and summary.blocked == 0
            and (not acm.applies or acm.treatment_commercial_lines_allowed is False)
        )
        # For ACM: commercial_ready means shell can price; treatments stay separately blocked.
        if acm.applies:
            commercial = (
                (acm.shell_registry_missing or 0) == 0
                and (acm.shell_registry_confirmed or 0) > 0
            )
        tech_notes = []
        if summary.total_items == 0:
            tech_notes.append("Nicio linie de rețetă derivabilă pentru acest template.")
        else:
            tech_notes.append(f"{summary.total_items} linii rețetă vizibile (catalog + reguli).")
        if labor_summary and labor_summary.total:
            tech_notes.append(
                f"Manoperă: {labor_summary.technical_ready}/{labor_summary.total} "
                "rețete tehnic pregătite (formula/qty pe template)."
            )
        comm_notes = []
        if summary.missing:
            comm_notes.append(f"{summary.missing} linii cu tarif lipsă în catalog.")
        if labor_summary and labor_summary.missing_rate:
            comm_notes.append(
                f"{labor_summary.missing_rate} rețete manoperă cu tarif central lipsă "
                "(blochează comercial, nu configurația tehnică)."
            )
        if acm.applies:
            comm_notes.append(
                f"ACM shell registry: {acm.shell_registry_confirmed}/"
                f"{acm.shell_registry_missing} (confirmed/missing)."
            )
            if acm.treatment_commercial_lines_allowed is False:
                comm_notes.append(
                    "Tratamente față blocate comercial (treatment_commercial_lines_allowed=false)."
                )
        labor_blocks_commercial = bool(labor_summary and labor_summary.missing_rate)
        return TemplatePricingReadiness(
            technical_ready=bool(technical),
            commercial_ready=bool(commercial)
            and summary.missing == 0
            and not labor_blocks_commercial,
            technical_notes_ro=tech_notes,
            commercial_notes_ro=comm_notes,
            inventory_notes_ro=[
                "Stocul neurmărit nu blochează prețuirea comercială.",
                "Materialele fără cost achiziție rămân vizibile și blocate comercial.",
                "Tariful de manoperă lipsă nu blochează configurația tehnică a produsului.",
            ],
        )
