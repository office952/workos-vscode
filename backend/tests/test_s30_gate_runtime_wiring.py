"""
S30 — Gate Runtime Wiring Remediation Tests.

Tests that the router correctly:
  1. Reads registry_productsystem_live from config into RegistrySnapshot
  2. Calls ProductSystemExecutionPreviewService when flag=true
  3. Passes productsystem_preview to evaluate_gate()
  4. Preserves legacy behavior when flag=false
  5. Gracefully degrades when preview service fails

These are integration-level tests for the router wiring layer.
No DB writes. No mutations.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from data_models.execution_preview import (
    GeneratedOperation,
    GeneratedTaskRequirement,
    MissingLink,
    ProductSystemExecutionPreview,
    TraceSource,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_clean_preview(order_id: int = 14) -> ProductSystemExecutionPreview:
    """Build a clean preview with no blockers."""
    return ProductSystemExecutionPreview(
        order_id=order_id,
        order_code="ORD-2026-014",
        template_code="TPL-ACP-LIGHT-ROUTED",
        template_version="1.0",
        generated_operations=[
            GeneratedOperation(
                operation_id="OP-001",
                task_type="cnc_routing",
                sequence_index=1,
                depends_on_operation_ids=[],
                component_id=None,
                description="CNC routing",
            ),
        ],
        generated_task_requirements=[
            GeneratedTaskRequirement(
                task_template_id="TT-001",
                source_operation_id="OP-001",
                task_type="cnc_routing",
                required_skill_ids=["cnc_routing"],
                required_workcenter_id="WC-CNC-01",
                required_machine_type=None,
                required_machine_id=None,
                material_requirements=[],
                estimated_duration={"minutes": 30},
            ),
        ],
        blockers=[],
        warnings=[],
        missing_links=[],
        trace_source=TraceSource(
            registries_consulted=["skills", "workcenters"],
            registries_unavailable=["materials", "machines"],
            template_resolved_at="2026-05-08T14:30:00Z",
            linkage_validation_run=True,
            linkage_blockers_count=0,
            linkage_warnings_count=0,
        ),
    )


def _make_preview_with_ps_blk05(order_id: int = 14) -> ProductSystemExecutionPreview:
    """Build a preview with PS-BLK-05 → maps to BLK-12."""
    return ProductSystemExecutionPreview(
        order_id=order_id,
        order_code="ORD-2026-014",
        template_code="TPL-ACP-LIGHT-ROUTED",
        template_version="1.0",
        generated_operations=[],
        generated_task_requirements=[],
        blockers=[
            {
                "code": "PS-BLK-05",
                "message": "Missing required_skill_ids",
                "task_template_id": "TT-002",
                "path": "task_templates.TT-002.required_skill_ids",
            }
        ],
        warnings=[],
        missing_links=[],
        trace_source=TraceSource(
            registries_consulted=["skills", "workcenters"],
            registries_unavailable=["materials", "machines"],
            template_resolved_at="2026-05-08T14:30:00Z",
            linkage_validation_run=True,
            linkage_blockers_count=1,
            linkage_warnings_count=0,
        ),
    )


# ---------------------------------------------------------------------------
# Test: _load_registry_snapshot reads config flag
# ---------------------------------------------------------------------------


class TestLoadRegistrySnapshotReadsConfig:
    """_load_registry_snapshot uses settings.registry_productsystem_live."""

    @pytest.mark.asyncio
    async def test_product_system_available_true_when_config_true(self):
        """When config flag is True, RegistrySnapshot.product_system_available=True."""
        with patch("routers.execution.settings") as mock_settings:
            mock_settings.registry_productsystem_live = True
            mock_settings.registry_materials_live = False
            mock_settings.registry_machines_live = False

            # Mock DB session and _read_codes
            mock_db = AsyncMock()
            with patch("routers.execution._read_codes", new_callable=AsyncMock) as mock_read:
                mock_read.return_value = ["SKILL-CNC"]

                from routers.execution import _load_registry_snapshot

                snapshot = await _load_registry_snapshot(mock_db)

                assert snapshot.product_system_available is True
                assert snapshot.materials_registry_available is False
                assert snapshot.machines_registry_available is False

    @pytest.mark.asyncio
    async def test_product_system_available_false_when_config_false(self):
        """When config flag is False, RegistrySnapshot.product_system_available=False."""
        with patch("routers.execution.settings") as mock_settings:
            mock_settings.registry_productsystem_live = False
            mock_settings.registry_materials_live = False
            mock_settings.registry_machines_live = False

            mock_db = AsyncMock()
            with patch("routers.execution._read_codes", new_callable=AsyncMock) as mock_read:
                mock_read.return_value = ["SKILL-CNC"]

                from routers.execution import _load_registry_snapshot

                snapshot = await _load_registry_snapshot(mock_db)

                assert snapshot.product_system_available is False

    @pytest.mark.asyncio
    async def test_materials_and_machines_flags_read(self):
        """Materials and machines flags also read from config."""
        with patch("routers.execution.settings") as mock_settings:
            mock_settings.registry_productsystem_live = True
            mock_settings.registry_materials_live = True
            mock_settings.registry_machines_live = True

            mock_db = AsyncMock()
            with patch("routers.execution._read_codes", new_callable=AsyncMock) as mock_read:
                mock_read.return_value = ["CODE-1"]

                from routers.execution import _load_registry_snapshot

                snapshot = await _load_registry_snapshot(mock_db)

                assert snapshot.materials_registry_available is True
                assert snapshot.machines_registry_available is True


# ---------------------------------------------------------------------------
# Test: gate endpoint wires preview when flag=true
# ---------------------------------------------------------------------------


class TestGateEndpointWiresPreview:
    """gate_plan_from_order calls preview service when flag=true."""

    @pytest.mark.asyncio
    async def test_preview_service_called_when_flag_true(self):
        """When registry_productsystem_live=True, preview service is invoked."""
        mock_preview = _make_clean_preview()

        with patch("routers.execution.settings") as mock_settings, \
             patch("routers.execution._read_codes", new_callable=AsyncMock) as mock_read, \
             patch("routers.execution._get_order_or_404", new_callable=AsyncMock) as mock_order, \
             patch("routers.execution._plan_already_exists", new_callable=AsyncMock) as mock_plan, \
             patch("routers.execution.ProductSystemExecutionPreviewService") as MockPreviewSvc, \
             patch("routers.execution.evaluate_gate") as mock_gate:

            mock_settings.registry_productsystem_live = True
            mock_settings.registry_materials_live = False
            mock_settings.registry_machines_live = False
            mock_read.return_value = ["SKILL-CNC"]

            # Mock order
            fake_order = MagicMock()
            fake_order.id = 14
            fake_order.code = "ORD-014"
            mock_order.return_value = fake_order
            mock_plan.return_value = False

            # Mock preview service
            mock_svc_instance = AsyncMock()
            mock_svc_instance.preview_for_execution = AsyncMock(return_value=mock_preview)
            MockPreviewSvc.return_value = mock_svc_instance

            # Mock gate evaluation
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {"can_generate": True, "blockers": [], "warnings": []}
            mock_gate.return_value = mock_result

            from routers.execution import gate_plan_from_order

            mock_db = AsyncMock()
            await gate_plan_from_order(14, mock_db)

            # Verify preview service was called
            MockPreviewSvc.assert_called_once_with(mock_db)
            mock_svc_instance.preview_for_execution.assert_called_once_with(14)

            # Verify evaluate_gate received the preview
            mock_gate.assert_called_once()
            call_kwargs = mock_gate.call_args
            assert call_kwargs.kwargs.get("productsystem_preview") == mock_preview

    @pytest.mark.asyncio
    async def test_preview_service_not_called_when_flag_false(self):
        """When registry_productsystem_live=False, preview service is NOT invoked."""
        with patch("routers.execution.settings") as mock_settings, \
             patch("routers.execution._read_codes", new_callable=AsyncMock) as mock_read, \
             patch("routers.execution._get_order_or_404", new_callable=AsyncMock) as mock_order, \
             patch("routers.execution._plan_already_exists", new_callable=AsyncMock) as mock_plan, \
             patch("routers.execution.ProductSystemExecutionPreviewService") as MockPreviewSvc, \
             patch("routers.execution.evaluate_gate") as mock_gate:

            mock_settings.registry_productsystem_live = False
            mock_settings.registry_materials_live = False
            mock_settings.registry_machines_live = False
            mock_read.return_value = ["SKILL-CNC"]

            fake_order = MagicMock()
            fake_order.id = 14
            mock_order.return_value = fake_order
            mock_plan.return_value = False

            mock_result = MagicMock()
            mock_result.to_dict.return_value = {"can_generate": False, "blockers": [], "warnings": []}
            mock_gate.return_value = mock_result

            from routers.execution import gate_plan_from_order

            mock_db = AsyncMock()
            await gate_plan_from_order(14, mock_db)

            # Preview service should NOT be instantiated
            MockPreviewSvc.assert_not_called()

            # evaluate_gate should receive productsystem_preview=None
            mock_gate.assert_called_once()
            call_kwargs = mock_gate.call_args
            assert call_kwargs.kwargs.get("productsystem_preview") is None


# ---------------------------------------------------------------------------
# Test: graceful degradation when preview service fails
# ---------------------------------------------------------------------------


class TestGateEndpointGracefulDegradation:
    """When preview service raises, gate proceeds with preview=None."""

    @pytest.mark.asyncio
    async def test_preview_failure_passes_none(self):
        """If preview service raises, productsystem_preview=None is passed to gate."""
        with patch("routers.execution.settings") as mock_settings, \
             patch("routers.execution._read_codes", new_callable=AsyncMock) as mock_read, \
             patch("routers.execution._get_order_or_404", new_callable=AsyncMock) as mock_order, \
             patch("routers.execution._plan_already_exists", new_callable=AsyncMock) as mock_plan, \
             patch("routers.execution.ProductSystemExecutionPreviewService") as MockPreviewSvc, \
             patch("routers.execution.evaluate_gate") as mock_gate:

            mock_settings.registry_productsystem_live = True
            mock_settings.registry_materials_live = False
            mock_settings.registry_machines_live = False
            mock_read.return_value = ["SKILL-CNC"]

            fake_order = MagicMock()
            fake_order.id = 14
            mock_order.return_value = fake_order
            mock_plan.return_value = False

            # Preview service raises
            mock_svc_instance = AsyncMock()
            mock_svc_instance.preview_for_execution = AsyncMock(
                side_effect=Exception("Template not found")
            )
            MockPreviewSvc.return_value = mock_svc_instance

            mock_result = MagicMock()
            mock_result.to_dict.return_value = {"can_generate": False, "blockers": [], "warnings": []}
            mock_gate.return_value = mock_result

            from routers.execution import gate_plan_from_order

            mock_db = AsyncMock()
            # Should NOT raise — graceful degradation
            await gate_plan_from_order(14, mock_db)

            # evaluate_gate receives None (graceful degradation)
            mock_gate.assert_called_once()
            call_kwargs = mock_gate.call_args
            assert call_kwargs.kwargs.get("productsystem_preview") is None

    @pytest.mark.asyncio
    async def test_endpoint_does_not_raise_on_preview_failure(self):
        """Endpoint returns 200 even when preview service fails."""
        with patch("routers.execution.settings") as mock_settings, \
             patch("routers.execution._read_codes", new_callable=AsyncMock) as mock_read, \
             patch("routers.execution._get_order_or_404", new_callable=AsyncMock) as mock_order, \
             patch("routers.execution._plan_already_exists", new_callable=AsyncMock) as mock_plan, \
             patch("routers.execution.ProductSystemExecutionPreviewService") as MockPreviewSvc, \
             patch("routers.execution.evaluate_gate") as mock_gate:

            mock_settings.registry_productsystem_live = True
            mock_settings.registry_materials_live = False
            mock_settings.registry_machines_live = False
            mock_read.return_value = ["SKILL-CNC"]

            fake_order = MagicMock()
            fake_order.id = 14
            mock_order.return_value = fake_order
            mock_plan.return_value = False

            mock_svc_instance = AsyncMock()
            mock_svc_instance.preview_for_execution = AsyncMock(
                side_effect=RuntimeError("DB connection lost")
            )
            MockPreviewSvc.return_value = mock_svc_instance

            mock_result = MagicMock()
            mock_result.to_dict.return_value = {"can_generate": False}
            mock_gate.return_value = mock_result

            from routers.execution import gate_plan_from_order

            mock_db = AsyncMock()
            result = await gate_plan_from_order(14, mock_db)

            # Should return the gate result, not raise
            assert result == {"can_generate": False}


# ---------------------------------------------------------------------------
# Test: BLK-14/18/19 remain unresolved (warnings)
# ---------------------------------------------------------------------------


class TestBlk14_18_19RemainWarnings:
    """BLK-14/18/19 remain as WRN-02/WRN-03, not falsely resolved."""

    @pytest.mark.asyncio
    async def test_wrn02_wrn03_still_emitted_when_ps_live(self):
        """WRN-02 and WRN-03 still emitted even when ProductSystem is live."""
        from services.execution_plan_gate_service import (
            RegistrySnapshot,
            evaluate_gate,
        )

        class MockOrder:
            id = 14
            code = "ORD-014"
            snapshot_version = 1
            snapshot_line_items = json.dumps({
                "product_definition": {
                    "product_id": "P1",
                    "quantity": 1,
                    "layers": [{"processes": [{"type": "cnc_routing", "estimated_time_minutes": 30}]}],
                },
                "cost_result": {"total": 100},
            })

        registries = RegistrySnapshot(
            skills=["SKILL-CNC-ROUTER"],
            workcenters=["WC-CNC-01"],
            roles=["OP_CNC"],
            product_system_available=True,
            materials_registry_available=False,  # NOT live → WRN-02
            machines_registry_available=False,  # NOT live → WRN-03
        )

        preview = _make_clean_preview()
        result = evaluate_gate(
            MockOrder(), registries, plan_already_exists=False,
            productsystem_preview=preview,
        )

        warning_codes = [w.get("code") for w in result.warnings]
        assert "WRN-02" in warning_codes
        assert "WRN-03" in warning_codes
        # WRN-01 should NOT be present (PS is live + preview provided)
        assert "WRN-01" not in warning_codes

    @pytest.mark.asyncio
    async def test_blk14_blk18_blk19_not_in_blockers(self):
        """BLK-14/18/19 never appear in blockers regardless of PS state."""
        from services.execution_plan_gate_service import (
            RegistrySnapshot,
            evaluate_gate,
        )

        class MockOrder:
            id = 14
            code = "ORD-014"
            snapshot_version = 1
            snapshot_line_items = json.dumps({
                "product_definition": {
                    "product_id": "P1",
                    "quantity": 1,
                    "layers": [{"processes": [{"type": "cnc_routing", "estimated_time_minutes": 30}]}],
                },
                "cost_result": {"total": 100},
            })

        registries = RegistrySnapshot(
            skills=["SKILL-CNC-ROUTER"],
            workcenters=["WC-CNC-01"],
            roles=["OP_CNC"],
            product_system_available=True,
            materials_registry_available=False,
            machines_registry_available=False,
        )

        preview = _make_clean_preview()
        result = evaluate_gate(
            MockOrder(), registries, plan_already_exists=False,
            productsystem_preview=preview,
        )

        blocker_codes = [b.get("code") for b in result.blockers]
        assert "BLK-14" not in blocker_codes
        assert "BLK-18" not in blocker_codes
        assert "BLK-19" not in blocker_codes