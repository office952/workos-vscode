"""Canonical Letters Slice 1 active-scope compiler.

Single authority for:
  offer_scope → active/inactive runtime modules → commercial + execution scope

Money and task materialization are out of scope — consumers filter on this result.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from data.offer_scope_canonical_map import (
    derive_calc_modules,
    runtime_modules_for_canonical,
)
from schemas.active_scope import (
    ACTIVE_SCOPE_RESOLVER_VERSION,
    ActiveScopeDependency,
    ActiveScopeResult,
)
from schemas.offer_scope import OfferScopeInput, OfferScopeResolveResult
from schemas.product_definition import ProductDefinitionPreview
from services.offer_scope_resolver_service import (
    _apply_conditional_gates,
    extract_offer_scope,
    resolve_offer_scope,
)

# All Letters mini-modules known to PD/form contract for Slice 1 (+ decoupled responsibilities).
LETTERS_RUNTIME_MODULES: frozenset[str] = frozenset(
    {
        "geometry_svg",
        "debitare_fata",
        "debitare_spate",
        "modelare_cant",
        "sistem_led",
        "finisaje",
        "sablon_montaj",
        "ambalare_livrare_montaj",
        "structura_suport",
        "electrica_logo",
    }
)

# Calc prerequisite codes → runtime modules (never sold / never priced alone).
CALC_TO_RUNTIME: dict[str, frozenset[str]] = {
    "GEOMETRY": frozenset({"geometry_svg"}),
    "PERIMETER": frozenset({"geometry_svg"}),
    "FACE_AREA": frozenset({"geometry_svg"}),
    "LED_COUNT": frozenset(),  # quantity fact only — sistem_led must be sold
}

# Composition-only priced ops / task keys — complete product, not standalone sold modules.
COMPOSITION_ONLY_EXECUTION_OPS: frozenset[str] = frozenset(
    {
        "return_face_bonding",
        "RETURN_PROFILE_FACE_BONDING",
    }
)

# When RETURN-CANT is sold alone, bonding remains composition-only.
RETURN_ONLY_COMPOSITION_EXCLUSIONS: frozenset[str] = frozenset(
    {
        "return_face_bonding",
        "RETURN_PROFILE_FACE_BONDING",
    }
)

# FACE+CANT interface materials — emit only when both FACE and RETURN-CANT are sold
# (or full-product legacy). Material codes + live-calc row keys.
INTERFACE_FACE_CANT_MATERIALS: frozenset[str] = frozenset(
    {
        "MAT-ADEZIV-CANT-LITERE",
        "adhesive_return_to_face",
    }
)


def _interface_face_cant_active(sold: list[str] | set[str]) -> bool:
    sold_set = set(sold)
    return "FACE" in sold_set and "RETURN-CANT" in sold_set


def _composition_excluded_materials_for_sold(sold: list[str]) -> list[str]:
    """Silence interface materials unless FACE+CANT interface is active."""
    if _interface_face_cant_active(sold):
        return []
    return sorted(INTERFACE_FACE_CANT_MATERIALS)


def _calc_runtime_modules(calc_modules: list[str]) -> set[str]:
    out: set[str] = set()
    for code in calc_modules:
        out.update(CALC_TO_RUNTIME.get(code, frozenset()))
    return out


def _dependency_rows(
    *,
    sold: list[str],
    calc_modules: list[str],
    active: set[str],
) -> list[ActiveScopeDependency]:
    rows: list[ActiveScopeDependency] = []
    sold_set = set(sold)
    if "RETURN-CANT" in sold_set:
        rows.append(
            ActiveScopeDependency(
                code="PERIMETER",
                dependency_class="hard_technical",
                reason="Modeled return requires perimeter geometry.",
                required_by=["RETURN-CANT", "modelare_cant"],
            )
        )
    if calc_modules:
        rows.append(
            ActiveScopeDependency(
                code="GEOMETRY",
                dependency_class="hard_technical",
                reason="Sold subset requires geometry/file preparation facts.",
                required_by=list(sold),
            )
        )
    if "return_face_bonding" in RETURN_ONLY_COMPOSITION_EXCLUSIONS and sold_set == {"RETURN-CANT"}:
        rows.append(
            ActiveScopeDependency(
                code="return_face_bonding",
                dependency_class="composition_only",
                reason="Face-to-return bonding belongs to complete volumetric letters, not return sold alone.",
                required_by=["full_product", "FACE+RETURN-CANT"],
            )
        )
    if not _interface_face_cant_active(sold_set) and "RETURN-CANT" in sold_set:
        rows.append(
            ActiveScopeDependency(
                code="MAT-ADEZIV-CANT-LITERE",
                dependency_class="composition_only",
                reason="Return-to-face adhesive belongs to FACE+CANT interface, not RETURN-CANT alone.",
                required_by=["FACE", "RETURN-CANT"],
            )
        )
    if _interface_face_cant_active(sold_set):
        rows.append(
            ActiveScopeDependency(
                code="RETURN_FACE_BONDING",
                dependency_class="composition_only",
                reason="FACE+CANT interface activates return-face bonding and adhesive once.",
                required_by=["FACE", "RETURN-CANT"],
            )
        )
    for code in sorted(active):
        if code in (
            "debitare_fata",
            "modelare_cant",
            "debitare_spate",
            "sistem_led",
            "finisaje",
            "sablon_montaj",
            "ambalare_livrare_montaj",
            "structura_suport",
        ):
            rows.append(
                ActiveScopeDependency(
                    code=code,
                    dependency_class="commercial",
                    reason="Sold/active commercial runtime module.",
                    required_by=list(sold_set) if sold_set else ["full_product"],
                )
            )
    return rows


def compile_active_scope(
    *,
    template_code: str,
    payload: dict[str, Any] | None = None,
    quote_input: dict[str, Any] | None = None,
    known_runtime_modules: frozenset[str] | None = None,
) -> ActiveScopeResult:
    """Compile canonical active scope from offer_scope (+ finish gates)."""
    payload = payload or {}
    known = known_runtime_modules or LETTERS_RUNTIME_MODULES
    scope = extract_offer_scope(payload, quote_input)
    resolved = resolve_offer_scope(scope)

    provenance: dict[str, Any] = {
        "resolver_version": ACTIVE_SCOPE_RESOLVER_VERSION,
        "offer_scope_present": scope is not None,
        "offer_scope_mode": resolved.mode,
    }

    if resolved.use_legacy:
        # Full product — consumers use PD legacy activation; we expose mode only.
        return ActiveScopeResult(
            template_code=template_code,
            mode=resolved.mode,
            use_legacy_full_product=True,
            sold_module_codes=list(resolved.canonical_sold_modules),
            active_runtime_modules=[],
            inactive_runtime_modules=[],
            calculation_prerequisites=[],
            commercial_scope_modules=[],
            execution_scope_modules=[],
            composition_excluded_operations=[],
            composition_excluded_materials=[],
            dependencies=[],
            warnings=["ACTIVE_SCOPE_LEGACY_FULL_PRODUCT"],
            errors=list(resolved.validation_errors),
            provenance=provenance,
        )

    if resolved.validation_errors:
        return ActiveScopeResult(
            template_code=template_code,
            mode="component_subset",
            use_legacy_full_product=False,
            sold_module_codes=list(resolved.canonical_sold_modules),
            active_runtime_modules=[],
            inactive_runtime_modules=sorted(known),
            calculation_prerequisites=[],
            commercial_scope_modules=[],
            execution_scope_modules=[],
            errors=list(resolved.validation_errors),
            provenance=provenance,
        )

    sold = list(resolved.canonical_sold_modules)
    calc = list(resolved.calc_modules)
    sold_runtime = set(resolved.runtime_sold_modules)
    gated = _apply_conditional_gates(
        sold_runtime,
        payload=payload,
        quote_input=quote_input,
    )
    calc_runtime = _calc_runtime_modules(calc)
    active = gated | calc_runtime
    # electrica_logo stays future / inactive unless explicitly sold (never in Slice1 map)
    inactive = sorted(code for code in known if code not in active)

    composition_excluded: list[str] = []
    if set(sold) == {"RETURN-CANT"}:
        composition_excluded = sorted(RETURN_ONLY_COMPOSITION_EXCLUSIONS)
    # Bonding is composition-only unless FACE+CANT interface is active.
    elif not _interface_face_cant_active(sold) and "RETURN-CANT" in set(sold):
        # RETURN-CANT with other modules but without FACE — still exclude bonding.
        composition_excluded = sorted(RETURN_ONLY_COMPOSITION_EXCLUSIONS)

    composition_excluded_materials = _composition_excluded_materials_for_sold(sold)

    commercial = sorted(gated)  # calc modules never commercial
    execution = sorted(gated | (calc_runtime & {"geometry_svg"}))

    return ActiveScopeResult(
        template_code=template_code,
        mode="component_subset",
        use_legacy_full_product=False,
        sold_module_codes=sold,
        active_runtime_modules=sorted(active),
        inactive_runtime_modules=inactive,
        calculation_prerequisites=calc,
        commercial_scope_modules=commercial,
        execution_scope_modules=execution,
        composition_excluded_operations=composition_excluded,
        composition_excluded_materials=composition_excluded_materials,
        dependencies=_dependency_rows(sold=sold, calc_modules=calc, active=gated),
        warnings=[],
        errors=[],
        provenance={
            **provenance,
            "sold_runtime_before_gates": sorted(sold_runtime),
            "sold_runtime_after_gates": sorted(gated),
            "calc_runtime": sorted(calc_runtime),
            "interface_face_cant_active": _interface_face_cant_active(sold),
        },
    )


def resolve_pricing_active_modules_from_scope(
    *,
    pd: ProductDefinitionPreview,
    payload: dict[str, Any],
    quote_input: dict[str, Any] | None,
    legacy_fn: Callable[[ProductDefinitionPreview, dict[str, Any] | None], set[str]],
) -> set[str]:
    """Pricing/BOM/EIC active modules — sold authority for subset; legacy for full product."""
    scope_result = compile_active_scope(
        template_code=pd.template_code,
        payload=payload,
        quote_input=quote_input,
    )
    if scope_result.use_legacy_full_product:
        return legacy_fn(pd, quote_input)
    if scope_result.errors:
        return set()
    # Commercial modules only (exclude geometry_svg gate from money)
    return set(scope_result.commercial_scope_modules)


def active_modules_for_aggregate(
    scope: ActiveScopeResult,
    *,
    legacy_active: set[str] | None = None,
) -> set[str]:
    """Modules that may emit Aggregate components/materials/ops/measurements."""
    if scope.use_legacy_full_product:
        return set(legacy_active or ())
    if scope.errors:
        return set()
    return scope.active_set()


# Re-export helpers used by existing call sites that migrate gradually.
__all__ = [
    "COMPOSITION_ONLY_EXECUTION_OPS",
    "INTERFACE_FACE_CANT_MATERIALS",
    "LETTERS_RUNTIME_MODULES",
    "active_modules_for_aggregate",
    "compile_active_scope",
    "extract_offer_scope",
    "resolve_offer_scope",
    "resolve_pricing_active_modules_from_scope",
    "OfferScopeInput",
    "OfferScopeResolveResult",
]
