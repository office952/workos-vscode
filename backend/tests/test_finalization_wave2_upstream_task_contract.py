"""FINALIZATION WAVE 2 — upstream task contract enrichment exit criteria.

Owner-approved decisions (binding):
  DEC-001=A, DEC-002=A, DEC-003=A, DEC-004=A, DEC-005=E,
  DEC-006=A, DEC-007=B, DEC-009=A

Does not materialize. Does not touch protected orders 880811 / 973019.
"""

from __future__ import annotations

import uuid

import pytest

from schemas.execution_plan_v2 import PlannedTaskPreview
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from services.execution_plan_v2_preview_service import (
    PLANNING_MINUTES_WARNING,
    _build_dependencies,
    build_execution_plan_v2_preview,
)
from services.operation_workcenter_resolution_service import (
    apply_workcenter_resolution_to_aggregate,
)
from services.product_process_aggregate_bridge import collapse_operational_alias_rules
from services.task_dependency_rules_service import PROCESS_DEPENDENCY_RULES
from tests.test_execution_plan_v2_preview import _seed_v2_order_with_snapshot
from tests.test_f7a_product_linked_task_contract_enrichment import (
    _f7a_oid,
    _f7a_snapshot_json,
)


WAVE2_OWNER_DECISIONS = {
    "DEC-001": "A",
    "DEC-002": "A",
    "DEC-003": "A",
    "DEC-004": "A",
    "DEC-005": "E",
    "DEC-006": "A",
    "DEC-007": "B",
    "DEC-009": "A",
}


def _rule(name: str, priced: str, deps: list[str] | None = None, seq: int = 1):
    return ProductAggregateTaskRule(
        task_name=name,
        task_type="process",
        priced_operation=priced,
        sequence=seq,
        depends_on_process_ids=list(deps or []),
        provenance="derived",
    )


def _task(key: str, op: str, seq: int) -> PlannedTaskPreview:
    return PlannedTaskPreview(
        task_key=key,
        label=op,
        canonical_task_type="process",
        source_operation_code=op,
        source_task_rule_code=op,
        sequence_index=seq,
        estimated_minutes=None,
        warnings=[PLANNING_MINUTES_WARNING],
    )


def test_wave2_owner_decisions_binding():
    assert WAVE2_OWNER_DECISIONS["DEC-003"] == "A"
    assert WAVE2_OWNER_DECISIONS["DEC-004"] == "A"
    assert WAVE2_OWNER_DECISIONS["DEC-005"] == "E"
    assert WAVE2_OWNER_DECISIONS["DEC-007"] == "B"
    assert WAVE2_OWNER_DECISIONS["DEC-009"] == "A"


def test_dec003_dec004_parent_canonical_aliases_only():
    rules = [
        _rule("side_forming", "side_forming", seq=1),
        _rule("RETURN_PROFILE_MACHINE_FORMING", "RETURN_PROFILE_MACHINE_FORMING", seq=2),
        _rule("return_face_bonding", "return_face_bonding", seq=3),
        _rule("RETURN_PROFILE_FACE_BONDING", "RETURN_PROFILE_FACE_BONDING", seq=4),
        _rule("painting", "painting", seq=5),
        _rule("PAINTING", "PAINTING", seq=6),
    ]
    collapsed = collapse_operational_alias_rules(rules)
    priced = {str(r.priced_operation).lower() for r in collapsed}
    assert priced == {"side_forming", "return_face_bonding", "painting"}
    assert "return_profile_machine_forming" not in priced
    assert "return_profile_face_bonding" not in priced


def test_foil_application_after_bonding_and_assembly_not_side_forming_only():
    vinyl = PROCESS_DEPENDENCY_RULES["vinyl_application"]
    deps = set(vinyl["depends_on_process_ids"])
    assert "return_face_bonding" in deps
    assert "assembly_letters" in deps
    assert "side_forming" not in deps
    assembly_deps = set(PROCESS_DEPENDENCY_RULES["assembly_letters"]["depends_on_process_ids"])
    assert "vinyl_application" not in assembly_deps


def test_finish_aware_foil_dag_converges_after_assembly():
    tasks = [
        _task("t_face", "face_cnc_cut", 1),
        _task("t_side", "side_forming", 2),
        _task("t_bond", "return_face_bonding", 3),
        _task("t_back", "back_cut", 4),
        _task("t_asm", "assembly_letters", 5),
        _task("t_vinyl", "vinyl_application", 6),
        _task("t_qc", "qc_letters", 7),
    ]
    rules = {
        "t_face": _rule("face", "face_cnc_cut", seq=1),
        "t_side": _rule("side", "side_forming", seq=2),
        "t_bond": _rule("bond", "return_face_bonding", deps=["face_cnc_cut", "side_forming"], seq=3),
        "t_back": _rule("back", "back_cut", seq=4),
        "t_asm": _rule(
            "asm",
            "assembly_letters",
            deps=["return_face_bonding", "back_cut"],
            seq=5,
        ),
        "t_vinyl": _rule(
            "vinyl",
            "vinyl_application",
            deps=["return_face_bonding", "assembly_letters"],
            seq=6,
        ),
        "t_qc": _rule("qc", "qc_letters", deps=["assembly_letters", "vinyl_application"], seq=7),
    }
    edges = _build_dependencies(tasks, rules_by_task_key=rules)
    by = {t.task_key: set(t.depends_on_task_keys) for t in tasks}
    assert "t_face" in by["t_bond"] and "t_side" in by["t_bond"]
    assert "t_bond" in by["t_asm"] and "t_back" in by["t_asm"]
    assert "t_vinyl" not in by["t_asm"]
    assert "t_asm" in by["t_vinyl"] and "t_bond" in by["t_vinyl"]
    assert "t_vinyl" in by["t_qc"]
    assert edges
    # acyclic: vinyl after assembly
    assert "t_vinyl" not in by["t_asm"]


def test_registry_change_does_not_mutate_already_stamped_aggregate():
    """Frozen Aggregate ops keep WC; live ORR remap does not rewrite old stamps until re-apply."""
    agg = ProductAggregate(
        template_code="TPL-WAVE2-FIXTURE",
        template_id=99002,
        operations=[
            ProductAggregateOperation(
                operation_code="side_forming",
                label="Side",
                workcenter="WC_LETTER_FORMING",
                workcenter_resolution_status="resolved",
                workcenter_mapping_source="orr_freeze",
                priced=True,
                provenance="derived",
            )
        ],
        task_contract=ProductAggregateTaskContract(
            task_rules=[_rule("side", "side_forming")],
            notes=["wave2_freeze_proof"],
        ),
    )
    before = agg.operations[0].workcenter
    assert before == "WC_LETTER_FORMING"
    remapped = apply_workcenter_resolution_to_aggregate(
        agg,
        [
            {
                "operation_code": "side_forming",
                "allowed_workcenter_codes": ["WC_ASSEMBLY"],
                "product_system_aliases": [],
            }
        ],
    )
    assert remapped.operations[0].workcenter == "WC_ASSEMBLY"
    # Original aggregate instance remains the historical frozen truth.
    assert agg.operations[0].workcenter == "WC_LETTER_FORMING"


@pytest.mark.asyncio
@pytest.mark.enforce_dec009_gate
async def test_wave2_controlled_fixture_preview_persist_audit_no_materialize(db_session):
    oid = _f7a_oid()
    assert oid not in {880811, 973019}
    snap = _f7a_snapshot_json(order_id=oid, quote_snapshot_v2_id=oid)
    await _seed_v2_order_with_snapshot(db_session, order_id=oid, snapshot_v2_json=snap)

    preview = await build_execution_plan_v2_preview(db_session, oid)
    assert preview.no_write is True
    assert preview.execution_tasks_created is False

    priced = {
        str(t.source_operation_code or "").lower()
        for t in preview.planned_tasks
        if t.source_operation_code
    }
    assert "return_profile_face_bonding" not in priced
    assert "return_profile_machine_forming" not in priced
    # parent painting may be present; module PAINTING must not appear as priced op
    assert "PAINTING" not in {
        str(t.source_operation_code or "") for t in preview.planned_tasks
    }

    for task in preview.planned_tasks:
        assert task.estimated_minutes is None
        assert PLANNING_MINUTES_WARNING in (task.warnings or []) or (
            "PLANNING_MINUTES_SOURCE_MISSING" in (task.warnings or [])
        )

    # WC projected from frozen Aggregate (DEC-005)
    by_op = {
        str(t.source_operation_code).lower(): t
        for t in preview.planned_tasks
        if t.source_operation_code
    }
    if "side_forming" in by_op:
        assert by_op["side_forming"].machine_requirement is not None
        assert by_op["side_forming"].machine_requirement.workcenter == "WC_LETTER_FORMING"

    from services.execution_plan_v2_materialization_audit_service import (
        build_execution_plan_v2_materialization_audit_by_order_id,
    )
    from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order

    first = await create_execution_plan_v2_from_order(db_session, oid)
    second = await create_execution_plan_v2_from_order(db_session, oid)
    assert first.execution_plan_id == second.execution_plan_id
    assert second.status in {"already_exists", "persisted"}

    audit = await build_execution_plan_v2_materialization_audit_by_order_id(db_session, oid)
    assert audit.guards.post_materialize_allowed is False
    assert audit.operational_tasks_in_envelope_count == 0
    candidate_ops = {
        str(c.source_operation_code or "").lower()
        for c in audit.materializable_task_candidates
        if c.source_operation_code
    }
    assert "return_profile_face_bonding" not in candidate_ops
    assert "return_profile_machine_forming" not in candidate_ops
