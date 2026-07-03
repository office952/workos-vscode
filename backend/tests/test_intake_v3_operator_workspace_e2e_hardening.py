"""Intake V3 Operator Workspace — Phase 6 E2E hardening matrix (backend integration)."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import func, select

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT,
    BLOCKER_UNCONFIRMED_LAYER_FINISH,
    BLOCKER_UNCONFIRMED_LIGHTING_PLAN,
)
from main import app
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from models.stock_movements import StockMovement
from services.intake_v3_layer_finish_assignment_service import layer_requires_finish, uses_native_layer_finish
from services.intake_v3_lighting_plan_service import propose_psu_units
from services.intake_v3_preview_fixtures import INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL
from tests.test_intake_v3_layer_finish_assignments import (
    _apply_global_finish,
    _backing_layer_assignment,
    _face_layer_assignment,
    _patch_layer_finishes,
    _return_layer_assignment,
)
from tests.test_intake_v3_layer_role_confirmation import LAYERED_SVG, _confirm_layers, _seed_and_upload
from tests.test_intake_v3_lighting_plan import _confirmed_plan, _patch_lighting
from tests.test_intake_v3_printed_artwork_layer_finish import _artwork_layer_assignment
from tests.test_intake_v3_layer_role_confirmation_propagation import (
    _reconfirm_litere_ignore,
)
from tests.test_intake_v3_real_commercial_quote_creation import _create_draft_quote, _seed_hub_workspace

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "intake_v3"
MULTI_LAYER_SVG_PATH = FIXTURES_DIR / "multi_layer_ten_layers.svg"

OPERATOR_CRITICAL_OPENAPI_PATHS: tuple[str, ...] = (
    "/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments",
    "/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments/targets",
    "/api/v1/intake-v3/workspaces/{workspace_id}/lighting-plan",
)

# Stale dev backends expose ~19 workspace paths; current code exposes ~39.
STALE_OPENAPI_WORKSPACE_PATH_MINIMUM = 30

SCENARIO_MATRIX: dict[str, str] = {
    "6.1_simple_one_color": "Layered SVG + global/layer finish + non-illuminated lighting",
    "6.2_multi_color_same_layer": "Sub-group detection limited — free layer names + global fallback safe",
    "6.3_multi_layer_svg": "10+ productive layers with reference/ignore exemptions",
    "6.4_printed_artwork": "Artwork layer finish + readiness + preview summary",
    "6.5_return_cant_fallback": "Global return finish when no dedicated cant layer in native path",
    "6.6_dedicated_return_layer": "CANT layer role + layer finish assignment",
    "6.7_backing_support": "Forex backing thickness in finish + preview",
    "6.8_lighting_psu": "Workspace-level lighting_plan calculations + PSU auto proposal",
    "6.9_missing_geometry": "Missing roll width blocks readiness without silent defaults",
    "6.10_stale_propagation": "Layer reconfirm marks quote propagation stale (visible, safe)",
    "6.11_pending_blocks_quote": "Unconfirmed layer finish blocks readiness can_create_quote",
    "6.12_confirmed_enables_quote_preview": "Complete setup clears readiness blockers",
    "6.13_materials_read_only": "Material availability boundary flags",
    "6.14_production_preview_read_only": "Production task dry-run non-executable",
    "6.15_negative_boundaries": "No quotes/orders/plans/movements from operator GET/PATCH",
    "6.16_runtime_stale_guard": "OpenAPI path count detects stale backend",
}


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


async def _side_effect_counts(db_session) -> dict[str, int]:
    return {
        "quotes": await db_session.scalar(select(func.count()).select_from(Quotes)) or 0,
        "orders": await db_session.scalar(select(func.count()).select_from(Orders)) or 0,
        "execution_plans": await db_session.scalar(select(func.count()).select_from(ExecutionPlan)) or 0,
        "stock_movements": await db_session.scalar(select(func.count()).select_from(StockMovement)) or 0,
    }


def _readiness_blocker_codes(preview_body: dict) -> set[str]:
    report = preview_body.get("preview", {}).get("readiness_report") or {}
    return {item["code"] for item in report.get("blockers", [])}


def _create_quote_after_full_operator_setup(auth_client) -> tuple[str, int]:
    workspace_id = _seed_and_upload(auth_client)
    _setup_layer_finishes_complete(auth_client, workspace_id)
    _setup_non_illuminated(auth_client, workspace_id)
    create = _create_draft_quote(auth_client, workspace_id)
    assert create.status_code == 201, create.text
    return workspace_id, create.json()["quote_id"]


def _setup_non_illuminated(auth_client, workspace_id: str) -> None:
    response = _patch_lighting(
        auth_client,
        workspace_id,
        {
            "enabled": False,
            "illumination_mode": "non_illuminated",
            "psu_strategy": "not_required",
            "is_confirmed": True,
        },
    )
    assert response.status_code == 200, response.text


def _setup_layer_finishes_complete(auth_client, workspace_id: str) -> None:
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


def _confirm_multi_layer_roles(auth_client, workspace_id: str, productive_count: int = 10) -> None:
    layers = [
        {
            "layer_key": f"PROD_{index:02d}",
            "confirmed_role": "face",
            "confirmation_state": "confirmed",
        }
        for index in range(1, productive_count + 1)
    ]
    layers.extend(
        [
            {"layer_key": "TECH_REF", "confirmed_role": "reference", "confirmation_state": "confirmed"},
            {"layer_key": "GOLURI", "confirmed_role": "inner_hole", "confirmation_state": "confirmed"},
        ]
    )
    response = auth_client.put(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
        json={"layers": layers},
    )
    assert response.status_code == 200, response.text


class TestRuntimeStaleBackendGuard:
    """Scenario 6.16 — mirrors start-dev.ps1 OpenAPI route probe."""

    def test_openapi_includes_critical_operator_paths(self):
        paths = set(app.openapi().get("paths", {}).keys())
        missing = [path for path in OPERATOR_CRITICAL_OPENAPI_PATHS if path not in paths]
        assert not missing, f"Missing operator workspace OpenAPI paths: {missing}"

    def test_openapi_workspace_path_count_above_stale_threshold(self):
        paths = set(app.openapi().get("paths", {}).keys())
        workspace_paths = [path for path in paths if "intake-v3/workspaces" in path]
        assert len(workspace_paths) >= STALE_OPENAPI_WORKSPACE_PATH_MINIMUM, (
            f"Only {len(workspace_paths)} workspace paths — likely stale backend (~19)"
        )


class TestScenario61SimpleOneColorVolumetric:
    @pytest.mark.asyncio
    async def test_end_to_end_simple_setup_readiness_and_preview(self, auth_client, db_session):
        before = await _side_effect_counts(db_session)
        workspace_id = _seed_and_upload(auth_client)
        _setup_layer_finishes_complete(auth_client, workspace_id)
        _setup_non_illuminated(auth_client, workspace_id)

        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        report = preview["preview"]["readiness_report"]
        assert report["can_create_quote"] is True
        assert preview["preview"]["finish_summary"]["face_vinyl_roll_width_mm"] == 1260

        workspace = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()
        model = workspace["payload"]["confirmed_production_model"]
        assert model["letter_count"] >= 1
        assert model["inner_hole_count"] is not None

        after = await _side_effect_counts(db_session)
        assert after == before


class TestScenario62MultiColorSameLayerLimitation:
    @pytest.mark.asyncio
    async def test_free_layer_names_and_global_fallback_without_subgroups(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        _apply_global_finish(auth_client, workspace_id)

        targets = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments/targets",
        ).json()
        face_target = next(item for item in targets["targets"] if item["layer_key"] == "LITERE")
        assert face_target["layer_key"] == "LITERE"
        assert face_target["requires_finish"] is True

        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        variation = preview["preview"]["finish_variation_summary"]
        assert "has_variations" in variation
        # Sub-group / color-group detection per SVG path is not a Phase 6 feature — global fallback remains safe.


class TestScenario63MultiLayerSvg:
    @pytest.mark.asyncio
    async def test_ten_productive_layers_accept_free_names(self, auth_client):
        svg_text = _read_fixture("multi_layer_ten_layers.svg")
        workspace_id = _seed_and_upload(auth_client, svg_text=svg_text)
        _confirm_multi_layer_roles(auth_client, workspace_id, productive_count=10)

        targets = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments/targets",
        ).json()
        by_key = {item["layer_key"]: item for item in targets["targets"]}
        assert len([key for key in by_key if key.startswith("PROD_")]) == 10
        assert by_key["TECH_REF"]["requires_finish"] is False
        assert by_key["GOLURI"]["requires_finish"] is False
        assert layer_requires_finish(by_key["PROD_05"]["confirmed_role"]) is True


class TestScenario64PrintedArtworkPolicromie:
    @pytest.mark.asyncio
    async def test_artwork_finish_in_preview_and_pending_blocks(self, auth_client):
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

        pending = _patch_layer_finishes(auth_client, workspace_id, [_artwork_layer_assignment("LITERE", confirmed=False)])
        assert pending.status_code == 422

        complete = _patch_layer_finishes(
            auth_client,
            workspace_id,
            [
                _artwork_layer_assignment("LITERE"),
                _return_layer_assignment("CANT"),
                _backing_layer_assignment("SPATE"),
            ],
        )
        assert complete.status_code == 200
        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        layer_preview = preview["preview"]["finish_summary"]["layer_finish_preview"]
        assert any(item.get("print_method") == "printed_vinyl" for item in layer_preview)


class TestScenario65ReturnCantFallback:
    @pytest.mark.asyncio
    async def test_global_return_finish_without_native_layer_assignments(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        _apply_global_finish(auth_client, workspace_id)

        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        finish_summary = preview["preview"]["finish_summary"]
        assert finish_summary["return_depth_mm"] == 60
        workspace = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()
        assert uses_native_layer_finish(workspace["payload"]) is False


class TestScenario66DedicatedReturnCantLayer:
    @pytest.mark.asyncio
    async def test_dedicated_cant_layer_finish_assignment(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _setup_layer_finishes_complete(auth_client, workspace_id)
        assignments = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments",
        ).json()["layer_finish_assignments"]
        cant = next(item for item in assignments if item["layer_key"] == "CANT")
        assert cant["confirmed_role"] == "return"
        assert cant["return_finish"]["return_depth_mm"] == 60


class TestScenario67BackingSupportSetup:
    @pytest.mark.asyncio
    async def test_forex_backing_in_finish_summary(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _setup_layer_finishes_complete(auth_client, workspace_id)
        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        finish_summary = preview["preview"]["finish_summary"]
        assert finish_summary["backing_material"] == "Forex"
        assert finish_summary["backing_thickness_mm"] == 10


class TestScenario68LightingLedPsuPlan:
    def test_psu_auto_proposal_sizes(self):
        units = propose_psu_units(130)
        total = sum(unit.capacity_w * unit.quantity for unit in units)
        assert total >= 130
        assert all(unit.capacity_w in {60, 100, 160, 200} for unit in units)

    @pytest.mark.asyncio
    async def test_confirmed_lighting_workspace_level_not_layer_finish(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        response = _patch_lighting(auth_client, workspace_id, _confirmed_plan())
        assert response.status_code == 200, response.text
        plan = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/lighting-plan",
        ).json()["lighting_plan"]
        assert plan["estimated_total_watts"] == pytest.approx(0.72 * 120)
        assert plan["required_watts_with_reserve"] == pytest.approx(plan["estimated_total_watts"] * 1.3)
        assert plan["psu_total_capacity_w"] == 200
        assert plan["psu_reserve_w"] == pytest.approx(200 - plan["required_watts_with_reserve"])

        workspace = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()["payload"]
        assert "lighting_plan" in workspace
        assert "layer_finish_assignments" in workspace or workspace.get("layer_finish_assignments") is None


class TestScenario69MissingGeometryManualFallback:
    @pytest.mark.asyncio
    async def test_missing_face_roll_width_blocks_readiness(self, auth_client):
        response = auth_client.post(
            "/api/v1/intake-v3/workspaces/seed-from-scenario",
            json={
                "scenario": "hub_missing_face_roll_width",
                "title": "Missing roll width hardening",
            },
        )
        assert response.status_code == 201
        workspace_id = response.json()["id"]
        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        blockers = _readiness_blocker_codes(preview)
        assert blockers
        assert preview["preview"]["readiness_report"]["can_create_quote"] is False


class TestScenario610StaleGeometryPropagation:
    @pytest.mark.asyncio
    async def test_layer_reconfirm_marks_quote_propagation_stale(self, auth_client):
        workspace_id, quote_id = _create_quote_after_full_operator_setup(auth_client)
        _reconfirm_litere_ignore(auth_client, workspace_id)
        propagation = auth_client.get(
            f"/api/v1/intake-v3/quotes/{quote_id}/layer-role-confirmation/propagation",
        ).json()
        assert propagation["is_snapshot_stale"] is True


class TestScenario611PendingLayerBlocksQuote:
    @pytest.mark.asyncio
    async def test_unconfirmed_layer_finish_blocks_can_create_quote(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _confirm_layers(auth_client, workspace_id)
        _setup_non_illuminated(auth_client, workspace_id)

        pending_response = _patch_layer_finishes(
            auth_client,
            workspace_id,
            [
                _face_layer_assignment("LITERE", confirmed=False),
                _return_layer_assignment("CANT", confirmed=False),
                _backing_layer_assignment("SPATE", confirmed=False),
            ],
        )
        assert pending_response.status_code == 422
        detail = pending_response.json()["detail"]
        if isinstance(detail, dict) and "blockers" in detail:
            codes = {item["code"] for item in detail["blockers"]}
            assert BLOCKER_UNCONFIRMED_LAYER_FINISH in codes or BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT in codes


class TestScenario612ConfirmedSetupEnablesQuotePreview:
    @pytest.mark.asyncio
    async def test_complete_setup_clears_readiness_blockers(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _setup_layer_finishes_complete(auth_client, workspace_id)
        _setup_non_illuminated(auth_client, workspace_id)

        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        report = preview["preview"]["readiness_report"]
        assert report["can_create_quote"] is True
        assert not _readiness_blocker_codes(preview)

        enablement = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-enablement",
        )
        assert enablement.status_code == 200
        policy = enablement.json()["enablement_policy"]
        assert policy["can_create_quote_now"] is False
        assert policy["owner_approval_required"] is True


class TestScenario613MaterialsReadOnly:
    @pytest.mark.asyncio
    async def test_material_availability_boundary_on_workspace(self, auth_client):
        workspace_id = _seed_hub_workspace(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/material-availability",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["boundary"]["read_only"] is True
        assert payload["boundary"]["reserves_inventory"] is False
        assert payload["boundary"]["mutates_inventory"] is False
        assert payload["boundary"]["creates_purchase_order"] is False
        assert payload["boundary"]["costengine_used"] is False
        assert "final_commercial_price" not in str(payload).lower()


class TestScenario614ProductionPreviewReadOnly:
    @pytest.mark.asyncio
    async def test_production_task_dry_run_non_executable(self, auth_client, db_session):
        workspace_id = _seed_hub_workspace(auth_client)
        before = await _side_effect_counts(db_session)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-task-dry-run",
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["creates_execution_tasks"] is False
        assert payload["would_create_execution_tasks"] is False
        assert payload["mutates_inventory"] is False
        after = await _side_effect_counts(db_session)
        assert after == before


class TestScenario615NegativeBoundaries:
    @pytest.mark.asyncio
    async def test_operator_workspace_endpoints_do_not_mutate_commercial_records(
        self,
        auth_client,
        db_session,
    ):
        before = await _side_effect_counts(db_session)
        workspace_id = _seed_and_upload(auth_client)
        _setup_layer_finishes_complete(auth_client, workspace_id)
        _patch_lighting(auth_client, workspace_id, _confirmed_plan(is_confirmed=False))

        endpoints = [
            ("GET", f"/api/v1/intake-v3/workspaces/{workspace_id}"),
            ("GET", f"/api/v1/intake-v3/workspaces/{workspace_id}/preview"),
            ("GET", f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments"),
            ("GET", f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments/targets"),
            ("GET", f"/api/v1/intake-v3/workspaces/{workspace_id}/lighting-plan"),
            ("GET", f"/api/v1/intake-v3/workspaces/{workspace_id}/material-availability"),
            ("GET", f"/api/v1/intake-v3/workspaces/{workspace_id}/production-task-dry-run"),
            ("GET", f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-enablement"),
        ]
        for method, url in endpoints:
            response = auth_client.request(method, url)
            assert response.status_code == 200, f"{method} {url}: {response.text}"
            body = response.json()
            if "costengine_used" in body:
                assert body["costengine_used"] is False
            if "boundary" in body and isinstance(body["boundary"], dict):
                boundary = body["boundary"]
                assert boundary.get("mutates_inventory", False) is False
                assert boundary.get("creates_purchase_order", False) is False
                assert boundary.get("creates_stock_movement", False) is False

        after = await _side_effect_counts(db_session)
        assert after == before

    @pytest.mark.asyncio
    async def test_pending_lighting_blocks_readiness_not_bypass(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _setup_layer_finishes_complete(auth_client, workspace_id)
        _patch_lighting(auth_client, workspace_id, _confirmed_plan(is_confirmed=False))
        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        assert preview["preview"]["readiness_report"]["can_create_quote"] is False
        assert BLOCKER_UNCONFIRMED_LIGHTING_PLAN in _readiness_blocker_codes(preview)


class TestScenarioHubSeedBackwardsCompatibility:
    @pytest.mark.asyncio
    async def test_hub_scenario_seed_still_serves_operator_endpoints(self, auth_client):
        response = auth_client.post(
            "/api/v1/intake-v3/workspaces/seed-from-scenario",
            json={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL, "title": "Phase 6 hub"},
        )
        assert response.status_code == 201
        workspace_id = response.json()["id"]
        for suffix in ("layer-finish-assignments", "lighting-plan"):
            probe = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/{suffix}")
            assert probe.status_code == 200, probe.text
