"""SECURITY_RELEASE_AUDIT_FIX_06 reproducibility integrity checks.

Scope:
- Frontend self-contained registry dependency
- Release identity consistency (manifest + canonical/mirror release files)
- Alembic expected head metadata consistency
"""

from __future__ import annotations

import json
import re
from pathlib import Path


_BACKEND_DIR = Path(__file__).resolve().parents[1]
_APP_DIR = _BACKEND_DIR.parent
_ROOT_DIR = _APP_DIR.parent


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    assert isinstance(payload, dict), f"Expected JSON object in {path}"
    return payload


def _extract_manifest_value(manifest_text: str, field: str) -> str:
    pattern = rf"\|\s*{re.escape(field)}\s*\|\s*([^|]+)\|"
    m = re.search(pattern, manifest_text)
    assert m is not None, f"Could not find manifest field: {field}"
    return m.group(1).strip()


def test_frontend_registry_is_self_contained_and_in_workspace() -> None:
    frontend_registry = _APP_DIR / "frontend" / "src" / "canonical" / "agent_authority_registry.json"
    canonical_registry = _ROOT_DIR / "docs" / "canonical" / "agent_authority_registry.json"

    assert frontend_registry.is_file(), "Frontend local registry is missing"
    assert canonical_registry.is_file(), "Canonical docs registry is missing"

    # Keep local copy deterministic and in sync with canonical source snapshot.
    assert _read_json(frontend_registry) == _read_json(canonical_registry)


def test_frontend_registry_import_does_not_escape_workspace() -> None:
    registry_module = _APP_DIR / "frontend" / "src" / "lib" / "agentAuthorityRegistry.ts"
    source = registry_module.read_text(encoding="utf-8")

    assert "@/canonical/agent_authority_registry.json" in source
    assert "../../../../docs/canonical/agent_authority_registry.json" not in source


def test_manifest_release_identity_matches_release_json_files() -> None:
    manifest_path = _ROOT_DIR / "RELEASE_MANIFEST.md"
    canonical_release_path = _APP_DIR / "release.json"
    mirror_release_path = _BACKEND_DIR / "release.json"

    manifest = manifest_path.read_text(encoding="utf-8")
    canonical_release = _read_json(canonical_release_path)
    mirror_release = _read_json(mirror_release_path)

    manifest_build_number = _extract_manifest_value(manifest, "Build Number")
    manifest_timestamp = _extract_manifest_value(manifest, "Timestamp")

    # Canonical and mirror must agree on public identity fields.
    for key in ("app_name", "release_version", "release_label", "environment", "release_scope", "build_time"):
        assert canonical_release.get(key) == mirror_release.get(key), f"Mismatch for {key}"

    # Release identity must align with current manifest build metadata.
    assert canonical_release["release_version"] == f"BUILD_{manifest_build_number}"
    assert canonical_release["release_label"] == f"workos-staging-release-BUILD_{manifest_build_number}"
    assert canonical_release["environment"] == "staging"
    assert canonical_release["build_time"] == manifest_timestamp.replace(" UTC", "Z").replace(" ", "T")


def test_alembic_expected_head_consistency_is_s33() -> None:
    manifest_path = _ROOT_DIR / "RELEASE_MANIFEST.md"
    release_script_path = _ROOT_DIR / "scripts" / "create_release_package.py"

    manifest = manifest_path.read_text(encoding="utf-8")
    release_script = release_script_path.read_text(encoding="utf-8")

    expected_head_manifest = _extract_manifest_value(manifest, "Expected Head")
    assert expected_head_manifest == "s33_rendered_output_snapshots"

    assert 'ALEMBIC_EXPECTED_HEAD = "s33_rendered_output_snapshots"' in release_script


def test_frontend_package_tools_are_pnpm_fail_closed() -> None:
    package_json_path = _APP_DIR / "frontend" / "package.json"
    dockerfile_frontend_path = _ROOT_DIR / "Dockerfile.frontend"

    package_json = _read_json(package_json_path)
    scripts = package_json.get("scripts", {})
    validate_script = scripts.get("validate", "")

    assert "pnpm run lint" in validate_script
    assert "pnpm run typecheck" in validate_script
    assert "pnpm run build" in validate_script
    # Guard against a standalone npm fallback command.
    assert re.search(r"(^|\s|&&)npm run\s", validate_script) is None

    dockerfile = dockerfile_frontend_path.read_text(encoding="utf-8")
    assert "pnpm install --frozen-lockfile" in dockerfile
    assert "|| npm install" not in dockerfile
    assert "RUN pnpm run build" in dockerfile
