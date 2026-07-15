"""Import isolation gate — parity foundation and observe adapter boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

OPERATIONAL_BACKEND_PATHS = [
    BACKEND_ROOT / "services" / "operator_task_truth_service.py",
    BACKEND_ROOT / "services" / "execution_task_assignment_service.py",
    BACKEND_ROOT / "services" / "execution_reality_service.py",
    BACKEND_ROOT / "services" / "employee_attendance_service.py",
    BACKEND_ROOT / "routers" / "operator_tasks.py",
    BACKEND_ROOT / "routers" / "employee_mobile_tasks.py",
    BACKEND_ROOT / "routers" / "execution.py",
    BACKEND_ROOT / "main.py",
]

ALLOWED_PARITY_OBSERVE_IMPORTS = {
    BACKEND_ROOT / "services" / "employee_mobile_tasks_service.py",
    BACKEND_ROOT / "routers" / "operational_registry.py",
}

FRONTEND_OPERATIONAL_PATHS = [
    REPO_ROOT / "frontend" / "src" / "hooks" / "useShopFloorData.ts",
    REPO_ROOT / "frontend" / "src" / "pages" / "TabletView.tsx",
    REPO_ROOT / "frontend" / "src" / "pages" / "OperatorView.tsx",
    REPO_ROOT / "frontend" / "src" / "services" / "employee_mobile_tasks_service.py",
]


def _imports_in_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.add(module)
            for alias in node.names:
                imports.add(f"{module}.{alias.name}" if module else alias.name)
    return imports


def _parity_related_imports(path: Path) -> list[str]:
    imports = _imports_in_file(path)
    return [
        item
        for item in imports
        if item == "parity" or item.startswith("parity.") or item.startswith("services.parity_observe")
    ]


@pytest.mark.parametrize("path", OPERATIONAL_BACKEND_PATHS)
def test_operational_backend_files_do_not_import_parity(path: Path):
    assert path.is_file(), f"missing operational file: {path}"
    parity_imports = _parity_related_imports(path)
    assert parity_imports == [], f"{path.name} imports parity: {parity_imports}"


@pytest.mark.parametrize("path", sorted(ALLOWED_PARITY_OBSERVE_IMPORTS))
def test_allowed_consumers_may_import_parity_observe(path: Path):
    assert path.is_file()
    imports = _imports_in_file(path)
    assert any("parity_observe" in item for item in imports), f"{path.name} should import parity_observe adapter"


@pytest.mark.parametrize(
    "path",
    [p for p in FRONTEND_OPERATIONAL_PATHS if p.is_file()],
)
def test_frontend_operational_files_do_not_reference_parity(path: Path):
    text = path.read_text(encoding="utf-8")
    assert "parity" not in text.lower()


def test_no_parity_router_registered():
    routers_dir = BACKEND_ROOT / "routers"
    for path in routers_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "operational-parity" not in text
        assert "parity_router" not in text


def test_core_settings_do_not_define_parity_flags():
    config_text = (BACKEND_ROOT / "core" / "config.py").read_text(encoding="utf-8")
    assert "parity_observe_enabled" not in config_text
    assert "parity_persistence_enabled" not in config_text


def test_parity_package_does_not_import_operational_services():
    parity_root = BACKEND_ROOT / "parity"
    forbidden_prefixes = ("services.", "routers.", "models.")
    for path in parity_root.rglob("*.py"):
        for item in _imports_in_file(path):
            if item.startswith(forbidden_prefixes):
                pytest.fail(f"{path.relative_to(BACKEND_ROOT)} imports operational module {item}")
