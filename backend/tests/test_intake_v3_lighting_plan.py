"""Intake V3 lighting / LED / PSU planning — workspace-level payload."""

from __future__ import annotations

import pytest

from data_models.intake_v3_contracts import (
    BLOCKER_INSUFFICIENT_PSU_CAPACITY,
    BLOCKER_MISSING_LED_MODULE_COUNT,
    BLOCKER_MISSING_LED_MODULE_POWER,
    BLOCKER_UNCONFIRMED_LIGHTING_PLAN,
)
from schemas.intake_v3 import IntakeV3ApplyLightingPlanRequest, IntakeV3LightingPlan, IntakeV3PsuPlanUnit
from services.intake_v3_lighting_plan_service import (
    apply_lighting_plan_to_payload,
    draft_lighting_plan,
    lighting_plan_required,
    propose_psu_units,
    sync_lighting_plan,
    validate_lighting_plan_entry,
)
from tests.test_intake_v3_layer_role_confirmation import _seed_and_upload


def _confirmed_plan(**overrides) -> dict:
    base = {
        "enabled": True,
        "illumination_mode": "frontlit",
        "led_system": "modules",
        "light_color": "neutral_white",
        "module_power_w": 0.72,
        "module_count": 120,
        "reserve_percent": 30,
        "psu_strategy": "manual",
        "psu_units": [{"capacity_w": 200, "quantity": 1, "source": "manual"}],
        "is_confirmed": True,
    }
    base.update(overrides)
    return base


def _patch_lighting(auth_client, workspace_id: str, plan: dict):
    return auth_client.patch(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/lighting-plan",
        json={"lighting_plan": plan, "regenerate_preview": True},
    )


class TestLightingPlanCalculations:
    def test_required_watts_with_reserve(self):
        plan = sync_lighting_plan(
            IntakeV3LightingPlan(
                enabled=True,
                illumination_mode="frontlit",
                module_power_w=1.0,
                module_count=100,
                reserve_percent=30,
            )
        )
        assert plan.estimated_total_watts == 100.0
        assert plan.required_watts_with_reserve == 130.0

    def test_psu_capacity_sum(self):
        plan = sync_lighting_plan(
            IntakeV3LightingPlan(
                enabled=True,
                illumination_mode="frontlit",
                module_power_w=1.0,
                module_count=100,
                psu_strategy="manual",
                psu_units=[
                    IntakeV3PsuPlanUnit(capacity_w=100, quantity=1),
                    IntakeV3PsuPlanUnit(capacity_w=60, quantity=1),
                ],
            )
        )
        assert plan.psu_total_capacity_w == 160.0

    def test_auto_proposal(self):
        units = propose_psu_units(130)
        total = sum(u.capacity_w * u.quantity for u in units)
        assert total >= 130

    def test_realistic_120_module_led_psu_chain(self):
        """E2E numeric probe: manual module_count model (Phase 5), not perimeter-derived."""
        plan = sync_lighting_plan(
            IntakeV3LightingPlan(
                enabled=True,
                illumination_mode="frontlit",
                led_system="modules",
                module_power_w=1.44,
                module_count=120,
                modules_per_letter=10,
                reserve_percent=30,
                psu_strategy="auto",
            )
        )
        assert plan.estimated_total_watts == 172.8
        assert plan.required_watts_with_reserve == 224.64
        assert plan.psu_total_capacity_w == 260.0
        assert plan.psu_reserve_w == 35.36
        capacities = sorted(
            [(int(u.capacity_w), u.quantity) for u in plan.psu_units],
            reverse=True,
        )
        assert capacities == [(200, 1), (60, 1)]

    def test_modules_per_letter_does_not_derive_module_count(self):
        plan = sync_lighting_plan(
            IntakeV3LightingPlan(
                enabled=True,
                illumination_mode="frontlit",
                module_power_w=1.44,
                modules_per_letter=10,
                reserve_percent=30,
            )
        )
        assert plan.module_count is None
        assert plan.estimated_total_watts is None
        assert plan.required_watts_with_reserve is None

    def test_non_illuminated_not_required(self):
        payload = {"support_context": {"illuminated": False}, "lighting_plan": {"enabled": False, "illumination_mode": "non_illuminated"}}
        assert lighting_plan_required(payload) is False

    def test_insufficient_psu_blocks_without_override(self):
        plan = IntakeV3LightingPlan.model_validate(
            _confirmed_plan(
                module_power_w=2,
                module_count=100,
                psu_units=[{"capacity_w": 60, "quantity": 1, "source": "manual"}],
                is_confirmed=True,
            )
        )
        codes = {item.code for item in validate_lighting_plan_entry(plan)}
        assert BLOCKER_INSUFFICIENT_PSU_CAPACITY in codes

    def test_manual_override_reason_clears_insufficient_blocker(self):
        plan = IntakeV3LightingPlan.model_validate(
            _confirmed_plan(
                module_power_w=2,
                module_count=100,
                psu_units=[{"capacity_w": 60, "quantity": 1, "source": "manual"}],
                manual_override_reason="Use existing stock PSU",
                is_confirmed=True,
            )
        )
        codes = {item.code for item in validate_lighting_plan_entry(plan)}
        assert BLOCKER_INSUFFICIENT_PSU_CAPACITY not in codes


class TestLightingPlanHttp:
    @pytest.mark.asyncio
    async def test_get_drafts_from_support_context(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/lighting-plan")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["lighting_plan"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_patch_persists_confirmed_plan(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        response = _patch_lighting(auth_client, workspace_id, _confirmed_plan())
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["summary"]["lighting_plan_status"] == "complete"
        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        assert preview["preview"]["lighting_summary"]["module_count"] == 120

    @pytest.mark.asyncio
    async def test_pending_confirmation_blocks_readiness(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        pending = _confirmed_plan(is_confirmed=False)
        response = _patch_lighting(auth_client, workspace_id, pending)
        assert response.status_code == 200, response.text
        readiness = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        blocker_codes = {item["code"] for item in readiness["preview"]["readiness_report"]["blockers"]}
        assert BLOCKER_UNCONFIRMED_LIGHTING_PLAN in blocker_codes

    @pytest.mark.asyncio
    async def test_confirmed_incomplete_rejected(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        bad = _confirmed_plan(module_power_w=None, module_count=None, is_confirmed=True)
        response = _patch_lighting(auth_client, workspace_id, bad)
        assert response.status_code == 422, response.text

    @pytest.mark.asyncio
    async def test_non_illuminated_skips_requirements(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
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
        readiness = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        lighting_blockers = [
            item
            for item in readiness["preview"]["readiness_report"]["blockers"]
            if item.get("section") == "iluminare"
        ]
        assert not lighting_blockers

    @pytest.mark.asyncio
    async def test_invalid_negative_module_count_rejected(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        response = _patch_lighting(auth_client, workspace_id, _confirmed_plan(module_count=-1, is_confirmed=False))
        assert response.status_code == 422, response.text

    @pytest.mark.asyncio
    async def test_old_workspace_without_plan_still_works(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        payload = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()["payload"]
        assert "lighting_plan" not in payload or payload.get("lighting_plan") is None
        plan = draft_lighting_plan(payload)
        assert plan.enabled is True

    @pytest.mark.asyncio
    async def test_apply_syncs_support_context(self, auth_client):
        workspace_id = _seed_and_upload(auth_client)
        _patch_lighting(
            auth_client,
            workspace_id,
            {
                "enabled": False,
                "illumination_mode": "non_illuminated",
                "psu_strategy": "not_required",
                "is_confirmed": True,
            },
        )
        workspace = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()
        assert workspace["payload"]["support_context"]["illuminated"] is False
