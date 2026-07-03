"""SECURITY_RELEASE_AUDIT_FIX_09 dependency hygiene contract checks."""

from __future__ import annotations

from pathlib import Path


_BACKEND_DIR = Path(__file__).resolve().parents[1]


def _normalized_requirements(path: Path) -> list[str]:
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def test_frontend_manifest_has_no_latest_dependency_specifier() -> None:
    package_json_path = _BACKEND_DIR.parent / "frontend" / "package.json"
    content = package_json_path.read_text(encoding="utf-8")

    assert '"latest"' not in content
    assert '"@metagptx/vite-plugin-source-locator": "0.0.16"' in content


def test_frontend_axios_is_pinned_to_non_vulnerable_version() -> None:
    package_json_path = _BACKEND_DIR.parent / "frontend" / "package.json"
    frontend_requirements_path = _BACKEND_DIR.parent / "frontend" / "requirements.txt"

    package_content = package_json_path.read_text(encoding="utf-8")
    requirements_content = frontend_requirements_path.read_text(encoding="utf-8")

    assert '"axios": "1.13.4"' in package_content
    assert "axios@1.13.4" in requirements_content


def test_backend_production_requirements_exclude_test_only_packages() -> None:
    prod_requirements = _normalized_requirements(_BACKEND_DIR / "requirements.txt")

    assert all(not entry.startswith("pytest") for entry in prod_requirements)
    assert all(not entry.startswith("pytest-asyncio") for entry in prod_requirements)
    assert any(entry.startswith("httpx") for entry in prod_requirements)


def test_backend_dev_requirements_include_test_only_packages() -> None:
    dev_requirements = _normalized_requirements(_BACKEND_DIR / "requirements-dev.txt")

    assert "-r requirements.txt" in dev_requirements
    assert any(entry.startswith("pytest") for entry in dev_requirements)
    assert any(entry.startswith("pytest-asyncio") for entry in dev_requirements)
