"""Agent B — F7D read-only CPP preview scenario probe.

Calls the existing read-only POST /api/v1/product-system/commercial-price-preview/{template}
endpoint (no persist, no /price, no CostEngine) with synthetic-but-held-constant geometry and
varying finish_setup values, to observe whether commercial_total / line subtotals change when
the operator-selectable finish changes.

NO DB writes. NO workspace mutation. Uses backend dev-bypass auth token (dev stack only).
"""
from __future__ import annotations

import json
import copy
from pathlib import Path

import requests

BASE = "http://localhost:8000/api/v1/product-system/commercial-price-preview"
HEADERS = {"Authorization": "Bearer __DEV_BYPASS_TOKEN__", "Content-Type": "application/json"}
OUT_DIR = Path(__file__).parent / "captures"
OUT_DIR.mkdir(exist_ok=True)

LETTERS_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
ACM_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"

# Held-constant synthetic geometry (NOT from a live analyzer run; explicitly synthetic and
# labeled as such in evidence — only used to hold quantity constant while varying finish).
BASE_GEOMETRY = {
    "letter_count": 9,
    "letter_face_area_m2": 2.5,
    "letter_perimeter_m": 8.0,
    "width_mm": 2000,
    "height_mm": 500,
    "depth_mm": 100,
}

BASE_PAYLOAD = {
    "quote_geometry": dict(BASE_GEOMETRY),
    "client": {"width_mm": 2000, "height_mm": 500},
    "vector_file": "test-bond-litere.svg",
    "finish_setup": {
        "return_depth_mm": 100,
        "letter_group_finishes": [
            {
                "group_key": "grp-A",
                "face_finish_type": "oracal_651",
                "face_oracal_code": "021",
                "return_finish_type": "white_aluminum",
                "confirmed": True,
            }
        ],
    },
}


def call(template: str, quote_input: dict) -> dict:
    resp = requests.post(
        f"{BASE}/{template}",
        headers=HEADERS,
        data=json.dumps({"template_code": template, "quote_input": quote_input, "currency": "RON"}),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def merge_finish(overrides: dict) -> dict:
    payload = copy.deepcopy(BASE_PAYLOAD)
    payload["finish_setup"].update(overrides)
    return payload


def summarize(name: str, resp: dict) -> dict:
    finish_line = next(
        (l for l in resp.get("commercial_price_lines", []) if l["code"] == "finisaje_colantare_vopsire"),
        None,
    )
    return {
        "scenario": name,
        "status": resp.get("status"),
        "commercial_total": resp.get("commercial_total"),
        "finish_line_unit_price": finish_line.get("commercial_unit_price") if finish_line else None,
        "finish_line_subtotal": finish_line.get("subtotal") if finish_line else None,
        "finish_line_warnings": finish_line.get("warnings") if finish_line else None,
        "blockers": [b["code"] for b in resp.get("commercial_blockers", [])],
        "active_modules": resp.get("input_summary", {}).get("active_modules"),
    }


# ---------------------------------------------------------------------------
# SCENARIO SET A — Letters face finish type (Oracal 651 / 641 / 8500 / print / none)
# ---------------------------------------------------------------------------
SCENARIOS_FACE = {
    "A1_face_oracal_651_code021": {"face_finish_type": "oracal_651", "face_oracal_code": "021"},
    "A2_face_oracal_651_code032_diffcolor": {"face_finish_type": "oracal_651", "face_oracal_code": "032"},
    "A3_face_oracal_641_code021": {"face_finish_type": "oracal_641", "face_oracal_code": "021"},
    "A4_face_oracal_8500": {"face_finish_type": "oracal_8500", "face_oracal_code": "021"},
    "A5_face_print_laminate": {"face_finish_type": "print_laminate"},
    "A6_face_none": {"face_finish_type": "none"},
}

# ---------------------------------------------------------------------------
# SCENARIO SET B — Letters return/cant finish (stock colors, mirror, RAL paint, oracal wrap)
# ---------------------------------------------------------------------------
SCENARIOS_RETURN = {
    "B1_return_white_aluminum_stock": {"return_finish_type": "white_aluminum"},
    "B2_return_black_aluminum_stock": {"return_finish_type": "black_aluminum"},
    "B3_return_gold_aluminum_stock": {"return_finish_type": "gold_aluminum"},
    "B4_return_mirror_silver": {"return_finish_type": "mirror_silver"},
    "B5_return_ral_paint_9016": {"return_finish_type": "ral_paint", "return_oracal_code": "9016"},
    "B6_return_ral_paint_3020_red": {"return_finish_type": "ral_paint", "return_oracal_code": "3020"},
    "B7_return_oracal_wrapped": {"return_finish_type": "oracal_wrapped", "return_oracal_code": "021"},
}

# ---------------------------------------------------------------------------
# SCENARIO SET C — letter_group_finishes confirmed vs unconfirmed vs empty vs absent
# ---------------------------------------------------------------------------
SCENARIOS_CONFIRM = {
    "C1_groups_confirmed_true": {
        "letter_group_finishes": [
            {"group_key": "grp-A", "face_finish_type": "oracal_651", "confirmed": True}
        ]
    },
    "C2_groups_confirmed_false": {
        "letter_group_finishes": [
            {"group_key": "grp-A", "face_finish_type": "oracal_651", "confirmed": False}
        ]
    },
    "C3_groups_empty_list": {"letter_group_finishes": []},
    "C4_groups_absent_none": {"letter_group_finishes": None},
}

# ---------------------------------------------------------------------------
# SCENARIO SET D — mounting_template material (control/contrast — SHOULD differ; sanity check)
# ---------------------------------------------------------------------------
SCENARIOS_MOUNTING = {
    "D1_sablon_paper": {
        "mounting_template_enabled": True,
        "mounting_template_area_m2": 1.0,
        "mounting_template_material_type": "paper",
        "mounting_solution": "installation_template",
    },
    "D2_sablon_forex": {
        "mounting_template_enabled": True,
        "mounting_template_area_m2": 1.0,
        "mounting_template_material_type": "forex",
        "mounting_solution": "installation_template",
    },
}


def run_group(group_name: str, scenarios: dict, template: str = LETTERS_TEMPLATE) -> list[dict]:
    results = []
    for name, overrides in scenarios.items():
        payload = merge_finish(overrides)
        resp = call(template, payload)
        (OUT_DIR / f"{group_name}__{name}.json").write_text(
            json.dumps(resp, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        results.append(summarize(name, resp))
    return results


# ---------------------------------------------------------------------------
# SCENARIO SET E — ACM boxed shell finish (stock_plate / oracal_651 / print_laminate)
# ---------------------------------------------------------------------------
ACM_BASE_PAYLOAD = {
    "template_code": ACM_TEMPLATE,
    "panel_width_mm": 1000,
    "panel_height_mm": 600,
    "acm_thickness_mm": 4,
    "return_depth_mm": 60,
    "fold_sides": "all",
}

SCENARIOS_ACM_SHELL = {
    "E1_shell_stock_plate": {"shell_finish": {"schema": "acm_shell_finish_v1", "face": {"kind": "stock_plate"}, "volume": {"kind": "stock_plate"}}},
    "E2_shell_oracal_651": {"shell_finish": {"schema": "acm_shell_finish_v1", "face": {"kind": "oracal_651", "color_code": "021"}, "volume": {"kind": "stock_plate"}}},
    "E3_shell_oracal_651_diffcolor": {"shell_finish": {"schema": "acm_shell_finish_v1", "face": {"kind": "oracal_651", "color_code": "9016"}, "volume": {"kind": "stock_plate"}}},
    "E4_shell_print_laminate": {"shell_finish": {"schema": "acm_shell_finish_v1", "face": {"kind": "print_laminate"}, "volume": {"kind": "stock_plate"}}},
}


def run_acm_group() -> list[dict]:
    results = []
    for name, overrides in SCENARIOS_ACM_SHELL.items():
        payload = copy.deepcopy(ACM_BASE_PAYLOAD)
        payload["finish_setup"] = {"acm_panel_instance": {"shell_finish": overrides["shell_finish"]}}
        resp = call(ACM_TEMPLATE, payload)
        (OUT_DIR / f"E_acm_shell__{name}.json").write_text(
            json.dumps(resp, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        results.append(summarize(name, resp))
    return results


def main() -> None:
    all_results = {}
    all_results["A_face_finish"] = run_group("A_face_finish", SCENARIOS_FACE)
    all_results["B_return_finish"] = run_group("B_return_finish", SCENARIOS_RETURN)
    all_results["C_confirm_state"] = run_group("C_confirm_state", SCENARIOS_CONFIRM)
    all_results["D_mounting_material_control"] = run_group("D_mounting_material_control", SCENARIOS_MOUNTING)
    all_results["E_acm_shell_finish"] = run_acm_group()

    summary_path = Path(__file__).parent / "agent-b-scenario-summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(all_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
