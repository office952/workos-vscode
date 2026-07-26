"""Unit tests for offer_scope resolver."""

from __future__ import annotations

import pytest

from data.offer_scope_canonical_map import runtime_to_canonical
from schemas.offer_scope import OfferScope, OfferScopeInput
from services.offer_scope_resolver_service import (
    extract_offer_scope,
    resolve_offer_scope,
    resolve_pricing_active_modules,
)
from schemas.product_definition import ProductDefinitionPreview, ProductDefinitionSourceContext


def _minimal_pd() -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        source_context=ProductDefinitionSourceContext(
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
            source_payload_type="template_only",
        ),
    )


def test_runtime_to_canonical_inverse() -> None:
    assert runtime_to_canonical("debitare_fata") == "FACE"
    assert runtime_to_canonical("modelare_cant") == "RETURN-CANT"
    assert runtime_to_canonical("debitare_spate") == "BACK"
    assert runtime_to_canonical("unknown_module") is None


def test_absent_offer_scope_uses_legacy() -> None:
    result = resolve_offer_scope(None)
    assert result.use_legacy is True
    assert result.runtime_sold_modules == set()


def test_full_product_mode_uses_legacy() -> None:
    scope = OfferScope(mode="full_product", sold_modules=["FACE"])
    result = resolve_offer_scope(scope)
    assert result.use_legacy is True


def test_face_only_subset() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=["FACE"])
    result = resolve_offer_scope(scope)
    assert result.use_legacy is False
    assert result.runtime_sold_modules == {"debitare_fata"}
    assert "GEOMETRY" in result.calc_modules
    assert "PERIMETER" not in result.calc_modules


def test_return_cant_only_subset() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=["RETURN-CANT"])
    result = resolve_offer_scope(scope)
    assert result.runtime_sold_modules == {"modelare_cant"}
    assert "PERIMETER" in result.calc_modules
    assert "debitare_fata" not in result.runtime_sold_modules


def test_back_only_subset() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=["BACK"])
    result = resolve_offer_scope(scope)
    assert result.runtime_sold_modules == {"debitare_spate"}
    assert "FACE_AREA" in result.calc_modules


def test_face_and_return_cant_subset() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=["FACE", "RETURN-CANT"])
    result = resolve_offer_scope(scope)
    assert result.runtime_sold_modules == {"debitare_fata", "modelare_cant"}


def test_empty_subset_rejected() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=[])
    result = resolve_offer_scope(scope)
    assert "SOLD_MODULES_EMPTY" in result.validation_errors


def test_unknown_module_rejected() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=["NOT_A_MODULE"])
    result = resolve_offer_scope(scope)
    assert any("UNKNOWN_SOLD_MODULE" in e for e in result.validation_errors)


def test_calc_modules_never_in_runtime_sold() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=["RETURN-CANT"])
    result = resolve_offer_scope(scope)
    for calc in result.calc_modules:
        assert calc not in result.runtime_sold_modules


def test_lighting_subset_resolves() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=["LIGHTING"])
    result = resolve_offer_scope(scope)
    assert not result.validation_errors
    assert result.runtime_sold_modules == {"sistem_led"}


def test_electrical_subset_includes_led_count_calc() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=["ELECTRICAL"])
    result = resolve_offer_scope(scope)
    assert not result.validation_errors
    assert "LED_COUNT" in result.calc_modules


def test_deferred_finish_rejected_in_v1() -> None:
    scope = OfferScopeInput(mode="component_subset", sold_modules=["FINISH"])
    result = resolve_offer_scope(scope)
    assert any("DEFERRED_SOLD_MODULE" in e for e in result.validation_errors)


def test_extract_from_quote_input() -> None:
    qi = {"offer_scope": {"mode": "component_subset", "sold_modules": ["FACE"]}}
    scope = extract_offer_scope({}, qi)
    assert scope is not None
    assert scope.sold_modules == ["FACE"]


def test_pricing_active_modules_legacy_unchanged() -> None:
    legacy_called = {"count": 0}

    def legacy(pd, quote_input):
        legacy_called["count"] += 1
        return {"debitare_fata", "modelare_cant", "debitare_spate", "finisaje"}

    active = resolve_pricing_active_modules(
        pd=_minimal_pd(),
        payload={},
        quote_input=None,
        legacy_fn=legacy,
    )
    assert legacy_called["count"] == 1
    assert "finisaje" in active


def test_pricing_active_modules_subset() -> None:
    def legacy(pd, quote_input):
        raise AssertionError("legacy must not run for component_subset")

    qi = {
        "offer_scope": {
            "contract_version": "offer_scope_contract/v1",
            "mode": "component_subset",
            "sold_modules": ["FACE"],
        }
    }
    active = resolve_pricing_active_modules(
        pd=_minimal_pd(),
        payload=qi,
        quote_input=qi,
        legacy_fn=legacy,
    )
    assert active == {"debitare_fata"}
