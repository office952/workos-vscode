import importlib.util
import uuid

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.inventory_materials import Inventory_materials
from models.inventory_sheet_remediation_audit_events import (
    Inventory_sheet_remediation_audit_events,
)
from models.orders import Orders
from models.quotes import Quotes


async def _seed_remediation_rows(db_session):
    suffix = uuid.uuid4().hex[:8]
    target_code = f"MAT-REMED-TARGET-{suffix}"
    control_code = f"MAT-REMED-CONTROL-{suffix}"

    db_session.add_all(
        [
            Inventory_materials(
                code=target_code,
                name="Target missing configuration",
                category="panou",
                unit="mp",
                status="active",
                sheet_format_type="sheet",
                sheet_unit="mm",
            ),
            Inventory_materials(
                code=control_code,
                name="Control unchanged",
                category="panou",
                unit="mp",
                status="active",
                sheet_format_type="sheet",
                sheet_width=1200,
                sheet_height=800,
                sheet_unit="mm",
            ),
            Quotes(code=f"Q-REMED-{suffix}", client_name="Client", status="draft", version=1),
            Orders(code=f"O-REMED-{suffix}", client_name="Client", status="new"),
            ExecutionPlan(
                order_id=1,
                order_code=f"ORD-REMED-{suffix}",
                snapshot_version=1,
                tasks_json="[]",
                total_estimated_time_minutes=0,
            ),
        ]
    )
    await db_session.commit()
    return {"target": target_code, "control": control_code}


def _valid_body(issue_code: str = "missing_configuration"):
    return {
        "issue_code": issue_code,
        "proposed_values": {
            "sheet_format_type": "sheet",
            "sheet_width": 3050,
            "sheet_height": 2050,
            "sheet_unit": "mm",
            "usable_width": 3030,
            "usable_height": 2030,
            "format_source": "manual",
            "format_verified": True,
            "format_notes": "Verified physical sheet format from supplier label.",
        },
        "reason": "Verified physical sheet format from supplier label.",
        "confirm": True,
    }


@pytest.fixture
def non_admin_auth_client(db_fixture):
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
            email="user@example.com",
            name="Test User",
            role="user",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    from fastapi.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


def test_remediation_unauth_rejected(unauth_client):
    response = unauth_client.patch(
        "/api/v1/admin/inventory/materials/MAT-ANY/sheet-format-remediation",
        json=_valid_body(),
    )
    assert response.status_code in (401, 403)


def test_remediation_non_admin_rejected(non_admin_auth_client):
    response = non_admin_auth_client.patch(
        "/api/v1/admin/inventory/materials/MAT-ANY/sheet-format-remediation",
        json=_valid_body(),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_remediate_single_material_success(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)

    before_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["target"])
    )
    before_target = before_result.scalar_one()
    before_width = before_target.sheet_width

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=_valid_body(),
    )
    assert response.status_code == 200
    body = response.json()

    assert body["source"] == "backend"
    assert body["operation"] == "inventory_sheet_remediation"
    assert body["status"] == "applied"
    assert body["material_id"] == codes["target"]
    assert body["issue_code"] == "missing_configuration"
    assert body["before"]["audit_status"] == "invalid"
    assert body["after"]["audit_status"] == "valid"
    assert body["after"]["sheet_format"]["sheet_width"] == 3050
    assert body["after"]["sheet_format"]["sheet_height"] == 2050
    assert body["audit_event_id"]

    db_session.expire_all()
    after_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["target"])
    )
    after_target = after_result.scalar_one()
    assert before_width is None
    assert after_target.sheet_width == 3050
    assert after_target.sheet_height == 2050


@pytest.mark.asyncio
async def test_remediation_writes_audit_event(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=_valid_body(),
    )
    assert response.status_code == 200
    body = response.json()

    event_id = int(body["audit_event_id"])
    event_result = await db_session.execute(
        select(Inventory_sheet_remediation_audit_events).where(
            Inventory_sheet_remediation_audit_events.id == event_id
        )
    )
    event = event_result.scalar_one()

    assert event.event_type == "inventory_sheet_remediation_applied"
    assert event.entity_type == "InventoryMaterial"
    assert event.entity_id == codes["target"]
    assert event.issue_code == "missing_configuration"
    assert event.source == "admin_manual_remediation"
    assert event.old_values["sheet_width"] is None
    assert event.new_values["sheet_width"] == 3050


@pytest.mark.asyncio
async def test_only_target_material_changes(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)

    before_control_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["control"])
    )
    before_control = before_control_result.scalar_one()
    before_control_width = before_control.sheet_width

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=_valid_body(),
    )
    assert response.status_code == 200

    after_control_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["control"])
    )
    after_control = after_control_result.scalar_one()
    assert after_control.sheet_width == before_control_width


@pytest.mark.asyncio
async def test_no_side_effects_stock_quote_order_execution(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)

    before_quotes = await db_session.scalar(select(func.count(Quotes.id)))
    before_orders = await db_session.scalar(select(func.count(Orders.id)))
    before_execution = await db_session.scalar(select(func.count(ExecutionPlan.id)))

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=_valid_body(),
    )
    assert response.status_code == 200

    after_quotes = await db_session.scalar(select(func.count(Quotes.id)))
    after_orders = await db_session.scalar(select(func.count(Orders.id)))
    after_execution = await db_session.scalar(select(func.count(ExecutionPlan.id)))

    assert before_quotes == after_quotes
    assert before_orders == after_orders
    assert before_execution == after_execution


@pytest.mark.asyncio
async def test_confirm_false_rejected(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)
    payload = _valid_body()
    payload["confirm"] = False

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "confirm_required"


@pytest.mark.asyncio
async def test_missing_reason_rejected(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)
    payload = _valid_body()
    payload.pop("reason")

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "reason_required"


@pytest.mark.asyncio
async def test_empty_reason_rejected(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)
    payload = _valid_body()
    payload["reason"] = "   "

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "reason_required"


@pytest.mark.asyncio
async def test_unsupported_issue_code_rejected(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=_valid_body(issue_code="missing_required_field"),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unsupported_issue_code"


@pytest.mark.asyncio
async def test_proposed_field_not_allowed_rejected(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)
    payload = _valid_body()
    payload["proposed_values"]["unit"] = "sqm"

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_dimensions_rejected_without_commit(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)
    payload = _valid_body()
    payload["proposed_values"]["sheet_width"] = -1

    before_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["target"])
    )
    before_target = before_result.scalar_one()

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_failed"

    after_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["target"])
    )
    after_target = after_result.scalar_one()
    assert before_target.sheet_width == after_target.sheet_width


@pytest.mark.asyncio
async def test_usable_gt_sheet_rejected_without_commit(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)
    payload = _valid_body()
    payload["proposed_values"]["usable_width"] = 4000

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_failed"


@pytest.mark.asyncio
async def test_issue_mismatch_rejected(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=_valid_body(issue_code="partial_payload"),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "issue_mismatch"


@pytest.mark.asyncio
async def test_audit_log_unavailable_prevents_write(auth_client, db_session, monkeypatch):
    from services import inventory_sheet_remediation_service as remediation_service

    codes = await _seed_remediation_rows(db_session)

    async def _raise_audit(*args, **kwargs):
        raise RuntimeError("audit backend unavailable")

    monkeypatch.setattr(remediation_service, "_create_audit_event", _raise_audit)

    before_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["target"])
    )
    before_target = before_result.scalar_one()

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{codes['target']}/sheet-format-remediation",
        json=_valid_body(),
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "audit_log_unavailable"

    after_result = await db_session.execute(
        select(Inventory_materials).where(Inventory_materials.code == codes["target"])
    )
    after_target = after_result.scalar_one()
    assert before_target.sheet_width == after_target.sheet_width


@pytest.mark.asyncio
async def test_material_not_found_returns_404(auth_client):
    response = auth_client.patch(
        "/api/v1/admin/inventory/materials/MAT-DOES-NOT-EXIST/sheet-format-remediation",
        json=_valid_body(),
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "material_not_found"


@pytest.mark.asyncio
async def test_multiple_material_ids_in_path_rejected(auth_client, db_session):
    codes = await _seed_remediation_rows(db_session)
    material_id = f"{codes['target']},{codes['control']}"

    response = auth_client.patch(
        f"/api/v1/admin/inventory/materials/{material_id}/sheet-format-remediation",
        json=_valid_body(),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "multiple_material_ids_not_allowed"


def test_no_filter_based_bulk_endpoint(auth_client):
    response = auth_client.post(
        "/api/v1/admin/inventory/materials/sheet-format-remediation",
        json={"issue_code": "missing_configuration"},
    )
    assert response.status_code in {404, 405}


def test_stock_movement_model_not_present():
    stock_movements_spec = importlib.util.find_spec("models.stock_movements")
    # BUILD 16 introduced stock_movements model — it should now exist
    assert stock_movements_spec is not None
