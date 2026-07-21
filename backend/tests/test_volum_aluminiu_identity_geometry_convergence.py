"""Identity + geometry convergence for TPL-VOLUM-ALUMINIU_v1 activation readiness."""

from __future__ import annotations

from data.commercial_rules_volumetric_v2 import RULES_BY_TEMPLATE
from data.mini_module_registry_volumetric_v2 import DOSSIER_COMPONENT_TO_MODULE
from services.commercial_price_proposal_service import _extract_quantity
from services.letters_commercial_measurement_service import build_letters_commercial_measurements
from services.product_aggregate_service import DOSSIER_COMPONENT_MINI_MODULE
from services.volum_aluminiu_component_contract import (
    BOM_COMPONENT_ID,
    COMMERCIAL_LINE_CODE,
    MINI_MODULE_CODE,
    PRICING_COMPONENT_CODE,
    TEMPLATE_CODE,
    build_identity_convergence_view,
    map_component_ref_to_module,
    map_template_to_module,
    resolve_identity_token,
)
from services.volum_aluminiu_quantity_ownership import (
    apply_confirmed_perimeter_quote_geometry_bridge,
    resolve_component_quantity_from_payload,
    resolve_product_total_perimeter_authority,
)


def _confirmed_payload(*, confirmed: float, evidence: float | None) -> dict:
    payload: dict = {
        "finish_setup": {
            "return_depth_mm": 60,
            "return_finish_type": "white_aluminum",
            "return_cant_component_confirmation": {
                "instances": {
                    "letter_group:fixture": {
                        "confirmed_perimeter_m": confirmed,
                        "confirmed_perimeter_source": "operator_confirmed",
                        "confirmation_source": "operator_component_confirmation",
                    }
                }
            },
        },
        "layer_role_setup": {
            "layers": [
                {
                    "layer_key": "fixture",
                    "layer_id": "fixture",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ]
        },
        "product_truth": {
            "components": {
                "return_cant": {
                    "instances": {
                        "letter_group:fixture": {
                            "confirmation_state": "confirmed",
                            "confirmation_source": "operator_component_confirmation",
                            "material_profile": {"width_mm": 60},
                            "finish_variant": "white_aluminum",
                            "geometry": {
                                "unit": "m",
                                "perimeter_source": "operator_confirmed",
                                "confirmed_perimeter_m": confirmed,
                                "confirmed_perimeter_source": "operator_confirmed",
                                "evidence_perimeter_m": evidence,
                            },
                        }
                    }
                }
            }
        },
    }
    if evidence is not None:
        payload["quote_geometry"] = {"letter_perimeter_m": evidence}
    return payload


def test_identity_map_has_one_canonical_bom_and_explicit_pricing_alias() -> None:
    view = build_identity_convergence_view()
    assert view["status"] == "PASS"
    assert view["canonical"]["template_code"] == TEMPLATE_CODE
    assert view["canonical"]["bom_component_id"] == BOM_COMPONENT_ID
    assert view["canonical"]["aggregate_module_code"] == MINI_MODULE_CODE
    assert view["aliases"]["pricing_component_code"] == PRICING_COMPONENT_CODE
    assert view["name_based_lookup"] is False
    assert "used_by" in view and len(view["used_by"]) >= 4


def test_identity_resolvers_are_id_based_not_name() -> None:
    assert resolve_identity_token(BOM_COMPONENT_ID)["is_canonical_bom"] is True
    assert resolve_identity_token(PRICING_COMPONENT_CODE)["is_pricing_stub"] is True
    assert resolve_identity_token("Cant din aluminiu") is None
    assert resolve_identity_token("VOLUM ALUMINIU") is None
    assert map_component_ref_to_module(BOM_COMPONENT_ID) == MINI_MODULE_CODE
    assert map_component_ref_to_module(PRICING_COMPONENT_CODE) == MINI_MODULE_CODE
    assert map_template_to_module(TEMPLATE_CODE) == MINI_MODULE_CODE


def test_aggregate_dossier_maps_bom_and_stub_once_to_same_module() -> None:
    assert DOSSIER_COMPONENT_MINI_MODULE[BOM_COMPONENT_ID] == MINI_MODULE_CODE
    assert DOSSIER_COMPONENT_MINI_MODULE[PRICING_COMPONENT_CODE] == MINI_MODULE_CODE
    assert DOSSIER_COMPONENT_TO_MODULE[BOM_COMPONENT_ID] == MINI_MODULE_CODE
    assert DOSSIER_COMPONENT_TO_MODULE[PRICING_COMPONENT_CODE] == MINI_MODULE_CODE
    # Same module token — no double Aggregate key.
    assert (
        DOSSIER_COMPONENT_MINI_MODULE[BOM_COMPONENT_ID]
        == DOSSIER_COMPONENT_MINI_MODULE[PRICING_COMPONENT_CODE]
    )


def test_product_total_prefers_confirmed_when_aligned_with_evidence() -> None:
    payload = _confirmed_payload(confirmed=12.5, evidence=12.5)
    authority = resolve_product_total_perimeter_authority(payload)
    assert authority["ok"] is True
    assert authority["authority"] == "confirmed_product_truth"
    assert authority["quantity_m"] == 12.5
    assert authority["quantity_ml"] == 12.5
    assert authority["divergence"] is False

    bridged, report = apply_confirmed_perimeter_quote_geometry_bridge(payload)
    assert report["authority"] == "confirmed_product_truth"
    assert bridged["quote_geometry"]["letter_perimeter_m"] == 12.5
    assert bridged["quote_geometry"]["letter_perimeter_authority"]["read_only_bridge"] is True
    assert bridged["quote_geometry"]["letter_perimeter_authority"]["parallel_authority"] is False


def test_product_total_fail_closed_on_divergence() -> None:
    payload = _confirmed_payload(confirmed=12.5, evidence=18.5)
    authority = resolve_product_total_perimeter_authority(payload)
    assert authority["ok"] is False
    assert authority["fail_closed"] is True
    assert authority["divergence"] is True
    assert "RETURN_CANT_PERIMETER_DIVERGENCE" in authority["blockers"]

    bridged, report = apply_confirmed_perimeter_quote_geometry_bridge(payload)
    assert report["divergence"] is True
    assert "letter_perimeter_m" not in bridged.get("quote_geometry", {})
    assert _extract_quantity(bridged, ("quote_geometry.letter_perimeter_m", "letter_perimeter_m")) is None


def test_legacy_quote_geometry_fallback_is_named_not_silent() -> None:
    payload = {
        "quote_geometry": {"letter_perimeter_m": 9.25},
        "product_truth": {"components": {"return_cant": {"instances": {}}}},
    }
    authority = resolve_product_total_perimeter_authority(payload)
    assert authority["ok"] is True
    assert authority["authority"] == "quote_geometry_legacy_fallback"
    assert authority["parent_unconfirmed_fallback_used"] is True
    assert "quote_geometry_legacy_fallback" in authority["warnings"]

    bridged, _ = apply_confirmed_perimeter_quote_geometry_bridge(payload)
    assert bridged["quote_geometry"]["letter_perimeter_authority"]["classification"] == "legacy_fallback"
    assert bridged["quote_geometry"]["letter_perimeter_authority"]["parallel_authority"] is False


def test_preview_qty_matches_product_total_bridge_within_rounding() -> None:
    payload = _confirmed_payload(confirmed=12.3456789, evidence=12.345679)
    # round to 6dp → both become 12.345679
    separate = resolve_component_quantity_from_payload(payload)
    total = resolve_product_total_perimeter_authority(payload)
    assert separate["ok"] is True
    assert total["ok"] is True
    assert separate["quantity_m"] == total["quantity_m"]
    assert separate["quantity_ml"] == total["quantity_ml"]

    bridged, _ = apply_confirmed_perimeter_quote_geometry_bridge(payload)
    cpp_qty = _extract_quantity(bridged, ("quote_geometry.letter_perimeter_m", "letter_perimeter_m"))
    assert cpp_qty == separate["quantity_m"]


def test_commercial_measurement_uses_confirmed_perimeter_for_modelare_cant() -> None:
    payload = _confirmed_payload(confirmed=7.0, evidence=7.0)
    bundle = build_letters_commercial_measurements(
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        pd=None,
        quote_input=payload,
        active_modules={"modelare_cant", "debitare_fata"},
    )
    assert bundle is not None
    assert "perimeter_authority=confirmed_product_truth" in (bundle.diagnostics or [])
    modelare = next(m for m in bundle.measurements if m.line_code == COMMERCIAL_LINE_CODE)
    assert modelare.quantity == 7.0
    assert modelare.unit == "ml"


def test_commercial_rule_still_keys_pricing_stub_not_second_bom() -> None:
    rules = RULES_BY_TEMPLATE["TPL-VOLUMETRIC-LETTERS_v2"]
    modelare = next(r for r in rules if r.line_code == COMMERCIAL_LINE_CODE)
    assert modelare.component_code == PRICING_COMPONENT_CODE
    assert modelare.module_code == MINI_MODULE_CODE
    # Alias maps to same Aggregate module as BOM — not a second commercial owner.
    assert map_component_ref_to_module(modelare.component_code) == map_component_ref_to_module(
        BOM_COMPONENT_ID
    )
