"""BUILD 20 — Startup / Health Safety Check.

Validates environment configuration at application startup.
Deployed builds fail closed on BLOCKED checks.
Local/development/test checks remain informational unless explicit deploy
metadata indicates a deployed runtime.

This module does NOT block local dev startup.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Optional

logger = logging.getLogger(__name__)

CheckStatus = Literal["PASS", "WARNING", "BLOCKED"]

_VALID_RUNTIME_ENVIRONMENTS = {"local", "development", "staging", "production", "test"}
_STRICT_DEPLOYMENT_ENVIRONMENTS = {"staging", "production", "live"}

_STARTUP_RELEASE_JSON_PATHS: tuple[Path, ...] = (
    Path("/app/release.json"),
    Path("/app/app/release.json"),
    Path("/app/app/backend/release.json"),
    Path(__file__).resolve().parent.parent / "release.json",
    Path(__file__).resolve().parent.parent.parent / "release.json",
    Path(__file__).resolve().parent.parent.parent / "backend" / "release.json",
)


@dataclass
class SafetyCheckResult:
    name: str
    status: CheckStatus
    message: str


@dataclass
class EnvironmentReadinessReport:
    environment: str
    overall_status: CheckStatus = "PASS"
    checks: List[SafetyCheckResult] = field(default_factory=list)

    def add(self, check: SafetyCheckResult) -> None:
        self.checks.append(check)
        if check.status == "BLOCKED" and self.overall_status != "BLOCKED":
            self.overall_status = "BLOCKED"
        elif check.status == "WARNING" and self.overall_status == "PASS":
            self.overall_status = "WARNING"


def _read_startup_release_environment() -> Optional[str]:
    for candidate in _STARTUP_RELEASE_JSON_PATHS:
        try:
            if not candidate.is_file():
                continue
            with candidate.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                continue
            release_environment = payload.get("environment")
            if isinstance(release_environment, str):
                normalized = release_environment.strip().lower()
                if normalized:
                    return normalized
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _get_explicit_runtime_environment() -> Optional[str]:
    app_env_raw = os.environ.get("APP_ENV", "").strip()
    if app_env_raw:
        return app_env_raw
    environment_raw = os.environ.get("ENVIRONMENT", "").strip()
    if environment_raw:
        return environment_raw
    return None


def _resolve_startup_environment() -> tuple[str, Optional[str], Optional[str]]:
    explicit_raw = _get_explicit_runtime_environment()
    explicit_normalized = explicit_raw.lower() if explicit_raw else None
    release_environment = _read_startup_release_environment()

    if explicit_normalized in _VALID_RUNTIME_ENVIRONMENTS:
        return explicit_normalized, explicit_raw, release_environment

    if release_environment in _STRICT_DEPLOYMENT_ENVIRONMENTS:
        return release_environment, explicit_raw, release_environment

    return "development", explicit_raw, release_environment


def run_startup_safety_checks() -> EnvironmentReadinessReport:
    """
    Run all startup safety checks and return a report.

    In staging/production/live builds:
    - BLOCKED checks indicate critical misconfigurations that should prevent deployment.
    - WARNING checks indicate non-ideal but non-critical issues.

    In local/development/test:
    - All checks are informational (WARNING at most, never BLOCKED).
    """
    env, explicit_env_raw, release_environment = _resolve_startup_environment()
    report = EnvironmentReadinessReport(environment=env)
    is_strict = env in _STRICT_DEPLOYMENT_ENVIRONMENTS

    explicit_normalized = explicit_env_raw.lower() if explicit_env_raw else None

    # --- Check 1: runtime environment is explicit and valid ---
    if explicit_normalized in _VALID_RUNTIME_ENVIRONMENTS:
        if is_strict and explicit_normalized in {"local", "development", "test"}:
            report.add(
                SafetyCheckResult(
                    name="APP_ENV_SET",
                    status="BLOCKED",
                    message=(
                        f"Runtime environment '{explicit_env_raw}' is a development fallback "
                        f"and is not allowed for deployed environment '{env}'"
                    ),
                )
            )
        else:
            report.add(
                SafetyCheckResult(
                    name="APP_ENV_SET",
                    status="PASS",
                    message=f"Runtime environment is explicitly set to '{explicit_env_raw}'",
                )
            )
    else:
        app_env_status: CheckStatus = "BLOCKED" if is_strict else "WARNING"
        if explicit_env_raw:
            message = (
                f"Runtime environment value '{explicit_env_raw}' is invalid; deployed environments must not fall back to development"
            )
        elif is_strict:
            message = (
                "Runtime environment is not explicitly set for a deployed build; must not fall back to development"
            )
        else:
            message = "APP_ENV is not set, defaulting to 'development'"
        report.add(
            SafetyCheckResult(
                name="APP_ENV_SET",
                status=app_env_status,
                message=message,
            )
        )

    if is_strict:
        if explicit_normalized in _VALID_RUNTIME_ENVIRONMENTS and explicit_normalized not in _STRICT_DEPLOYMENT_ENVIRONMENTS:
            report.add(
                SafetyCheckResult(
                    name="DEPLOYMENT_ENVIRONMENT_MATCH",
                    status="BLOCKED",
                    message=(
                        f"Deployed environment '{env}' cannot run with development-mode runtime value '{explicit_env_raw}'"
                    ),
                )
            )
        elif explicit_normalized in _VALID_RUNTIME_ENVIRONMENTS:
            report.add(
                SafetyCheckResult(
                    name="DEPLOYMENT_ENVIRONMENT_MATCH",
                    status="PASS",
                    message=(
                        f"Deployed environment '{env}' has an explicit runtime value '{explicit_env_raw}'"
                    ),
                )
            )
        else:
            report.add(
                SafetyCheckResult(
                    name="DEPLOYMENT_ENVIRONMENT_MATCH",
                    status="BLOCKED",
                    message=(
                        f"Deployed environment '{env}' requires an explicit runtime environment value"
                    ),
                )
            )

    # --- Check 2: Dev auth not active in deployed builds ---
    if is_strict:
        report.add(
            SafetyCheckResult(
                name="DEV_AUTH_DISABLED",
                status="PASS",
                message="Dev auth fallback is disabled for deployed environments",
            )
        )
    else:
        report.add(
            SafetyCheckResult(
                name="DEV_AUTH_DISABLED",
                status="PASS",
                message=f"Dev auth fallback is permitted (environment is {env})",
            )
        )

    # --- Check 3: Debug mode ---
    debug_val = os.environ.get("DEBUG", "").strip().lower()
    if is_strict and debug_val in ("true", "1", "yes"):
        report.add(
            SafetyCheckResult(
                name="DEBUG_MODE_OFF",
                status="BLOCKED",
                message="DEBUG mode is enabled in staging/production/live — this is unsafe",
            )
        )
    else:
        report.add(
            SafetyCheckResult(
                name="DEBUG_MODE_OFF",
                status="PASS",
                message="Debug mode is appropriately configured",
            )
        )

    # --- Check 3b: Parity observe flags forced off in deployed environments ---
    try:
        from services.parity_observe.config import check_parity_production_guard

        parity_status, parity_message = check_parity_production_guard()
        report.add(
            SafetyCheckResult(
                name="PARITY_RUNTIME_FLAGS_GUARD",
                status="BLOCKED" if parity_status == "BLOCKED" else ("WARNING" if parity_status == "WARNING" else "PASS"),
                message=parity_message,
            )
        )
    except Exception as exc:
        report.add(
            SafetyCheckResult(
                name="PARITY_RUNTIME_FLAGS_GUARD",
                status="WARNING" if not is_strict else "BLOCKED",
                message=f"Parity runtime guard check failed: {exc}",
            )
        )

    # --- Check 4: DATABASE_URL presence ---
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if is_strict and not db_url:
        report.add(
            SafetyCheckResult(
                name="DATABASE_URL_SET",
                status="BLOCKED",
                message="DATABASE_URL is not set in staging/production/live",
            )
        )
    elif db_url:
        report.add(
            SafetyCheckResult(
                name="DATABASE_URL_SET",
                status="PASS",
                message="DATABASE_URL is configured",
            )
        )
    else:
        report.add(
            SafetyCheckResult(
                name="DATABASE_URL_SET",
                status="PASS",
                message="DATABASE_URL not set (acceptable in local/dev)",
            )
        )

    # --- Check 5: JWT/OIDC configuration in deployed builds ---
    jwt_secret = os.environ.get("JWT_SECRET_KEY", "").strip()
    oidc_issuer = os.environ.get("OIDC_ISSUER_URL", "").strip()
    if is_strict:
        if not jwt_secret:
            report.add(
                SafetyCheckResult(
                    name="JWT_SECRET_CONFIGURED",
                    status="BLOCKED",
                    message="JWT_SECRET_KEY is not set in staging/production/live",
                )
            )
        else:
            report.add(
                SafetyCheckResult(
                    name="JWT_SECRET_CONFIGURED",
                    status="PASS",
                    message="JWT_SECRET_KEY is configured",
                )
            )

        if not oidc_issuer:
            report.add(
                SafetyCheckResult(
                    name="OIDC_ISSUER_CONFIGURED",
                    status="WARNING",
                    message="OIDC_ISSUER_URL is not set — OIDC login will not work",
                )
            )
        else:
            report.add(
                SafetyCheckResult(
                    name="OIDC_ISSUER_CONFIGURED",
                    status="PASS",
                    message="OIDC_ISSUER_URL is configured",
                )
            )
    else:
        report.add(
            SafetyCheckResult(
                name="JWT_SECRET_CONFIGURED",
                status="PASS",
                message="JWT/OIDC config check skipped (non-strict environment)",
            )
        )

    # --- Check 6: CORS wildcard ---
    cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()
    if is_strict and cors_origins == "*":
        report.add(
            SafetyCheckResult(
                name="CORS_NOT_WILDCARD",
                status="WARNING",
                message="CORS_ALLOWED_ORIGINS is '*' in staging/production/live — consider restricting",
            )
        )
    else:
        report.add(
            SafetyCheckResult(
                name="CORS_NOT_WILDCARD",
                status="PASS",
                message="CORS origins are appropriately configured",
            )
        )

    return report


def log_startup_safety_report(report: EnvironmentReadinessReport) -> None:
    """Log the safety report at appropriate levels."""
    logger.info(
        "=== Environment Readiness Report [%s] === Overall: %s",
        report.environment,
        report.overall_status,
    )
    for check in report.checks:
        if check.status == "BLOCKED":
            logger.error("  [BLOCKED] %s: %s", check.name, check.message)
        elif check.status == "WARNING":
            logger.warning("  [WARNING] %s: %s", check.name, check.message)
        else:
            logger.info("  [PASS] %s: %s", check.name, check.message)

    if report.overall_status == "BLOCKED":
        logger.error(
            "=== CRITICAL: Environment has BLOCKED checks. Deployment to %s should NOT proceed. ===",
            report.environment,
        )