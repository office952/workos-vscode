"""Security and behavior tests for employee-mobile self-only execution tasks."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.intake_requests import Intake_requests
from models.orders import Orders
from models.quotes import Quotes
from schemas.auth import UserResponse

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from services.operational_registry_service import OperationalRegistryService
from services.production_document_handoff_service import merge_production_documents


def _user(user_id: str, role: str = "employee_mobile") -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name=f"User {user_id}",
        role=role,
        last_login=None,
    )


async def _seed_employee(
    db_session,
    *,
    user_id: str | None,
    name: str = "Mobile Employee",
    status: str = "active",
) -> Employees:
    emp = Employees(
        name=name,
        status=status,
        employee_type="productive",
        user_id=user_id,
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _seed_plan_unassigned_task(
    db_session,
    *,
    order_id: int,
    task_id: str = "T-001",
    extra_task_fields: dict | None = None,
) -> None:
    task = {
        "task_id": task_id,
        "name": "Print",
        "display_name": "Printare",
        "process_id": "print",
        "process_type": "print",
        "machine_type": "printer_large_format",
        "estimated_time_minutes": 30,
    }
    if extra_task_fields:
        task.update(extra_task_fields)
    tasks = [task]
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-{order_id:04d}",
            snapshot_version=1,
            tasks_json=json.dumps(tasks),
            total_estimated_time_minutes=30,
        )
    )
    await db_session.commit()


async def _seed_active_order(db_session, *, order_id: int) -> None:
    quote = Quotes(
        code=f"QT-{order_id:04d}",
        intake_code=f"IR-{order_id:04d}",
        client_name="Test Client",
        status="accepted",
        version=1,
    )
    db_session.add(quote)
    await db_session.flush()
    db_session.add(
        Orders(
            id=order_id,
            code=f"ORD-{order_id:04d}",
            quote_id=quote.id,
            quote_code=quote.code,
            client_name="Test Client",
            status="in_production",
        )
    )
    await db_session.commit()


async def _seed_print_eligibility(db_session, employee_id: int) -> None:
    svc = OperationalRegistryService(db_session)
    await svc.set_employee_authorizations(
        employee_id,
        skill_codes=["SK_PRINT_OPERATOR"],
        workcenter_codes=["WC_PRINT"],
        resource_codes=["MCH-EPSON-60800"],
    )
    await svc.upsert_operation_mapping(
        {
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_workcenter_codes": ["WC_PRINT"],
            "allowed_resource_codes": ["MCH-EPSON-60800"],
            "authorization_mode": "hybrid",
            "authorized_employee_ids": [employee_id],
        }
    )


async def _seed_cnc_eligibility(db_session, employee_id: int) -> None:
    svc = OperationalRegistryService(db_session)
    await svc.upsert_operation_mapping(
        {
            "operation_code": "cnc_routing",
            "authorization_mode": "explicit",
            "authorized_employee_ids": [employee_id],
        }
    )


async def _seed_plan_with_assigned_task(
    db_session,
    *,
    order_id: int,
    assigned_employee_id: int,
    task_id: str = "T-001",
    extra_task_fields: dict | None = None,
) -> None:
    task = {
        "task_id": task_id,
        "name": "Print",
        "display_name": "Printare",
        "process_id": "print",
        "process_type": "print",
        "machine_type": "printer_large_format",
        "estimated_time_minutes": 30,
        "assigned_employee_id": assigned_employee_id,
    }
    if extra_task_fields:
        task.update(extra_task_fields)
    tasks = [task]
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-{order_id:04d}",
            snapshot_version=1,
            tasks_json=json.dumps(tasks),
            total_estimated_time_minutes=30,
        )
    )
    await db_session.commit()


async def _seed_reality_task(
    db_session,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
    started_at: str | None = None,
    ended_at: str | None = None,
    blocked_at: str | None = None,
) -> None:
    entry = {
        "task_id": task_id,
        "employee_id": employee_id,
        "employee_name": "Worker",
        "operator_name": "Worker",
    }
    if started_at:
        entry["started_at"] = started_at
    if ended_at:
        entry["ended_at"] = ended_at
    if blocked_at:
        entry["blocked_at"] = blocked_at
    db_session.add(
        ExecutionReality(
            order_id=order_id,
            order_code=f"ORD-{order_id:04d}",
            tasks_json=json.dumps([entry]),
            total_actual_time_minutes=0.0,
        )
    )
    await db_session.commit()


def _client_for(db_fixture, user: UserResponse) -> TestClient:
    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    return TestClient(app, raise_server_exceptions=False)


def _cleanup_overrides():
    app.dependency_overrides.clear()


@pytest.fixture
def mobile_client(db_fixture, db_session):
    user_id = f"mobile-user-{uuid.uuid4().hex[:8]}"

    async def _setup():
        await _seed_employee(db_session, user_id=user_id, name="Linked Mobile")

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    yield client
    _cleanup_overrides()


def test_list_tasks_empty_when_no_assignment(mobile_client):
    response = mobile_client.get("/api/v1/employee-mobile/tasks")
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_list_tasks_returns_assigned_plan_task(db_fixture, db_session):
    owner_id = f"owner-{uuid.uuid4().hex[:8]}"
    other_id = f"other-{uuid.uuid4().hex[:8]}"

    async def _setup():
        owner = await _seed_employee(db_session, user_id=owner_id, name="Owner")
        other = await _seed_employee(db_session, user_id=other_id, name="Other")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=101,
            assigned_employee_id=owner.id,
            task_id="T-OWN",
        )
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=102,
            assigned_employee_id=other.id,
            task_id="T-OTH",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(owner_id, "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks")
        assert response.status_code == 200, response.text
        rows = response.json()
        assert len(rows) == 1
        assert rows[0]["task_id"] == "T-OWN"
        assert rows[0]["status"] == "assigned"
    finally:
        _cleanup_overrides()


def test_start_assigned_task(db_fixture, db_session):
    user_id = f"starter-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Starter")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=201,
            assigned_employee_id=emp.id,
            task_id="T-START",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.patch(
            "/api/v1/employee-mobile/tasks/T-START/start",
            json={"order_id": 201},
        )
        assert response.status_code == 200, response.text
        listed = client.get("/api/v1/employee-mobile/tasks").json()
        assert listed[0]["status"] == "in_progress"
        assert listed[0]["started_at"]
    finally:
        _cleanup_overrides()


def test_cannot_start_other_employee_task(db_fixture, db_session):
    owner_id = f"owner2-{uuid.uuid4().hex[:8]}"
    intruder_id = f"intruder-{uuid.uuid4().hex[:8]}"

    async def _setup():
        owner = await _seed_employee(db_session, user_id=owner_id, name="Owner2")
        await _seed_employee(db_session, user_id=intruder_id, name="Intruder")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=301,
            assigned_employee_id=owner.id,
            task_id="T-LOCK",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(intruder_id, "employee_mobile"))
    try:
        response = client.patch(
            "/api/v1/employee-mobile/tasks/T-LOCK/start",
            json={"order_id": 301},
        )
        assert response.status_code == 403, response.text
    finally:
        _cleanup_overrides()


def test_complete_in_progress_task(db_fixture, db_session):
    user_id = f"finisher-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Finisher")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=401,
            assigned_employee_id=emp.id,
            task_id="T-DONE",
        )
        await _seed_reality_task(
            db_session,
            order_id=401,
            task_id="T-DONE",
            employee_id=emp.id,
            started_at="2026-06-12T08:00:00+00:00",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.patch(
            "/api/v1/employee-mobile/tasks/T-DONE/complete",
            json={"order_id": 401},
        )
        assert response.status_code == 200, response.text
        listed = client.get("/api/v1/employee-mobile/tasks").json()
        assert listed[0]["status"] == "done"
        assert listed[0]["completed_at"]
    finally:
        _cleanup_overrides()


def test_pause_and_resume_mobile_task(db_fixture, db_session):
    user_id = f"pauser-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Pauser")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=601,
            assigned_employee_id=emp.id,
            task_id="T-PAUSE",
        )
        await _seed_reality_task(
            db_session,
            order_id=601,
            task_id="T-PAUSE",
            employee_id=emp.id,
            started_at="2026-06-12T08:00:00+00:00",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        pause = client.patch(
            "/api/v1/employee-mobile/tasks/T-PAUSE/pause",
            json={"order_id": 601},
        )
        assert pause.status_code == 200, pause.text
        listed = client.get("/api/v1/employee-mobile/tasks").json()
        assert listed[0]["status"] == "paused"
        assert not listed[0].get("blocked_at")

        resume = client.patch(
            "/api/v1/employee-mobile/tasks/T-PAUSE/resume",
            json={"order_id": 601},
        )
        assert resume.status_code == 200, resume.text
        listed = client.get("/api/v1/employee-mobile/tasks").json()
        assert listed[0]["status"] == "in_progress"
    finally:
        _cleanup_overrides()


def test_block_requires_started_task(db_fixture, db_session):
    user_id = f"blocker-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Blocker")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=501,
            assigned_employee_id=emp.id,
            task_id="T-BLOCK",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.patch(
            "/api/v1/employee-mobile/tasks/T-BLOCK/block",
            json={"order_id": 501, "reason": "Lipsă material"},
        )
        assert response.status_code == 422, response.text
        assert response.json()["detail"]["error"] == "task_not_started"
    finally:
        _cleanup_overrides()


def test_user_without_employee_link_gets_403(db_fixture):
    client = _client_for(db_fixture, _user("no-link-user", "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks")
        assert response.status_code == 403, response.text
        assert response.json()["detail"]["error"] == "employee_link_missing"
    finally:
        _cleanup_overrides()


def test_list_tasks_includes_instructions_and_documents_from_plan(db_fixture, db_session):
    user_id = f"docs-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Docs Worker")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=601,
            assigned_employee_id=emp.id,
            task_id="T-DOC",
            extra_task_fields={
                "instructions": "Montează LED conform schiței.",
                "documents": [
                    {
                        "id": "doc-1",
                        "name": "Schiță LED",
                        "type": "pdf",
                        "url": "https://example.com/sketch.pdf",
                        "source": "task",
                    },
                    {
                        "name": "Plan fără URL",
                        "type": "metadata",
                        "source": "dev_fixture",
                    },
                ],
            },
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks")
        assert response.status_code == 200, response.text
        row = response.json()[0]
        assert row["instructions"] == "Montează LED conform schiței."
        assert len(row["documents"]) == 2
        assert row["documents"][0]["name"] == "Schiță LED"
        assert row["documents"][0]["url"] == "https://example.com/sketch.pdf"
        assert "url" not in row["documents"][1]
    finally:
        _cleanup_overrides()


async def _seed_order_intake_work_file_chain(
    db_session,
    *,
    order_id: int,
    intake_code: str,
    assigned_employee_id: int,
    task_id: str = "T-WF",
    file_id: str = "wf-test-file",
    storage_root: Path,
) -> None:
    stored_name = f"{file_id}_schita.svg"
    storage_dir = storage_root / intake_code
    storage_dir.mkdir(parents=True, exist_ok=True)
    (storage_dir / stored_name).write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text>test</text></svg>',
        encoding="utf-8",
    )

    work_file = {
        "id": file_id,
        "fileName": "schita_litere.svg",
        "storedFileName": stored_name,
        "mimeType": "image/svg+xml",
        "extension": ".svg",
        "role": "master_work_file",
        "usableFor": ["general_production"],
        "isPrimary": True,
    }
    product_spec = {"workFileAttachments": [work_file]}

    intake = Intake_requests(
        code=intake_code,
        client_name="Test Client",
        product_family="Litere volumetrice",
        status="confirmed",
        product_spec_json=json.dumps(product_spec),
    )
    db_session.add(intake)
    await db_session.flush()

    quote = Quotes(
        code=f"QT-{order_id:04d}",
        intake_id=intake.id,
        intake_code=intake_code,
        client_name="Test Client",
        status="accepted",
        version=1,
    )
    db_session.add(quote)
    await db_session.flush()

    db_session.add(
        Orders(
            id=order_id,
            code=f"ORD-{order_id:04d}",
            quote_id=quote.id,
            quote_code=quote.code,
            client_name="Test Client",
            status="in_production",
        )
    )
    await _seed_plan_with_assigned_task(
        db_session,
        order_id=order_id,
        assigned_employee_id=assigned_employee_id,
        task_id=task_id,
    )
    await db_session.commit()


def test_merge_production_documents_excludes_commercial_quote_pdf():
    task_docs = [
        {
            "id": "commercial-1",
            "name": "Oferta client",
            "type": "quote_pdf",
            "source": "quote_documents_archive",
            "url": "/api/v1/entities/quotes/1/pdf/1/download",
        }
    ]
    order_docs = [
        {
            "id": "wf-1",
            "name": "schita.svg",
            "type": "svg",
            "source": "intake_work_file",
            "url": "/api/v1/employee-mobile/orders/1/work-files/wf-1/download",
            "downloadable": True,
        }
    ]
    merged = merge_production_documents(task_docs, order_docs)
    assert len(merged) == 1
    assert merged[0]["source"] == "intake_work_file"


def test_list_tasks_includes_intake_work_files_for_assigned_order(
    db_fixture,
    db_session,
    monkeypatch,
    tmp_path,
):
    user_id = f"wf-user-{uuid.uuid4().hex[:8]}"
    intake_code = f"IR-WF-{uuid.uuid4().hex[:6]}"
    order_id = 701
    file_id = "wfassigned001"

    monkeypatch.setattr(
        "services.work_intake_work_file_service.STORAGE_ROOT",
        tmp_path,
    )
    monkeypatch.setattr(
        "services.employee_mobile_production_documents_service.STORAGE_ROOT",
        tmp_path,
    )

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="WF Worker")
        await _seed_order_intake_work_file_chain(
            db_session,
            order_id=order_id,
            intake_code=intake_code,
            assigned_employee_id=emp.id,
            task_id="T-WF",
            file_id=file_id,
            storage_root=tmp_path,
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks")
        assert response.status_code == 200, response.text
        row = response.json()[0]
        assert len(row["documents"]) == 1
        doc = row["documents"][0]
        assert doc["name"] == "schita_litere.svg"
        assert doc["source"] == "intake_work_file"
        assert doc["downloadable"] is True
        assert doc["url"] == f"/api/v1/employee-mobile/orders/{order_id}/work-files/{file_id}/download"
    finally:
        _cleanup_overrides()


def test_work_file_download_requires_assigned_order_task(
    db_fixture,
    db_session,
    monkeypatch,
    tmp_path,
):
    owner_id = f"wf-owner-{uuid.uuid4().hex[:8]}"
    intruder_id = f"wf-intruder-{uuid.uuid4().hex[:8]}"
    intake_code = f"IR-WF-{uuid.uuid4().hex[:6]}"
    order_id = 801
    file_id = "wfsecure001"

    monkeypatch.setattr(
        "services.work_intake_work_file_service.STORAGE_ROOT",
        tmp_path,
    )
    monkeypatch.setattr(
        "services.employee_mobile_production_documents_service.STORAGE_ROOT",
        tmp_path,
    )

    async def _setup():
        owner = await _seed_employee(db_session, user_id=owner_id, name="Owner WF")
        await _seed_employee(db_session, user_id=intruder_id, name="Intruder WF")
        await _seed_order_intake_work_file_chain(
            db_session,
            order_id=order_id,
            intake_code=intake_code,
            assigned_employee_id=owner.id,
            task_id="T-WF-SEC",
            file_id=file_id,
            storage_root=tmp_path,
        )

    db_fixture.run(_setup())
    try:
        owner_client = _client_for(db_fixture, _user(owner_id, "employee_mobile"))
        ok = owner_client.get(
            f"/api/v1/employee-mobile/orders/{order_id}/work-files/{file_id}/download"
        )
        assert ok.status_code == 200, ok.text
        assert "image/svg+xml" in ok.headers.get("content-type", "")

        intruder_client = _client_for(db_fixture, _user(intruder_id, "employee_mobile"))
        denied = intruder_client.get(
            f"/api/v1/employee-mobile/orders/{order_id}/work-files/{file_id}/download"
        )
        assert denied.status_code == 403, denied.text
        assert denied.json()["detail"]["error"] == "task_not_assigned_to_employee"
    finally:
        _cleanup_overrides()


def test_available_tasks_visible_for_eligible_unassigned(db_fixture, db_session):
    user_id = f"avail-{uuid.uuid4().hex[:8]}"
    order_id = 901

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Eligible Claimer")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, emp.id)
        await _seed_plan_unassigned_task(
            db_session,
            order_id=order_id,
            task_id="T-AVAIL",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks/available")
        assert response.status_code == 200, response.text
        rows = response.json()
        assert len(rows) == 1
        assert rows[0]["task_id"] == "T-AVAIL"
        assert rows[0].get("claimable") is True
        assert rows[0].get("is_startable") is True
    finally:
        _cleanup_overrides()


def test_available_tasks_hidden_when_not_eligible(db_fixture, db_session):
    user_id = f"noelig-{uuid.uuid4().hex[:8]}"
    order_id = 902

    async def _setup():
        await _seed_employee(db_session, user_id=user_id, name="Not Eligible")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_plan_unassigned_task(
            db_session,
            order_id=order_id,
            task_id="T-HIDE",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks/available")
        assert response.status_code == 200, response.text
        assert response.json() == []
    finally:
        _cleanup_overrides()


def test_available_tasks_hidden_when_assigned_to_other(db_fixture, db_session):
    owner_id = f"own-avail-{uuid.uuid4().hex[:8]}"
    viewer_id = f"view-avail-{uuid.uuid4().hex[:8]}"
    order_id = 903

    async def _setup():
        owner = await _seed_employee(db_session, user_id=owner_id, name="Owner Avail")
        viewer = await _seed_employee(db_session, user_id=viewer_id, name="Viewer Avail")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, viewer.id)
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=owner.id,
            task_id="T-TAKEN",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(viewer_id, "employee_mobile"))
    try:
        response = client.get("/api/v1/employee-mobile/tasks/available")
        assert response.status_code == 200, response.text
        task_ids = {row["task_id"] for row in response.json()}
        assert "T-TAKEN" not in task_ids
    finally:
        _cleanup_overrides()


def test_claim_success_assigns_and_lists_in_my_tasks(db_fixture, db_session):
    user_id = f"claim-ok-{uuid.uuid4().hex[:8]}"
    order_id = 904

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Claimer OK")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, emp.id)
        await _seed_plan_unassigned_task(
            db_session,
            order_id=order_id,
            task_id="T-CLAIM",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        claim = client.post(
            "/api/v1/employee-mobile/tasks/T-CLAIM/claim",
            json={"order_id": order_id},
        )
        assert claim.status_code == 200, claim.text
        body = claim.json()
        assert body["assigned_employee_id"] > 0
        assert body["already_claimed"] is False

        mine = client.get("/api/v1/employee-mobile/tasks").json()
        assert len(mine) == 1
        assert mine[0]["task_id"] == "T-CLAIM"

        available = client.get("/api/v1/employee-mobile/tasks/available").json()
        assert not any(row["task_id"] == "T-CLAIM" for row in available)
    finally:
        _cleanup_overrides()


def test_claim_conflict_when_assigned_to_other(db_fixture, db_session):
    owner_id = f"claim-own-{uuid.uuid4().hex[:8]}"
    intruder_id = f"claim-intr-{uuid.uuid4().hex[:8]}"
    order_id = 905

    async def _setup():
        owner = await _seed_employee(db_session, user_id=owner_id, name="Claim Owner")
        intruder = await _seed_employee(db_session, user_id=intruder_id, name="Claim Intruder")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, intruder.id)
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=owner.id,
            task_id="T-CONFLICT",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(intruder_id, "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/tasks/T-CONFLICT/claim",
            json={"order_id": order_id},
        )
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["error"] == "task_already_assigned"
    finally:
        _cleanup_overrides()


def test_claim_not_eligible_returns_403(db_fixture, db_session):
    user_id = f"claim-noel-{uuid.uuid4().hex[:8]}"
    order_id = 906

    async def _setup():
        await _seed_employee(db_session, user_id=user_id, name="Claim No Elig")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_plan_unassigned_task(
            db_session,
            order_id=order_id,
            task_id="T-NOELIG",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/tasks/T-NOELIG/claim",
            json={"order_id": order_id},
        )
        assert response.status_code == 403, response.text
        assert response.json()["detail"]["error"] == "employee_not_eligible"
    finally:
        _cleanup_overrides()


def test_claim_does_not_start_work_session(db_fixture, db_session):
    user_id = f"claim-nostart-{uuid.uuid4().hex[:8]}"
    order_id = 907

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Claim No Start")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, emp.id)
        await _seed_plan_unassigned_task(
            db_session,
            order_id=order_id,
            task_id="T-NOSTART",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        claim = client.post(
            "/api/v1/employee-mobile/tasks/T-NOSTART/claim",
            json={"order_id": order_id},
        )
        assert claim.status_code == 200, claim.text

        listed = client.get("/api/v1/employee-mobile/tasks").json()
        assert listed[0]["status"] == "assigned"
        assert not listed[0].get("started_at")
    finally:
        _cleanup_overrides()


def test_start_after_claim_still_respects_readiness(db_fixture, db_session):
    from tests.test_task_readiness_dependencies import _build_volumetric_tasks

    user_id = f"claim-gate-{uuid.uuid4().hex[:8]}"
    order_id = 908

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Claim Gate")
        await _seed_cnc_eligibility(db_session, emp.id)
        tasks = _build_volumetric_tasks(sandu_id=999)
        t002 = next(t for t in tasks if t["task_id"] == "T-002")
        t002.pop("assigned_employee_id", None)
        quote = Quotes(
            code=f"QT-{order_id:04d}",
            intake_code=f"IR-{order_id:04d}",
            client_name="Client",
            status="accepted",
            version=1,
        )
        db_session.add(quote)
        await db_session.flush()
        db_session.add(
            Orders(
                id=order_id,
                code=f"ORD-{order_id:04d}",
                quote_id=quote.id,
                quote_code=quote.code,
                client_name="Client",
                status="in_production",
            )
        )
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-{order_id:04d}",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=300,
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        claim = client.post(
            "/api/v1/employee-mobile/tasks/T-002/claim",
            json={"order_id": order_id},
        )
        assert claim.status_code == 200, claim.text

        start = client.patch(
            "/api/v1/employee-mobile/tasks/T-002/start",
            json={"order_id": order_id},
        )
        assert start.status_code == 409, start.text
        assert start.json()["detail"]["code"] == "task_not_ready"
    finally:
        _cleanup_overrides()


async def _plan_assigned_employee_id(db_session, *, order_id: int, task_id: str):
    from sqlalchemy import select

    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one()
    for entry in json.loads(plan.tasks_json):
        if isinstance(entry, dict) and entry.get("task_id") == task_id:
            return entry.get("assigned_employee_id")
    return None


def test_start_from_available_success(db_fixture, db_session):
    user_id = f"sfa-ok-{uuid.uuid4().hex[:8]}"
    order_id = 910

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Start Avail OK")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, emp.id)
        await _seed_plan_unassigned_task(
            db_session,
            order_id=order_id,
            task_id="T-SFA-OK",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        avail_before = client.get("/api/v1/employee-mobile/tasks/available").json()
        assert any(r["task_id"] == "T-SFA-OK" and r.get("is_startable") for r in avail_before)

        response = client.post(
            "/api/v1/employee-mobile/tasks/T-SFA-OK/start-from-available",
            json={"order_id": order_id},
        )
        assert response.status_code == 200, response.text

        listed = client.get("/api/v1/employee-mobile/tasks").json()
        assert len(listed) == 1
        assert listed[0]["task_id"] == "T-SFA-OK"
        assert listed[0]["status"] == "in_progress"
        assert listed[0].get("started_at")

        available = client.get("/api/v1/employee-mobile/tasks/available").json()
        assert not any(row["task_id"] == "T-SFA-OK" for row in available)
    finally:
        _cleanup_overrides()


def test_start_from_available_not_ready_leaves_unassigned(db_fixture, db_session):
    from tests.test_task_readiness_dependencies import _build_volumetric_tasks

    user_id = f"sfa-nr-{uuid.uuid4().hex[:8]}"
    order_id = 911

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Start Avail NR")
        await _seed_cnc_eligibility(db_session, emp.id)
        tasks = _build_volumetric_tasks(sandu_id=999)
        t002 = next(t for t in tasks if t["task_id"] == "T-002")
        t002.pop("assigned_employee_id", None)
        quote = Quotes(
            code=f"QT-{order_id:04d}",
            intake_code=f"IR-{order_id:04d}",
            client_name="Client",
            status="accepted",
            version=1,
        )
        db_session.add(quote)
        await db_session.flush()
        db_session.add(
            Orders(
                id=order_id,
                code=f"ORD-{order_id:04d}",
                quote_id=quote.id,
                quote_code=quote.code,
                client_name="Client",
                status="in_production",
            )
        )
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-{order_id:04d}",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=300,
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/tasks/T-002/start-from-available",
            json={"order_id": order_id},
        )
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["code"] == "task_not_ready"

        available = client.get("/api/v1/employee-mobile/tasks/available").json()
        t002_rows = [row for row in available if row.get("task_id") == "T-002"]
        if t002_rows:
            assert t002_rows[0].get("is_startable") is False

        async def _check_unassigned():
            assigned = await _plan_assigned_employee_id(
                db_session,
                order_id=order_id,
                task_id="T-002",
            )
            assert assigned is None

        db_fixture.run(_check_unassigned())

        listed = client.get("/api/v1/employee-mobile/tasks").json()
        assert listed == []
    finally:
        _cleanup_overrides()


def test_start_from_available_not_eligible(db_fixture, db_session):
    user_id = f"sfa-ne-{uuid.uuid4().hex[:8]}"
    order_id = 912

    async def _setup():
        await _seed_employee(db_session, user_id=user_id, name="Start Avail NE")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_plan_unassigned_task(
            db_session,
            order_id=order_id,
            task_id="T-SFA-NE",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/tasks/T-SFA-NE/start-from-available",
            json={"order_id": order_id},
        )
        assert response.status_code == 403, response.text
        assert response.json()["detail"]["error"] == "employee_not_eligible"
    finally:
        _cleanup_overrides()


def test_start_from_available_assigned_to_other(db_fixture, db_session):
    owner_id = f"sfa-own-{uuid.uuid4().hex[:8]}"
    intruder_id = f"sfa-intr-{uuid.uuid4().hex[:8]}"
    order_id = 913

    async def _setup():
        owner = await _seed_employee(db_session, user_id=owner_id, name="SFA Owner")
        intruder = await _seed_employee(db_session, user_id=intruder_id, name="SFA Intruder")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, intruder.id)
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=owner.id,
            task_id="T-SFA-OTH",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(intruder_id, "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/tasks/T-SFA-OTH/start-from-available",
            json={"order_id": order_id},
        )
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["error"] == "task_already_assigned"
    finally:
        _cleanup_overrides()


def test_start_from_available_already_mine_starts(db_fixture, db_session):
    user_id = f"sfa-mine-{uuid.uuid4().hex[:8]}"
    order_id = 914

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="SFA Mine")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, emp.id)
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=emp.id,
            task_id="T-SFA-MINE",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/tasks/T-SFA-MINE/start-from-available",
            json={"order_id": order_id},
        )
        assert response.status_code == 200, response.text
        listed = client.get("/api/v1/employee-mobile/tasks").json()
        assert listed[0]["status"] == "in_progress"
    finally:
        _cleanup_overrides()
