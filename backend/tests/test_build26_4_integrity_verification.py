"""
BUILD 26.4 — Release Package Integrity & Verification Gate Tests

Tests the strengthened verification checks added in BUILD 26.4:
- Docker runtime files inclusion
- OIDC auth code content verification
- QA documentation presence
- Backend test files presence
- Docker compose secrets safety (no real credentials)
"""

import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

# Add scripts directory to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from create_release_package import (
    collect_files,
    check_for_secrets,
    create_package,
    verify_package,
    should_exclude,
    is_safe_exception,
    parse_dockerfile_copy_sources,
    verify_dockerfile_copy_sources,
    INCLUDE_FILES,
)


class TestDockerFilesInclusion:
    """Verify Docker runtime files are included in the package."""

    def test_docker_compose_in_include_files(self):
        """docker-compose.yml must be in INCLUDE_FILES."""
        assert "docker-compose.yml" in INCLUDE_FILES

    def test_dockerfile_backend_in_include_files(self):
        """Dockerfile.backend must be in INCLUDE_FILES."""
        assert "Dockerfile.backend" in INCLUDE_FILES

    def test_dockerfile_frontend_in_include_files(self):
        """Dockerfile.frontend must be in INCLUDE_FILES."""
        assert "Dockerfile.frontend" in INCLUDE_FILES

    def test_caddyfile_in_include_files(self):
        """Caddyfile must be in INCLUDE_FILES."""
        assert "Caddyfile" in INCLUDE_FILES

    def test_caddyfile_frontend_in_include_files(self):
        """Caddyfile.frontend must be in INCLUDE_FILES."""
        assert "Caddyfile.frontend" in INCLUDE_FILES

    def test_docker_compose_exists_on_disk(self):
        """docker-compose.yml must exist in project root."""
        assert (PROJECT_ROOT / "docker-compose.yml").exists()

    def test_dockerfile_backend_exists_on_disk(self):
        """Dockerfile.backend must exist in project root."""
        assert (PROJECT_ROOT / "Dockerfile.backend").exists()

    def test_dockerfile_frontend_exists_on_disk(self):
        """Dockerfile.frontend must exist in project root."""
        assert (PROJECT_ROOT / "Dockerfile.frontend").exists()

    def test_caddyfile_exists_on_disk(self):
        """Caddyfile must exist in project root."""
        assert (PROJECT_ROOT / "Caddyfile").exists()

    def test_caddyfile_frontend_exists_on_disk(self):
        """Caddyfile.frontend must exist in project root."""
        assert (PROJECT_ROOT / "Caddyfile.frontend").exists()

    def test_docker_files_collected(self):
        """All Docker files must be collected by collect_files."""
        files = collect_files(PROJECT_ROOT)
        rel_paths = [rel for _, rel in files]
        docker_files = [
            "docker-compose.yml",
            "Dockerfile.backend",
            "Dockerfile.frontend",
            "Caddyfile",
            "Caddyfile.frontend",
        ]
        for df in docker_files:
            assert df in rel_paths, f"{df} not collected"

    def test_docker_compose_no_secrets(self):
        """docker-compose.yml must not trigger secrets detection."""
        filepath = PROJECT_ROOT / "docker-compose.yml"
        violations = check_for_secrets(filepath)
        assert violations == [], f"Secrets detected in docker-compose.yml: {violations}"

    def test_docker_compose_no_hardcoded_database_url(self):
        """docker-compose.yml must NOT have a hardcoded DATABASE_URL in environment block.
        
        DATABASE_URL should come from .env.staging via env_file directive,
        not from the compose environment block which would override it.
        """
        content = (PROJECT_ROOT / "docker-compose.yml").read_text()
        # Must not have DATABASE_URL in environment (it comes from env_file)
        assert "DATABASE_URL=postgresql" not in content, \
            "docker-compose.yml must not hardcode DATABASE_URL — env_file provides it"
        # Must have env_file directive for backend service
        assert "env_file:" in content
        assert ".env.staging" in content


class TestDockerFileContent:
    """Verify Docker file content is valid for staging deployment."""

    def test_docker_compose_has_services(self):
        """docker-compose.yml must define postgres, backend, frontend, caddy services."""
        content = (PROJECT_ROOT / "docker-compose.yml").read_text()
        for service in ["postgres:", "backend:", "frontend:", "caddy:"]:
            assert service in content, f"Service {service} not found in docker-compose.yml"

    def test_docker_compose_no_backend_bind_mount(self):
        """docker-compose.yml must NOT have ./app/backend:/app bind mount.
        
        Staging release must use the built image, not override /app with host source.
        A bind mount would defeat the purpose of the Docker build.
        """
        content = (PROJECT_ROOT / "docker-compose.yml").read_text()
        assert "./app/backend:/app" not in content, (
            "docker-compose.yml must not bind-mount ./app/backend:/app — "
            "staging uses the built image, not host source override"
        )
        assert "./app/backend" not in content, (
            "docker-compose.yml must not reference ./app/backend in volumes — "
            "staging release is self-contained"
        )

    def test_dockerfile_backend_has_requirements(self):
        """Dockerfile.backend must install requirements.txt."""
        content = (PROJECT_ROOT / "Dockerfile.backend").read_text()
        assert "requirements.txt" in content

    def test_dockerfile_backend_has_uvicorn(self):
        """Dockerfile.backend must run uvicorn."""
        content = (PROJECT_ROOT / "Dockerfile.backend").read_text()
        assert "uvicorn" in content

    def test_dockerfile_frontend_multistage(self):
        """Dockerfile.frontend must use multi-stage build."""
        content = (PROJECT_ROOT / "Dockerfile.frontend").read_text()
        assert "AS builder" in content or "as builder" in content

    def test_dockerfile_frontend_builds_app(self):
        """Dockerfile.frontend must run npm run build."""
        content = (PROJECT_ROOT / "Dockerfile.frontend").read_text()
        assert "npm run build" in content

    def test_caddyfile_has_staging_domain(self):
        """Caddyfile must reference staging.workos.ro."""
        content = (PROJECT_ROOT / "Caddyfile").read_text()
        assert "staging.workos.ro" in content

    def test_caddyfile_has_api_domain(self):
        """Caddyfile must reference api-staging.workos.ro."""
        content = (PROJECT_ROOT / "Caddyfile").read_text()
        assert "api-staging.workos.ro" in content


class TestOIDCContentVerification:
    """Verify OIDC auth code is present in core/auth.py."""

    def test_oidc_optional_value_function(self):
        """core/auth.py must contain _optional_oidc_value."""
        content = (PROJECT_ROOT / "app/backend/core/auth.py").read_text()
        assert "_optional_oidc_value" in content

    def test_oidc_resolve_authorization_endpoint(self):
        """core/auth.py must contain _resolve_authorization_endpoint."""
        content = (PROJECT_ROOT / "app/backend/core/auth.py").read_text()
        assert "_resolve_authorization_endpoint" in content

    def test_oidc_resolve_token_endpoint(self):
        """core/auth.py must contain _resolve_token_endpoint."""
        content = (PROJECT_ROOT / "app/backend/core/auth.py").read_text()
        assert "_resolve_token_endpoint" in content

    def test_oidc_resolve_jwks_url(self):
        """core/auth.py must contain _resolve_jwks_url."""
        content = (PROJECT_ROOT / "app/backend/core/auth.py").read_text()
        assert "_resolve_jwks_url" in content

    def test_auth_router_resolve_frontend_url(self):
        """routers/auth.py must contain _resolve_frontend_url."""
        content = (PROJECT_ROOT / "app/backend/routers/auth.py").read_text()
        assert "_resolve_frontend_url" in content

    def test_env_example_has_oidc_overrides(self):
        """.env.example must document OIDC endpoint overrides."""
        content = (PROJECT_ROOT / "app/backend/.env.example").read_text()
        assert "OIDC" in content


class TestQADocumentation:
    """Verify QA documentation is sufficient."""

    def test_qa_directory_exists(self):
        """docs/qa/ must exist."""
        assert (PROJECT_ROOT / "docs/qa").is_dir()

    def test_qa_has_minimum_docs(self):
        """docs/qa/ must have at least 3 QA documents."""
        qa_files = list((PROJECT_ROOT / "docs/qa").glob("*.md"))
        assert len(qa_files) >= 3, f"Only {len(qa_files)} QA docs found"

    def test_qa_has_build26_docs(self):
        """docs/qa/ must have BUILD 26 related QA docs."""
        qa_files = [f.name for f in (PROJECT_ROOT / "docs/qa").glob("BUILD_26*.md")]
        assert len(qa_files) >= 1, f"No BUILD 26 QA docs found"


class TestBackendTestFiles:
    """Verify backend test files are present and sufficient."""

    def test_tests_directory_exists(self):
        """app/backend/tests/ must exist."""
        assert (PROJECT_ROOT / "app/backend/tests").is_dir()

    def test_minimum_test_files(self):
        """app/backend/tests/ must have at least 10 test files."""
        test_files = list((PROJECT_ROOT / "app/backend/tests").glob("test_*.py"))
        assert len(test_files) >= 10, f"Only {len(test_files)} test files found"

    def test_build26_tests_exist(self):
        """BUILD 26 release package tests must exist."""
        assert (PROJECT_ROOT / "app/backend/tests/test_build26_release_package.py").exists()

    def test_build26_2_oidc_tests_exist(self):
        """BUILD 26.2 OIDC tests must exist."""
        assert (PROJECT_ROOT / "app/backend/tests/test_build26_2_oidc_google_auth.py").exists()


class TestVerificationGateStrength:
    """Test that the strengthened verification gate catches issues."""

    def test_verify_catches_missing_docker_files(self):
        """Verification should fail if Docker files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "workos-staging-release-BUILD_25.zip"
            with zipfile.ZipFile(artifact_path, "w") as zf:
                zf.writestr("app/backend/main.py", "# backend")
                zf.writestr("app/backend/core/auth.py", "def _optional_oidc_value(): pass\ndef _resolve_authorization_endpoint(): pass\ndef _resolve_token_endpoint(): pass")
                zf.writestr("app/frontend/src/App.tsx", "// frontend")
                zf.writestr("docs/deployment/README.md", "# deploy")
                zf.writestr("docs/qa/QA1.md", "# qa1")
                zf.writestr("docs/qa/QA2.md", "# qa2")
                zf.writestr("docs/qa/QA3.md", "# qa3")
                zf.writestr("app/backend/alembic/versions/s31_merge_heads.py", "# migration")
                zf.writestr("app/backend/tests/test_a.py", "# test")
                zf.writestr("docs/canonical/agent_authority_registry.json", "{}")
                zf.writestr("RELEASE_MANIFEST.md", "# manifest")
                # Note: NO Docker files
            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is False

    def test_verify_catches_missing_oidc_markers(self):
        """Verification should fail if OIDC markers are missing from auth.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "workos-staging-release-BUILD_25.zip"
            with zipfile.ZipFile(artifact_path, "w") as zf:
                zf.writestr("app/backend/main.py", "# backend")
                # auth.py WITHOUT OIDC markers
                zf.writestr("app/backend/core/auth.py", "def validate_token(): pass")
                zf.writestr("app/frontend/src/App.tsx", "// frontend")
                zf.writestr("docs/deployment/README.md", "# deploy")
                zf.writestr("docs/qa/QA1.md", "# qa1")
                zf.writestr("docs/qa/QA2.md", "# qa2")
                zf.writestr("docs/qa/QA3.md", "# qa3")
                zf.writestr("app/backend/alembic/versions/s31_merge_heads.py", "# migration")
                zf.writestr("app/backend/tests/test_a.py", "# test")
                zf.writestr("docs/canonical/agent_authority_registry.json", "{}")
                zf.writestr("RELEASE_MANIFEST.md", "# manifest")
                zf.writestr("docker-compose.yml", "# compose")
                zf.writestr("Dockerfile.backend", "# backend")
                zf.writestr("Dockerfile.frontend", "# frontend")
                zf.writestr("Caddyfile", "# caddy")
                zf.writestr("Caddyfile.frontend", "# caddy frontend")
            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is False

    def test_verify_passes_with_all_checks(self):
        """Verification should pass when all 13 checks are satisfied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "workos-staging-release-BUILD_25.zip"
            with zipfile.ZipFile(artifact_path, "w") as zf:
                # Check 1: app/backend
                zf.writestr("app/backend/main.py", "# backend")
                # Check 2: app/frontend
                zf.writestr("app/frontend/src/App.tsx", "// frontend")
                # Check 3: docs/deployment
                zf.writestr("docs/deployment/README.md", "# deploy")
                # Check 4 & 5: alembic with s31
                zf.writestr("app/backend/alembic/versions/s31_merge_heads.py", "# migration")
                # Check 6: no forbidden (implicitly satisfied)
                # Check 7: manifest
                zf.writestr("RELEASE_MANIFEST.md", "# manifest")
                # Check 8: no secrets (implicitly satisfied)
                # Check 9: frontend build deps
                zf.writestr("docs/canonical/agent_authority_registry.json", "{}")
                # Check 10: Docker files
                zf.writestr("docker-compose.yml", "# compose")
                zf.writestr("Dockerfile.backend", "# backend")
                zf.writestr("Dockerfile.frontend", "# frontend")
                zf.writestr("Caddyfile", "# caddy")
                zf.writestr("Caddyfile.frontend", "# caddy frontend")
                # Check 11: OIDC markers
                zf.writestr(
                    "app/backend/core/auth.py",
                    "def _optional_oidc_value(): pass\n"
                    "def _resolve_authorization_endpoint(): pass\n"
                    "def _resolve_token_endpoint(): pass\n",
                )
                # Check 12: QA docs (>= 3)
                zf.writestr("docs/qa/QA1.md", "# qa1")
                zf.writestr("docs/qa/QA2.md", "# qa2")
                zf.writestr("docs/qa/QA3.md", "# qa3")
                # Check 13: Backend test files (>= 10)
                for i in range(10):
                    zf.writestr(f"app/backend/tests/test_{i}.py", f"# test {i}")
            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is True

    def test_verify_catches_insufficient_qa_docs(self):
        """Verification should fail if fewer than 3 QA docs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "workos-staging-release-BUILD_25.zip"
            with zipfile.ZipFile(artifact_path, "w") as zf:
                zf.writestr("app/backend/main.py", "# backend")
                zf.writestr("app/backend/core/auth.py", "def _optional_oidc_value(): pass\ndef _resolve_authorization_endpoint(): pass\ndef _resolve_token_endpoint(): pass")
                zf.writestr("app/frontend/src/App.tsx", "// frontend")
                zf.writestr("docs/deployment/README.md", "# deploy")
                # Only 2 QA docs (need >= 3)
                zf.writestr("docs/qa/QA1.md", "# qa1")
                zf.writestr("docs/qa/QA2.md", "# qa2")
                zf.writestr("app/backend/alembic/versions/s31_merge_heads.py", "# migration")
                zf.writestr("docs/canonical/agent_authority_registry.json", "{}")
                zf.writestr("RELEASE_MANIFEST.md", "# manifest")
                zf.writestr("docker-compose.yml", "# compose")
                zf.writestr("Dockerfile.backend", "# backend")
                zf.writestr("Dockerfile.frontend", "# frontend")
                zf.writestr("Caddyfile", "# caddy")
                zf.writestr("Caddyfile.frontend", "# caddy frontend")
                for i in range(10):
                    zf.writestr(f"app/backend/tests/test_{i}.py", f"# test {i}")
            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is False

    def test_verify_catches_insufficient_test_files(self):
        """Verification should fail if fewer than 10 test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "workos-staging-release-BUILD_25.zip"
            with zipfile.ZipFile(artifact_path, "w") as zf:
                zf.writestr("app/backend/main.py", "# backend")
                zf.writestr("app/backend/core/auth.py", "def _optional_oidc_value(): pass\ndef _resolve_authorization_endpoint(): pass\ndef _resolve_token_endpoint(): pass")
                zf.writestr("app/frontend/src/App.tsx", "// frontend")
                zf.writestr("docs/deployment/README.md", "# deploy")
                zf.writestr("docs/qa/QA1.md", "# qa1")
                zf.writestr("docs/qa/QA2.md", "# qa2")
                zf.writestr("docs/qa/QA3.md", "# qa3")
                zf.writestr("app/backend/alembic/versions/s31_merge_heads.py", "# migration")
                zf.writestr("docs/canonical/agent_authority_registry.json", "{}")
                zf.writestr("RELEASE_MANIFEST.md", "# manifest")
                zf.writestr("docker-compose.yml", "# compose")
                zf.writestr("Dockerfile.backend", "# backend")
                zf.writestr("Dockerfile.frontend", "# frontend")
                zf.writestr("Caddyfile", "# caddy")
                zf.writestr("Caddyfile.frontend", "# caddy frontend")
                # Only 5 test files (need >= 10)
                for i in range(5):
                    zf.writestr(f"app/backend/tests/test_{i}.py", f"# test {i}")
            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is False


class TestPackageCreationWithDockerFiles:
    """Test that package creation includes Docker files."""

    def test_package_includes_docker_files(self):
        """Created package must contain all Docker runtime files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert result is not None
            with zipfile.ZipFile(result, "r") as zf:
                names = zf.namelist()
                docker_files = [
                    "docker-compose.yml",
                    "Dockerfile.backend",
                    "Dockerfile.frontend",
                    "Caddyfile",
                    "Caddyfile.frontend",
                ]
                for df in docker_files:
                    assert df in names, f"{df} not in package"

    def test_full_verify_passes_on_created_package(self):
        """Full verification should pass on a freshly created package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert result is not None
            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is True


class TestDockerfileCopySourceVerification:
    """Verify that all Dockerfile COPY/ADD sources exist in project and package."""

    def test_parse_dockerfile_backend_sources(self):
        """parse_dockerfile_copy_sources extracts COPY sources from Dockerfile.backend."""
        dockerfile = PROJECT_ROOT / "Dockerfile.backend"
        sources = parse_dockerfile_copy_sources(dockerfile)
        source_paths = [s[0] for s in sources]
        assert "app/backend/requirements.txt" in source_paths
        assert "app/backend/" in source_paths
        assert "app/backend/alembic.ini" in source_paths

    def test_parse_dockerfile_frontend_sources(self):
        """parse_dockerfile_copy_sources extracts COPY sources from Dockerfile.frontend."""
        dockerfile = PROJECT_ROOT / "Dockerfile.frontend"
        sources = parse_dockerfile_copy_sources(dockerfile)
        source_paths = [s[0] for s in sources]
        assert "app/frontend/package.json" in source_paths
        assert "app/frontend/" in source_paths
        assert "docs/canonical/agent_authority_registry.json" in source_paths

    def test_parse_skips_multistage_copy(self):
        """parse_dockerfile_copy_sources skips COPY --from=... instructions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dockerfile", delete=False) as f:
            f.write("FROM node:18 AS builder\n")
            f.write("COPY package.json /app/\n")
            f.write("FROM nginx:alpine\n")
            f.write("COPY --from=builder /app/dist /usr/share/nginx/html\n")
            f.flush()
            sources = parse_dockerfile_copy_sources(Path(f.name))
            source_paths = [s[0] for s in sources]
            assert "package.json" in source_paths
            # --from= should be skipped
            assert "/app/dist" not in source_paths
        Path(f.name).unlink()

    def test_parse_skips_variable_expansions(self):
        """parse_dockerfile_copy_sources skips sources with $ variables."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dockerfile", delete=False) as f:
            f.write("FROM python:3.11\n")
            f.write("COPY ${APP_DIR}/config.py /app/\n")
            f.write("COPY requirements.txt /app/\n")
            f.flush()
            sources = parse_dockerfile_copy_sources(Path(f.name))
            source_paths = [s[0] for s in sources]
            assert "requirements.txt" in source_paths
            assert "${APP_DIR}/config.py" not in source_paths
        Path(f.name).unlink()

    def test_verify_dockerfile_copy_sources_passes(self):
        """All Dockerfile COPY sources must exist in the project root."""
        errors = verify_dockerfile_copy_sources(PROJECT_ROOT)
        assert errors == [], f"Dockerfile COPY source errors: {errors}"

    def test_alembic_ini_exists_at_correct_path(self):
        """alembic.ini must exist at app/backend/alembic.ini (Dockerfile.backend references it)."""
        alembic_path = PROJECT_ROOT / "app" / "backend" / "alembic.ini"
        assert alembic_path.exists(), f"alembic.ini not found at {alembic_path}"

    def test_dockerfile_backend_references_correct_alembic_path(self):
        """Dockerfile.backend must COPY alembic.ini from app/backend/alembic.ini."""
        dockerfile = PROJECT_ROOT / "Dockerfile.backend"
        content = dockerfile.read_text()
        assert "app/backend/alembic.ini" in content, (
            "Dockerfile.backend must reference app/backend/alembic.ini"
        )

    def test_dockerfile_backend_no_root_alembic_reference(self):
        """Dockerfile.backend must NOT reference bare 'alembic.ini' (root-level)."""
        dockerfile = PROJECT_ROOT / "Dockerfile.backend"
        content = dockerfile.read_text()
        # Should not have "COPY alembic.ini" without a path prefix
        import re
        bare_copy = re.search(r"^COPY\s+alembic\.ini\s", content, re.MULTILINE)
        assert bare_copy is None, (
            "Dockerfile.backend must not COPY bare 'alembic.ini' — use 'app/backend/alembic.ini'"
        )

    def test_package_contains_all_dockerfile_copy_sources(self):
        """Created package must contain every COPY/ADD source from both Dockerfiles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert result is not None
            with zipfile.ZipFile(result, "r") as zf:
                names = zf.namelist()

                # Verify backend Dockerfile sources
                backend_sources = ["app/backend/requirements.txt", "app/backend/", "app/backend/alembic.ini"]
                for src in backend_sources:
                    src_clean = src.rstrip("/")
                    found = any(n == src_clean or n.startswith(src_clean + "/") for n in names)
                    assert found, f"Dockerfile.backend COPY source '{src}' not in package"

                # Verify frontend Dockerfile sources
                frontend_sources = ["app/frontend/package.json", "app/frontend/", "docs/canonical/agent_authority_registry.json"]
                for src in frontend_sources:
                    src_clean = src.rstrip("/")
                    found = any(n == src_clean or n.startswith(src_clean + "/") for n in names)
                    assert found, f"Dockerfile.frontend COPY source '{src}' not in package"

    def test_verify_check14_dockerfile_sources_in_package(self):
        """verify_package Check 14 must pass on a freshly created package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert result is not None
            # Verify passes (includes Check 14)
            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is True

    def test_verify_catches_missing_copy_source(self):
        """verify_package Check 14 must fail if a COPY source is missing from package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "workos-staging-release-BUILD_25.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                # Include Dockerfile.backend that references a path NOT in the archive
                zf.writestr("Dockerfile.backend", "FROM python:3.11\nCOPY missing/path/file.txt /app/\n")
                zf.writestr("Dockerfile.frontend", "FROM node:18\nCOPY app/frontend/ /app/\n")
                # Minimal other files to pass other checks
                for i in range(15):
                    zf.writestr(f"app/backend/tests/test_{i}.py", f"# test {i}")
                    zf.writestr(f"app/backend/src/mod_{i}.py", f"# mod {i}")
                for i in range(15):
                    zf.writestr(f"app/frontend/src/comp_{i}.tsx", f"// comp {i}")
                zf.writestr("app/backend/core/auth.py",
                    "def _optional_oidc_value(): pass\n"
                    "def _resolve_authorization_endpoint(): pass\n"
                    "def _resolve_token_endpoint(): pass\n"
                )
                zf.writestr("app/backend/alembic/versions/s31_merge_heads.py", "# migration")
                zf.writestr("docs/deployment/deploy.md", "# deploy")
                zf.writestr("docs/canonical/agent_authority_registry.json", "{}")
                zf.writestr("docs/qa/QA1.md", "# qa1")
                zf.writestr("docs/qa/QA2.md", "# qa2")
                zf.writestr("docs/qa/QA3.md", "# qa3")
                zf.writestr("RELEASE_MANIFEST.md", "# manifest")
                zf.writestr("docker-compose.yml", "# compose")
                zf.writestr("Caddyfile", "# caddy")
                zf.writestr("Caddyfile.frontend", "# caddy frontend")
                # Note: app/frontend/ exists but missing/path/file.txt does NOT

            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            # Should fail because "missing/path/file.txt" is not in the archive
            assert success is False

    def test_dockerfile_frontend_copy_destination_not_app_docs(self):
        """Dockerfile.frontend must COPY agent_authority_registry.json to /docs/canonical/, NOT /app/docs/canonical/."""
        dockerfile_path = PROJECT_ROOT / "Dockerfile.frontend"
        content = dockerfile_path.read_text()
        # Must NOT have the old incorrect path
        assert "/app/docs/canonical" not in content, (
            "Dockerfile.frontend still references /app/docs/canonical — "
            "frontend import resolves to /docs/canonical/ inside Docker builder"
        )
        # Must have the correct mkdir + COPY
        assert "mkdir -p /docs/canonical" in content, (
            "Dockerfile.frontend missing 'mkdir -p /docs/canonical'"
        )
        assert "COPY docs/canonical/agent_authority_registry.json /docs/canonical/agent_authority_registry.json" in content, (
            "Dockerfile.frontend missing correct COPY to /docs/canonical/"
        )

    def test_package_dockerfile_frontend_has_correct_path(self):
        """Release package Dockerfile.frontend must have /docs/canonical/ destination (not /app/docs/canonical/)."""
        zip_path = PROJECT_ROOT / "dist" / "releases" / "workos-staging-release-BUILD_25.zip"
        if not zip_path.exists():
            pytest.skip("Release package not found")
        with zipfile.ZipFile(zip_path, "r") as zf:
            content = zf.read("Dockerfile.frontend").decode()
            assert "/app/docs/canonical" not in content, (
                "Package Dockerfile.frontend still has old /app/docs/canonical path"
            )
            assert "mkdir -p /docs/canonical" in content
            assert "COPY docs/canonical/agent_authority_registry.json /docs/canonical/agent_authority_registry.json" in content
