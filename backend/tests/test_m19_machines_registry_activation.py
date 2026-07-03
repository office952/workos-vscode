"""
M19 Machines Registry — Full Controlled Activation Sprint Tests.

Test categories:
  1. MachinesReadService tests
  2. RegistryLinkageValidator machine tests
  3. S30 gate flag OFF tests
  4. S30 gate flag ON tests
  5. BLK-19 machine missing/inactive/unavailable tests
  6. WRN-03 present when flag=false
  7. WRN-03 absent when flag=true and machines registry responds
  8. ProductSystem/S30/M22 regression tests
  9. Backend regression subset relevant to gate/ProductSystem
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from services.machines_read_service import MachinesReadService
from services.execution_plan_gate_service import (
    GateEvaluation,
    RegistrySnapshot,
    evaluate_gate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class MockRow:
    """Mock DB row for machines table."""

    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()


MACHINE_CNC_01 = {
    "id": 1,
    "machine_code": "MCH-CNC-ROUTER-01",
    "name": "CNC Router Primary",
    "description": "Main CNC router for panel cutting",
    "machine_type": "cnc_router",
    "workcenter_code": "WC_CNC_ROUTING",
    "operational_status": "active",
    "is_available": True,
    "manufacturer": "Biesse",
    "model": "Rover A",
    "year_acquired": 2021,
    "capabilities": ["panel_cutting", "3d_routing", "edge_profiling"],
    "capacity_metadata": {"max_sheet_width_mm": 2100, "max_sheet_length_mm": 3100},
    "is_active": True,
    "created_at": "2026-05-09T00:00:00Z",
    "updated_at": "2026-05-09T00:00:00Z",
}

MACHINE_INACTIVE = {
    **MACHINE_CNC_01,
    "id": 99,
    "machine_code": "MCH-INACTIVE-01",
    "is_active": False,
    "is_available": False,
    "operational_status": "inactive",
}

MACHINE_UNAVAILABLE = {
    **MACHINE_CNC_01,
    "id": 98,
    "machine_code": "MCH-UNAVAILABLE-01",
    "is_active": True,
    "is_available": False,
    "operational_status": "active",
}

MACHINE_MAINTENANCE = {
    **MACHINE_CNC_01,
    "id": 97,
    "machine_code": "MCH-MAINTENANCE-01",
    "is_active": True,
    "is_available": True,
    "operational_status": "maintenance",
}


def _make_mock_db(rows_by_query=None):
    """Create a mock AsyncSession that returns controlled results."""
    db = MagicMock()

    async def mock_execute(sql, params=None):
        result = MagicMock()
        sql_str = str(sql.text if hasattr(sql, 'text') else sql)

        if rows_by_query:
            for key, val in rows_by_query.items():
                if key in sql_str:
                    if isinstance(val, list):
                        mappings_mock = MagicMock()
                        mappings_mock.first.return_value = val[0] if val else None
                        mappings_mock.all.return_value = val
                        result.mappings.return_value = mappings_mock
                        result.scalar.return_value = val[0].get("_scalar") if val and "_scalar" in val[0] else (1 if val else None)
                        result.all.return_value = [(v.get("machine_code", v.get("_scalar", "")),) for v in val]
                    elif isinstance(val, int):
                        result.scalar.return_value = val
                    elif val is None:
                        mappings_mock = MagicMock()
                        mappings_mock.first.return_value = None
                        mappings_mock.all.return_value = []
                        result.mappings.return_value = mappings_mock
                        result.scalar.return_value = None
                        result.all.return_value = []
                    return result

        # Default: empty
        mappings_mock = MagicMock()
        mappings_mock.first.return_value = None
        mappings_mock.all.return_value = []
        result.mappings.return_value = mappings_mock
        result.scalar.return_value = None
        result.all.return_value = []
        return result

    db.execute = mock_execute
    return db


# ---------------------------------------------------------------------------
# Category 1: MachinesReadService tests
# ---------------------------------------------------------------------------


class TestMachinesReadService:
    """Test MachinesReadService read-only methods."""

    @pytest.mark.asyncio
    async def test_get_by_code_found(self):
        db = _make_mock_db({"machine_code = :code": [MACHINE_CNC_01]})
        svc = MachinesReadService(db)
        result = await svc.get_by_code("MCH-CNC-ROUTER-01")
        assert result is not None
        assert result["machine_code"] == "MCH-CNC-ROUTER-01"
        assert result["machine_type"] == "cnc_router"

    @pytest.mark.asyncio
    async def test_get_by_code_not_found(self):
        db = _make_mock_db({"machine_code = :code": None})
        svc = MachinesReadService(db)
        result = await svc.get_by_code("MCH-NONEXISTENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists_true(self):
        db = _make_mock_db({"machine_code = :code": [{"_scalar": 1}]})
        svc = MachinesReadService(db)
        result = await svc.exists("MCH-CNC-ROUTER-01")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        db = MagicMock()

        async def mock_exec(sql, params=None):
            result = MagicMock()
            result.scalar.return_value = None
            return result

        db.execute = mock_exec
        svc = MachinesReadService(db)
        result = await svc.exists("MCH-NONEXISTENT")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_active_true(self):
        db = _make_mock_db({"is_active FROM machines": [{"_scalar": True}]})
        svc = MachinesReadService(db)
        # Need to mock scalar properly
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar.return_value = True
        mock_db.execute = AsyncMock(return_value=mock_result)
        svc2 = MachinesReadService(mock_db)
        result = await svc2.is_active("MCH-CNC-ROUTER-01")
        assert result is True

    @pytest.mark.asyncio
    async def test_machine_available_full(self):
        db = _make_mock_db({"machine_code = :code": [MACHINE_CNC_01]})
        svc = MachinesReadService(db)
        result = await svc.machine_available("MCH-CNC-ROUTER-01")
        assert result["found"] is True
        assert result["active"] is True
        assert result["available"] is True
        assert result["operational"] is True

    @pytest.mark.asyncio
    async def test_machine_available_inactive(self):
        db = _make_mock_db({"machine_code = :code": [MACHINE_INACTIVE]})
        svc = MachinesReadService(db)
        result = await svc.machine_available("MCH-INACTIVE-01")
        assert result["found"] is True
        assert result["active"] is False

    @pytest.mark.asyncio
    async def test_machine_available_unavailable(self):
        db = _make_mock_db({"machine_code = :code": [MACHINE_UNAVAILABLE]})
        svc = MachinesReadService(db)
        result = await svc.machine_available("MCH-UNAVAILABLE-01")
        assert result["found"] is True
        assert result["active"] is True
        assert result["available"] is False

    @pytest.mark.asyncio
    async def test_machine_available_maintenance(self):
        db = _make_mock_db({"machine_code = :code": [MACHINE_MAINTENANCE]})
        svc = MachinesReadService(db)
        result = await svc.machine_available("MCH-MAINTENANCE-01")
        assert result["found"] is True
        assert result["operational"] is False

    @pytest.mark.asyncio
    async def test_check_readiness(self):
        mock_db = MagicMock()
        call_count = [0]

        async def multi_execute(sql, params=None):
            result = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                result.scalar.return_value = 14
            elif call_count[0] == 2:
                result.scalar.return_value = 14
            else:
                result.scalar.return_value = 14
            return result

        mock_db.execute = multi_execute
        svc = MachinesReadService(mock_db)
        result = await svc.check_readiness()
        assert result["ready"] is True
        assert result["row_count"] == 14
        assert result["active_count"] == 14
        assert result["available_count"] == 14

    @pytest.mark.asyncio
    async def test_check_capability(self):
        db = _make_mock_db({"machine_code = :code": [MACHINE_CNC_01]})
        svc = MachinesReadService(db)
        result = await svc.check_capability("MCH-CNC-ROUTER-01", "panel_cutting")
        assert result["found"] is True
        assert result["has_capability"] is True

    @pytest.mark.asyncio
    async def test_check_capability_missing(self):
        db = _make_mock_db({"machine_code = :code": [MACHINE_CNC_01]})
        svc = MachinesReadService(db)
        result = await svc.check_capability("MCH-CNC-ROUTER-01", "welding")
        assert result["found"] is True
        assert result["has_capability"] is False


# ---------------------------------------------------------------------------
# Category 2: RegistryLinkageValidator machine tests
# ---------------------------------------------------------------------------


class TestLinkageValidatorMachines:
    """Test ProductSystemLinkageValidator machine integration."""

    @pytest.mark.asyncio
    async def test_machine_id_wrn03_when_flag_off(self):
        """When registry_machines_live=false, machine_id emits WRN-03."""
        with patch.object(settings, 'registry_machines_live', False):
            from services.product_system_linkage_validator import ProductSystemLinkageValidator
            db = AsyncMock()
            validator = ProductSystemLinkageValidator(db)
            issues = validator._validate_machine_id(
                task_id="task_1",
                required_machine_id="MCH-CNC-ROUTER-01",
                prefix="task_templates[0]",
            )
            assert len(issues) == 1
            assert issues[0].code == "PS-WRN-03"
            assert issues[0].severity == "warning"

    @pytest.mark.asyncio
    async def test_machine_id_blocker_when_flag_on_sync(self):
        """When registry_machines_live=true, sync path emits PS-BLK-12 (Phase 4 spec)."""
        with patch.object(settings, 'registry_machines_live', True):
            from services.product_system_linkage_validator import ProductSystemLinkageValidator
            db = AsyncMock()
            validator = ProductSystemLinkageValidator(db)
            issues = validator._validate_machine_id(
                task_id="task_1",
                required_machine_id="MCH-CNC-ROUTER-01",
                prefix="task_templates[0]",
            )
            # Phase 4 spec: unresolvable machine_id + live registry → PS-BLK-12
            assert len(issues) == 1
            assert issues[0].code == "PS-BLK-12"
            assert issues[0].severity == "blocker"


# ---------------------------------------------------------------------------
# Category 3: S30 gate flag OFF tests
# ---------------------------------------------------------------------------


class TestGateFlagOff:
    """Test gate behavior when registry_machines_live=false."""

    def _make_order(self, order_id=14, code="ORD-014", snapshot_version=1):
        order = MagicMock()
        order.id = order_id
        order.code = code
        order.snapshot_version = snapshot_version
        order.snapshot_line_items = json.dumps({
            "order_id": order_id,
            "product_definition": {
                "product_id": "PROD-001",
                "product_code": "LIGHTBOX-A",
                "quantity": 2,
                "layers": [
                    {
                        "layer_id": "L-01",
                        "processes": [
                            {
                                "process_id": "P-01",
                                "type": "cnc_routing",
                                "estimated_time_minutes": 30,
                            }
                        ],
                    }
                ],
            },
            "cost_result": {
                "total_cost": 500.0,
                "estimated_time_minutes": 120,
            },
        })
        return order

    def test_wrn03_emitted_when_machines_not_live(self):
        """WRN-03 is emitted when machines_registry_available=False."""
        order = self._make_order()
        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            roles=["OP_CNC"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=False,
        )
        # Mock the productsystem_preview
        preview = MagicMock()
        preview.blockers = []
        preview.warnings = []

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(
                    order_row=order,
                    registries=registries,
                    plan_already_exists=False,
                    productsystem_preview=preview,
                )

        wrn03_found = any(w.get("code") == "WRN-03" for w in evaluation.warnings)
        assert wrn03_found, "WRN-03 should be emitted when machines registry not live"

    def test_legacy_behavior_preserved_flag_off(self):
        """Gate still returns can_generate=true with WRN-03 (not a blocker)."""
        order = self._make_order()
        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            roles=["OP_CNC"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=False,
        )
        preview = MagicMock()
        preview.blockers = []
        preview.warnings = []

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(
                    order_row=order,
                    registries=registries,
                    plan_already_exists=False,
                    productsystem_preview=preview,
                )

        assert evaluation.can_generate is True, "Legacy: WRN-03 should not block generation"


# ---------------------------------------------------------------------------
# Category 4: S30 gate flag ON tests
# ---------------------------------------------------------------------------


class TestGateFlagOn:
    """Test gate behavior when registry_machines_live=true."""

    def _make_order(self, order_id=14, code="ORD-014", snapshot_version=1):
        order = MagicMock()
        order.id = order_id
        order.code = code
        order.snapshot_version = snapshot_version
        order.snapshot_line_items = json.dumps({
            "order_id": order_id,
            "product_definition": {
                "product_id": "PROD-001",
                "product_code": "LIGHTBOX-A",
                "quantity": 2,
                "layers": [
                    {
                        "layer_id": "L-01",
                        "processes": [
                            {
                                "process_id": "P-01",
                                "type": "cnc_routing",
                                "estimated_time_minutes": 30,
                            }
                        ],
                    }
                ],
            },
            "cost_result": {
                "total_cost": 500.0,
                "estimated_time_minutes": 120,
            },
        })
        return order

    def test_wrn03_not_emitted_when_machines_live(self):
        """WRN-03 is NOT emitted when machines_registry_available=True."""
        order = self._make_order()
        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            roles=["OP_CNC"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=True,
        )
        preview = MagicMock()
        preview.blockers = []
        preview.warnings = []

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(
                    order_row=order,
                    registries=registries,
                    plan_already_exists=False,
                    productsystem_preview=preview,
                )

        wrn03_found = any(w.get("code") == "WRN-03" for w in evaluation.warnings)
        assert not wrn03_found, "WRN-03 should NOT be emitted when machines registry is live"

    def test_gate_can_generate_when_machines_live(self):
        """Gate can still generate when machines registry is live and no blockers."""
        order = self._make_order()
        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            roles=["OP_CNC"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=True,
        )
        preview = MagicMock()
        preview.blockers = []
        preview.warnings = []

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(
                    order_row=order,
                    registries=registries,
                    plan_already_exists=False,
                    productsystem_preview=preview,
                )

        assert evaluation.can_generate is True


# ---------------------------------------------------------------------------
# Category 5: BLK-19 machine missing/inactive/unavailable tests
# ---------------------------------------------------------------------------


class TestBLK19:
    """Test BLK-19 blocker paths via _validate_machine_async."""

    @pytest.mark.asyncio
    async def test_blk19_machine_not_found(self):
        """BLK-19 when machine_id not found in registry."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        # Mock machines service to return not found
        validator._machines_svc = AsyncMock()
        validator._machines_svc.machine_available = AsyncMock(return_value={
            "found": False, "active": False, "available": False, "operational": False, "machine": None
        })
        validator._machines_svc.get_by_type = AsyncMock(return_value=[])

        with patch.object(settings, 'registry_machines_live', True):
            issues = await validator._validate_machine_async(
                task_id="task_1",
                required_machine_id="MCH-NONEXISTENT",
                required_machine_type=None,
                prefix="task_templates[0]",
            )

        assert len(issues) == 1
        assert issues[0].code == "PS-BLK-19"
        assert "not found" in issues[0].message

    @pytest.mark.asyncio
    async def test_blk19_machine_inactive(self):
        """BLK-19 when machine exists but is inactive."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        validator._machines_svc = AsyncMock()
        validator._machines_svc.machine_available = AsyncMock(return_value={
            "found": True, "active": False, "available": False, "operational": False, "machine": MACHINE_INACTIVE
        })

        with patch.object(settings, 'registry_machines_live', True):
            issues = await validator._validate_machine_async(
                task_id="task_1",
                required_machine_id="MCH-INACTIVE-01",
                required_machine_type=None,
                prefix="task_templates[0]",
            )

        assert len(issues) == 1
        assert issues[0].code == "PS-BLK-19"
        assert "inactive" in issues[0].message

    @pytest.mark.asyncio
    async def test_blk19_machine_unavailable(self):
        """BLK-19 when machine exists, active, but not available."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        validator._machines_svc = AsyncMock()
        validator._machines_svc.machine_available = AsyncMock(return_value={
            "found": True, "active": True, "available": False, "operational": True, "machine": MACHINE_UNAVAILABLE
        })

        with patch.object(settings, 'registry_machines_live', True):
            issues = await validator._validate_machine_async(
                task_id="task_1",
                required_machine_id="MCH-UNAVAILABLE-01",
                required_machine_type=None,
                prefix="task_templates[0]",
            )

        assert len(issues) == 1
        assert issues[0].code == "PS-BLK-19"
        assert "not available" in issues[0].message

    @pytest.mark.asyncio
    async def test_blk19_machine_not_operational(self):
        """BLK-19 when machine exists, active, available, but not operational."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        validator._machines_svc = AsyncMock()
        validator._machines_svc.machine_available = AsyncMock(return_value={
            "found": True, "active": True, "available": True, "operational": False,
            "machine": MACHINE_MAINTENANCE
        })

        with patch.object(settings, 'registry_machines_live', True):
            issues = await validator._validate_machine_async(
                task_id="task_1",
                required_machine_id="MCH-MAINTENANCE-01",
                required_machine_type=None,
                prefix="task_templates[0]",
            )

        assert len(issues) == 1
        assert issues[0].code == "PS-BLK-19"
        assert "not operational" in issues[0].message

    @pytest.mark.asyncio
    async def test_blk19_no_machines_of_type(self):
        """BLK-19 when machine_type specified but no machines of that type exist."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        validator._machines_svc = AsyncMock()
        validator._machines_svc.machine_available = AsyncMock(return_value={
            "found": False, "active": False, "available": False, "operational": False, "machine": None
        })
        validator._machines_svc.get_by_type = AsyncMock(return_value=[])

        with patch.object(settings, 'registry_machines_live', True):
            issues = await validator._validate_machine_async(
                task_id="task_1",
                required_machine_id=None,
                required_machine_type="cnc_router",
                prefix="task_templates[0]",
            )

        assert len(issues) == 1
        assert issues[0].code == "PS-BLK-19"
        assert "No machines of type" in issues[0].message

    @pytest.mark.asyncio
    async def test_blk19_no_available_machines_of_type(self):
        """BLK-19 when machines of type exist but none are available."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        validator._machines_svc = AsyncMock()
        validator._machines_svc.get_by_type = AsyncMock(return_value=[
            {**MACHINE_CNC_01, "is_available": False, "operational_status": "maintenance"}
        ])

        with patch.object(settings, 'registry_machines_live', True):
            issues = await validator._validate_machine_async(
                task_id="task_1",
                required_machine_id=None,
                required_machine_type="cnc_router",
                prefix="task_templates[0]",
            )

        assert len(issues) == 1
        assert issues[0].code == "PS-BLK-19"
        assert "No available machines" in issues[0].message

    @pytest.mark.asyncio
    async def test_no_blk19_when_machine_valid(self):
        """No BLK-19 when machine is found, active, available, operational."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        validator._machines_svc = AsyncMock()
        validator._machines_svc.machine_available = AsyncMock(return_value={
            "found": True, "active": True, "available": True, "operational": True, "machine": MACHINE_CNC_01
        })

        with patch.object(settings, 'registry_machines_live', True):
            issues = await validator._validate_machine_async(
                task_id="task_1",
                required_machine_id="MCH-CNC-ROUTER-01",
                required_machine_type=None,
                prefix="task_templates[0]",
            )

        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Category 6: WRN-03 present when flag=false
# ---------------------------------------------------------------------------


class TestWRN03FlagOff:
    """WRN-03 presence when registry_machines_live=false."""

    def test_wrn03_in_gate_warnings(self):
        """WRN-03 appears in gate warnings when machines not live."""
        order = MagicMock()
        order.id = 14
        order.code = "ORD-014"
        order.snapshot_version = 1
        order.snapshot_line_items = json.dumps({
            "order_id": 14,
            "product_definition": {
                "product_id": "PROD-001",
                "quantity": 1,
                "layers": [{"layer_id": "L-01", "processes": [{"type": "cnc_routing", "estimated_time_minutes": 10}]}],
            },
            "cost_result": {"estimated_time_minutes": 60},
        })

        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=False,
        )
        preview = MagicMock()

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(order, registries, False, preview)

        wrn03_warnings = [w for w in evaluation.warnings if w.get("code") == "WRN-03"]
        assert len(wrn03_warnings) == 1
        assert "M19" in wrn03_warnings[0]["message"]
        assert "BLK-19" in wrn03_warnings[0]["message"]

    def test_wrn03_in_linkage_validator(self):
        """PS-WRN-03 emitted by linkage validator when flag off."""
        with patch.object(settings, 'registry_machines_live', False):
            from services.product_system_linkage_validator import ProductSystemLinkageValidator
            db = AsyncMock()
            validator = ProductSystemLinkageValidator(db)
            issues = validator._validate_machine_id(
                task_id="task_1",
                required_machine_id="MCH-CNC-ROUTER-01",
                prefix="task_templates[0]",
            )
            assert any(i.code == "PS-WRN-03" for i in issues)


# ---------------------------------------------------------------------------
# Category 7: WRN-03 absent when flag=true
# ---------------------------------------------------------------------------


class TestWRN03FlagOn:
    """WRN-03 absence when registry_machines_live=true."""

    def test_wrn03_absent_in_gate(self):
        """WRN-03 NOT in gate warnings when machines registry is live."""
        order = MagicMock()
        order.id = 14
        order.code = "ORD-014"
        order.snapshot_version = 1
        order.snapshot_line_items = json.dumps({
            "order_id": 14,
            "product_definition": {
                "product_id": "PROD-001",
                "quantity": 1,
                "layers": [{"layer_id": "L-01", "processes": [{"type": "cnc_routing", "estimated_time_minutes": 10}]}],
            },
            "cost_result": {"estimated_time_minutes": 60},
        })

        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=True,
        )
        preview = MagicMock()

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(order, registries, False, preview)

        wrn03_warnings = [w for w in evaluation.warnings if w.get("code") == "WRN-03"]
        assert len(wrn03_warnings) == 0, "WRN-03 should NOT appear when machines registry is live"

    def test_no_wrn03_but_blk12_in_linkage_validator_sync(self):
        """No PS-WRN-03 from sync path when flag is on; PS-BLK-12 emitted instead."""
        with patch.object(settings, 'registry_machines_live', True):
            from services.product_system_linkage_validator import ProductSystemLinkageValidator
            db = AsyncMock()
            validator = ProductSystemLinkageValidator(db)
            issues = validator._validate_machine_id(
                task_id="task_1",
                required_machine_id="MCH-CNC-ROUTER-01",
                prefix="task_templates[0]",
            )
            wrn03 = [i for i in issues if i.code == "PS-WRN-03"]
            assert len(wrn03) == 0, "Sync path should not emit WRN-03 when flag is on"
            blk12 = [i for i in issues if i.code == "PS-BLK-12"]
            assert len(blk12) == 1, "Sync path should emit PS-BLK-12 when flag is on (Phase 4 spec)"


# ---------------------------------------------------------------------------
# Category 8: ProductSystem/S30/M22 regression tests
# ---------------------------------------------------------------------------


class TestRegressionProductSystemM22:
    """Ensure ProductSystem and M22 behavior unchanged."""

    def test_wrn01_absent_when_productsystem_live(self):
        """WRN-01 NOT emitted when product_system_available=True and preview provided."""
        order = MagicMock()
        order.id = 14
        order.code = "ORD-014"
        order.snapshot_version = 1
        order.snapshot_line_items = json.dumps({
            "order_id": 14,
            "product_definition": {
                "product_id": "PROD-001",
                "quantity": 1,
                "layers": [{"layer_id": "L-01", "processes": [{"type": "cnc_routing", "estimated_time_minutes": 10}]}],
            },
            "cost_result": {"estimated_time_minutes": 60},
        })

        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=True,
        )
        preview = MagicMock()

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(order, registries, False, preview)

        wrn01_found = any(w.get("code") == "WRN-01" for w in evaluation.warnings)
        assert not wrn01_found, "WRN-01 should NOT appear when ProductSystem is live with preview"

    def test_wrn02_absent_when_materials_live(self):
        """WRN-02 NOT emitted when materials_registry_available=True."""
        order = MagicMock()
        order.id = 14
        order.code = "ORD-014"
        order.snapshot_version = 1
        order.snapshot_line_items = json.dumps({
            "order_id": 14,
            "product_definition": {
                "product_id": "PROD-001",
                "quantity": 1,
                "layers": [{"layer_id": "L-01", "processes": [{"type": "cnc_routing", "estimated_time_minutes": 10}]}],
            },
            "cost_result": {"estimated_time_minutes": 60},
        })

        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=True,
        )
        preview = MagicMock()

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(order, registries, False, preview)

        wrn02_found = any(w.get("code") == "WRN-02" for w in evaluation.warnings)
        assert not wrn02_found, "WRN-02 should NOT appear when Materials Registry is live"

    def test_materials_registry_still_consulted(self):
        """Materials registry still in registries_consulted when live."""
        order = MagicMock()
        order.id = 14
        order.code = "ORD-014"
        order.snapshot_version = 1
        order.snapshot_line_items = json.dumps({
            "order_id": 14,
            "product_definition": {
                "product_id": "PROD-001",
                "quantity": 1,
                "layers": [{"layer_id": "L-01", "processes": [{"type": "cnc_routing", "estimated_time_minutes": 10}]}],
            },
            "cost_result": {"estimated_time_minutes": 60},
        })

        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=True,
        )
        preview = MagicMock()

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(order, registries, False, preview)

        unavailable = evaluation.trace_source.get("registries_unavailable", [])
        assert "materials" not in unavailable


# ---------------------------------------------------------------------------
# Category 9: Backend regression — gate/ProductSystem
# ---------------------------------------------------------------------------


class TestBackendRegression:
    """Backend regression for gate and ProductSystem integration."""

    def test_gate_structural_blockers_still_work(self):
        """BLK-01 still fires for invalid snapshot."""
        order = MagicMock()
        order.id = 14
        order.code = "ORD-014"
        order.snapshot_version = 1
        order.snapshot_line_items = None  # BLK-01

        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=True,
        )

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            evaluation = evaluate_gate(order, registries, False)

        blk01 = [b for b in evaluation.blockers if b.get("code") == "BLK-01"]
        assert len(blk01) >= 1
        assert evaluation.can_generate is False

    def test_gate_blk07_plan_exists(self):
        """BLK-07 still fires when plan already exists."""
        order = MagicMock()
        order.id = 14
        order.code = "ORD-014"
        order.snapshot_version = 1
        order.snapshot_line_items = json.dumps({
            "order_id": 14,
            "product_definition": {
                "product_id": "PROD-001",
                "quantity": 1,
                "layers": [{"layer_id": "L-01", "processes": [{"type": "cnc_routing", "estimated_time_minutes": 10}]}],
            },
            "cost_result": {"estimated_time_minutes": 60},
        })

        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=True,
        )
        preview = MagicMock()

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(order, registries, True, preview)

        blk07 = [b for b in evaluation.blockers if b.get("code") == "BLK-07"]
        assert len(blk07) == 1
        assert evaluation.can_generate is False

    def test_machines_not_in_registries_unavailable_when_live(self):
        """When machines_registry_available=True, 'machines' not in unavailable list."""
        order = MagicMock()
        order.id = 14
        order.code = "ORD-014"
        order.snapshot_version = 1
        order.snapshot_line_items = json.dumps({
            "order_id": 14,
            "product_definition": {
                "product_id": "PROD-001",
                "quantity": 1,
                "layers": [{"layer_id": "L-01", "processes": [{"type": "cnc_routing", "estimated_time_minutes": 10}]}],
            },
            "cost_result": {"estimated_time_minutes": 60},
        })

        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=True,
        )
        preview = MagicMock()

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(order, registries, False, preview)

        unavailable = evaluation.trace_source.get("registries_unavailable", [])
        assert "machines" not in unavailable

    def test_machines_in_registries_unavailable_when_not_live(self):
        """When machines_registry_available=False, 'machines' in unavailable list."""
        order = MagicMock()
        order.id = 14
        order.code = "ORD-014"
        order.snapshot_version = 1
        order.snapshot_line_items = json.dumps({
            "order_id": 14,
            "product_definition": {
                "product_id": "PROD-001",
                "quantity": 1,
                "layers": [{"layer_id": "L-01", "processes": [{"type": "cnc_routing", "estimated_time_minutes": 10}]}],
            },
            "cost_result": {"estimated_time_minutes": 60},
        })

        registries = RegistrySnapshot(
            skills=["SK_CNC_OPERATION"],
            workcenters=["WC_CNC_ROUTING"],
            product_system_available=True,
            materials_registry_available=True,
            machines_registry_available=False,
        )
        preview = MagicMock()

        with patch("services.execution_plan_gate_service._scan_static_invariants", return_value=[]):
            with patch("services.gate_blocker_mapper.map_preview_to_gate_blockers", return_value=[]):
                evaluation = evaluate_gate(order, registries, False, preview)

        unavailable = evaluation.trace_source.get("registries_unavailable", [])
        assert "machines" in unavailable