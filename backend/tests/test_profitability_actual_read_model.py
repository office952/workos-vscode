"""Profitability Actual Read Model V1 — honesty and unavailable-cost rules."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.profitability_actual_read_model_service import (
    REASON_EMPLOYEE_COST_POLICY_MISSING,
    ProfitabilityActualReadModelService,
)


@pytest.mark.asyncio
async def test_missing_labor_and_materials_not_zero(monkeypatch):
    order = SimpleNamespace(
        id=973019,
        snapshot_v2_json=json.dumps(
            {
                "accepted_commercial_total": 1000.0,
                "accepted_currency": "RON",
                "estimated_internal_total": 600.0,
                "estimated_internal_cost_snapshot": {
                    "estimated_material_cost": 200.0,
                    "estimated_operation_cost": 400.0,
                },
                "commercial_price_proposal_snapshot": {},
            }
        ),
    )
    service = ProfitabilityActualReadModelService(AsyncMock())
    monkeypatch.setattr(service, "_load_order", AsyncMock(return_value=order))
    # Awaited AsyncSession contract: return completed facts (empty labor/material/open).
    # Do not leave bare AsyncMock() for db.execute — that creates unawaited coroutines.
    monkeypatch.setattr(
        service,
        "_load_actual_cost_facts",
        AsyncMock(
            return_value=(
                [],
                {
                    "available": False,
                    "value": None,
                    "reason": "actual_material_cost_missing",
                },
                None,
            )
        ),
    )
    monkeypatch.setattr(
        "services.profitability_actual_read_model_service.build_execution_actuals_read_model",
        AsyncMock(
            return_value={
                "status": "ok",
                "tasks": [
                    {
                        "task_id": "LED",
                        "assigned_employee_id": 7,
                        "session_count": 1,
                        "active_session": False,
                        "total_actual_duration_minutes": 40,
                        "first_started_at": "2026-08-02T12:00:00+00:00",
                        "last_ended_at": "2026-08-02T12:40:00+00:00",
                        "planned_minutes": None,
                        "variance_reason": "planning_minutes_source_missing",
                    }
                ],
                "reality_total_actual_time_minutes": 40.0,
            }
        ),
    )
    monkeypatch.setattr(service, "_load_plan_tasks", AsyncMock(return_value=[]))

    model = await service.build(973019)
    assert model["actual_operational_truth"]["actual_duration_minutes"]["value"] == 40.0
    assert model["actual_cost_truth"]["labor_actual_cost"]["available"] is False
    assert (
        model["actual_cost_truth"]["labor_actual_cost"]["reason"]
        == REASON_EMPLOYEE_COST_POLICY_MISSING
    )
    assert model["actual_cost_truth"]["labor_actual_cost"]["value"] is None
    assert model["profitability_result"]["actual_margin"]["amount"]["available"] is False
    assert model["profitability_result"]["estimated_margin"]["amount"]["value"] == 400.0
    assert model["mutated"]["sessions"] is False
    assert "employee_cost_policy_missing" in model["profitability_result"]["unavailable_reasons"]
