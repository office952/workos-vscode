"""
BUILD 26 — Canonical Release Export Package Builder Tests

Tests for scripts/create_release_package.py:
- Dry run execution
- Excluded patterns detection
- Manifest generation
- Forbidden file detection
- Secrets scanning
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from create_release_package import (
    EXCLUDE_EXTENSIONS,
    EXCLUDE_PATTERNS,
    check_for_secrets,
    collect_files,
    create_package,
    generate_manifest,
    get_project_root,
    should_exclude,
    verify_package,
)


class TestShouldExclude:
    """Test the exclusion logic."""

    def test_excludes_git_directory(self):
        assert should_exclude(".git/config") is True
        assert should_exclude("some/path/.git/objects") is True

    def test_excludes_node_modules(self):
        assert should_exclude("node_modules/package/index.js") is True
        assert should_exclude("app/frontend/node_modules/react/index.js") is True

    def test_excludes_pycache(self):
        assert should_exclude("__pycache__/module.cpython-311.pyc") is True
        assert should_exclude("app/backend/__pycache__/main.cpython-311.pyc") is True

    def test_excludes_venv(self):
        assert should_exclude(".venv/lib/python3.11/site-packages") is True

    def test_excludes_pytest_cache(self):
        assert should_exclude(".pytest_cache/v/cache") is True

    def test_excludes_db_files(self):
        assert should_exclude("data.db") is True
        assert should_exclude("local.sqlite") is True
        assert should_exclude("test.sqlite3") is True

    def test_excludes_pyc_files(self):
        assert should_exclude("module.pyc") is True
        assert should_exclude("app/backend/main.pyc") is True

    def test_excludes_env_runtime(self):
        assert should_exclude(".env") is True
        assert should_exclude("app/backend/.env") is True

    def test_excludes_env_local(self):
        assert should_exclude(".env.local") is True

    def test_excludes_dist_releases(self):
        assert should_exclude("dist/releases/some-file.zip") is True

    def test_excludes_frontend_dist(self):
        assert should_exclude("app/frontend/dist/index.html") is True

    def test_excludes_ds_store(self):
        assert should_exclude(".DS_Store") is True
        assert should_exclude("some/path/.DS_Store") is True

    def test_excludes_thumbs_db(self):
        assert should_exclude("Thumbs.db") is True

    def test_excludes_backup_zips(self):
        assert should_exclude("project.backup.zip") is True

    def test_excludes_tmp_files(self):
        assert should_exclude("temp.tmp") is True

    def test_excludes_log_files(self):
        assert should_exclude("server.log") is True

    def test_excludes_atoms_directory(self):
        assert should_exclude(".atoms/PROGRESS.md") is True

    def test_excludes_mgx_directory(self):
        assert should_exclude(".mgx/config.yaml") is True

    def test_includes_normal_python_file(self):
        assert should_exclude("app/backend/main.py") is False

    def test_includes_normal_typescript_file(self):
        assert should_exclude("app/frontend/src/App.tsx") is False

    def test_includes_docs(self):
        assert should_exclude("docs/deployment/README.md") is False

    def test_includes_alembic_versions(self):
        assert should_exclude("app/backend/alembic/versions/s31_merge.py") is False

    def test_includes_env_example(self):
        assert should_exclude("app/backend/.env.example") is True

    def test_includes_env_production(self):
        assert should_exclude("app/frontend/.env.production") is True


class TestSecretsDetection:
    """Test the secrets scanning logic."""

    def test_detects_aws_key(self):
        # Construct the key dynamically to avoid the scanner detecting this test file
        prefix = "AKIA"
        suffix = "IOSFODNN7REALKEY1"
        fake_key = prefix + suffix
        temp_path = None
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(f'AWS_KEY = "{fake_key}"\n')
            f.flush()
            temp_path = Path(f.name)
        assert temp_path is not None
        violations = check_for_secrets(temp_path)
        os.unlink(temp_path)
        assert len(violations) > 0

    def test_allows_placeholder_values(self):
        temp_path = None
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('DATABASE_URL = "postgresql+asyncpg://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:5432/<DB_NAME>"\n')
            f.flush()
            temp_path = Path(f.name)
        assert temp_path is not None
        violations = check_for_secrets(temp_path)
        os.unlink(temp_path)
        assert len(violations) == 0

    def test_no_secrets_in_normal_code(self):
        temp_path = None
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('def hello():\n    return "world"\n')
            f.flush()
            temp_path = Path(f.name)
        assert temp_path is not None
        violations = check_for_secrets(temp_path)
        os.unlink(temp_path)
        assert len(violations) == 0


class TestManifestGeneration:
    """Test the release manifest generation."""

    def test_manifest_contains_build_number(self):
        files = [(Path("/tmp/test.py"), "app/backend/test.py")]
        manifest = generate_manifest(25, files, Path("/tmp"))
        assert "BUILD_25" in manifest
        assert "25" in manifest

    def test_manifest_contains_staging_domains(self):
        files = [(Path("/tmp/test.py"), "app/backend/test.py")]
        manifest = generate_manifest(25, files, Path("/tmp"))
        assert "staging.workos.ro" in manifest
        assert "api-staging.workos.ro" in manifest

    def test_manifest_contains_alembic_head(self):
        files = [(Path("/tmp/test.py"), "app/backend/test.py")]
        manifest = generate_manifest(25, files, Path("/tmp"))
        assert "s33_rendered_output_snapshots" in manifest

    def test_manifest_contains_test_counts(self):
        files = [(Path("/tmp/test.py"), "app/backend/test.py")]
        manifest = generate_manifest(25, files, Path("/tmp"))
        assert "1564" in manifest
        assert "216" in manifest

    def test_manifest_contains_security_statement(self):
        files = [(Path("/tmp/test.py"), "app/backend/test.py")]
        manifest = generate_manifest(25, files, Path("/tmp"))
        assert "NO secrets" in manifest

    def test_manifest_contains_file_count(self):
        files = [
            (Path("/tmp/a.py"), "app/backend/a.py"),
            (Path("/tmp/b.py"), "app/backend/b.py"),
        ]
        manifest = generate_manifest(25, files, Path("/tmp"))
        assert "2" in manifest


class TestDryRun:
    """Test dry run mode."""

    def test_dry_run_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            result = create_package(
                build_number=99,
                output_dir=output_dir,
                project_root=PROJECT_ROOT,
                dry_run=True,
            )
            # Dry run returns the path but doesn't create the file
            assert result is not None
            assert not Path(output_dir, "workos-staging-release-BUILD_99.zip").exists()


class TestCreateAndVerify:
    """Test full create + verify cycle."""

    def test_create_and_verify_package(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create
            result = create_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
                dry_run=False,
            )
            assert result is not None
            assert result.exists()
            assert result.stat().st_size > 0

            # Verify
            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is True

    def test_verify_nonexistent_package_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            success = verify_package(
                build_number=999,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is False

    def test_package_contains_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
                dry_run=False,
            )
            assert result is not None
            with zipfile.ZipFile(result, "r") as zf:
                assert "RELEASE_MANIFEST.md" in zf.namelist()

    def test_package_excludes_forbidden(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
                dry_run=False,
            )
            assert result is not None
            with zipfile.ZipFile(result, "r") as zf:
                names = zf.namelist()
                for name in names:
                    assert "node_modules" not in name.split("/")
                    assert "__pycache__" not in name.split("/")
                    assert ".git" not in name.split("/")
                    assert ".venv" not in name.split("/")
                    assert not name.endswith(".pyc")
                    assert not name.endswith(".db")


class TestCollectFiles:
    """Test file collection logic."""

    @staticmethod
    def _norm(rel_path: str) -> str:
        return rel_path.replace("\\", "/")

    def test_collects_backend_files(self):
        files = collect_files(PROJECT_ROOT)
        backend_files = [self._norm(rel) for _, rel in files if self._norm(rel).startswith("app/backend/")]
        assert len(backend_files) > 0

    def test_collects_frontend_files(self):
        files = collect_files(PROJECT_ROOT)
        frontend_files = [self._norm(rel) for _, rel in files if self._norm(rel).startswith("app/frontend/")]
        assert len(frontend_files) > 0

    def test_collects_docs_files(self):
        files = collect_files(PROJECT_ROOT)
        docs_files = [self._norm(rel) for _, rel in files if self._norm(rel).startswith("docs/")]
        assert len(docs_files) > 0

    def test_no_excluded_files_collected(self):
        files = collect_files(PROJECT_ROOT)
        for _, rel in files:
            assert "node_modules" not in rel.split("/")
            assert "__pycache__" not in rel.split("/")
            assert ".git" not in rel.split("/")

    def test_collects_docs_canonical(self):
        """docs/canonical remains part of the release package."""
        files = collect_files(PROJECT_ROOT)
        canonical_files = [self._norm(rel) for _, rel in files if self._norm(rel).startswith("docs/canonical/")]
        assert len(canonical_files) > 0

    def test_collects_safe_env_files_via_explicit_allowlist(self):
        files = collect_files(PROJECT_ROOT)
        rel_paths = {self._norm(rel) for _, rel in files}
        assert "app/backend/.env.example" in rel_paths
        assert "app/frontend/.env.production" in rel_paths

    def test_collects_agent_authority_registry_json(self):
        """Canonical agent registry remains included for documentation parity."""
        files = collect_files(PROJECT_ROOT)
        registry_files = [
            self._norm(rel) for _, rel in files
            if self._norm(rel) == "docs/canonical/agent_authority_registry.json"
        ]
        assert len(registry_files) == 1


class TestFrontendBuildDependency:
    """Test that frontend build dependencies are included in the package."""

    def test_package_contains_agent_authority_registry(self):
        """Verify the zip archive includes frontend-local authority registry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
                dry_run=False,
            )
            assert result is not None
            with zipfile.ZipFile(result, "r") as zf:
                names = zf.namelist()
                assert "app/frontend/src/canonical/agent_authority_registry.json" in names

    def test_package_contains_all_canonical_docs(self):
        """Verify docs/canonical directory files are present in the package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
                dry_run=False,
            )
            assert result is not None
            with zipfile.ZipFile(result, "r") as zf:
                names = zf.namelist()
                canonical_files = [n for n in names if n.startswith("docs/canonical/")]
                assert len(canonical_files) >= 1
                # Frontend-local registry must also be present for self-contained builds
                assert "app/frontend/src/canonical/agent_authority_registry.json" in names

    def test_verify_catches_missing_frontend_dependency(self):
        """Verification should fail if agent_authority_registry.json is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal zip WITHOUT frontend local canonical registry
            artifact_path = Path(tmpdir) / "workos-staging-release-BUILD_25.zip"
            with zipfile.ZipFile(artifact_path, "w") as zf:
                zf.writestr("app/backend/main.py", "# backend")
                zf.writestr("app/frontend/src/App.tsx", "// frontend")
                zf.writestr("docs/deployment/README.md", "# deploy")
                zf.writestr("app/backend/alembic/versions/s33_create_rendered_output_snapshots.py", "# migration")
                zf.writestr("RELEASE_MANIFEST.md", "# manifest")
            # Verify should fail because app/frontend/src/canonical/agent_authority_registry.json is missing
            success = verify_package(
                build_number=25,
                output_dir=tmpdir,
                project_root=PROJECT_ROOT,
            )
            assert success is False