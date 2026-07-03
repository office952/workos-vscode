"""SECURITY_RELEASE_AUDIT_FIX_08 Docker/release packaging hygiene checks."""

from __future__ import annotations

import sys
from pathlib import Path


_BACKEND_DIR = Path(__file__).resolve().parents[1]
_APP_DIR = _BACKEND_DIR.parent
_ROOT_DIR = _APP_DIR.parent
_SCRIPTS_DIR = _ROOT_DIR / "scripts"

sys.path.insert(0, str(_SCRIPTS_DIR))

from create_release_package import EXCLUDE_PATTERNS, should_exclude


def test_root_dockerignore_exists_with_required_hygiene_patterns() -> None:
    dockerignore_path = _ROOT_DIR / ".dockerignore"
    assert dockerignore_path.is_file(), ".dockerignore is required to constrain Docker build context"

    content = dockerignore_path.read_text(encoding="utf-8")

    required_patterns = [
        ".git",
        "**/node_modules/",
        "**/__pycache__/",
        "**/*.pyc",
        ".venv/",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        "app/frontend/dist/",
        "dist/",
        "app/backend/logs/",
        "**/*.db",
        "**/*.sqlite",
        "**/*.sqlite3",
        ".env",
        ".env.*",
    ]

    for pattern in required_patterns:
        assert pattern in content, f"Missing .dockerignore pattern: {pattern}"


def test_release_packager_excludes_local_build_runtime_artifacts() -> None:
    # Packaging exclusions should mirror Docker context hygiene for local artifacts.
    for required in [
        ".mypy_cache",
        ".ruff_cache",
        ".cache",
        ".vscode",
        ".idea",
        "venv",
        ".tox",
        "coverage",
    ]:
        assert required in EXCLUDE_PATTERNS

    assert should_exclude("app/backend/__pycache__/main.cpython-312.pyc") is True
    assert should_exclude("app/frontend/node_modules/react/index.js") is True
    assert should_exclude("app/backend/logs/app.log") is True
    assert should_exclude("dist/releases/workos-staging-release-BUILD_25.zip") is True
    assert should_exclude("app/frontend/dist/index.html") is True
    assert should_exclude("app/backend/test_placeholder.db") is True
    assert should_exclude("app/backend/local.sqlite3") is True
    assert should_exclude(".env") is True
    assert should_exclude("app/backend/.env.staging") is True


def test_release_packager_still_includes_runtime_source_files() -> None:
    assert should_exclude("app/backend/main.py") is False
    assert should_exclude("app/frontend/src/main.tsx") is False
    assert should_exclude("Dockerfile.backend") is False
    assert should_exclude("Dockerfile.frontend") is False
