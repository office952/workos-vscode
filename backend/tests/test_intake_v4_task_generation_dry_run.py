"""Intake V4 task generation dry-run contract — read-only, no ExecutionTask."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from schemas.intake_v4 import PILOT_V4_TEMPLATE_CODE
from seeds.seed_build4_templates import seed_build4_templates
from services.intake_v4_task_generation_dry_run_service import (
    build_intake_v4_task_generation_dry_run,
)

_DEFAULT_PRICING = {
    "MAT-ORACAL-651": {"unit_cost": 5.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-ACP-FATA-LITERE": {"unit_cost": 10.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-SPATE-PVC-LITERE": {"unit_cost": 16.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-PROFIL-LATERAL-LITERE-60MM": {"unit_cost": 3.0, "currency": "EUR", "source": "inventory_materials"},
    "MAT-LED-MODULE": {"unit_cost": 0.5, "currency": "EUR", "source": "inventory_materials"},
    "MAT-LED-PSU-12V-100W": {"unit_cost": 16.0, "currency": "EUR", "source": "inventory_materials"},
}


@pytest.fixture
def seeded_db(db_fixture):
    asyncio.run(seed_build4_templates())
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


async def _run_dry_run(
    workspace_id: str,
    payload_dict: dict,
    *,
    pricing: dict | None = None,
):
    from services.intake_v4_workspace_service import _parse_payload

    payload = _parse_payload(payload_dict)
    with patch(
        "services.inventory_materials_admin_service.load_material_pricing_dict",
        new_callable=AsyncMock,
    ) as mock_pricing:
        mock_pricing.return_value = pricing if pricing is not None else _DEFAULT_PRICING
        return await build_intake_v4_task_generation_dry_run(
            None,  # type: ignore[arg-type]
            workspace_id,
            payload_dict,
            payload,
        )


def _complete_payload(*, confirmed: bool = True, illuminated: bool = False) -> dict:
    nesting = {
        "sheets": [
            {
                "configId": "sheet_1300x900",
                "sheetsUsed": 2,
                "usedSheetAreaSqm": 2.34,
                "placedItemsCount": 2,
                "unplacedItemsCount": 0,
                "placements": [
                    {
                        "partId": "letter-face-a",
                        "sourceLayerName": "litere-volumetrice-1",
                        "placedWidthMm": 800,
                        "placedHeightMm": 500,
                    },
                    {
                        "partId": "letter-back-a",
                        "sourceLayerName": "litere-backing",
                        "placedWidthMm": 400,
                        "placedHeightMm": 400,
                    },
                ],
            }
        ],
        "rolls": [
            {
                "rollWidthMm": 1000,
                "jobs": [{"usedRollAreaSqm": 8.0, "placedItemsCount": 3, "unplacedItemsCount": 0}],
            }
        ],
    }
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
        "svg_source": {
            "file_name": "test.svg",
            "file_size_bytes": 100,
            "file_hash": "a" * 64,
            "upload_status": "analyzed",
        },
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "nesting": nesting,
            "parts": {
                "items": [
                    {"id": "letter-face-a", "source": {"layerName": "litere-volumetrice-1"}},
                    {
                        "id": "letter-back-a",
                        "derivedPartKind": "back-cover-plate",
                        "source": {"layerName": "litere-backing"},
                    },
                ]
            },
            "layers": [
                {
                    "id": "litere-volumetrice-1",
                    "name": "litere-volumetrice-1",
                    "perimeterMl": 10.0,
                    "filledAreaSqm": 1.5,
                }
            ],
        },
        "quote_geometry": {
            "letter_perimeter_m": 10.0,
            "face_area_m2": 1.5,
            "backing_area_m2": 1.2,
            "return_material_perimeter_ml": 10.0,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": 1.5,
            "backing_area_m2": 1.2,
            "return_material_perimeter_ml": 10.0,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "litere-backing",
                    "layer_name": "litere-backing",
                    "confirmed_role": "backing",
                    "confirmation_state": "confirmed",
                },
            ],
        },
        "finish_setup": {
            "face_finish_type": "oracal_651",
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 60,
            "illuminated": illuminated,
            "face_vinyl_roll_width_mm": 1000,
            "letter_group_finishes": [
                {
                    "group_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "face_finish_type": "oracal_651",
                    "return_finish_type": "oracal_wrapped",
                    "return_depth_mm": 60,
                    "face_vinyl_roll_width_mm": 1000,
                }
            ],
            "confirmed": confirmed,
            **({"psu_configuration": [100], "lighting_system_type": "led_modules"} if illuminated else {}),
        },
    }


@pytest.mark.asyncio
async def test_standard_aluminum_return_skips_return_vinyl_task():
    payload = _complete_payload()
    payload["finish_setup"]["letter_group_finishes"] = [
        {
            "group_key": "litere-volumetrice-1",
            "layer_name": "litere-volumetrice-1",
            "face_finish_type": "none",
            "return_finish_type": "standard_aluminum",
            "return_depth_mm": 60,
        }
    ]
    payload["finish_setup"]["face_finish_type"] = "oracal_651"
    payload["finish_setup"]["return_finish_type"] = "oracal_wrapped"
    result = await _run_dry_run("ws-truth-return", payload)
    by_key = {c.task_key: c for c in result.task_candidates}
    assert by_key.get("return_vinyl_application_workbench") is None or not by_key[
        "return_vinyl_application_workbench"
    ].active
    assert by_key.get("oracal_vinyl_cutting") is None or not by_key["oracal_vinyl_cutting"].active


@pytest.mark.asyncio
async def test_dry_run_mode_and_flags():
    result = await _run_dry_run("ws-dry-1", _complete_payload())
    assert result.dry_run_mode == "task_generation_preview_only"
    assert result.creates_execution_tasks is False
    assert result.writes_to_production is False
    assert result.stock_consumption is False
    assert result.dry_run_only is True
    assert result.can_generate_tasks is False


@pytest.mark.asyncio
async def test_generates_task_candidates_from_handoff():
    result = await _run_dry_run("ws-dry-2", _complete_payload())
    keys = {c.task_key for c in result.task_candidates}
    assert "cnc_face_cutting" in keys
    assert "cnc_face_bevel" in keys
    assert result.cnc_task_source == "operation_rows"
    assert result.legacy_cnc_mapping_used is False
    assert "face_vinyl_final" in keys
    assert all(not c.creates_execution_task for c in result.task_candidates)


@pytest.mark.asyncio
async def test_return_forming_when_return_depth():
    result = await _run_dry_run("ws-dry-3", _complete_payload())
    keys = {c.task_key for c in result.task_candidates}
    assert "return_side_forming" in keys
    assert "return_face_bonding" in keys


@pytest.mark.asyncio
async def test_led_tasks_when_illuminated():
    result = await _run_dry_run("ws-dry-4", _complete_payload(illuminated=True))
    keys = {c.task_key for c in result.task_candidates}
    assert "led_module_install" in keys
    assert "psu_electrical_wiring" in keys


@pytest.mark.asyncio
async def test_dependencies_present():
    result = await _run_dry_run("ws-dry-5", _complete_payload())
    assert len(result.dependency_graph) >= 1
    edge_keys = {(e.from_task_key, e.to_task_key) for e in result.dependency_graph}
    assert ("cnc_file_preparation", "cnc_face_cutting") in edge_keys or any(
        e.from_task_key == "preflight_vector_and_layers" for e in result.dependency_graph
    )


@pytest.mark.asyncio
async def test_idempotency_keys_stable():
    result = await _run_dry_run("ws-stable", _complete_payload())
    assert len(result.idempotency_plan) >= 1
    for entry in result.idempotency_plan:
        assert entry.idempotency_key.startswith("intake-v4:ws-stable:")
        assert entry.source_fingerprint
        assert "do_not_create_duplicate" in entry.duplicate_policy


@pytest.mark.asyncio
async def test_source_fingerprint_in_summary():
    result = await _run_dry_run("ws-fp", _complete_payload())
    assert result.summary.get("source_fingerprint")
    assert result.audit_preview is not None
    assert result.audit_preview.analysis_hash == "a" * 64


@pytest.mark.asyncio
async def test_blockers_for_incomplete_finish():
    result = await _run_dry_run("ws-block", _complete_payload(confirmed=False))
    codes = {b.code for b in result.blockers}
    assert "finish_setup_not_confirmed" in codes
    assert "dry_run_only_no_order" in codes


@pytest.mark.asyncio
async def test_unsupported_template_safe():
    payload_dict = _complete_payload()
    payload_dict["product_binding"] = {"template_code": "TPL-OTHER"}
    result = await _run_dry_run("ws-other", payload_dict, pricing={})
    assert result.creates_execution_tasks is False
    assert any(b.code == "unsupported_template" for b in result.blockers)


@pytest.mark.asyncio
async def test_provisional_warnings_when_preview_not_template_backed():
    payload_dict = _complete_payload()
    with patch(
        "services.intake_v4_task_generation_dry_run_service.evaluate_v4_template_option_contract"
    ) as mock_contract:
        from services.intake_v4_template_option_contract_service import (
            TemplateOptionContractIssue,
            TemplateOptionContractResult,
        )

        mock_contract.return_value = TemplateOptionContractResult(
            template_code=PILOT_V4_TEMPLATE_CODE,
            warnings=[
                TemplateOptionContractIssue(
                    code="production_preview_not_template_backed",
                    severity="warning",
                    message="preview provisional",
                    source="test",
                )
            ],
        )
        with patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
        ) as mock_pricing:
            mock_pricing.return_value = _DEFAULT_PRICING
            from services.intake_v4_workspace_service import _parse_payload

            result = await build_intake_v4_task_generation_dry_run(
                None,  # type: ignore[arg-type]
                "ws-prov",
                payload_dict,
                _parse_payload(payload_dict),
            )
    warn_codes = {w.code for w in result.warnings}
    assert "production_preview_not_template_backed" in warn_codes or any(
        c.provisional for c in result.task_candidates
    )


class TestTaskGenerationDryRunEndpoint:
    def _seed(self, v4_client):
        from tests.test_intake_v4_workspace import _put_analysis_bundle

        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Dry-run contract", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        _put_analysis_bundle(v4_client, workspace_id)
        v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json={
                "face_finish_type": "oracal_651",
                "return_finish_type": "oracal_wrapped",
                "return_depth_mm": 60,
                "illuminated": False,
                "confirmed": True,
            },
        )
        return workspace_id

    def test_endpoint_returns_contract(self, v4_client):
        workspace_id = self._seed(v4_client)
        response = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/task-generation-dry-run",
        )
        assert response.status_code == 200
        body = response.json()
        assert body["dry_run_mode"] == "task_generation_preview_only"
        assert body["creates_execution_tasks"] is False
        assert body["stock_consumption"] is False
        assert body["can_generate_tasks"] is False
        assert isinstance(body["task_candidates"], list)
        assert isinstance(body["dependency_graph"], list)
        assert isinstance(body["idempotency_plan"], list)
        assert body["writes_to_production"] is False
        assert body["audit_preview"] is not None
        assert body["audit_preview"]["would_create_count"] >= 0