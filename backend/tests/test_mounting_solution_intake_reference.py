"""PRODUCT_SYSTEM_MOUNTING_SOLUTION_INTAKE_REFERENCE_V1 — targeted tests."""

from __future__ import annotations

import pytest

from schemas.intake_v4 import IntakeV4FinishSetup, IntakeV4MountingSolution
from services.intake_v4_finish_truth_service import normalize_intake_v4_finish_setup
from services.mounting_solution_service import (
    METAL_PREMOUNT_TEMPLATE_CODE,
    hydrate_mounting_solution_from_legacy,
    is_mounting_solution_composition_active,
    is_structura_suport_active,
    read_mounting_solution,
)
from services.product_definition_builder_service import (
    BAR_MOUNTING,
    _derive_metal_support_required,
    _resolve_module_state,
)
from services.execution_sold_scope_reader_service import effective_runtime_module_for_task_rule
from schemas.product_aggregate import ProductAggregateTaskRule


def _metal_solution_setup(**overrides):
    base = {
        "mounting_scope": "preparation_only",
        "mounting_solution": {
            "template_code": METAL_PREMOUNT_TEMPLATE_CODE,
            "configuration": {
                "bar_material": "steel",
                "mounting_bar_profile": "30x30x1.5",
                "bar_count": 2,
            },
        },
        "confirmed": True,
        "letter_group_finishes": [
            {
                "group_key": "a",
                "layer_name": "A",
                "face_finish_type": "oracal_651",
                "return_finish_type": "white_aluminum",
                "return_depth_mm": 60,
            }
        ],
    }
    base.update(overrides)
    return IntakeV4FinishSetup.model_validate(base)


def test_mounting_scope_none_excludes_composition_active() -> None:
    setup = _metal_solution_setup(mounting_scope="none")
    assert is_mounting_solution_composition_active(setup.model_dump(mode="json")) is False


def test_preparation_only_with_metal_solution_is_active() -> None:
    setup = _metal_solution_setup()
    assert is_mounting_solution_composition_active(setup.model_dump(mode="json")) is True
    assert is_structura_suport_active(setup.model_dump(mode="json")) is True


def test_preparation_and_site_installation_keeps_solution_active() -> None:
    setup = _metal_solution_setup(
        mounting_scope="preparation_and_site_installation",
        site_installation_included=True,
    )
    payload = setup.model_dump(mode="json")
    assert is_mounting_solution_composition_active(payload) is True
    assert payload["site_installation_included"] is True


def test_canonical_reference_persists_and_strips_legacy_on_normalize() -> None:
    setup = _metal_solution_setup(
        mounting_system="steel_bars",
        mounting_bar_profile="30x30x1.5",
    )
    normalized = normalize_intake_v4_finish_setup(setup)
    assert normalized.mounting_solution is not None
    assert normalized.mounting_solution.template_code == METAL_PREMOUNT_TEMPLATE_CODE
    assert normalized.mounting_system is None
    assert normalized.mounting_bar_profile is None


def test_legacy_mounting_system_hydrates_canonical_reference() -> None:
    hydrated = hydrate_mounting_solution_from_legacy(
        {
            "mounting_system": "aluminum_bars",
            "mounting_bar_profile": "30x30x1.5",
        }
    )
    assert hydrated is not None
    assert hydrated["template_code"] == METAL_PREMOUNT_TEMPLATE_CODE
    assert hydrated["configuration"]["bar_material"] == "aluminum"


def test_normalize_hydrates_legacy_when_prep_scope_without_canonical() -> None:
    setup = IntakeV4FinishSetup.model_validate(
        {
            "mounting_scope": "preparation_only",
            "mounting_system": "steel_bars",
            "mounting_bar_profile": "30x30x1.5",
            "confirmed": True,
            "letter_group_finishes": [
                {
                    "group_key": "a",
                    "layer_name": "A",
                    "face_finish_type": "oracal_651",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                }
            ],
        }
    )
    normalized = normalize_intake_v4_finish_setup(setup)
    assert normalized.mounting_solution is not None
    assert normalized.mounting_solution.template_code == METAL_PREMOUNT_TEMPLATE_CODE
    assert normalized.mounting_system is None


def test_derive_metal_support_required_from_solution() -> None:
    finish = _metal_solution_setup().model_dump(mode="json")
    assert _derive_metal_support_required(None, finish) is True


def test_structura_module_state_active_from_solution() -> None:
    from schemas.intake_v6_modular_form import IntakeModuleFormSection

    module = IntakeModuleFormSection(
        module_code="structura_suport",
        module_name="Structura suport",
        label="Structura suport",
        activation_kind="optional_addon",
        operational_status="ACTIVE_OPERATIONAL",
        required_form_fields=[],
        optional_form_fields=[],
        field_bindings=[],
    )
    finish = _metal_solution_setup().model_dump(mode="json")
    state = _resolve_module_state(
        module,
        finish=finish,
        quote_geometry={"width_mm": 1000},
        svg_source={"file_name": "test.svg"},
        analysis_ready=True,
    )
    assert state == "active"


def test_scope_none_preserves_historical_solution_object() -> None:
    setup = _metal_solution_setup(mounting_scope="none")
    normalized = normalize_intake_v4_finish_setup(setup)
    assert normalized.mounting_solution is not None
    assert is_mounting_solution_composition_active(normalized.model_dump(mode="json")) is False


def test_sablon_task_maps_to_finisaje_runtime_module() -> None:
    rule = ProductAggregateTaskRule(
        task_name="mounting_template",
        priced_operation="mounting_template_cnc_cut",
        mini_module_code="sablon_montaj",
        task_type="cnc_routing",
        sequence=10,
    )
    assert effective_runtime_module_for_task_rule(rule) == "finisaje"


def test_acm_not_available_in_allowed_templates() -> None:
    from services.mounting_solution_service import ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES

    assert "TPL-ACM-CASSETTED-PANEL" not in ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES


def test_no_dual_write_after_canonical_normalize() -> None:
    setup = _metal_solution_setup()
    once = normalize_intake_v4_finish_setup(setup)
    twice = normalize_intake_v4_finish_setup(once)
    assert twice.mounting_solution == once.mounting_solution
    assert twice.mounting_system is None
    assert twice.mounting_bar_profile is None


@pytest.fixture(scope="module")
def mounting_solution_seeded_db(db_fixture):
    import asyncio

    from seeds.seed_build4_templates import seed_build4_templates
    from seeds.seed_tpl_volumetric_letters_dossier import seed_tpl_volumetric_letters_dossier
    from seeds.seed_tpl_volumetric_letters_v2 import seed_tpl_volumetric_letters_v2

    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    asyncio.get_event_loop().run_until_complete(seed_tpl_volumetric_letters_dossier())
    asyncio.get_event_loop().run_until_complete(seed_tpl_volumetric_letters_v2())
    return db_fixture


@pytest.fixture
def mounting_solution_v4_client(mounting_solution_seeded_db):
    from core.database import get_db
    from dependencies.auth import get_current_user
    from fastapi.testclient import TestClient
    from main import app
    from schemas.auth import UserResponse

    async def _override_get_db():
        async with mounting_solution_seeded_db.session_maker() as session:
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
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


def test_api_save_finish_setup_persists_mounting_solution(mounting_solution_v4_client) -> None:
    from tests.test_finish_target_runtime_capture import _create_workspace, _put_analysis_bundle

    client = mounting_solution_v4_client
    workspace_id = _create_workspace(client)
    _put_analysis_bundle(client, workspace_id)

    saved = client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "mounting_scope": "preparation_only",
            "mounting_solution": {
                "template_code": METAL_PREMOUNT_TEMPLATE_CODE,
                "configuration": {
                    "bar_material": "steel",
                    "mounting_bar_profile": "30x30x1.5",
                    "bar_count": 2,
                },
            },
            "confirmed": True,
        },
    )
    assert saved.status_code == 200, saved.text
    finish = saved.json()["payload"]["finish_setup"]
    assert finish["mounting_solution"]["template_code"] == METAL_PREMOUNT_TEMPLATE_CODE
    assert finish["mounting_system"] is None

    reloaded = client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}")
    assert reloaded.status_code == 200
    reloaded_finish = reloaded.json()["payload"]["finish_setup"]
    assert reloaded_finish["mounting_solution"]["template_code"] == METAL_PREMOUNT_TEMPLATE_CODE
