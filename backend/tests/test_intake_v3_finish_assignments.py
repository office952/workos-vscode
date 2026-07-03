"""Intake V3 finish assignment per letter / group — payload only, no quote/order writes."""

from __future__ import annotations

from services.intake_v3_finish_assignment_service import resolve_effective_finish_for_letter

VALID_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100mm" height="50mm">
  <g id="letters">
    <path id="letter-a" d="M10 40 L20 10 L30 40 Z" fill="#ff0000" stroke="#000000"/>
    <path id="letter-b" d="M40 40 L40 10 L55 10 Q60 10 60 20 Q60 30 55 30 L40 30" fill="#00ff00"/>
  </g>
</svg>"""

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "Finish assignment test",
        "request_code": "FA-TEST-001",
        "job_title": "Finish assignment test",
        "width_mm": 1000,
        "height_mm": 500,
    },
    "product_selection": {"template_code": "TPL-VOLUMETRIC-LETTERS", "pilot_scope": True},
    "material_intent": {"inventory_mutation_allowed": False, "estimate_status": "not_started"},
    "production_handoff": {"preview_only": True},
    "employee_preview_seed": {"non_executable": True, "preview_tasks": []},
}

HUB_CONFIRM_PAYLOAD = {
    "letter_count": 18,
    "cut_contour_count": 27,
    "inner_hole_count": 9,
    "ignored_object_ids": [],
    "operator_notes": "HUB reference — holes are not separate letters.",
    "confirmed": True,
}

GLOBAL_FINISH_PATCHES = [
    {"field_path": "finish_assignment.face_finish.finish_type", "value": "oracal_8500"},
    {"field_path": "finish_assignment.face_finish.material", "value": "Oracal 8500"},
    {"field_path": "finish_assignment.face_finish.color_code", "value": "527"},
    {"field_path": "finish_assignment.face_finish.color_name", "value": "Pastel blue"},
    {"field_path": "finish_assignment.face_finish.roll_width_mm", "value": 1260},
    {"field_path": "finish_assignment.face_finish.confirmed", "value": True},
    {"field_path": "finish_assignment.return_finish.finish_type", "value": "oracal_651"},
    {"field_path": "finish_assignment.return_finish.material", "value": "Oracal 651"},
    {"field_path": "finish_assignment.return_finish.depth_mm", "value": 60},
    {"field_path": "finish_assignment.return_finish.confirmed", "value": True},
    {"field_path": "finish_assignment.backing_finish.material", "value": "Forex"},
    {"field_path": "finish_assignment.backing_finish.thickness_mm", "value": 10},
    {"field_path": "finish_assignment.backing_finish.confirmed", "value": True},
]


def _create_workspace(auth_client, payload: dict | None = None) -> str:
    response = auth_client.post(
        "/api/v1/intake-v3/workspaces",
        json={"title": "Finish assignment test", "payload": payload or MINIMAL_WORKSPACE_PAYLOAD},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _upload_svg(auth_client, workspace_id: str) -> None:
    response = auth_client.post(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/svg",
        files={"file": ("letters.svg", VALID_SVG, "image/svg+xml")},
    )
    assert response.status_code == 200


def _confirm_hub(auth_client, workspace_id: str) -> dict:
    response = auth_client.post(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
        json=HUB_CONFIRM_PAYLOAD,
    )
    assert response.status_code == 200
    return response.json()


def _apply_global_finish(auth_client, workspace_id: str) -> None:
    response = auth_client.patch(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/fields",
        json={"patches": GLOBAL_FINISH_PATCHES, "regenerate_preview": False},
    )
    assert response.status_code == 200


def _patch_finish_assignments(auth_client, workspace_id: str, payload: dict) -> dict:
    return auth_client.patch(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/finish-assignments",
        json=payload,
    )


def _hub_ready_workspace(auth_client) -> str:
    workspace_id = _create_workspace(auth_client)
    _upload_svg(auth_client, workspace_id)
    _confirm_hub(auth_client, workspace_id)
    _apply_global_finish(auth_client, workspace_id)
    return workspace_id


class TestIntakeV3FinishAssignments:
    def test_cannot_assign_before_confirmed_model(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)
        _apply_global_finish(auth_client, workspace_id)

        before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        before_payload = before.json()["payload"]

        response = _patch_finish_assignments(
            auth_client,
            workspace_id,
            {
                "letter_group_finish_assignments": [
                    {
                        "assignment_id": "grp-hub",
                        "label": "HUB",
                        "target_letter_ids": ["L-01"],
                        "face_finish": {"finish_type": "oracal_8500", "color_code": "527"},
                        "enabled": True,
                    }
                ],
                "letter_finish_assignments": [],
            },
        )
        assert response.status_code in {400, 422}

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert after.json()["payload"] == before_payload

    def test_targets_list_from_confirmed_model(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)
        _confirm_hub(auth_client, workspace_id)

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/finish-assignments/targets",
        )
        assert response.status_code == 200
        body = response.json()
        assert body["letter_count"] == 18
        assert len(body["targets"]) == 18
        assert all(target["is_hole"] is False for target in body["targets"])
        assert all(not target["letter_id"].upper().startswith("C-HOLE") for target in body["targets"])

    def test_apply_group_assignment_works(self, auth_client):
        workspace_id = _hub_ready_workspace(auth_client)

        response = _patch_finish_assignments(
            auth_client,
            workspace_id,
            {
                "letter_group_finish_assignments": [
                    {
                        "assignment_id": "grp-hub",
                        "label": "HUB",
                        "target_letter_ids": ["L-01", "L-02", "L-03"],
                        "face_finish": {
                            "finish_type": "oracal_8500",
                            "color_code": "527",
                            "color_name": "Pastel blue",
                        },
                        "enabled": True,
                    }
                ],
                "letter_finish_assignments": [],
            },
        )
        assert response.status_code == 200
        body = response.json()
        payload = body["workspace"]["payload"]
        assert len(payload["letter_group_finish_assignments"]) == 1
        assert payload["finish_assignment_status"] == "group_overrides"
        assert body["summary"]["group_assignment_count"] == 1
        assert body["preview"] is not None
        assert body["preview"]["preview"]["finish_summary"]["finish_variations_present"] is True

    def test_letter_override_wins_over_group(self, auth_client):
        workspace_id = _hub_ready_workspace(auth_client)

        response = _patch_finish_assignments(
            auth_client,
            workspace_id,
            {
                "letter_group_finish_assignments": [
                    {
                        "assignment_id": "grp-hub",
                        "label": "HUB",
                        "target_letter_ids": ["L-01", "L-02", "L-03"],
                        "face_finish": {
                            "finish_type": "oracal_8500",
                            "color_code": "527",
                            "color_name": "Pastel blue",
                        },
                        "enabled": True,
                    }
                ],
                "letter_finish_assignments": [
                    {
                        "assignment_id": "letter-l01",
                        "target_letter_id": "L-01",
                        "face_finish": {
                            "finish_type": "oracal_8500",
                            "color_code": "302",
                            "color_name": "Red",
                        },
                        "enabled": True,
                    }
                ],
            },
        )
        assert response.status_code == 200
        payload = response.json()["workspace"]["payload"]

        l01 = resolve_effective_finish_for_letter(payload, "L-01")
        l02 = resolve_effective_finish_for_letter(payload, "L-02")
        assert l01["face_finish"]["color_code"] == "302"
        assert l02["face_finish"]["color_code"] == "527"

    def test_unknown_letter_id_rejected(self, auth_client):
        workspace_id = _hub_ready_workspace(auth_client)
        before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        before_payload = before.json()["payload"]

        response = _patch_finish_assignments(
            auth_client,
            workspace_id,
            {
                "letter_group_finish_assignments": [
                    {
                        "assignment_id": "grp-bad",
                        "label": "BAD",
                        "target_letter_ids": ["L-999"],
                        "face_finish": {"finish_type": "oracal_8500", "color_code": "527"},
                        "enabled": True,
                    }
                ],
                "letter_finish_assignments": [],
            },
        )
        assert response.status_code in {400, 422}

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert after.json()["payload"] == before_payload

    def test_hole_id_cannot_be_targeted(self, auth_client):
        workspace_id = _hub_ready_workspace(auth_client)
        before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        before_payload = before.json()["payload"]

        response = _patch_finish_assignments(
            auth_client,
            workspace_id,
            {
                "letter_group_finish_assignments": [
                    {
                        "assignment_id": "grp-hole",
                        "label": "HOLE",
                        "target_letter_ids": ["C-HOLE-01"],
                        "face_finish": {"finish_type": "oracal_8500", "color_code": "527"},
                        "enabled": True,
                    }
                ],
                "letter_finish_assignments": [],
            },
        )
        assert response.status_code in {400, 422}
        detail = response.json()["detail"]
        blockers = detail.get("blockers", [])
        assert any("hole_target_forbidden" in item for item in blockers)

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert after.json()["payload"] == before_payload

    def test_wrapped_return_requires_depth(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)
        _confirm_hub(auth_client, workspace_id)

        shallow_finish_patches = [
            patch
            for patch in GLOBAL_FINISH_PATCHES
            if patch["field_path"] != "finish_assignment.return_finish.depth_mm"
        ]
        shallow_finish_patches.append(
            {"field_path": "finish_assignment.return_finish.finish_type", "value": "oracal_651"},
        )
        response_fields = auth_client.patch(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/fields",
            json={"patches": shallow_finish_patches, "regenerate_preview": False},
        )
        assert response_fields.status_code == 200

        response = _patch_finish_assignments(
            auth_client,
            workspace_id,
            {
                "letter_group_finish_assignments": [
                    {
                        "assignment_id": "grp-wrap",
                        "label": "WRAP",
                        "target_letter_ids": ["L-01"],
                        "return_finish": {
                            "finish_type": "oracal_wrapped",
                            "material_code": "Oracal 651",
                        },
                        "enabled": True,
                    }
                ],
                "letter_finish_assignments": [],
            },
        )
        assert response.status_code in {400, 422}
        detail = response.json()["detail"]
        blockers = detail.get("blockers", [])
        assert any("MISSING_RETURN_DEPTH" in item for item in blockers)

    def test_painted_return_disables_return_vinyl(self, auth_client):
        workspace_id = _hub_ready_workspace(auth_client)

        response = _patch_finish_assignments(
            auth_client,
            workspace_id,
            {
                "letter_group_finish_assignments": [
                    {
                        "assignment_id": "grp-paint",
                        "label": "PAINT",
                        "target_letter_ids": ["L-01"],
                        "return_finish": {
                            "finish_type": "painted",
                            "color_code": "9005",
                            "color_name": "Black",
                            "confirmed": True,
                        },
                        "enabled": True,
                    }
                ],
                "letter_finish_assignments": [],
            },
        )
        assert response.status_code == 200
        payload = response.json()["workspace"]["payload"]
        effective = resolve_effective_finish_for_letter(payload, "L-01")
        assert effective["return_painted_active"] is True
        assert effective["return_vinyl_active"] is False

    def test_disabled_assignment_ignored(self, auth_client):
        workspace_id = _hub_ready_workspace(auth_client)

        response = _patch_finish_assignments(
            auth_client,
            workspace_id,
            {
                "letter_group_finish_assignments": [
                    {
                        "assignment_id": "grp-disabled",
                        "label": "DISABLED",
                        "target_letter_ids": ["L-01"],
                        "face_finish": {
                            "finish_type": "oracal_8500",
                            "color_code": "302",
                            "color_name": "Red",
                        },
                        "enabled": False,
                    }
                ],
                "letter_finish_assignments": [],
            },
        )
        assert response.status_code == 200
        payload = response.json()["workspace"]["payload"]
        assert len(payload["letter_group_finish_assignments"]) == 1
        assert payload["finish_assignment_status"] == "global_only"
        effective = resolve_effective_finish_for_letter(payload, "L-01")
        assert effective["face_finish"]["color_code"] == "527"

    def test_no_side_effects(self, auth_client):
        workspace_id = _hub_ready_workspace(auth_client)

        response = _patch_finish_assignments(
            auth_client,
            workspace_id,
            {
                "letter_group_finish_assignments": [
                    {
                        "assignment_id": "grp-safe",
                        "label": "SAFE",
                        "target_letter_ids": ["L-01"],
                        "face_finish": {"finish_type": "oracal_8500", "color_code": "527"},
                        "enabled": True,
                    }
                ],
                "letter_finish_assignments": [],
            },
        )
        assert response.status_code == 200
        payload = response.json()["workspace"]["payload"]
        forbidden_keys = {
            "created_quote_id",
            "created_order_id",
            "execution_plan_id",
            "execution_task_id",
            "stock_movement_id",
            "quote_id",
            "order_id",
        }
        assert forbidden_keys.isdisjoint(payload.keys())
        assert payload["production_handoff"]["preview_only"] is True
        assert payload["employee_preview_seed"]["non_executable"] is True
        preview = response.json()["preview"]["preview"]
        assert preview["boundary_flags"]["quote_creation_allowed"] is False
        assert preview["boundary_flags"]["preview_only"] is True
