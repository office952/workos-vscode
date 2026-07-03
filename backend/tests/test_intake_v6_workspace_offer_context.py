from __future__ import annotations

import json

import pytest
from fastapi import HTTPException
from sqlalchemy import delete, func, select, text

from models.intake_requests import Intake_requests
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from schemas.auth import UserResponse
from services.intake_v6_workspace_service import ensure_intake_v6_workspace_for_intake_request


LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"
VOLUM_ALUMINUM = "TPL-VOLUM-ALUMINIU_v1"


def _user() -> UserResponse:
    return UserResponse(id="test-user", email="test@example.com", name="Test User", role="admin", last_login=None)


async def _table_count(session, table_name: str) -> int:
    return int((await session.execute(text(f"select count(*) from {table_name}"))).scalar_one())


async def _seed_fixture(session) -> None:
    await session.execute(delete(IntakeV6WorkspaceRecord))
    await session.execute(delete(Intake_requests))
    await session.execute(delete(ProductTemplateModuleLink))
    await session.execute(delete(Product_templates))
    await session.commit()

    parent = Product_templates(
        template_code=LETTERS,
        family_id="litere_volumetrice",
        family_name="Litere volumetrice",
        description="Offerable fixture",
        components_json="[]",
        operations_json="[]",
        required_materials_json="[]",
        active=True,
    )
    child = Product_templates(
        template_code=VOLUM_ALUMINUM,
        family_id="litere_volumetrice",
        family_name="Litere volumetrice",
        description="Runtime module fixture",
        components_json="[]",
        operations_json="[]",
        required_materials_json="[]",
        active=True,
    )
    session.add_all([parent, child])
    await session.flush()
    session.add(
        ProductTemplateModuleLink(
            parent_template_id=parent.id,
            parent_template_code=LETTERS,
            module_template_id=child.id,
            module_template_code=VOLUM_ALUMINUM,
            relation_type="required_module",
            trigger_field="volum_aluminum_module_template_code",
            trigger_value_json=json.dumps([VOLUM_ALUMINUM]),
            input_mapping_json="{}",
            default_values_json="{}",
            pricing_mode="separate_quote_line",
            execution_mode="linked_child_work",
            active=True,
        )
    )
    session.add(
        Intake_requests(
            code="IR-AVAILABILITY-1",
            client_id=1,
            client_name="Client Test",
            contact_person="Operator",
            channel="email",
            product_family="litere_volumetrice",
            description="Litere volumetrice test",
            dimensions="—",
            quantity=1,
            status="new",
            assigned_to="—",
            notes="",
            priority="normal",
            delivery_type="delivery_standard",
            confirmed_template_code=LETTERS,
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_ensure_workspace_persists_offer_method_selected_template_and_source(db_session):
    await _seed_fixture(db_session)
    before_quotes = await _table_count(db_session, "quotes")
    before_orders = await _table_count(db_session, "orders")
    before_execution = await _table_count(db_session, "execution_plan")

    response = await ensure_intake_v6_workspace_for_intake_request(
        db_session,
        "IR-AVAILABILITY-1",
        _user(),
        offer_method="svg_analyzer_intake_v6",
        selected_template_code=LETTERS,
        source="work_intake_new_request",
    )

    assert response.template_code == LETTERS
    assert response.payload["selected_template_code"] == LETTERS
    assert response.payload["offer_method"] == "svg_analyzer_intake_v6"
    assert response.payload["source"] == "work_intake_new_request"
    assert response.payload["work_intake_context"]["selected_template_is_initial"] is True
    assert response.payload["work_intake_context"]["product_truth_final_decided_later"] is True

    row = (
        await db_session.execute(select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == response.id))
    ).scalar_one()
    assert row.template_code == LETTERS
    assert await _table_count(db_session, "quotes") == before_quotes
    assert await _table_count(db_session, "orders") == before_orders
    assert await _table_count(db_session, "execution_plan") == before_execution


@pytest.mark.asyncio
async def test_ensure_workspace_rejects_runtime_module_as_selected_template(db_session):
    await _seed_fixture(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await ensure_intake_v6_workspace_for_intake_request(
            db_session,
            "IR-AVAILABILITY-1",
            _user(),
            offer_method="svg_analyzer_intake_v6",
            selected_template_code=VOLUM_ALUMINUM,
            source="work_intake_new_request",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["error"] == "selected_template_not_quote_offerable"
    assert exc_info.value.detail["status_reason"] == "runtime_module_only"


@pytest.mark.asyncio
async def test_new_work_intake_flow_requires_selected_template_code(db_session):
    await _seed_fixture(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await ensure_intake_v6_workspace_for_intake_request(
            db_session,
            "IR-AVAILABILITY-1",
            _user(),
            offer_method="svg_analyzer_intake_v6",
            selected_template_code=None,
            source="work_intake_new_request",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["error"] == "selected_template_code_required"
