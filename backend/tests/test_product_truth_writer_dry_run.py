from __future__ import annotations

import json

import pytest
from sqlalchemy import delete, select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.product_truth_writer_dry_run_service import compute_payload_hash


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
SUCCESS_WORKSPACE_ID = "product-truth-dry-run-success"
SUCCESS_WORKSPACE_CODE = "IV6-PRODUCT-TRUTH-DRY-RUN-SUCCESS"
BLOCKED_WORKSPACE_ID = "product-truth-dry-run-blocked"
BLOCKED_WORKSPACE_CODE = "IV6-PRODUCT-TRUTH-DRY-RUN-BLOCKED"
MIXED_WORKSPACE_ID = "product-truth-dry-run-mixed"
MIXED_WORKSPACE_CODE = "IV6-PRODUCT-TRUTH-DRY-RUN-MIXED"


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


def _blocked_payload() -> dict:
    payload = _complete_payload()
    payload.pop("svg")
    payload["finish_setup"].pop("finish_target")
    payload["finish_setup"]["artwork_finishes"] = [{"layer_key": "logo-left", "execution_type": "print_laminate"}]
    payload["finish_setup"].pop("mounting_scope")
    payload["finish_setup"].pop("support_type")
    payload["finish_setup"]["support_source"] = "detected_svg"
    return payload


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


async def _read_payload_json(db_fixture, workspace_id: str) -> str | None:
    async with db_fixture.session_maker() as session:
        result = await session.execute(
            select(IntakeV6WorkspaceRecord.payload_json).where(IntakeV6WorkspaceRecord.id == workspace_id)
        )
        return result.scalar_one_or_none()


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
            workspace_id=BLOCKED_WORKSPACE_ID,
            workspace_code=BLOCKED_WORKSPACE_CODE,
            payload=_blocked_payload(),
            status="collecting_data",
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
    return True


def _post(auth_client, workspace_id: str, body: dict):
    return auth_client.post(f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth-writer/dry-run", json=body)


def _request_for(workspace_code: str, payload: dict, **overrides: object) -> dict:
    body = {
        "dry_run_only": True,
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


def test_success_eligible_entries_produce_would_write_and_no_payload_mutation(auth_client, seeded_workspaces, db_fixture):
    payload = _complete_payload()
    request = _request_for(
        SUCCESS_WORKSPACE_CODE,
        payload,
        requested_entry_keys=[
            "finish.finish_target",
            "finish.print_required:layer_key:logo-left",
            "svg.selected_layer_refs[]:layer_id:face-1",
        ],
    )

    before = db_fixture.run(_read_payload_json(db_fixture, SUCCESS_WORKSPACE_ID))
    response = _post(auth_client, SUCCESS_WORKSPACE_ID, request)
    after = db_fixture.run(_read_payload_json(db_fixture, SUCCESS_WORKSPACE_ID))

    assert response.status_code == 200
    assert before == after
    body = response.json()
    assert body["read_only"] is True
    assert body["dry_run"] is True
    assert body["target_path"] == "payload_json.product_truth.confirmed_snapshot_v1"
    assert body["refused_entries"] == []
    assert {item["action"] for item in body["proposed_mutations"]} == {"would_write"}
    assert {item["entry_key"] for item in body["proposed_mutations"]} == {
        "finish.finish_target",
        "finish.print_required:layer_key:logo-left",
        "svg.selected_layer_refs[]:layer_id:face-1",
    }
    assert all(
        item["target_path"].startswith("payload_json.product_truth.confirmed_snapshot_v1")
        for item in body["proposed_mutations"]
    )
    assert all("components.return_cant" not in item["target_path"] for item in body["proposed_mutations"])
    assert body["no_mutation_proof"]["payload_hash_unchanged"] is True
    assert body["no_mutation_proof"]["planner_hash_unchanged"] is True
    assert body["no_mutation_proof"]["product_truth_target_mutated"] is False
    assert body["no_mutation_proof"]["return_cant_bridge_mutated"] is False
    assert body["no_mutation_proof"]["downstream_mutated"] is False
    assert all(value is False for value in body["downstream_write_intent"].values())


def test_zero_eligible_many_blocked_produces_only_refused_entries(auth_client, seeded_workspaces):
    payload = _blocked_payload()
    request = _request_for(BLOCKED_WORKSPACE_CODE, payload)

    response = _post(auth_client, BLOCKED_WORKSPACE_ID, request)

    assert response.status_code == 200
    body = response.json()
    assert body["proposed_mutations"] == []
    assert body["promotion_hash"] is None
    assert body["refused_entries"]
    assert {item["action"] for item in body["refused_entries"]} == {"refused"}
    assert all(item["refusal_is_blocking"] is True for item in body["refused_entries"])
    assert {item["entry_key"] for item in body["refused_entries"]} >= {
        "svg.selected_layer_refs[]",
        "finish.finish_target",
        "mounting.mounting_scope",
        "support.support_type",
    }


def test_blocked_requested_entries_never_produce_proposed_mutations(auth_client, seeded_workspaces):
    payload = _blocked_payload()
    request = _request_for(
        BLOCKED_WORKSPACE_CODE,
        payload,
        requested_entry_keys=["support.support_type"],
    )

    response = _post(auth_client, BLOCKED_WORKSPACE_ID, request)

    assert response.status_code == 200
    body = response.json()
    assert body["proposed_mutations"] == []
    assert [item["entry_key"] for item in body["refused_entries"]] == ["support.support_type"]


def test_mixed_visibility_shows_both_lists_and_fail_closed_writer_policy(auth_client, seeded_workspaces):
    payload = _mixed_payload()
    request = _request_for(MIXED_WORKSPACE_CODE, payload)

    response = _post(auth_client, MIXED_WORKSPACE_ID, request)

    assert response.status_code == 200
    body = response.json()
    assert body["proposed_mutations"]
    assert body["refused_entries"]
    assert body["writer_real_atomic_policy"] == "fail_closed_if_request_contains_blocked"
    assert any(item["field_key"] == "support.support_type" for item in body["refused_entries"])
    assert any(item["field_key"] == "finish.finish_target" for item in body["proposed_mutations"])


def test_missing_workspace_returns_404(auth_client):
    request = _request_for("IV6-MISSING", _complete_payload())
    response = _post(auth_client, "missing-product-truth-dry-run-workspace", request)

    assert response.status_code == 404


def test_template_mismatch_is_controlled_failure(auth_client, seeded_workspaces):
    payload = _complete_payload()
    request = _request_for(
        SUCCESS_WORKSPACE_CODE,
        payload,
        expected_root_template_code="TPL-WRONG-TEMPLATE",
    )

    response = _post(auth_client, SUCCESS_WORKSPACE_ID, request)

    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "root_template_code_mismatch"


def test_repeated_dry_run_is_deterministic(auth_client, seeded_workspaces):
    payload = _complete_payload()
    request = _request_for(SUCCESS_WORKSPACE_CODE, payload)

    first = _post(auth_client, SUCCESS_WORKSPACE_ID, request)
    second = _post(auth_client, SUCCESS_WORKSPACE_ID, request)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()