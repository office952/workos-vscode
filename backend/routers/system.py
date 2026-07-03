"""System-level read-only endpoints (version, runtime info).

Canonical source for the runtime release indicator.

Resolution order (STRICT — first source that provides a value wins):
    1. Environment variables:
         - WORKOS_RELEASE_VERSION
         - WORKOS_RELEASE_LABEL
         - WORKOS_ENV
         - WORKOS_BUILD_TIME
         - WORKOS_RELEASE_SCOPE
         - WORKOS_APP_NAME
    2. Canonical file: <workspace>/app/release.json
    3. Mirror file (read-only):   <workspace>/app/backend/release.json
    4. Fallback: unknown / null fields, `source: "unknown"`.

Notes:
    - The mirror at ``app/backend/release.json`` is a byte-identical copy of
      the canonical ``app/release.json`` (plus an optional ``_mirror_of``
      meta field). It exists so that deployments which only ship the
      ``backend/`` subtree still get a valid release descriptor.
    - There is NO hardcoded fallback version. If all three sources are
      missing or unreadable, ``source`` is ``"unknown"`` and every payload
      field is ``None``.

This router is read-only. It does not mutate any business state.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_admin_user as _get_admin_user_lazy
from dependencies.permissions import require_permission

router = APIRouter(
    prefix="/api/v1/system",
    tags=["system"],
    # System version and health are intentionally public (monitoring/probes).
    # The db-identity diagnostic endpoint has its own admin guard below.
)


# ---------------------------------------------------------------------------
# Resolution helpers
# ---------------------------------------------------------------------------

def _unique_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    out: list[Path] = []
    seen: set[str] = set()
    for p in paths:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return tuple(out)


_THIS_FILE = Path(__file__).resolve()
_ROUTER_DIR = _THIS_FILE.parent
_BACKEND_DIR = _ROUTER_DIR.parent
_APP_DIR = _BACKEND_DIR.parent

# Deterministic runtime/repo lookup order:
# 1) explicit container/runtime candidates
# 2) repository/workspace candidates
_RELEASE_JSON_PATHS: tuple[Path, ...] = _unique_paths((
    Path("/app/release.json"),
    Path("/app/app/release.json"),
    Path("/app/app/backend/release.json"),
    _BACKEND_DIR / "release.json",
    _APP_DIR / "release.json",
    _APP_DIR / "backend" / "release.json",
))

# Fields that are part of the public contract of `release.json`.
# The `_mirror_of` field is meta-only and must NEVER appear in responses.
_PUBLIC_RELEASE_FIELDS: tuple[str, ...] = (
    "app_name",
    "release_version",
    "release_label",
    "environment",
    "release_scope",
    "build_time",
)

_EXTRA_RELEASE_FIELDS: tuple[str, ...] = (
    "build_number",
    "git_commit",
    "release_name",
)

_ALL_RELEASE_FIELDS: tuple[str, ...] = _PUBLIC_RELEASE_FIELDS + _EXTRA_RELEASE_FIELDS

_RELEASE_MANIFEST_PATHS: tuple[Path, ...] = _unique_paths((
    Path("/app/RELEASE_MANIFEST.md"),
    Path("/app/app/RELEASE_MANIFEST.md"),
    _BACKEND_DIR / "RELEASE_MANIFEST.md",
    _APP_DIR / "RELEASE_MANIFEST.md",
    _APP_DIR / "backend" / "RELEASE_MANIFEST.md",
))

_ENV_KEYS = {
    "app_name": "WORKOS_APP_NAME",
    "release_version": "WORKOS_RELEASE_VERSION",
    "release_label": "WORKOS_RELEASE_LABEL",
    "environment": "WORKOS_ENV",
    "release_scope": "WORKOS_RELEASE_SCOPE",
    "build_time": "WORKOS_BUILD_TIME",
    "build_number": "WORKOS_BUILD_NUMBER",
    "git_commit": "WORKOS_GIT_COMMIT",
    "release_name": "WORKOS_RELEASE_NAME",
}


def _sanitize_release_name_for_environment(
    release_name: Any,
    environment: Any,
) -> str | None | Any:
    """Prevent staging markers in release_name for live/production payloads."""
    if not isinstance(release_name, str):
        return release_name

    env = str(environment or "").strip().lower()
    if env not in {"live", "prod", "production"}:
        return release_name

    if "staging" not in release_name.lower():
        return release_name

    cleaned = re.sub(r"(?i)\bstaging\b[-_ ]*", "", release_name)
    cleaned = re.sub(r"[-_]{2,}", "-", cleaned).strip("-_ ")
    return cleaned or None


def _read_env_overrides() -> dict[str, str]:
    """Read WORKOS_* env vars that are present (non-empty)."""
    out: dict[str, str] = {}
    for field, env_name in _ENV_KEYS.items():
        val = os.environ.get(env_name)
        if val is not None and val.strip() != "":
            out[field] = val.strip()
    return out


def _load_single_release_file(path: Path) -> dict[str, Any] | None:
    """Load one release.json file. Return None if missing or invalid."""
    try:
        if not path.is_file():
            return None
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return None
        # Strip meta-only fields; never expose them.
        return {k: v for k, v in data.items() if k in _ALL_RELEASE_FIELDS}
    except (OSError, json.JSONDecodeError):
        return None


def _read_release_json() -> tuple[dict[str, Any] | None, Path | None]:
    """Read the first valid release file in strict lookup order.

    Returns a tuple ``(payload, origin_path)``. If no file is readable,
    both elements are ``None``. No hardcoded fallback is ever returned.
    """
    for candidate in _RELEASE_JSON_PATHS:
        data = _load_single_release_file(candidate)
        if data is not None:
            return data, candidate
    return None, None


def _parse_manifest_table_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line.startswith("|"):
        return None
    if set(line.replace("|", "").strip()) == {"-"}:
        return None

    parts = [p.strip() for p in line.split("|") if p.strip()]
    if len(parts) < 2:
        return None

    field, value = parts[0], parts[1]
    if field.lower() == "field" and value.lower() == "value":
        return None
    return field, value


def _read_release_manifest() -> tuple[dict[str, Any] | None, Path | None]:
    for candidate in _RELEASE_MANIFEST_PATHS:
        try:
            if not candidate.is_file():
                continue

            parsed: dict[str, str] = {}
            with candidate.open("r", encoding="utf-8") as fh:
                for line in fh:
                    row = _parse_manifest_table_line(line)
                    if row is None:
                        continue
                    key, value = row
                    parsed[key] = value

            if not parsed:
                continue

            payload: dict[str, Any] = {}
            if parsed.get("Release Name"):
                payload["release_name"] = parsed["Release Name"]
            if parsed.get("Build Number"):
                payload["build_number"] = parsed["Build Number"]
                payload["release_version"] = f"BUILD_{parsed['Build Number']}"
            if parsed.get("Git Commit"):
                payload["git_commit"] = parsed["Git Commit"]
                payload["release_label"] = parsed["Git Commit"][:12]
            if parsed.get("Timestamp"):
                payload["build_time"] = parsed["Timestamp"]

            # Best-effort env classification from release name.
            release_name = payload.get("release_name")
            if isinstance(release_name, str):
                lowered = release_name.lower()
                if re.search(r"\bstaging\b", lowered):
                    payload["environment"] = "staging"

            if payload:
                return payload, candidate
        except OSError:
            continue

    return None, None


def resolve_version_payload() -> dict[str, Any]:
    """Build the canonical version payload from env + release.json files.

    Env vars always win over file contents. Any field still missing stays
    ``None``. The ``source`` field tags which providers contributed:
        - "env"        : at least one env var provided data, no file used.
        - "env+file"   : env vars overrode some fields, a file filled the rest.
        - "file"       : no env vars, a file provided data.
        - "unknown"    : neither source provided anything.
    """
    env_overrides = _read_env_overrides()
    file_payload, _origin = _read_release_json()
    manifest_payload, _manifest_origin = _read_release_manifest()
    manifest_payload = manifest_payload or {}
    file_payload = file_payload or {}

    merged: dict[str, Any] = {field: None for field in _ALL_RELEASE_FIELDS}

    # merge order: manifest (weakest) -> file -> env (strongest)
    for key in merged.keys():
        if key in manifest_payload and manifest_payload[key] not in (None, ""):
            merged[key] = manifest_payload[key]

    for key in merged.keys():
        if key in file_payload and file_payload[key] not in (None, ""):
            merged[key] = file_payload[key]
    for key, value in env_overrides.items():
        merged[key] = value

    merged["release_name"] = _sanitize_release_name_for_environment(
        merged.get("release_name"),
        merged.get("environment"),
    )

    # Derive source tag
    # Keep env/file ordering stable for existing tests and integrations.
    sources: list[str] = []
    if env_overrides:
        sources.append("env")
    if file_payload:
        sources.append("file")
    if manifest_payload:
        sources.append("manifest")
    source = "+".join(sources) if sources else "unknown"

    merged["source"] = source
    merged["observed_at"] = datetime.now(timezone.utc).isoformat()
    return merged


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/version")
async def get_system_version() -> dict[str, Any]:
    """Return the runtime release version indicator.

    Read-only. Never mutates business state.
    """
    return resolve_version_payload()


# ---------------------------------------------------------------------------
# Sprint #40 — GET /api/v1/system/health
# ---------------------------------------------------------------------------

@router.get("/health")
async def get_system_health(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return a minimal public health payload safe for unauthenticated probes."""
    # Imported lazily to avoid circular imports at startup.
    from services.system_health_service import SystemHealthService, _iso_now_utc

    try:
        return await SystemHealthService(db).run_public_health()
    except Exception:
        # Fail safe without leaking diagnostics while preserving liveness semantics.
        return {
            "status": "degraded",
            "service": "workos",
            "generated_at": _iso_now_utc(),
            "checks": {},
        }


@router.get(
    "/diagnostics",
    dependencies=[Depends(require_permission("system.diagnostics.read"))],
)
async def get_system_diagnostics(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return authenticated system diagnostics payload with detailed check data."""
    from services.system_health_service import SystemHealthService

    return await SystemHealthService(db).run_diagnostics()


# ---------------------------------------------------------------------------
# DIAGNOSTIC-ONLY — GET /api/v1/system/db-identity
#
# Gated behind the feature flag ``DEBUG_DB_IDENTITY_ENABLED``. Returns
# non-secret information about the Postgres connection the runtime is
# currently bound to. Used by ``plan__backend_db_identity_alignment`` to
# confirm whether live and workspace resolve to the same DB/schema/user.
#
# CLEANUP: This route and its service (`services.db_identity_service`)
# MUST be removed or the feature flag MUST be unset once the
# investigation concludes. See
# `docs/logs/log__backend_db_identity_alignment.md` for the timeline.
# ---------------------------------------------------------------------------

@router.get("/db-identity")
async def get_system_db_identity(
    db: AsyncSession = Depends(get_db),
    _admin: "Any" = Depends(_get_admin_user_lazy),
) -> dict[str, Any]:
    """Return diagnostic DB identity info. Read-only. Gated by env flag.

    AUDIT FIX: Requires admin authentication. Returns HTTP 404 when the
    diagnostic flag is not enabled, so the route is invisible by default.
    """
    # Imported lazily so unrelated code paths never pull the diagnostic.
    from fastapi import HTTPException
    from services.db_identity_service import DBIdentityService, is_enabled

    if not is_enabled():
        raise HTTPException(
            status_code=404,
            detail="db-identity endpoint is disabled",
        )

    version_payload = resolve_version_payload()
    release_version = version_payload.get("release_version")
    return await DBIdentityService(db).run(release_version=release_version)