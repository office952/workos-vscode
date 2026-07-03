"""Sprint #23 — Seed integrity & idempotency guard.

Three hard guarantees, enforced at the DB level AFTER `seed_sync_all`
has been run (the orchestrator is invoked inside each test so the
tests are self-contained and reproducible on any environment):

1. **Coverage guard** — NO `product_templates` row in the DB has a
   formula-based line with `coverage_pct > 1`. Failure prints the
   exact path (`template_code / component_id / materials[i] / coverage_pct`).

2. **TPL-ACP-LIGHT-ROUTED ACP split** — the template has exactly TWO
   `MAT-ACP-3MM` formula-based lines inside `comp_fata_acp_routata`,
   with `coverage_pct` values `1.00` and `0.42` (spec §2.2).

3. **Idempotency** — running `seed_sync_all` twice produces:
   - identical row counts across the 4 seeded tables, and
   - byte-identical `components_json` on `TPL-ACP-LIGHT-ROUTED`.

No CostEngine, QuoteOrchestrator, router, or seed logic is touched or
monkey-patched in these tests.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest
from sqlalchemy import func, select

import models  # noqa: F401 — register all models
from core.database import db_manager
from models.inventory_materials import Inventory_materials
from models.product_families import Product_families
from models.product_templates import Product_templates
from models.workcenter_rates import Workcenter_rates
from scripts.seed_sync_all import run_all_seeds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _components(row: Product_templates) -> List[Dict[str, Any]]:
    """Return `components_json` decoded to a list of component dicts.

    Defensive: some legacy rows store `components_json` as a JSON string
    that itself contains a JSON string (double-encoded). We peel until
    we reach a list and then filter out non-dict entries so callers can
    safely `.get(...)` on every element.
    """
    raw: Any = row.components_json
    if raw is None:
        return []
    # Peel string layers (handles double-encoded JSON).
    for _ in range(3):
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return []
        else:
            break
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


async def _counts() -> Dict[str, int]:
    async with db_manager.async_session_maker() as session:
        fam = await session.execute(select(func.count()).select_from(Product_families))
        wc = await session.execute(select(func.count()).select_from(Workcenter_rates))
        mat = await session.execute(
            select(func.count()).select_from(Inventory_materials)
        )
        tpl = await session.execute(
            select(func.count()).select_from(Product_templates)
        )
        return {
            "product_families": fam.scalar_one(),
            "workcenter_rates": wc.scalar_one(),
            "inventory_materials": mat.scalar_one(),
            "product_templates": tpl.scalar_one(),
        }


async def _tpl_acp_row() -> Product_templates:
    async with db_manager.async_session_maker() as session:
        res = await session.execute(
            select(Product_templates).where(
                Product_templates.template_code == "TPL-ACP-LIGHT-ROUTED"
            )
        )
        row = res.scalar_one_or_none()
    assert row is not None, "TPL-ACP-LIGHT-ROUTED missing after seed_sync_all"
    return row


async def _tpl_acp_components_json_raw() -> str:
    """Return the raw `components_json` string for byte-level comparison."""
    row = await _tpl_acp_row()
    raw = row.components_json
    if isinstance(raw, str):
        return raw
    # Normalize to a canonical JSON string so comparison is stable.
    return json.dumps(raw, ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------------------
# Test 1 — Coverage guard (NO coverage_pct > 1 anywhere)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_no_coverage_pct_above_one_in_any_template():
    """No formula-based line may declare coverage_pct > 1.

    coverage_pct semantically means "fraction of front_face covered by
    this line" and must therefore lie in (0, 1]. A value >1 indicates
    a stale seed or a hand-edit bypassing the canonical split rule
    (cf. Sprint #22.1 bug: TPL-ACP-LIGHT-ROUTED had coverage_pct=1.42).
    """
    await run_all_seeds()

    violations: List[str] = []
    async with db_manager.async_session_maker() as session:
        res = await session.execute(select(Product_templates))
        rows = res.scalars().all()

    for row in rows:
        comps = _components(row)
        for ci, comp in enumerate(comps):
            mats = comp.get("materials") or []
            for mi, mat in enumerate(mats):
                params = mat.get("formula_params") or {}
                cov = params.get("coverage_pct")
                if cov is None:
                    continue
                try:
                    cov_f = float(cov)
                except (TypeError, ValueError):
                    continue
                if cov_f > 1.0:
                    violations.append(
                        f"{row.template_code} / components[{ci}]"
                        f"({comp.get('component_id')}) / materials[{mi}]"
                        f"({mat.get('material_code')}) / "
                        f"coverage_pct={cov_f}"
                    )

    assert not violations, (
        "coverage_pct > 1 detected (stale DB / bypassed split rule):\n  - "
        + "\n  - ".join(violations)
    )


# ---------------------------------------------------------------------------
# Test 2 — TPL-ACP-LIGHT-ROUTED ACP split = [1.00, 0.42]
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_tpl_acp_light_routed_acp_split_is_1_00_and_0_42():
    """`comp_fata_acp_routata` must have exactly 2 MAT-ACP-3MM lines
    with coverage_pct 1.00 and 0.42 (canonical split from spec §2.2)."""
    await run_all_seeds()
    row = await _tpl_acp_row()
    comps = _components(row)

    fata = next(
        (c for c in comps if c.get("component_id") == "comp_fata_acp_routata"),
        None,
    )
    assert fata is not None, "comp_fata_acp_routata missing"

    acp_lines = [
        m
        for m in (fata.get("materials") or [])
        if m.get("material_code") == "MAT-ACP-3MM"
        and m.get("calculation_type") == "formula_based"
    ]
    assert len(acp_lines) == 2, (
        f"Expected exactly 2 MAT-ACP-3MM formula_based lines in "
        f"comp_fata_acp_routata, got {len(acp_lines)}"
    )

    coverages = sorted(
        float((m.get("formula_params") or {}).get("coverage_pct"))
        for m in acp_lines
    )
    assert coverages == [0.42, 1.00], (
        f"Expected ACP coverage split [0.42, 1.00], got {coverages}"
    )

    # And each line must stay within the formula handler contract.
    for m in acp_lines:
        cov = float((m.get("formula_params") or {}).get("coverage_pct"))
        assert 0.0 < cov <= 1.0, f"coverage_pct {cov} out of (0, 1]"


# ---------------------------------------------------------------------------
# Test 3 — Idempotency: 2nd run = 1st run (counts + tpl json byte-identical)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_seed_sync_is_idempotent_on_second_run():
    """Running `seed_sync_all` twice in a row must be a no-op on the
    2nd pass: identical row counts and byte-identical template JSON."""
    # Run #1
    await run_all_seeds()
    counts_1 = await _counts()
    tpl_json_1 = await _tpl_acp_components_json_raw()

    # Run #2
    await run_all_seeds()
    counts_2 = await _counts()
    tpl_json_2 = await _tpl_acp_components_json_raw()

    assert counts_1 == counts_2, (
        f"Row counts drifted between runs:\n  run1={counts_1}\n  run2={counts_2}"
    )
    assert tpl_json_1 == tpl_json_2, (
        "TPL-ACP-LIGHT-ROUTED.components_json changed between runs "
        "(non-idempotent upsert)"
    )