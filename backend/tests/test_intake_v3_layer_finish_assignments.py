"""Intake V3 native layer finish assignments — payload only."""

from __future__ import annotations

import pytest

from data_models.intake_v3_contracts import (
    BLOCKER_UNCONFIRMED_LAYER_FINISH,
    BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT,
)
from services.intake_v3_layer_finish_assignment_service import (
    apply_layer_finish_assignments_to_payload,
    draft_layer_finish_assignments,
    layer_requires_finish,
    summarize_layer_finish_assignments,
    uses_native_layer_finish,
    validate_layer_finish_assignment_entry,
)
from schemas.intake_v3 import (
    BackingFinishSpec,
    FaceFinishSpec,
    IntakeV3ApplyLayerFinishAssignmentsRequest,
    IntakeV3LayerFinishAssignment,
    ReturnFinishSpec,
)
from tests.test_intake_v3_layer_role_confirmation import LAYERED_SVG, _confirm_layers, _seed_and_upload

GLOBAL_FINISH_PATCHES = [
    {"field_path": "finish_assignment.face_finish.finish_type", "value": "oracal_8500"},
    {"field_path": "finish_assignment.face_finish.material", "value": "Oracal 8500"},
    {"field_path": "finish_assignment.face_finish.color_code", "value": "527"},
    {"field_path": "finish_assignment.face_finish.color_name", "value": "Pastel blue"},
    {"field_path": "finish_assignment.face_finish.roll_width_mm", "value": 1260},
    {"field_path": "finish_assignment.face_finish.confirmed", "value": True},
    {"field_path": "finish_assignment.return_finish.finish_type", "value": "oracal_651"},
    {"field_path": "finish_assignment.return_finish.material", "value": "Oracal 651"},
    {"field_path": "finish_assignment.return_finish.color_code", "value": "055m"},
    {"field_path": "finish_assignment.return_finish.depth_mm", "value": 60},
    {"field_path": "finish_assignment.return_finish.confirmed", "value": True},
    {"field_path": "finish_assignment.backing_finish.material", "value": "Forex"},
    {"field_path": "finish_assignment.backing_finish.thickness_mm", "value": 10},
    {"field_path": "finish_assignment.backing_finish.confirmed", "value": True},
]


def _apply_global_finish(auth_client, workspace_id: str) -> None:
    response = auth_client.patch(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/fields",
        json={"patches": GLOBAL_FINISH_PATCHES, "regenerate_preview": False},
    )
    assert response.status_code == 200


def _face_layer_assignment(layer_key: str = "LITERE", *, confirmed: bool = True) -> dict:
    return {
        "layer_key": layer_key,
        "layer_name": layer_key,
        "confirmed_role": "face",
        "finish_target_type": "face",
        "face_finish": {
            "finish_type": "oracal_8500",
            "material_code": "Oracal 8500",
            "color_code": "527",
            "color_name": "Pastel blue",
            "face_vinyl_roll_width_mm": 1260,
            "confirmed": confirmed,
        },
        "is_confirmed": confirmed,
        "enabled": True,
    }


def _return_layer_assignment(layer_key: str = "CANT", *, confirmed: bool = True) -> dict:
    return {
        "layer_key": layer_key,
        "layer_name": layer_key,
        "confirmed_role": "return",
        "finish_target_type": "return",
        "return_finish": {
            "finish_type": "oracal_651",
            "material_code": "Oracal 651",
            "color_code": "055m",
            "color_name": "Int",
            "return_depth_mm": 60,
            "confirmed": confirmed,
        },
        "is_confirmed": confirmed,
        "enabled": True,
    }


def _backing_layer_assignment(layer_key: str = "SPATE", *, confirmed: bool = True) -> dict:
    return {
        "layer_key": layer_key,
        "layer_name": layer_key,
        "confirmed_role": "backing",
        "finish_target_type": "backing",
        "backing_finish": {
            "material": "Forex",
            "thickness_mm": 10,
            "confirmed": confirmed,
        },
        "is_confirmed": confirmed,
        "enabled": True,
    }


def _patch_layer_finishes(auth_client, workspace_id: str, assignments: list[dict]) -> dict:
    response = auth_client.patch(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments",
        json={"layer_finish_assignments": assignments, "regenerate_preview": True},
    )
    return response


class TestLayerFinishAssignmentRules:
    def test_layer_requires_finish_respects_role(self):
        assert layer_requires_finish("face") is True
        assert layer_requires_finish("inner_hole") is False
        assert layer_requires_finish("ignore") is False

    def test_free_layer_names_supported(self):
        assignment = IntakeV3LayerFinishAssignment(
            layer_key="Emblema",
            layer_name="Emblema",
            confirmed_role="face",
            finish_target_type="face",
            face_finish=FaceFinishSpec(
                finish_type="oracal_8500",
                color_code="527",
                face_vinyl_roll_width_mm=1260,
                confirmed=True,
            ),
            is_confirmed=True,
        )
        assert not validate_layer_finish_assignment_entry(assignment)


class TestLayerFinishAssignmentsHttp:
    @pytest.mark.asyncio
    async def test_draft_targets_from_layer_roles(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)

        targets = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments/targets",
        )
        assert targets.status_code == 200, targets.text
        body = targets.json()
        assert body["target_count"] >= 3
        by_key = {item["layer_key"]: item for item in body["targets"]}
        assert by_key["LITERE"]["requires_finish"] is True
        assert by_key["GOLURI"]["requires_finish"] is False

        state = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments",
        )
        assert state.status_code == 200, state.text
        draft = state.json()
        assert len(draft["layer_finish_assignments"]) >= 3
        assert uses_native_layer_finish({"layer_finish_assignments": []}) is False

    @pytest.mark.asyncio
    async def test_patch_persists_and_syncs_global_finish(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)

        response = _patch_layer_finishes(
            auth_client,
            workspace_id,
            [
                _face_layer_assignment("LITERE"),
                _return_layer_assignment("CANT"),
                _backing_layer_assignment("SPATE"),
            ],
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["summary"]["layer_finish_assignment_status"] == "complete"
        assert body["validation"]["is_valid"] is True

        workspace = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()
        payload = workspace["payload"]
        assert uses_native_layer_finish(payload) is True
        assert payload["finish_assignment"]["face_finish"]["color_code"] == "527"
        assert payload["finish_assignment"]["return_finish"]["return_depth_mm"] == 60

    @pytest.mark.asyncio
    async def test_unconfirmed_productive_layer_blocks_readiness(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)

        response = _patch_layer_finishes(
            auth_client,
            workspace_id,
            [
                _face_layer_assignment("LITERE", confirmed=False),
                _return_layer_assignment("CANT", confirmed=False),
                _backing_layer_assignment("SPATE", confirmed=False),
            ],
        )
        assert response.status_code == 422, response.text

    @pytest.mark.asyncio
    async def test_backwards_compat_global_finish_without_layer_assignments(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        _apply_global_finish(auth_client, workspace_id)

        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview")
        assert preview.status_code == 200, preview.text
        finish_summary = preview.json()["preview"]["finish_summary"]
        assert finish_summary["face_vinyl_roll_width_mm"] == 1260

        workspace = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()
        assert uses_native_layer_finish(workspace["payload"]) is False

    @pytest.mark.asyncio
    async def test_technical_layer_does_not_require_finish(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        assignments = draft_layer_finish_assignments(
            auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()["payload"]
        )
        hole = next(a for a in assignments if a.layer_key == "GOLURI")
        assert layer_requires_finish(hole.confirmed_role) is False

    @pytest.mark.asyncio
    async def test_pending_face_layer_validation(self):
        assignment = IntakeV3LayerFinishAssignment(
            layer_key="Logo",
            layer_name="Logo",
            confirmed_role="face",
            finish_target_type="face",
            enabled=True,
            is_confirmed=False,
        )
        codes = [item.code for item in validate_layer_finish_assignment_entry(assignment)]
        assert BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT in codes

    @pytest.mark.asyncio
    async def test_apply_service_sets_status(self):
        payload = {
            "layer_role_confirmation_snapshot": {
                "schema_version": "layer_role_confirmation_v1",
                "confirmation_status": "complete",
                "layers": [
                    {
                        "layer_key": "LITERE",
                        "layer_name": "LITERE",
                        "confirmed_role": "face",
                        "confirmation_state": "confirmed",
                    }
                ],
            }
        }
        request = IntakeV3ApplyLayerFinishAssignmentsRequest(
            layer_finish_assignments=[
                IntakeV3LayerFinishAssignment.model_validate(_face_layer_assignment("LITERE"))
            ]
        )
        updated, summary = apply_layer_finish_assignments_to_payload(payload, request, confirmed_by="user-1")
        assert updated["layer_finish_assignment_status"] == "complete"
        assert summary.confirmed_count == 1
