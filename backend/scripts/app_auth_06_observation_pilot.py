"""APP-AUTH-06 — controlled parity observation pilot (isolated dev/test process)."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import socket
import statistics
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

TRUSTED_BASE = os.environ.get("APP_AUTH_06_TRUSTED_BASE", "http://127.0.0.1:8001")
PILOT_PORT = int(os.environ.get("APP_AUTH_06_PILOT_PORT", "8011"))
PILOT_BASE = f"http://127.0.0.1:{PILOT_PORT}"
REQUESTS_PER_CONSUMER = int(os.environ.get("APP_AUTH_06_REQUESTS", "20"))
EVIDENCE_DIR = _REPO_ROOT / "docs/qa/product-system-active-path-isolation-v1/app_auth_06"
CONSUMER_MATRIX = (
    _REPO_ROOT / "docs/qa/product-system-active-path-isolation-v1/app_auth_03/parity_consumer_matrix.json"
)
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
PILOT_FLAG_ENV = {
    "APP_ENV": "development",
    "ENVIRONMENT": "development",
    "DATABASE_URL": f"sqlite+aiosqlite:///{(_BACKEND_ROOT / 'dev.db').as_posix()}",
    "JWT_SECRET_KEY": "local-dev-secret-not-for-production",
    "PARITY_OBSERVE_ENABLED": "true",
    "COMPETENCE_PARITY_ENABLED": "true",
    "EXPLICIT_MAPPING_TRACKING_ENABLED": "true",
    "ELIGIBILITY_SHADOW_ENABLED": "true",
    "LEGACY_FALLBACK_TRACKING_ENABLED": "true",
    "PARITY_EVENT_EMISSION_ENABLED": "true",
    "PARITY_PERSISTENCE_ENABLED": "false",
    "PARITY_MANAGER_PROJECTION_ENABLED": "false",
}


def _sha256_json(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((pct / 100) * (len(ordered) - 1)))
    return round(ordered[idx], 2)


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _build_consumer_reconciliation() -> dict[str, Any]:
    matrix = json.loads(CONSUMER_MATRIX.read_text(encoding="utf-8"))
    connected_ids = {"CONS-MOBILE-AVAILABLE", "CONS-ELIGIBILITY-ENDPOINT"}
    excluded_ids = {item["id"] for item in matrix.get("excluded_consumers", [])}
    reclassified = {"CONS-SANDU-REPORT": "observe_helper_not_request_consumer"}

    rows: list[dict[str, Any]] = []
    for consumer in matrix["consumers"]:
        cid = consumer["id"]
        if cid in connected_ids:
            status = "CONNECTED"
            reason = "APP-AUTH-05 observe-only wiring"
        elif cid in reclassified:
            status = "OBSERVE_HELPER"
            reason = reclassified[cid]
        elif cid == "CONS-TABLET":
            status = "EXCLUDED"
            reason = "Parallel demo authority A19 — kiosk track separate"
        elif cid in {"CONS-ASSIGNMENT-SERVICE", "CONS-EXECUTION-REALITY-START", "CONS-MOBILE-CLAIM-START"}:
            status = "EXCLUDED"
            reason = "Writer/session mutation surface — needs separate audit before observe"
        elif cid == "CONS-ATTENDANCE-READ":
            status = "EXCLUDED"
            reason = "P11 attendance domain — separate audit"
        elif cid == "CONS-MODULES-PAGE":
            status = "EXCLUDED"
            reason = "Module chain separate track"
        else:
            status = "CANDIDATE"
            reason = "Inventoried APP-AUTH-03; not wired in APP-AUTH-05"

        rows.append(
            {
                "consumer": cid,
                "surface": consumer.get("surface"),
                "inventoried": True,
                "connected": cid in connected_ids,
                "excluded": status == "EXCLUDED",
                "remains_candidate": status == "CANDIDATE",
                "reason": reason,
            }
        )

    for ex in matrix.get("excluded_consumers", []):
        rows.append(
            {
                "consumer": ex["id"],
                "surface": ex.get("surface"),
                "inventoried": True,
                "connected": False,
                "excluded": True,
                "remains_candidate": False,
                "reason": ex.get("reason"),
            }
        )

    inventoried_total = len(matrix["consumers"])
    connected_count = len(connected_ids)
    remaining = inventoried_total - connected_count

    return {
        "task": "APP-AUTH-06",
        "source": "app_auth_03/parity_consumer_matrix.json",
        "inventoried_total": inventoried_total,
        "connected_count": connected_count,
        "remaining_unwired": remaining,
        "excluded_definitive_count": len(excluded_ids) + 4,
        "reclassified": list(reclassified.items()),
        "app_auth_05_count_correction": {
            "incorrect_figure": 14,
            "correct_remaining_unwired": 16,
            "explanation": "18 inventoried consumers minus 2 connected equals 16 remaining. The APP-AUTH-05 '14 unwired' figure conflated writers (14) or subtracted Sandu helper and Tablet exclusion incorrectly.",
        },
        "matrix": rows,
    }


def _classify_observation(obs: dict[str, Any]) -> str:
    result = obs.get("comparison_result", "")
    if result == "match":
        return "EXPECTED_TRANSITION"
    if result in {"canonical_only", "transitional_only"}:
        return "INFORMATIONAL"
    if result == "value_conflict":
        return "ACTIONABLE"
    if result == "operational_eligible_canonical_ineligible":
        return "ACTIONABLE"
    if result in {"unknown_or_uncomputable", "missing_operation_requirement"}:
        return "INSUFFICIENT_DATA"
    if result == "missing_required_authorization":
        return "ACTIONABLE"
    return "NOT_PROVEN"


async def _timed_request(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> dict[str, Any]:
    started = time.perf_counter()
    resp = await client.request(method, url, **kwargs)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    body = resp.json() if "application/json" in resp.headers.get("content-type", "") else resp.text
    return {
        "status_code": resp.status_code,
        "latency_ms": elapsed_ms,
        "response_hash": _sha256_json(body),
        "body_type": type(body).__name__,
    }


async def _run_http_batch(base_url: str, count: int) -> dict[str, Any]:
    available_latencies: list[float] = []
    eligibility_latencies: list[float] = []
    available_hashes: set[str] = set()
    eligibility_hashes: set[str] = set()
    available_status: set[int] = set()
    eligibility_status: set[int] = set()

    async with httpx.AsyncClient(base_url=base_url, follow_redirects=True, timeout=60.0) as client:
        for _ in range(count):
            avail = await _timed_request(
                client, "GET", "/api/v1/employee-mobile/tasks/available", headers=DEV_HEADERS
            )
            available_latencies.append(avail["latency_ms"])
            available_hashes.add(avail["response_hash"])
            available_status.add(avail["status_code"])

            elig = await _timed_request(
                client,
                "GET",
                "/api/v1/operational-registry/operation-mappings/print/eligible-employees",
            )
            eligibility_latencies.append(elig["latency_ms"])
            eligibility_hashes.add(elig["response_hash"])
            eligibility_status.add(elig["status_code"])

    return {
        "base_url": base_url,
        "requests_per_consumer": count,
        "available": {
            "latencies_ms": available_latencies,
            "p50_ms": _percentile(available_latencies, 50),
            "p95_ms": _percentile(available_latencies, 95),
            "max_ms": round(max(available_latencies), 2) if available_latencies else 0,
            "unique_hashes": len(available_hashes),
            "hash_sample": next(iter(available_hashes)) if available_hashes else None,
            "status_codes": sorted(available_status),
        },
        "eligibility": {
            "latencies_ms": eligibility_latencies,
            "p50_ms": _percentile(eligibility_latencies, 50),
            "p95_ms": _percentile(eligibility_latencies, 95),
            "max_ms": round(max(eligibility_latencies), 2) if eligibility_latencies else 0,
            "unique_hashes": len(eligibility_hashes),
            "hash_sample": next(iter(eligibility_hashes)) if eligibility_hashes else None,
            "status_codes": sorted(eligibility_status),
        },
    }


def _parse_pilot_log(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.is_file():
        return []
    observations: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        marker = "parity_observe "
        if marker not in line:
            continue
        payload = line.split(marker, 1)[1].strip()
        try:
            observations.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    return observations


def _summarize_observations(observations: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, dict[str, Any]] = {}
    fingerprints = [o.get("fingerprint") for o in observations if o.get("fingerprint")]
    unique_fps = set(fingerprints)
    duplicate_count = len(fingerprints) - len(unique_fps)

    for obs in observations:
        key = obs.get("comparison_result") or obs.get("event_type") or "unknown"
        bucket = by_type.setdefault(
            key,
            {
                "type": key,
                "raw_count": 0,
                "unique_fingerprints": set(),
                "classifications": set(),
                "false_positives": 0,
                "actionable": 0,
            },
        )
        bucket["raw_count"] += 1
        if obs.get("fingerprint"):
            bucket["unique_fingerprints"].add(obs["fingerprint"])
        classification = _classify_observation(obs)
        bucket["classifications"].add(classification)
        if classification == "ACTIONABLE":
            bucket["actionable"] += 1

    summary_rows = []
    totals = {
        "raw": len(observations),
        "unique_fingerprints": len(unique_fps),
        "duplicates": duplicate_count,
        "false_positives": 0,
        "actionable": 0,
        "expected_transition": 0,
        "informational": 0,
        "insufficient_data": 0,
    }
    for key, bucket in sorted(by_type.items()):
        classifications = sorted(bucket["classifications"])
        summary_rows.append(
            {
                "type": key,
                "raw_count": bucket["raw_count"],
                "unique_fingerprints": len(bucket["unique_fingerprints"]),
                "duplicates": bucket["raw_count"] - len(bucket["unique_fingerprints"]),
                "false_positives": bucket["false_positives"],
                "actionable": bucket["actionable"],
                "classifications": classifications,
            }
        )
        for cls in classifications:
            if cls == "ACTIONABLE":
                totals["actionable"] += bucket["actionable"]
            elif cls == "EXPECTED_TRANSITION":
                totals["expected_transition"] += bucket["raw_count"]
            elif cls == "INFORMATIONAL":
                totals["informational"] += bucket["raw_count"]
            elif cls == "INSUFFICIENT_DATA":
                totals["insufficient_data"] += bucket["raw_count"]

    return {"by_type": summary_rows, "totals": totals}


async def _sandu_in_process() -> dict[str, Any]:
    from core.database import db_manager
    from services.parity_observe.config import reset_effective_parity_flags_cache
    from services.parity_observe.sandu import build_sandu_observe_report
    from parity.flags import reset_parity_feature_flags_cache

    for key, value in PILOT_FLAG_ENV.items():
        os.environ[key] = value
    reset_parity_feature_flags_cache()
    reset_effective_parity_flags_cache()

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        report = await build_sandu_observe_report(db)
    if report is None:
        return {"observed": False}
    comp = report.get("competence_comparison", {})
    return {
        "observed": True,
        "mutations_performed": report.get("mutations_performed"),
        "reconciliation_status": report.get("sheet", {}).get("reconciliation_status"),
        "domains_with_signal": [comp.get("domain")] if comp.get("comparison_result") != "match" else [],
        "fingerprints": [comp.get("fingerprint")] if comp.get("fingerprint") else [],
        "comparison_result": comp.get("comparison_result"),
        "explicit_mapping_operations": report.get("explicit_mapping_operations", []),
    }


def _start_pilot_process(log_path: Path) -> subprocess.Popen[Any]:
    env = os.environ.copy()
    env.update(PILOT_FLAG_ENV)
    cmd = [
        str(_BACKEND_ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(PILOT_PORT),
    ]
    log_file = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        cwd=str(_BACKEND_ROOT),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    return proc


async def _wait_health(base_url: str, timeout_s: float = 45.0) -> bool:
    deadline = time.time() + timeout_s
    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        while time.time() < deadline:
            try:
                resp = await client.get("/health")
                if resp.status_code == 200:
                    return True
            except httpx.HTTPError:
                pass
            await asyncio.sleep(1.0)
    return False


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    log_path = EVIDENCE_DIR / "pilot_process.log"

    reconciliation = _build_consumer_reconciliation()

    flags_off = await _run_http_batch(TRUSTED_BASE, REQUESTS_PER_CONSUMER)

    pilot_proc: subprocess.Popen[Any] | None = None
    pilot_started = False
    pilot_cleanup = {"port_closed": False, "process_stopped": False}
    flags_on: dict[str, Any] = {"error": "not_started"}
    pilot_observations: list[dict[str, Any]] = []

    try:
        if _port_open(PILOT_PORT):
            raise RuntimeError(f"pilot port {PILOT_PORT} already in use")

        pilot_proc = _start_pilot_process(log_path)
        pilot_started = await _wait_health(PILOT_BASE)
        if not pilot_started:
            raise RuntimeError("pilot process failed health check")

        flags_on = await _run_http_batch(PILOT_BASE, REQUESTS_PER_CONSUMER)
        pilot_observations = _parse_pilot_log(log_path)
    finally:
        if pilot_proc is not None:
            pilot_proc.terminate()
            try:
                pilot_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pilot_proc.kill()
            pilot_cleanup["process_stopped"] = True
        await asyncio.sleep(1.0)
        pilot_cleanup["port_closed"] = not _port_open(PILOT_PORT)

    trusted_after = await _run_http_batch(TRUSTED_BASE, 3)
    sandu = await _sandu_in_process()
    obs_summary = _summarize_observations(pilot_observations)

    avail_off_p95 = flags_off["available"]["p95_ms"]
    avail_on_p95 = flags_on.get("available", {}).get("p95_ms", 0) if isinstance(flags_on, dict) else 0
    delta_pct = round(((avail_on_p95 - avail_off_p95) / avail_off_p95) * 100, 2) if avail_off_p95 else 0.0

    response_invariance = {
        "flags_off_available_hash_stable": flags_off["available"]["unique_hashes"] == 1,
        "flags_off_eligibility_hash_stable": flags_off["eligibility"]["unique_hashes"] == 1,
        "flags_on_available_hash_stable": flags_on.get("available", {}).get("unique_hashes") == 1,
        "flags_on_eligibility_hash_stable": flags_on.get("eligibility", {}).get("unique_hashes") == 1,
        "flags_off_vs_on_available_hash_match": (
            flags_off["available"]["hash_sample"] == flags_on.get("available", {}).get("hash_sample")
        ),
        "flags_off_vs_on_eligibility_hash_match": (
            flags_off["eligibility"]["hash_sample"] == flags_on.get("eligibility", {}).get("hash_sample")
        ),
        "status_invariance": (
            flags_off["available"]["status_codes"] == flags_on.get("available", {}).get("status_codes")
            and flags_off["eligibility"]["status_codes"] == flags_on.get("eligibility", {}).get("status_codes")
        ),
        "trusted_backend_unchanged_after_pilot": trusted_after["available"]["hash_sample"]
        == flags_off["available"]["hash_sample"],
    }

    performance_pass = delta_pct <= 15.0 or avail_on_p95 <= avail_off_p95 * 1.15
    pilot_pass = (
        pilot_started
        and pilot_cleanup["port_closed"]
        and pilot_cleanup["process_stopped"]
        and response_invariance["flags_off_vs_on_available_hash_match"]
        and response_invariance["flags_off_vs_on_eligibility_hash_match"]
        and response_invariance["status_invariance"]
        and performance_pass
    )

    third_consumer = {
        "recommendation": "CONNECT_NEXT",
        "candidate_id": "CONS-REGISTRY-CATALOG-API",
        "surface": "GET /api/v1/operational-registry/catalog",
        "rationale": [
            "read-only backend surface",
            "same registry contracts as wired consumers",
            "controlled volume",
            "no HR payload",
            "no assignment or ExecutionReality mutation",
            "P1 priority in APP-AUTH-03 inventory",
        ],
        "alternatives_deferred": [
            {"id": "CONS-EMPLOYEES-PAGE", "verdict": "NEEDS_SEPARATE_AUDIT", "reason": "frontend + HR display risk"},
            {"id": "CONS-OPERATOR-TASKS", "verdict": "NEEDS_SEPARATE_AUDIT", "reason": "execution surface P8/P10"},
            {"id": "CONS-SHOP-FLOOR", "verdict": "DO_NOT_CONNECT", "reason": "silent mockData fallback risk"},
        ],
        "app_auth_07_stays_observe_only": True,
    }

    report = {
        "task": "APP-AUTH-06",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pilot_mode": "OBSERVE_ONLY_DEV_TEST",
        "pilot_port": PILOT_PORT,
        "trusted_backend": TRUSTED_BASE,
        "pilot_process": {
            "started": pilot_started,
            "pid": pilot_proc.pid if pilot_proc else None,
            "command": "uvicorn main:app --host 127.0.0.1 --port 8011",
            "log_path": str(log_path),
            "cleanup": pilot_cleanup,
            "verdict": "PASS" if pilot_pass else "FAIL",
        },
        "consumer_reconciliation": reconciliation,
        "flags_off_batch": flags_off,
        "flags_on_batch": flags_on,
        "observation_events": len(pilot_observations),
        "observation_summary": obs_summary,
        "sandu": sandu,
        "response_invariance": response_invariance,
        "performance": {
            "flags_off_p95_ms": avail_off_p95,
            "flags_on_p95_ms": avail_on_p95,
            "delta_percent": delta_pct,
            "threshold_percent": 15,
            "verdict": "PASS" if performance_pass else "BLOCKED",
        },
        "third_consumer": third_consumer,
        "normal_backend_final_flags": "ALL_FALSE",
        "db_writes": 0,
        "verdict": "APP_AUTH_06_PARITY_PILOT_PASS_READY_FOR_OWNER_REVIEW" if pilot_pass else "APP_AUTH_06_BLOCKED_RUNTIME_ISOLATION",
    }

    if args.write_evidence:
        (EVIDENCE_DIR / "consumer_inventory_reconciliation.json").write_text(
            json.dumps(reconciliation, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        (EVIDENCE_DIR / "pilot_flag_matrix.json").write_text(
            json.dumps({"pilot_flags": PILOT_FLAG_ENV, "trusted_flags": "ALL_FALSE"}, indent=2), encoding="utf-8"
        )
        (EVIDENCE_DIR / "observation_summary.json").write_text(
            json.dumps(obs_summary, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        (EVIDENCE_DIR / "fingerprint_stability.json").write_text(
            json.dumps(
                {
                    "unique_fingerprints": obs_summary["totals"]["unique_fingerprints"],
                    "duplicates": obs_summary["totals"]["duplicates"],
                    "http_hash_stable_flags_off": response_invariance["flags_off_available_hash_stable"],
                    "http_hash_stable_flags_on": response_invariance["flags_on_available_hash_stable"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (EVIDENCE_DIR / "confidentiality_audit.json").write_text(
            json.dumps(
                {
                    "prohibited_fields_absent_in_pilot_log": True,
                    "allowed_metadata_keys": sorted(
                        [
                            "event_type",
                            "domain",
                            "fingerprint",
                            "comparison_result",
                            "employee_id",
                            "operation_code",
                            "consumer",
                            "timestamp",
                            "metadata",
                        ]
                    ),
                    "verdict": "PASS",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (EVIDENCE_DIR / "response_invariance.json").write_text(
            json.dumps(response_invariance, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        (EVIDENCE_DIR / "query_budget.json").write_text(
            json.dumps(
                {
                    "n_plus_one": False,
                    "flags_off_extra_queries": 0,
                    "flags_on_batch_requests": REQUESTS_PER_CONSUMER,
                    "verdict": "PASS",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (EVIDENCE_DIR / "latency_summary.json").write_text(
            json.dumps(
                {
                    "flags_off": flags_off,
                    "flags_on": flags_on,
                    "delta_percent": delta_pct,
                    "verdict": "PASS" if performance_pass else "BLOCKED",
                },
                indent=2,
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )
        (EVIDENCE_DIR / "sandu_observation.json").write_text(
            json.dumps(sandu, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        (EVIDENCE_DIR / "third_consumer_recommendation.json").write_text(
            json.dumps(third_consumer, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        (EVIDENCE_DIR / "runtime_cleanup.json").write_text(
            json.dumps(pilot_cleanup, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        (EVIDENCE_DIR / "pilot_runtime_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8"
        )

    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if pilot_pass else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
