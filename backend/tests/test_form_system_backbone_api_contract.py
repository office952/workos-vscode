from __future__ import annotations

import json

import pytest

from services.form_system_contract_backbone_service import build_form_system_contract_map
from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
LEGACY_ROOT = "TPL-VOLUMETRIC-LETTERS"

FORBIDDEN_LEAKAGE_TOKENS = (
    "pricing_total",
    "final_price",
    "commercial_total",
    "execution_write",
    "execution_plan",
    "task_materialization",
    "stock_movement",
    "employee_assignment",
    "machine_capacity_blocking",
    "collaborator_routing",
)


@pytest.fixture
def form_auth_client(db_fixture):
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


def _assert_backbone_shape(backbone: dict):
    for key in ("root", "components", "fields", "readiness", "blockers", "downstream_write_intent"):
        assert key in backbone
    assert backbone["blockers"] == backbone["readiness"]["blockers"]
    assert isinstance(backbone["components"], list)
    assert isinstance(backbone["fields"], list)
    assert isinstance(backbone["blockers"], list)


def _assert_field_shape(field: dict):
    assert field["field_key"]
    assert field["owning_component"]
    assert field["source_type"]
    assert field["state"]
    assert field.get("product_truth_path") or field.get("missing_target_path")
    assert isinstance(field["required_for"], list)
    assert "blocker_code" in field


def _assert_no_downstream_leakage(backbone: dict):
    assert all(value is False for value in backbone["downstream_write_intent"].values())
    serialized = json.dumps(backbone, sort_keys=True).lower()
    for token in FORBIDDEN_LEAKAGE_TOKENS:
        assert token not in serialized
    assert "quote_write" in backbone["downstream_write_intent"]
    assert "order_write" in backbone["downstream_write_intent"]
    assert backbone["downstream_write_intent"]["quote_write"] is False
    assert backbone["downstream_write_intent"]["order_write"] is False


def test_get_endpoint_returns_backbone_for_letters_v2(form_auth_client):
    response = form_auth_client.get(f"/api/v1/intake-v6/form-contract/{ROOT}")

    assert response.status_code == 200
    body = response.json()
    backbone = body["form_system_backbone"]
    _assert_backbone_shape(backbone)
    assert body["summary"]["template_code"] == ROOT
    assert body["modules"]
    assert body["field_bindings"]
    assert backbone["root"]["canonical_code"] == ROOT
    assert backbone["root"]["root_type"] == "product_template"
    assert backbone["root"]["quote_mode"] == "product_total"
    assert backbone["root"]["allowed"] is True
    assert backbone["root"]["blocked"] is False


def test_get_endpoint_returns_linked_template_composition_for_letters_v2(form_auth_client):
    response = form_auth_client.get(f"/api/v1/intake-v6/form-contract/{ROOT}")

    assert response.status_code == 200
    backbone = response.json()["form_system_backbone"]
    composition = backbone["linked_template_composition"]
    linked_logo = composition["linked_templates"][0]

    assert composition["root_template_code"] == ROOT
    assert composition["root_role"] == "root_product"
    assert linked_logo["template_code"] == "TPL-VOLUMETRIC-LOGO_v1"
    assert linked_logo["composition_role"] == "linked_logo_segment"
    assert linked_logo["binding_status"] == "suggested"
    assert linked_logo["activation_state"] == "child_only_not_root_offerable"
    assert linked_logo["quote_policy"] == "no_separate_quote"
    assert linked_logo["root_offerability_policy"] == "blocked_as_root_in_this_flow"
    assert linked_logo["segment_discovery"]["status"] == "runtime_payload_required"
    assert composition["no_duplicate_task_policy"]["task_graph_implemented"] is False
    assert all(value is False for value in backbone["downstream_write_intent"].values())


def test_get_endpoint_legacy_letters_alias_returns_canonical_v2_backbone(form_auth_client):
    response = form_auth_client.get(f"/api/v1/intake-v6/form-contract/{LEGACY_ROOT}")

    assert response.status_code == 200
    body = response.json()
    backbone = body["form_system_backbone"]
    assert body["summary"]["template_code"] == ROOT
    assert backbone["root"]["requested_code"] == LEGACY_ROOT
    assert backbone["root"]["canonical_code"] == ROOT
    assert backbone["root"]["canonical_alias_resolution"] is True
    assert backbone["root"]["code"] == ROOT


def test_logo_endpoint_404_and_service_fail_closed_state_visible(form_auth_client):
    response = form_auth_client.get("/api/v1/intake-v6/form-contract/TPL-VOLUMETRIC-LOGO_v1")
    assert response.status_code == 404

    backbone = IntakeV6ModularFormContractService().get_backbone_section_for_template("TPL-VOLUMETRIC-LOGO_v1")
    assert backbone is not None
    assert backbone["root"]["allowed"] is False
    assert backbone["root"]["blocker_code"] == "LOGO_NOT_OFFERABLE"
    assert backbone["fields"] == []
    assert "linked_template_composition" not in backbone


def test_component_root_and_component_quote_remain_blocked():
    service = IntakeV6ModularFormContractService()
    component_root = service.get_backbone_section_for_template("TPL-VOLUMETRIC-FACE_v1")
    assert component_root is not None
    assert component_root["root"]["allowed"] is False
    assert component_root["root"]["blocker_code"] == "COMPONENT_ROOT_BLOCKED"
    assert service.get_for_template("TPL-VOLUMETRIC-FACE_v1") is None

    component_quote = build_form_system_contract_map(ROOT, quote_mode="component_only")
    assert component_quote["root"]["allowed"] is False
    assert component_quote["root"]["blocker_code"] == "QUOTE_MODE_BLOCKED"

    explicit_component_root = build_form_system_contract_map(
        "TPL-VOLUMETRIC-FACE_v1",
        root_type="component_template",
        quote_mode="component_only",
    )
    assert explicit_component_root["root"]["allowed"] is False
    assert explicit_component_root["root"]["blocker_code"] == "ROOT_TYPE_BLOCKED"


def test_payload_field_shape_source_state_truth_paths_and_blockers():
    contract = IntakeV6ModularFormContractService().get_for_template(ROOT)
    assert contract is not None
    backbone = contract.form_system_backbone
    _assert_backbone_shape(backbone)

    fields = {field["field_key"]: field for field in backbone["fields"]}
    for key in (
        "svg.layer_group_role",
        "svg.selected_layer_group",
        "face.material",
        "return.depth_mm",
        "lighting.type",
        "mounting.support_option",
    ):
        _assert_field_shape(fields[key])

    blocker_codes = {blocker["blocker_code"] for blocker in backbone["blockers"]}
    assert "LAYER_ROLES_INCOMPLETE" in blocker_codes
    assert "FACE_MATERIAL_MISSING" in blocker_codes
    assert "PRODUCT_TRUTH_INCOMPLETE" in blocker_codes


def test_source_state_safety_suggested_fallback_hydrated_are_not_confirmed():
    contract = IntakeV6ModularFormContractService().get_for_template(ROOT)
    fields = {field["field_key"]: field for field in contract.form_system_backbone["fields"]}

    assert fields["svg.layer_group_role"]["source_type"] == "svg_suggested"
    assert fields["svg.layer_group_role"]["state"] == "suggested"
    assert fields["svg.layer_group_role"]["state"] != "confirmed"

    assert fields["lighting.type"]["state"] == "fallback"
    assert fields["lighting.type"]["state"] != "confirmed"

    assert fields["return.depth_mm"]["state"] == "hydrated"
    assert fields["return.depth_mm"]["state"] != "confirmed"


def test_downstream_leakage_check_on_endpoint_payload(form_auth_client):
    response = form_auth_client.get(f"/api/v1/intake-v6/form-contract/{ROOT}")
    assert response.status_code == 200
    backbone = response.json()["form_system_backbone"]
    _assert_no_downstream_leakage(backbone)


def test_backward_compatible_existing_response_fields_remain_available(form_auth_client):
    response = form_auth_client.get(f"/api/v1/intake-v6/form-contract/{ROOT}")
    assert response.status_code == 200
    body = response.json()

    assert body["summary"]["active_module_count"] == 7
    assert len(body["field_bindings"]) >= 20
    assert {module["module_code"] for module in body["modules"]} >= {
        "geometry_svg",
        "debitare_fata",
        "modelare_cant",
        "debitare_spate",
        "sistem_led",
        "finisaje",
        "structura_suport",
    }
    assert body["trigger_alignments"]