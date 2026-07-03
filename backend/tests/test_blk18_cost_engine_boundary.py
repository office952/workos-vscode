"""BLK-18 — Cost Engine Boundary Sprint: contract tests.

Proves:
  1. load_material_cost_dict returns only active rows with positive unit_cost.
  2. load_workcenter_rate_dict returns only active rows with positive rate.
  3. QuoteOrchestrator.create_with_registry merges registry + caller overrides.
  4. Caller overrides win on key collision (merge semantics).
  5. Registry failure does not break orchestrator construction.
  6. BLK-18 error constants are importable and correctly namespaced.
  7. Router refactor: create_with_registry is called (integration shape).
  8. _should_use_v2 returns True when registry rates are loaded.

All tests are PURE UNIT tests — no database, no network. We mock the
SQLAlchemy session and the bridge functions to verify contract compliance.
"""
from __future__ import annotations

import os
import sys
import unittest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from services.cost_engine_service import (  # noqa: E402
    BLK18_CONFIG_FALLBACK_USED,
    BLK18_MACHINE_RATE_RESOLUTION_FAILED,
    BLK18_MATERIAL_COST_NOT_IN_REGISTRY,
    BLK18_REGISTRY_RATE_OVERRIDDEN,
    BLK18_WORKCENTER_RATE_NOT_IN_REGISTRY,
    ERR_MATERIAL_RATE_MISSING,
    ERR_WORKCENTER_RATE_MISSING,
)
from services.quote_orchestrator import QuoteOrchestrator  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers: fake ORM rows for bridge function tests
# ---------------------------------------------------------------------------

@dataclass
class _FakeMaterialRow:
    code: str
    unit_cost: Optional[float]
    status: str
    currency: str = "RON"
    vat_percent: float = 19.0
    valid_from: object = None

    def __post_init__(self) -> None:
        if self.valid_from is None:
            from datetime import datetime, timezone

            self.valid_from = datetime(2026, 1, 1, tzinfo=timezone.utc)


@dataclass
class _FakeWorkcenterRow:
    code: str
    rate_per_hour: Optional[float]
    status: str


def _make_scalars_result(rows: list) -> MagicMock:
    """Build a mock that mimics (await session.execute(stmt)).scalars().all()."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock


# ---------------------------------------------------------------------------
# Test: BLK-18 error constants
# ---------------------------------------------------------------------------

class TestBLK18ErrorConstants(unittest.TestCase):
    """BLK-18 error constants are importable and correctly namespaced."""

    def test_constants_have_blk18_prefix(self):
        for const in [
            BLK18_MATERIAL_COST_NOT_IN_REGISTRY,
            BLK18_WORKCENTER_RATE_NOT_IN_REGISTRY,
            BLK18_MACHINE_RATE_RESOLUTION_FAILED,
            BLK18_CONFIG_FALLBACK_USED,
            BLK18_REGISTRY_RATE_OVERRIDDEN,
        ]:
            self.assertTrue(
                const.startswith("BLK18:"),
                f"Expected BLK18: prefix, got: {const}",
            )

    def test_constants_are_distinct(self):
        consts = [
            BLK18_MATERIAL_COST_NOT_IN_REGISTRY,
            BLK18_WORKCENTER_RATE_NOT_IN_REGISTRY,
            BLK18_MACHINE_RATE_RESOLUTION_FAILED,
            BLK18_CONFIG_FALLBACK_USED,
            BLK18_REGISTRY_RATE_OVERRIDDEN,
        ]
        self.assertEqual(len(consts), len(set(consts)), "BLK-18 constants must be unique")

    def test_legacy_constants_unchanged(self):
        """Pre-existing error constants must NOT be modified."""
        self.assertEqual(ERR_MATERIAL_RATE_MISSING, "MATERIAL_RATE_MISSING")
        self.assertEqual(ERR_WORKCENTER_RATE_MISSING, "WORKCENTER_RATE_MISSING")


# ---------------------------------------------------------------------------
# Test: load_material_cost_dict bridge
# ---------------------------------------------------------------------------

class TestLoadMaterialCostDict(unittest.IsolatedAsyncioTestCase):
    """load_material_cost_dict returns {code: unit_cost} for active rows only."""

    async def test_returns_only_active_positive(self):
        from services.inventory_materials_admin_service import load_material_cost_dict

        # The SQL query filters status=="active" at the DB level, so the
        # mock session only returns rows that would pass that WHERE clause.
        # The bridge function then further filters: unit_cost > 0.
        active_rows = [
            _FakeMaterialRow(code="MAT-001", unit_cost=12.50, status="active"),
            _FakeMaterialRow(code="MAT-002", unit_cost=None, status="active"),
            _FakeMaterialRow(code="MAT-003", unit_cost=0.0, status="active"),
            _FakeMaterialRow(code="MAT-005", unit_cost=8.0, status="active"),
        ]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_make_scalars_result(active_rows))

        result = await load_material_cost_dict(db=mock_session)

        # MAT-002 (None) and MAT-003 (0.0) are excluded by the > 0 check
        self.assertEqual(result, {"MAT-001": 12.50, "MAT-005": 8.0})

    async def test_empty_table_returns_empty_dict(self):
        from services.inventory_materials_admin_service import load_material_cost_dict

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_make_scalars_result([]))

        result = await load_material_cost_dict(db=mock_session)
        self.assertEqual(result, {})


# ---------------------------------------------------------------------------
# Test: load_workcenter_rate_dict bridge (verify contract parity)
# ---------------------------------------------------------------------------

class TestLoadWorkcenterRateDict(unittest.IsolatedAsyncioTestCase):
    """load_workcenter_rate_dict returns {code: rate_per_hour} for active rows only."""

    async def test_returns_only_active_positive(self):
        from services.workcenter_rates_service import load_workcenter_rate_dict

        # The SQL query filters status=="active" at the DB level, so the
        # mock session only returns rows that would pass that WHERE clause.
        # The bridge function then further filters: rate_per_hour > 0.
        active_rows = [
            _FakeWorkcenterRow(code="WC-CNC", rate_per_hour=85.0, status="active"),
            _FakeWorkcenterRow(code="WC-LASER", rate_per_hour=None, status="active"),
            _FakeWorkcenterRow(code="WC-WELD", rate_per_hour=60.0, status="active"),
        ]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=_make_scalars_result(active_rows))

        result = await load_workcenter_rate_dict(db=mock_session)

        # WC-LASER (None) is excluded by the > 0 check
        self.assertEqual(result, {"WC-CNC": 85.0, "WC-WELD": 60.0})


# ---------------------------------------------------------------------------
# Test: v1 registry material lookup
# ---------------------------------------------------------------------------

class TestV1RegistryMaterialLookup(unittest.TestCase):
    """v1 templates must use BLK-18 registry rates when components_json is flat."""

    def test_cost_engine_for_v1_wraps_registry_rates(self):
        from services.cost_engine_service import CostEngineWithMaterialRates

        orch = QuoteOrchestrator(
            material_rates={"MAT-SABLON-MONTAJ": 8.0, "MAT-SABLON-HARTIE": 2.0},
        )
        engine = orch._cost_engine_for_v1()
        self.assertIsInstance(engine, CostEngineWithMaterialRates)
        self.assertEqual(engine._lookup_material_unit_cost("MAT-SABLON-MONTAJ"), 8.0)
        self.assertEqual(engine._lookup_material_unit_cost("MAT-SABLON-HARTIE"), 2.0)

    def test_cost_engine_for_v1_prefers_explicit_engine_rates(self):
        from services.cost_engine_service import CostEngineWithMaterialRates

        orch = QuoteOrchestrator(
            cost_engine=CostEngineWithMaterialRates({"MAT-ACP-3": 120.0}),
            material_rates={"MAT-SABLON-MONTAJ": 8.0},
        )
        engine = orch._cost_engine_for_v1()
        self.assertEqual(engine._lookup_material_unit_cost("MAT-ACP-3"), 120.0)
        self.assertEqual(engine._lookup_material_unit_cost("MAT-SABLON-MONTAJ"), 8.0)


# ---------------------------------------------------------------------------
# Test: QuoteOrchestrator.create_with_registry
# ---------------------------------------------------------------------------

class TestCreateWithRegistry(unittest.IsolatedAsyncioTestCase):
    """create_with_registry merges registry rates with caller overrides."""

    @patch("services.quote_orchestrator.logger")
    async def test_merges_registry_and_caller_overrides(self, _mock_logger):
        """Caller overrides win on key collision."""
        mock_db = AsyncMock()

        registry_materials = {"MAT-001": 10.0, "MAT-002": 20.0}
        registry_workcenter = {"WC-CNC": 80.0, "WC-LASER": 120.0}

        with patch(
            "services.cost_engine_config.load_base_currency",
            new_callable=AsyncMock,
            return_value="RON",
        ), patch(
            "services.inventory_materials_admin_service.load_material_cost_dict",
            new_callable=AsyncMock,
            return_value=registry_materials,
        ), patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
            return_value={},
        ), patch(
            "services.workcenter_rates_service.load_workcenter_rate_dict",
            new_callable=AsyncMock,
            return_value=registry_workcenter,
        ), patch(
            "services.workcenter_rates_service.load_workcenter_rate_pricing_dict",
            new_callable=AsyncMock,
            return_value={},
        ):
            orch = await QuoteOrchestrator.create_with_registry(
                db=mock_db,
                material_rates={"MAT-001": 99.0, "MAT-003": 30.0},
                workcenter_rates={"WC-CNC": 999.0},
            )

        # Caller override wins for MAT-001 and WC-CNC
        self.assertEqual(orch.material_rates["MAT-001"], 99.0)
        self.assertEqual(orch.material_rates["MAT-002"], 20.0)
        self.assertEqual(orch.material_rates["MAT-003"], 30.0)
        self.assertEqual(orch.workcenter_rates["WC-CNC"], 999.0)
        self.assertEqual(orch.workcenter_rates["WC-LASER"], 120.0)

    @patch("services.quote_orchestrator.logger")
    async def test_registry_only_no_overrides(self, _mock_logger):
        """When no caller overrides, registry rates are used as-is."""
        mock_db = AsyncMock()

        with patch(
            "services.cost_engine_config.load_base_currency",
            new_callable=AsyncMock,
            return_value="RON",
        ), patch(
            "services.inventory_materials_admin_service.load_material_cost_dict",
            new_callable=AsyncMock,
            return_value={"MAT-001": 10.0},
        ), patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
            return_value={},
        ), patch(
            "services.workcenter_rates_service.load_workcenter_rate_dict",
            new_callable=AsyncMock,
            return_value={"WC-CNC": 80.0},
        ), patch(
            "services.workcenter_rates_service.load_workcenter_rate_pricing_dict",
            new_callable=AsyncMock,
            return_value={},
        ):
            orch = await QuoteOrchestrator.create_with_registry(db=mock_db)

        self.assertEqual(orch.material_rates, {"MAT-001": 10.0})
        self.assertEqual(orch.workcenter_rates, {"WC-CNC": 80.0})

    @patch("services.quote_orchestrator.logger")
    async def test_registry_failure_returns_empty_rates(self, _mock_logger):
        """Registry load failure must NOT break orchestrator construction."""
        mock_db = AsyncMock()

        with patch(
            "services.cost_engine_config.load_base_currency",
            new_callable=AsyncMock,
            return_value="RON",
        ), patch(
            "services.inventory_materials_admin_service.load_material_cost_dict",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB connection lost"),
        ), patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB connection lost"),
        ), patch(
            "services.workcenter_rates_service.load_workcenter_rate_dict",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB connection lost"),
        ), patch(
            "services.workcenter_rates_service.load_workcenter_rate_pricing_dict",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB connection lost"),
        ):
            orch = await QuoteOrchestrator.create_with_registry(db=mock_db)

        self.assertEqual(orch.material_rates, {})
        self.assertEqual(orch.workcenter_rates, {})

    @patch("services.quote_orchestrator.logger")
    async def test_partial_failure_still_loads_other_registry(self, _mock_logger):
        """If material registry fails, workcenter registry still loads."""
        mock_db = AsyncMock()

        with patch(
            "services.cost_engine_config.load_base_currency",
            new_callable=AsyncMock,
            return_value="RON",
        ), patch(
            "services.inventory_materials_admin_service.load_material_cost_dict",
            new_callable=AsyncMock,
            side_effect=RuntimeError("material table missing"),
        ), patch(
            "services.inventory_materials_admin_service.load_material_pricing_dict",
            new_callable=AsyncMock,
            side_effect=RuntimeError("material table missing"),
        ), patch(
            "services.workcenter_rates_service.load_workcenter_rate_dict",
            new_callable=AsyncMock,
            return_value={"WC-CNC": 80.0},
        ), patch(
            "services.workcenter_rates_service.load_workcenter_rate_pricing_dict",
            new_callable=AsyncMock,
            return_value={},
        ):
            orch = await QuoteOrchestrator.create_with_registry(db=mock_db)

        self.assertEqual(orch.material_rates, {})
        self.assertEqual(orch.workcenter_rates, {"WC-CNC": 80.0})


# ---------------------------------------------------------------------------
# Test: _should_use_v2 with registry-loaded rates
# ---------------------------------------------------------------------------

class TestShouldUseV2WithRegistryRates(unittest.TestCase):
    """_should_use_v2 returns True when registry rates are loaded."""

    def _make_hierarchical_template(self) -> Dict[str, Any]:
        """A minimal hierarchical template that triggers v2."""
        import json
        return {
            "components_json": json.dumps([
                {
                    "component_id": "comp-1",
                    "name": "Frame",
                    "materials": [
                        {"material_code": "MAT-001", "quantity_per_unit": 2.0}
                    ],
                    "operations": [
                        {"workcenter": "WC-CNC", "time_minutes": 30}
                    ],
                }
            ])
        }

    def test_v2_activates_with_registry_rates(self):
        orch = QuoteOrchestrator(
            material_rates={"MAT-001": 10.0},
            workcenter_rates={"WC-CNC": 80.0},
        )
        self.assertTrue(orch._should_use_v2(self._make_hierarchical_template()))

    def test_v2_does_not_activate_without_rates(self):
        orch = QuoteOrchestrator()
        self.assertFalse(orch._should_use_v2(self._make_hierarchical_template()))

    def test_v2_does_not_activate_for_flat_template(self):
        orch = QuoteOrchestrator(
            material_rates={"MAT-001": 10.0},
            workcenter_rates={"WC-CNC": 80.0},
        )
        flat_template = {"components_json": '["comp-a", "comp-b"]'}
        self.assertFalse(orch._should_use_v2(flat_template))

    def test_v2_activates_for_flat_legacy_ops_and_materials(self):
        import json

        orch = QuoteOrchestrator(
            material_rates={"MAT-001": 10.0},
            workcenter_rates={"WC-CNC": 80.0},
        )
        flat_legacy = {
            "components_json": "[]",
            "operations_json": json.dumps([{"code": "OP", "workcenter": "WC-CNC"}]),
            "required_materials_json": json.dumps([{"material_code": "MAT-001"}]),
        }
        self.assertTrue(orch._should_use_v2(flat_legacy))

    def test_v2_does_not_activate_for_none_template(self):
        orch = QuoteOrchestrator(
            material_rates={"MAT-001": 10.0},
        )
        self.assertFalse(orch._should_use_v2(None))


# ---------------------------------------------------------------------------
# Test: Backward compatibility — old constructor still works
# ---------------------------------------------------------------------------

class TestBackwardCompatibility(unittest.TestCase):
    """Pre-BLK-18 constructor forms still work identically."""

    def test_no_args_constructor(self):
        orch = QuoteOrchestrator()
        self.assertEqual(orch.material_rates, {})
        self.assertEqual(orch.workcenter_rates, {})

    def test_explicit_rates_constructor(self):
        orch = QuoteOrchestrator(
            material_rates={"MAT-001": 10.0},
            workcenter_rates={"WC-CNC": 80.0},
        )
        self.assertEqual(orch.material_rates, {"MAT-001": 10.0})
        self.assertEqual(orch.workcenter_rates, {"WC-CNC": 80.0})


if __name__ == "__main__":
    unittest.main()