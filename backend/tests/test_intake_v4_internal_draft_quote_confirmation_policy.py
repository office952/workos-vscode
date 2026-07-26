"""Intake V4 internal draft quote confirmation policy."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from models.intake_v4_workspace import IntakeV4WorkspaceRecord
from schemas.intake_v4 import PILOT_V4_TEMPLATE_CODE, IntakeV4WorkspacePayload
from seeds.seed_build4_templates import seed_build4_templates
from seeds.seed_tpl_volumetric_letters_v2 import seed_tpl_volumetric_letters_v2
from services.intake_v4_commercial_quote_service import INTAKE_V4_LINKAGE_JSON_KEY
from services.intake_v4_internal_draft_quote_policy_service import (
    classify_handoff_issue_codes,
    has_unclassified_vector_artwork,
    list_v4_handoff_issue_codes,
)

FIXTURE_SVG = Path(__file__).parent / "fixtures" / "intake_v3" / "multi_layer_ten_layers.svg"

DRAFT_QUOTE_BODY = {
    "confirm_create_draft_only": True,
    "confirm_no_order": True,
    "confirm_no_execution": True,
    "confirm_no_inventory": True,
    "confirm_internal_draft_quote": True,
    "decision_reason": "pytest internal draft policy",
}

FINISH_WITH_ORACAL = {
    "face_finish_type": "oracal_651",
    "return_finish_type": "oracal_wrapped",
    "return_depth_mm": 60,
    "illuminated": True,
    "return_oracal_code": "ORACAL651-WHITE",
    "return_oracal_name": "Oracal 651 White",
    "lighting_system_type": "led_modules",
    "led_module_power_w": 1.44,
    "led_module_count": 10,
    "psu_configuration": [100],
    "letter_group_finishes": [
        {
            "group_key": "group-1",
            "face_finish_type": "oracal_651",
            "face_oracal_code": "ORACAL651-WHITE",
            "face_oracal_name": "Oracal 651 White",
            "return_finish_type": "oracal_wrapped",
            "return_oracal_code": "ORACAL651-WHITE",
            "return_depth_mm": 60,
            "confirmed": True,
        }
    ],
    "artwork_finishes": [
        {
            "layer_key": "artwork-layer",
            "layer_name": "Artwork",
            "execution_type": "needs_decision",
            "return_finish_type": "standard_aluminum",
        }
    ],
    "confirmed": True,
}


def _get_persisted_file_hash(v4_client, workspace_id: str) -> str:
    ws = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}")
    assert ws.status_code == 200, ws.text
    file_hash = ws.json()["payload"]["svg_source"]["file_hash"]
    assert isinstance(file_hash, str) and len(file_hash) == 64
    return file_hash


def _draft_quote_body(v4_client, workspace_id: str, **overrides) -> dict:
    return {
        **DRAFT_QUOTE_BODY,
        "client_analysis_hash": _get_persisted_file_hash(v4_client, workspace_id),
        **overrides,
    }


def _confirm_layer_roles(v4_client, workspace_id: str, svg_path: Path = FIXTURE_SVG) -> dict:
    svg_bytes = svg_path.read_bytes()
    upload = v4_client.post(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/svg",
        files={"file": ("multi_layer.svg", svg_bytes, "image/svg+xml")},
    )
    assert upload.status_code == 200, upload.text
    layers = upload.json()["layer_role_setup"]["layers"]
    updates = [
        {
            "layer_key": layer["layer_key"],
            "confirmed_role": layer["auto_role"] if layer["auto_role"] != "unknown" else "face",
            "confirmation_state": "confirmed",
        }
        for layer in layers
    ]
    confirmed = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/layer-roles",
        json={"layers": updates},
    )
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()["payload"]["layer_role_setup"]


def _put_analysis_bundle(v4_client, workspace_id: str, layer_role_setup: dict | None = None) -> None:
    svg_text = FIXTURE_SVG.read_text(encoding="utf-8")
    if layer_role_setup is None:
        layer_role_setup = _confirm_layer_roles(v4_client, workspace_id)
    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
        json={
            "file_name": FIXTURE_SVG.name,
            "file_size_bytes": len(svg_text.encode("utf-8")),
            "svg_text": svg_text,
            "svg_analysis_json": {
                "schemaVersion": "1.10.0",
                "layers": [
                    {
                        "id": layer["layer_key"],
                        "name": layer.get("layer_name") or layer["layer_key"],
                        "perimeterMl": 10.0,
                        "filledAreaSqm": 1.2,
                    }
                    for layer in layer_role_setup.get("layers", [])
                    if layer.get("confirmation_state") != "ignored"
                ],
                "parts": {"count": 10, "nestableCount": 8},
                "geometry": {"perimeterMl": 10.0},
            },
            "layer_role_setup": layer_role_setup,
        },
    )
    assert saved.status_code == 200, saved.text


def _confirm_internal_draft(v4_client, workspace_id: str) -> None:
    response = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/internal-draft-quote-confirmation",
        json={"confirmed": True},
    )
    assert response.status_code == 200, response.text
    assert response.json()["payload"]["finish_setup"]["internal_draft_quote_confirmed"] is True


def _seed_ready_workspace(v4_client, *, finish_body: dict | None = None):
    create = v4_client.post(
        "/api/v1/intake-v4/workspaces",
        json={"title": "Internal draft policy", "template_code": PILOT_V4_TEMPLATE_CODE, "client_name": "HUB TEST"},
    )
    assert create.status_code == 201, create.text
    workspace_id = create.json()["id"]
    _put_analysis_bundle(v4_client, workspace_id)
    finish = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json=finish_body or FINISH_WITH_ORACAL,
    )
    assert finish.status_code == 200, finish.text
    _confirm_internal_draft(v4_client, workspace_id)
    return workspace_id


@pytest.fixture(scope="module")
def seeded_db(db_fixture):
    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    asyncio.get_event_loop().run_until_complete(seed_tpl_volumetric_letters_v2())
    return db_fixture


@pytest.fixture
def v4_client(seeded_db):
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse
    from fastapi.testclient import TestClient

    async def _override_get_db():
        async with seeded_db.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


class TestIntakeV4InternalDraftQuoteConfirmationPolicy:
    def test_owner_valid_v2_template_is_in_scope_for_handoff_policy(self):
        record = IntakeV4WorkspaceRecord(
            id="policy-template-scope",
            workspace_code="IV4-POLICY",
            title="Policy template scope",
            template_code=PILOT_V4_TEMPLATE_CODE,
            status="ready_for_quote_preview",
            payload_json="{}",
            readiness_status="ready_for_quote_preview",
        )
        payload = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": {"perimeter_mm_approx": 31637.330856},
                "finish_setup": FINISH_WITH_ORACAL,
                "layer_role_setup": {"confirmation_status": "complete", "layers": []},
                "svg_analysis_json": {"layers": [], "geometry": {"perimeterMl": 31.6}},
            }
        )

        issues = list_v4_handoff_issue_codes(record, payload, include_hash_sync=False)

        assert "template_out_of_scope" not in issues

    def test_non_owner_template_remains_out_of_scope_for_handoff_policy(self):
        record = IntakeV4WorkspaceRecord(
            id="policy-template-out-of-scope",
            workspace_code="IV4-POLICY-OLD",
            title="Policy template out of scope",
            template_code="TPL-BANNER-STANDARD",
            status="ready_for_quote_preview",
            payload_json="{}",
            readiness_status="ready_for_quote_preview",
        )
        payload = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": "TPL-BANNER-STANDARD"},
                "path_geometry_summary": {"perimeter_mm_approx": 31637.330856},
                "finish_setup": FINISH_WITH_ORACAL,
                "layer_role_setup": {"confirmation_status": "complete", "layers": []},
                "svg_analysis_json": {"layers": [], "geometry": {"perimeterMl": 31.6}},
            }
        )

        issues = list_v4_handoff_issue_codes(record, payload, include_hash_sync=False)

        assert "template_out_of_scope" in issues

    def test_unclassified_vector_artwork_is_review_warning_not_fatal(self):
        payload = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": {"perimeter_mm_approx": 31637.330856},
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": [
                        {
                            "group_key": "letters",
                            "perimeter_m": 26.7472,
                            "confirmed": True,
                        }
                    ],
                },
            }
        )

        assert has_unclassified_vector_artwork(payload) is True
        fatal, review = classify_handoff_issue_codes(["unclassified_vector_artwork_requires_decision"])
        assert fatal == []
        assert review == ["unclassified_vector_artwork_requires_decision"]

    def test_vector_residual_case_a_confirmed_logos_no_warning(self):
        """Confirmed artwork perimeter in denominator clears false-positive residual."""
        payload = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": {"perimeter_mm_approx": 31637.330856},
                "quote_geometry": {"artwork_return_perimeter_ml": 4.891},
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": [
                        {"group_key": "letters", "perimeter_m": 26.7472, "confirmed": True},
                    ],
                    "artwork_finishes": [
                        {
                            "layer_key": "logo-stanga",
                            "layer_name": "logo stanga",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                        {
                            "layer_key": "logo-dreapta",
                            "layer_name": "logo dreapta",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                    ],
                },
            }
        )

        assert has_unclassified_vector_artwork(payload) is False

    def test_vector_residual_case_b_product_configured_logos_without_finish_confirmed_flag(self):
        """Execution-decided Vector Logos count like letters even when confirmed=false."""
        payload = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": {"perimeter_mm_approx": 31637.330856},
                "quote_geometry": {"artwork_return_perimeter_ml": 4.891},
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": [
                        {"group_key": "letters", "perimeter_m": 26.7472, "confirmed": True},
                    ],
                    "artwork_finishes": [
                        {
                            "layer_key": "logo-stanga",
                            "layer_name": "logo stanga",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": False,
                        },
                        {
                            "layer_key": "logo-dreapta",
                            "layer_name": "logo dreapta",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                    ],
                },
            }
        )

        assert has_unclassified_vector_artwork(payload) is False

    def test_vector_logo_scalability_zero_one_two_four_and_partial_incomplete(self):
        """Generic N logos: zero/one/two/four; incomplete Logo 3 does not drop 1/2/4."""
        letters = [{"group_key": "letters", "perimeter_m": 26.7472, "confirmed": True}]
        raw = {"perimeter_mm_approx": 31637.330856}

        zero = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": raw,
                "finish_setup": {"confirmed": True, "letter_group_finishes": letters, "artwork_finishes": []},
            }
        )
        assert has_unclassified_vector_artwork(zero) is True

        one = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": raw,
                "svg_analysis_json": {
                    "layers": [{"id": "logo_instance_001", "name": "Logo 1", "perimeterMl": 4.891}],
                },
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": letters,
                    "artwork_finishes": [
                        {
                            "layer_key": "logo_instance_001",
                            "layer_name": "Logo 1",
                            "execution_type": "print_laminate",
                            "confirmed": False,
                        }
                    ],
                },
            }
        )
        assert has_unclassified_vector_artwork(one) is False

        two = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": raw,
                "svg_analysis_json": {
                    "layers": [
                        {"id": "logo_instance_001", "name": "Logo 1", "perimeterMl": 2.4455},
                        {"id": "logo_instance_002", "name": "Logo 2", "perimeterMl": 2.4455},
                    ],
                },
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": letters,
                    "artwork_finishes": [
                        {
                            "layer_key": "logo_instance_001",
                            "layer_name": "Logo 1",
                            "execution_type": "print_laminate",
                            "confirmed": False,
                        },
                        {
                            "layer_key": "logo_instance_002",
                            "layer_name": "Logo 2",
                            "execution_type": "print_laminate",
                            "confirmed": False,
                        },
                    ],
                },
            }
        )
        assert has_unclassified_vector_artwork(two) is False

        four_layers = [
            {"id": f"logo_instance_{i:03d}", "name": f"Logo {i}", "perimeterMl": 1.22275}
            for i in range(1, 5)
        ]
        four_rows = [
            {
                "layer_key": f"logo_instance_{i:03d}",
                "layer_name": f"Logo {i}",
                "execution_type": "print_laminate",
                "confirmed": False,
            }
            for i in range(1, 5)
        ]
        four = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": raw,
                "svg_analysis_json": {"layers": four_layers},
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": letters,
                    "artwork_finishes": four_rows,
                },
            }
        )
        assert has_unclassified_vector_artwork(four) is False

        # Logo 3 incomplete (needs_decision): only that logo is excluded; residual remains.
        partial_rows = [
            {
                "layer_key": f"logo_instance_{i:03d}",
                "layer_name": f"Logo {i}",
                "execution_type": "needs_decision" if i == 3 else "print_laminate",
                "confirmed": False,
            }
            for i in range(1, 5)
        ]
        partial = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": raw,
                "svg_analysis_json": {"layers": four_layers},
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": letters,
                    "artwork_finishes": partial_rows,
                },
            }
        )
        assert has_unclassified_vector_artwork(partial) is True
        # Eligible logos 1+2+4 still contribute (3.66825); residual ~1.22 from Logo 3.
        from services.intake_v4_internal_draft_quote_policy_service import (
            _operator_confirmed_artwork_perimeter_m,
        )

        eligible = _operator_confirmed_artwork_perimeter_m(partial)
        assert eligible is not None
        assert abs(eligible - (1.22275 * 3)) < 0.001

    def test_vector_residual_case_b_unconfirmed_logos_warning_remains(self):
        """Undecided execution must not enter confirmed denominator."""
        payload = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": {"perimeter_mm_approx": 31637.330856},
                "quote_geometry": {"artwork_return_perimeter_ml": 4.891},
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": [
                        {"group_key": "letters", "perimeter_m": 26.7472, "confirmed": True},
                    ],
                    "artwork_finishes": [
                        {
                            "layer_key": "logo-stanga",
                            "layer_name": "logo stanga",
                            "execution_type": "needs_decision",
                            "confirmed": False,
                        },
                        {
                            "layer_key": "logo-dreapta",
                            "layer_name": "logo dreapta",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                    ],
                },
            }
        )

        assert has_unclassified_vector_artwork(payload) is True

    def test_vector_residual_case_c_real_residual_beyond_confirmed_artwork_warning_remains(self):
        """Residual larger than confirmed artwork still triggers review warning."""
        payload = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": {"perimeter_mm_approx": 31637.330856},
                "quote_geometry": {"artwork_return_perimeter_ml": 2.0},
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": [
                        {"group_key": "letters", "perimeter_m": 26.7472, "confirmed": True},
                    ],
                    "artwork_finishes": [
                        {
                            "layer_key": "logo-stanga",
                            "layer_name": "logo stanga",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                        {
                            "layer_key": "logo-dreapta",
                            "layer_name": "logo dreapta",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                    ],
                },
            }
        )

        assert has_unclassified_vector_artwork(payload) is True

    def test_vector_residual_case_d_missing_artwork_perimeter_warning_remains(self):
        """Confirmed logos without perimeter data must not be assumed — letter-only check."""
        payload = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": {"perimeter_mm_approx": 31637.330856},
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": [
                        {"group_key": "letters", "perimeter_m": 26.7472, "confirmed": True},
                    ],
                    "artwork_finishes": [
                        {
                            "layer_key": "logo-stanga",
                            "layer_name": "logo stanga",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                        {
                            "layer_key": "logo-dreapta",
                            "layer_name": "logo dreapta",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                    ],
                },
            }
        )

        assert has_unclassified_vector_artwork(payload) is True

    def test_vector_residual_case_a_per_row_analysis_perimeter_no_warning(self):
        """Per-row analysis perimeters for all confirmed artwork rows also clear residual."""
        payload = IntakeV4WorkspacePayload.model_validate(
            {
                "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
                "path_geometry_summary": {"perimeter_mm_approx": 31637.330856},
                "svg_analysis_json": {
                    "layers": [
                        {"id": "logo-stanga", "name": "logo stanga", "perimeterMl": 2.4455},
                        {"id": "logo-dreapta", "name": "logo dreapta", "perimeterMl": 2.4455},
                    ],
                },
                "finish_setup": {
                    "confirmed": True,
                    "letter_group_finishes": [
                        {"group_key": "letters", "perimeter_m": 26.7472, "confirmed": True},
                    ],
                    "artwork_finishes": [
                        {
                            "layer_key": "logo-stanga",
                            "layer_name": "logo stanga",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                        {
                            "layer_key": "logo-dreapta",
                            "layer_name": "logo dreapta",
                            "execution_type": "print_on_vinyl_laminated",
                            "confirmed": True,
                        },
                    ],
                },
            }
        )

        assert has_unclassified_vector_artwork(payload) is False

    def test_finish_setup_incomplete_blocks_internal_draft_quote(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Incomplete finish", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        _put_analysis_bundle(v4_client, workspace_id)
        v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json={**FINISH_WITH_ORACAL, "confirmed": False},
        )
        preview = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}/quote-handoff-preview")
        assert preview.status_code == 200
        body = preview.json()
        assert body["can_create_internal_draft_quote"] is False
        assert "finish_setup_not_confirmed" in body["fatal_blockers"]

        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert response.status_code == 422

    def test_operator_confirmation_missing_blocks_internal_draft_quote(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "No operator confirm", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        _put_analysis_bundle(v4_client, workspace_id)
        finish = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json=FINISH_WITH_ORACAL,
        )
        assert finish.status_code == 200
        preview = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}/quote-handoff-preview")
        assert preview.status_code == 200
        assert "operator_confirmation_missing" in preview.json()["fatal_blockers"]

        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "INTERNAL_DRAFT_CONFIRMATION_REQUIRED"

    def test_artwork_needs_decision_allows_internal_draft_with_operator_confirmation(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        preview = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/quote-handoff-preview",
            params={"client_analysis_hash": _get_persisted_file_hash(v4_client, workspace_id)},
        )
        assert preview.status_code == 200
        body = preview.json()
        assert body["can_create_internal_draft_quote"] is True
        assert body["status_label"] == "READY_FOR_INTERNAL_DRAFT_REVIEW"
        assert any(w.startswith("artwork_execution_undecided:") for w in body["review_warnings"])

        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert response.status_code == 201, response.text
        assert response.json()["requires_pricing_review"] is True

    def test_allowed_draft_with_artwork_warning_sets_client_order_production_flags_false(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["client_send_allowed"] is False
        assert body["accept_allowed"] is False
        assert body["convert_to_order_allowed"] is False
        assert body["production_allowed"] is False
        assert body["order_created"] is False
        assert body["execution_plan_created"] is False
        assert body["inventory_mutated"] is False

        quote_row = v4_client.get(f"/api/v1/entities/quotes/{body['quote_id']}")
        linkage = json.loads(quote_row.json()["notes"])[INTAKE_V4_LINKAGE_JSON_KEY]
        assert linkage["client_send_allowed"] is False
        assert linkage["convert_to_order_allowed"] is False
        assert linkage["production_allowed"] is False
        assert linkage["internal_draft_review_only"] is True

    def test_metal_support_creates_separate_linked_module_line(self, v4_client):
        workspace_id = _seed_ready_workspace(
            v4_client,
            finish_body={
                **FINISH_WITH_ORACAL,
                "mounting_system": "steel_bars",
                "mounting_bar_profile": "30x30x1.5",
            },
        )
        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert response.status_code == 201, response.text

        quote_row = v4_client.get(f"/api/v1/entities/quotes/{response.json()['quote_id']}")
        quote_payload = quote_row.json()
        line_items = json.loads(quote_payload["line_items"])
        assert any(item["productCode"] == "TPL-METAL-PREMOUNT-STRUCTURE_v1" for item in line_items)

        linkage = json.loads(quote_payload["notes"])[INTAKE_V4_LINKAGE_JSON_KEY]
        quote_input = linkage["quote_input_payload"]
        assert quote_input["mounting_system"] == "direct_wall"
        assert quote_input["parent_mounting_system"] == "steel_bars"
        assert quote_input["metal_support_required"] is True
        assert quote_input["linked_support_pricing_mode"] == "separate_quote_line"
        linked_modules = linkage["snapshot"]["linked_modules"]
        assert linked_modules[0]["module_template_code"] == "TPL-METAL-PREMOUNT-STRUCTURE_v1"
        assert linked_modules[0]["pricing_mode"] == "separate_quote_line"
        assert linked_modules[0]["execution_mode"] == "linked_child_work"
        assert linked_modules[0]["input_payload"]["bar_material"] == "steel"

    def test_missing_oracal_color_remains_fatal(self, v4_client):
        finish_missing_color = {
            **FINISH_WITH_ORACAL,
            "letter_group_finishes": [
                {
                    **FINISH_WITH_ORACAL["letter_group_finishes"][0],
                    "face_oracal_code": None,
                }
            ],
        }
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Missing oracal", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        _put_analysis_bundle(v4_client, workspace_id)
        finish = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json=finish_missing_color,
        )
        assert finish.status_code == 200
        confirm = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/internal-draft-quote-confirmation",
            json={"confirmed": True},
        )
        assert confirm.status_code == 422
        preview = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}/quote-handoff-preview")
        assert preview.status_code == 200
        assert any(code.startswith("missing_face_oracal_color:") for code in preview.json()["fatal_blockers"])

        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] in {
            "INTERNAL_DRAFT_QUOTE_BLOCKED",
            "INTERNAL_DRAFT_CONFIRMATION_REQUIRED",
        }

    def test_fatal_blocker_does_not_create_quote(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id, client_analysis_hash="0" * 64),
        )
        assert response.status_code == 422

    def test_finish_save_resets_operator_confirmation(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        finish = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json=FINISH_WITH_ORACAL,
        )
        assert finish.status_code == 200
        assert finish.json()["payload"]["finish_setup"]["internal_draft_quote_confirmed"] is False
