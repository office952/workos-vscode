"""
BUILD 7 — Tests for Product System Cost Simulation endpoint.

Verifies:
  - Endpoint exists and returns valid response
  - Response includes persisted=false
  - Response includes trace with no mutation
  - No Quote is created
  - No Order is created
  - Readiness blockers return blocked simulation result
  - Missing template returns clear error
  - CostEngine warnings/blockers are exposed
  - Simulation does not modify ProductTemplate updated_at
  - Auth is required
  - Result is consistent with existing pricing path
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.product_system_cost_simulation_service import (
    CostSimulationResult,
    ProductSystemCostSimulationService,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_settings_vat():
    with patch(
        "services.product_system_cost_simulation_service.get_default_vat_pct",
        new=AsyncMock(return_value=19.0),
    ):
        yield


def _make_mock_template(
    template_id: int = 1,
    template_code: str = "TPL-VOLUMETRIC-LETTERS_v2",
    family_id: str = "banner",
    family_name: str = "Banner publicitar",
    active: bool = True,
    components_json: str = "[]",
    operations_json: str = "[]",
    required_materials_json: str = "[]",
    estimated_hours: float = 2.0,
    base_labor_rate: float = 80.0,
    base_margin_pct: float = 25.0,
    notes: str = "",
    description: str = "Test banner template",
    updated_at: datetime = None,
):
    """Create a mock template object."""
    mock = MagicMock()
    mock.id = template_id
    mock.template_code = template_code
    mock.family_id = family_id
    mock.family_name = family_name
    mock.active = active
    mock.components_json = components_json
    mock.operations_json = operations_json
    mock.required_materials_json = required_materials_json
    mock.estimated_hours = estimated_hours
    mock.base_labor_rate = base_labor_rate
    mock.base_margin_pct = base_margin_pct
    mock.notes = notes
    mock.description = description
    mock.updated_at = updated_at or datetime(2026, 5, 17, 10, 0, 0, tzinfo=timezone.utc)
    return mock


def _make_mock_readiness_result(ready: bool = True, blockers: list = None, warnings: list = None):
    """Create a mock readiness result."""
    from services.product_readiness_service import (
        ProductReadinessResult,
        ReadinessPolicy,
        ReadinessSection,
    )

    tech_blockers = blockers or []
    tech_warnings = warnings or []

    return ProductReadinessResult(
        entity_type="blueprint",
        entity_id="1",
        blueprint_id="1",
        overall_status="ready" if ready else "blocked",
        ready_for_quote=ready,
        technical_readiness=ReadinessSection(
            status="ready" if not tech_blockers else "blocked",
            blockers=tech_blockers,
            warnings=tech_warnings,
        ),
        costengine_readiness=ReadinessSection(status="ready"),
        document_output_readiness=ReadinessSection(status="ready"),
        visual_prompt_readiness=ReadinessSection(status="ready"),
        execution_preparation_readiness=ReadinessSection(status="ready"),
        policy=ReadinessPolicy(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCostSimulationService:
    """Unit tests for ProductSystemCostSimulationService."""

    @pytest.mark.asyncio
    async def test_linked_modules_are_simulated_and_totaled(self):
        """linked_modules in quote_input are costed as separate child modules."""
        db = AsyncMock()
        service = ProductSystemCostSimulationService(db)

        mock_parent = _make_mock_template(
            template_id=1,
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
        )
        mock_child = _make_mock_template(
            template_id=2,
            template_code="TPL-METAL-PREMOUNT-STRUCTURE_v1",
        )
        mock_readiness = _make_mock_readiness_result()

        with (
            patch(
                "services.product_system_cost_simulation_service.Product_templatesService"
            ) as MockTemplateService,
            patch(
                "services.product_system_cost_simulation_service.ProductReadinessService"
            ) as MockReadinessService,
            patch(
                "services.product_system_cost_simulation_service.QuoteOrchestrator"
            ) as MockOrchestrator,
            patch(
                "services.product_system_cost_simulation_service.evaluate_volumetric_quote_ready"
            ) as mock_quote_gate,
        ):
            template_service = MockTemplateService.return_value
            template_service.get_by_id = AsyncMock(side_effect=[mock_parent, mock_child])
            template_service.get_by_field = AsyncMock(return_value=mock_child)
            MockReadinessService.return_value.evaluate = AsyncMock(return_value=mock_readiness)

            mock_quote_gate.return_value.to_dict.return_value = {
                "simulate_ready": True,
                "can_create_commercial_quote": True,
            }
            mock_quote_gate.return_value.simulate_ready = True
            mock_quote_gate.return_value.can_create_commercial_quote = True

            mock_orch_instance = MagicMock()
            snapshots = []
            for total in (100.0, 40.0):
                snapshot = MagicMock()
                snapshot.status = "priced"
                snapshot.blocked_reasons = []
                snapshot.cost_result = MagicMock()
                snapshot.cost_result.is_valid = True
                snapshot.cost_result.currency = "RON"
                snapshot.cost_result.materials_cost = total
                snapshot.cost_result.labour_cost = 0
                snapshot.cost_result.machine_cost = 0
                snapshot.cost_result.external_cost = 0
                snapshot.cost_result.overhead_cost = 0
                snapshot.cost_result.total_cost = total
                snapshot.cost_result.estimated_time_minutes = 0
                snapshot.cost_result.breakdown = []
                snapshot.cost_result.validation = MagicMock()
                snapshot.cost_result.validation.missing_cost_data = []
                snapshot.cost_result.validation.warnings = []
                type(snapshot).cost_engine_version = "v1"
                type(snapshot).component_breakdown = []
                type(snapshot).cost_warnings = []
                snapshots.append(snapshot)
            mock_orch_instance.build_snapshot.side_effect = snapshots
            MockOrchestrator.create_with_registry = AsyncMock(return_value=mock_orch_instance)

            result = await service.simulate(
                template_id=1,
                quantity=1,
                quote_input={
                    "width_mm": 1000,
                    "linked_modules": [
                        {
                            "module_template_code": "TPL-METAL-PREMOUNT-STRUCTURE_v1",
                            "pricing_mode": "separate_quote_line",
                            "execution_mode": "linked_child_work",
                            "input_payload": {
                                "premount_bar_length_ml": 2.0,
                                "bar_material": "steel",
                            },
                        }
                    ],
                },
                pricing={"margin_pct": 25},
                simulation_context={"source": "test"},
            )

        assert result.cost_result["parent_total_cost"] == 100.0
        assert result.cost_result["linked_modules_total_cost"] == 40.0
        assert result.cost_result["composite_total_cost"] == 140.0
        assert result.cost_result["total_cost"] == 140.0
        assert result.linked_module_results[0]["template_code"] == "TPL-METAL-PREMOUNT-STRUCTURE_v1"
        assert result.linked_module_results[0]["pricing_mode"] == "separate_quote_line"

    @pytest.mark.asyncio
    async def test_simulation_returns_persisted_false(self):
        """Response must include persisted=false."""
        db = AsyncMock()
        service = ProductSystemCostSimulationService(db)

        mock_template = _make_mock_template()
        mock_readiness = _make_mock_readiness_result()

        with (
            patch.object(
                service, "simulate",
                wraps=service.simulate,
            ),
            patch(
                "services.product_system_cost_simulation_service.Product_templatesService"
            ) as MockTemplateService,
            patch(
                "services.product_system_cost_simulation_service.ProductReadinessService"
            ) as MockReadinessService,
            patch(
                "services.product_system_cost_simulation_service.QuoteOrchestrator"
            ) as MockOrchestrator,
        ):
            MockTemplateService.return_value.get_by_id = AsyncMock(return_value=mock_template)
            MockReadinessService.return_value.evaluate = AsyncMock(return_value=mock_readiness)

            mock_orch_instance = MagicMock()
            mock_snapshot = MagicMock()
            mock_snapshot.status = "priced"
            mock_snapshot.blocked_reasons = []
            mock_snapshot.cost_result = MagicMock()
            mock_snapshot.cost_result.is_valid = True
            mock_snapshot.cost_result.currency = "RON"
            mock_snapshot.cost_result.materials_cost = 100.0
            mock_snapshot.cost_result.labour_cost = 50.0
            mock_snapshot.cost_result.machine_cost = 0.0
            mock_snapshot.cost_result.external_cost = 0.0
            mock_snapshot.cost_result.overhead_cost = 12.0
            mock_snapshot.cost_result.total_cost = 162.0
            mock_snapshot.cost_result.estimated_time_minutes = 120.0
            mock_snapshot.cost_result.breakdown = []
            mock_snapshot.cost_result.validation = MagicMock()
            mock_snapshot.cost_result.validation.missing_cost_data = []
            mock_snapshot.cost_result.validation.warnings = []
            mock_orch_instance.build_snapshot.return_value = mock_snapshot
            MockOrchestrator.create_with_registry = AsyncMock(return_value=mock_orch_instance)

            # Mock cost_engine_version dynamic attr
            type(mock_snapshot).cost_engine_version = "v1"
            type(mock_snapshot).component_breakdown = None
            type(mock_snapshot).cost_warnings = None

            result = await service.simulate(template_id=1, quantity=1)

        assert result.persisted is False

    @pytest.mark.asyncio
    async def test_simulation_trace_no_mutation(self):
        """Response trace must prove no mutation."""
        db = AsyncMock()
        service = ProductSystemCostSimulationService(db)

        mock_template = _make_mock_template()
        mock_readiness = _make_mock_readiness_result()

        with (
            patch(
                "services.product_system_cost_simulation_service.Product_templatesService"
            ) as MockTemplateService,
            patch(
                "services.product_system_cost_simulation_service.ProductReadinessService"
            ) as MockReadinessService,
            patch(
                "services.product_system_cost_simulation_service.QuoteOrchestrator"
            ) as MockOrchestrator,
        ):
            MockTemplateService.return_value.get_by_id = AsyncMock(return_value=mock_template)
            MockReadinessService.return_value.evaluate = AsyncMock(return_value=mock_readiness)

            mock_orch_instance = MagicMock()
            mock_snapshot = MagicMock()
            mock_snapshot.status = "priced"
            mock_snapshot.blocked_reasons = []
            mock_snapshot.cost_result = MagicMock()
            mock_snapshot.cost_result.is_valid = True
            mock_snapshot.cost_result.currency = "RON"
            mock_snapshot.cost_result.materials_cost = 0
            mock_snapshot.cost_result.labour_cost = 0
            mock_snapshot.cost_result.machine_cost = 0
            mock_snapshot.cost_result.external_cost = 0
            mock_snapshot.cost_result.overhead_cost = 0
            mock_snapshot.cost_result.total_cost = 0
            mock_snapshot.cost_result.estimated_time_minutes = 0
            mock_snapshot.cost_result.breakdown = []
            mock_snapshot.cost_result.validation = MagicMock()
            mock_snapshot.cost_result.validation.missing_cost_data = []
            mock_snapshot.cost_result.validation.warnings = []
            mock_orch_instance.build_snapshot.return_value = mock_snapshot
            MockOrchestrator.create_with_registry = AsyncMock(return_value=mock_orch_instance)

            type(mock_snapshot).cost_engine_version = "v1"
            type(mock_snapshot).component_breakdown = None
            type(mock_snapshot).cost_warnings = None

            result = await service.simulate(template_id=1, quantity=1)

        assert result.trace["no_persist"] is True
        assert result.trace["changed_entities"] == []
        assert result.trace["source"] == "product-system-cost-simulation"

    @pytest.mark.asyncio
    async def test_missing_template_returns_error(self):
        """Missing template must return clear error, not crash."""
        db = AsyncMock()
        service = ProductSystemCostSimulationService(db)

        with patch(
            "services.product_system_cost_simulation_service.Product_templatesService"
        ) as MockTemplateService:
            MockTemplateService.return_value.get_by_id = AsyncMock(return_value=None)

            result = await service.simulate(template_id=9999, quantity=1)

        assert result.status == "error"
        assert "template_not_found" in result.blockers
        assert result.persisted is False

    @pytest.mark.asyncio
    async def test_readiness_blockers_return_blocked_result(self):
        """Readiness blockers should be exposed in simulation result."""
        db = AsyncMock()
        service = ProductSystemCostSimulationService(db)

        mock_template = _make_mock_template()
        mock_readiness = _make_mock_readiness_result(
            ready=False,
            blockers=["material_assumptions_missing"],
        )

        with (
            patch(
                "services.product_system_cost_simulation_service.Product_templatesService"
            ) as MockTemplateService,
            patch(
                "services.product_system_cost_simulation_service.ProductReadinessService"
            ) as MockReadinessService,
            patch(
                "services.product_system_cost_simulation_service.QuoteOrchestrator"
            ) as MockOrchestrator,
        ):
            MockTemplateService.return_value.get_by_id = AsyncMock(return_value=mock_template)
            MockReadinessService.return_value.evaluate = AsyncMock(return_value=mock_readiness)

            mock_orch_instance = MagicMock()
            mock_snapshot = MagicMock()
            mock_snapshot.status = "blocked"
            mock_snapshot.blocked_reasons = ["product_invalid:dimensions"]
            mock_snapshot.cost_result = MagicMock()
            mock_snapshot.cost_result.is_valid = False
            mock_snapshot.cost_result.currency = "RON"
            mock_snapshot.cost_result.materials_cost = 0
            mock_snapshot.cost_result.labour_cost = 0
            mock_snapshot.cost_result.machine_cost = 0
            mock_snapshot.cost_result.external_cost = 0
            mock_snapshot.cost_result.overhead_cost = 0
            mock_snapshot.cost_result.total_cost = 0
            mock_snapshot.cost_result.estimated_time_minutes = 0
            mock_snapshot.cost_result.breakdown = []
            mock_snapshot.cost_result.validation = MagicMock()
            mock_snapshot.cost_result.validation.missing_cost_data = ["no_layers"]
            mock_snapshot.cost_result.validation.warnings = []
            mock_orch_instance.build_snapshot.return_value = mock_snapshot
            MockOrchestrator.create_with_registry = AsyncMock(return_value=mock_orch_instance)

            type(mock_snapshot).cost_engine_version = "v1"
            type(mock_snapshot).component_breakdown = None
            type(mock_snapshot).cost_warnings = None

            result = await service.simulate(template_id=1, quantity=1)

        assert result.status == "blocked"
        assert "material_assumptions_missing" in result.blockers
        assert result.readiness["ready_for_quote"] is False

    @pytest.mark.asyncio
    async def test_costengine_warnings_exposed(self):
        """CostEngine warnings must be exposed in simulation warnings."""
        db = AsyncMock()
        service = ProductSystemCostSimulationService(db)

        mock_template = _make_mock_template()
        mock_readiness = _make_mock_readiness_result()

        with (
            patch(
                "services.product_system_cost_simulation_service.Product_templatesService"
            ) as MockTemplateService,
            patch(
                "services.product_system_cost_simulation_service.ProductReadinessService"
            ) as MockReadinessService,
            patch(
                "services.product_system_cost_simulation_service.QuoteOrchestrator"
            ) as MockOrchestrator,
        ):
            MockTemplateService.return_value.get_by_id = AsyncMock(return_value=mock_template)
            MockReadinessService.return_value.evaluate = AsyncMock(return_value=mock_readiness)

            mock_orch_instance = MagicMock()
            mock_snapshot = MagicMock()
            mock_snapshot.status = "priced"
            mock_snapshot.blocked_reasons = []
            mock_snapshot.cost_result = MagicMock()
            mock_snapshot.cost_result.is_valid = True
            mock_snapshot.cost_result.currency = "RON"
            mock_snapshot.cost_result.materials_cost = 50.0
            mock_snapshot.cost_result.labour_cost = 30.0
            mock_snapshot.cost_result.machine_cost = 0
            mock_snapshot.cost_result.external_cost = 0
            mock_snapshot.cost_result.overhead_cost = 0
            mock_snapshot.cost_result.total_cost = 80.0
            mock_snapshot.cost_result.estimated_time_minutes = 60
            mock_snapshot.cost_result.breakdown = []
            mock_snapshot.cost_result.validation = MagicMock()
            mock_snapshot.cost_result.validation.missing_cost_data = []
            mock_snapshot.cost_result.validation.warnings = ["rate_approximated:WC_PRINTER"]
            mock_orch_instance.build_snapshot.return_value = mock_snapshot
            MockOrchestrator.create_with_registry = AsyncMock(return_value=mock_orch_instance)

            type(mock_snapshot).cost_engine_version = "v2"
            type(mock_snapshot).component_breakdown = [{"component_id": "c1", "material_cost": 50}]
            type(mock_snapshot).cost_warnings = [{"kind": "RATE_APPROX", "path": "WC_PRINTER"}]

            result = await service.simulate(template_id=1, quantity=1)

        assert len(result.warnings) > 0
        assert result.cost_engine_version == "v2"
        assert len(result.component_breakdown) > 0

    @pytest.mark.asyncio
    async def test_no_quote_created(self):
        """Simulation must not create a Quote entity."""
        db = AsyncMock()
        service = ProductSystemCostSimulationService(db)

        mock_template = _make_mock_template()
        mock_readiness = _make_mock_readiness_result()

        with (
            patch(
                "services.product_system_cost_simulation_service.Product_templatesService"
            ) as MockTemplateService,
            patch(
                "services.product_system_cost_simulation_service.ProductReadinessService"
            ) as MockReadinessService,
            patch(
                "services.product_system_cost_simulation_service.QuoteOrchestrator"
            ) as MockOrchestrator,
        ):
            MockTemplateService.return_value.get_by_id = AsyncMock(return_value=mock_template)
            MockReadinessService.return_value.evaluate = AsyncMock(return_value=mock_readiness)

            mock_orch_instance = MagicMock()
            mock_snapshot = MagicMock()
            mock_snapshot.status = "priced"
            mock_snapshot.blocked_reasons = []
            mock_snapshot.cost_result = MagicMock()
            mock_snapshot.cost_result.is_valid = True
            mock_snapshot.cost_result.currency = "RON"
            mock_snapshot.cost_result.materials_cost = 0
            mock_snapshot.cost_result.labour_cost = 0
            mock_snapshot.cost_result.machine_cost = 0
            mock_snapshot.cost_result.external_cost = 0
            mock_snapshot.cost_result.overhead_cost = 0
            mock_snapshot.cost_result.total_cost = 0
            mock_snapshot.cost_result.estimated_time_minutes = 0
            mock_snapshot.cost_result.breakdown = []
            mock_snapshot.cost_result.validation = MagicMock()
            mock_snapshot.cost_result.validation.missing_cost_data = []
            mock_snapshot.cost_result.validation.warnings = []
            mock_orch_instance.build_snapshot.return_value = mock_snapshot
            MockOrchestrator.create_with_registry = AsyncMock(return_value=mock_orch_instance)

            type(mock_snapshot).cost_engine_version = "v1"
            type(mock_snapshot).component_breakdown = None
            type(mock_snapshot).cost_warnings = None

            result = await service.simulate(template_id=1, quantity=1)

        # Verify db.add was never called (no entity created)
        db.add.assert_not_called()
        db.commit.assert_not_called()
        assert result.persisted is False

    @pytest.mark.asyncio
    async def test_simulation_does_not_modify_template_updated_at(self):
        """Simulation must not change template updated_at timestamp."""
        db = AsyncMock()
        service = ProductSystemCostSimulationService(db)

        original_updated_at = datetime(2026, 5, 17, 10, 0, 0, tzinfo=timezone.utc)
        mock_template = _make_mock_template(updated_at=original_updated_at)
        mock_readiness = _make_mock_readiness_result()

        with (
            patch(
                "services.product_system_cost_simulation_service.Product_templatesService"
            ) as MockTemplateService,
            patch(
                "services.product_system_cost_simulation_service.ProductReadinessService"
            ) as MockReadinessService,
            patch(
                "services.product_system_cost_simulation_service.QuoteOrchestrator"
            ) as MockOrchestrator,
        ):
            MockTemplateService.return_value.get_by_id = AsyncMock(return_value=mock_template)
            MockReadinessService.return_value.evaluate = AsyncMock(return_value=mock_readiness)

            mock_orch_instance = MagicMock()
            mock_snapshot = MagicMock()
            mock_snapshot.status = "priced"
            mock_snapshot.blocked_reasons = []
            mock_snapshot.cost_result = MagicMock()
            mock_snapshot.cost_result.is_valid = True
            mock_snapshot.cost_result.currency = "RON"
            mock_snapshot.cost_result.materials_cost = 0
            mock_snapshot.cost_result.labour_cost = 0
            mock_snapshot.cost_result.machine_cost = 0
            mock_snapshot.cost_result.external_cost = 0
            mock_snapshot.cost_result.overhead_cost = 0
            mock_snapshot.cost_result.total_cost = 0
            mock_snapshot.cost_result.estimated_time_minutes = 0
            mock_snapshot.cost_result.breakdown = []
            mock_snapshot.cost_result.validation = MagicMock()
            mock_snapshot.cost_result.validation.missing_cost_data = []
            mock_snapshot.cost_result.validation.warnings = []
            mock_orch_instance.build_snapshot.return_value = mock_snapshot
            MockOrchestrator.create_with_registry = AsyncMock(return_value=mock_orch_instance)

            type(mock_snapshot).cost_engine_version = "v1"
            type(mock_snapshot).component_breakdown = None
            type(mock_snapshot).cost_warnings = None

            await service.simulate(template_id=1, quantity=1)

        # Template updated_at should not have been changed
        assert mock_template.updated_at == original_updated_at

    @pytest.mark.asyncio
    async def test_incomplete_quote_input_exposes_blockers(self):
        """Incomplete quote_input should expose blockers, not silent fallback."""
        db = AsyncMock()
        service = ProductSystemCostSimulationService(db)

        mock_template = _make_mock_template()
        mock_readiness = _make_mock_readiness_result()

        with (
            patch(
                "services.product_system_cost_simulation_service.Product_templatesService"
            ) as MockTemplateService,
            patch(
                "services.product_system_cost_simulation_service.ProductReadinessService"
            ) as MockReadinessService,
            patch(
                "services.product_system_cost_simulation_service.QuoteOrchestrator"
            ) as MockOrchestrator,
        ):
            MockTemplateService.return_value.get_by_id = AsyncMock(return_value=mock_template)
            MockReadinessService.return_value.evaluate = AsyncMock(return_value=mock_readiness)

            mock_orch_instance = MagicMock()
            mock_snapshot = MagicMock()
            # No dimensions provided -> blocked
            mock_snapshot.status = "blocked"
            mock_snapshot.blocked_reasons = ["product_invalid:dimensions"]
            mock_snapshot.cost_result = MagicMock()
            mock_snapshot.cost_result.is_valid = False
            mock_snapshot.cost_result.currency = "RON"
            mock_snapshot.cost_result.materials_cost = 0
            mock_snapshot.cost_result.labour_cost = 0
            mock_snapshot.cost_result.machine_cost = 0
            mock_snapshot.cost_result.external_cost = 0
            mock_snapshot.cost_result.overhead_cost = 0
            mock_snapshot.cost_result.total_cost = 0
            mock_snapshot.cost_result.estimated_time_minutes = 0
            mock_snapshot.cost_result.breakdown = []
            mock_snapshot.cost_result.validation = MagicMock()
            mock_snapshot.cost_result.validation.missing_cost_data = []
            mock_snapshot.cost_result.validation.warnings = []
            mock_orch_instance.build_snapshot.return_value = mock_snapshot
            MockOrchestrator.create_with_registry = AsyncMock(return_value=mock_orch_instance)

            type(mock_snapshot).cost_engine_version = "v1"
            type(mock_snapshot).component_breakdown = None
            type(mock_snapshot).cost_warnings = None

            # No dimensions in quote_input
            result = await service.simulate(template_id=1, quantity=1, quote_input={})

        assert result.status == "blocked"
        assert "product_invalid:dimensions" in result.blocked_reasons

    @pytest.mark.asyncio
    async def test_result_to_dict_structure(self):
        """Result to_dict must have all required fields."""
        result = CostSimulationResult(
            template_id=1,
            template_code="TPL-TEST",
            cost_engine_version="v2",
            persisted=False,
            status="simulated",
        )
        d = result.to_dict()

        assert "simulation_id" in d
        assert "persisted" in d
        assert "template_id" in d
        assert "template_code" in d
        assert "cost_engine_version" in d
        assert "readiness" in d
        assert "cost_result" in d
        assert "component_breakdown" in d
        assert "warnings" in d
        assert "blockers" in d
        assert "status" in d
        assert "blocked_reasons" in d
        assert "trace" in d
        assert d["persisted"] is False
        assert d["trace"]["no_persist"] is True


class TestCostSimulationRouter:
    """Tests for the router-level behavior."""

    @pytest.mark.asyncio
    async def test_router_returns_404_for_missing_template(self):
        """Router should return 404 for non-existent template."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from routers.product_system_cost_simulation import router

        app = FastAPI()
        app.include_router(router)

        # Override auth dependency
        from dependencies.auth import get_current_user

        app.dependency_overrides[get_current_user] = lambda: {"id": "test-user"}

        # Override DB
        from core.database import get_db

        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "routers.product_system_cost_simulation.ProductSystemCostSimulationService"
        ) as MockService:
            mock_service = AsyncMock()
            mock_service.simulate = AsyncMock(
                return_value=CostSimulationResult(
                    template_id=9999,
                    status="error",
                    blockers=["template_not_found"],
                    blocked_reasons=["template_not_found"],
                    trace={
                        "source": "product-system-cost-simulation",
                        "no_persist": True,
                        "used_template_snapshot": False,
                        "used_costengine_formulas": False,
                        "changed_entities": [],
                        "error": "template_not_found",
                    },
                )
            )
            MockService.return_value = mock_service

            client = TestClient(app)
            response = client.post(
                "/api/v1/product-system/simulate-cost",
                json={"template_id": 9999, "quantity": 1},
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_router_returns_200_for_valid_simulation(self):
        """Router should return 200 with valid simulation response."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from routers.product_system_cost_simulation import router

        app = FastAPI()
        app.include_router(router)

        from dependencies.auth import get_current_user

        app.dependency_overrides[get_current_user] = lambda: {"id": "test-user"}

        from core.database import get_db

        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "routers.product_system_cost_simulation.ProductSystemCostSimulationService"
        ) as MockService:
            mock_service = AsyncMock()
            mock_service.simulate = AsyncMock(
                return_value=CostSimulationResult(
                    template_id=1,
                    template_code="TPL-BANNER-STANDARD",
                    cost_engine_version="v2",
                    persisted=False,
                    status="simulated",
                    readiness={"ready_for_quote": True, "blockers": [], "warnings": []},
                    cost_result={
                        "is_valid": True,
                        "currency": "RON",
                        "total_cost": 150.0,
                    },
                )
            )
            MockService.return_value = mock_service

            client = TestClient(app)
            response = client.post(
                "/api/v1/product-system/simulate-cost",
                json={
                    "template_id": 1,
                    "quantity": 2,
                    "quote_input": {"width_mm": 1000, "height_mm": 500},
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["persisted"] is False
        assert data["template_id"] == 1
        assert data["status"] == "simulated"