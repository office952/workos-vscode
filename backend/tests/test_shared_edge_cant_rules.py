"""Tests for shared edge/cant rules foundation."""

from __future__ import annotations

import pytest

from services.shared_edge_cant_rules import (
    EDGE_CANT_ADHESIVE_ML_PER_ML,
    EDGE_CANT_BOND_OPERATION_KEY,
    EDGE_CANT_BOND_OWNER_EUR_PER_ML,
    EDGE_CANT_ORACAL_MATERIAL_KEY,
    EDGE_CANT_ORACAL_WRAP_OPERATION_KEY,
    EDGE_CANT_QUOTE_WASTE_PERCENT,
    EDGE_CANT_LINEAR_UNIT,
    SHARED_EDGE_CANT_SOURCE,
    apply_edge_cant_quote_waste,
    build_edge_cant_adhesive_consumable_row,
    build_edge_cant_oracal_651_material_row,
    compute_return_wrap_area_m2,
    edge_cant_profiles_forbidden_on_wrap,
    evaluate_edge_cant_rules,
    resolve_edge_cant_oracal_651_profile,
    EdgeCantRuleInput,
)
from services.shared_vinyl_material_catalog import ORACAL_651_OWNER_EUR_PER_M2


PBL_COMBINED_RETURN_ML = 15.4672
PBL_LETTER_RETURN_ML = 13.6211
PBL_WRAPPED_GROUP_ML = 6.1683


def test_quote_edge_length_applies_twenty_percent_waste():
    calc, quote, waste = apply_edge_cant_quote_waste(PBL_COMBINED_RETURN_ML)
    assert waste == EDGE_CANT_QUOTE_WASTE_PERCENT
    assert calc == PBL_COMBINED_RETURN_ML
    assert quote == round(PBL_COMBINED_RETURN_ML * 1.2, 4)


def test_compute_return_wrap_area_m2_matches_pricing_geometry_without_default_depth():
    # 10m × 1.20 × (60+10)/1000 = 0.84 — same band math as Oracal material row.
    assert compute_return_wrap_area_m2(10.0, 60.0) == 0.84
    row = build_edge_cant_oracal_651_material_row(
        wrapped_calculated_ml=10.0,
        return_depth_mm=60,
    )
    assert row is not None
    assert row.quantity == 0.84


def test_calculated_and_quote_edge_lengths_are_separate():
    calc, quote, _ = apply_edge_cant_quote_waste(PBL_COMBINED_RETURN_ML)
    assert calc < quote
    assert round(quote - calc, 4) == round(PBL_COMBINED_RETURN_ML * 0.2, 4)


def test_edge_adhesive_ml_from_rule():
    row = build_edge_cant_adhesive_consumable_row(PBL_LETTER_RETURN_ML)
    expected = round(PBL_LETTER_RETURN_ML * EDGE_CANT_ADHESIVE_ML_PER_ML, 4)
    assert row.quantity == expected
    assert SHARED_EDGE_CANT_SOURCE in row.quantity_source


def test_pbl_fixture_calculated_and_quote_lengths():
    result = evaluate_edge_cant_rules(
        EdgeCantRuleInput(
            letter_return_ml=PBL_LETTER_RETURN_ML,
            total_return_ml=PBL_COMBINED_RETURN_ML,
            artwork_return_ml=1.8461,
            letter_groups=[
                {"group_key": "a", "return_finish_type": "oracal_wrapped", "perimeter_m": PBL_WRAPPED_GROUP_ML},
                {"group_key": "b", "return_finish_type": "standard_aluminum", "perimeter_m": 7.4528},
            ],
            default_return_finish="white_aluminum",
            edge_depth_mm=60,
        )
    )
    assert round(result.calculated_edge_length_m, 4) == round(PBL_COMBINED_RETURN_ML, 4)
    assert round(result.quote_edge_length_m, 4) == round(PBL_COMBINED_RETURN_ML * 1.2, 4)


def test_oracal_wrapped_uses_651_profile_from_catalog():
    profile = resolve_edge_cant_oracal_651_profile()
    assert profile is not None
    assert profile.series == "651"
    assert profile.price_eur_per_sqm == ORACAL_651_OWNER_EUR_PER_M2


def test_oracal_wrapped_material_row_not_641_or_8500():
    row = build_edge_cant_oracal_651_material_row(
        wrapped_calculated_ml=PBL_WRAPPED_GROUP_ML,
        return_depth_mm=60,
    )
    assert row is not None
    assert row.material_key == EDGE_CANT_ORACAL_MATERIAL_KEY
    assert "641" not in row.material_key
    assert "8500" not in row.material_key
    assert row.unit_price == ORACAL_651_OWNER_EUR_PER_M2


def test_forbidden_series_on_wrap():
    assert "641" in edge_cant_profiles_forbidden_on_wrap()
    assert "8500" in edge_cant_profiles_forbidden_on_wrap()
    assert "651" not in edge_cant_profiles_forbidden_on_wrap()


def test_operation_rows_source_shared_edge_cant_rules():
    result = evaluate_edge_cant_rules(
        EdgeCantRuleInput(
            letter_return_ml=PBL_LETTER_RETURN_ML,
            total_return_ml=PBL_COMBINED_RETURN_ML,
            letter_groups=[
                {"group_key": "a", "return_finish_type": "oracal_wrapped", "perimeter_m": PBL_WRAPPED_GROUP_ML},
            ],
            default_return_finish="oracal_wrapped",
            edge_depth_mm=60,
        )
    )
    assert result.operation_rows
    for row in result.operation_rows:
        assert row.source == SHARED_EDGE_CANT_SOURCE
        assert row.consumes_stock_now is False
        assert row.creates_task_now is False


def test_consumable_row_source_via_adhesive_builder():
    row = build_edge_cant_adhesive_consumable_row(PBL_LETTER_RETURN_ML)
    assert SHARED_EDGE_CANT_SOURCE in row.quantity_source


def test_bond_operation_uses_owner_rate_on_total_graphic_perimeter():
    result = evaluate_edge_cant_rules(
        EdgeCantRuleInput(letter_return_ml=8.0, total_return_ml=10.0, default_return_finish="white_aluminum")
    )
    bond = next(r for r in result.operation_rows if r.key == EDGE_CANT_BOND_OPERATION_KEY)
    assert bond.unit == EDGE_CANT_LINEAR_UNIT
    assert bond.quantity == 10.0
    assert bond.basis_key == "return_material_perimeter_ml"
    assert bond.pricing_status == "owner_rate"
    assert bond.unit_price == EDGE_CANT_BOND_OWNER_EUR_PER_ML
    assert bond.estimated_cost == 50.0


def test_oracal_wrap_operation_only_when_wrapped():
    wrapped = evaluate_edge_cant_rules(
        EdgeCantRuleInput(
            letter_return_ml=10.0,
            total_return_ml=10.0,
            letter_groups=[{"return_finish_type": "oracal_wrapped", "perimeter_m": 10.0}],
            default_return_finish="oracal_wrapped",
            edge_depth_mm=60,
        )
    )
    assert any(r.key == EDGE_CANT_ORACAL_WRAP_OPERATION_KEY for r in wrapped.operation_rows)

    plain = evaluate_edge_cant_rules(
        EdgeCantRuleInput(
            letter_return_ml=10.0,
            total_return_ml=10.0,
            default_return_finish="white_aluminum",
        )
    )
    assert not any(r.key == EDGE_CANT_ORACAL_WRAP_OPERATION_KEY for r in plain.operation_rows)
