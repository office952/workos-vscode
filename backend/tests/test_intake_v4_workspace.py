"""Intake V4 workspace persistence and ProductSystem binding tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from schemas.intake_v4 import PILOT_V4_TEMPLATE_CODE
from seeds.seed_build4_templates import seed_build4_templates
from seeds.seed_tpl_volumetric_letters_dossier import seed_tpl_volumetric_letters_dossier

FIXTURE_SVG = Path(__file__).parent / "fixtures" / "intake_v3" / "multi_layer_ten_layers.svg"
PBL_COMPLEX_SVG = (
    Path(__file__).parent.parent.parent
    / "frontend"
    / "src"
    / "lib"
    / "svgAnalyzer"
    / "fixtures"
    / "pbl-complex.svg"
)


def _confirm_layer_roles(v4_client, workspace_id: str, svg_path: Path = FIXTURE_SVG) -> dict:
    svg_bytes = svg_path.read_bytes()
    upload = v4_client.post(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/svg",
        files={"file": (svg_path.name, svg_bytes, "image/svg+xml")},
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


def _put_analysis_bundle(
    v4_client,
    workspace_id: str,
    *,
    svg_path: Path = FIXTURE_SVG,
    layer_role_setup: dict | None = None,
) -> None:
    svg_text = svg_path.read_text(encoding="utf-8")
    if layer_role_setup is None:
        layer_role_setup = _confirm_layer_roles(v4_client, workspace_id, svg_path)
    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
        json={
            "file_name": svg_path.name,
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


@pytest.fixture(scope="module")
def seeded_db(db_fixture):
    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    asyncio.get_event_loop().run_until_complete(seed_tpl_volumetric_letters_dossier())
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


class TestIntakeV4WorkspaceEndpoints:
    def test_create_workspace_binds_product_system(self, v4_client):
        response = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={
                "title": "V4 HUB test",
                "template_code": PILOT_V4_TEMPLATE_CODE,
                "client_name": "HUB MEDIA PRODUCTION",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["id"]
        assert body["workspace_code"].startswith("IV4-")
        assert body["template_code"] == PILOT_V4_TEMPLATE_CODE
        binding = body["payload"]["product_binding"]
        assert binding["template_code"] == PILOT_V4_TEMPLATE_CODE
        assert binding["template_id"]
        assert binding["template_label"]
        assert body["payload"]["schema_version"] == "1.0.0"

    def test_get_product_system_binding(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Binding test", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        binding = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}/product-system-binding")
        assert binding.status_code == 200
        body = binding.json()
        assert body["template_code"] == PILOT_V4_TEMPLATE_CODE
        assert body["template_active"] is True
        assert body["operation_count"] > 0

    def test_template_form_contract_reports_dossier_authority_and_v4_alignment(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Template contract test", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/template-form-contract"
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["template_code"] == PILOT_V4_TEMPLATE_CODE
        assert body["dossier_source"] == "product_blueprint_dossier"
        assert body["intended_form_authority"].startswith("ProductSystem")
        assert body["current_runtime_authority"].startswith("Intake V4")
        fields = {field["field_key"]: field for field in body["variant_fields"]}
        assert fields["return_depth_mm"]["alignment_status"] == "canonical"
        assert fields["mounting_system"]["alignment_status"] == "canonical"
        assert fields["selected_psu_watts"]["alignment_status"] == "canonical"
        assert fields["back_bevel_enabled"]["alignment_status"] == "canonical"
        assert body["ui_must_not_invent_final_options"] is True
        assert body["blockers"] == []

    def test_upload_svg_builds_layer_role_setup(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "SVG test", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        svg_bytes = FIXTURE_SVG.read_bytes()
        upload = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/svg",
            files={"file": ("multi_layer.svg", svg_bytes, "image/svg+xml")},
        )
        assert upload.status_code == 200
        body = upload.json()
        setup = body["layer_role_setup"]
        assert len(setup["layers"]) > 0
        workspace = body["workspace"]
        assert workspace["payload"]["svg_source"]["file_name"] == "multi_layer.svg"
        assert workspace["payload"]["svg_source"]["file_size_bytes"] > 0
        assert workspace["payload"]["path_geometry_summary"]["parse_status"] == "parsed"

    def test_task_preview_from_product_system(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Task preview", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        preview = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}/task-preview")
        assert preview.status_code == 200
        items = preview.json()["items"]
        assert len(items) > 0
        assert all(item["source"] == "operation_catalog" for item in items)
        assert preview.json().get("preview_engine") == "v3_operation_catalog"
        assert any(item["operation_code"] == "face_vinyl_application_final" for item in items)
        assert any(item["active"] for item in items)

    def test_save_layer_roles_updates_readiness(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Layer roles", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        svg_bytes = FIXTURE_SVG.read_bytes()
        upload = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/svg",
            files={"file": ("multi_layer.svg", svg_bytes, "image/svg+xml")},
        )
        layers = upload.json()["layer_role_setup"]["layers"]
        updates = [
            {
                "layer_key": layer["layer_key"],
                "confirmed_role": layer["auto_role"] if layer["auto_role"] != "unknown" else "face",
                "confirmation_state": "confirmed",
            }
            for layer in layers
        ]
        saved = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/layer-roles",
            json={"layers": updates},
        )
        assert saved.status_code == 200
        setup = saved.json()["payload"]["layer_role_setup"]
        assert setup["confirmation_status"] == "complete"
        assert saved.json()["readiness_status"] == "finish_setup_incomplete"

    def test_save_analysis_bundle_from_nest2_handoff(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Analysis bundle", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        svg_text = PBL_COMPLEX_SVG.read_text(encoding="utf-8")
        layer_setup = {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "logo",
                    "layer_name": "logo",
                    "auto_role": "face",
                    "auto_confidence": "high",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
            "warnings": [],
        }
        saved = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
            json={
                "file_name": "pbl-complex.svg",
                "file_size_bytes": len(svg_text.encode("utf-8")),
                "svg_text": svg_text,
                "svg_analysis_json": {"schemaVersion": "svg_analysis_v1", "layers": []},
                "layer_role_setup": layer_setup,
            },
        )
        assert saved.status_code == 200
        body = saved.json()
        assert body["payload"]["svg_source"]["file_name"] == "pbl-complex.svg"
        assert body["payload"]["svg_source"]["upload_status"] == "analyzed"
        assert body["payload"]["svg_analysis_json"]["schemaVersion"] == "svg_analysis_v1"
        assert body["payload"]["layer_role_setup"]["confirmation_status"] == "complete"
        assert body["payload"]["path_geometry_summary"]["parse_status"] == "parsed"
        assert body["payload"]["svg_source_text"]
        assert "pbl-complex" in body["payload"]["svg_source_text"] or len(body["payload"]["svg_source_text"]) > 10
        assert body["readiness_status"] == "finish_setup_incomplete"

    def test_save_finish_setup_advances_readiness(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Finish setup", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        _put_analysis_bundle(v4_client, workspace_id)
        saved = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json={
                "face_finish_type": "oracal_8500",
                "return_finish_type": "oracal_651",
                "return_depth_mm": 60,
                "illuminated": True,
                "confirmed": True,
            },
        )
        assert saved.status_code == 200
        body = saved.json()
        assert body["payload"]["finish_setup"]["face_finish_type"] == "oracal_8500"
        assert body["payload"]["finish_setup"]["confirmed"] is True
        assert body["readiness_status"] == "ready_for_quote_preview"
        preview = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}/task-preview")
        assert preview.status_code == 200
        items = preview.json()["items"]
        assert len(items) > 0

    def test_save_finish_setup_persists_commercial_inputs(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Finish setup commercial", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        _put_analysis_bundle(v4_client, workspace_id)

        saved = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json={
                "face_finish_type": "oracal_8500",
                "return_finish_type": "oracal_651",
                "return_depth_mm": 60,
                "illuminated": True,
                "confirmed": True,
                "commercial_inputs": {
                    "markup_percent": 42,
                    "discount_percent": 3,
                    "vat_percent": 19,
                    "manual_adjustment_ron": 125,
                },
            },
        )

        assert saved.status_code == 200
        finish_setup = saved.json()["payload"]["finish_setup"]
        assert finish_setup["commercial_inputs"] == {
            "markup_percent": 42,
            "discount_percent": 3,
            "vat_percent": 19,
            "manual_adjustment_ron": 125,
        }

        fetched = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}")
        assert fetched.status_code == 200
        assert fetched.json()["payload"]["finish_setup"]["commercial_inputs"] == {
            "markup_percent": 42,
            "discount_percent": 3,
            "vat_percent": 19,
            "manual_adjustment_ron": 125,
        }


class TestIntakeV4MaterialBreakdown:
    def test_material_breakdown_requires_analysis_bundle(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Breakdown empty", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        response = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}/material-breakdown")
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "analysis_boundary_blocked"

    def test_material_breakdown_after_analysis_bundle(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Breakdown full", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        svg_text = PBL_COMPLEX_SVG.read_text(encoding="utf-8")
        nesting = {
            "sheets": [
                {
                    "configId": "sheet_1300x900",
                    "sheetsUsed": 2,
                    "efficiencyPercent": 72.5,
                    "wasteAreaSqm": 0.15,
                }
            ],
            "rolls": [],
        }
        v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
            json={
                "file_name": "pbl-complex.svg",
                "file_size_bytes": len(svg_text.encode("utf-8")),
                "svg_text": svg_text,
                "svg_analysis_json": {
                    "schemaVersion": "1.10.0",
                    "nesting": nesting,
                    "geometry": {"document": {"widthMm": 1000, "heightMm": 500}, "perimeterMl": 5},
                    "layers": [
                        {
                            "id": "litere-1",
                            "name": "litere-volumetrice-1",
                            "perimeterMl": 12.5,
                            "boundingAreaSqm": 1.5,
                        }
                    ],
                    "parts": {"count": 8, "nestableCount": 6},
                },
                "layer_role_setup": {
                    "confirmation_status": "complete",
                    "layers": [
                        {
                            "layer_key": "litere-1",
                            "confirmed_role": "face",
                            "confirmation_state": "confirmed",
                            "auto_role": "face",
                            "auto_confidence": "high",
                        }
                    ],
                    "warnings": [],
                },
            },
        )
        v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json={
                "face_finish_type": "oracal_651",
                "return_finish_type": "oracal_651",
                "return_depth_mm": 50,
                "illuminated": True,
                "lighting_system_type": "led_modules",
                "light_color": "warm",
                "required_psu_watts": 160,
                "psu_configuration": [160],
                "confirmed": True,
            },
        )
        response = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}/material-breakdown")
        assert response.status_code == 200
        body = response.json()
        assert len(body["nesting_rows"]) >= 1
        assert body["nesting_rows"][0]["config_id"] == "sheet_1300x900"
        assert len(body["material_rows"]) >= 1
        assert len(body["consumable_rows"]) >= 1
        assert body["totals"]["contains_missing_prices"] is True
        assert body["totals"]["material_cost_total"] == 0.0
        saved = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}")
        quote_geom = saved.json()["payload"].get("quote_geometry") or {}
        assert (quote_geom.get("letter_perimeter_m") or 0) > 0

    def test_task_preview_honors_draft_finish_query(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Task preview draft", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        lit = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/task-preview",
            params={"illuminated": "true", "lighting_system_type": "led_modules"},
        )
        unlit = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/task-preview",
            params={"illuminated": "false"},
        )
        assert lit.status_code == 200
        assert unlit.status_code == 200
        lit_codes = {item["operation_code"] for item in lit.json()["items"] if item["active"]}
        unlit_codes = {item["operation_code"] for item in unlit.json()["items"] if item["active"]}
        assert "led_installation_wiring_and_light_test" in lit_codes
        assert "led_installation_wiring_and_light_test" not in unlit_codes


class TestIntakeV4Sprint2Previews:
    def _seed_workspace_with_finish(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Sprint2 preview", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        _put_analysis_bundle(v4_client, workspace_id)
        v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json={
                "face_finish_type": "oracal_651",
                "return_finish_type": "oracal_wrapped",
                "return_depth_mm": 60,
                "illuminated": True,
                "confirmed": True,
            },
        )
        return workspace_id

    def test_pricing_input_preview_endpoint(self, v4_client):
        workspace_id = self._seed_workspace_with_finish(v4_client)
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/pricing-input-preview",
        )
        assert response.status_code == 200
        body = response.json()
        assert body["workspace_id"] == workspace_id
        assert body["template_code"] == PILOT_V4_TEMPLATE_CODE
        assert body["preview_only"] is True
        assert body["quote_input_payload"]["intake_source"] == "intake_v4"
        assert isinstance(body["operation_flags"], dict)

    def test_production_task_dry_run_endpoint(self, v4_client):
        workspace_id = self._seed_workspace_with_finish(v4_client)
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/production-task-dry-run",
        )
        assert response.status_code == 200
        body = response.json()
        assert body["source_module"] == "intake_v4"
        assert body["source_type"] == "intake_v4_workspace"
        assert body["source_workspace_id"] == workspace_id
        assert body["creates_execution_plan"] is False
        assert body["summary"]["candidate_tasks_count"] >= 0

