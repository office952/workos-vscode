"""Live proof for PRODUCT_SYSTEM_REFERENCE_COMPLETE (:8020)."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8020"
OUT = Path(__file__).resolve().parent / "runtime"
OUT.mkdir(parents=True, exist_ok=True)


def get_json(path: str):
    with urllib.request.urlopen(BASE + path, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    body = get_json("/api/v1/product-system/reference-complete")
    (OUT / "reference_complete.json").write_text(
        json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    summary = {
        "overall_verdict": body.get("overall_verdict"),
        "freeze_readiness": body.get("freeze_readiness"),
        "live_proof": body.get("live_proof"),
        "matrix_axes": len(body.get("completion_matrix") or []),
        "documentation_docs": len(body.get("documentation_handoff") or []),
        "accepted_limitations": [x.get("id") for x in body.get("accepted_limitations") or []],
        "do_not_transfer_count": len(body.get("do_not_transfer") or []),
    }
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    assert body["overall_verdict"] == "PASS"
    assert body["freeze_readiness"] == "READY_FOR_DOCUMENTATION_HANDOFF"
    live = body["live_proof"]
    assert live["field_count"] == 26
    assert live["active_template_critical_codes"] == []
    assert live["psu_selector_ok"] is True
    assert live["vl_fixture_ok"] is True
    assert abs(float(live["vl_internal_total"]) - 923.2) < 0.05
    assert abs(float(live["vl_commercial_total"]) - 1061.0) < 0.05


if __name__ == "__main__":
    main()
