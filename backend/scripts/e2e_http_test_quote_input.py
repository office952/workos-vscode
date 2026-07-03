"""
Sprint #21.4 — End-to-end HTTP proof generator for `quote_input` forwarding.

This script is the AUDIT-REPRODUCIBLE driver for Sprint #21.4. It:

  1. Boots a FastAPI app with the canonical quotes router.
  2. Seeds an isolated database with the `TPL-ACP-LIGHT-ROUTED` hierarchical
     template (and its operations / required materials / workcenter rates /
     inventory materials) using the same seed functions used in production.
  3. Fires TWO HTTP requests via `TestClient` against
     `POST /api/v1/entities/quotes/price`:
        - Case A (INVALID): no `quote_input` field in the request body.
          Expected behavior: 422 blocked, with `NEEDS_QUOTE_INPUT:*` reasons.
        - Case B (VALID):   full `quote_input` with `relief_pct=8.0`,
          `psu_watts=100`, `acp_sqm=1.42`.
          Expected behavior: 201 priced, snapshot returned, breakdown present.
  4. Writes the FULL HTTP response (status_code, headers, body) for each
     case to `docs/proof/sprint21_4_http_case_*_*.json`.
  5. Prints a deterministic verdict to stdout for easy re-audit.

Run from backend root:
    python scripts/e2e_http_test_quote_input.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Path bootstrap — allow running as a plain script from backend root.
# --------------------------------------------------------------------------- #
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

REPO_ROOT = BACKEND_ROOT.parent.parent
PROOF_DIR = REPO_ROOT / "docs" / "proof"
PROOF_DIR.mkdir(parents=True, exist_ok=True)

CASE_A_PATH = PROOF_DIR / "sprint21_4_http_case_a_invalid.json"
CASE_B_PATH = PROOF_DIR / "sprint21_4_http_case_b_valid.json"

# --------------------------------------------------------------------------- #
# Imports after sys.path setup.
# --------------------------------------------------------------------------- #
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.database import get_db  # noqa: E402

# Ensure ORM models are importable so Base.metadata knows them
from models.quotes import Quotes  # noqa: E402,F401
from models.orders import Orders  # noqa: E402,F401
from models.inventory_materials import Inventory_materials  # noqa: E402,F401
from models.workcenter_rates import Workcenter_rates  # noqa: E402,F401
from models.product_templates import Product_templates  # noqa: E402,F401
from models.product_families import Product_families  # noqa: E402,F401

from routers.quotes import router as quotes_router  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


TEMPLATE_CODE = "TPL-ACP-LIGHT-ROUTED"

# ACP Backlit Light Routed Panel — canonical dimensions for Sprint #21.4 proof.
DIMENSIONS = {"width_mm": 1000, "height_mm": 2000, "depth_mm": 80}
PRICING = {"margin_pct": 25, "vat_pct": 19, "discount_pct": 0}

# Canonical Case B payload — mirrors `tests/test_e2e_http_quote_input.py`
# and `tests/test_e2e_tpl_acp_light_routed.py` (same shape the hierarchical
# formula-based handlers expect).
QUOTE_INPUT_VALID = {
    "front_face_area_m2": 1.0,
    "personalization_path_length_mm": 3000.0,
    "personalization_bounding_area_m2": 0.6,
    "diffuser_cut_path_length_mm": 4000.0,
    "led_count": 55,
    "relief_cut_path_length_mm": 4000.0,
}


# --------------------------------------------------------------------------- #
# Helpers.
# --------------------------------------------------------------------------- #
def _dump_response(path: Path, resp: Any, case_label: str) -> dict:
    """Serialize a `TestClient` response as an audit-grade JSON dump."""
    try:
        body = resp.json()
    except Exception:
        body = {"__raw_text__": resp.text}

    payload = {
        "case": case_label,
        "endpoint": "POST /api/v1/entities/quotes/price",
        "status_code": resp.status_code,
        "headers": {k: v for k, v in resp.headers.items()},
        "body": body,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def _seed_template(fixture: IsolatedDBFixture) -> None:
    """Seed the `TPL-ACP-LIGHT-ROUTED` template + dependencies into the
    isolated DB. Reuses production seed scripts (they use the global
    ``db_manager`` which the fixture has already patched to this suite's
    DB), so the proof path matches the production path 1:1."""

    async def _run_seeds() -> None:
        from seeds.seed_workcenter_rates import seed_workcenter_rates
        from seeds.seed_inventory_materials_stubs import (
            seed_inventory_material_stubs,
        )
        from scripts.seed_tpl_acp_light_routed import (
            seed_tpl_acp_light_routed,
        )
        from scripts.fill_registry_values_sprint20_5 import (
            _fill_material_prices,
            _fill_workcenter_rates,
        )

        await seed_workcenter_rates()
        await seed_inventory_material_stubs()
        await _fill_workcenter_rates()
        await _fill_material_prices()
        await seed_tpl_acp_light_routed()

    fixture.run(_run_seeds())


def _load_template_from_db(fixture: IsolatedDBFixture) -> dict:
    """Load the seeded `TPL-ACP-LIGHT-ROUTED` template row as a dict
    suitable for the `/quotes/price` request body."""
    from sqlalchemy import select

    async def _fetch() -> dict:
        async with fixture.session_maker() as session:
            result = await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == TEMPLATE_CODE
                )
            )
            tpl = result.scalar_one()
            return {
                "id": tpl.id,
                "template_code": tpl.template_code,
                "family_id": tpl.family_id,
                "family_name": tpl.family_name,
                "components_json": tpl.components_json,
                "operations_json": tpl.operations_json,
                "required_materials_json": tpl.required_materials_json,
                "estimated_hours": tpl.estimated_hours,
                "base_labor_rate": tpl.base_labor_rate,
                "base_margin_pct": tpl.base_margin_pct,
                "active": tpl.active,
            }

    return fixture.run(_fetch())


# --------------------------------------------------------------------------- #
# Main.
# --------------------------------------------------------------------------- #
def main() -> int:
    print("=" * 72)
    print("Sprint #21.4 — HTTP proof generator for `quote_input` forwarding")
    print("=" * 72)

    fixture = IsolatedDBFixture(prefix="mgx_sprint21_4_")
    fixture.setup()

    try:
        print("[1/4] Seeding TPL-ACP-LIGHT-ROUTED + dependencies...")
        _seed_template(fixture)
        tpl = _load_template_from_db(fixture)
        print(f"       ✓ Template loaded: id={tpl['id']} code={tpl['template_code']}")

        print("[2/4] Booting FastAPI app with quotes router...")
        app = FastAPI()
        app.include_router(quotes_router)

        async def _override_get_db():
            async with fixture.session_maker() as session:
                yield session

        app.dependency_overrides[get_db] = _override_get_db
        client = TestClient(app)
        print("       ✓ TestClient ready.")

        # ------------------------------------------------------------------
        # Case A — INVALID: no quote_input. Expected 422 NEEDS_QUOTE_INPUT:*.
        # ------------------------------------------------------------------
        print("[3/4] Case A (INVALID): POST without quote_input...")
        case_a_body = {
            "product_template": tpl,
            "user_config": {"quantity": 2, "dimensions": DIMENSIONS},
            "pricing": PRICING,
            "client_name": "Sprint 21.4 Audit — Case A",
        }
        resp_a = client.post("/api/v1/entities/quotes/price", json=case_a_body)
        dump_a = _dump_response(CASE_A_PATH, resp_a, "A_INVALID_NO_QUOTE_INPUT")
        dump_a_request = {"request_body": case_a_body}
        # Append request to dump for full audit trail.
        full_a = {**dump_a_request, **dump_a}
        CASE_A_PATH.write_text(json.dumps(full_a, indent=2, ensure_ascii=False))
        print(f"       ✓ status={resp_a.status_code}, written to {CASE_A_PATH}")

        # ------------------------------------------------------------------
        # Case B — VALID: full quote_input. Expected 201 priced snapshot.
        # ------------------------------------------------------------------
        print("[4/4] Case B (VALID): POST with quote_input...")
        case_b_body = {
            "product_template": tpl,
            "user_config": {"quantity": 2, "dimensions": DIMENSIONS},
            "pricing": PRICING,
            "client_name": "Sprint 21.4 Audit — Case B",
            "quote_input": QUOTE_INPUT_VALID,
        }
        resp_b = client.post("/api/v1/entities/quotes/price", json=case_b_body)
        dump_b = _dump_response(CASE_B_PATH, resp_b, "B_VALID_WITH_QUOTE_INPUT")
        full_b = {"request_body": case_b_body, **dump_b}
        CASE_B_PATH.write_text(json.dumps(full_b, indent=2, ensure_ascii=False))
        print(f"       ✓ status={resp_b.status_code}, written to {CASE_B_PATH}")

        # ------------------------------------------------------------------
        # Verdict.
        # ------------------------------------------------------------------
        print()
        print("=" * 72)
        print("VERDICT")
        print("=" * 72)

        ok_a = resp_a.status_code == 422
        body_a_text = json.dumps(dump_a["body"]).lower()
        has_needs_qi = "needs_quote_input" in body_a_text
        print(
            f"  Case A: status={resp_a.status_code} "
            f"(expected 422) — {'OK' if ok_a else 'FAIL'}; "
            f"contains NEEDS_QUOTE_INPUT: {has_needs_qi}"
        )

        ok_b = resp_b.status_code == 201
        body_b = dump_b["body"] if isinstance(dump_b["body"], dict) else {}
        snapshot = body_b.get("snapshot", {})
        price = snapshot.get("price", {}) if isinstance(snapshot, dict) else {}
        gross = price.get("gross")
        print(
            f"  Case B: status={resp_b.status_code} "
            f"(expected 201) — {'OK' if ok_b else 'FAIL'}; "
            f"snapshot.price.gross={gross}"
        )

        overall = ok_a and has_needs_qi and ok_b and (gross is not None)
        print()
        print(
            "  OVERALL: "
            + ("HTTP_READY_FOR_PRODUCTION ✅" if overall else "FAILED ❌")
        )
        print()
        print(f"  Proof A: {CASE_A_PATH}")
        print(f"  Proof B: {CASE_B_PATH}")
        return 0 if overall else 1

    finally:
        fixture.teardown()


if __name__ == "__main__":
    sys.exit(main())