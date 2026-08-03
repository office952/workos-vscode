"""F7F Lead runtime proof — Owner commercial law scenario matrix, read-only.

Calls the read-only POST /api/v1/product-system/commercial-price-preview/{template} endpoint
(no persist, no /price, no CostEngine, no workspace mutation) plus the read-only Intake V6
priced-quote dry run for the F7D/F7E workspace, and writes the observed rates, blockers and
per-product breakdown into evidence/.

NO DB writes. Dev-bypass auth token (dev stack only).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8000/api/v1"
PREVIEW = f"{BASE}/product-system/commercial-price-preview"
HEADERS = {"Authorization": "Bearer __DEV_BYPASS_TOKEN__", "Content-Type": "application/json"}
OUT_DIR = Path(__file__).parent / "evidence"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LETTERS_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
F7E_WORKSPACE_ID = "5a5ce742-f50f-47b0-985b-32cc6f2fb6a4"

BASE_PAYLOAD: dict = {
	"quote_geometry": {
		"letter_count": 9,
		"letter_face_area_m2": 2.5,
		"letter_perimeter_m": 8.0,
		"width_mm": 2000,
		"height_mm": 500,
		"depth_mm": 100,
	},
	"client": {"width_mm": 2000, "height_mm": 500},
	"vector_file": "test-bond-litere.svg",
	"finish_setup": {
		"return_depth_mm": 100,
		"face_finish_type": "none",
		"return_finish_type": "white_aluminum",
		"letter_group_finishes": [{"group_key": "grp-A", "confirmed": True}],
	},
}

# Owner F7F expected arithmetic on A = 2.5 m2 face area.
SCENARIOS: list[tuple[str, dict, dict]] = [
	("F1_face_none", {"face_finish_type": "none"}, {}),
	("F2_face_oracal_651", {"face_finish_type": "oracal_651", "face_oracal_code": "021"}, {}),
	("F2b_face_oracal_651_other_color", {"face_finish_type": "oracal_651", "face_oracal_code": "032"}, {}),
	("F3_face_oracal_641", {"face_finish_type": "oracal_641"}, {}),
	("F4_face_oracal_8500_no_width", {"face_finish_type": "oracal_8500"}, {}),
	(
		"F4a_face_oracal_8500_w1000",
		{"face_finish_type": "oracal_8500", "face_vinyl_roll_width_mm": 1000},
		{},
	),
	(
		"F4b_face_oracal_8500_w1260",
		{"face_finish_type": "oracal_8500", "face_vinyl_roll_width_mm": 1260},
		{},
	),
	("F5_face_print_laminate", {"face_finish_type": "print_laminate"}, {}),
	("F6_face_printed_vinyl_unpriced", {"face_finish_type": "printed_vinyl"}, {}),
	("R1_return_white_aluminum_stock", {"return_finish_type": "white_aluminum"}, {}),
	("R2_return_ral_paint", {"return_finish_type": "ral_paint"}, {}),
	("R3_return_oracal_wrapped", {"return_finish_type": "oracal_wrapped"}, {}),
]

WATCH_PREFIXES = ("finisaje_", "acm_")


def call_preview(quote_input: dict) -> dict:
	resp = requests.post(
		f"{PREVIEW}/{LETTERS_TEMPLATE}",
		headers=HEADERS,
		data=json.dumps(
			{"template_code": LETTERS_TEMPLATE, "quote_input": quote_input, "currency": "RON"}
		),
		timeout=60,
	)
	resp.raise_for_status()
	return resp.json()


def summarize(name: str, resp: dict) -> dict:
	preview = resp.get("preview") if isinstance(resp.get("preview"), dict) else resp
	lines = preview.get("commercial_price_lines") or []
	return {
		"scenario": name,
		"status": preview.get("status"),
		"subtotal_commercial": preview.get("subtotal_commercial"),
		"currency": preview.get("currency"),
		"blockers": [
			{"code": b.get("code"), "message": b.get("message")}
			for b in (preview.get("commercial_blockers") or [])
		],
		"watched_lines": [
			{
				"code": line.get("code"),
				"product": line.get("commercial_product_key"),
				"qty": line.get("quantity"),
				"unit_price": line.get("commercial_unit_price"),
				"currency": line.get("source_currency") or line.get("cpp_currency"),
				"subtotal": line.get("subtotal"),
				"owner_decision_required": line.get("owner_decision_required"),
			}
			for line in lines
			if str(line.get("code") or "").startswith(WATCH_PREFIXES)
		],
		"product_breakdown": preview.get("commercial_product_breakdown"),
	}


def main() -> None:
	results = []
	for name, finish_overrides, root_overrides in SCENARIOS:
		payload = copy.deepcopy(BASE_PAYLOAD)
		payload["finish_setup"].update(finish_overrides)
		payload.update(root_overrides)
		try:
			results.append(summarize(name, call_preview(payload)))
		except Exception as exc:  # noqa: BLE001 - probe must report, not crash the run
			results.append({"scenario": name, "error": repr(exc)})

	(OUT_DIR / "runtime-scenario-matrix.json").write_text(
		json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
	)

	dry_run: dict = {}
	try:
		resp = requests.get(
			f"{BASE}/intake-v6/workspaces/{F7E_WORKSPACE_ID}/priced-quote-dry-run",
			headers=HEADERS,
			timeout=120,
		)
		resp.raise_for_status()
		dry_run = resp.json()
	except Exception as exc:  # noqa: BLE001
		dry_run = {"error": repr(exc)}
	(OUT_DIR / "runtime-step3-dry-run.json").write_text(
		json.dumps(dry_run, indent=2, ensure_ascii=False), encoding="utf-8"
	)

	for row in results:
		print(json.dumps(row, ensure_ascii=False))
	print("STEP3 pricing_status =", dry_run.get("pricing_status"))
	print(
		"STEP3 breakdown =",
		json.dumps(dry_run.get("commercial_product_breakdown"), ensure_ascii=False),
	)
	print("STEP3 totals =", json.dumps(dry_run.get("commercial_totals"), ensure_ascii=False))


if __name__ == "__main__":
	main()
