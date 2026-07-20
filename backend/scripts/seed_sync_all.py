"""Sprint #23 — Seed idempotency orchestrator.

Runs the canonical seeds in dependency order, idempotently, so any
environment (fresh, partially-seeded, or stale) converges to the
canonical registry state defined by the seed modules themselves.

Order (registries first, then the template that references them,
then purely configurational singletons):

1. `seeds/seed_product_families.py`           — canonical families
2. `seeds/seed_workcenter_rates.py`           — canonical workcenters
3. `seeds/seed_inventory_materials_stubs.py`  — canonical material stubs
4. `scripts/seed_tpl_acp_light_routed.py`     — `TPL-ACP-LIGHT-ROUTED`
5. `seeds/seed_observation_config.py`         — Sprint #37 thresholds
6. `seeds/seed_build4_materials.py`           — BUILD 4 material stubs
7. `seeds/seed_build4_workcenters.py`         — BUILD 4 workcenter stubs
8. `seeds/seed_build4_templates.py`           — BUILD 4 6 real templates

This module NEVER rewrites pricing, CostEngine, QuoteOrchestrator,
formula handlers, or routers. It only delegates to the existing seed
functions, which are themselves idempotent on their unique keys.

Usage (Sprint #39 — both invocations now work identically):

    cd /workspace/app/backend
    python -m scripts.seed_sync_all
    # --- OR ---
    python scripts/seed_sync_all.py

The `sys.path` shim below makes the script runnable as a plain file
without losing the ability to be imported as a module (e.g. from
`tests/test_seed_integrity_guard.py` via
`from scripts.seed_sync_all import run_all_seeds`).

Exit codes:
    0   all seeds ran, DB is in canonical state
    1   any seed raised an exception (logged + re-raised)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from typing import Any, Dict, List, Tuple

# Sprint #39 — sys.path shim.
# When this file is executed as a script (`python scripts/seed_sync_all.py`),
# Python adds `scripts/` to `sys.path` instead of the backend root, which
# breaks `from core.database ...`, `import models`, `from seeds...`, and the
# sibling `from scripts.seed_tpl_acp_light_routed ...` import. Prepending the
# resolved backend root fixes standalone file execution while remaining a
# no-op when the module is imported from an environment where the backend
# root is already on `sys.path` (e.g. pytest, `python -m scripts...`).
# This is the same pattern already used by
# `scripts/seed_canonical_order_for_e2e.py` (Sprint #33).
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from core.database import db_manager  # noqa: E402
import models  # noqa: F401,E402 — register all models with Base.metadata

from seeds.seed_product_families import seed_product_families  # noqa: E402
from seeds.seed_workcenter_rates import seed_workcenter_rates  # noqa: E402
from seeds.seed_inventory_materials_stubs import (  # noqa: E402
    seed_inventory_material_stubs,
)
from seeds.seed_observation_config import seed_observation_config  # noqa: E402
from scripts.seed_tpl_acp_light_routed import (  # noqa: E402
    seed_tpl_acp_light_routed,
)
# BUILD 4 — advertising production seeds
from seeds.seed_build4_materials import seed_build4_materials  # noqa: E402
from seeds.seed_build4_workcenters import seed_build4_workcenters  # noqa: E402
from seeds.seed_build4_templates import seed_build4_templates  # noqa: E402
from seeds.seed_tpl_volumetric_letters_v2 import seed_tpl_volumetric_letters_v2  # noqa: E402
from seeds.seed_tpl_volumetric_letters_component_modules_v1 import (  # noqa: E402
    seed_tpl_volumetric_letters_component_modules_v1,
)
from seeds.seed_volumetric_workcenter_rates import (  # noqa: E402
    seed_volumetric_operations_and_rates,
)
from seeds.seed_acm_bond_materials import seed_acm_bond_materials  # noqa: E402
from seeds.seed_acm_owner_confirmed_prices import (  # noqa: E402
    seed_acm_owner_confirmed_prices,
)
from seeds.seed_acm_boxed_mounting_owner_rates import (  # noqa: E402
    seed_acm_boxed_mounting_owner_rates,
)
from seeds.seed_tpl_acm_boxed_mounting_support_v1 import (  # noqa: E402
    seed_tpl_acm_boxed_mounting_support_v1,
)
from scripts.seed_acm_template_pack import seed_acm_template_pack  # noqa: E402
from seeds.seed_cost_engine_template_currency import (  # noqa: E402
    seed_cost_engine_template_base_currency,
)
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    seed_volumetric_owner_confirmed_prices,
)
from seeds.seed_tpl_volumetric_face_back_prep_template import (  # noqa: E402
    seed_tpl_volumetric_face_back_prep_template,
)
from seeds.seed_operational_workforce_registry import (  # noqa: E402
    seed_operational_workforce_registry,
)
from seeds.seed_active_template_scope import seed_active_template_scope  # noqa: E402
from scripts.cleanup_retired_product_templates import (  # noqa: E402
    cleanup_retired_product_templates,
)


logger = logging.getLogger(__name__)


SEED_PIPELINE: List[Tuple[str, Any]] = [
    ("product_families", seed_product_families),
    ("workcenter_rates", seed_workcenter_rates),
    ("inventory_materials_stubs", seed_inventory_material_stubs),
    ("tpl_acp_light_routed", seed_tpl_acp_light_routed),
    ("observation_config", seed_observation_config),
    # BUILD 4 — advertising production (after registries)
    ("build4_materials", seed_build4_materials),
    ("build4_workcenters", seed_build4_workcenters),
    ("build4_templates", seed_build4_templates),
    ("tpl_volumetric_letters_v2", seed_tpl_volumetric_letters_v2),
    ("tpl_volumetric_face_back_prep", seed_tpl_volumetric_face_back_prep_template),
    ("volumetric_workcenter_rates", seed_volumetric_operations_and_rates),
    ("acm_bond_materials", seed_acm_bond_materials),
    ("acm_owner_confirmed_prices", seed_acm_owner_confirmed_prices),
    ("acm_boxed_mounting_owner_rates", seed_acm_boxed_mounting_owner_rates),
    ("acm_template_pack", seed_acm_template_pack),
    ("tpl_acm_boxed_mounting_support_v1", seed_tpl_acm_boxed_mounting_support_v1),
    # After VL root + ACM optional link exist — complete FACE/BACK/LED/FINISH contracts.
    ("tpl_volumetric_letters_component_modules_v1", seed_tpl_volumetric_letters_component_modules_v1),
    ("volumetric_owner_confirmed_prices", seed_volumetric_owner_confirmed_prices),
    ("cost_engine_template_base_currency", seed_cost_engine_template_base_currency),
    ("active_template_scope", seed_active_template_scope),
    ("operational_workforce_registry", seed_operational_workforce_registry),
    ("cleanup_retired_product_templates", cleanup_retired_product_templates),
]


async def run_all_seeds() -> Dict[str, Dict[str, Any]]:
    """Run the canonical seeds in order. Returns per-seed stats dict."""
    await db_manager.init_db()

    results: Dict[str, Dict[str, Any]] = {}
    for name, seed_fn in SEED_PIPELINE:
        t0 = time.perf_counter()
        print(f"[seed_sync_all] >>> running seed: {name}", flush=True)
        stats = await seed_fn()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        results[name] = dict(stats)
        results[name]["elapsed_ms"] = round(elapsed_ms, 2)
        print(
            f"[seed_sync_all] <<< {name}: {stats} "
            f"(elapsed={elapsed_ms:.1f} ms)",
            flush=True,
        )

    return results


def _format_summary(results: Dict[str, Dict[str, Any]]) -> str:
    lines = ["", "=" * 60, "seed_sync_all SUMMARY", "=" * 60]
    for name, stats in results.items():
        lines.append(f"  {name}: {stats}")
    lines.append("=" * 60)
    return "\n".join(lines)


async def _main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        results = await run_all_seeds()
    except Exception as exc:  # noqa: BLE001 — top-level orchestrator
        logger.exception("seed_sync_all FAILED: %s", exc)
        print(f"[seed_sync_all] FAILED: {exc}", flush=True)
        return 1

    print(_format_summary(results), flush=True)
    print("[seed_sync_all] OK", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))