"""
Phase 6 — PS-BLK to Gate BLK mapping utility (S27).

Maps ProductSystem linkage blocker codes to Execution Plan Gate blocker codes.

Mapping table (spec §17.4):
  PS-BLK-05 → BLK-12 (TASK_MISSING_REQUIRED_SKILLS)
  PS-BLK-06 → BLK-13 (TASK_MISSING_MACHINE_OR_WORKCENTER)
  PS-BLK-09 → BLK-16 (SKILL_CODE_NOT_IN_REGISTRY)
  PS-BLK-10 → BLK-17 (WORKCENTER_CODE_NOT_IN_REGISTRY)
  (missing source_operation_id) → BLK-15 (TASK_WITHOUT_SOURCE_OPERATION)

No DB writes. No mutations. Pure mapping utility.

Forbidden imports:
  - cost_engine_service
  - quote_orchestrator
  - ExecutionPlanService
  - MaterialRate
"""

from __future__ import annotations

from typing import Any, Dict, List

from data_models.execution_preview import MissingLink, ProductSystemExecutionPreview


# ---------------------------------------------------------------------------
# Mapping table
# ---------------------------------------------------------------------------

# PS blocker code → gate blocker code
_PS_TO_GATE_BLK: Dict[str, str] = {
    "PS-BLK-05": "BLK-12",
    "PS-BLK-06": "BLK-13",
    "PS-BLK-09": "BLK-16",
    "PS-BLK-10": "BLK-17",
}

# Gate blocker descriptions
_GATE_BLK_DESCRIPTIONS: Dict[str, str] = {
    "BLK-12": "TASK_MISSING_REQUIRED_SKILLS",
    "BLK-13": "TASK_MISSING_MACHINE_OR_WORKCENTER",
    "BLK-15": "TASK_WITHOUT_SOURCE_OPERATION",
    "BLK-16": "SKILL_CODE_NOT_IN_REGISTRY",
    "BLK-17": "WORKCENTER_CODE_NOT_IN_REGISTRY",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def map_preview_to_gate_blockers(
    preview: ProductSystemExecutionPreview,
) -> List[Dict[str, Any]]:
    """
    Map a ProductSystemExecutionPreview's blockers and missing_links
    to gate-level blocker dicts.

    Returns a list of gate blocker dicts ready for GateEvaluation.blockers.
    """
    gate_blockers: List[Dict[str, Any]] = []

    # Map PS-BLK-* blockers to gate BLK-*
    for blk in preview.blockers:
        ps_code = blk.get("code", "")
        gate_code = _PS_TO_GATE_BLK.get(ps_code)
        if gate_code is not None:
            gate_blockers.append(
                {
                    "code": gate_code,
                    "severity": "blocker",
                    "message": f"{_GATE_BLK_DESCRIPTIONS.get(gate_code, gate_code)}: {blk.get('message', '')}",
                    "task_ref": {
                        "task_template_id": blk.get("task_template_id", ""),
                    },
                    "details": {
                        "source_ps_code": ps_code,
                        "source_message": blk.get("message", ""),
                        "source_path": blk.get("path", ""),
                    },
                }
            )

    # Map missing source_operation_id links to BLK-15
    for link in preview.missing_links:
        if link.field == "source_operation_id" and link.available_today:
            gate_blockers.append(
                {
                    "code": "BLK-15",
                    "severity": "blocker",
                    "message": f"{_GATE_BLK_DESCRIPTIONS['BLK-15']}: {link.reason}",
                    "task_ref": {
                        "task_template_id": link.task_template_id,
                    },
                    "details": {
                        "field": link.field,
                        "reason": link.reason,
                    },
                }
            )

    return gate_blockers