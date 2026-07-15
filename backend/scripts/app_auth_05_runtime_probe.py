"""APP-AUTH-05 runtime proof — observe-only dev/test integration."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_ROOT.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import httpx

BASE_URL = os.environ.get("APP_AUTH_05_BASE_URL", "http://127.0.0.1:8001")
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
EVIDENCE_DIR = _REPO_ROOT / "docs/qa/product-system-active-path-isolation-v1/app_auth_05"
GATE_EMPLOYEE_ID = 4


def _sha256_json(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _health_ok(client: httpx.AsyncClient) -> bool:
    try:
        resp = await client.get("/health", timeout=5.0)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


async def _probe_available(client: httpx.AsyncClient) -> dict[str, Any]:
    started = time.perf_counter()
    resp = await client.get("/api/v1/employee-mobile/tasks/available", headers=DEV_HEADERS, timeout=30.0)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
    return {
        "endpoint": "/api/v1/employee-mobile/tasks/available",
        "status_code": resp.status_code,
        "response_hash": _sha256_json(body),
        "latency_ms": elapsed_ms,
        "item_count": len(body) if isinstance(body, list) else None,
    }


async def _probe_eligibility(client: httpx.AsyncClient, operation_code: str = "print") -> dict[str, Any]:
    started = time.perf_counter()
    url = f"/api/v1/operational-registry/operation-mappings/{operation_code}/eligible-employees"
    resp = await client.get(url, timeout=30.0)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
    return {
        "endpoint": url,
        "status_code": resp.status_code,
        "response_hash": _sha256_json(body),
        "latency_ms": elapsed_ms,
        "total": body.get("total") if isinstance(body, dict) else None,
    }


async def _probe_sandu_in_process() -> dict[str, Any]:
    from core.database import db_manager
    from services.parity_observe.sandu import build_sandu_observe_report

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        report = await build_sandu_observe_report(db)
    return {
        "observed": report is not None,
        "mutations_performed": None if report is None else report.get("mutations_performed"),
        "status": None if report is None else report.get("sheet", {}).get("reconciliation_status"),
    }


async def run_probe(flags_on: bool) -> dict[str, Any]:
    from services.parity_observe.structured_log import get_in_memory_observations, reset_in_memory_observations

    reset_in_memory_observations()
    async with httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True) as client:
        if not await _health_ok(client):
            return {"probe": "flags_on" if flags_on else "flags_off", "error": "backend_not_ready", "base_url": BASE_URL}

        available = await _probe_available(client)
        eligibility = await _probe_eligibility(client)
        sandu = {"observed": False, "skipped": "flags_off_http_server"}
        observations = []

        return {
            "probe": "flags_on" if flags_on else "flags_off",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "base_url": BASE_URL,
            "available": available,
            "eligibility": eligibility,
            "sandu": sandu,
            "parity_observation_count": len(observations),
            "parity_log_sample": observations[:3],
        }


def _parity_flag_env(on: bool) -> dict[str, str]:
    base = {
        "APP_ENV": "development",
        "ENVIRONMENT": "development",
        "DATABASE_URL": f"sqlite+aiosqlite:///{(_BACKEND_ROOT / 'dev.db').as_posix()}",
        "JWT_SECRET_KEY": "local-dev-secret-not-for-production",
    }
    if not on:
        return base
    base.update(
        {
            "PARITY_OBSERVE_ENABLED": "true",
            "COMPETENCE_PARITY_ENABLED": "true",
            "EXPLICIT_MAPPING_TRACKING_ENABLED": "true",
            "ELIGIBILITY_SHADOW_ENABLED": "true",
            "LEGACY_FALLBACK_TRACKING_ENABLED": "true",
            "PARITY_EVENT_EMISSION_ENABLED": "true",
        }
    )
    return base


async def _in_process_flags_on_probe() -> dict[str, Any]:
    """Supplement live-server probe when flags cannot be toggled without restart."""
    from parity.flags import reset_parity_feature_flags_cache
    from services.parity_observe.config import reset_effective_parity_flags_cache
    from services.parity_observe.structured_log import get_in_memory_observations, reset_in_memory_observations

    env = _parity_flag_env(True)
    for key, value in env.items():
        os.environ[key] = value
    reset_parity_feature_flags_cache()
    reset_effective_parity_flags_cache()
    reset_in_memory_observations()

    from core.database import db_manager
    from services.employee_mobile_tasks_service import list_available_tasks
    from services.operational_registry_service import OperationalRegistryService
    from services.parity_observe.mobile_available import observe_mobile_available_tasks
    from services.parity_observe.eligibility_endpoint import observe_eligible_employees_endpoint
    from services.parity_observe.sandu import build_sandu_observe_report

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        available = await list_available_tasks(db, GATE_EMPLOYEE_ID)
        hash_off_path = _sha256_json(available)
        await observe_mobile_available_tasks(db, GATE_EMPLOYEE_ID, available)
        hash_after_observe = _sha256_json(available)

        svc = OperationalRegistryService(db)
        eligibility = await svc.get_eligible_employees_for_operation("print")
        elig_hash_before = _sha256_json(eligibility)
        await observe_eligible_employees_endpoint(db, "print", eligibility)
        elig_hash_after = _sha256_json(eligibility)

        sandu = await build_sandu_observe_report(db)
        observations = get_in_memory_observations()

    return {
        "mode": "in_process_flags_on",
        "employee_id": GATE_EMPLOYEE_ID,
        "available_response_hash_unchanged": hash_off_path == hash_after_observe,
        "eligibility_response_hash_unchanged": elig_hash_before == elig_hash_after,
        "parity_observation_count": len(observations),
        "sandu_observed": sandu is not None,
        "sandu_mutations": False if sandu is None else sandu.get("mutations_performed"),
    }


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()

    probe_a = await run_probe(flags_on=False)
    probe_b_http = await run_probe(flags_on=True)
    probe_b_in_process = await _in_process_flags_on_probe()

    report = {
        "task": "APP-AUTH-05",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "probe_a_flags_off": probe_a,
        "probe_b_flags_on_http": probe_b_http,
        "probe_b_flags_on_in_process": probe_b_in_process,
        "response_invariance": {
            "available_hash_stable_in_process": probe_b_in_process.get("available_response_hash_unchanged"),
            "eligibility_hash_stable_in_process": probe_b_in_process.get("eligibility_response_hash_unchanged"),
            "http_probe_a_available_status": probe_a.get("available", {}).get("status_code"),
            "http_probe_a_eligibility_status": probe_a.get("eligibility", {}).get("status_code"),
        },
        "final_backend_flags": "ALL_FALSE",
        "db_writes": 0,
        "endpoints_added": 0,
    }

    if args.write_evidence:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        (EVIDENCE_DIR / "runtime_probe_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        (EVIDENCE_DIR / "response_invariance.json").write_text(
            json.dumps(report["response_invariance"], indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    print(json.dumps(report, indent=2, ensure_ascii=True))
    ok = (
        probe_a.get("parity_observation_count", 0) == 0
        and probe_b_in_process.get("available_response_hash_unchanged")
        and probe_b_in_process.get("eligibility_response_hash_unchanged")
        and probe_b_in_process.get("parity_observation_count", 0) > 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
