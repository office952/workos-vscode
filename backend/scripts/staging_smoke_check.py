"""
WorkOS / ProdFlow — Staging Smoke Check Script

Non-invasive, read-only verification script for staging deployment.
Does NOT:
- Create data
- Modify database
- Run migrations
- Send emails
- Call mutation endpoints
- Use real credentials for login

Usage:
    python scripts/staging_smoke_check.py --base-url https://staging-api.workos.example.com

    Or with defaults (localhost:8000):
    python scripts/staging_smoke_check.py
"""

import argparse
import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def check(name: str, passed: bool, detail: str = "") -> bool:
    """Print check result and return pass/fail."""
    status = "✅ PASS" if passed else "❌ FAIL"
    msg = f"  {status} | {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return passed


def http_get(url: str, timeout: int = 10) -> tuple:
    """
    Perform HTTP GET. Returns (status_code, body_str, error_str).
    """
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, ""
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return e.code, body, str(e)
    except URLError as e:
        return 0, "", str(e.reason)
    except Exception as e:
        return 0, "", str(e)


def run_smoke_checks(base_url: str) -> dict:
    """Run all smoke checks and return results summary."""
    results = {"passed": 0, "failed": 0, "checks": []}

    print(f"\n{'='*60}")
    print(f"  WorkOS Staging Smoke Check")
    print(f"  Target: {base_url}")
    print(f"{'='*60}\n")

    # --- 1. Health / Environment Readiness ---
    print("  [1] Environment Readiness")
    status, body, err = http_get(f"{base_url}/api/v1/system/environment-readiness")

    if check("Health endpoint reachable", status == 200, f"status={status}"):
        results["passed"] += 1
    else:
        results["failed"] += 1
        if err:
            print(f"       Error: {err}")

    if status == 200:
        try:
            data = json.loads(body)
            env = data.get("environment", "unknown")
            if check("Environment is staging or production", env in ("staging", "production"), f"env={env}"):
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Check no secrets in response
            body_lower = body.lower()
            has_secrets = any(s in body_lower for s in ["password", "secret_key", "client_secret", "token"])
            if check("No secrets in readiness response", not has_secrets):
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Check dev auth status
            dev_auth = data.get("dev_auth_status", data.get("dev_auth_enabled", None))
            if dev_auth is not None:
                is_disabled = dev_auth in (False, "disabled", "blocked", "false")
                if check("Dev auth disabled", is_disabled, f"dev_auth={dev_auth}"):
                    results["passed"] += 1
                else:
                    results["failed"] += 1
        except json.JSONDecodeError:
            if check("Readiness response is valid JSON", False, "parse error"):
                results["passed"] += 1
            else:
                results["failed"] += 1

    print()

    # --- 2. Auth Enforcement ---
    print("  [2] Auth Enforcement")

    # Unauthenticated request should return 401 or 403
    protected_endpoints = [
        "/api/v1/products/",
        "/api/v1/quotes/",
        "/api/v1/orders/",
        "/api/v1/execution/tasks/",
    ]

    for endpoint in protected_endpoints:
        status, _, err = http_get(f"{base_url}{endpoint}")
        # 401 or 403 means auth is enforced; 200 might mean dev auth is active
        auth_enforced = status in (401, 403)
        name = f"Auth enforced on {endpoint}"
        if check(name, auth_enforced, f"status={status}"):
            results["passed"] += 1
        else:
            results["failed"] += 1
            if status == 200:
                print(f"       ⚠️  WARNING: Endpoint returned 200 without auth — dev auth may be active!")

    print()

    # --- 3. Critical Route Availability ---
    print("  [3] Critical Route Availability (expect 401/403 or 200)")

    # These should at least respond (not 500/502/503)
    critical_routes = [
        "/api/v1/system/environment-readiness",
    ]

    for route in critical_routes:
        status, _, err = http_get(f"{base_url}{route}")
        available = status > 0 and status < 500
        if check(f"Route available: {route}", available, f"status={status}"):
            results["passed"] += 1
        else:
            results["failed"] += 1

    print()

    # --- 4. No Server Errors ---
    print("  [4] No Server Errors on Key Endpoints")

    check_endpoints = [
        "/api/v1/system/environment-readiness",
    ]

    for endpoint in check_endpoints:
        status, _, _ = http_get(f"{base_url}{endpoint}")
        no_server_error = status < 500
        if check(f"No 5xx on {endpoint}", no_server_error, f"status={status}"):
            results["passed"] += 1
        else:
            results["failed"] += 1

    print()

    # --- Summary ---
    total = results["passed"] + results["failed"]
    print(f"{'='*60}")
    print(f"  SUMMARY: {results['passed']}/{total} checks passed")
    if results["failed"] == 0:
        print("  VERDICT: ✅ ALL SMOKE CHECKS PASS")
    else:
        print(f"  VERDICT: ⚠️  {results['failed']} check(s) failed")
    print(f"{'='*60}\n")

    return results


def main():
    parser = argparse.ArgumentParser(description="WorkOS Staging Smoke Check")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the staging backend (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    results = run_smoke_checks(args.base_url)

    # Exit code: 0 if all pass, 1 if any fail
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()