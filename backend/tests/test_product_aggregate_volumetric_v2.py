"""Tests for read-only ProductAggregate service and GET endpoint (volumetric v2)."""

from __future__ import annotations

import json

import pytest
import pytest_asyncio

from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from services.product_aggregate_service import ProductAggregateService

TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"
CHILD_ALUMINUM = "TPL-VOLUM-ALUMINIU_v1"
CHILD_PREMOUNT = "TPL-METAL-PREMOUNT-STRUCTURE_v1"

DOSSIER_COMPONENTS = [
    {"id": "comp_face_litere", "label": "VIZUAL FAȚĂ", "role": "față plexi/acrilic"},
    {"id": "comp_lateral_litere", "label": "VOLUM ALUMINIU", "role": "profil lateral"},
    {"id": "comp_spate_litere", "label": "CAPAC SPATE", "role": "spate Forex"},
    {"id": "comp_led_litere", "label": "SISTEM LED", "role": "LED"},
    {"id": "comp_finisaj_litere", "label": "FINISAJ", "role": "finisaj"},
]

COSTENGINE_MAPPING = {
    "inputs": {
        "required": [
            "width_mm",
            "height_mm",
            "depth_mm",
            "letter_count",
            "letter_face_area_m2",
            "letter_perimeter_m",
            "return_depth_mm",
            "mounting_template_enabled",
            "mounting_template_area_m2",
        ],
        "optional": ["selected_psu_watts"],
    },
    "material_keys": [
        "MAT-SABLON-MONTAJ",
        "MAT-SABLON-HARTIE",
        "MAT-LED-MODULE",
        "MAT-LED-PSU-12V",
    ],
    "operation_keys": [
        "face_cnc_cut",
        "back_cut",
        "side_forming",
        "led_install_letters",
        "electrical_letters",
        "mounting_template_cnc_cut",
    ],
}

TASK_RULES = {
    "rules": [
        {"task_name": "cnc_face_cut", "task_type": "cnc_routing", "priced_operation": "face_cnc_cut", "sequence": 2},
        {"task_name": "electrical_wiring", "task_type": "led_wiring", "priced_operation": "electrical_letters", "sequence": 9},
    ]
}


async def _seed_volumetric_v2_fixture(session) -> None:
    """Inline fixture — no seed_sync_all, no global destructive seed."""
    from sqlalchemy import select

    existing = await session.execute(
        select(Product_templates).where(Product_templates.template_code == TEMPLATE_CODE).limit(1)
    )
    if existing.scalar_one_or_none() is not None:
        return

    parent = Product_templates(
        template_code=TEMPLATE_CODE,
        family_id="litere_volumetrice",
        family_name="Litere volumetrice luminoase",
        description="Parent volumetric v2 test fixture",
        components_json=json.dumps([]),
        operations_json=json.dumps(
            [
                {
                    "code": "svg_geometry_analysis",
                    "workcenter": "PREPRESS",
                    "sequence": 0,
                    "formula_id": "svg_geometry_readiness_gate",
                    "formula_params": {"non_priced": True},
                }
            ]
        ),
        required_materials_json=json.dumps(
            [
                {"material_code": "MAT-SABLON-MONTAJ", "unit": "mp", "formula_id": "mounting_template_area"},
                {"material_code": "MAT-SABLON-HARTIE", "unit": "mp", "formula_id": "mounting_template_area"},
            ]
        ),
        active=True,
    )
    child_al = Product_templates(
        template_code=CHILD_ALUMINUM,
        family_id="volum_aluminiu_modular",
        family_name="Volum aluminiu modular",
        components_json=json.dumps([{"component_id": "comp_volum_aluminiu_module"}]),
        operations_json=json.dumps([{"code": "RETURN_PROFILE_MACHINE_FORMING", "workcenter": "WC_METAL"}]),
        required_materials_json=json.dumps([{"material_code": "MAT-PROFIL-LATERAL-LITERE-60MM"}]),
        active=True,
    )
    child_pm = Product_templates(
        template_code=CHILD_PREMOUNT,
        family_id="structuri_metalice_premontaj",
        family_name="Structuri metalice premontaj",
        components_json=json.dumps([{"component_id": "comp_premount_bars"}]),
        operations_json=json.dumps([{"code": "premount_bar_preparation", "workcenter": "WC_METAL_FAB"}]),
        required_materials_json=json.dumps([{"material_code": "MAT-PREMOUNT-BAR-STEEL"}]),
        active=True,
    )
    session.add_all([parent, child_al, child_pm])
    await session.flush()

    dossier = ProductBlueprintDossier(
        template_id=parent.id,
        template_code=TEMPLATE_CODE,
        dossier_version=3,
        status="approved",
        sections_json=json.dumps({"template_identity": {"family_name": "Litere volumetrice luminoase"}, "components": DOSSIER_COMPONENTS}),
        costengine_mapping_json=json.dumps(COSTENGINE_MAPPING),
        task_rules_json=json.dumps(TASK_RULES),
    )
    link_required = ProductTemplateModuleLink(
        parent_template_id=parent.id,
        parent_template_code=TEMPLATE_CODE,
        module_template_id=child_al.id,
        module_template_code=CHILD_ALUMINUM,
        relation_type="required_module",
        trigger_field="volum_aluminum_module_template_code",
        trigger_value_json='["TPL-VOLUM-ALUMINIU_v1"]',
        input_mapping_json="{}",
        pricing_mode="separate_quote_line",
        execution_mode="linked_child_work",
        active=True,
    )
    link_optional = ProductTemplateModuleLink(
        parent_template_id=parent.id,
        parent_template_code=TEMPLATE_CODE,
        module_template_id=child_pm.id,
        module_template_code=CHILD_PREMOUNT,
        relation_type="optional_addon",
        trigger_field="metal_support_required",
        trigger_value_json="true",
        input_mapping_json="{}",
        pricing_mode="separate_quote_line",
        execution_mode="linked_child_work",
        active=True,
    )
    session.add_all([dossier, link_required, link_optional])
    await session.commit()


@pytest_asyncio.fixture
async def volumetric_v2_db(db_session):
    await _seed_volumetric_v2_fixture(db_session)
    return db_session


@pytest.mark.asyncio
async def test_aggregate_exists_for_volumetric_v2(volumetric_v2_db):
    service = ProductAggregateService(volumetric_v2_db)
    aggregate = await service.build(TEMPLATE_CODE)
    assert aggregate is not None
    assert aggregate.template_code == TEMPLATE_CODE


@pytest.mark.asyncio
async def test_parent_direct_components_zero_in_provenance(volumetric_v2_db):
    service = ProductAggregateService(volumetric_v2_db)
    aggregate = await service.build(TEMPLATE_CODE)
    assert aggregate.provenance_summary.parent["components"] == 0


@pytest.mark.asyncio
async def test_aggregate_does_not_produce_comp_auto_1(volumetric_v2_db):
    service = ProductAggregateService(volumetric_v2_db)
    aggregate = await service.build(TEMPLATE_CODE)
    component_ids = {c.component_id for c in aggregate.components}
    assert "comp_auto_1" not in component_ids
    raw = aggregate.model_dump_json()
    assert "comp_auto_1" not in raw


@pytest.mark.asyncio
async def test_aggregate_includes_dossier_components(volumetric_v2_db):
    service = ProductAggregateService(volumetric_v2_db)
    aggregate = await service.build(TEMPLATE_CODE)
    ids = {c.component_id for c in aggregate.components}
    assert "comp_face_litere" in ids
    assert "comp_lateral_litere" in ids
    assert "comp_spate_litere" in ids
    assert "comp_led_litere" in ids
    assert "comp_finisaj_litere" in ids


@pytest.mark.asyncio
async def test_aggregate_includes_required_linked_module(volumetric_v2_db):
    service = ProductAggregateService(volumetric_v2_db)
    aggregate = await service.build(TEMPLATE_CODE)
    required_codes = {m.child_template_code for m in aggregate.modules.required}
    assert CHILD_ALUMINUM in required_codes


@pytest.mark.asyncio
async def test_aggregate_includes_optional_linked_module(volumetric_v2_db):
    service = ProductAggregateService(volumetric_v2_db)
    aggregate = await service.build(TEMPLATE_CODE)
    optional_codes = {m.child_template_code for m in aggregate.modules.optional}
    assert CHILD_PREMOUNT in optional_codes


@pytest.mark.asyncio
async def test_aggregate_includes_parent_components_empty_warning(volumetric_v2_db):
    service = ProductAggregateService(volumetric_v2_db)
    aggregate = await service.build(TEMPLATE_CODE)
    codes = {w.code for w in aggregate.warnings}
    assert "PARENT_COMPONENTS_EMPTY" in codes


@pytest.mark.asyncio
async def test_aggregate_includes_trigger_field_mismatch_warning(volumetric_v2_db):
    service = ProductAggregateService(volumetric_v2_db)
    aggregate = await service.build(TEMPLATE_CODE)
    codes = {w.code for w in aggregate.warnings}
    assert "TRIGGER_FIELD_MISMATCH" in codes


@pytest.mark.asyncio
async def test_build_returns_none_for_invalid_template(volumetric_v2_db):
    service = ProductAggregateService(volumetric_v2_db)
    assert await service.build("TPL-DOES-NOT-EXIST") is None



@pytest.fixture
def volumetric_auth_client(db_fixture):
    """Auth client with volumetric v2 seeded in isolated DB."""
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse

    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)

    db_fixture.run(_seed())

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


def test_get_endpoint_returns_200(volumetric_auth_client):
    response = volumetric_auth_client.get(f"/api/v1/product-system/aggregate/{TEMPLATE_CODE}")
    assert response.status_code == 200
    body = response.json()
    assert body["template_code"] == TEMPLATE_CODE
    assert len(body["components"]) == 5
    assert any(w["code"] == "PARENT_COMPONENTS_EMPTY" for w in body.get("warnings", []))


def test_get_endpoint_returns_404(volumetric_auth_client):
    response = volumetric_auth_client.get("/api/v1/product-system/aggregate/TPL-INVALID-CODE-XYZ")
    assert response.status_code == 404
