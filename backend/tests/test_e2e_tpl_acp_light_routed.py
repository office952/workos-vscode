"""Sprint #21.3 — Automated end-to-end test for `TPL-ACP-LIGHT-ROUTED`.

Drives the CostEngine v2 directly (the same way the sprint driver script
does) and asserts the canonical numeric invariants defined in the sprint
contract.

Case B (VALID) — 1000×1000mm, qty=1, led_count=55, relief_cut=4000mm:
  - is_valid == True, source == "hierarchical"
  - len(components) == 6
  - ACP component (comp[1]) has 2 material lines totalling 1.42 m²
  - LED component (comp[3]) has MAT-LED-MODULE with quantity == 55
  - Relief CNC operation (comp[4]) resolves to 8.0 minutes
    (4000 mm ÷ 2000 mm·min⁻¹ × 4 passes = 8 min)
  - errors == [], warnings == []

Case A (INVALID) — empty quote_input:
  - is_valid == False, source == "hierarchical"
  - ≥10 errors, every one of kind NEEDS_QUOTE_INPUT

NO CostEngine / Orchestrator / Router source files are modified or
imported-for-edit here; only public service APIs are exercised.
"""

from __future__ import annotations

import pytest

from scripts.e2e_test_tpl_acp_light_routed import (
    CASE_B_QUOTE_INPUT,
    USER_CONFIG,
    _load_rate_registries,
    _load_template,
    _seed_all,
    run_case_a_direct,
    run_case_b_direct,
)
from tests._db_fixture import IsolatedDBFixture


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------
@pytest.fixture()
def seeded_context():
    """Seed registries + template, then return (template, mat_rates, wc_rates)."""
    db = IsolatedDBFixture()
    db.setup()
    try:
        db.run(_seed_all())
        mat_rates, wc_rates = db.run(_load_rate_registries(db))
        template = db.run(_load_template(db))
        yield template, mat_rates, wc_rates
    finally:
        db.teardown()


# ---------------------------------------------------------------------------
# Case B — VALID
# ---------------------------------------------------------------------------
def test_case_b_valid_full_breakdown(seeded_context):
    template, mat_rates, wc_rates = seeded_context
    result = run_case_b_direct(template, mat_rates, wc_rates)

    assert result["is_valid"] is True
    assert result["source"] == "hierarchical"
    assert result["errors"] == []
    assert result["warnings"] == []
    assert len(result["components"]) == 6

    # Component 1 (ACP panels): 2 material lines, 1.42 m² total (1.00 + 0.42).
    acp_comp = result["components"][1]
    acp_mats = acp_comp["materials_detail"]
    assert len(acp_mats) == 2
    assert {m["material_code"] for m in acp_mats} == {"MAT-ACP-3MM"}
    total_m2 = sum(m["quantity"] for m in acp_mats)
    assert round(total_m2, 4) == 1.42

    # Component 3 (LED assembly): LED module qty follows user-provided led_count=55.
    led_comp = result["components"][3]
    led_mat = next(
        m
        for m in led_comp["materials_detail"]
        if m["material_code"] == "MAT-LED-MODULE"
    )
    assert led_mat["quantity"] == 55.0

    # Component 4 (Relief CNC): 4000 mm ÷ 2000 mm·min⁻¹ × 4 passes = 8 minutes.
    relief_op = result["components"][4]["operations_detail"][0]
    assert relief_op["workcenter"] == "CNC_ROUTER"
    assert relief_op["formula_id"] == "cnc_time_from_path"
    assert round(relief_op["estimated_minutes"], 2) == 8.0


# ---------------------------------------------------------------------------
# Case A — INVALID
# ---------------------------------------------------------------------------
def test_case_a_invalid_missing_quote_input(seeded_context):
    template, mat_rates, wc_rates = seeded_context
    result = run_case_a_direct(template, mat_rates, wc_rates)

    assert result["is_valid"] is False
    assert result["source"] == "hierarchical"

    errors = result["errors"]
    assert len(errors) >= 10
    kinds = {e["kind"] for e in errors}
    assert kinds == {"NEEDS_QUOTE_INPUT"}


# ---------------------------------------------------------------------------
# Contract sanity — sprint-locked driver constants
# ---------------------------------------------------------------------------
def test_e2e_contract_constants_are_stable():
    assert USER_CONFIG["product_id"] == "TPL-ACP-LIGHT-ROUTED"
    assert USER_CONFIG["quantity"] == 1
    assert USER_CONFIG["dimensions"] == {
        "width_mm": 1000,
        "height_mm": 1000,
        "depth_mm": 0,
    }
    assert CASE_B_QUOTE_INPUT["led_count"] == 55
    assert CASE_B_QUOTE_INPUT["relief_cut_path_length_mm"] == 4000.0