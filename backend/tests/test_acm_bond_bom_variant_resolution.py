"""ACM bond panel variant resolution in aggregate cost BOM (W3-INT-01)."""

from __future__ import annotations

from services.acm_bond_material_rate_resolver import TEMPLATE_ACM_BOND_CODE
from services.aggregate_cost_bom_adapter import _resolve_material_code


def test_acm_bond_panel_resolves_thickness_variant_from_values() -> None:
    resolved, keys, err = _resolve_material_code(
        TEMPLATE_ACM_BOND_CODE,
        {"acm_thickness_mm": 3},
    )
    assert err is None
    assert resolved == "MAT-ACM-BOND-3MM"
    assert keys == ["acm_thickness_mm"]


def test_acm_bond_panel_missing_thickness_returns_variant_error() -> None:
    resolved, keys, err = _resolve_material_code(TEMPLATE_ACM_BOND_CODE, {})
    assert resolved == TEMPLATE_ACM_BOND_CODE
    assert err == "missing_acm_thickness_mm"
    assert keys == ["acm_thickness_mm"]
