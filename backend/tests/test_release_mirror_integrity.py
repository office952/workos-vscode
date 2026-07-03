"""Release-mirror integrity tests.

These tests enforce the Sprint v92.1 "Live Environment Alignment" rule:
  - ``/workspace/app/release.json`` is the canonical release descriptor.
  - ``/workspace/app/backend/release.json`` is a read-only byte-identical
    mirror of it (excluding the optional meta key ``_mirror_of``).

They MUST fail if any of the following is true:
  1. The mirror file is missing.
  2. Canonical and mirror disagree on any public field.
  3. The resolver returns ``source="unknown"`` while at least one of
     canonical/mirror exists and is parseable on disk.

These tests are dependency-free on DB/env and safe to run in any CI stage.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

# --- Paths ------------------------------------------------------------------

# This test file lives at /workspace/app/backend/tests/...
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_APP_DIR = _BACKEND_DIR.parent

CANONICAL_PATH = _APP_DIR / "release.json"
MIRROR_PATH = _BACKEND_DIR / "release.json"

_PUBLIC_FIELDS = (
    "app_name",
    "release_version",
    "release_label",
    "environment",
    "release_scope",
    "build_time",
)


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, dict), f"{path} must contain a JSON object"
    return data


def _strip_meta(payload: dict) -> dict:
    """Remove meta-only fields (like ``_mirror_of``) before comparison."""
    return {k: v for k, v in payload.items() if not k.startswith("_")}


# --- Tests ------------------------------------------------------------------

def test_canonical_exists() -> None:
    """Sanity: canonical file must exist."""
    assert CANONICAL_PATH.is_file(), (
        f"Canonical release file missing: {CANONICAL_PATH}"
    )


def test_mirror_exists() -> None:
    """FAIL if the mirror file is missing."""
    assert MIRROR_PATH.is_file(), (
        f"Mirror release file missing: {MIRROR_PATH}. "
        "The backend mirror is required so that deploys that only ship "
        "the backend/ subtree still have a valid release descriptor."
    )


def test_canonical_equals_mirror_public_fields() -> None:
    """FAIL if canonical and mirror diverge on any public field.

    The mirror is allowed to contain the extra meta key ``_mirror_of`` for
    traceability, but no other divergence is permitted.
    """
    canonical = _strip_meta(_read_json(CANONICAL_PATH))
    mirror = _strip_meta(_read_json(MIRROR_PATH))
    assert canonical == mirror, (
        "Canonical and mirror release.json disagree on public fields. "
        f"canonical={canonical} mirror={mirror}"
    )
    for field in _PUBLIC_FIELDS:
        assert field in canonical, f"Canonical missing required field: {field}"
        assert field in mirror, f"Mirror missing required field: {field}"


def test_mirror_has_no_unexpected_extra_fields() -> None:
    """Mirror may only add the ``_mirror_of`` meta key; nothing else."""
    mirror_raw = _read_json(MIRROR_PATH)
    allowed = set(_PUBLIC_FIELDS) | {"_mirror_of"}
    extra = set(mirror_raw.keys()) - allowed
    assert not extra, f"Mirror has unexpected extra fields: {extra}"


def test_resolver_not_unknown_when_files_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    """FAIL if resolver returns ``source='unknown'`` while a file exists.

    Env overrides are stripped for this test so the assertion targets the
    file-lookup path strictly.
    """
    # Strip env overrides to exercise file lookup path only.
    for env_name in (
        "WORKOS_APP_NAME",
        "WORKOS_RELEASE_VERSION",
        "WORKOS_RELEASE_LABEL",
        "WORKOS_ENV",
        "WORKOS_RELEASE_SCOPE",
        "WORKOS_BUILD_TIME",
    ):
        monkeypatch.delenv(env_name, raising=False)

    # Precondition: at least one of canonical/mirror is present on disk.
    assert CANONICAL_PATH.is_file() or MIRROR_PATH.is_file(), (
        "Precondition failed: neither canonical nor mirror file exists. "
        "This test only asserts resolver behaviour when a file is present."
    )

    # Import lazily so monkeypatch takes effect before the resolver reads env.
    import sys
    backend_dir_str = str(_BACKEND_DIR)
    if backend_dir_str not in sys.path:
        sys.path.insert(0, backend_dir_str)
    from routers.system import resolve_version_payload  # noqa: WPS433

    payload = resolve_version_payload()
    assert payload["source"] != "unknown", (
        "Resolver returned source='unknown' while at least one of "
        f"{CANONICAL_PATH} / {MIRROR_PATH} exists on disk. "
        f"Full payload: {payload}"
    )
    # When a file source is used without env overrides, source must be 'file'.
    assert payload["source"] == "file", (
        f"Expected source='file' with no env overrides; got: {payload['source']}"
    )
    # And release_version must be populated (not None) in this scenario.
    assert payload["release_version"] is not None, (
        f"release_version is None despite file source present. payload={payload}"
    )