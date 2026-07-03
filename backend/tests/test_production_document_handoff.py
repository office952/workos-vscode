"""Tests for production document handoff at plan generation and merge rules."""

from __future__ import annotations

import json
import uuid

import pytest
from models.execution_plan import ExecutionPlan
from models.intake_requests import Intake_requests
from models.orders import Orders
from models.quotes import Quotes
from schemas.auth import UserResponse
from services.production_document_handoff_service import (
    attach_documents_to_planned_tasks,
    load_eligible_intake_documents_for_plan,
    merge_production_documents,
    normalize_intake_work_file_for_plan,
)

from core.database import get_db
from dependencies.auth import get_current_user
from main import app


def test_normalize_intake_work_file_for_plan_excludes_commercial():
    blocked = normalize_intake_work_file_for_plan(
        {
            "id": "quote-1",
            "fileName": "Oferta client.pdf",
            "mimeType": "application/pdf",
            "extension": ".pdf",
        }
    )
    assert blocked is None

    ok = normalize_intake_work_file_for_plan(
        {
            "id": "sketch-1",
            "fileName": "Schiță.svg",
            "mimeType": "image/svg+xml",
            "extension": ".svg",
        }
    )
    assert ok is not None
    assert ok["source"] == "intake_work_file"
    assert "url" not in ok


def test_merge_dedupes_by_id_and_source_and_prefers_url():
    task_docs = [
        {
            "id": "wf-1",
            "name": "Plan copy",
            "type": "svg",
            "source": "intake_work_file",
        }
    ]
    order_docs = [
        {
            "id": "wf-1",
            "name": "Plan copy",
            "type": "svg",
            "source": "intake_work_file",
            "url": "/api/v1/employee-mobile/orders/1/work-files/wf-1/download",
            "downloadable": True,
        }
    ]
    merged = merge_production_documents(task_docs, order_docs)
    assert len(merged) == 1
    assert merged[0].get("url")


def test_attach_documents_preserves_existing_task_documents():
    tasks = [
        {
            "task_id": "T-1",
            "documents": [
                {
                    "id": "custom-1",
                    "name": "Task sketch",
                    "type": "pdf",
                    "source": "task",
                }
            ],
        },
        {"task_id": "T-2"},
    ]
    handoff = [
        {
            "id": "wf-1",
            "name": "Intake SVG",
            "type": "svg",
            "source": "intake_work_file",
            "downloadable": True,
        }
    ]
    updated = attach_documents_to_planned_tasks(tasks, handoff)
    assert len(updated[0]["documents"]) == 2
    assert updated[0]["documents"][0]["id"] == "custom-1"
    assert updated[1]["documents"][0]["id"] == "wf-1"


def test_merge_excludes_quote_pdf_and_snapshot_sources():
    merged = merge_production_documents(
        [
            {
                "id": "q1",
                "name": "Quote",
                "type": "quote_pdf",
                "source": "quote_documents_archive",
            },
            {
                "id": "snap",
                "name": "Snapshot",
                "type": "order_snapshot",
                "source": "order_snapshot",
            },
        ],
        [],
    )
    assert merged == []


@pytest.mark.asyncio
async def test_load_eligible_intake_documents_for_plan(db_session):
    intake_code = f"IR-HANDOFF-{uuid.uuid4().hex[:6]}"
    intake = Intake_requests(
        code=intake_code,
        client_name="Client",
        product_family="Litere",
        status="confirmed",
        product_spec_json=json.dumps(
            {
                "workFileAttachments": [
                    {
                        "id": "wf-eligible",
                        "fileName": "schita.svg",
                        "mimeType": "image/svg+xml",
                        "extension": ".svg",
                    },
                    {
                        "id": "wf-blocked",
                        "fileName": "quote.pdf",
                        "mimeType": "application/pdf",
                        "extension": ".pdf",
                    },
                ]
            }
        ),
    )
    db_session.add(intake)
    await db_session.flush()

    quote = Quotes(
        code=f"QT-{uuid.uuid4().hex[:6]}",
        intake_id=intake.id,
        intake_code=intake_code,
        client_name="Client",
        status="accepted",
        version=1,
    )
    db_session.add(quote)
    await db_session.flush()

    order_id = 9001 + int(uuid.uuid4().hex[:4], 16) % 1000
    db_session.add(
        Orders(
            id=order_id,
            code=f"ORD-{order_id}",
            quote_id=quote.id,
            quote_code=quote.code,
            client_name="Client",
            status="in_production",
        )
    )
    await db_session.commit()

    docs = await load_eligible_intake_documents_for_plan(db_session, order_id=order_id)
    assert len(docs) == 1
    assert docs[0]["id"] == "wf-eligible"


def _admin_user() -> UserResponse:
    return UserResponse(
        id="admin-handoff",
        email="admin@workos.test",
        name="Admin",
        role="admin",
        last_login=None,
    )


def test_plan_from_order_attaches_intake_documents(db_fixture, db_session, monkeypatch, tmp_path):
    from tests.test_execution_flow import _complete_snapshot_dict

    monkeypatch.setattr("services.work_intake_work_file_service.STORAGE_ROOT", tmp_path)

    intake_code = f"IR-PLAN-{uuid.uuid4().hex[:6]}"
    order_id = 9100 + int(uuid.uuid4().hex[:4], 16) % 100

    async def _setup():
        stored_name = "planwf001_schita.svg"
        storage_dir = tmp_path / intake_code
        storage_dir.mkdir(parents=True, exist_ok=True)
        (storage_dir / stored_name).write_text("<svg/>", encoding="utf-8")

        intake = Intake_requests(
            code=intake_code,
            client_name="Client",
            product_family="Litere",
            status="confirmed",
            product_spec_json=json.dumps(
                {
                    "workFileAttachments": [
                        {
                            "id": "planwf001",
                            "fileName": "schita.svg",
                            "storedFileName": stored_name,
                            "mimeType": "image/svg+xml",
                            "extension": ".svg",
                        }
                    ]
                }
            ),
        )
        db_session.add(intake)
        await db_session.flush()

        quote = Quotes(
            code=f"QT-{order_id}",
            intake_id=intake.id,
            intake_code=intake_code,
            client_name="Client",
            status="accepted",
            version=1,
        )
        db_session.add(quote)
        await db_session.flush()

        db_session.add(
            Orders(
                id=order_id,
                code=f"ORD-{order_id}",
                quote_id=quote.id,
                quote_code=quote.code,
                client_name="Client",
                status="locked",
                snapshot_version=1,
                snapshot_line_items=json.dumps(_complete_snapshot_dict()),
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return _admin_user()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    from fastapi.testclient import TestClient

    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.post(f"/api/v1/execution/plan/from-order/{order_id}")
        assert resp.status_code in {200, 201}, resp.text
        plan = resp.json()
        assert plan["tasks"]
        for task in plan["tasks"]:
            docs = task.get("documents") or []
            assert any(d.get("id") == "planwf001" for d in docs)
            assert all(d.get("source") != "quote_pdf" for d in docs)
            assert all("employee-mobile" not in str(d.get("url") or "") for d in docs)
    finally:
        app.dependency_overrides.clear()
