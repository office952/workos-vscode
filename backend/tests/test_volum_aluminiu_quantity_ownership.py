"""Quantity ownership boundaries for TPL-VOLUM-ALUMINIU_v1 separate calc."""

from __future__ import annotations

from services.volum_aluminiu_quantity_ownership import (
    resolve_component_quantity_from_payload,
    sum_confirmed_perimeter_m,
)


def _confirmed_instance(perimeter: float) -> dict:
    return {
        "confirmation_state": "confirmed",
        "confirmation_source": "operator_component_confirmation",
        "material_profile": {"width_mm": 60},
        "geometry": {
            "perimeter_source": "operator_confirmed",
            "confirmed_perimeter_m": perimeter,
            "confirmed_perimeter_source": "operator_confirmed",
            "evidence_perimeter_m": 99.0,
            "unit": "m",
        },
    }


def test_sum_confirmed_perimeter_fails_closed_without_confirmation() -> None:
    qty, blockers = sum_confirmed_perimeter_m(
        {
            "letter_group:a": {
                "confirmation_state": "blocked",
                "geometry": {
                    "perimeter_source": "evidence_only",
                    "evidence_perimeter_m": 12.0,
                },
            }
        }
    )
    assert qty is None
    assert any("UNCONFIRMED" in b for b in blockers)


def test_sum_confirmed_perimeter_adds_instances() -> None:
    qty, blockers = sum_confirmed_perimeter_m(
        {
            "letter_group:a": _confirmed_instance(10.25),
            "letter_group:b": _confirmed_instance(2.5),
        }
    )
    assert blockers == []
    assert qty == 12.75


def test_resolve_rejects_parent_evidence_fallback() -> None:
    out = resolve_component_quantity_from_payload(
        {
            "quote_geometry": {"letter_perimeter_m": 18.5},
            "product_truth": {
                "components": {
                    "return_cant": {
                        "instances": {
                            "letter_group:a": {
                                "confirmation_state": "blocked",
                                "geometry": {
                                    "perimeter_source": "evidence_only",
                                    "evidence_perimeter_m": 18.5,
                                },
                            }
                        }
                    }
                }
            },
        }
    )
    assert out["ok"] is False
    assert out["parent_unconfirmed_fallback_used"] is False
    assert out["evidence_drives_calc"] is False
    assert out["quantity_m"] is None


def test_resolve_uses_confirmed_only() -> None:
    out = resolve_component_quantity_from_payload(
        {
            "quote_geometry": {"letter_perimeter_m": 99.0},
            "product_truth": {
                "components": {
                    "return_cant": {
                        "instances": {"letter_group:a": _confirmed_instance(7.0)}
                    }
                }
            },
        }
    )
    assert out["ok"] is True
    assert out["quantity_m"] == 7.0
    assert out["quantity_ml"] == 7.0
    assert out["evidence_perimeter_m"] == 99.0
    assert out["evidence_drives_calc"] is False
