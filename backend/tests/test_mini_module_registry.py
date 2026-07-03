"""Tests for read-only Mini-module Contract Registry (Step 4)."""

from __future__ import annotations

import pytest

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

from data.mini_module_registry_volumetric_v2 import (
    CHILD_TEMPLATE_TO_MODULE,
    DOSSIER_COMPONENT_TO_MODULE,
    REGISTRY_BY_CODE,
)
from services.mini_module_registry_service import MiniModuleRegistryService

TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"
CHILD_ALUMINUM = "TPL-VOLUM-ALUMINIU_v1"
CHILD_PREMOUNT = "TPL-METAL-PREMOUNT-STRUCTURE_v1"


@pytest.fixture
def registry_service() -> MiniModuleRegistryService:
    return MiniModuleRegistryService()


def test_registry_returns_modelare_cant(registry_service: MiniModuleRegistryService):
    module = registry_service.get_by_code("modelare_cant")
    assert module is not None
    assert module.child_template_code == CHILD_ALUMINUM


def test_modelare_cant_active_operational(registry_service: MiniModuleRegistryService):
    module = registry_service.get_by_code("modelare_cant")
    assert module is not None
    assert module.operational_status == "ACTIVE_OPERATIONAL"


def test_modelare_cant_declares_produced_component_roles(registry_service: MiniModuleRegistryService):
    module = registry_service.get_by_code("modelare_cant")
    assert module is not None
    assert "side_wall" in module.produced_component_roles or "return_profile" in module.produced_component_roles


def test_modelare_cant_declares_cost_engine_inputs(registry_service: MiniModuleRegistryService):
    module = registry_service.get_by_code("modelare_cant")
    assert module is not None
    assert len(module.cost_engine_inputs) > 0
    assert "return_profile_machine_forming" in module.cost_engine_inputs


def test_modelare_cant_declares_task_preview_outputs(registry_service: MiniModuleRegistryService):
    module = registry_service.get_by_code("modelare_cant")
    assert module is not None
    assert len(module.task_preview_outputs) > 0


def test_structura_suport_optional_activation(registry_service: MiniModuleRegistryService):
    module = registry_service.get_by_code("structura_suport")
    assert module is not None
    assert module.child_template_code == CHILD_PREMOUNT
    assert module.operational_status == "ACTIVE_OPERATIONAL"
    assert any(r.rule_type == "optional_addon" for r in module.activation_rules)
    assert any(c.code == "TRIGGER_FIELD_MISMATCH" for c in module.conflicts)


def test_by_template_returns_linked_modules(registry_service: MiniModuleRegistryService):
    response = registry_service.get_by_template(TEMPLATE_CODE)
    codes = {m.module_code for m in response.modules}
    assert "modelare_cant" in codes
    assert "structura_suport" in codes
    assert response.summary.active_operational_count >= 2


def test_no_active_module_missing_operational_destination(registry_service: MiniModuleRegistryService):
    errors = registry_service.validate_operational_destinations()
    assert errors == []


def test_no_dead_piece_without_warning(registry_service: MiniModuleRegistryService):
    for module in REGISTRY_BY_CODE.values():
        if module.operational_status == "DEAD_PIECE_REMOVE_OR_APPROVE":
            pytest.fail(f"{module.module_code} is DEAD_PIECE — requires explicit approval")


def test_child_template_index_aligns_with_aggregate_map():
    assert CHILD_TEMPLATE_TO_MODULE[CHILD_ALUMINUM] == "modelare_cant"
    assert CHILD_TEMPLATE_TO_MODULE[CHILD_PREMOUNT] == "structura_suport"


def test_dossier_component_index_covers_five_components():
    assert len(DOSSIER_COMPONENT_TO_MODULE) == 5
    assert DOSSIER_COMPONENT_TO_MODULE["comp_face_litere"] == "debitare_fata"


def test_future_reserved_electrica_logo(registry_service: MiniModuleRegistryService):
    module = registry_service.get_by_code("electrica_logo")
    assert module is not None
    assert module.operational_status == "FUTURE_RESERVED_STEP_6"
    assert len(module.warnings) > 0


@pytest.fixture
def registry_auth_client(db_fixture):
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    from fastapi.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()


def test_list_endpoint_returns_200(registry_auth_client):
    response = registry_auth_client.get("/api/v1/product-system/mini-modules")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total_modules"] >= 7
    codes = {m["module_code"] for m in body["modules"]}
    assert "modelare_cant" in codes


def test_get_by_code_endpoint(registry_auth_client):
    response = registry_auth_client.get("/api/v1/product-system/mini-modules/modelare_cant")
    assert response.status_code == 200
    assert response.json()["child_template_code"] == CHILD_ALUMINUM


def test_get_by_code_404(registry_auth_client):
    response = registry_auth_client.get("/api/v1/product-system/mini-modules/does-not-exist")
    assert response.status_code == 404


def test_by_template_endpoint(registry_auth_client):
    response = registry_auth_client.get(
        f"/api/v1/product-system/mini-modules/by-template/{TEMPLATE_CODE}"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["template_code"] == TEMPLATE_CODE
    required = [m for m in body["modules"] if m["module_code"] == "modelare_cant"]
    optional = [m for m in body["modules"] if m["module_code"] == "structura_suport"]
    assert len(required) == 1
    assert len(optional) == 1


@pytest.mark.asyncio
async def test_aggregate_includes_registry_refs(volumetric_v2_db):
    from services.product_aggregate_service import ProductAggregateService

    service = ProductAggregateService(volumetric_v2_db)
    aggregate = await service.build(TEMPLATE_CODE)
    assert aggregate is not None
    assert aggregate.mini_module_registry is not None
    refs = {r.module_code for r in aggregate.mini_module_registry.module_refs}
    assert "modelare_cant" in refs
    assert "structura_suport" in refs
