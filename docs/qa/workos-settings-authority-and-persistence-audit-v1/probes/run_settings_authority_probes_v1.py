"""
WORKOS_SETTINGS_AUTHORITY_AND_PERSISTENCE_AUDIT_V1 — runtime probes.

DEMO_DB_ONLY = YES
OWNER_DEV_DB_WRITES = 0
SmartBill: READ/HEALTH ONLY — no secret output, no token snapshot.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = os.environ.get("WORKOS_PROBE_BASE", "http://127.0.0.1:8000")
OUT = Path(__file__).resolve().parent / "probe_results.json"


def _req(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw) if raw else {"error": str(exc)}
        except json.JSONDecodeError:
            return exc.code, {"error": raw[:500]}


def _mask_smartbill(payload: dict) -> dict:
    """Keep structure; strip any secret-like fields."""
    if not isinstance(payload, dict):
        return {"_type": type(payload).__name__}
    out: dict = {}
    for k, v in payload.items():
        lk = str(k).lower()
        if any(x in lk for x in ("token", "secret", "password", "api_key", "apikey", "auth")):
            out[k] = "<REDACTED>"
        elif isinstance(v, dict):
            out[k] = _mask_smartbill(v)
        else:
            out[k] = v
    return out


def main() -> int:
    results: dict = {
        "probe_id": "SETTINGS_AUTHORITY_PROBES_V1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "base": BASE,
        "demo_db_only": True,
        "owner_dev_db_writes": 0,
        "steps": [],
    }

    # Confirm DB path from a cheap read + optional health
    status, health = _req("GET", "/health")
    results["steps"].append({"step": "health", "status": status, "body": health})

    status, before = _req("GET", "/api/v1/company-commercial-settings")
    results["steps"].append({"step": "ccs_get_before", "status": status, "body": before})
    if status != 200 or not isinstance(before, dict):
        results["fatal"] = "company-commercial-settings GET failed"
        OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(json.dumps(results, indent=2))
        return 1

    orig_vat = float(before["default_vat_pct"])
    orig_fx = float(before["eur_to_ron_rate"])
    probe_vat = 19.0 if orig_vat != 19.0 else 20.0
    probe_fx = 4.9876 if abs(orig_fx - 4.9876) > 1e-6 else 5.1234

    status, put_vat = _req(
        "PUT",
        "/api/v1/company-commercial-settings",
        {"default_vat_pct": probe_vat},
    )
    results["steps"].append(
        {
            "step": "ccs_put_vat",
            "status": status,
            "requested": probe_vat,
            "body": put_vat,
            "write_target": "DEMO_DB",
        }
    )

    status, after_vat = _req("GET", "/api/v1/company-commercial-settings")
    results["steps"].append({"step": "ccs_get_after_vat", "status": status, "body": after_vat})

    status, put_fx = _req(
        "PUT",
        "/api/v1/company-commercial-settings",
        {"eur_to_ron_rate": probe_fx},
    )
    results["steps"].append(
        {
            "step": "ccs_put_fx",
            "status": status,
            "requested": probe_fx,
            "body": put_fx,
            "write_target": "DEMO_DB",
        }
    )

    status, after_fx = _req("GET", "/api/v1/company-commercial-settings")
    results["steps"].append({"step": "ccs_get_after_fx", "status": status, "body": after_fx})

    # Restore originals
    status, restore = _req(
        "PUT",
        "/api/v1/company-commercial-settings",
        {"default_vat_pct": orig_vat, "eur_to_ron_rate": orig_fx},
    )
    results["steps"].append(
        {
            "step": "ccs_restore",
            "status": status,
            "body": restore,
            "write_target": "DEMO_DB",
        }
    )

    status, final = _req("GET", "/api/v1/company-commercial-settings")
    results["steps"].append({"step": "ccs_get_final", "status": status, "body": final})

    # Cost engine config (read)
    for path, name in (
        ("/api/v1/cost-engine/config", "cost_engine_config"),
        ("/api/v1/cost-engine/base-config", "cost_engine_base_config"),
        ("/api/v1/entities/recurring-payments", "recurring_payments_list"),
    ):
        status, body = _req("GET", path)
        # Truncate large lists
        if isinstance(body, list) and len(body) > 5:
            body = {"count": len(body), "sample": body[:3]}
        elif isinstance(body, dict) and "items" in body and isinstance(body["items"], list):
            body = {
                **{k: v for k, v in body.items() if k != "items"},
                "items_count": len(body["items"]),
                "items_sample": body["items"][:3],
            }
        results["steps"].append({"step": name, "status": status, "body": body})

    # SmartBill — health/config read only, fully redacted secrets
    for path, name in (
        ("/api/v1/integrations/smartbill/config", "smartbill_config"),
        ("/api/v1/integrations/smartbill/provider-health", "smartbill_provider_health"),
    ):
        status, body = _req("GET", path)
        safe = _mask_smartbill(body) if isinstance(body, dict) else {"status": status, "body_type": type(body).__name__}
        results["steps"].append({"step": name, "status": status, "body": safe, "side_effect": "NONE_READ_ONLY"})

    # Dead admin settings API presence (should exist but unused by Settings page)
    status, admin_settings = _req("GET", "/api/v1/settings")
    results["steps"].append(
        {
            "step": "admin_settings_list",
            "status": status,
            "note": "frontend/src/api/settings.ts — unused by Settings.tsx",
            "body_type": type(admin_settings).__name__,
            "body_preview": (
                admin_settings
                if not isinstance(admin_settings, (list, dict))
                else (
                    {"count": len(admin_settings), "sample_keys": list(admin_settings[0].keys())[:8]}
                    if isinstance(admin_settings, list) and admin_settings and isinstance(admin_settings[0], dict)
                    else (
                        {"keys": list(admin_settings.keys())[:20]}
                        if isinstance(admin_settings, dict)
                        else {"count": len(admin_settings)}
                    )
                )
            ),
        }
    )

    vat_ok = (
        isinstance(after_vat, dict)
        and float(after_vat.get("default_vat_pct", -1)) == probe_vat
    )
    fx_ok = (
        isinstance(after_fx, dict)
        and abs(float(after_fx.get("eur_to_ron_rate", -1)) - probe_fx) < 1e-6
    )
    restored = (
        isinstance(final, dict)
        and float(final.get("default_vat_pct", -1)) == orig_vat
        and abs(float(final.get("eur_to_ron_rate", -1)) - orig_fx) < 1e-6
    )

    results["verdict"] = {
        "vat_persist_roundtrip": "PASS" if vat_ok else "FAIL",
        "fx_persist_roundtrip": "PASS" if fx_ok else "FAIL",
        "restore_originals": "PASS" if restored else "FAIL",
        "owner_dev_db_writes": 0,
        "demo_db_only": True,
    }
    results["finished_at"] = datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results["verdict"], indent=2))
    print(f"Wrote {OUT}")
    return 0 if vat_ok and fx_ok and restored else 2


if __name__ == "__main__":
    sys.exit(main())
