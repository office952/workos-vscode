"""Sprint #21.3 — End-to-end real test for `TPL-ACP-LIGHT-ROUTED`.

Goal
----
Exercise the production template seeded in Sprint #21.2 through a real
`POST /api/v1/entities/quotes/price` call — exactly the way a frontend
client would drive a pricing request today — AND (because the HTTP
contract does not yet expose `quote_input`) re-run the same two cases
directly through `QuoteOrchestrator` + `CostEngine v2` with the rate
registries loaded from `Inventory_materials` and `Workcenter_rates`.

What this script does
---------------------
1. Sets up an isolated SQLite DB via `IsolatedDBFixture`.
2. Seeds `workcenter_rates`, `inventory_materials`, and the template
   itself (`TPL-ACP-LIGHT-ROUTED`) from the Sprint #20 / #21.2 seeds.
3. Loads the real rate registries from the seeded tables.
4. Loads the seeded template row.
5. **Case B (valid)** — calls the orchestrator with full `quote_input`;
   dumps the component-level breakdown JSON.
6. **Case A (invalid)** — calls the orchestrator with empty
   `quote_input`; dumps the `NEEDS_QUOTE_INPUT` error list.
7. **HTTP probe** — calls `POST /api/v1/entities/quotes/price` via
   `TestClient` to prove whether the HTTP endpoint exposes the v2
   flow (it does NOT, as of Sprint #21.2 — see the log for details).
8. Writes two JSON files to `docs/proof/`:
     - `sprint21_3_case_b_valid.json`
     - `sprint21_3_case_a_invalid.json`

Strict scope
------------
- NO modifications to `cost_engine_service.py`, `formula_handlers.py`,
  `quote_orchestrator.py`, any router, or the frontend.
- NO new migrations.
- This script is read/compute only; every write is a seed call that is
  already idempotent.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure `app/backend` is on the path when invoked from anywhere.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import models  # noqa: F401  — register every model onto Base.metadata
from models.inventory_materials import Inventory_materials
from models.product_templates import Product_templates
from models.workcenter_rates import Workcenter_rates
from scripts.fill_registry_values_sprint20_5 import (
    _fill_material_prices,
    _fill_workcenter_rates,
)
from scripts.seed_tpl_acp_light_routed import (
    TEMPLATE_CODE,
    seed_tpl_acp_light_routed,
)
from seeds.seed_inventory_materials_stubs import seed_inventory_material_stubs
from seeds.seed_workcenter_rates import seed_workcenter_rates
from services.cost_engine_service import (
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.quote_orchestrator import QuoteOrchestrator
from data_models.product_contracts import PricingContext, QuotePricing
from sqlalchemy import select
from tests._db_fixture import IsolatedDBFixture


# ---------------------------------------------------------------------------
# The canonical Case B payload (quote_input) — matches the contract in
# `docs/spec/spec__product_template__tpl_acp_light_routed.md` §3.
# ---------------------------------------------------------------------------
CASE_B_QUOTE_INPUT: Dict[str, Any] = {
    "front_face_area_m2": 1.0,
    "personalization_path_length_mm": 3000.0,
    "personalization_bounding_area_m2": 0.6,
    "diffuser_cut_path_length_mm": 4000.0,
    "led_count": 55,
    "relief_cut_path_length_mm": 4000.0,
}

# user_config shared by both cases — 1000×1000mm, qty=1, width/height > 0.
USER_CONFIG: Dict[str, Any] = {
    "product_id": TEMPLATE_CODE,
    "quantity": 1,
    "dimensions": {"width_mm": 1000, "height_mm": 1000, "depth_mm": 0},
}


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------
async def _seed_all() -> None:
    """Run all seeds required for a realistic end-to-end pass.

    Order matters:
      1. Sprint #20   — stubs (rows with NULL rates, status=\'missing_price\').
      2. Sprint #20.5 — fill real CFO-provided rates (status→\'active\').
      3. Sprint #21.2 — canonical `TPL-ACP-LIGHT-ROUTED` template.
    """
    await seed_workcenter_rates()
    await seed_inventory_material_stubs()
    await _fill_workcenter_rates()
    await _fill_material_prices()
    await seed_tpl_acp_light_routed()


async def _load_rate_registries(db) -> Tuple[Dict[str, float], Dict[str, float]]:
    async with db.session_maker() as session:
        mat_rows = (await session.execute(select(Inventory_materials))).scalars().all()
        wc_rows = (await session.execute(select(Workcenter_rates))).scalars().all()
    material_rates = {
        r.code: float(r.unit_cost or 0.0) for r in mat_rows if r.unit_cost is not None
    }
    workcenter_rates = {
        r.code: float(r.rate_per_hour or 0.0)
        for r in wc_rows
        if r.rate_per_hour is not None
    }
    return material_rates, workcenter_rates


async def _load_template(db) -> Dict[str, Any]:
    async with db.session_maker() as session:
        row = (
            await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == TEMPLATE_CODE
                )
            )
        ).scalar_one()
    # Convert the ORM row into the plain-dict shape `QuoteOrchestrator`
    # and `build_execution_layers_from_components` expect.
    return {
        "id": row.id,
        "template_code": row.template_code,
        "family_id": row.family_id,
        "family_name": "Panouri ACP Iluminate",
        "active": bool(row.active),
        "components_json": row.components_json,
        "operations_json": row.operations_json,
        "required_materials_json": row.required_materials_json,
    }


# ---------------------------------------------------------------------------
# Direct orchestrator / cost-engine runs (the authoritative end-to-end path
# because the HTTP endpoint does not yet accept `quote_input`).
# ---------------------------------------------------------------------------
def run_case_b_direct(
    template: Dict[str, Any],
    material_rates: Dict[str, float],
    workcenter_rates: Dict[str, float],
) -> Dict[str, Any]:
    """Case B — full quote_input, expected to succeed."""
    ctx = ComponentCostContext(
        material_rates=dict(material_rates),
        workcenter_rates=dict(workcenter_rates),
        quantity=1,
        quote_input=dict(CASE_B_QUOTE_INPUT),
    )
    return build_execution_layers_from_components(template, ctx)


def run_case_a_direct(
    template: Dict[str, Any],
    material_rates: Dict[str, float],
    workcenter_rates: Dict[str, float],
) -> Dict[str, Any]:
    """Case A — empty quote_input, expected to flag NEEDS_QUOTE_INPUT per formula line."""
    ctx = ComponentCostContext(
        material_rates=dict(material_rates),
        workcenter_rates=dict(workcenter_rates),
        quantity=1,
        quote_input={},
    )
    return build_execution_layers_from_components(template, ctx)


def run_case_b_orchestrator(
    template: Dict[str, Any],
    material_rates: Dict[str, float],
    workcenter_rates: Dict[str, float],
) -> Dict[str, Any]:
    """Case B — invoked through `QuoteOrchestrator.build_snapshot()` so the
    commercial transform and the v2-vs-v1 routing decision are exercised."""
    # Inject the quote_input as `user_config['quote_input']` — the orchestrator
    # currently reads user_config.quantity, but the v2 branch constructs a
    # ComponentCostContext() without quote_input today. To feed the template
    # we must build the context ourselves AND monkey-patch a minimal wrapper
    # so the orchestrator sees our context. We keep the change local — no
    # change to quote_orchestrator.py (Sprint #21.3 guardrail).
    orchestrator = QuoteOrchestrator(
        material_rates=material_rates,
        workcenter_rates=workcenter_rates,
    )

    # Monkey-patch build_execution_layers_from_components only on the local
    # module binding held by QuoteOrchestrator — so we can inject quote_input
    # without editing the service module. This proves the end-to-end
    # snapshot flow works AS-SOON-AS the orchestrator is taught to thread
    # `quote_input` through; it does NOT modify any committed file.
    import services.quote_orchestrator as qo_mod

    _orig = qo_mod.build_execution_layers_from_components

    def _patched(pt, ctx):
        patched_ctx = ComponentCostContext(
            material_rates=ctx.material_rates,
            workcenter_rates=ctx.workcenter_rates,
            quantity=ctx.quantity,
            quote_input=dict(CASE_B_QUOTE_INPUT),
        )
        return _orig(pt, patched_ctx)

    qo_mod.build_execution_layers_from_components = _patched
    try:
        snap = orchestrator.build_snapshot(
            product_template=template,
            user_config=USER_CONFIG,
            pricing=QuotePricing(margin_pct=0, discount_pct=0, vat_pct=0),
            pricing_context=PricingContext(currency="RON"),
        )
    finally:
        qo_mod.build_execution_layers_from_components = _orig

    return {
        "status": snap.status,
        "blocked_reasons": list(snap.blocked_reasons or []),
        "cost_engine_version": getattr(snap, "cost_engine_version", None),
        "cost_warnings": getattr(snap, "cost_warnings", None),
        "component_breakdown": getattr(snap, "component_breakdown", None),
        "price": {
            "net": None if snap.price is None else float(snap.price.net),
            "gross": None if snap.price is None else float(snap.price.gross),
            "final": None if snap.price is None else float(snap.price.final),
        },
        "cost_result": {
            "is_valid": snap.cost_result.is_valid if snap.cost_result else None,
            "total_cost": snap.cost_result.total_cost if snap.cost_result else None,
            "materials_cost": snap.cost_result.materials_cost if snap.cost_result else None,
            "labour_cost": snap.cost_result.labour_cost if snap.cost_result else None,
            "estimated_time_minutes": (
                snap.cost_result.estimated_time_minutes if snap.cost_result else None
            ),
        },
    }


# ---------------------------------------------------------------------------
# HTTP probe — documents the gap: `POST /quotes/price` does not expose
# `quote_input`, so it cannot drive `TPL-ACP-LIGHT-ROUTED` today.
# ---------------------------------------------------------------------------
def probe_http_price(template: Dict[str, Any]) -> Dict[str, Any]:
    """Best-effort probe of `POST /api/v1/entities/quotes/price` to document
    the current HTTP surface. Reports status_code + body — does NOT assert."""
    try:
        from fastapi.testclient import TestClient
        from main import app
    except Exception as e:
        return {"probe": "skipped", "reason": f"cannot import FastAPI app: {e}"}

    payload = {
        "product_template": template,
        "user_config": USER_CONFIG,
        "pricing": {"margin_pct": 0, "discount_pct": 0, "vat_pct": 0},
        "pricing_context": {"currency": "RON"},
        "client_name": "E2E Sprint #21.3",
        "code": "Q-E2E-TPL-ACP-LIGHT-ROUTED",
    }
    try:
        with TestClient(app) as client:
            resp = client.post("/api/v1/entities/quotes/price", json=payload)
        body: Any
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        return {
            "probe": "executed",
            "request_payload_keys": sorted(payload.keys()),
            "status_code": resp.status_code,
            "body": body,
            "note": (
                "The QuotePriceRequest pydantic schema does NOT expose a "
                "`quote_input` field; even a hierarchical template + full "
                "user_config cannot reach the CostEngine v2 formula layer "
                "through the HTTP route today."
            ),
        }
    except Exception as e:
        return {
            "probe": "errored",
            "error": repr(e),
            "note": "HTTP probe raised — see error detail.",
        }


# ---------------------------------------------------------------------------
# Numeric verdict — assert-free, just annotates Expected vs Actual.
# ---------------------------------------------------------------------------
def verdict_case_b(v2: Dict[str, Any]) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    def _check(label: str, expected: Any, actual: Any, tol: float = 1e-6) -> bool:
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            ok = abs(float(actual) - float(expected)) <= tol
        else:
            ok = expected == actual
        checks.append(
            {
                "check": label,
                "expected": expected,
                "actual": actual,
                "passed": ok,
            }
        )
        return ok

    by_id = {c["component_id"]: c for c in v2.get("components", [])}

    _check("is_valid", True, v2.get("is_valid"))
    _check("source", "hierarchical", v2.get("source"))
    _check("errors_count", 0, len(v2.get("errors") or []))

    # Relief CNC minutes = 8.0 (4000/2000 × 4 passes)
    relief = by_id.get("comp_relief_plexi_10mm", {})
    relief_cnc = next(
        (
            o
            for o in relief.get("operations_detail", [])
            if o.get("code") == "CNC_RELIEF"
        ),
        None,
    )
    _check(
        "relief_cnc_estimated_minutes",
        8.0,
        None if relief_cnc is None else relief_cnc.get("estimated_minutes"),
    )

    # PSU = 100W, count = 1
    ilum = by_id.get("comp_iluminare", {})
    psu = next(
        (
            m
            for m in ilum.get("materials_detail", [])
            if m.get("material_code") == "MAT-LED-PSU-12V"
        ),
        None,
    )
    _check(
        "psu_count",
        1.0,
        None if psu is None else psu.get("quantity"),
    )
    psu_breakdown = (psu or {}).get("formula_breakdown") or {}
    _check(
        "psu_watts_picked",
        100.0,
        psu_breakdown.get("psu_watts_picked"),
    )

    # ACP total = 1.42 m² (1.00 base + 0.42 flange)
    acp = by_id.get("comp_fata_acp_routata", {})
    acp_lines = [
        m
        for m in acp.get("materials_detail", [])
        if m.get("material_code") == "MAT-ACP-3MM"
    ]
    acp_total = sum(float(m.get("quantity") or 0.0) for m in acp_lines)
    _check("acp_total_m2", 1.42, round(acp_total, 6))
    _check("acp_line_count", 2, len(acp_lines))

    return {"checks": checks, "all_passed": all(c["passed"] for c in checks)}


def verdict_case_a(v2: Dict[str, Any]) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    errors = v2.get("errors") or []
    needs = [e for e in errors if e.get("kind") == "NEEDS_QUOTE_INPUT"]

    def _check(label: str, expected: Any, actual: Any) -> bool:
        ok = expected == actual
        checks.append(
            {"check": label, "expected": expected, "actual": actual, "passed": ok}
        )
        return ok

    _check("is_valid", False, v2.get("is_valid"))
    _check("source", "hierarchical", v2.get("source"))
    # ≥10 formula lines × 1 NEEDS_QUOTE_INPUT each (Sprint #21.2).
    checks.append(
        {
            "check": "needs_quote_input_count_>=_10",
            "expected": ">= 10",
            "actual": len(needs),
            "passed": len(needs) >= 10,
        }
    )
    return {"checks": checks, "all_passed": all(c["passed"] for c in checks)}


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
def run_e2e() -> Dict[str, Any]:
    db = IsolatedDBFixture(prefix="mgx_sprint21_3_e2e_")
    db.setup()
    try:
        db.run(_seed_all())
        material_rates, workcenter_rates = db.run(_load_rate_registries(db))
        template = db.run(_load_template(db))

        case_b_direct = run_case_b_direct(template, material_rates, workcenter_rates)
        case_a_direct = run_case_a_direct(template, material_rates, workcenter_rates)
        case_b_orch = run_case_b_orchestrator(
            template, material_rates, workcenter_rates
        )
        http_probe = probe_http_price(template)

        case_b_verdict = verdict_case_b(case_b_direct)
        case_a_verdict = verdict_case_a(case_a_direct)

        case_b_payload = {
            "scenario": "case_b_valid",
            "request": {
                "template_code": TEMPLATE_CODE,
                "user_config": USER_CONFIG,
                "quote_input": CASE_B_QUOTE_INPUT,
                "material_rates": material_rates,
                "workcenter_rates": workcenter_rates,
            },
            "cost_engine_v2_response": case_b_direct,
            "orchestrator_snapshot": case_b_orch,
            "http_probe": http_probe,
            "verdict": case_b_verdict,
        }
        case_a_payload = {
            "scenario": "case_a_invalid",
            "request": {
                "template_code": TEMPLATE_CODE,
                "user_config": USER_CONFIG,
                "quote_input": {},
                "material_rates": material_rates,
                "workcenter_rates": workcenter_rates,
            },
            "cost_engine_v2_response": case_a_direct,
            "verdict": case_a_verdict,
        }

        proof_dir = _BACKEND_ROOT.parent.parent / "docs" / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)
        (proof_dir / "sprint21_3_case_b_valid.json").write_text(
            json.dumps(case_b_payload, indent=2, ensure_ascii=False)
        )
        (proof_dir / "sprint21_3_case_a_invalid.json").write_text(
            json.dumps(case_a_payload, indent=2, ensure_ascii=False)
        )

        return {
            "case_b": case_b_payload,
            "case_a": case_a_payload,
            "proof_dir": str(proof_dir),
        }
    finally:
        db.teardown()


if __name__ == "__main__":
    result = run_e2e()
    print("=" * 72)
    print("SPRINT #21.3 — E2E TPL-ACP-LIGHT-ROUTED")
    print("=" * 72)
    print()
    print("Proof files:")
    for name in ("sprint21_3_case_b_valid.json", "sprint21_3_case_a_invalid.json"):
        print(f"  - {os.path.join(result['proof_dir'], name)}")
    print()
    print("Case B verdict:")
    print(json.dumps(result["case_b"]["verdict"], indent=2))
    print()
    print("Case A verdict:")
    print(json.dumps(result["case_a"]["verdict"], indent=2))
    print()
    print("HTTP probe (documentation only):")
    http = result["case_b"]["http_probe"]
    print(
        json.dumps(
            {
                "probe": http.get("probe"),
                "status_code": http.get("status_code"),
                "body": http.get("body"),
                "note": http.get("note"),
            },
            indent=2,
        )
    )
    print()
    b_ok = result["case_b"]["verdict"]["all_passed"]
    a_ok = result["case_a"]["verdict"]["all_passed"]
    print(
        "FINAL VERDICT: "
        + ("VALID" if (b_ok and a_ok) else "INVALID")
    )