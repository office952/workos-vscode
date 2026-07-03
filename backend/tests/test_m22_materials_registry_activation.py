"""
M22 Materials Registry — Full Controlled Activation Sprint Tests.

Tests cover:
1. MaterialsReadService unit tests
2. RegistryLinkageValidator material integration tests
3. S30 gate flag OFF tests
4. S30 gate flag ON tests
5. BLK-14 material missing/inactive/unavailable tests
6. WRN-02 present when flag=false
7. WRN-02 absent when flag=true
8. BLK-18 remains deferred
9. ProductSystem/S30 regression tests
10. Backend regression subset relevant to gate/ProductSystem
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from data_models.execution_preview import (
    ProductSystemExecutionPreview,
    TraceSource,
)
from services.execution_plan_gate_service import (
    GateEvaluation,
    RegistrySnapshot,
    evaluate_gate,
)
from services.materials_read_service import MaterialsReadService


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------


@dataclass
class FakeOrderRow:
    id: int
    code: str
    snapshot_version: Optional[int]
    snapshot_line_items: Any


def _good_snapshot() -> dict:
    return {
        "order_id": 14,
        "product_definition": {
            "product_id": "PROD-CASETA-LUMINOASA",
            "product_code": "PROD-CASETA-LUMINOASA",
            "quantity": 1,
            "layers": [
                {
                    "layer_id": "layer_1",
                    "processes": [
                        {
                            "process_id": "P-001",
                            "type": "cnc_routing",
                            "estimated_time_minutes": 60,
                            "machine_type": "cnc_router",
                        }
                    ],
                }
            ],
        },
        "cost_result": {
            "total_cost": 500.0,
            "estimated_time_minutes": 120,
        },
    }


def _empty_ps_preview() -> ProductSystemExecutionPreview:
    """Empty ProductSystem preview (no blockers, no warnings)."""
    return ProductSystemExecutionPreview(
        order_id=14,
        order_code="CMD-2024-014",
        template_code="TPL-CASETA-LUMINOASA",
        template_version="1",
        generated_operations=[],
        generated_task_requirements=[],
        missing_links=[],
        blockers=[],
        warnings=[],
        trace_source=TraceSource(
            registries_consulted=["skills", "workcenters", "roles"],
            registries_unavailable=[],
            template_resolved_at="2026-05-09T00:00:00Z",
            linkage_validation_run=True,
            linkage_blockers_count=0,
            linkage_warnings_count=0,
        ),
    )


def _registry_flag_off() -> RegistrySnapshot:
    """Registry snapshot with materials NOT live (flag=false)."""
    return RegistrySnapshot(
        skills=["CNC_ROUTING", "LASER_CUTTING"],
        workcenters=["WC_CNC", "WC_LASER"],
        roles=["OP_CNC_ROUTER"],
        product_system_available=True,
        materials_registry_available=False,
        machines_registry_available=False,
    )


def _registry_flag_on() -> RegistrySnapshot:
    """Registry snapshot with materials LIVE (flag=true)."""
    return RegistrySnapshot(
        skills=["CNC_ROUTING", "LASER_CUTTING"],
        workcenters=["WC_CNC", "WC_LASER"],
        roles=["OP_CNC_ROUTER"],
        product_system_available=True,
        materials_registry_available=True,
        machines_registry_available=False,
    )


# ---------------------------------------------------------------------------
# 1. MaterialsReadService unit tests
# ---------------------------------------------------------------------------


class TestMaterialsReadService:
    """Unit tests for MaterialsReadService (mocked DB)."""

    @pytest.mark.asyncio
    async def test_get_by_code_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": 1,
            "code": "MAT-PROFIL-ALU",
            "name": "Profil aluminiu",
            "description": None,
            "category": "structural",
            "unit": "m",
            "stock_available": 500.0,
            "minimum_stock": 50.0,
            "is_active": True,
            "created_at": "2026-05-09T00:00:00Z",
            "updated_at": "2026-05-09T00:00:00Z",
        }
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.get_by_code("MAT-PROFIL-ALU")

        assert result is not None
        assert result["code"] == "MAT-PROFIL-ALU"
        assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_by_code_not_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.get_by_code("MAT-NONEXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_exists_true(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.exists("MAT-PROFIL-ALU")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.exists("MAT-NONEXISTENT")

        assert result is False

    @pytest.mark.asyncio
    async def test_is_active_true(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = True
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.is_active("MAT-PROFIL-ALU")

        assert result is True

    @pytest.mark.asyncio
    async def test_is_active_not_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.is_active("MAT-NONEXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_material_available_found_active_stock(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": 1,
            "code": "MAT-PROFIL-ALU",
            "name": "Profil aluminiu",
            "description": None,
            "category": "structural",
            "unit": "m",
            "stock_available": 500.0,
            "minimum_stock": 50.0,
            "is_active": True,
            "created_at": None,
            "updated_at": None,
        }
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.material_available("MAT-PROFIL-ALU")

        assert result["found"] is True
        assert result["active"] is True
        assert result["has_stock"] is True

    @pytest.mark.asyncio
    async def test_material_available_not_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.material_available("MAT-NONEXISTENT")

        assert result["found"] is False
        assert result["active"] is False
        assert result["has_stock"] is False

    @pytest.mark.asyncio
    async def test_material_available_inactive(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": 1,
            "code": "MAT-INACTIVE",
            "name": "Inactive material",
            "description": None,
            "category": "structural",
            "unit": "m",
            "stock_available": 100.0,
            "minimum_stock": 10.0,
            "is_active": False,
            "created_at": None,
            "updated_at": None,
        }
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.material_available("MAT-INACTIVE")

        assert result["found"] is True
        assert result["active"] is False

    @pytest.mark.asyncio
    async def test_check_readiness_success(self):
        mock_db = AsyncMock()
        call_count = [0]

        async def mock_execute(sql, *args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.scalar.return_value = 30
            else:
                result.scalar.return_value = 30
            return result

        mock_db.execute = mock_execute

        svc = MaterialsReadService(mock_db)
        result = await svc.check_readiness()

        assert result["ready"] is True
        assert result["row_count"] == 30
        assert result["active_count"] == 30

    @pytest.mark.asyncio
    async def test_list_all_codes(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("MAT-ACP-3MM",),
            ("MAT-PROFIL-ALU",),
        ]
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = MaterialsReadService(mock_db)
        result = await svc.list_all_codes(active_only=True)

        assert result == ["MAT-ACP-3MM", "MAT-PROFIL-ALU"]


# ---------------------------------------------------------------------------
# 2. RegistryLinkageValidator material integration tests
# ---------------------------------------------------------------------------


class TestLinkageValidatorMaterials:
    """Test ProductSystemLinkageValidator material validation paths."""

    @pytest.mark.asyncio
    async def test_validate_materials_sync_flag_off_canonical_code(self):
        """When flag=false, canonical material codes produce no issues."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = False
            mock_settings.registry_machines_live = False

            issues = validator._validate_materials(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-PROFIL-ALU", "quantity": 5.0}],
                prefix="task_templates[0]",
            )

        # Canonical code should NOT produce WRN-02
        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_validate_materials_sync_flag_off_unknown_code(self):
        """When flag=false, unknown material codes produce WRN-02."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = False
            mock_settings.registry_machines_live = False

            issues = validator._validate_materials(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-UNKNOWN-XYZ", "quantity": 5.0}],
                prefix="task_templates[0]",
            )

        assert len(issues) == 1
        assert issues[0].code == "PS-WRN-02"
        assert issues[0].severity == "warning"

    @pytest.mark.asyncio
    async def test_validate_materials_async_flag_on_found_active(self):
        """When flag=true, found+active material produces no issues."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        # Mock the materials service
        validator._materials_svc = AsyncMock()
        validator._materials_svc.material_available = AsyncMock(return_value={
            "found": True,
            "active": True,
            "has_stock": True,
            "material": {"code": "MAT-PROFIL-ALU"},
        })

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = True
            mock_settings.registry_machines_live = False

            issues = await validator._validate_materials_async(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-PROFIL-ALU", "quantity": 5.0}],
                prefix="task_templates[0]",
            )

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_validate_materials_async_flag_on_not_found(self):
        """When flag=true, material not found produces BLK-14."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        validator._materials_svc = AsyncMock()
        validator._materials_svc.material_available = AsyncMock(return_value={
            "found": False,
            "active": False,
            "has_stock": False,
            "material": None,
        })

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = True
            mock_settings.registry_machines_live = False

            issues = await validator._validate_materials_async(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-NONEXISTENT", "quantity": 5.0}],
                prefix="task_templates[0]",
            )

        assert len(issues) == 1
        assert issues[0].code == "PS-BLK-14"
        assert issues[0].severity == "blocker"
        assert "not_found" in issues[0].details.get("reason", "")

    @pytest.mark.asyncio
    async def test_validate_materials_async_flag_on_inactive(self):
        """When flag=true, inactive material produces BLK-14."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        validator._materials_svc = AsyncMock()
        validator._materials_svc.material_available = AsyncMock(return_value={
            "found": True,
            "active": False,
            "has_stock": False,
            "material": {"code": "MAT-INACTIVE", "is_active": False},
        })

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = True
            mock_settings.registry_machines_live = False

            issues = await validator._validate_materials_async(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-INACTIVE", "quantity": 5.0}],
                prefix="task_templates[0]",
            )

        assert len(issues) == 1
        assert issues[0].code == "PS-BLK-14"
        assert "inactive" in issues[0].details.get("reason", "")


# ---------------------------------------------------------------------------
# 3. S30 gate flag OFF tests
# ---------------------------------------------------------------------------


class TestGateFlagOff:
    """Gate behavior when registry_materials_live=false."""

    def test_gate_emits_wrn02_when_materials_not_live(self):
        """WRN-02 must be present when materials_registry_available=false."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_off()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        wrn_codes = [w["code"] for w in evaluation.warnings]
        assert "WRN-02" in wrn_codes

    def test_gate_wrn02_message_content(self):
        """WRN-02 message must mention M22 and BLK-14/BLK-18."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_off()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        wrn02 = [w for w in evaluation.warnings if w["code"] == "WRN-02"]
        assert len(wrn02) == 1
        assert "M22" in wrn02[0]["message"]
        assert "BLK-14" in wrn02[0]["message"]

    def test_gate_materials_in_registries_unavailable_when_flag_off(self):
        """trace_source.registries_unavailable must include 'materials' when flag=false."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_off()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        assert "materials" in evaluation.trace_source["registries_unavailable"]


# ---------------------------------------------------------------------------
# 4. S30 gate flag ON tests
# ---------------------------------------------------------------------------


class TestGateFlagOn:
    """Gate behavior when registry_materials_live=true."""

    def test_gate_no_wrn02_when_materials_live(self):
        """WRN-02 must NOT be present when materials_registry_available=true."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        wrn_codes = [w["code"] for w in evaluation.warnings]
        assert "WRN-02" not in wrn_codes

    def test_gate_materials_not_in_registries_unavailable_when_flag_on(self):
        """trace_source.registries_unavailable must NOT include 'materials' when flag=true."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        assert "materials" not in evaluation.trace_source["registries_unavailable"]

    def test_gate_can_generate_with_materials_live(self):
        """Gate should still allow generation when materials is live (no material blockers in snapshot)."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        assert evaluation.can_generate is True


# ---------------------------------------------------------------------------
# 5. BLK-14 material missing/inactive/unavailable tests
# ---------------------------------------------------------------------------


class TestBLK14:
    """BLK-14 tests via linkage validator (async path)."""

    @pytest.mark.asyncio
    async def test_blk14_material_not_found(self):
        """BLK-14 fires when material code not found in registry."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)
        validator._materials_svc = AsyncMock()
        validator._materials_svc.material_available = AsyncMock(return_value={
            "found": False, "active": False, "has_stock": False, "material": None,
        })

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = True
            mock_settings.registry_machines_live = False

            issues = await validator._validate_materials_async(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-DOES-NOT-EXIST", "quantity": 2.0}],
                prefix="task_templates[0]",
            )

        blockers = [i for i in issues if i.severity == "blocker"]
        assert len(blockers) == 1
        assert blockers[0].code == "PS-BLK-14"
        assert blockers[0].details["reason"] == "not_found"

    @pytest.mark.asyncio
    async def test_blk14_material_inactive(self):
        """BLK-14 fires when material exists but is inactive."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)
        validator._materials_svc = AsyncMock()
        validator._materials_svc.material_available = AsyncMock(return_value={
            "found": True, "active": False, "has_stock": False,
            "material": {"code": "MAT-INACTIVE", "is_active": False},
        })

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = True
            mock_settings.registry_machines_live = False

            issues = await validator._validate_materials_async(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-INACTIVE", "quantity": 2.0}],
                prefix="task_templates[0]",
            )

        blockers = [i for i in issues if i.severity == "blocker"]
        assert len(blockers) == 1
        assert blockers[0].code == "PS-BLK-14"
        assert blockers[0].details["reason"] == "material_inactive"

    @pytest.mark.asyncio
    async def test_blk14_not_fired_for_valid_material(self):
        """BLK-14 does NOT fire when material is found and active."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)
        validator._materials_svc = AsyncMock()
        validator._materials_svc.material_available = AsyncMock(return_value={
            "found": True, "active": True, "has_stock": True,
            "material": {"code": "MAT-PROFIL-ALU", "is_active": True},
        })

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = True
            mock_settings.registry_machines_live = False

            issues = await validator._validate_materials_async(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-PROFIL-ALU", "quantity": 2.0}],
                prefix="task_templates[0]",
            )

        blockers = [i for i in issues if i.severity == "blocker"]
        assert len(blockers) == 0


# ---------------------------------------------------------------------------
# 6. WRN-02 present when flag=false
# ---------------------------------------------------------------------------


class TestWRN02FlagOff:
    """WRN-02 behavior when registry_materials_live=false."""

    def test_wrn02_in_gate_warnings(self):
        """WRN-02 must appear in gate warnings when materials not live."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_off()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        wrn_codes = [w["code"] for w in evaluation.warnings]
        assert "WRN-02" in wrn_codes

    def test_wrn02_linkage_validator_flag_off(self):
        """Linkage validator emits PS-WRN-02 for unknown code when flag=false."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = False
            mock_settings.registry_machines_live = False

            issues = validator._validate_materials(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-UNKNOWN", "quantity": 1.0}],
                prefix="task_templates[0]",
            )

        assert any(i.code == "PS-WRN-02" for i in issues)


# ---------------------------------------------------------------------------
# 7. WRN-02 absent when flag=true
# ---------------------------------------------------------------------------


class TestWRN02FlagOn:
    """WRN-02 must NOT appear when registry_materials_live=true."""

    def test_wrn02_absent_in_gate_when_materials_live(self):
        """WRN-02 must NOT appear in gate warnings when materials live."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        wrn_codes = [w["code"] for w in evaluation.warnings]
        assert "WRN-02" not in wrn_codes

    @pytest.mark.asyncio
    async def test_no_wrn02_from_linkage_validator_flag_on(self):
        """Linkage validator does NOT emit PS-WRN-02 when flag=true (uses BLK-14 instead)."""
        from services.product_system_linkage_validator import ProductSystemLinkageValidator

        mock_db = AsyncMock()
        validator = ProductSystemLinkageValidator(mock_db)
        validator._materials_svc = AsyncMock()
        validator._materials_svc.material_available = AsyncMock(return_value={
            "found": False, "active": False, "has_stock": False, "material": None,
        })

        with patch("services.product_system_linkage_validator.settings") as mock_settings:
            mock_settings.registry_materials_live = True
            mock_settings.registry_machines_live = False

            issues = await validator._validate_materials_async(
                task_id="task_0",
                material_requirements=[{"material_code": "MAT-UNKNOWN", "quantity": 1.0}],
                prefix="task_templates[0]",
            )

        # Should be BLK-14, NOT WRN-02
        assert not any(i.code == "PS-WRN-02" for i in issues)
        assert any(i.code == "PS-BLK-14" for i in issues)


# ---------------------------------------------------------------------------
# 8. BLK-18 remains deferred
# ---------------------------------------------------------------------------


class TestBLK18Deferred:
    """BLK-18 (material cost validation) must remain deferred."""

    def test_blk18_not_in_gate_blockers_flag_off(self):
        """BLK-18 must NOT appear as a hard blocker when flag=false."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_off()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        blk_codes = [b["code"] for b in evaluation.blockers]
        assert "BLK-18" not in blk_codes

    def test_blk18_not_in_gate_blockers_flag_on(self):
        """BLK-18 must NOT appear as a hard blocker when flag=true (Cost Engine not integrated)."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        blk_codes = [b["code"] for b in evaluation.blockers]
        assert "BLK-18" not in blk_codes


# ---------------------------------------------------------------------------
# 9. ProductSystem/S30 regression tests
# ---------------------------------------------------------------------------


class TestProductSystemRegression:
    """Ensure ProductSystem/S30 behavior is not broken by M22 changes."""

    def test_gate_still_works_with_productsystem_preview(self):
        """Gate with PS preview and materials flag=true still returns valid evaluation."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        # Should pass — no structural blockers
        assert evaluation.can_generate is True
        assert evaluation.order_id == 14

    def test_gate_wrn03_still_present_for_machines(self):
        """WRN-03 (machines not live) must still be present regardless of M22."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()  # materials live, machines NOT live

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        wrn_codes = [w["code"] for w in evaluation.warnings]
        assert "WRN-03" in wrn_codes

    def test_gate_wrn01_not_present_when_productsystem_live(self):
        """WRN-01 must NOT appear when product_system_available=true and preview provided."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        wrn_codes = [w["code"] for w in evaluation.warnings]
        assert "WRN-01" not in wrn_codes


# ---------------------------------------------------------------------------
# 10. Backend regression subset relevant to gate/ProductSystem
# ---------------------------------------------------------------------------


class TestBackendRegression:
    """Regression tests for gate envelope shape and classification."""

    def test_gate_envelope_shape(self):
        """Gate evaluation must have all required fields."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        d = evaluation.to_dict()
        assert "order_id" in d
        assert "order_code" in d
        assert "snapshot_version" in d
        assert "evaluated_at" in d
        assert "can_generate" in d
        assert "blockers" in d
        assert "warnings" in d
        assert "missing_links" in d
        assert "trace_source" in d

    def test_gate_trace_source_has_registries(self):
        """trace_source must enumerate consulted and unavailable registries."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        ts = evaluation.trace_source
        assert "registries_consulted" in ts
        assert "registries_unavailable" in ts
        # machines should be unavailable
        assert "machines" in ts["registries_unavailable"]
        # materials should NOT be unavailable
        assert "materials" not in ts["registries_unavailable"]

    def test_gate_blk07_still_works(self):
        """BLK-07 (plan already exists) must still fire correctly."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=True,
            productsystem_preview=_empty_ps_preview(),
        )

        assert evaluation.can_generate is False
        blk_codes = [b["code"] for b in evaluation.blockers]
        assert "BLK-07" in blk_codes

    def test_gate_structural_blockers_still_work(self):
        """BLK-01 (bad snapshot) must still fire correctly."""
        order = FakeOrderRow(
            id=14,
            code="CMD-2024-014",
            snapshot_version=1,
            snapshot_line_items="not valid json {{",
        )
        registries = _registry_flag_on()

        evaluation = evaluate_gate(
            order_row=order,
            registries=registries,
            plan_already_exists=False,
            productsystem_preview=_empty_ps_preview(),
        )

        assert evaluation.can_generate is False
        blk_codes = [b["code"] for b in evaluation.blockers]
        assert "BLK-01" in blk_codes