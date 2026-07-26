"""Dump finish-line contract evidence from live proof backend (:8020 by default)."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8020"
OUT = Path(__file__).resolve().parent / "runtime"
OUT.mkdir(parents=True, exist_ok=True)


def get_json(path: str) -> tuple[int, dict | list]:
    req = urllib.request.Request(BASE + path, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def post_json(path: str, body: dict | None = None) -> tuple[int, dict | str]:
    data = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        return e.code, e.read().decode("utf-8", errors="replace")[:800]


def main() -> None:
    import urllib.error  # noqa: F401 — used in post_json

    _, contract = get_json("/api/v1/product-system/reference-finish-line/contract")
    _, form_map = get_json(
        "/api/v1/product-system/reference-finish-line/form-field-ownership-map"
    )
    _, analyzer = get_json(
        "/api/v1/product-system/reference-finish-line/analyzer-io-contract"
    )
    _, critical = get_json(
        "/api/v1/product-system/reference-finish-line/critical-materials"
    )
    vl_status, vl_bd = post_json(
        "/api/v1/product-system/templates/TPL-VOLUMETRIC-LETTERS_v2/price-breakdown"
    )
    child_status, child_bd = post_json(
        "/api/v1/product-system/templates/TPL-VOLUM-ALUMINIU_v1/price-breakdown"
    )
    logo_status, logo_bd = post_json(
        "/api/v1/product-system/templates/TPL-VOLUMETRIC-LOGO_v1/price-breakdown"
    )

    assert isinstance(contract, dict)
    assert isinstance(form_map, dict)
    assert isinstance(analyzer, dict)
    assert isinstance(critical, dict)

    (OUT / "contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (OUT / "form_field_ownership_map.json").write_text(
        json.dumps(form_map, indent=2), encoding="utf-8"
    )
    (OUT / "analyzer_io_contract.json").write_text(
        json.dumps(analyzer, indent=2), encoding="utf-8"
    )
    (OUT / "critical_materials.json").write_text(
        json.dumps(critical, indent=2), encoding="utf-8"
    )

    summary: dict = {
        "mode": "live_http",
        "base": BASE,
        "overall_verdict": contract.get("overall_verdict"),
        "modularity_verdict": contract.get("modularity_verdict"),
        "form_system_verdict": contract.get("form_system_verdict"),
        "scalability_verdict": contract.get("scalability_verdict"),
        "authoring_decision": contract.get("authoring_decision"),
        "field_count": len(form_map.get("fields") or []),
        "reusable_fields": form_map.get("reusable_field_ids"),
        "hardcoded_ui_fields": form_map.get("hardcoded_ui_field_ids"),
        "active_template_critical": critical.get("active_template_critical_codes"),
        "manual_fill_required": critical.get("manual_fill_required_codes"),
        "analyzer_do_not": analyzer.get("do_not"),
        "vl_breakdown_status": vl_status,
        "child_breakdown_status": child_status,
        "logo_breakdown_status": logo_status,
        "production_cost_authority": contract.get("production_cost_boundary", {}).get(
            "completion_authority"
        ),
        "warnings": contract.get("warnings"),
    }
    if vl_status == 200 and isinstance(vl_bd, dict):
        summary["vl_internal_total"] = vl_bd.get("totals", {}).get("internal_total")
        summary["vl_commercial_total"] = vl_bd.get("totals", {}).get("commercial_total")
        summary["ownership_note_ro"] = vl_bd.get("ownership_note_ro")
        (OUT / "vl_breakdown.json").write_text(
            json.dumps(vl_bd, indent=2), encoding="utf-8"
        )
    if child_status == 200 and isinstance(child_bd, dict):
        (OUT / "volum_aluminiu_breakdown.json").write_text(
            json.dumps(child_bd, indent=2), encoding="utf-8"
        )
    if logo_status == 200 and isinstance(logo_bd, dict):
        summary["logo_publication"] = logo_bd.get("publication_status")
        summary["logo_blockers"] = logo_bd.get("blockers")
        (OUT / "logo_breakdown.json").write_text(
            json.dumps(logo_bd, indent=2), encoding="utf-8"
        )
    else:
        summary["logo_gap"] = logo_bd if isinstance(logo_bd, str) else str(logo_bd)[:500]

    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
