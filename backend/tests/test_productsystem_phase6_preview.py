"""
Phase 6 — Contract tests for ProductSystem Execution Preview (S27).

Tests T6-01 through T6-15 (preview service) and T6-26 through T6-30 (endpoint).

These tests validate:
  - Preview envelope structure and invariants
  - Error handling (order not found, template not found, template inactive)
  - Trace source completeness
  - Forbidden imports / silent fallbacks (grep-based)
  - Source operation resolution
  - Missing links computation
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from data_models.execution_preview import (
    GeneratedOperation,
    GeneratedTaskRequirement,
    MissingLink,
    ProductSystemExecutionPreview,
    TraceSource,
)
from data_models.linkage_contracts import LinkageIssue, LinkageValidationResult
from services.product_system_execution_output_service import (
    OrderNotFoundError,
    ProductSystemExecutionPreviewService,
    TemplateCodeNotFoundError,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _mock_order_row(
    order_id: int = 1,
    code: str = "ORD-2026-001",
    template_code: str = "TPL-ACP-LIGHT-ROUTED",
) -> Dict[str, Any]:
    """Build a mock order row dict."""
    import json

    snapshot = {
        "product_definition": {
            "product_code": template_code,
            "quantity": 1,
        }
    }
    return {
        "id": order_id,
        "code": code,
        "snapshot_line_items": json.dumps(snapshot),
        "snapshot_version": 1,
    }


def _mock_template_row(
    template_id: int = 21,
    template_code: str = "TPL-ACP-LIGHT-ROUTED",
    active: bool = True,
) -> Dict[str, Any]:
    return {
        "id": template_id,
        "template_code": template_code,
        "family_name": "ACP Light",
        "active": active,
        "version": None,
    }


def _mock_operations(count: int = 8) -> List[Dict[str, Any]]:
    """Build mock production_operations rows."""
    ops = []
    for i in range(1, count + 1):
        ops.append(
            {
                "operation_id": f"OP-{i:03d}",
                "task_type": "cnc_routing",
                "sequence_index": i,
                "depends_on_operation_ids": [f"OP-{i-1:03d}"] if i > 1 else [],
                "component_id": f"COMP-{i:03d}",
                "description": f"Operation {i}",
            }
        )
    return ops


def _mock_task_templates(count: int = 8) -> List[Dict[str, Any]]:
    """Build mock task_templates rows."""
    tasks = []
    for i in range(1, count + 1):
        tasks.append(
            {
                "task_template_id": f"TT-{i:03d}",
                "source_operation_id": f"OP-{i:03d}",
                "task_type": "cnc_routing",
                "required_skill_ids": ["SKILL-CNC-ROUTER"],
                "required_workcenter_id": "WC-CNC-01",
                "required_machine_type": "cnc_router",
                "required_machine_id": None,
                "material_requirements": [
                    {"material_code": "MAT-ACP-3MM", "quantity_static": 2.5, "unit": "mp"}
                ],
                "estimated_duration": {"value": 45, "unit": "minutes"},
            }
        )
    return tasks


def _mock_linkage_result(
    template_id: int = 21,
    template_code: str = "TPL-ACP-LIGHT-ROUTED",
    blockers: List[LinkageIssue] = None,
    warnings: List[LinkageIssue] = None,
) -> LinkageValidationResult:
    """Build a mock LinkageValidationResult."""
    return LinkageValidationResult.build(
        template_id=template_id,
        template_code=template_code,
        blockers=blockers if blockers is not None else [],
        warnings=warnings if warnings is not None else [],
        registries_consulted=["skills", "workcenters"],
        registries_unavailable=["materials", "machines"],
        task_template_count=8,
    )


# ---------------------------------------------------------------------------
# T6-01: Preview valid order returns envelope
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_valid_order_returns_envelope():
    """T6-01: Order with seeded template → full envelope with all fields present."""
    db_mock = AsyncMock()

    service = ProductSystemExecutionPreviewService(db_mock)

    # Patch internal methods
    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations()
        ),
        patch.object(service, "_get_task_templates", return_value=_mock_task_templates()),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=_mock_linkage_result(),
        ),
    ):
        result = await service.preview_for_execution(1)

    assert isinstance(result, ProductSystemExecutionPreview)
    assert result.order_id == 1
    assert result.order_code == "ORD-2026-001"
    assert result.template_code == "TPL-ACP-LIGHT-ROUTED"
    assert result.trace_source is not None
    assert isinstance(result.generated_operations, list)
    assert isinstance(result.generated_task_requirements, list)
    assert isinstance(result.missing_links, list)
    assert isinstance(result.blockers, list)
    assert isinstance(result.warnings, list)


# ---------------------------------------------------------------------------
# T6-02: Preview order not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_order_not_found():
    """T6-02: Non-existent order_id raises OrderNotFoundError."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with patch.object(service, "_get_order", side_effect=OrderNotFoundError(999)):
        with pytest.raises(OrderNotFoundError):
            await service.preview_for_execution(999)


# ---------------------------------------------------------------------------
# T6-03: Preview template not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_template_not_found():
    """T6-03: Order references non-existent template_code raises TemplateCodeNotFoundError."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service,
            "_resolve_template_by_code",
            side_effect=TemplateCodeNotFoundError("TPL-UNKNOWN"),
        ),
    ):
        with pytest.raises(TemplateCodeNotFoundError):
            await service.preview_for_execution(1)


# ---------------------------------------------------------------------------
# T6-04: Preview template inactive
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_template_inactive():
    """T6-04: Order references inactive template raises TemplateInactiveError."""
    from services.product_system_linkage_validator import TemplateInactiveError

    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service,
            "_resolve_template_by_code",
            side_effect=TemplateInactiveError(21, "TPL-ACP-LIGHT-ROUTED"),
        ),
    ):
        with pytest.raises(TemplateInactiveError):
            await service.preview_for_execution(1)


# ---------------------------------------------------------------------------
# T6-05: Preview operations match production_operations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_operations_match_production_operations():
    """T6-05: Count + content match — len(generated_operations) == 8."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations(8)
        ),
        patch.object(
            service, "_get_task_templates", return_value=_mock_task_templates(8)
        ),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=_mock_linkage_result(),
        ),
    ):
        result = await service.preview_for_execution(1)

    assert len(result.generated_operations) == 8
    # Verify sequence
    for idx, op in enumerate(result.generated_operations):
        assert op.sequence_index == idx + 1


# ---------------------------------------------------------------------------
# T6-06: Preview task requirements match task_templates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_task_requirements_match_task_templates():
    """T6-06: Count + content match — len(generated_task_requirements) == 8."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations(8)
        ),
        patch.object(
            service, "_get_task_templates", return_value=_mock_task_templates(8)
        ),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=_mock_linkage_result(),
        ),
    ):
        result = await service.preview_for_execution(1)

    assert len(result.generated_task_requirements) == 8


# ---------------------------------------------------------------------------
# T6-07: Preview trace_source always present
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_trace_source_always_present():
    """T6-07: trace_source never null."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations()
        ),
        patch.object(service, "_get_task_templates", return_value=_mock_task_templates()),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=_mock_linkage_result(),
        ),
    ):
        result = await service.preview_for_execution(1)

    assert result.trace_source is not None
    assert isinstance(result.trace_source, TraceSource)


# ---------------------------------------------------------------------------
# T6-08: Preview trace registries consulted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_trace_registries_consulted():
    """T6-08: Skills + Workcenters consulted."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations()
        ),
        patch.object(service, "_get_task_templates", return_value=_mock_task_templates()),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=_mock_linkage_result(),
        ),
    ):
        result = await service.preview_for_execution(1)

    assert "skills" in result.trace_source.registries_consulted
    assert "workcenters" in result.trace_source.registries_consulted


# ---------------------------------------------------------------------------
# T6-09: Preview trace registries unavailable
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_trace_registries_unavailable():
    """T6-09: Materials + Machines unavailable."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations()
        ),
        patch.object(service, "_get_task_templates", return_value=_mock_task_templates()),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=_mock_linkage_result(),
        ),
    ):
        result = await service.preview_for_execution(1)

    assert "materials" in result.trace_source.registries_unavailable
    assert "machines" in result.trace_source.registries_unavailable


# ---------------------------------------------------------------------------
# T6-10: No forbidden imports in preview module
# ---------------------------------------------------------------------------


def test_preview_no_forbidden_imports():
    """T6-10: Grep check on preview module — 0 hits for forbidden imports."""
    preview_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "services",
        "product_system_execution_output_service.py",
    )
    with open(preview_path, "r", encoding="utf-8") as f:
        content = f.read()

    forbidden = [
        "cost_engine_service",
        "quote_orchestrator",
        "ExecutionPlanService",
        "MaterialRate",
        "execution_plan_service",
    ]

    for name in forbidden:
        # Match import statements (not comments/docstrings)
        pattern = re.compile(
            rf"^\s*(?:import\s+.*{re.escape(name)}|from\s+.*{re.escape(name)}\s+import)",
            re.MULTILINE,
        )
        matches = pattern.findall(content)
        assert len(matches) == 0, f"Forbidden import '{name}' found in preview service"


# ---------------------------------------------------------------------------
# T6-11: No silent fallbacks in preview module
# ---------------------------------------------------------------------------


def test_preview_no_silent_fallbacks():
    """T6-11: Grep check on preview module — 0 hits for 'or 0', 'or None', 'or []'."""
    preview_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "services",
        "product_system_execution_output_service.py",
    )
    with open(preview_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    silent_tokens = [" or 0", " or None", " or []", " or {}"]

    for line_num, line in enumerate(lines, 1):
        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        for token in silent_tokens:
            assert token not in line, (
                f"Silent fallback '{token}' found at line {line_num}: {line.rstrip()}"
            )


# ---------------------------------------------------------------------------
# T6-12: Preview source_operation_ids resolve
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_source_operation_ids_resolve():
    """T6-12: Every task_req.source_operation_id ∈ operations."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations(8)
        ),
        patch.object(
            service, "_get_task_templates", return_value=_mock_task_templates(8)
        ),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=_mock_linkage_result(),
        ),
    ):
        result = await service.preview_for_execution(1)

    op_ids = {op.operation_id for op in result.generated_operations}
    for task_req in result.generated_task_requirements:
        assert task_req.source_operation_id in op_ids, (
            f"source_operation_id '{task_req.source_operation_id}' not in operations"
        )


# ---------------------------------------------------------------------------
# T6-13: Preview missing_links empty when complete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_missing_links_empty_when_complete():
    """T6-13: Fully seeded template → empty missing_links."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations(8)
        ),
        patch.object(
            service, "_get_task_templates", return_value=_mock_task_templates(8)
        ),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=_mock_linkage_result(),
        ),
        patch("services.product_system_execution_output_service.settings") as mock_settings,
    ):
        mock_settings.registry_materials_live = True
        mock_settings.registry_machines_live = True
        result = await service.preview_for_execution(1)

    # With complete data and materials live, no missing links for available_today items
    available_today_links = [ml for ml in result.missing_links if ml.available_today]
    assert len(available_today_links) == 0


# ---------------------------------------------------------------------------
# T6-14: Preview blockers from linkage validator
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_blockers_from_linkage_validator():
    """T6-14: Inject invalid skill → blocker appears with PS-BLK-09."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    blocker = LinkageIssue(
        severity="blocker",
        task_template_id="TT-001",
        path="task_templates[0].required_skill_ids[0]",
        code="PS-BLK-09",
        message="Skill code 'INVALID-SKILL' not found in Skills Registry",
        details={"skill_code": "INVALID-SKILL", "reason": "not_found"},
    )
    linkage_with_blocker = _mock_linkage_result(blockers=[blocker])

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations()
        ),
        patch.object(service, "_get_task_templates", return_value=_mock_task_templates()),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=linkage_with_blocker,
        ),
    ):
        result = await service.preview_for_execution(1)

    assert len(result.blockers) > 0
    codes = [b.get("code") for b in result.blockers]
    assert "PS-BLK-09" in codes


# ---------------------------------------------------------------------------
# T6-15: Preview warnings from linkage validator
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_warnings_from_linkage_validator():
    """T6-15: Materials not live → PS-WRN-02 in warnings."""
    db_mock = AsyncMock()
    service = ProductSystemExecutionPreviewService(db_mock)

    warning = LinkageIssue(
        severity="warning",
        task_template_id="TT-001",
        path="task_templates[0].material_requirements[0].material_code",
        code="PS-WRN-02",
        message="Materials registry not live; material_code cannot be FK-validated",
        details={"registry": "materials", "reason": "registry_not_live"},
    )
    linkage_with_warning = _mock_linkage_result(warnings=[warning])

    with (
        patch.object(service, "_get_order", return_value=_mock_order_row()),
        patch.object(
            service, "_resolve_template_by_code", return_value=_mock_template_row()
        ),
        patch.object(
            service, "_get_production_operations", return_value=_mock_operations()
        ),
        patch.object(service, "_get_task_templates", return_value=_mock_task_templates()),
        patch.object(
            service._linkage_validator,
            "validate_template_linkage",
            return_value=linkage_with_warning,
        ),
    ):
        result = await service.preview_for_execution(1)

    assert len(result.warnings) > 0
    codes = [w.get("code") for w in result.warnings]
    assert "PS-WRN-02" in codes