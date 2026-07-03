"""Intake V3 printed artwork / policromie layer finish — extends native layer_finish_assignments."""

from __future__ import annotations

import pytest

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_PRINTED_ARTWORK_CONTOUR_DECISION,
    BLOCKER_MISSING_PRINTED_ARTWORK_PRINT_METHOD,
    BLOCKER_UNCONFIRMED_PRINTED_ARTWORK,
)
from schemas.intake_v3 import IntakeV3LayerFinishAssignment, IntakeV3PrintedArtworkFinishSpec
from services.intake_v3_layer_finish_assignment_service import (
    is_artwork_role,
    layer_requires_finish,
    validate_layer_finish_assignment_entry,
)
from tests.test_intake_v3_layer_finish_assignments import (
    _backing_layer_assignment,
    _confirm_layers,
    _face_layer_assignment,
    _patch_layer_finishes,
    _return_layer_assignment,
    _seed_and_upload,
)


def _artwork_layer_assignment(layer_key: str = "Emblema", *, confirmed: bool = True) -> dict:
    return {
        "layer_key": layer_key,
        "layer_name": layer_key,
        "confirmed_role": "printed_artwork",
        "finish_target_type": "printed_artwork",
        "enabled": True,
        "is_confirmed": confirmed,
        "printed_artwork_finish": {
            "enabled": True,
            "print_method": "printed_vinyl",
            "media_family": "Printed vinyl",
            "media_code": "PV-651",
            "laminate_enabled": True,
            "laminate_type": "gloss",
            "contour_cut": True,
            "white_ink": False,
            "white_backing": True,
            "area_sqm": 0.42,
            "waste_percent": 10,
            "notes": "Emblema policromie",
            "is_confirmed": confirmed,
        },
    }




class TestPrintedArtworkLayerFinishRules:
    def test_artwork_roles_require_finish(self):
        assert is_artwork_role("printed_artwork") is True
        assert layer_requires_finish("printed_artwork") is True
        assert layer_requires_finish("inner_hole") is False

    def test_pending_artwork_validation(self):
        assignment = IntakeV3LayerFinishAssignment(
            layer_key="Emblema",
            layer_name="Emblema",
            confirmed_role="printed_artwork",
            finish_target_type="printed_artwork",
            enabled=True,
            is_confirmed=False,
            printed_artwork_finish=IntakeV3PrintedArtworkFinishSpec(enabled=True),
        )
        codes = {item.code for item in validate_layer_finish_assignment_entry(assignment)}
        assert BLOCKER_MISSING_PRINTED_ARTWORK_PRINT_METHOD in codes
        assert BLOCKER_UNCONFIRMED_PRINTED_ARTWORK in codes

    def test_confirmed_artwork_passes_validation(self):
        assignment = IntakeV3LayerFinishAssignment.model_validate(_artwork_layer_assignment("Emblema"))
        assert not validate_layer_finish_assignment_entry(assignment)

    def test_laminate_enabled_requires_type(self):
        assignment = IntakeV3LayerFinishAssignment.model_validate(
            {
                **_artwork_layer_assignment("Logo", confirmed=False),
                "printed_artwork_finish": {
                    "enabled": True,
                    "print_method": "uv_print",
                    "laminate_enabled": True,
                    "laminate_type": None,
                    "contour_cut": False,
                    "is_confirmed": False,
                },
            }
        )
        codes = {item.code for item in validate_layer_finish_assignment_entry(assignment)}
        assert "MISSING_PRINTED_ARTWORK_LAMINATE_TYPE" in codes

    def test_contour_decision_required(self):
        assignment = IntakeV3LayerFinishAssignment.model_validate(
            {
                **_artwork_layer_assignment("Logo", confirmed=False),
                "printed_artwork_finish": {
                    "enabled": True,
                    "print_method": "printed_vinyl",
                    "laminate_enabled": False,
                    "contour_cut": None,
                    "is_confirmed": False,
                },
            }
        )
        codes = {item.code for item in validate_layer_finish_assignment_entry(assignment)}
        assert BLOCKER_MISSING_PRINTED_ARTWORK_CONTOUR_DECISION in codes


class TestPrintedArtworkLayerFinishHttp:
    @pytest.mark.asyncio
    async def test_patch_persists_printed_artwork_finish(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)

        auth_client.put(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
            json={
                "layers": [
                    {"layer_key": "LITERE", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
                    {"layer_key": "SPATE", "confirmed_role": "backing", "confirmation_state": "confirmed"},
                    {"layer_key": "CANT", "confirmed_role": "return", "confirmation_state": "confirmed"},
                    {"layer_key": "GOLURI", "confirmed_role": "inner_hole", "confirmation_state": "confirmed"},
                    {"layer_key": "UNKNOWN", "confirmed_role": "ignore", "confirmation_state": "ignored"},
                ]
            },
        )

        artwork = _artwork_layer_assignment("LITERE")
        artwork["layer_name"] = "Emblema"
        assignments = [
            artwork,
            _return_layer_assignment("CANT"),
            _backing_layer_assignment("SPATE"),
        ]
        response = _patch_layer_finishes(auth_client, workspace_id, assignments)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["summary"]["layer_finish_assignment_status"] == "complete"
        preview_items = body["summary"]["preview_items"]
        artwork_item = next(item for item in preview_items if item["finish_target_type"] == "printed_artwork")
        assert artwork_item["print_method"] == "printed_vinyl"
        assert artwork_item["layer_name"] == "Emblema"

        workspace = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        layer_preview = workspace["preview"]["finish_summary"]["layer_finish_preview"]
        assert any(item.get("print_method") == "printed_vinyl" for item in layer_preview)

    @pytest.mark.asyncio
    async def test_pending_artwork_blocks_patch(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        auth_client.put(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
            json={
                "layers": [
                    {"layer_key": "LITERE", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
                    {"layer_key": "SPATE", "confirmed_role": "backing", "confirmation_state": "confirmed"},
                    {"layer_key": "CANT", "confirmed_role": "return", "confirmation_state": "confirmed"},
                    {"layer_key": "GOLURI", "confirmed_role": "inner_hole", "confirmation_state": "confirmed"},
                    {"layer_key": "UNKNOWN", "confirmed_role": "ignore", "confirmation_state": "ignored"},
                ]
            },
        )
        pending = _artwork_layer_assignment("LITERE", confirmed=False)
        response = _patch_layer_finishes(auth_client, workspace_id, [pending])
        assert response.status_code == 422, response.text

    @pytest.mark.asyncio
    async def test_old_workspace_without_artwork_still_works(self, auth_client):
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
