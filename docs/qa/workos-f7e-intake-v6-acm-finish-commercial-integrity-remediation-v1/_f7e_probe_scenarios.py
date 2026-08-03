"""F7E Lead runtime proof — read-only CPP preview scenario probe.

Calls the existing read-only POST /api/v1/product-system/commercial-price-preview/{template}
endpoint (no persist, no /price, no CostEngine) with synthetic-but-held-constant geometry and
varying finish_setup values, to check whether the F7E remediation rules produce non-zero-delta
pricing where required, and COMMERCIAL_RULE_MISSING (not silent flat 35) where no rule exists yet.

NO DB writes. NO workspace mutation. Uses backend dev-bypass auth token (dev stack only).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import requests

BASE = "http://localhost:8000/api/v1/product-system/commercial-price-preview"
HEADERS = {"Authorization": "Bearer __DEV_BYPASS_TOKEN__", "Content-Type": "application/json"}
OUT_DIR = Path(__file__).parent / "captures"
OUT_DIR.mkdir(exist_ok=True)

LETTERS_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"

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
    finish_lines = [
        {"code": l["code"], "subtotal": l.get("subtotal"), "unit_price": l.get("commercial_unit_price")}
        for l in resp.get("commercial_price_lines", [])
        if l["code"].startswith("finisaje")
    ]
    return {
        "scenario": name,
        "status": resp.get("status"),
        "commercial_total": resp.get("commercial_total"),
        "finish_lines": finish_lines,
        "unknown_owner_decisions": [d["code"] for d in resp.get("unknown_owner_decisions", [])],
        "blockers": [b.get("code", b) if isinstance(b, dict) else b for b in resp.get("commercial_blockers", [])],
        "active_modules": resp.get("input_summary", {}).get("active_modules"),
    }


SCENARIOS_FACE = {
    "F1_face_none": {"face_finish_type": "none"},
    "F2_face_oracal_651_code021": {"face_finish_type": "oracal_651", "face_oracal_code": "021"},
    "F3_face_oracal_641_code021": {"face_finish_type": "oracal_641", "face_oracal_code": "021"},
    "F4_face_oracal_8500": {"face_finish_type": "oracal_8500", "face_oracal_code": "021"},
    "F5_face_print_laminate": {"face_finish_type": "print_laminate"},
}

SCENARIOS_RETURN = {
    "R1_return_white_aluminum_stock": {"return_finish_type": "white_aluminum"},
    "R2_return_black_aluminum_stock": {"return_finish_type": "black_aluminum"},
    "R3_return_gold_aluminum_stock": {"return_finish_type": "gold_aluminum"},
    "R4_return_ral_paint_9016": {"return_finish_type": "ral_paint", "return_oracal_code": "9016"},
    "R5_return_oracal_wrapped": {"return_finish_type": "oracal_wrapped", "return_oracal_code": "021"},
}

SCENARIOS_MOUNTING = {
    "M1_sablon_paper": {
        "mounting_template_enabled": True,
        "mounting_template_area_m2": 1.0,
        "mounting_template_material_type": "paper",
        "mounting_solution": "installation_template",
    },
    "M2_sablon_forex": {
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


def main() -> None:
    all_results = {}
    all_results["F_face_finish"] = run_group("F_face_finish", SCENARIOS_FACE)
    all_results["R_return_finish"] = run_group("R_return_finish", SCENARIOS_RETURN)
    all_results["M_mounting_material_control"] = run_group("M_mounting_material_control", SCENARIOS_MOUNTING)

    summary_path = Path(__file__).parent / "f7e-scenario-summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(all_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
