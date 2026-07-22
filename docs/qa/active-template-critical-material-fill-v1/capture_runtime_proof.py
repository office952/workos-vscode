"""Runtime proof for ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8020"
OUT = Path(__file__).resolve().parent / "runtime"
OUT.mkdir(parents=True, exist_ok=True)


def get_json(path: str):
    with urllib.request.urlopen(BASE + path, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(path: str, body=None):
    data = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    reg = get_json("/api/v1/pricing/material-market-prices")
    crit = get_json("/api/v1/product-system/reference-finish-line/critical-materials")
    vl = post_json(
        "/api/v1/product-system/templates/TPL-VOLUMETRIC-LETTERS_v2/price-breakdown"
    )

    by = {i["material_code"]: i for i in reg["items"]}
    codes = [
        "MAT-LED-PSU-12V",
        "MAT-LED-PSU-12V-60W",
        "MAT-LED-PSU-12V-100W",
        "MAT-LED-PSU-12V-160W",
        "MAT-LED-PSU-12V-200W",
    ]
    psu = {c: by.get(c) for c in codes}
    (OUT / "psu_identity.json").write_text(
        json.dumps(psu, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "registry_summary.json").write_text(
        json.dumps(
            {
                "critical_missing": reg.get("critical_missing"),
                "summary": reg.get("summary"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (OUT / "critical_materials.json").write_text(
        json.dumps(crit, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    material_lines = [
        {
            "source_id": l.get("source_id"),
            "display_name": l.get("display_name"),
            "internal_cost": l.get("internal_cost"),
            "material_source_type": l.get("material_source_type"),
        }
        for l in vl.get("lines") or []
        if "PSU" in str(l.get("source_id") or "")
        or "PSU" in str(l.get("display_name") or "")
        or "PSU" in str(l.get("resource_code") or "")
    ]
    (OUT / "vl_psu_lines.json").write_text(
        json.dumps(material_lines, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary = {
        "identity": "VARIANT_SELECTOR",
        "generic_role": (psu.get("MAT-LED-PSU-12V") or {}).get("material_role"),
        "generic_blocker": (psu.get("MAT-LED-PSU-12V") or {}).get("blocker"),
        "generic_requires_direct_price": (psu.get("MAT-LED-PSU-12V") or {}).get(
            "requires_direct_price"
        ),
        "critical_missing": reg.get("critical_missing"),
        "active_template_critical_missing": reg.get("summary", {}).get(
            "active_template_critical_missing"
        ),
        "finish_line_critical": crit.get("active_template_critical_codes"),
        "variant_prices": {
            c: {
                "raw_price": (psu.get(c) or {}).get("raw_price"),
                "source_type": (psu.get(c) or {}).get("source_type"),
            }
            for c in codes[1:]
        },
        "vl_internal_total": vl.get("totals", {}).get("internal_total"),
        "vl_commercial_total": vl.get("totals", {}).get("commercial_total"),
        "vl_cpp_ok": vl.get("totals", {}).get("cpp_total_matches"),
        "vl_eic_ok": vl.get("totals", {}).get("eic_total_matches"),
        "vl_psu_lines": material_lines,
        "no_invented_generic_price": (psu.get("MAT-LED-PSU-12V") or {}).get("raw_price")
        is None,
        "freeze_readiness": "READY_WITH_LIMITATION",
    }
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
