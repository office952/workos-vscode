"""
QuoteOrchestrator — commercial orchestration only.

Canonical rules:
  - Does NOT contain cost formulas.
  - Does NOT modify ProductDefinition or CostResult.
  - Flow:
      1. Receive user_config + product_template.
      2. Ask ProductSystemService for ProductDefinition.
      3. If invalid -> Quote = blocked.
      4. Otherwise ask CostEngineService for CostResult.
      5. If invalid -> Quote = blocked.
      6. Else apply commercial rules (margin, discount, vat) and mark "priced".
  - Produces QuoteCalculationSnapshot.

Sprint #10 — Flow Hardening (Option B: strict validation, no new contracts):
  ProductDefinition is built EXCLUSIVELY at quote-time (here). Intake stays
  pure CRUD and does NOT build a ProductDefinition. The Request -> Product
  Definition link is made explicit by contract-level validation: missing
  `family`, missing `quantity`, or missing required `dimensions` MUST cause
  a `blocked` snapshot with `product_invalid:<field>` reasons, which the
  `/price` router maps to HTTP 422. No silent fallbacks, no new DTOs.

Sprint #17 — Quote Orchestrator v2 (component-aware integration, additive):
  If the product template carries a HIERARCHICAL components_json (Sprint #15
  shape where components own their own `materials[]` and `operations[]`),
  AND the caller provided at least one explicit rate context
  (material_rates or workcenter_rates), the orchestrator delegates cost
  computation to `build_execution_layers_from_components` (CostEngine v2,
  Sprint #16) and persists the per-component breakdown on the returned
  snapshot.

  Backward compatibility (absolutely non-negotiable):
    - Templates with a FLAT / LEGACY `components_json` (null, string[], or
      objects without nested materials/operations) keep going through the
      existing `CostEngineService.calculate()` path — byte-for-byte
      identical behaviour as pre-Sprint-17.
    - If v2 rates context is NOT provided, we do NOT auto-invent rates and
      we do NOT route through v2. We fall back to the legacy engine so no
      existing caller silently changes behaviour.
    - The `QuoteCalculationSnapshot` DATACLASS is NOT modified (contract
      frozen). v2 data is exposed as DYNAMIC attributes on the returned
      instance: `component_breakdown`, `cost_warnings`, `component_breakdown_json`,
      `cost_engine_version`. Callers that don't know about them are
      unaffected (`asdict()` only serializes declared dataclass fields).

  Strictly scoped: cost_engine_service.py, routers, Orders, Execution,
  ProductSystem, and frontend are NOT modified in this sprint.
"""

from __future__ import annotations

import json as _json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from data_models.product_contracts import (
    CostLine,
    CostRequest,
    CostResult,
    CostValidation,
    PricingContext,
    ProductDefinition,
    QuoteCalculationSnapshot,
    QuotePrice,
    QuotePricing,
)
from services.cost_engine_service import (
    BLK18_CONFIG_FALLBACK_USED,
    BLK18_MACHINE_RATE_RESOLUTION_FAILED,
    BLK18_MATERIAL_COST_NOT_IN_REGISTRY,
    BLK18_REGISTRY_RATE_OVERRIDDEN,
    BLK18_WORKCENTER_RATE_NOT_IN_REGISTRY,
    ComponentCostContext,
    CostEngineService,
    ERR_MATERIAL_RATE_MISSING,
    ERR_WORKCENTER_RATE_MISSING,
    WARN_COMPONENT_EMPTY,
    _detect_hierarchical,
    _parse_json_field,
    build_execution_layers_from_components,
)
from services.product_system_service import ProductSystemService
from services.aggregate_cost_bom_price_bridge import (
    AggregatePriceContext,
    build_synthetic_hierarchical_template,
    collect_aggregate_pricing_blockers,
    is_aggregate_cost_template,
)

logger = logging.getLogger(__name__)


class QuoteOrchestrator:
    def __init__(
        self,
        product_service: Optional[ProductSystemService] = None,
        cost_engine: Optional[CostEngineService] = None,
        material_rates: Optional[Dict[str, float]] = None,
        workcenter_rates: Optional[Dict[str, Any]] = None,
        base_currency: Optional[str] = None,
        material_currencies: Optional[Dict[str, str]] = None,
        workcenter_currencies: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
          product_service: ProductSystemService (as before).
          cost_engine:     Legacy CostEngine used for flat/legacy templates
                           (or when v2 rates are not provided). Unchanged
                           pre-sprint behaviour for every existing caller.
          material_rates:  OPTIONAL explicit rates for CostEngine v2
                           ({material_code: unit_cost}). If omitted, v2
                           branch is disabled and we fall back to legacy.
          workcenter_rates: OPTIONAL explicit rates for CostEngine v2
                           ({workcenter: rate_per_hour}). If omitted, v2
                           branch is disabled and we fall back to legacy.

        Backward compatibility: the old two-argument form
        `QuoteOrchestrator(product_service=..., cost_engine=...)` still
        works identically — the v2 branch simply never activates.
        """
        self.product_service = product_service or ProductSystemService()
        self.cost_engine = cost_engine or CostEngineService()
        self.material_rates: Dict[str, float] = dict(material_rates or {})
        self.workcenter_rates: Dict[str, Any] = dict(workcenter_rates or {})
        self.base_currency: Optional[str] = (
            str(base_currency).strip().upper() if base_currency else None
        )
        self.material_currencies: Dict[str, str] = dict(material_currencies or {})
        self.workcenter_currencies: Dict[str, str] = dict(workcenter_currencies or {})

    # ------------------------------------------------------------------
    # BLK-18 — Async factory that auto-loads rates from registries
    # ------------------------------------------------------------------
    @classmethod
    async def create_with_registry(
        cls,
        db: AsyncSession,
        *,
        material_rates: Optional[Dict[str, float]] = None,
        workcenter_rates: Optional[Dict[str, Any]] = None,
        product_service: Optional[ProductSystemService] = None,
        cost_engine: Optional[CostEngineService] = None,
    ) -> "QuoteOrchestrator":
        """Factory that auto-loads rates from live registries.

        BLK-18 wiring: loads material costs and workcenter rates from the
        canonical bridge functions. Caller-provided rates OVERRIDE registry
        rates (merge semantics: caller wins on key collision).

        This factory replaces the ad-hoc inline rate loading that was
        previously done in the quotes router (Sprint #21.4).

        Args:
            db: Active async database session.
            material_rates: Optional caller-provided overrides.
            workcenter_rates: Optional caller-provided overrides.
            product_service: Optional ProductSystemService instance.
            cost_engine: Optional CostEngineService instance.

        Returns:
            Fully initialized QuoteOrchestrator with registry rates merged.
        """
        from services.cost_engine_config import load_base_currency
        from services.inventory_materials_admin_service import (
            load_material_cost_dict,
            load_material_pricing_dict,
        )
        from services.workcenter_rates_service import (
            load_workcenter_rate_dict,
            load_workcenter_rate_pricing_dict,
        )

        try:
            base_currency = await load_base_currency(db)
        except Exception as exc:
            logger.warning("BLK-18: load_base_currency failed: %s", exc)
            base_currency = "RON"

        # Load from registries (empty dict on failure — never breaks quoting)
        registry_material_pricing: Dict[str, Dict[str, Any]] = {}
        try:
            registry_material_pricing = await load_material_pricing_dict(db)
        except Exception as exc:
            logger.warning("BLK-18: load_material_pricing_dict failed: %s", exc)

        try:
            registry_material_rates = await load_material_cost_dict(db)
        except Exception as exc:
            logger.warning("BLK-18: load_material_cost_dict failed: %s", exc)
            registry_material_rates = {}

        registry_workcenter_pricing: Dict[str, Dict[str, Any]] = {}
        try:
            registry_workcenter_rates = await load_workcenter_rate_dict(db)
        except Exception as exc:
            logger.warning("BLK-18: load_workcenter_rate_dict failed: %s", exc)
            registry_workcenter_rates = {}

        try:
            registry_workcenter_pricing = await load_workcenter_rate_pricing_dict(db)
        except Exception as exc:
            logger.warning("BLK-18: load_workcenter_rate_pricing_dict failed: %s", exc)

        # Merge: registry base, caller overrides win
        merged_material = {**registry_material_rates, **(material_rates or {})}
        merged_workcenter = {**registry_workcenter_rates, **(workcenter_rates or {})}

        merged_material_currencies = {
            code: str(row.get("currency") or base_currency).strip().upper()
            for code, row in registry_material_pricing.items()
        }
        merged_workcenter_currencies = {
            code: str(row.get("currency") or base_currency).strip().upper()
            for code, row in registry_workcenter_pricing.items()
        }
        for code in material_rates or {}:
            merged_material_currencies[code] = base_currency
        for code in workcenter_rates or {}:
            merged_workcenter_currencies[code] = base_currency

        logger.info(
            "BLK-18: create_with_registry loaded %d material rates, %d workcenter rates "
            "(caller overrides: %d material, %d workcenter)",
            len(registry_material_rates),
            len(registry_workcenter_rates),
            len(material_rates or {}),
            len(workcenter_rates or {}),
        )

        return cls(
            product_service=product_service,
            cost_engine=cost_engine,
            material_rates=merged_material,
            workcenter_rates=merged_workcenter,
            base_currency=base_currency,
            material_currencies=merged_material_currencies,
            workcenter_currencies=merged_workcenter_currencies,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build_snapshot(
        self,
        product_template: Optional[Dict[str, Any]],
        user_config: Optional[Dict[str, Any]] = None,
        pricing: Optional[QuotePricing] = None,
        pricing_context: Optional[PricingContext] = None,
        quote_input: Optional[Dict[str, Any]] = None,
        aggregate_price_context: AggregatePriceContext | None = None,
    ) -> QuoteCalculationSnapshot:
        """Build a pricing snapshot for the given template + user_config.

        Sprint #21.4 — ``quote_input`` is an OPTIONAL per-quote-instance
        payload (e.g. ``personalization_path_length_mm``, ``led_count``, ...)
        consumed by formula-based lines in the v2 (component-aware) engine.
        When provided, it is threaded verbatim into
        ``ComponentCostContext.quote_input`` inside ``_build_snapshot_v2``.

        Backwards compatibility: omitting ``quote_input`` (or passing
        ``None`` / ``{}``) preserves pre-Sprint-21.4 behaviour byte-for-byte.
        The v1 legacy branch does not consume ``quote_input`` at all — it
        is silently ignored there because v1 templates have no
        formula-based lines.
        """
        pricing = pricing or QuotePricing()
        pricing_context = pricing_context or PricingContext()
        if self.base_currency:
            pricing_context = PricingContext(
                currency=self.base_currency,
                location=pricing_context.location,
                overhead_profile_id=pricing_context.overhead_profile_id,
            )

        # Step 1: Product definition (unchanged)
        pd: ProductDefinition = self.product_service.build_product_definition(
            product_template=product_template,
            user_config=user_config,
        )

        # Step 2: Route — v2 (component-aware) OR v1 (legacy flat).
        #
        # Sprint #27 — Strict Contract Hardening:
        #   Even on the v2 branch, a missing/invalid PRODUCT-LEVEL field
        #   (quantity, dimensions, product_type) MUST block the quote with
        #   `product_invalid:<field>`. These fields are not rebuildable by
        #   CostEngine v2 — if the user did not provide a quantity or a
        #   dimension, the commercial side cannot price the quote, period.
        #
        #   What v2 still takes over (vs pre-Sprint-27 behaviour) is the
        #   TEMPLATE-LEVEL validation: `material_ref`, `layers`, etc. These
        #   are inferred from the template, not the user config, and the
        #   v2 engine already surfaces its own precise errors for them.
        use_v2 = self._should_use_v2(product_template)

        # Which missing fields are "product-level" (user-provided), i.e. the
        # ones the v2 engine cannot repair by introspecting the template.
        PRODUCT_LEVEL_MISSING = {"quantity", "dimensions", "product_type", "product_template"}
        product_level_missing = [
            f for f in pd.validation.missing_fields if f in PRODUCT_LEVEL_MISSING
        ]

        if not pd.validation.is_valid and (not use_v2 or product_level_missing):
            # v1 branch: ALL missing_fields block.
            # v2 branch: only PRODUCT-LEVEL missing fields block here; the
            #            v2 engine will report its own TEMPLATE-LEVEL errors.
            reasons_source = (
                pd.validation.missing_fields if not use_v2 else product_level_missing
            )
            snap = QuoteCalculationSnapshot(
                product_definition=pd,
                pricing=pricing,
                status="blocked",
                blocked_reasons=[f"product_invalid:{f}" for f in reasons_source],
            )
            self._attach_v2_extras(
                snap,
                breakdown=None,
                warnings=None,
                version="v2" if use_v2 else "v1",
            )
            return snap

        template_code = str(
            (product_template or {}).get("template_code")
            or (product_template or {}).get("product_id")
            or ""
        )

        if use_v2 and is_aggregate_cost_template(template_code):
            if aggregate_price_context is None:
                snap = QuoteCalculationSnapshot(
                    product_definition=pd,
                    pricing=pricing,
                    status="blocked",
                    blocked_reasons=["aggregate_bom:context_not_prepared"],
                )
                self._attach_v2_extras(
                    snap,
                    breakdown=None,
                    warnings=None,
                    version="v2_aggregate",
                )
                return snap
            return self._build_snapshot_v2_aggregate(
                product_template=product_template or {},
                pd=pd,
                pricing=pricing,
                pricing_context=pricing_context,
                quote_input=quote_input,
                aggregate_price_context=aggregate_price_context,
            )

        if use_v2:
            return self._build_snapshot_v2(
                product_template=product_template or {},
                user_config=user_config or {},
                pd=pd,
                pricing=pricing,
                pricing_context=pricing_context,
                quote_input=quote_input,
            )
        return self._build_snapshot_v1(
            pd=pd,
            pricing=pricing,
            pricing_context=pricing_context,
        )

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def _should_use_v2(self, product_template: Optional[Dict[str, Any]]) -> bool:
        """True iff:
          - the template can be priced by CostEngine v2 (hierarchical or flat legacy), AND
          - the orchestrator was constructed with at least one rate registry.

        Flat templates with only ``operations_json`` / ``required_materials_json``
        (e.g. TPL-VOLUMETRIC-LETTERS_v2) must use v2's ``comp_flat_legacy`` branch."""
        if not product_template:
            return False
        has_rates = bool(self.material_rates) or bool(self.workcenter_rates)
        if not has_rates:
            return False
        parsed = _parse_json_field(product_template.get("components_json"))
        if _detect_hierarchical(parsed):
            return True
        ops = _parse_json_field(product_template.get("operations_json")) or []
        mats = _parse_json_field(product_template.get("required_materials_json")) or []
        return bool(ops or mats)

    # ------------------------------------------------------------------
    # v1 — legacy flat (pre-Sprint-17 behaviour, byte-for-byte)
    # ------------------------------------------------------------------
    def _cost_engine_for_v1(self) -> CostEngineService:
        """Use registry-backed material lookup on v1 templates when rates exist."""
        from services.cost_engine_service import CostEngineWithMaterialRates

        registry_rates = dict(self.material_rates or {})
        if isinstance(self.cost_engine, CostEngineWithMaterialRates):
            registry_rates = {**registry_rates, **self.cost_engine.material_unit_costs}
            return CostEngineWithMaterialRates(registry_rates)
        if registry_rates:
            return CostEngineWithMaterialRates(registry_rates)
        return self.cost_engine

    def _build_snapshot_v1(
        self,
        pd: ProductDefinition,
        pricing: QuotePricing,
        pricing_context: PricingContext,
    ) -> QuoteCalculationSnapshot:
        cost_result = self._cost_engine_for_v1().calculate(
            CostRequest(product_definition=pd, pricing_context=pricing_context)
        )

        if not cost_result.is_valid:
            snap = QuoteCalculationSnapshot(
                product_definition=pd,
                cost_result=cost_result,
                pricing=pricing,
                status="blocked",
                blocked_reasons=[
                    f"cost_invalid:{m}" for m in cost_result.validation.missing_cost_data
                ],
            )
            self._attach_v2_extras(snap, breakdown=None, warnings=None, version="v1")
            return snap

        price = self._apply_commercial(cost_result.total_cost, pricing)
        snap = QuoteCalculationSnapshot(
            product_definition=pd,
            cost_result=cost_result,
            pricing=pricing,
            price=price,
            status="priced",
            blocked_reasons=[],
        )
        self._attach_v2_extras(snap, breakdown=None, warnings=None, version="v1")
        return snap

    # ------------------------------------------------------------------
    # v2 — component-aware (Sprint #16 engine + breakdown persistence)
    # ------------------------------------------------------------------
    def _build_snapshot_v2(
        self,
        product_template: Dict[str, Any],
        user_config: Dict[str, Any],
        pd: ProductDefinition,
        pricing: QuotePricing,
        pricing_context: PricingContext,
        quote_input: Optional[Dict[str, Any]] = None,
    ) -> QuoteCalculationSnapshot:
        # Sprint #27 — no silent fallback. `pd.validation.is_valid` has
        # already been checked for product-level fields in `build_snapshot`,
        # so `pd.quantity` is guaranteed > 0 here. We still defensively
        # guard against an unexpected 0/negative value (e.g. a caller that
        # constructs a ProductDefinition directly bypassing build_snapshot).
        qty = int(pd.quantity or 0)
        if qty <= 0:
            # This would only hit if a caller bypassed build_snapshot with
            # an invalid PD. We mirror the product_invalid:quantity contract
            # rather than silently clamping to 1.
            cost_result = self._build_cost_result_from_v2(
                v2={
                    "is_valid": False,
                    "total_material_cost": 0.0,
                    "total_operation_cost": 0.0,
                    "total_cost": 0.0,
                    "components": [],
                    "errors": [],
                    "warnings": [],
                },
                currency=pricing_context.currency,
            )
            snap = QuoteCalculationSnapshot(
                product_definition=pd,
                cost_result=cost_result,
                pricing=pricing,
                status="blocked",
                blocked_reasons=["product_invalid:quantity"],
            )
            self._attach_v2_extras(snap, breakdown=None, warnings=None, version="v2")
            return snap

        # Sprint #21.4 — thread the per-quote-instance ``quote_input`` into
        # the CostEngine v2 context so formula-based lines declaring
        # ``requires_quote_input`` can resolve without monkey-patching.
        # Defensive copy so the engine cannot mutate the caller's dict.
        ctx_quote_input: Dict[str, Any] = dict(quote_input or {})

        from services.acm_bond_material_rate_resolver import (
            resolve_acm_bond_panel_material_rate,
        )
        from services.volumetric_material_rate_resolver import (
            resolve_volumetric_material_rates_with_trace,
        )

        template_code = str(product_template.get("template_code") or "")
        resolved_material_rates, material_resolution_trace = (
            resolve_volumetric_material_rates_with_trace(
                self.material_rates,
                ctx_quote_input,
                template_code=template_code or None,
            )
        )
        acm_resolution = resolve_acm_bond_panel_material_rate(
            resolved_material_rates,
            ctx_quote_input,
            template_code=template_code or None,
        )
        if (
            acm_resolution.resolution_status == "resolved"
            and acm_resolution.unit_cost is not None
        ):
            resolved_material_rates = dict(resolved_material_rates)
            resolved_material_rates["MAT-ACM-BOND-PANEL"] = acm_resolution.unit_cost

        ctx = ComponentCostContext(
            material_rates=resolved_material_rates,
            workcenter_rates=dict(self.workcenter_rates),
            quantity=qty,
            quote_input=ctx_quote_input,
            base_currency=self.base_currency or pricing_context.currency,
            material_currencies=dict(self.material_currencies),
            workcenter_currencies=dict(self.workcenter_currencies),
        )

        v2 = build_execution_layers_from_components(product_template, ctx)
        resolution_trace_payload = material_resolution_trace.to_dict()

        # Build a legacy-shaped CostResult so downstream code (orders,
        # commercial transform, snapshot serialization) stays compatible.
        cost_result = self._build_cost_result_from_v2(
            v2=v2,
            currency=pricing_context.currency,
        )

        if not v2["is_valid"]:
            blocked_reasons = [
                self._format_v2_error(err) for err in v2["errors"]
            ]
            snap = QuoteCalculationSnapshot(
                product_definition=pd,
                cost_result=cost_result,
                pricing=pricing,
                status="blocked",
                blocked_reasons=blocked_reasons,
            )
            self._attach_v2_extras(
                snap,
                breakdown=v2.get("components", []),
                warnings=v2.get("warnings", []),
                version="v2",
            )
            setattr(snap, "material_rate_resolution_trace", resolution_trace_payload)
            return snap

        captured_warnings = self._volumetric_captured_unpriced_warnings(
            template_code, ctx_quote_input
        )
        if captured_warnings:
            cost_result = self._append_cost_validation_warnings(
                cost_result, captured_warnings
            )

        price = self._apply_commercial(cost_result.total_cost, pricing)
        snap = QuoteCalculationSnapshot(
            product_definition=pd,
            cost_result=cost_result,
            pricing=pricing,
            price=price,
            status="priced",
            blocked_reasons=[],
        )
        self._attach_v2_extras(
            snap,
            breakdown=v2.get("components", []),
            warnings=v2.get("warnings", []),
            version="v2",
        )
        setattr(snap, "material_rate_resolution_trace", resolution_trace_payload)
        return snap

    def _build_snapshot_v2_aggregate(
        self,
        *,
        product_template: Dict[str, Any],
        pd: ProductDefinition,
        pricing: QuotePricing,
        pricing_context: PricingContext,
        quote_input: Optional[Dict[str, Any]] = None,
        aggregate_price_context: AggregatePriceContext,
    ) -> QuoteCalculationSnapshot:
        """Step 7C — aggregate-expanded BOM as structural cost source for volumetric v2."""
        qty = int(pd.quantity or 0)
        if qty <= 0:
            cost_result = self._build_cost_result_from_v2(
                v2={
                    "is_valid": False,
                    "total_material_cost": 0.0,
                    "total_operation_cost": 0.0,
                    "total_cost": 0.0,
                    "components": [],
                    "errors": [],
                    "warnings": [],
                },
                currency=pricing_context.currency,
            )
            snap = QuoteCalculationSnapshot(
                product_definition=pd,
                cost_result=cost_result,
                pricing=pricing,
                status="blocked",
                blocked_reasons=["product_invalid:quantity"],
            )
            self._attach_v2_extras(snap, breakdown=None, warnings=None, version="v2_aggregate")
            return snap

        bom = aggregate_price_context.aggregate_cost_bom
        aggregate_blockers = collect_aggregate_pricing_blockers(bom)
        if aggregate_blockers:
            cost_result = self._build_cost_result_from_v2(
                v2={
                    "is_valid": False,
                    "total_material_cost": 0.0,
                    "total_operation_cost": 0.0,
                    "total_cost": 0.0,
                    "components": [],
                    "errors": [],
                    "warnings": [],
                },
                currency=pricing_context.currency,
            )
            snap = QuoteCalculationSnapshot(
                product_definition=pd,
                cost_result=cost_result,
                pricing=pricing,
                status="blocked",
                blocked_reasons=aggregate_blockers,
            )
            self._attach_v2_extras(
                snap,
                breakdown=None,
                warnings=[{"kind": "AGGREGATE_BOM", "detail": r} for r in aggregate_blockers],
                version="v2_aggregate",
            )
            setattr(snap, "aggregate_cost_bom_status", bom.bom_status)
            setattr(snap, "aggregate_cost_source", True)
            return snap

        ctx_quote_input: Dict[str, Any] = dict(quote_input or {})

        from services.acm_bond_material_rate_resolver import resolve_acm_bond_panel_material_rate
        from services.volumetric_material_rate_resolver import resolve_volumetric_material_rates_with_trace

        template_code = aggregate_price_context.template_code
        resolved_material_rates, material_resolution_trace = resolve_volumetric_material_rates_with_trace(
            self.material_rates,
            ctx_quote_input,
            template_code=template_code or None,
        )
        acm_resolution = resolve_acm_bond_panel_material_rate(
            resolved_material_rates,
            ctx_quote_input,
            template_code=template_code or None,
        )
        if acm_resolution.resolution_status == "resolved" and acm_resolution.unit_cost is not None:
            resolved_material_rates = dict(resolved_material_rates)
            resolved_material_rates["MAT-ACM-BOND-PANEL"] = acm_resolution.unit_cost

        ctx = ComponentCostContext(
            material_rates=resolved_material_rates,
            workcenter_rates=dict(self.workcenter_rates),
            quantity=qty,
            quote_input=ctx_quote_input,
            base_currency=self.base_currency or pricing_context.currency,
            material_currencies=dict(self.material_currencies),
            workcenter_currencies=dict(self.workcenter_currencies),
        )

        synthetic_template = build_synthetic_hierarchical_template(aggregate_price_context)
        v2 = build_execution_layers_from_components(synthetic_template, ctx)
        v2["source"] = "aggregate_expanded"
        resolution_trace_payload = material_resolution_trace.to_dict()

        component_ids = [c.get("component_id") for c in v2.get("components", [])]
        if "comp_flat_legacy" in component_ids:
            blocked = ["aggregate_bom:comp_flat_legacy_leaked"]
            cost_result = self._build_cost_result_from_v2(
                v2={**v2, "is_valid": False},
                currency=pricing_context.currency,
            )
            snap = QuoteCalculationSnapshot(
                product_definition=pd,
                cost_result=cost_result,
                pricing=pricing,
                status="blocked",
                blocked_reasons=blocked,
            )
            self._attach_v2_extras(snap, breakdown=v2.get("components"), warnings=v2.get("warnings"), version="v2_aggregate")
            setattr(snap, "aggregate_cost_source", True)
            return snap

        cost_result = self._build_cost_result_from_v2(
            v2=v2,
            currency=pricing_context.currency,
        )

        if not v2["is_valid"]:
            blocked_reasons = [self._format_v2_error(err) for err in v2["errors"]]
            blocked_reasons.extend(aggregate_blockers)
            snap = QuoteCalculationSnapshot(
                product_definition=pd,
                cost_result=cost_result,
                pricing=pricing,
                status="blocked",
                blocked_reasons=blocked_reasons,
            )
            self._attach_v2_extras(
                snap,
                breakdown=v2.get("components", []),
                warnings=v2.get("warnings", []),
                version="v2_aggregate",
            )
            setattr(snap, "material_rate_resolution_trace", resolution_trace_payload)
            setattr(snap, "aggregate_cost_bom_status", bom.bom_status)
            setattr(snap, "aggregate_cost_source", True)
            return snap

        if float(v2.get("total_cost") or 0.0) <= 0.0:
            snap = QuoteCalculationSnapshot(
                product_definition=pd,
                cost_result=cost_result,
                pricing=pricing,
                status="blocked",
                blocked_reasons=["aggregate_bom:zero_total_cost"],
            )
            self._attach_v2_extras(
                snap,
                breakdown=v2.get("components", []),
                warnings=v2.get("warnings", []),
                version="v2_aggregate",
            )
            setattr(snap, "aggregate_cost_source", True)
            return snap

        captured_warnings = self._volumetric_captured_unpriced_warnings(
            template_code, ctx_quote_input
        )
        if captured_warnings:
            cost_result = self._append_cost_validation_warnings(cost_result, captured_warnings)

        price = self._apply_commercial(cost_result.total_cost, pricing)
        snap = QuoteCalculationSnapshot(
            product_definition=pd,
            cost_result=cost_result,
            pricing=pricing,
            price=price,
            status="priced",
            blocked_reasons=[],
        )
        self._attach_v2_extras(
            snap,
            breakdown=v2.get("components", []),
            warnings=v2.get("warnings", []),
            version="v2_aggregate",
        )
        setattr(snap, "material_rate_resolution_trace", resolution_trace_payload)
        setattr(snap, "aggregate_cost_bom_status", bom.bom_status)
        setattr(snap, "aggregate_cost_source", True)
        setattr(snap, "aggregate_cost_line_keys", sorted(
            f"material:{m.resolved_material_code or m.material_code}" for m in bom.costable_materials
        ) + sorted(f"operation:{o.operation_code}" for o in bom.costable_operations))
        return snap

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _volumetric_captured_unpriced_warnings(
        template_code: str,
        quote_input: Dict[str, Any],
    ) -> list[str]:
        from services.volumetric_quote_input_policy import (
            collect_volumetric_captured_unpriced_warnings,
        )

        return collect_volumetric_captured_unpriced_warnings(
            template_code, quote_input
        )

    @staticmethod
    def _append_cost_validation_warnings(
        cost_result: CostResult,
        extra_warnings: list[str],
    ) -> CostResult:
        if not extra_warnings:
            return cost_result
        validation = cost_result.validation
        merged = list(validation.warnings or []) + list(extra_warnings)
        return CostResult(
            is_valid=cost_result.is_valid,
            currency=cost_result.currency,
            materials_cost=cost_result.materials_cost,
            labour_cost=cost_result.labour_cost,
            machine_cost=cost_result.machine_cost,
            external_cost=cost_result.external_cost,
            overhead_cost=cost_result.overhead_cost,
            total_cost=cost_result.total_cost,
            estimated_time_minutes=cost_result.estimated_time_minutes,
            breakdown=cost_result.breakdown,
            validation=CostValidation(
                missing_cost_data=list(validation.missing_cost_data or []),
                warnings=merged,
            ),
        )

    @staticmethod
    def _format_v2_error(err: Dict[str, Any]) -> str:
        """Map v2 engine error dicts to the canonical `cost_invalid:<kind>@<path>`
        reason strings consumed by the /price router (HTTP 422 detail).

        Keeping the `cost_invalid:` prefix preserves compatibility with the
        router and with tests that assert `r.startswith("cost_invalid:")`.
        """
        kind = str(err.get("kind", "COST_ERROR"))
        path = str(err.get("path", ""))
        detail = str(err.get("detail", ""))
        if path:
            return f"cost_invalid:{kind}@{path}:{detail}" if detail else f"cost_invalid:{kind}@{path}"
        return f"cost_invalid:{kind}:{detail}" if detail else f"cost_invalid:{kind}"

    @staticmethod
    def _build_cost_result_from_v2(v2: Dict[str, Any], currency: str) -> CostResult:
        """Translate v2 engine output into a legacy-shape CostResult.

        - materials_cost  <- total_material_cost
        - labour_cost     <- total_operation_cost    (v2 merges labour+machine)
        - machine_cost    <- 0  (no separate figure from v2)
        - total_cost      <- total_cost
        - breakdown[]     <- per-component rows (material + labour), keyed
                             so order snapshot readers still see something
                             meaningful when they inspect the breakdown.
        - validation.missing_cost_data <- v2 errors (formatted)
        - validation.warnings          <- v2 warnings (formatted)
        """
        breakdown: List[CostLine] = []
        est_minutes = 0.0
        for comp in v2.get("components", []):
            comp_name = comp.get("name") or comp.get("component_id") or "component"
            if comp.get("material_cost"):
                breakdown.append(
                    CostLine(
                        type="material",
                        name=f"{comp_name} — materials",
                        quantity=1.0,
                        unit="set",
                        unit_cost=float(comp.get("material_cost", 0.0)),
                        total=float(comp.get("material_cost", 0.0)),
                    )
                )
            if comp.get("operation_cost"):
                breakdown.append(
                    CostLine(
                        type="labour",
                        name=f"{comp_name} — operations",
                        quantity=1.0,
                        unit="set",
                        unit_cost=float(comp.get("operation_cost", 0.0)),
                        total=float(comp.get("operation_cost", 0.0)),
                    )
                )
            for op in comp.get("operations_detail", []):
                est_minutes += float(op.get("estimated_minutes", 0.0) or 0.0)

        missing = [
            (
                f"{err.get('kind', 'COST_ERROR')}@{err.get('path', '')}:{err.get('detail', '')}"
            )
            for err in v2.get("errors", [])
        ]
        warnings = [
            (
                f"{w.get('kind', 'WARNING')}@{w.get('path', '')}:{w.get('detail', '')}"
            )
            for w in v2.get("warnings", [])
        ]

        return CostResult(
            is_valid=bool(v2.get("is_valid", False)),
            currency=currency or "RON",
            materials_cost=float(v2.get("total_material_cost", 0.0)),
            labour_cost=float(v2.get("total_operation_cost", 0.0)),
            machine_cost=0.0,
            external_cost=0.0,
            overhead_cost=0.0,
            total_cost=float(v2.get("total_cost", 0.0)),
            estimated_time_minutes=round(est_minutes, 2),
            breakdown=breakdown,
            validation=CostValidation(
                missing_cost_data=missing,
                warnings=warnings,
            ),
        )

    @staticmethod
    def _attach_v2_extras(
        snap: QuoteCalculationSnapshot,
        breakdown: Optional[List[Dict[str, Any]]],
        warnings: Optional[List[Dict[str, Any]]],
        version: str,
    ) -> None:
        """Attach v2 extras as DYNAMIC attributes on the snapshot.

        Rationale: the `QuoteCalculationSnapshot` dataclass contract is
        frozen (modifying it is out of scope for this sprint), so we use
        dynamic attributes — dataclass instances allow them by default and
        `asdict()` ignores them, which preserves the exact legacy
        serialization surface.

        Persisted fields:
          - component_breakdown      : list[dict] (or None)
          - component_breakdown_json : JSON string (or None)
          - cost_warnings            : list[dict] (or None)
          - cost_engine_version      : "v1" | "v2"
        """
        try:
            setattr(snap, "component_breakdown", breakdown)
            setattr(
                snap,
                "component_breakdown_json",
                _json.dumps(breakdown, ensure_ascii=False) if breakdown is not None else None,
            )
            setattr(snap, "cost_warnings", warnings)
            setattr(snap, "cost_engine_version", version)
        except Exception:
            # Dynamic attribute assignment is best-effort; failing here
            # MUST NOT break the legacy flow.
            pass

    @staticmethod
    def _apply_commercial(total_cost: float, pricing: QuotePricing) -> QuotePrice:
        margin = max(float(pricing.margin_pct or 0), 0) / 100.0
        discount = max(float(pricing.discount_pct or 0), 0) / 100.0
        vat = max(float(pricing.vat_pct or 0), 0) / 100.0

        net_before_discount = total_cost * (1.0 + margin)
        net = net_before_discount * (1.0 - discount)
        gross = net * (1.0 + vat)
        final = gross
        return QuotePrice(
            net=round(net, 2),
            gross=round(gross, 2),
            final=round(final, 2),
        )