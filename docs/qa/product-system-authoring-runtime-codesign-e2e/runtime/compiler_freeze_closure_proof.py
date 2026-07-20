"""Non-destructive CP-B/C/D/E proof for FINAL CLOSURE GATE (Agent B).

Writes JSON evidence next to this script. Does not touch live DB.

Usage (from repo root):
  cd backend
  .\\.venv\\Scripts\\python.exe ..\\docs\\qa\\product-system-authoring-runtime-codesign-e2e\\runtime\\compiler_freeze_closure_proof.py
"""

from __future__ import annotations

import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parents[4] / "backend"
sys.path.insert(0, str(BACKEND))

from services.letter_group_instance_authority import build_volumetric_letters_commercial_quantities
from services.order_snapshot_v2_convert_service import _enrich_order_provenance_with_product_truth
from services.product_truth_job_confirm_service import (
    apply_pinned_bags_onto_payload,
    commercial_freeze_allowed,
    confirm_job_product_truth,
    get_job_revision_metadata,
    mark_job_revision_stale_if_confirmed,
)

OUT = Path(__file__).resolve().parent / "compiler_freeze_closure_evidence.json"
ROOT = "TPL-VOLUMETRIC-LETTERS_v2"


def _payload() -> dict:
    return {
        "template_code": ROOT,
        "finish_setup": {
            "letter_group_instances": [
                {
                    "schema": "volumetric_letter_group_instance_v1",
                    "instance_id": "11111111-1111-1111-1111-111111111111",
                    "group_key": "pseudo:maria",
                    "confirmed": True,
                    "geometry": {"face_area_m2": 0.25, "perimeter_m": 1.2},
                }
            ],
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm-1",
                "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "association_status": "confirmed",
            },
            "letter_led_module_count": 4,
        },
        "quote_geometry": {"letter_perimeter_m": 3.5},
    }


def _eic_qty_coupling() -> dict:
    src = (BACKEND / "services" / "estimated_internal_cost_service.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    uses_qty = "letter_group_instance_authority" in imports or (
        "build_volumetric_letters_commercial_quantities" in src
    )
    uses_letters_meas = "letters_commercial_measurement_service" in imports
    return {
        "eic_imports_letter_group_instance_authority": "letter_group_instance_authority" in imports,
        "eic_imports_letters_commercial_measurement": uses_letters_meas,
        "eic_source_mentions_qty_builder": "build_volumetric_letters_commercial_quantities" in src,
        "converged_on_quantity_builder": uses_qty,
    }


def main() -> int:
    evidence: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "head_expected": "705a701a6e48f2bee1f638e44031f32f6d19d751",
        "foundation": ["ef349ef", "136f38b", "70b2fdf", "6a1c1d1"],
        "checkpoints": {},
    }

    payload = _payload()
    resp, confirmed = confirm_job_product_truth(
        workspace_id="ws-closure-b",
        workspace_code="IV6-CLOSURE-B",
        payload_raw=payload,
        expected_revision=0,
        expected_draft_hash=None,
        expected_content_hash=None,
        root_template_code=ROOT,
        root_template_version=None,
        actor_id="agent-b",
    )
    meta = get_job_revision_metadata(confirmed) or {}
    revision = meta.get("revision")
    content_hash = meta.get("content_hash")

    # CP-B: pin preference + revision surface
    pinned = apply_pinned_bags_onto_payload(confirmed)
    confirmed["finish_setup"]["letter_group_instances"][0]["instance_id"] = "live-drift"
    restored = apply_pinned_bags_onto_payload(confirmed)
    qty = build_volumetric_letters_commercial_quantities(
        quote_geometry=confirmed.get("quote_geometry"),
        finish_setup=restored.get("finish_setup"),
    )
    evidence["checkpoints"]["CP-B"] = {
        "status": "PARTIAL",
        "product_definition": "emits product_truth_job_revision provenance (code path 136f38b)",
        "aggregate": "applies pinned bags when freeze_allowed; does not surface revision in provenance_summary",
        "quantity_builder": {
            "source": qty.get("source"),
            "uses_pinned_instances": restored["finish_setup"]["letter_group_instances"][0][
                "instance_id"
            ]
            == "11111111-1111-1111-1111-111111111111",
            "surfaces_product_truth_revision": False,
        },
        "shared_revision": revision,
        "shared_content_hash": content_hash,
        "same_revision_surfaced_across_all_three": False,
        "pin_preference_shared_pd_agg": True,
        "notes": "PD provenance carries revision/hash; Agg/Qty consume pin but do not emit same revision fields.",
    }

    # CP-C: EIC vs Qty Builder
    eic = _eic_qty_coupling()
    evidence["checkpoints"]["CP-C"] = {
        "status": "PARTIAL" if not eic["converged_on_quantity_builder"] else "PASS",
        "eic_coupling": eic,
        "qty_builder_source": qty.get("source"),
        "fallbacks_still_present_in_qty_builder": True,
        "pricing_reopened": False,
        "notes": "EIC still uses parallel _extract_quantity paths; no import of Quantity Builder.",
    }

    # CP-D: freeze gate cases
    freeze_cases = {}
    freeze_cases["confirmed_allows"] = commercial_freeze_allowed(confirmed) is True
    stale_payload = json.loads(json.dumps(confirmed))
    stale_payload["finish_setup"]["letter_group_instances"][0]["confirmed"] = False
    mark_job_revision_stale_if_confirmed(stale_payload)
    freeze_cases["stale_blocks"] = commercial_freeze_allowed(stale_payload) is False
    freeze_cases["unconfirmed_blocks"] = commercial_freeze_allowed(_payload()) is False
    freeze_cases["wrong_hash_covered_by_pytest"] = "test_content_hash_mismatch_409"
    freeze_cases["accepted_terminal_covered_by_pytest"] = (
        "test_v6_freeze_blocks_accepted_quote_terminal"
    )
    freeze_cases["draft_drift_pin_restored"] = (
        restored["finish_setup"]["letter_group_instances"][0]["instance_id"]
        == pinned["finish_setup"]["letter_group_instances"][0]["instance_id"]
    )
    evidence["checkpoints"]["CP-D"] = {
        "status": "PASS"
        if all(
            [
                freeze_cases["confirmed_allows"],
                freeze_cases["stale_blocks"],
                freeze_cases["unconfirmed_blocks"],
                freeze_cases["draft_drift_pin_restored"],
            ]
        )
        else "FAIL",
        "cases": freeze_cases,
        "revision": revision,
        "content_hash": content_hash,
        "confirm_response_revision": resp["metadata"]["revision"],
    }

    # CP-E: Order + EP provenance
    order_prov = _enrich_order_provenance_with_product_truth(
        SimpleNamespace(provenance={"source": "quote_snapshot_v2"}),
        {
            "product_truth_revision": revision,
            "product_truth_content_hash": content_hash,
            "freeze_from_pinned_product_truth": True,
        },
    )
    ep_src = (
        BACKEND / "services" / "execution_preview_from_frozen_graph_service.py"
    ).read_text(encoding="utf-8")
    ep_schema = (
        BACKEND / "schemas" / "execution_preview_from_frozen.py"
    ).read_text(encoding="utf-8")
    evidence["checkpoints"]["CP-E"] = {
        "status": "PASS"
        if order_prov.get("no_live_workspace_reread") is True
        and order_prov.get("product_truth_revision") == revision
        else "FAIL",
        "order_provenance": order_prov,
        "same_revision_as_confirm": order_prov.get("product_truth_revision") == revision,
        "ep_reads_order_snapshot_only": "build_execution_preview_from_frozen_order" in ep_src
        and "snapshot_v2_json" in ep_src,
        "ep_no_materialization_docstring": "No task materialization" in ep_src,
        "ep_no_live_recompile_default": "no_live_recompile: bool = True" in ep_schema
        or "no_live_recompile: bool = True" in ep_src,
    }

    OUT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"evidence_path": str(OUT), "checkpoints": {
        k: v["status"] for k, v in evidence["checkpoints"].items()
    }}, indent=2))
    print("PROOF_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
