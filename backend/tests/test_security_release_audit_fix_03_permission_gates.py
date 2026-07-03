from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from core.database import get_db
from dependencies.auth import get_current_user
from models.output_blocks import OutputBlock
from models.quotes import Quotes
from models.rendered_output_snapshots import RenderedOutputSnapshot
from routers.admin_workcenter_rates import router as workcenter_rates_router
from routers.aihub import router as aihub_router
from routers.operator_tasks import router as operator_router
from routers.output_blocks import router as output_blocks_router
from routers.quote_output_snapshots import router as quote_output_snapshots_router
from routers.quote_pdf import router as quote_pdf_router
from routers.storage import router as storage_router
from schemas.auth import UserResponse


def _request_as_role(
    db_fixture,
    role: str,
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
):
    app = FastAPI()
    app.include_router(storage_router)
    app.include_router(quote_output_snapshots_router)
    app.include_router(quote_pdf_router)
    app.include_router(operator_router)
    app.include_router(workcenter_rates_router)
    app.include_router(aihub_router)
    app.include_router(output_blocks_router)

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id=f"test-{role}",
            email=f"{role}@workos.test",
            name=f"Test {role}",
            role=role,
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app, raise_server_exceptions=False) as client:
        return client.request(method=method, url=path, json=json_body)


def _assert_permission_denied(response, expected_permission: str):
    assert response.status_code == 403
    body = response.json()
    detail = body.get("detail", {})
    assert detail.get("error") == "permission_denied"
    assert detail.get("permission") == expected_permission


async def _seed_output_block_and_quote(db_fixture):
    async with db_fixture.session_maker() as session:
        block = OutputBlock(
            block_id="perm-gate-ob-1",
            block_type="offer_short_description",
            title="Permission gate block",
            purpose="Permission gate",
            audience="client",
            document_type="offer",
            source_fields=json.dumps(["identity.product_name"]),
            variables=json.dumps(
                [
                    {
                        "key": "product_name",
                        "source_field": "identity.product_name",
                        "required": True,
                        "format": "plain_text",
                        "missing_behavior": "block_rendering",
                    }
                ]
            ),
            template_text="{{product_name}}",
            conditions=json.dumps({}),
            approval_status="approved",
            version="1.0.0",
            owner_role="manager",
            reviewer_role="manager",
            snapshot_policy=json.dumps({"preserve_rendered_text": True}),
        )
        quote = Quotes(
            id=9001,
            code="Q-9001",
            intake_id=None,
            intake_code=None,
            client_id=1,
            client_name="Client",
            contact_person="User",
            status="draft",
            version=1,
            valid_until="2026-12-31",
            line_items=json.dumps({"product_definition": {"name": "Test"}}),
            subtotal=100.0,
            discount=0.0,
            discount_pct=0.0,
            total_before_vat=100.0,
            vat=19.0,
            grand_total=119.0,
            margin_pct=10.0,
            notes="seed",
            assigned_to="tester",
        )
        session.add(block)
        session.add(quote)
        await session.commit()


async def _count_rendered_snapshots(db_fixture) -> int:
    async with db_fixture.session_maker() as session:
        return (await session.execute(select(func.count(RenderedOutputSnapshot.id)))).scalar() or 0


def test_storage_upload_url_requires_storage_upload_url(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/storage/upload-url",
        json_body={"bucket_name": "valid-bucket", "object_key": "a.pdf"},
    )
    _assert_permission_denied(response, "storage.upload_url")


def test_storage_rename_requires_storage_rename(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/storage/rename-object",
        json_body={
            "bucket_name": "valid-bucket",
            "source_key": "a.pdf",
            "target_key": "b.pdf",
            "overwrite_key": True,
        },
    )
    _assert_permission_denied(response, "storage.rename")


def test_storage_delete_requires_storage_delete(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="DELETE",
        path="/api/v1/storage/delete-object",
        json_body={
            "bucket_name": "valid-bucket",
            "object_key": "a.pdf",
        },
    )
    _assert_permission_denied(response, "storage.delete")


def test_storage_download_url_requires_storage_download_url(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/storage/download-url",
        json_body={"bucket_name": "valid-bucket", "object_key": "a.pdf"},
    )
    _assert_permission_denied(response, "storage.download_url")


def test_quote_snapshot_approve_requires_manage_permission(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/entities/quotes/1/output-snapshots/1/approve",
        json_body={},
    )
    _assert_permission_denied(response, "quote_output_snapshot.manage")


def test_quote_snapshot_create_requires_manage_permission(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/entities/quotes/1/output-snapshots",
        json_body={"source": "quote_output_composition_preview", "initial_status": "draft"},
    )
    _assert_permission_denied(response, "quote_output_snapshot.manage")


def test_quote_snapshot_submit_review_requires_manage_permission(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/entities/quotes/1/output-snapshots/1/submit-review",
        json_body={},
    )
    _assert_permission_denied(response, "quote_output_snapshot.manage")


def test_quote_snapshot_archive_requires_manage_permission(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/entities/quotes/1/output-snapshots/1/archive",
        json_body={},
    )
    _assert_permission_denied(response, "quote_output_snapshot.manage")


def test_quote_snapshot_reject_requires_manage_permission(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/entities/quotes/1/output-snapshots/1/reject",
        json_body={"reason": "test"},
    )
    _assert_permission_denied(response, "quote_output_snapshot.manage")


def test_quote_snapshot_supersede_requires_manage_permission(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/entities/quotes/1/output-snapshots/1/supersede",
        json_body={"new_snapshot_id": 2},
    )
    _assert_permission_denied(response, "quote_output_snapshot.manage")


def test_quote_pdf_generate_requires_quote_export_pdf(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/entities/quotes/1/pdf/generate",
        json_body={},
    )
    _assert_permission_denied(response, "quote.export_pdf")


def test_operator_task_action_requires_execution_task_start(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/operator/task-action",
        json_body={
            "order_id": 1,
            "task_id": "T1",
            "action": "start",
        },
    )
    _assert_permission_denied(response, "operator.task_action")


def test_workcenter_rates_create_requires_manage_permission(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="manager",
        method="POST",
        path="/api/admin/workcenter-rates",
        json_body={
            "code": "CUT-LASER",
            "label": "Cut Laser",
            "rate_per_hour": 100.0,
            "status": "active",
            "currency": "RON",
        },
    )
    _assert_permission_denied(response, "workcenter_rates.manage")


def test_workcenter_rates_patch_requires_manage_permission(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="manager",
        method="PATCH",
        path="/api/admin/workcenter-rates/CUT-LASER",
        json_body={"rate_per_hour": 120.0},
    )
    _assert_permission_denied(response, "workcenter_rates.manage")


def test_output_block_snapshot_create_requires_permission_and_creates_no_row(db_fixture):
    db_fixture.run(_seed_output_block_and_quote(db_fixture))
    before = db_fixture.run(_count_rendered_snapshots(db_fixture))

    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/product-system/output-blocks/snapshots",
        json_body={
            "block_ids": ["perm-gate-ob-1"],
            "context": "quote_snapshot",
            "source_payload": {"identity": {"product_name": "Gate Test"}},
            "document_type": "offer",
            "audience": "client",
            "snapshot_purpose": "gate_test",
            "target_type": "quote",
            "target_id": 9001,
        },
    )

    after = db_fixture.run(_count_rendered_snapshots(db_fixture))
    _assert_permission_denied(response, "output_blocks.snapshot_create")
    assert before == after


def test_aihub_keeps_aihub_execute_gate(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="POST",
        path="/api/v1/aihub/gentxt",
        json_body={
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
        },
    )
    _assert_permission_denied(response, "aihub.execute")
