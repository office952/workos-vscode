"""Resolve offer_scope sold modules for BOM / EIC / CPP pricing filters."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from data.offer_scope_canonical_map import (
    ALL_CANONICAL_SOLD_MODULES,
    SLICE1_ACTIVE_CANONICAL,
    SLICE1_DEFERRED_CANONICAL,
    derive_calc_modules,
    runtime_modules_for_canonical,
)
from pydantic import ValidationError
from schemas.offer_scope import OFFER_SCOPE_CONTRACT_VERSION, OfferScopeInput, OfferScopeResolveResult
from schemas.product_definition import ProductDefinitionPreview

BAR_MOUNTING = frozenset({"steel_bars", "aluminum_bars"})


def extract_offer_scope(
    payload: dict[str, Any] | None,
    quote_input: dict[str, Any] | None,
) -> OfferScopeInput | None:
    """quote_input offer_scope wins over payload."""
    raw: dict[str, Any] | None = None
    if quote_input and isinstance(quote_input.get("offer_scope"), dict):
        raw = quote_input["offer_scope"]
    elif payload and isinstance(payload.get("offer_scope"), dict):
        raw = payload["offer_scope"]
    if not raw:
        return None
    try:
        return OfferScopeInput.model_validate(raw)
    except ValidationError:
        return None


def _validate_subset(scope: OfferScopeInput) -> list[str]:
    errors: list[str] = []
    if scope.contract_version != OFFER_SCOPE_CONTRACT_VERSION:
        errors.append("UNSUPPORTED_CONTRACT_VERSION")
    if not scope.sold_modules:
        errors.append("SOLD_MODULES_EMPTY")
    for code in scope.sold_modules:
        if code not in ALL_CANONICAL_SOLD_MODULES:
            errors.append(f"UNKNOWN_SOLD_MODULE:{code}")
        elif code in SLICE1_DEFERRED_CANONICAL:
            errors.append(f"DEFERRED_SOLD_MODULE_NOT_SUPPORTED_IN_V1:{code}")
    return errors


def resolve_offer_scope(scope: OfferScopeInput | None) -> OfferScopeResolveResult:
    if scope is None or scope.mode == "full_product":
        return OfferScopeResolveResult(
            use_legacy=True,
            mode="full_product" if scope is None else scope.mode,
        )

    errors = _validate_subset(scope)
    canonical = list(scope.sold_modules)
    runtime = runtime_modules_for_canonical(canonical) if not errors else set()
    calc = derive_calc_modules(canonical)

    return OfferScopeResolveResult(
        use_legacy=False,
        mode="component_subset",
        canonical_sold_modules=canonical,
        runtime_sold_modules=runtime,
        calc_modules=calc,
        validation_errors=errors,
    )


def _apply_conditional_gates(
    runtime_sold: set[str],
    *,
    payload: dict[str, Any],
    quote_input: dict[str, Any] | None,
) -> set[str]:
    """Apply illumination/bars gates only for modules already in sold runtime set."""
    active = set(runtime_sold)
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    merged_finish = dict(finish)
    if quote_input:
        qi_finish = quote_input.get("finish_setup")
        if isinstance(qi_finish, dict):
            merged_finish.update(qi_finish)
        for key in (
            "mounting_system",
            "lighting_system_type",
            "illuminated",
        ):
            if key in quote_input and key not in merged_finish:
                merged_finish[key] = quote_input[key]

    if "structura_suport" in active:
        from services.mounting_solution_service import is_structura_suport_active

        finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
        merged_finish = dict(finish)
        if quote_input:
            qi_finish = quote_input.get("finish_setup")
            if isinstance(qi_finish, dict):
                merged_finish.update(qi_finish)
            for key in ("mounting_system",):
                if key in quote_input and key not in merged_finish:
                    merged_finish[key] = quote_input[key]
        if not is_structura_suport_active(merged_finish):
            mounting = merged_finish.get("mounting_system") or payload.get("mounting_system")
            if mounting not in BAR_MOUNTING:
                active.discard("structura_suport")

    if "sistem_led" in active:
        illuminated = merged_finish.get("illuminated")
        is_lit = illuminated is True or str(illuminated).lower() in ("true", "1", "yes")
        lighting = merged_finish.get("lighting_system_type") or payload.get("lighting_system_type")
        if not (is_lit and lighting and str(lighting).strip().lower() not in ("", "none")):
            active.discard("sistem_led")

    return active


def resolve_pricing_active_modules(
    *,
    pd: ProductDefinitionPreview,
    payload: dict[str, Any],
    quote_input: dict[str, Any] | None,
    legacy_fn: Callable[[ProductDefinitionPreview, dict[str, Any] | None], set[str]],
) -> set[str]:
    """Return runtime mini_module_codes used to filter BOM / EIC / CPP rows."""
    scope = extract_offer_scope(payload, quote_input)
    resolved = resolve_offer_scope(scope)

    if resolved.use_legacy:
        return legacy_fn(pd, quote_input)

    if resolved.validation_errors:
        return set()

    active = _apply_conditional_gates(
        resolved.runtime_sold_modules,
        payload=payload,
        quote_input=quote_input,
    )
    return active


def merge_scope_payload(
    payload: dict[str, Any],
    quote_input: dict[str, Any] | None,
) -> dict[str, Any]:
    """Shallow merge for offer_scope extraction — quote_input keys overlay payload."""
    merged = dict(payload or {})
    if quote_input:
        if isinstance(quote_input.get("offer_scope"), dict):
            merged["offer_scope"] = quote_input["offer_scope"]
        if isinstance(quote_input.get("finish_setup"), dict):
            merged.setdefault("finish_setup", {}).update(quote_input["finish_setup"])
        if isinstance(quote_input.get("quote_geometry"), dict):
            merged.setdefault("quote_geometry", {}).update(quote_input["quote_geometry"])
    return merged
