"""Tests for TPL-ACP-LIGHT-ROUTED seed (Sprint #21.2 REWORK).

Locks the canonical contract of the first real production template:

- 6 canonical components in the exact order defined by the spec
  (`docs/spec/spec__product_template__tpl_acp_light_routed.md` §2).
- Every referenced material_code / workcenter resolves against the
  Sprint #20 registries.
- Every `calculation_type=="formula_based"` line references a known
  `FormulaId` and declares non-empty `requires_quote_input`.
- CNC operations use distinct `path_length_key`s so geometry inputs
  cannot collide between ACP routing / diffuser cut / relief cut.
- The relief component uses `passes=4` (template-owned, Sprint #21.1.5).
- Seed is idempotent on `template_code`.
- End-to-end CostEngine v2 run:
    * Case A (empty quote_input) → `is_valid=False` with at least one
      `NEEDS_QUOTE_INPUT` per formula-based line.
    * Case B (full realistic quote_input) → `is_valid=True`,
      `source="hierarchical"`, deterministic totals including:
        - relief CNC minutes = 8.0 (4000mm / 2000 / min × 4 passes),
        - PSU count = 1 × 100 W (55 LEDs × 1.44 × 1.2 = 95.04 W).
- Sprint #21.1.5 handler outputs remain byte-for-byte compatible: the
  legacy `path_length_mm` + `passes` quote_input call still produces
  the exact same `FormulaResult.value`.
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401 - register all models
from models.inventory_materials import Inventory_materials
from models.product_templates import Product_templates
from models.workcenter_rates import Workcenter_rates

from scripts.seed_tpl_acp_light_routed import (
    COMPONENTS,
    TEMPLATE_CODE,
    FAMILY_ID,
    seed_tpl_acp_light_routed,
)
from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs
from seeds.seed_workcenter_rates import seed_workcenter_rates
from services.cost_engine_service import (
    ComponentCostContext,
    ERR_NEEDS_QUOTE_INPUT,
    build_execution_layers_from_components,
)
from services.formula_handlers import FormulaId, known_formulas, resolve_formula
from tests._db_fixture import IsolatedDBFixture


# ---------------------------------------------------------------------------
# Isolated DB fixture — shared helper from Sprint #20 (tests/_db_fixture.py).
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def isolated_db():
    """Isolated SQLite DB patched onto `core.database.db_manager`.

    Uses the canonical `IsolatedDBFixture` so the test ordering behaviour
    matches the rest of the Sprint #20 / Sprint #20.5 suites (no shared
    engine between suites, clean teardown).
    """
    fixture = IsolatedDBFixture(prefix="mgx_tpl_acp_")
    fixture.setup()
    try:
        yield fixture
    finally:
        fixture.teardown()


# ---------------------------------------------------------------------------
# Canonical constants from the spec (DO NOT relax — these ARE the contract)
# ---------------------------------------------------------------------------
EXPECTED_COMPONENT_IDS: List[str] = [
    "comp_structura",
    "comp_fata_acp_routata",
    "comp_difuzie_plexi",
    "comp_iluminare",
    "comp_relief_plexi_10mm",
    "comp_finisaj",
]

EXPECTED_COMPONENT_TYPES: List[str] = [
    "STRUCTURA",
    "FATA_ACP_ROUTATA",
    "DIFUZIE_PLEXI",
    "ILUMINARE",
    "RELIEF_PLEXI_10MM",
    "FINISAJ",
]

EXPECTED_MATERIAL_CODES = {
    "MAT-ACP-3MM",
    "MAT-PLEXI-OPAL-3MM",
    "MAT-PLEXI-OPAL-10MM",
    "MAT-LED-MODULE",
    "MAT-LED-PSU-12V",
    "MAT-PROFIL-ALU",
    "MAT-SURUBURI-GEN",
    "MAT-ADEZIV-SILICON",
    "MAT-CONSUMABILE-MONTAJ",
}

EXPECTED_WORKCENTERS = {
    "CNC_ROUTER",
    "PANEL_CUTTING",
    "LED_ASSEMBLY",
    "ASSEMBLY",
    "FINISHING",
    "INSTALL_PREP",
}


def _iter_all_lines(components: List[Dict[str, Any]]):
    """Yield (component_id, section, index, entry) for every line."""
    for c in components:
        for i, mat in enumerate(c.get("materials") or []):
            yield c["component_id"], "materials", i, mat
        for i, op in enumerate(c.get("operations") or []):
            yield c["component_id"], "operations", i, op


# ===========================================================================
# Test 1 — seed is idempotent
# ===========================================================================
def test_seed_is_idempotent(isolated_db):
    async def _run():
        r1 = await seed_tpl_acp_light_routed()
        r2 = await seed_tpl_acp_light_routed()
        async with db_manager.async_session_maker() as session:
            rows = (
                await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == TEMPLATE_CODE
                    )
                )
            ).scalars().all()
        return r1, r2, rows

    r1, r2, rows = isolated_db.run(_run())
    assert r1["inserted"] == 1 and r1["skipped"] == 0
    assert r2["inserted"] == 0 and r2["skipped"] == 1
    assert len(rows) == 1, "seed must not duplicate on re-run"
    assert rows[0].template_code == TEMPLATE_CODE
    assert rows[0].family_id == FAMILY_ID
    assert rows[0].active is True


# ===========================================================================
# Test 2 — template stores the 6 canonical components in the correct order
# ===========================================================================
def test_template_has_six_canonical_components(isolated_db):
    async def _run():
        await seed_tpl_acp_light_routed()
        async with db_manager.async_session_maker() as session:
            row = (
                await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == TEMPLATE_CODE
                    )
                )
            ).scalar_one()
        return row.components_json, row.operations_json, row.required_materials_json

    components_json, ops_json, mats_json = isolated_db.run(_run())

    assert components_json, "components_json must be populated"
    # v2 hierarchical → ops/materials live inside components.
    assert ops_json is None, "operations_json must be NULL in hierarchical mode"
    assert mats_json is None, (
        "required_materials_json must be NULL in hierarchical mode"
    )

    parsed = json.loads(components_json)
    assert isinstance(parsed, list) and len(parsed) == 6, (
        "template must have exactly 6 components (spec §2)"
    )
    assert [c["component_id"] for c in parsed] == EXPECTED_COMPONENT_IDS
    assert [c["type"] for c in parsed] == EXPECTED_COMPONENT_TYPES
    # All components carry `materials` + `operations` lists — shape required
    # by CostEngine v2 hierarchical detection.
    for c in parsed:
        assert isinstance(c.get("materials"), list), c["component_id"]
        assert isinstance(c.get("operations"), list), c["component_id"]


# ===========================================================================
# Test 3 — every material_code exists in the Inventory_materials registry
# ===========================================================================
def test_all_material_codes_exist_in_registry(isolated_db):
    async def _run():
        await seed_inventory_material_stubs()
        async with db_manager.async_session_maker() as session:
            rows = (
                await session.execute(select(Inventory_materials))
            ).scalars().all()
        return {r.code for r in rows}

    registry_codes = isolated_db.run(_run())
    # Seeded stubs cover all codes referenced by the template.
    referenced = {
        mat["material_code"]
        for c in COMPONENTS
        for mat in c.get("materials") or []
    }
    assert referenced == EXPECTED_MATERIAL_CODES, (
        f"Template references unexpected material set: {referenced}"
    )
    missing = referenced - registry_codes
    assert not missing, (
        f"template references material codes not in Inventory_materials: {missing}"
    )


# ===========================================================================
# Test 4 — every workcenter exists in the Workcenter_rates registry
# ===========================================================================
def test_all_workcenters_exist_in_registry(isolated_db):
    async def _run():
        await seed_workcenter_rates()
        async with db_manager.async_session_maker() as session:
            rows = (
                await session.execute(select(Workcenter_rates))
            ).scalars().all()
        return {r.code for r in rows}

    registry_codes = isolated_db.run(_run())
    referenced = {
        op["workcenter"]
        for c in COMPONENTS
        for op in c.get("operations") or []
    }
    assert referenced == EXPECTED_WORKCENTERS, (
        f"Template references unexpected workcenter set: {referenced}"
    )
    missing = referenced - registry_codes
    assert not missing, (
        f"template references workcenters not in Workcenter_rates: {missing}"
    )


# ===========================================================================
# Test 5 — formula-based lines all reference known FormulaId + declare
#           non-empty requires_quote_input + distinct path_length_key per CNC op
# ===========================================================================
def test_formula_ids_and_quote_input_contract():
    known = set(known_formulas())
    formula_lines_found = 0
    cnc_path_keys: List[str] = []

    for component_id, section, index, entry in _iter_all_lines(COMPONENTS):
        if entry.get("calculation_type") != "formula_based":
            continue
        formula_lines_found += 1

        fid = entry.get("formula_id")
        assert isinstance(fid, str) and fid in known, (
            f"{component_id}.{section}[{index}] uses unknown formula_id={fid!r}; "
            f"known={sorted(known)}"
        )
        # Enum lookup must succeed (guards against typos like 'cnc_time').
        FormulaId(fid)

        req = entry.get("requires_quote_input")
        assert isinstance(req, list) and len(req) > 0, (
            f"{component_id}.{section}[{index}] must declare non-empty "
            f"requires_quote_input"
        )
        for key in req:
            assert isinstance(key, str) and key, (
                f"{component_id}.{section}[{index}].requires_quote_input "
                f"contains an empty/non-string key"
            )

        # Sprint #21.1.5: CNC ops must declare a distinct path_length_key.
        if fid == FormulaId.CNC_TIME_FROM_PATH.value:
            params = entry.get("formula_params") or {}
            key = params.get("path_length_key")
            assert isinstance(key, str) and key, (
                f"{component_id}.{section}[{index}] uses cnc_time_from_path "
                f"but does not set path_length_key in formula_params"
            )
            assert key in req, (
                f"{component_id}.{section}[{index}].path_length_key={key!r} "
                f"must be declared in requires_quote_input={req}"
            )
            cnc_path_keys.append(key)

    # Sanity: the spec mandates at least 6 formula-based lines. With the
    # Sprint #21.2 REWORK split of ACP into base+flange lines, the actual
    # count is 7, but downstream code only relies on the lower bound.
    assert formula_lines_found >= 6, (
        f"expected >= 6 formula_based lines; found {formula_lines_found}"
    )
    # Every CNC op MUST have its own distinct path_length_key.
    assert len(cnc_path_keys) == len(set(cnc_path_keys)), (
        f"CNC operations must use distinct path_length_key values; "
        f"got {cnc_path_keys}"
    )
    # And specifically 3 CNC ops (ACP route, diffuser cut, relief cut).
    assert len(cnc_path_keys) == 3, (
        f"expected exactly 3 CNC operations (ACP, diffuser, relief); "
        f"got {cnc_path_keys}"
    )


# ===========================================================================
# Test 6 — relief component uses template-owned passes=4 (Sprint #21.1.5)
# ===========================================================================
def test_relief_component_uses_four_passes():
    relief = next(
        (c for c in COMPONENTS if c["component_id"] == "comp_relief_plexi_10mm"),
        None,
    )
    assert relief is not None, "comp_relief_plexi_10mm must exist"
    ops = relief["operations"]
    assert len(ops) == 1
    op = ops[0]
    assert op["code"] == "CNC_RELIEF"
    assert op["workcenter"] == "CNC_ROUTER"
    assert op["formula_id"] == FormulaId.CNC_TIME_FROM_PATH.value
    params = op["formula_params"]
    assert params["passes"] == 4, (
        "10mm plexi relief must be routed in 4 passes per spec §2.5"
    )
    # passes lives in params, NOT in requires_quote_input (Sprint #21.1.5).
    assert "passes" not in op["requires_quote_input"], (
        "passes is template-owned; callers MUST NOT override it per quote"
    )
    assert params["path_length_key"] == "relief_cut_path_length_mm"
    assert op["requires_quote_input"] == ["relief_cut_path_length_mm"]


# ===========================================================================
# Test 7 — Case A: empty quote_input → NEEDS_QUOTE_INPUT on every formula line
# ===========================================================================
def test_case_a_empty_quote_input_flags_needs_quote_input():
    template = {
        "template_code": TEMPLATE_CODE,
        "components_json": json.dumps(COMPONENTS, ensure_ascii=False),
        "operations_json": None,
        "required_materials_json": None,
    }
    # Provide active rates so the ONLY errors come from missing quote inputs.
    ctx = ComponentCostContext(
        material_rates={code: 100.0 for code in EXPECTED_MATERIAL_CODES},
        workcenter_rates={wc: 60.0 for wc in EXPECTED_WORKCENTERS},
        quantity=1,
        quote_input={},
    )
    result = build_execution_layers_from_components(template, ctx)

    assert result["is_valid"] is False
    assert result["source"] == "hierarchical"
    assert len(result["components"]) == 6

    # Count the exact formula-based lines in the spec = must match the
    # number of NEEDS_QUOTE_INPUT errors emitted when quote_input is empty.
    formula_line_count = sum(
        1
        for _, _, _, entry in _iter_all_lines(COMPONENTS)
        if entry.get("calculation_type") == "formula_based"
    )
    needs = [
        e for e in result["errors"] if e["kind"] == ERR_NEEDS_QUOTE_INPUT
    ]
    assert len(needs) == formula_line_count, (
        f"expected one NEEDS_QUOTE_INPUT per formula-based line "
        f"({formula_line_count}); got {len(needs)}: {needs}"
    )


# ===========================================================================
# Test 8 — Case B: full realistic quote_input → is_valid=True with canonical
#                   numeric assertions from the spec §5
# ===========================================================================
def test_case_b_full_quote_input_returns_valid_with_canonical_numbers():
    template = {
        "template_code": TEMPLATE_CODE,
        "components_json": json.dumps(COMPONENTS, ensure_ascii=False),
        "operations_json": None,
        "required_materials_json": None,
    }
    ctx = ComponentCostContext(
        material_rates={code: 100.0 for code in EXPECTED_MATERIAL_CODES},
        workcenter_rates={wc: 60.0 for wc in EXPECTED_WORKCENTERS},
        quantity=1,
        quote_input={
            "front_face_area_m2": 1.0,
            "personalization_path_length_mm": 3000.0,
            "personalization_bounding_area_m2": 0.6,
            "diffuser_cut_path_length_mm": 4000.0,
            "led_count": 55,
            "relief_cut_path_length_mm": 4000.0,
        },
    )
    result = build_execution_layers_from_components(template, ctx)

    assert result["is_valid"] is True, (
        f"expected is_valid=True; errors={result['errors']}"
    )
    assert result["source"] == "hierarchical"
    assert result["total_cost"] > 0

    # Index by component_id for readability.
    by_id = {c["component_id"]: c for c in result["components"]}

    # --- Relief CNC: 4000mm / 2000 × 4 passes = 8.0 minutes (spec §5) ---
    relief = by_id["comp_relief_plexi_10mm"]
    relief_cnc = next(
        op
        for op in relief["operations_detail"]
        if op["code"] == "CNC_RELIEF"
    )
    assert relief_cnc["estimated_minutes"] == pytest.approx(8.0, abs=1e-6), (
        f"relief CNC must be 8.0 min (4000/2000 × 4); got "
        f"{relief_cnc['estimated_minutes']}"
    )
    assert relief_cnc["resolved"] is True
    assert relief_cnc["formula_breakdown"]["passes_source"] == "params"

    # --- PSU sizing: 55 × 1.44 × 1.2 = 95.04W → picked 100W → count=1 ---
    ilum = by_id["comp_iluminare"]
    psu = next(
        m
        for m in ilum["materials_detail"]
        if m["material_code"] == "MAT-LED-PSU-12V"
    )
    assert psu["quantity"] == pytest.approx(1.0, abs=1e-6), (
        f"PSU count must be 1 for 55 LEDs; got {psu['quantity']}"
    )
    assert psu["formula_breakdown"]["psu_watts_picked"] == 100.0
    assert psu["formula_breakdown"]["total_watts"] == pytest.approx(
        95.04, abs=1e-6
    )

    # --- ACP area: front_face × 1.42 = 1.42 m² (split into 1.00 + 0.42
    #     because the relief_material_area handler caps coverage at 1).
    acp_face = by_id["comp_fata_acp_routata"]
    acp_lines = [
        m
        for m in acp_face["materials_detail"]
        if m["material_code"] == "MAT-ACP-3MM"
    ]
    assert len(acp_lines) == 2, (
        "ACP material must be encoded as 2 lines (base 1.00 + flange/waste "
        "0.42) because relief_material_area caps coverage_pct at 1"
    )
    acp_qty_total = sum(m["quantity"] for m in acp_lines)
    assert acp_qty_total == pytest.approx(1.42, abs=1e-6)
    acp_coverages = sorted(
        m["formula_breakdown"]["coverage_pct"] for m in acp_lines
    )
    assert acp_coverages == pytest.approx([0.42, 1.00], abs=1e-6)

    # --- Relief material: front_face × 0.30 = 0.30 m² ---
    relief_mat = next(
        m
        for m in relief["materials_detail"]
        if m["material_code"] == "MAT-PLEXI-OPAL-10MM"
    )
    assert relief_mat["quantity"] == pytest.approx(0.30, abs=1e-6)

    # --- LED count: ceil(1.0 × 55) = 55 ---
    led_mat = next(
        m
        for m in ilum["materials_detail"]
        if m["material_code"] == "MAT-LED-MODULE"
    )
    assert led_mat["quantity"] == pytest.approx(55.0, abs=1e-6)

    # --- LED assembly: max(55/3, 15) = 18.333... min ---
    led_mount = next(
        op
        for op in ilum["operations_detail"]
        if op["code"] == "LED_MOUNT"
    )
    assert led_mount["estimated_minutes"] == pytest.approx(55 / 3.0, abs=1e-3)


# ===========================================================================
# Test 9 — Sprint #21.1.5 byte-compatibility: legacy direct-handler call
#           still produces the exact same FormulaResult as before.
# ===========================================================================
def test_handler_backward_compatibility_unchanged():
    # Pre-Sprint-21.1.5 style: divisor only, passes from quote_input,
    # default path_length_key="path_length_mm".
    legacy = resolve_formula(
        "cnc_time_from_path",
        {"divisor_mm_per_min": 2000.0},
        {"path_length_mm": 4000.0, "passes": 4},
    )
    assert legacy.resolved is True
    assert legacy.value == pytest.approx(8.0, abs=1e-6)
    assert legacy.breakdown["passes_source"] == "quote_input"
    assert legacy.breakdown["path_length_key"] == "path_length_mm"

    # New template-owned style (what this seed uses):
    new_style = resolve_formula(
        "cnc_time_from_path",
        {
            "divisor_mm_per_min": 2000.0,
            "passes": 4,
            "path_length_key": "relief_cut_path_length_mm",
        },
        {"relief_cut_path_length_mm": 4000.0},
    )
    assert new_style.resolved is True
    assert new_style.value == pytest.approx(8.0, abs=1e-6)
    assert new_style.breakdown["passes_source"] == "params"
    assert new_style.breakdown["path_length_key"] == "relief_cut_path_length_mm"

    # Both code paths must produce the SAME numeric minutes — proves the
    # Sprint #21.1.5 extension is strictly additive.
    assert legacy.value == new_style.value