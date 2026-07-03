"""
S30 ProductSystem Gate Integration — Contract Tests.

Tests the integration between the S30 Execution Plan Generation Gate and the
Phase 6 ProductSystem Execution Output Model.

Covers:
  - Config=false → WRN-01 emitted, no BLK-12..17
  - Config=true + preview provided → WRN-01 NOT emitted, BLK-* emitted
  - Config=true + preview=None (failure) → WRN-01 fallback
  - BLK-14/18/19 never emitted from this integration
  - WRN-02/WRN-03 independent of registry_productsystem_live
  - can_generate reflects mapped blockers
  - trace_source includes product_system when preview consumed

No DB writes. No mutations. Pure function tests.
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.execution_plan_gate_service import (
    GateEvaluation,
    RegistrySnapshot,
    evaluate_gate,
)
from data_models.execution_preview import (
    GeneratedOperation,
    GeneratedTaskRequirement,
    MissingLink,
    ProductSystemExecutionPreview,
    TraceSource,
)


# ---------------------------------------------------------------------------
# Fixtures — minimal order row and registries
# ---------------------------------------------------------------------------


@dataclass
class FakeOrderRow:
    """Minimal duck-typed order row for gate tests."""

    id: int = 1001
    code: str = "ORD-TEST-001"
    snapshot_version: int = 1
    snapshot_line_items: Optional[str] = None

    def __post_init__(self):
        if self.snapshot_line_items is None:
            import json

            self.snapshot_line_items = json.dumps(
                {
                    "line_items": [
                        {
                            "product_definition": {
                                "product_id": "PROD-001",
                                "template_code": "TPL-ACP-LIGHT-ROUTED",
                                "layers": [
                                    {
                                        "layer_type": "base",
                                        "material": "aluminium_composite",
                                        "thickness_mm": 3,
                                    }
                                ],
                            },
                            "quantity": 2,
                            "cost_result": {
                                "total": 150.0,
                                "currency": "EUR",
                                "breakdown": {"material": 80, "labour": 70},
                            },
                        }
                    ]
                }
            )


def _make_registries(
    product_system_available: bool = False,
    materials_available: bool = False,
    machines_available: bool = False,
    skills: Optional[List[str]] = None,
    workcenters: Optional[List[str]] = None,
) -> RegistrySnapshot:
    """Create a RegistrySnapshot with specified availability."""
    return RegistrySnapshot(
        skills=skills or ["cnc_routing", "laser_cutting", "laminating"],
        workcenters=workcenters or ["WC-CNC-01", "WC-LASER-01"],
        roles=["operator", "supervisor"],
        product_system_available=product_system_available,
        materials_registry_available=materials_available,
        machines_registry_available=machines_available,
        version_tag="v92.1-test",
    )


def _make_trace_source() -> TraceSource:
    """Create a valid TraceSource for preview fixtures."""
    return TraceSource(
        registries_consulted=["skills", "workcenters"],
        registries_unavailable=["materials", "machines"],
        template_resolved_at="2026-05-08T10:00:00Z",
        linkage_validation_run=True,
        linkage_blockers_count=0,
        linkage_warnings_count=0,
    )


def _make_clean_preview(order_id: int = 1001) -> ProductSystemExecutionPreview:
    """Preview with no blockers (template is clean)."""
    return ProductSystemExecutionPreview(
        order_id=order_id,
        order_code="ORD-TEST-001",
        template_code="TPL-ACP-LIGHT-ROUTED",
        template_version="1.0",
        generated_operations=[
            GeneratedOperation(
                operation_id="OP-001",
                task_type="cnc_routing",
                sequence_index=1,
                depends_on_operation_ids=[],
                component_id=None,
                description="CNC routing of ACP panel",
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
        trace_source=_make_trace_source(),
    )


def _make_preview_with_blk05(order_id: int = 1001) -> ProductSystemExecutionPreview:
    """Preview with PS-BLK-05 (missing required skills) → maps to BLK-12."""
    return ProductSystemExecutionPreview(
        order_id=order_id,
        order_code="ORD-TEST-001",
        template_code="TPL-ACP-LIGHT-ROUTED",
        template_version="1.0",
        generated_operations=[],
        generated_task_requirements=[],
        blockers=[
            {
                "code": "PS-BLK-05",
                "message": "Task template TT-002 missing required_skill_ids for task_type cnc_routing",
                "task_template_id": "TT-002",
                "path": "task_templates.TT-002.required_skill_ids",
            }
        ],
        warnings=[],
        missing_links=[],
        trace_source=TraceSource(
            registries_consulted=["skills", "workcenters"],
            registries_unavailable=["materials", "machines"],
            template_resolved_at="2026-05-08T10:00:00Z",
            linkage_validation_run=True,
            linkage_blockers_count=1,
            linkage_warnings_count=0,
        ),
    )


def _make_preview_with_blk06(order_id: int = 1001) -> ProductSystemExecutionPreview:
    """Preview with PS-BLK-06 (missing machine/workcenter) → maps to BLK-13."""
    return ProductSystemExecutionPreview(
        order_id=order_id,
        order_code="ORD-TEST-001",
        template_code="TPL-ACP-LIGHT-ROUTED",
        template_version="1.0",
        generated_operations=[],
        generated_task_requirements=[],
        blockers=[
            {
                "code": "PS-BLK-06",
                "message": "Task template TT-003 missing workcenter or machine for task_type laser_cutting",
                "task_template_id": "TT-003",
                "path": "task_templates.TT-003.required_workcenter_id",
            }
        ],
        warnings=[],
        missing_links=[],
        trace_source=TraceSource(
            registries_consulted=["skills", "workcenters"],
            registries_unavailable=["materials", "machines"],
            template_resolved_at="2026-05-08T10:00:00Z",
            linkage_validation_run=True,
            linkage_blockers_count=1,
            linkage_warnings_count=0,
        ),
    )


def _make_preview_with_blk09(order_id: int = 1001) -> ProductSystemExecutionPreview:
    """Preview with PS-BLK-09 (skill not in registry) → maps to BLK-16."""
    return ProductSystemExecutionPreview(
        order_id=order_id,
        order_code="ORD-TEST-001",
        template_code="TPL-ACP-LIGHT-ROUTED",
        template_version="1.0",
        generated_operations=[],
        generated_task_requirements=[],
        blockers=[
            {
                "code": "PS-BLK-09",
                "message": "Skill code 'unknown_skill' not found in Skills Registry",
                "task_template_id": "TT-004",
                "path": "task_templates.TT-004.required_skill_ids[0]",
            }
        ],
        warnings=[],
        missing_links=[],
        trace_source=TraceSource(
            registries_consulted=["skills", "workcenters"],
            registries_unavailable=["materials", "machines"],
            template_resolved_at="2026-05-08T10:00:00Z",
            linkage_validation_run=True,
            linkage_blockers_count=1,
            linkage_warnings_count=0,
        ),
    )


def _make_preview_with_blk10(order_id: int = 1001) -> ProductSystemExecutionPreview:
    """Preview with PS-BLK-10 (workcenter not in registry) → maps to BLK-17."""
    return ProductSystemExecutionPreview(
        order_id=order_id,
        order_code="ORD-TEST-001",
        template_code="TPL-ACP-LIGHT-ROUTED",
        template_version="1.0",
        generated_operations=[],
        generated_task_requirements=[],
        blockers=[
            {
                "code": "PS-BLK-10",
                "message": "Workcenter code 'WC-UNKNOWN' not found in Workcenters Registry",
                "task_template_id": "TT-005",
                "path": "task_templates.TT-005.required_workcenter_id",
            }
        ],
        warnings=[],
        missing_links=[],
        trace_source=TraceSource(
            registries_consulted=["skills", "workcenters"],
            registries_unavailable=["materials", "machines"],
            template_resolved_at="2026-05-08T10:00:00Z",
            linkage_validation_run=True,
            linkage_blockers_count=1,
            linkage_warnings_count=0,
        ),
    )


def _make_preview_with_missing_source_op(
    order_id: int = 1001,
) -> ProductSystemExecutionPreview:
    """Preview with missing source_operation_id → maps to BLK-15."""
    return ProductSystemExecutionPreview(
        order_id=order_id,
        order_code="ORD-TEST-001",
        template_code="TPL-ACP-LIGHT-ROUTED",
        template_version="1.0",
        generated_operations=[],
        generated_task_requirements=[],
        blockers=[],
        warnings=[],
        missing_links=[
            MissingLink(
                task_template_id="TT-006",
                field="source_operation_id",
                reason="source_operation_id does not resolve in production_operations",
                available_today=True,
            )
        ],
        trace_source=TraceSource(
            registries_consulted=["skills", "workcenters"],
            registries_unavailable=["materials", "machines"],
            template_resolved_at="2026-05-08T10:00:00Z",
            linkage_validation_run=True,
            linkage_blockers_count=0,
            linkage_warnings_count=0,
        ),
    )


# ---------------------------------------------------------------------------
# Test 1: Config=false → WRN-01 emitted, no BLK-12..17
# ---------------------------------------------------------------------------


class TestGateIntegrationConfigFalse:
    """When registry_productsystem_live=false, gate behaves as before."""

    def test_wrn01_emitted(self):
        """WRN-01 is emitted when product_system_available=False."""
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=False)
        result = evaluate_gate(order, registries, False, productsystem_preview=None)

        warning_codes = [w["code"] for w in result.warnings]
        assert "WRN-01" in warning_codes

    def test_no_blk12_through_17(self):
        """BLK-12..17 are NOT in blockers when config=false."""
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=False)
        result = evaluate_gate(order, registries, False, productsystem_preview=None)

        blocker_codes = [b["code"] for b in result.blockers]
        for code in ("BLK-12", "BLK-13", "BLK-15", "BLK-16", "BLK-17"):
            assert code not in blocker_codes

    def test_missing_links_emitted(self):
        """3 missing_links entries emitted when config=false."""
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=False)
        result = evaluate_gate(order, registries, False, productsystem_preview=None)

        # Gate missing_links use "link" key, not "field"
        ml_links = [ml["link"] for ml in result.missing_links]
        assert "task.required_skill_ids" in ml_links
        assert "task.required_workcenter_id_or_machine_type" in ml_links
        assert "task.source_operation_id" in ml_links

    def test_backward_compatible_no_preview_param(self):
        """Gate works without the productsystem_preview parameter (backward compat)."""
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=False)
        # Call without the new parameter — should use default None
        result = evaluate_gate(order, registries, False)

        warning_codes = [w["code"] for w in result.warnings]
        assert "WRN-01" in warning_codes


# ---------------------------------------------------------------------------
# Test 2: Config=true + preview provided → WRN-01 NOT emitted
# ---------------------------------------------------------------------------


class TestGateIntegrationConfigTrueNoWrn01:
    """When product_system_available=True and preview is provided, WRN-01 suppressed."""

    def test_no_wrn01_with_clean_preview(self):
        """WRN-01 NOT emitted when preview is provided and config=true."""
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_clean_preview()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        warning_codes = [w["code"] for w in result.warnings]
        assert "WRN-01" not in warning_codes

    def test_no_missing_links_for_productsystem(self):
        """Missing links for ProductSystem NOT emitted when preview consumed."""
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_clean_preview()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        ml_links = [ml["link"] for ml in result.missing_links]
        assert "task.required_skill_ids" not in ml_links
        assert "task.required_workcenter_id_or_machine_type" not in ml_links
        assert "task.source_operation_id" not in ml_links


# ---------------------------------------------------------------------------
# Test 3: Config=true + BLK-12 (PS-BLK-05)
# ---------------------------------------------------------------------------


class TestGateIntegrationBlk12:
    """BLK-12 emitted when preview contains PS-BLK-05."""

    def test_blk12_in_blockers(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_preview_with_blk05()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        blocker_codes = [b["code"] for b in result.blockers]
        assert "BLK-12" in blocker_codes

    def test_blk12_has_task_ref(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_preview_with_blk05()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        blk12 = [b for b in result.blockers if b["code"] == "BLK-12"][0]
        assert blk12["task_ref"]["task_template_id"] == "TT-002"


# ---------------------------------------------------------------------------
# Test 4: Config=true + BLK-13 (PS-BLK-06)
# ---------------------------------------------------------------------------


class TestGateIntegrationBlk13:
    """BLK-13 emitted when preview contains PS-BLK-06."""

    def test_blk13_in_blockers(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_preview_with_blk06()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        blocker_codes = [b["code"] for b in result.blockers]
        assert "BLK-13" in blocker_codes


# ---------------------------------------------------------------------------
# Test 5: Config=true + BLK-15 (missing source_operation_id)
# ---------------------------------------------------------------------------


class TestGateIntegrationBlk15:
    """BLK-15 emitted when preview has missing source_operation_id link."""

    def test_blk15_in_blockers(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_preview_with_missing_source_op()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        blocker_codes = [b["code"] for b in result.blockers]
        assert "BLK-15" in blocker_codes


# ---------------------------------------------------------------------------
# Test 6: Config=true + BLK-16 (PS-BLK-09)
# ---------------------------------------------------------------------------


class TestGateIntegrationBlk16:
    """BLK-16 emitted when preview contains PS-BLK-09."""

    def test_blk16_in_blockers(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_preview_with_blk09()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        blocker_codes = [b["code"] for b in result.blockers]
        assert "BLK-16" in blocker_codes


# ---------------------------------------------------------------------------
# Test 7: Config=true + BLK-17 (PS-BLK-10)
# ---------------------------------------------------------------------------


class TestGateIntegrationBlk17:
    """BLK-17 emitted when preview contains PS-BLK-10."""

    def test_blk17_in_blockers(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_preview_with_blk10()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        blocker_codes = [b["code"] for b in result.blockers]
        assert "BLK-17" in blocker_codes


# ---------------------------------------------------------------------------
# Test 8: Config=true + clean preview → no BLK-12..17
# ---------------------------------------------------------------------------


class TestGateIntegrationCleanPreview:
    """Clean preview (no blockers) → no BLK-12..17 emitted."""

    def test_no_blk12_through_17(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_clean_preview()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        blocker_codes = [b["code"] for b in result.blockers]
        for code in ("BLK-12", "BLK-13", "BLK-15", "BLK-16", "BLK-17"):
            assert code not in blocker_codes


# ---------------------------------------------------------------------------
# Test 9: Config=true + preview=None (failure) → WRN-01 fallback
# ---------------------------------------------------------------------------


class TestGateIntegrationPreviewFailure:
    """When config=true but preview is None (service failed), WRN-01 is emitted."""

    def test_wrn01_fallback(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        result = evaluate_gate(order, registries, False, productsystem_preview=None)

        warning_codes = [w["code"] for w in result.warnings]
        assert "WRN-01" in warning_codes

    def test_no_blk12_through_17_on_failure(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        result = evaluate_gate(order, registries, False, productsystem_preview=None)

        blocker_codes = [b["code"] for b in result.blockers]
        for code in ("BLK-12", "BLK-13", "BLK-15", "BLK-16", "BLK-17"):
            assert code not in blocker_codes


# ---------------------------------------------------------------------------
# Test 10: WRN-02 independent of registry_productsystem_live
# ---------------------------------------------------------------------------


class TestGateIntegrationWrn02Independent:
    """WRN-02 still emitted when materials_registry_available=False, regardless of PS config."""

    def test_wrn02_with_ps_true(self):
        order = FakeOrderRow()
        registries = _make_registries(
            product_system_available=True, materials_available=False
        )
        preview = _make_clean_preview()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        warning_codes = [w["code"] for w in result.warnings]
        assert "WRN-02" in warning_codes


# ---------------------------------------------------------------------------
# Test 11: WRN-03 independent of registry_productsystem_live
# ---------------------------------------------------------------------------


class TestGateIntegrationWrn03Independent:
    """WRN-03 still emitted when machines_registry_available=False, regardless of PS config."""

    def test_wrn03_with_ps_true(self):
        order = FakeOrderRow()
        registries = _make_registries(
            product_system_available=True, machines_available=False
        )
        preview = _make_clean_preview()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        warning_codes = [w["code"] for w in result.warnings]
        assert "WRN-03" in warning_codes


# ---------------------------------------------------------------------------
# Test 12: BLK-14/18/19 NEVER emitted from this integration
# ---------------------------------------------------------------------------


class TestGateIntegrationNoBlk14_18_19:
    """BLK-14, BLK-18, BLK-19 must NEVER appear from PS integration."""

    def test_no_blk14_blk18_blk19(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        # Use a preview with all PS blockers
        preview = _make_preview_with_blk05()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        blocker_codes = [b["code"] for b in result.blockers]
        assert "BLK-14" not in blocker_codes
        assert "BLK-18" not in blocker_codes
        assert "BLK-19" not in blocker_codes


# ---------------------------------------------------------------------------
# Test 13: can_generate=False when preview blockers present
# ---------------------------------------------------------------------------


class TestGateIntegrationCanGenerate:
    """can_generate reflects mapped blockers."""

    def test_can_generate_false_with_blockers(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_preview_with_blk05()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        assert result.can_generate is False

    def test_can_generate_not_blocked_by_productsystem(self):
        """Clean preview does NOT add BLK-12..17 blockers (can_generate unaffected by PS)."""
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_clean_preview()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        # Verify no PS-related blockers are present
        blocker_codes = [b["code"] for b in result.blockers]
        for code in ("BLK-12", "BLK-13", "BLK-15", "BLK-16", "BLK-17"):
            assert code not in blocker_codes
        # Note: can_generate may still be False due to other structural blockers
        # (BLK-02, BLK-03) from the test snapshot format. The key invariant is
        # that ProductSystem clean preview does NOT contribute blockers.


# ---------------------------------------------------------------------------
# Test 14/15: trace_source includes product_system when preview consumed
# ---------------------------------------------------------------------------


class TestGateIntegrationTraceSource:
    """trace_source includes product_system info when preview consumed."""

    def test_trace_source_includes_product_system(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=True)
        preview = _make_clean_preview()
        result = evaluate_gate(order, registries, False, productsystem_preview=preview)

        consulted_names = [
            r["name"] for r in result.trace_source.get("registries_consulted", [])
        ]
        assert "product_system" in consulted_names

    def test_trace_source_no_product_system_when_config_false(self):
        order = FakeOrderRow()
        registries = _make_registries(product_system_available=False)
        result = evaluate_gate(order, registries, False, productsystem_preview=None)

        consulted_names = [
            r["name"] for r in result.trace_source.get("registries_consulted", [])
        ]
        assert "product_system" not in consulted_names