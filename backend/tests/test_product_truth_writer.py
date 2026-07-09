from __future__ import annotations

import json

import pytest
from sqlalchemy import delete, select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.product_truth_writer_dry_run_service import compute_payload_hash


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
SUCCESS_WORKSPACE_ID = "product-truth-writer-success"
SUCCESS_WORKSPACE_CODE = "IV6-PRODUCT-TRUTH-WRITER-SUCCESS"
MIXED_WORKSPACE_ID = "product-truth-writer-mixed"
MIXED_WORKSPACE_CODE = "IV6-PRODUCT-TRUTH-WRITER-MIXED"
UNKNOWN_WORKSPACE_ID = "product-truth-writer-unknown"
UNKNOWN_WORKSPACE_CODE = "IV6-PRODUCT-TRUTH-WRITER-UNKNOWN"


def _complete_payload() -> dict:
    return {
        "product_binding": {"template_code": ROOT},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "face-1",
                    "layer_id": "face-1",
                    "layer_name": "face 1",
                    "auto_role": "face",
                    "auto_confidence": "high",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
            "warnings": [],
        },
        "svg": {
            "selected_layer_refs": [
                {
                    "layer_id": "face-1",
                    "role": "vector_litere",
                    "source": "operator_confirmed_layer_role",
                    "confirmed": True,
                }
            ]
        },
        "finish_setup": {
            "finish_target": "face",
            "confirmed": True,
            "artwork_finishes": [
                {
                    "layer_key": "logo-left",
                    "print_required": True,
                    "lamination_required": False,
                },
                {
                    "layer_key": "logo-right",
                    "print_required": False,
                    "lamination_required": True,
                },
            ],
            "mounting_scope": "mounting_included",
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
            "support_required": "yes",
        },
        "product_truth": {
            "components": {
                "return_cant": {
                    "version": "v1",
                    "instances": {
                        "existing": {
                            "instance_key": "existing",
                            "confirmation_state": "blocked",
                        }
                    },
                }
            }
        },
    }


def _mixed_payload() -> dict:
    payload = _complete_payload()
    payload["finish_setup"]["artwork_finishes"] = [
        {
            "layer_key": "logo-left",
            "print_required": True,
            "lamination_required": False,
        },
        {
            "layer_key": "logo-right",
            "execution_type": "print_laminate",
        },
    ]
    payload["finish_setup"].pop("support_type")
    payload["finish_setup"]["support_source"] = "detected_svg"
    return payload


async def _seed_workspace(db_fixture, *, workspace_id: str, workspace_code: str, payload: dict, status: str) -> None:
    async with db_fixture.session_maker() as session:
        await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id))
        await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == workspace_code))
        session.add(
            IntakeV6WorkspaceRecord(
                id=workspace_id,
                workspace_code=workspace_code,
                title=f"{workspace_code} workspace",
                template_code=ROOT,
                status=status,
                payload_json=json.dumps(payload),
                readiness_status=status,
                created_by_user_id="test-user-id",
                updated_by_user_id="test-user-id",
            )
        )
        await session.commit()


async def _read_payload(db_fixture, workspace_id: str) -> dict | None:
    async with db_fixture.session_maker() as session:
        result = await session.execute(
            select(IntakeV6WorkspaceRecord.payload_json).where(IntakeV6WorkspaceRecord.id == workspace_id)
        )
        payload_json = result.scalar_one_or_none()
    return json.loads(payload_json) if payload_json else None


def _flatten(value, prefix: str = "") -> dict[str, object]:
    flattened: dict[str, object] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(_flatten(child, child_prefix))
        return flattened
    flattened[prefix] = value
    return flattened


def _changed_paths(before: dict, after: dict) -> list[str]:
    before_flat = _flatten(before)
    after_flat = _flatten(after)
    return sorted(
        key
        for key in (set(before_flat) | set(after_flat))
        if before_flat.get(key) != after_flat.get(key)
    )


@pytest.fixture
def seeded_workspaces(db_fixture):
    db_fixture.run(
        _seed_workspace(
            db_fixture,
            workspace_id=SUCCESS_WORKSPACE_ID,
            workspace_code=SUCCESS_WORKSPACE_CODE,
            payload=_complete_payload(),
            status="ready_for_quote_preview",
        )
    )
    db_fixture.run(
        _seed_workspace(
            db_fixture,
            workspace_id=MIXED_WORKSPACE_ID,
            workspace_code=MIXED_WORKSPACE_CODE,
            payload=_mixed_payload(),
            status="collecting_data",
        )
    )
    db_fixture.run(
        _seed_workspace(
            db_fixture,
            workspace_id=UNKNOWN_WORKSPACE_ID,
            workspace_code=UNKNOWN_WORKSPACE_CODE,
            payload=_complete_payload(),
            status="ready_for_quote_preview",
        )
    )
    return True


def _post(auth_client, workspace_id: str, body: dict):
    return auth_client.post(f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/promote", json=body)


def _request_for(workspace_code: str, payload: dict, **overrides: object) -> dict:
    body = {
        "promotion_confirmed": True,
        "expected_workspace_code": workspace_code,
        "expected_root_template_code": ROOT,
        "expected_product_binding_template_code": ROOT,
        "planner_version": "v1",
        "payload_hash_basis": compute_payload_hash(payload),
        "actor": {
            "actor_id": "operator-123",
            "actor_email": "operator@example.com",
            "actor_role": "operator",
            "actor_label": "Operator Review",
        },
    }
    body.update(overrides)
    return body


def test_writer_promotes_requested_entries_only_into_confirmed_snapshot(auth_client, seeded_workspaces, db_fixture):
    payload = _complete_payload()
    before = db_fixture.run(_read_payload(db_fixture, SUCCESS_WORKSPACE_ID))
    request = _request_for(
        SUCCESS_WORKSPACE_CODE,
        payload,
        requested_entry_keys=[
            "finish.finish_target",
            "finish.print_required:layer_key:logo-left",
            "svg.selected_layer_refs[]:layer_id:face-1",
        ],
    )

    response = _post(auth_client, SUCCESS_WORKSPACE_ID, request)
    after = db_fixture.run(_read_payload(db_fixture, SUCCESS_WORKSPACE_ID))

    assert response.status_code == 200
    body = response.json()
    assert body["write_performed"] is True
    assert body["idempotent_replay"] is False
    assert body["refused_entries"] == []
    assert {item["entry_key"] for item in body["promoted_entries"]} == {
        "finish.finish_target",
        "finish.print_required:layer_key:logo-left",
        "svg.selected_layer_refs[]:layer_id:face-1",
    }
    changed_paths = _changed_paths(before, after)
    snapshot = after["product_truth"]["confirmed_snapshot_v1"]
    assert snapshot["metadata"]["target_path"] == "payload_json.product_truth.confirmed_snapshot_v1"
    assert snapshot["entries"]["finish"]["finish_target"]["value"] == "face"
    assert snapshot["entries"]["finish"]["print_required"]["layer_key:logo-left"]["value"] is True
    assert snapshot["entries"]["svg"]["selected_layer_refs[]"]["layer_id:face-1"]["value"]["layer_id"] == "face-1"
    assert after["product_truth"]["components"]["return_cant"] == before["product_truth"]["components"]["return_cant"]
    assert "confirmed_snapshot_v1" not in before.get("product_truth", {})
    assert len(snapshot["audit_trail"]) == 1
    assert body["confirmed_snapshot_hash_before"] != body["confirmed_snapshot_hash_after"]
    assert body["return_cant_bridge_hash_before"] == body["return_cant_bridge_hash_after"]
    assert all(value is False for value in body["downstream_write_intent"].values())
    assert changed_paths
    assert all(path.startswith("product_truth.confirmed_snapshot_v1") for path in changed_paths)


def test_writer_refuses_atomically_when_requested_scope_contains_blocked_entry(auth_client, seeded_workspaces, db_fixture):
    payload = _mixed_payload()
    before = db_fixture.run(_read_payload(db_fixture, MIXED_WORKSPACE_ID))
    request = _request_for(
        MIXED_WORKSPACE_CODE,
        payload,
        requested_entry_keys=[
            "finish.finish_target",
            "support.support_type",
        ],
    )

    response = _post(auth_client, MIXED_WORKSPACE_ID, request)
    after = db_fixture.run(_read_payload(db_fixture, MIXED_WORKSPACE_ID))

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "product_truth_promotion_refused"
    assert detail["write_performed"] is False
    assert detail["idempotent_replay"] is False
    assert detail["promoted_entries"] == []
    assert {item["entry_key"] for item in detail["refused_entries"]} == {"support.support_type"}
    assert before == after
    assert detail["payload_hash_before"] == detail["payload_hash_after"]
    assert detail["confirmed_snapshot_hash_before"] == detail["confirmed_snapshot_hash_after"]
    assert detail["return_cant_bridge_hash_before"] == detail["return_cant_bridge_hash_after"]


def test_writer_replay_is_idempotent_and_does_not_append_audit_or_rewrite_payload(auth_client, seeded_workspaces, db_fixture):
    payload = _complete_payload()
    request = _request_for(
        SUCCESS_WORKSPACE_CODE,
        payload,
        requested_entry_keys=["finish.finish_target"],
    )

    first = _post(auth_client, SUCCESS_WORKSPACE_ID, request)
    after_first = db_fixture.run(_read_payload(db_fixture, SUCCESS_WORKSPACE_ID))
    second = _post(auth_client, SUCCESS_WORKSPACE_ID, request)
    after_second = db_fixture.run(_read_payload(db_fixture, SUCCESS_WORKSPACE_ID))

    assert first.status_code == 200
    assert second.status_code == 200
    first_body = first.json()
    second_body = second.json()
    assert first_body["write_performed"] is True
    assert first_body["idempotent_replay"] is False
    assert second_body["write_performed"] is False
    assert second_body["idempotent_replay"] is True
    assert after_first == after_second
    assert len(after_second["product_truth"]["confirmed_snapshot_v1"]["audit_trail"]) == 1
    assert second_body["payload_hash_before"] == second_body["payload_hash_after"]
    assert second_body["confirmed_snapshot_hash_before"] == second_body["confirmed_snapshot_hash_after"]
    assert second_body["return_cant_bridge_hash_before"] == second_body["return_cant_bridge_hash_after"]


def test_writer_refuses_unknown_requested_entry_key_without_mutation(auth_client, seeded_workspaces, db_fixture):
    payload = _complete_payload()
    before = db_fixture.run(_read_payload(db_fixture, UNKNOWN_WORKSPACE_ID))
    request = _request_for(
        UNKNOWN_WORKSPACE_CODE,
        payload,
        requested_entry_keys=[
            "finish.finish_target",
            "unknown.product.truth.key",
        ],
    )

    response = _post(auth_client, UNKNOWN_WORKSPACE_ID, request)
    after = db_fixture.run(_read_payload(db_fixture, UNKNOWN_WORKSPACE_ID))

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "product_truth_promotion_refused"
    assert detail["write_performed"] is False
    assert detail["idempotent_replay"] is False
    assert detail["promoted_entries"] == []
    assert [item["entry_key"] for item in detail["refused_entries"]] == ["unknown.product.truth.key"]
    assert before == after
    assert detail["payload_hash_before"] == detail["payload_hash_after"]
    assert detail["confirmed_snapshot_hash_before"] == detail["confirmed_snapshot_hash_after"]
    assert detail["return_cant_bridge_hash_before"] == detail["return_cant_bridge_hash_after"]
    assert all(value is False for value in detail["downstream_write_intent"].values())
