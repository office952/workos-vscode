"""Sold-scope dependency validator matrix and integration tests."""

from __future__ import annotations

from itertools import combinations

import pytest

from services.sold_scope_dependency_validator_service import (
    CODE_ELECTRICAL_LOAD_NOT_SOLD,
    CODE_LED_MOUNT_SURFACE_NOT_SOLD,
    CODE_SOLD_MODULES_EMPTY,
    validate_sold_graph,
)

MODULES = ["FACE", "RETURN-CANT", "BACK", "LIGHTING", "ELECTRICAL"]
TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _sold_combos() -> list[list[str]]:
    combos: list[list[str]] = [[]]
    for r in range(1, len(MODULES) + 1):
        combos.extend(list(c) for c in combinations(MODULES, r))
    return combos


def _mount_satisfied(sold: set[str]) -> bool:
    return "BACK" in sold or ({"FACE", "RETURN-CANT"}.issubset(sold))


def _expected_confirmation_codes(sold: set[str]) -> set[str]:
    codes: set[str] = set()
    if not sold:
        return codes
    if "LIGHTING" in sold and not _mount_satisfied(sold):
        codes.add(CODE_LED_MOUNT_SURFACE_NOT_SOLD)
    if "ELECTRICAL" in sold and "LIGHTING" not in sold:
        codes.add(CODE_ELECTRICAL_LOAD_NOT_SOLD)
    return codes


@pytest.mark.parametrize("sold", _sold_combos())
def test_validate_sold_graph_matrix_permissive(sold: list[str]) -> None:
    result = validate_sold_graph(
        mode="component_subset",
        sold_modules=sold,
        template_code=TEMPLATE,
        strict=False,
    )
    sold_set = set(sold)

    if not sold_set:
        assert any(issue.code == CODE_SOLD_MODULES_EMPTY for issue in result.blockers)
        assert result.valid_for_save is False
        return

    expected = _expected_confirmation_codes(sold_set)
    actual = {issue.code for issue in result.confirmations_required}
    assert actual == expected
    assert result.valid_for_save is True
    if expected:
        assert result.valid_for_confirmation is False
    else:
        assert result.valid_for_confirmation is True


@pytest.mark.parametrize("sold", _sold_combos())
def test_validate_sold_graph_matrix_strict(sold: list[str]) -> None:
    result = validate_sold_graph(
        mode="component_subset",
        sold_modules=sold,
        template_code=TEMPLATE,
        strict=True,
    )
    sold_set = set(sold)
    if not sold_set:
        assert result.valid_for_save is False
        return
    expected = _expected_confirmation_codes(sold_set)
    if expected:
        assert result.valid_for_save is False
    else:
        assert result.valid_for_save is True


def test_full_product_skips_dependency_rules() -> None:
    result = validate_sold_graph(mode="full_product", sold_modules=[], template_code=TEMPLATE)
    assert result.valid is True
    assert result.valid_for_save is True
    assert result.confirmations_required == []


def test_lighting_mount_confirmed_clears_requirement() -> None:
    result = validate_sold_graph(
        mode="component_subset",
        sold_modules=["LIGHTING"],
        template_code=TEMPLATE,
        dependency_confirmations={CODE_LED_MOUNT_SURFACE_NOT_SOLD},
    )
    assert result.confirmations_required == []
    assert result.valid_for_confirmation is True


def test_back_provides_mount_surface() -> None:
    result = validate_sold_graph(
        mode="component_subset",
        sold_modules=["BACK", "LIGHTING"],
        template_code=TEMPLATE,
    )
    assert "LED_MOUNT_SURFACE" in result.satisfied_capabilities
    assert result.confirmations_required == []


def test_face_cant_bundle_provides_mount_surface() -> None:
    result = validate_sold_graph(
        mode="component_subset",
        sold_modules=["FACE", "RETURN-CANT", "LIGHTING"],
        template_code=TEMPLATE,
    )
    assert "LED_MOUNT_SURFACE" in result.satisfied_capabilities
    assert result.confirmations_required == []


def test_electrical_resolves_led_count_calc_module() -> None:
    result = validate_sold_graph(
        mode="component_subset",
        sold_modules=["ELECTRICAL"],
        template_code=TEMPLATE,
    )
    assert "LED_COUNT" in result.resolved_calc_modules
    assert "GEOMETRY" in result.resolved_calc_modules
