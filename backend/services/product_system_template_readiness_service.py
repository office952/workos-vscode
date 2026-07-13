from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_materials import Inventory_materials
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from schemas.product_system_template_readiness import (
    CommercialReadinessStatus,
    ExecutionReadinessStatus,
    PricingReadinessStatus,
    ProductSystemReadinessBlocker,
    ProductSystemReadinessDimension,
    ProductSystemTemplateCapabilities,
    ProductSystemTemplateReadiness,
    ReadinessRollup,
    TechnicalReadinessStatus,
)
from services.inventory_materials_admin_service import load_material_cost_dict
from services.pricing_registry_service import TEMPLATE_MATERIAL_VARIANT_EXPANSION
from services.product_readiness_service import ProductReadinessService
from services.template_usage_mode_policy import (
    get_template_usage_mode_policy,
    is_linked_child_allowed_template,
    is_root_offerable_template,
    normalize_template_code,
)
from services.workcenter_rates_service import load_workcenter_rate_dict

TPL_VOLUMETRIC_LETTERS_V2 = "TPL-VOLUMETRIC-LETTERS_v2"
TPL_ACM_BOXED = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
TPL_PREMOUNT = "TPL-METAL-PREMOUNT-STRUCTURE_v1"
TPL_LOGO = "TPL-VOLUMETRIC-LOGO_v1"
TPL_VOLUM_ALUMINIU = "TPL-VOLUM-ALUMINIU_v1"


@dataclass
class TemplateAvailabilityReadinessContext:
    template_code: str
    db_active: bool
    quote_offerable: bool
    runtime_module: bool
    is_parent: bool
    has_modules: bool
    missing_module_codes: list[str] = field(default_factory=list)
    missing_parent_codes: list[str] = field(default_factory=list)
    product_system_role: str = ""
    display_group: str = ""
    owner_decision_required: bool = False


@dataclass
class PricingEvaluationContext:
    material_costs: dict[str, float]
    workcenter_rates: dict[str, float]
    material_rows: dict[str, Inventory_materials]


class ProductSystemTemplateReadinessService:
    """Derives canonical Product System readiness from existing backend truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_pricing_context(self) -> PricingEvaluationContext:
        material_costs = await load_material_cost_dict(self.db)
        workcenter_rates = await load_workcenter_rate_dict(self.db)
        rows = (await self.db.execute(select(Inventory_materials))).scalars().all()
        material_rows = {str(row.code): row for row in rows if row.code}
        return PricingEvaluationContext(
            material_costs=material_costs,
            workcenter_rates=workcenter_rates,
            material_rows=material_rows,
        )

    async def load_dossiers_by_template_id(
        self, template_ids: list[int]
    ) -> dict[int, ProductBlueprintDossier]:
        if not template_ids:
            return {}
        rows = (
            await self.db.execute(
                select(ProductBlueprintDossier).where(
                    ProductBlueprintDossier.template_id.in_(template_ids)
                )
            )
        ).scalars().all()
        return {int(row.template_id): row for row in rows if row.template_id is not None}

    async def build_readiness(
        self,
        *,
        template: Product_templates,
        context: TemplateAvailabilityReadinessContext,
        pricing_context: PricingEvaluationContext,
        dossier: ProductBlueprintDossier | None,
    ) -> tuple[ProductSystemTemplateReadiness, ProductSystemTemplateCapabilities]:
        capabilities = self._derive_capabilities(template, context)
        technical = self._derive_technical(template, context)
        pricing = self._derive_pricing(template, context, pricing_context)
        execution = self._derive_execution(template, context, dossier)
        commercial = self._derive_commercial(template, context, capabilities)
        rollup = self._derive_rollup(
            commercial=commercial,
            technical=technical,
            pricing=pricing,
            execution=execution,
            capabilities=capabilities,
            context=context,
        )
        readiness = ProductSystemTemplateReadiness(
            technical=technical,
            pricing=pricing,
            execution=execution,
            commercial=commercial,
            rollup=rollup,
        )
        return readiness, capabilities

    def _derive_capabilities(
        self,
        template: Product_templates,
        context: TemplateAvailabilityReadinessContext,
    ) -> ProductSystemTemplateCapabilities:
        code = normalize_template_code(template.template_code)
        policy = get_template_usage_mode_policy(code)
        db_active = context.db_active
        root_offerable = bool(policy and policy.root_offerable and db_active)
        linked_child_offerable = bool(
            is_linked_child_allowed_template(code) and db_active
        )
        internal_only = bool(
            (policy and policy.component_only)
            or (policy and policy.candidate_only and not policy.root_offerable)
            or (
                context.runtime_module
                and not (policy and policy.root_offerable)
            )
            or context.product_system_role
            in {"internal_module", "shared_component", "archived_experimental"}
        )
        return ProductSystemTemplateCapabilities(
            root_offerable=root_offerable,
            linked_child_offerable=linked_child_offerable,
            internal_only=internal_only,
        )

    def _derive_technical(
        self,
        template: Product_templates,
        context: TemplateAvailabilityReadinessContext,
    ) -> ProductSystemReadinessDimension:
        blockers: list[ProductSystemReadinessBlocker] = []
        if not context.db_active:
            blockers.append(
                self._blocker(
                    "TEMPLATE_INACTIVE",
                    "technical",
                    "Template inactive in database.",
                    owner="registry",
                    source_code=context.template_code,
                    target_route="/product-system/products",
                )
            )
        if context.missing_module_codes:
            for code in context.missing_module_codes:
                blockers.append(
                    self._blocker(
                        "MISSING_REQUIRED_MODULE",
                        "technical",
                        f"Missing linked module template {code}.",
                        owner="composition",
                        source_code=code,
                        target_route="/product-system/products",
                    )
                )
        if context.missing_parent_codes:
            for code in context.missing_parent_codes:
                blockers.append(
                    self._blocker(
                        "MISSING_PARENT_TEMPLATE",
                        "technical",
                        f"Missing parent template {code}.",
                        owner="composition",
                        source_code=code,
                    )
                )
        if context.is_parent and not context.has_modules:
            blockers.append(
                self._blocker(
                    "INCOMPLETE_COMPOSITION",
                    "technical",
                    "Parent template has no linked modules.",
                    owner="composition",
                    source_code=context.template_code,
                    target_route="/product-system/products",
                )
            )
        components = self._parse_json(template.components_json)
        if components is None and template.components_json:
            blockers.append(
                self._blocker(
                    "INVALID_COMPONENT_CONTRACT",
                    "technical",
                    "components_json is not valid JSON.",
                    owner="registry",
                    source_code=context.template_code,
                )
            )
        status = (
            TechnicalReadinessStatus.TECHNICALLY_READY
            if not blockers
            else TechnicalReadinessStatus.DRAFT
        )
        return ProductSystemReadinessDimension(status=status.value, blockers=blockers)

    def _derive_pricing(
        self,
        template: Product_templates,
        context: TemplateAvailabilityReadinessContext,
        pricing_context: PricingEvaluationContext,
    ) -> ProductSystemReadinessDimension:
        if not context.db_active:
            return ProductSystemReadinessDimension(
                status=PricingReadinessStatus.PRICING_INCOMPLETE.value,
                blockers=[
                    self._blocker(
                        "TEMPLATE_INACTIVE",
                        "pricing",
                        "Inactive templates cannot be pricing-ready.",
                        owner="registry",
                        source_code=context.template_code,
                    )
                ],
            )

        blockers: list[ProductSystemReadinessBlocker] = []
        code = normalize_template_code(template.template_code)
        material_codes = self._material_codes_for_template(template, code)
        for mat_code in sorted(material_codes):
            row = pricing_context.material_rows.get(mat_code)
            cost = pricing_context.material_costs.get(mat_code)
            if cost is None or float(cost) <= 0:
                blockers.append(
                    self._blocker(
                        "MISSING_PRICING_REGISTRY_ENTRY",
                        "pricing",
                        f"Missing commercial price for material {mat_code}.",
                        owner="pricing",
                        source_code=mat_code,
                        target_route="/inventory/pricing",
                    )
                )
                continue
            review = str(getattr(row, "source_review_status", "") or "").lower()
            status = str(getattr(row, "status", "") or "").lower()
            if review in {"needs_review", "draft"} or status in {"needs_review", "draft"}:
                blockers.append(
                    self._blocker(
                        "PRICING_NEEDS_REVIEW",
                        "pricing",
                        f"Material {mat_code} requires owner-approved pricing.",
                        owner="pricing",
                        source_code=mat_code,
                        severity="warning",
                        target_route="/inventory/pricing",
                    )
                )

        workcenter_codes = self._workcenter_codes_for_template(template)
        for wc_code in sorted(workcenter_codes):
            rate = pricing_context.workcenter_rates.get(wc_code)
            resolved_rate = self._resolve_workcenter_rate(rate)
            if resolved_rate is None or resolved_rate <= 0:
                blockers.append(
                    self._blocker(
                        "MISSING_OPERATION_RATE",
                        "pricing",
                        f"Missing commercial operation rate for {wc_code}.",
                        owner="pricing",
                        source_code=wc_code,
                        target_route="/inventory/pricing",
                    )
                )

        blocking = [b for b in blockers if b.severity == "blocking"]
        status = (
            PricingReadinessStatus.PRICING_READY
            if not blocking
            else PricingReadinessStatus.PRICING_INCOMPLETE
        )
        return ProductSystemReadinessDimension(status=status.value, blockers=blockers)

    def _derive_execution(
        self,
        template: Product_templates,
        context: TemplateAvailabilityReadinessContext,
        dossier: ProductBlueprintDossier | None,
    ) -> ProductSystemReadinessDimension:
        blockers: list[ProductSystemReadinessBlocker] = []
        if not context.db_active:
            return ProductSystemReadinessDimension(
                status=ExecutionReadinessStatus.EXECUTION_INCOMPLETE.value,
                blockers=[
                    self._blocker(
                        "TEMPLATE_INACTIVE",
                        "execution",
                        "Inactive templates are not execution-ready.",
                        owner="execution",
                        source_code=context.template_code,
                    )
                ],
            )

        operations = self._parse_json(template.operations_json)
        components = self._parse_json(template.components_json)
        has_operations = isinstance(operations, list) and len(operations) > 0
        has_component_ops = False
        if isinstance(components, list):
            for component in components:
                if isinstance(component, dict) and component.get("operations"):
                    has_component_ops = True
                    break

        if not has_operations and not has_component_ops:
            blockers.append(
                self._blocker(
                    "MISSING_CANONICAL_OPERATION",
                    "execution",
                    "No canonical operations defined on template.",
                    owner="execution",
                    source_code=context.template_code,
                    target_route="/product-system/products",
                )
            )

        code = normalize_template_code(template.template_code)
        if code in {
            normalize_template_code(TPL_VOLUMETRIC_LETTERS_V2),
            normalize_template_code(TPL_ACM_BOXED),
        }:
            if not has_operations and not has_component_ops:
                blockers.append(
                    self._blocker(
                        "MISSING_TASK_RULE",
                        "execution",
                        "Canonical template operations/task mapping incomplete.",
                        owner="execution",
                        source_code=context.template_code,
                        target_route="/product-system/products",
                    )
                )

        if context.runtime_module and not context.quote_offerable:
            if not has_operations and not has_component_ops and code == normalize_template_code(TPL_PREMOUNT):
                blockers.append(
                    self._blocker(
                        "MISSING_TASK_RULE",
                        "execution",
                        "Premount structure lacks execution task mapping.",
                        owner="execution",
                        source_code=context.template_code,
                    )
                )

        status = (
            ExecutionReadinessStatus.EXECUTION_READY
            if not blockers
            else ExecutionReadinessStatus.EXECUTION_INCOMPLETE
        )
        return ProductSystemReadinessDimension(status=status.value, blockers=blockers)

    def _derive_commercial(
        self,
        template: Product_templates,
        context: TemplateAvailabilityReadinessContext,
        capabilities: ProductSystemTemplateCapabilities,
    ) -> ProductSystemReadinessDimension:
        blockers: list[ProductSystemReadinessBlocker] = []
        code = normalize_template_code(template.template_code)
        policy = get_template_usage_mode_policy(code)

        if not context.db_active or context.display_group == "archived_experimental":
            blockers.append(
                self._blocker(
                    "TEMPLATE_DEPRECATED",
                    "commercial",
                    "Template is inactive or archived.",
                    owner="policy",
                    source_code=context.template_code,
                )
            )
            return ProductSystemReadinessDimension(
                status=CommercialReadinessStatus.DEPRECATED.value,
                blockers=blockers,
            )

        if policy and policy.owner_go_required and not policy.root_offerable:
            blockers.append(
                self._blocker(
                    "OWNER_GO_REQUIRED",
                    "commercial",
                    "Root offerability blocked pending owner decision.",
                    owner="policy",
                    source_code=context.template_code,
                    target_route="/product-system/advanced",
                )
            )
            return ProductSystemReadinessDimension(
                status=CommercialReadinessStatus.INTERNAL_ONLY.value,
                blockers=blockers,
            )

        if context.quote_offerable and is_root_offerable_template(code):
            return ProductSystemReadinessDimension(
                status=CommercialReadinessStatus.OFFERABLE.value,
                blockers=blockers,
            )

        if capabilities.internal_only or (policy and policy.component_only):
            if context.runtime_module:
                blockers.append(
                    self._blocker(
                        "INTERNAL_MODULE_ONLY",
                        "commercial",
                        "Internal module is not root-offerable.",
                        owner="policy",
                        source_code=context.template_code,
                    )
                )
            return ProductSystemReadinessDimension(
                status=CommercialReadinessStatus.INTERNAL_ONLY.value,
                blockers=blockers,
            )

        blockers.append(
            self._blocker(
                "NOT_ROOT_OFFERABLE",
                "commercial",
                "Template is not in root offerable policy.",
                owner="policy",
                source_code=context.template_code,
            )
        )
        return ProductSystemReadinessDimension(
            status=CommercialReadinessStatus.INTERNAL_ONLY.value,
            blockers=blockers,
        )

    def _derive_rollup(
        self,
        *,
        commercial: ProductSystemReadinessDimension,
        technical: ProductSystemReadinessDimension,
        pricing: ProductSystemReadinessDimension,
        execution: ProductSystemReadinessDimension,
        capabilities: ProductSystemTemplateCapabilities,
        context: TemplateAvailabilityReadinessContext,
    ) -> ReadinessRollup:
        if commercial.status == CommercialReadinessStatus.DEPRECATED.value:
            return ReadinessRollup.DEPRECATED
        if commercial.status == CommercialReadinessStatus.INTERNAL_ONLY.value:
            if any(blocker.code == "OWNER_GO_REQUIRED" for blocker in commercial.blockers):
                return ReadinessRollup.INTERNAL
            if (
                capabilities.linked_child_offerable
                and not capabilities.root_offerable
                and technical.status == TechnicalReadinessStatus.TECHNICALLY_READY.value
                and any(
                    dim.status
                    in {
                        PricingReadinessStatus.PRICING_INCOMPLETE.value,
                        ExecutionReadinessStatus.EXECUTION_INCOMPLETE.value,
                    }
                    for dim in (pricing, execution)
                )
            ):
                return ReadinessRollup.PARTIALLY_READY
            return ReadinessRollup.INTERNAL

        if commercial.status == CommercialReadinessStatus.OFFERABLE.value:
            ready = (
                technical.status == TechnicalReadinessStatus.TECHNICALLY_READY.value
                and pricing.status == PricingReadinessStatus.PRICING_READY.value
                and execution.status == ExecutionReadinessStatus.EXECUTION_READY.value
            )
            if ready:
                return ReadinessRollup.READY
            return ReadinessRollup.BLOCKED

        return ReadinessRollup.BLOCKED

    @staticmethod
    def _blocker(
        code: str,
        dimension: str,
        message: str,
        *,
        owner: str,
        source_code: str | None = None,
        severity: str = "blocking",
        target_route: str | None = None,
    ) -> ProductSystemReadinessBlocker:
        return ProductSystemReadinessBlocker(
            code=code,
            dimension=dimension,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            owner=owner,
            message=message,
            source_code=source_code,
            target_route=target_route,
        )

    @staticmethod
    def _resolve_workcenter_rate(rate: Any) -> float | None:
        if rate is None:
            return None
        if isinstance(rate, (int, float)):
            return float(rate)
        if isinstance(rate, dict):
            for key in ("rate_per_hour", "rate_per_linear_meter", "rate"):
                value = rate.get(key)
                if value is not None:
                    return float(value)
        return None

    @staticmethod
    def _parse_json(raw: str | None) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def _material_codes_for_template(
        self, template: Product_templates, normalized_code: str
    ) -> set[str]:
        codes: set[str] = set()
        for source in (
            self._parse_json(template.required_materials_json),
            self._parse_json(template.components_json),
        ):
            codes.update(ProductReadinessService._extract_material_codes(source))
            if isinstance(source, list):
                codes.update(
                    ProductReadinessService._extract_material_codes_from_components(source)
                )
        expansion = TEMPLATE_MATERIAL_VARIANT_EXPANSION.get(
            str(template.template_code or "").strip(),
            TEMPLATE_MATERIAL_VARIANT_EXPANSION.get(normalized_code, {}),
        )
        for variants in expansion.values():
            codes.update(variants)
        return {code for code in codes if code}

    @staticmethod
    def _workcenter_codes_for_template(template: Product_templates) -> set[str]:
        from services.pricing_registry_service import _extract_workcenter_codes_from_components

        codes: set[str] = set()
        components = ProductSystemTemplateReadinessService._parse_json(
            template.components_json
        )
        codes.update(_extract_workcenter_codes_from_components(components))
        operations = ProductSystemTemplateReadinessService._parse_json(
            template.operations_json
        )
        if isinstance(operations, list):
            for op in operations:
                if isinstance(op, dict):
                    wc = str(op.get("workcenter") or op.get("workcenter_code") or "").strip()
                    if wc:
                        codes.add(wc)
        return codes
