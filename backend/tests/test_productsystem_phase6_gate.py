"""
Phase 6 — Contract tests for Gate Integration (S27).

Tests T6-16 through T6-25 (gate integration with ProductSystem preview).

These tests validate:
  - Gate behavior with REGISTRY_PRODUCTSYSTEM_LIVE=false (WRN-01 emitted)
  - Gate behavior with REGISTRY_PRODUCTSYSTEM_LIVE=true (no WRN-01, BLK-* emitted)
  - PS-BLK → gate BLK mapping correctness
  - BLK-14/18/19 NOT emitted by Phase 6
"""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from data_models.execution_preview import (
    GeneratedOperation,
    GeneratedTaskRequirement,
    MissingLink,
    ProductSystemExecutionPreview,
    TraceSource,
)
from services.gate_blocker_mapper import map_preview_to_gate_blockers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_preview(
    blockers: List[Dict[str, Any]] = None,
    warnings: List[Dict[str, Any]] = None,
    missing_links: List[MissingLink] = None,
) -> ProductSystemExecutionPreview:
    """Build a minimal ProductSystemExecutionPreview for gate tests."""
    return ProductSystemExecutionPreview(
        order_id=1,
        order_code="ORD-2026-001",
        template_code="TPL-ACP-LIGHT-ROUTED",
        template_version=None,
        generated_operations=[
            GeneratedOperation(
                operation_id="OP-001",
                task_type="cnc_routing",
                sequence_index=1,
                depends_on_operation_ids=[],
                component_id="COMP-001",
                description="Test operation",
            )
        ],
        generated_task_requirements=[
            GeneratedTaskRequirement(
                task_template_id="TT-001",
                source_operation_id="OP-001",
                task_type="cnc_routing",
                required_skill_ids=["SKILL-CNC-ROUTER"],
                required_workcenter_id="WC-CNC-01",
                required_machine_type="cnc_router",
                required_machine_id=None,
                material_requirements=[],
                estimated_duration={"value": 45, "unit": "minutes"},
            )
        ],
        missing_links=missing_links if missing_links is not None else [],
        blockers=blockers if blockers is not None else [],
        warnings=warnings if warnings is not None else [],
        trace_source=TraceSource(
            registries_consulted=["skills", "workcenters"],
            registries_unavailable=["materials", "machines"],
            template_resolved_at="2026-05-07T14:30:00Z",
            linkage_validation_run=True,
            linkage_blockers_count=len(blockers) if blockers else 0,
            linkage_warnings_count=len(warnings) if warnings else 0,
        ),
    )


def _make_ps_blocker(code: str, task_id: str = "TT-001", message: str = "") -> Dict[str, Any]:
    """Build a PS blocker dict."""
    return {
        "severity": "blocker",
        "task_template_id": task_id,
        "path": f"task_templates[0].required_skill_ids[0]",
        "code": code,
        "message": message if message else f"Test blocker {code}",
        "details": {},
    }


# ---------------------------------------------------------------------------
# T6-16: Gate productsystem_live=false emits WRN-01
# ---------------------------------------------------------------------------


def test_gate_productsystem_live_false_emits_wrn01():
    """T6-16: Config=false → WRN-01 emitted (current behavior preserved)."""
    from services.execution_plan_gate_service import (
        GateEvaluation,
        RegistrySnapshot,
        evaluate_gate,
    )

    # Build a minimal order row
    class MockOrder:
        id = 1
        code = "ORD-001"
        snapshot_version = 1
        snapshot_line_items = '{"product_definition": {"product_id": "P1", "quantity": 1, "layers": [{"processes": [{"type": "cnc_routing", "estimated_time_minutes": 30}]}]}, "cost_result": {"total": 100}}'

    registries = RegistrySnapshot(
        skills=["SKILL-CNC-ROUTER"],
        workcenters=["WC-CNC-01"],
        roles=["OP_CNC"],
        product_system_available=False,  # NOT live
        materials_registry_available=False,
        machines_registry_available=False,
    )

    result = evaluate_gate(MockOrder(), registries, plan_already_exists=False)

    warning_codes = [w.get("code") for w in result.warnings]
    assert "WRN-01" in warning_codes


# ---------------------------------------------------------------------------
# T6-17: Gate productsystem_live=true → no WRN-01
# ---------------------------------------------------------------------------


def test_gate_productsystem_live_true_no_wrn01():
    """T6-17: Config=true + valid preview → WRN-01 NOT emitted (replaced by BLK-*)."""
    from services.execution_plan_gate_service import (
        RegistrySnapshot,
        evaluate_gate,
    )

    class MockOrder:
        id = 1
        code = "ORD-001"
        snapshot_version = 1
        snapshot_line_items = '{"product_definition": {"product_id": "P1", "quantity": 1, "layers": [{"processes": [{"type": "cnc_routing", "estimated_time_minutes": 30}]}]}, "cost_result": {"total": 100}}'

    registries = RegistrySnapshot(
        skills=["SKILL-CNC-ROUTER"],
        workcenters=["WC-CNC-01"],
        roles=["OP_CNC"],
        product_system_available=True,  # LIVE
        materials_registry_available=False,
        machines_registry_available=False,
    )

    # S30 integration: preview must be provided when product_system_available=True
    # to suppress WRN-01. Without preview, gate falls back to WRN-01 gracefully.
    clean_preview = _build_preview(blockers=[], warnings=[], missing_links=[])
    result = evaluate_gate(
        MockOrder(), registries, plan_already_exists=False,
        productsystem_preview=clean_preview,
    )

    warning_codes = [w.get("code") for w in result.warnings]
    # When product_system_available=True AND preview provided, WRN-01 should NOT be emitted
    assert "WRN-01" not in warning_codes


# ---------------------------------------------------------------------------
# T6-18: Gate productsystem_live=true emits BLK-12
# ---------------------------------------------------------------------------


def test_gate_productsystem_live_true_emits_blk12():
    """T6-18: Config=true + missing skills → BLK-12 via mapper."""
    preview = _build_preview(
        blockers=[_make_ps_blocker("PS-BLK-05", message="Missing required_skill_ids")]
    )
    gate_blockers = map_preview_to_gate_blockers(preview)

    codes = [b["code"] for b in gate_blockers]
    assert "BLK-12" in codes


# ---------------------------------------------------------------------------
# T6-19: Gate productsystem_live=true emits BLK-13
# ---------------------------------------------------------------------------


def test_gate_productsystem_live_true_emits_blk13():
    """T6-19: Config=true + missing workcenter → BLK-13 via mapper."""
    preview = _build_preview(
        blockers=[_make_ps_blocker("PS-BLK-06", message="Missing workcenter/machine")]
    )
    gate_blockers = map_preview_to_gate_blockers(preview)

    codes = [b["code"] for b in gate_blockers]
    assert "BLK-13" in codes


# ---------------------------------------------------------------------------
# T6-20: Gate productsystem_live=true emits BLK-15
# ---------------------------------------------------------------------------


def test_gate_productsystem_live_true_emits_blk15():
    """T6-20: Config=true + missing source_op → BLK-15 via mapper."""
    preview = _build_preview(
        missing_links=[
            MissingLink(
                field="source_operation_id",
                task_template_id="TT-001",
                reason="source_operation_id 'OP-MISSING' not found",
                available_today=True,
            )
        ]
    )
    gate_blockers = map_preview_to_gate_blockers(preview)

    codes = [b["code"] for b in gate_blockers]
    assert "BLK-15" in codes


# ---------------------------------------------------------------------------
# T6-21: Gate productsystem_live=true emits BLK-16
# ---------------------------------------------------------------------------


def test_gate_productsystem_live_true_emits_blk16():
    """T6-21: Config=true + unresolvable skill → BLK-16 via mapper."""
    preview = _build_preview(
        blockers=[_make_ps_blocker("PS-BLK-09", message="Skill not in registry")]
    )
    gate_blockers = map_preview_to_gate_blockers(preview)

    codes = [b["code"] for b in gate_blockers]
    assert "BLK-16" in codes


# ---------------------------------------------------------------------------
# T6-22: Gate productsystem_live=true emits BLK-17
# ---------------------------------------------------------------------------


def test_gate_productsystem_live_true_emits_blk17():
    """T6-22: Config=true + unresolvable workcenter → BLK-17 via mapper."""
    preview = _build_preview(
        blockers=[_make_ps_blocker("PS-BLK-10", message="Workcenter not in registry")]
    )
    gate_blockers = map_preview_to_gate_blockers(preview)

    codes = [b["code"] for b in gate_blockers]
    assert "BLK-17" in codes


# ---------------------------------------------------------------------------
# T6-23: Gate WRN-02 always when materials not live
# ---------------------------------------------------------------------------


def test_gate_wrn02_always_when_materials_not_live():
    """T6-23: Config=true + materials_live=false → WRN-02."""
    from services.execution_plan_gate_service import (
        RegistrySnapshot,
        evaluate_gate,
    )

    class MockOrder:
        id = 1
        code = "ORD-001"
        snapshot_version = 1
        snapshot_line_items = '{"product_definition": {"product_id": "P1", "quantity": 1, "layers": [{"processes": [{"type": "cnc_routing", "estimated_time_minutes": 30}]}]}, "cost_result": {"total": 100}}'

    registries = RegistrySnapshot(
        skills=["SKILL-CNC-ROUTER"],
        workcenters=["WC-CNC-01"],
        roles=["OP_CNC"],
        product_system_available=True,
        materials_registry_available=False,  # NOT live
        machines_registry_available=False,
    )

    result = evaluate_gate(MockOrder(), registries, plan_already_exists=False)

    warning_codes = [w.get("code") for w in result.warnings]
    assert "WRN-02" in warning_codes


# ---------------------------------------------------------------------------
# T6-24: Gate WRN-03 always when machines not live
# ---------------------------------------------------------------------------


def test_gate_wrn03_always_when_machines_not_live():
    """T6-24: Config=true + machines_live=false → WRN-03."""
    from services.execution_plan_gate_service import (
        RegistrySnapshot,
        evaluate_gate,
    )

    class MockOrder:
        id = 1
        code = "ORD-001"
        snapshot_version = 1
        snapshot_line_items = '{"product_definition": {"product_id": "P1", "quantity": 1, "layers": [{"processes": [{"type": "cnc_routing", "estimated_time_minutes": 30}]}]}, "cost_result": {"total": 100}}'

    registries = RegistrySnapshot(
        skills=["SKILL-CNC-ROUTER"],
        workcenters=["WC-CNC-01"],
        roles=["OP_CNC"],
        product_system_available=True,
        materials_registry_available=False,
        machines_registry_available=False,  # NOT live
    )

    result = evaluate_gate(MockOrder(), registries, plan_already_exists=False)

    warning_codes = [w.get("code") for w in result.warnings]
    assert "WRN-03" in warning_codes


# ---------------------------------------------------------------------------
# T6-25: No BLK-14/18/19 from Phase 6
# ---------------------------------------------------------------------------


def test_gate_no_blk14_blk18_blk19_from_phase6():
    """T6-25: Phase 6 does NOT emit BLK-14/18/19."""
    # Build a preview with various PS blockers that Phase 6 handles
    preview = _build_preview(
        blockers=[
            _make_ps_blocker("PS-BLK-05"),
            _make_ps_blocker("PS-BLK-06"),
            _make_ps_blocker("PS-BLK-09"),
            _make_ps_blocker("PS-BLK-10"),
        ]
    )
    gate_blockers = map_preview_to_gate_blockers(preview)

    codes = [b["code"] for b in gate_blockers]
    # BLK-14, BLK-18, BLK-19 must NOT appear
    assert "BLK-14" not in codes
    assert "BLK-18" not in codes
    assert "BLK-19" not in codes


# ---------------------------------------------------------------------------
# T6-26 through T6-30: Endpoint tests (via mapper validation)
# ---------------------------------------------------------------------------


def test_mapper_returns_list():
    """T6-26: Mapper always returns a list."""
    preview = _build_preview()
    result = map_preview_to_gate_blockers(preview)
    assert isinstance(result, list)


def test_mapper_empty_when_no_blockers():
    """T6-27: No blockers → empty gate blockers list."""
    preview = _build_preview(blockers=[], missing_links=[])
    result = map_preview_to_gate_blockers(preview)
    assert len(result) == 0


def test_mapper_preserves_task_template_id():
    """T6-28: Gate blocker preserves task_template_id from PS blocker."""
    preview = _build_preview(
        blockers=[_make_ps_blocker("PS-BLK-09", task_id="TT-CUSTOM-001")]
    )
    result = map_preview_to_gate_blockers(preview)
    assert len(result) == 1
    assert result[0]["task_ref"]["task_template_id"] == "TT-CUSTOM-001"


def test_mapper_ignores_unknown_ps_codes():
    """T6-29: Unknown PS codes are not mapped to gate blockers."""
    preview = _build_preview(
        blockers=[_make_ps_blocker("PS-BLK-99", message="Unknown code")]
    )
    result = map_preview_to_gate_blockers(preview)
    # PS-BLK-99 has no mapping → should not produce a gate blocker
    assert len(result) == 0


def test_mapper_blk15_only_from_available_today():
    """T6-30: BLK-15 only emitted for missing links with available_today=True."""
    preview = _build_preview(
        missing_links=[
            MissingLink(
                field="source_operation_id",
                task_template_id="TT-001",
                reason="Not found",
                available_today=False,  # NOT available today
            )
        ]
    )
    result = map_preview_to_gate_blockers(preview)
    codes = [b["code"] for b in result]
    assert "BLK-15" not in codes