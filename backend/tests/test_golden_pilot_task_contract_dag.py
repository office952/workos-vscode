"""Golden Pilot — task contract alias collapse + finish-aware DAG."""

from __future__ import annotations

from schemas.execution_plan_v2 import PlannedTaskPreview
from schemas.product_aggregate import ProductAggregateTaskRule
from services.execution_plan_v2_preview_service import (
    _build_dependencies,
    _finish_allows_priced_op,
)
from services.product_process_aggregate_bridge import _collapse_operational_alias_rules


def _rule(name: str, priced: str, deps: list[str] | None = None, seq: int = 1):
    return ProductAggregateTaskRule(
        task_name=name,
        task_type="process",
        priced_operation=priced,
        sequence=seq,
        depends_on_process_ids=list(deps or []),
        provenance="derived",
    )


def test_collapse_return_and_painting_aliases():
    rules = [
        _rule("return_face_bonding", "return_face_bonding", seq=5),
        _rule("RETURN_PROFILE_FACE_BONDING", "RETURN_PROFILE_FACE_BONDING", seq=6),
        _rule("painting", "painting", seq=7),
        _rule("PAINTING", "PAINTING", seq=8),
        _rule("side_forming", "side_forming", seq=4),
    ]
    collapsed = _collapse_operational_alias_rules(rules)
    priced = {str(r.priced_operation).lower() for r in collapsed}
    assert "return_face_bonding" in priced
    assert "painting" in priced
    assert "side_forming" in priced
    assert "return_profile_face_bonding" not in priced
    assert "painting" in priced
    assert len(collapsed) == 3


def test_promote_alias_when_parent_absent():
    rules = [_rule("PAINTING", "PAINTING", seq=1)]
    collapsed = _collapse_operational_alias_rules(rules)
    assert len(collapsed) == 1
    assert collapsed[0].priced_operation == "painting"


def test_finish_paint_vs_vinyl():
    assert _finish_allows_priced_op("painting", {}) is True  # no signal → no invent
    assert _finish_allows_priced_op("painting", {"paint_ral_code": "ral9016"}) is True
    assert _finish_allows_priced_op("vinyl_application", {"paint_ral_code": "ral9016"}) is False
    assert (
        _finish_allows_priced_op("vinyl_application", {"face_finish_type": "oracal_651"})
        is True
    )
    assert _finish_allows_priced_op("painting", {"face_finish_type": "oracal_651"}) is False
    assert _finish_allows_priced_op("painting", {"face_finish_type": "none"}) is False
    assert _finish_allows_priced_op("face_cnc_cut", {"face_finish_type": "none"}) is True


def test_dag_uses_process_deps_not_linear_chain():
    tasks = [
        PlannedTaskPreview(
            task_key="t_face",
            label="Face",
            canonical_task_type="cnc_routing",
            source_operation_code="face_cnc_cut",
            source_task_rule_code="cnc_face_cut",
            sequence_index=2,
        ),
        PlannedTaskPreview(
            task_key="t_side",
            label="Side",
            canonical_task_type="edge_bending",
            source_operation_code="side_forming",
            source_task_rule_code="return_profile_forming",
            sequence_index=4,
        ),
        PlannedTaskPreview(
            task_key="t_bond",
            label="Bond",
            canonical_task_type="volumetric_letter_assembly",
            source_operation_code="return_face_bonding",
            source_task_rule_code="return_face_bonding",
            sequence_index=5,
        ),
        PlannedTaskPreview(
            task_key="t_pack",
            label="Pack",
            canonical_task_type="packaging",
            source_operation_code="packaging_letters",
            source_task_rule_code="packaging",
            sequence_index=14,
        ),
    ]
    rules = {
        "t_face": _rule("cnc_face_cut", "face_cnc_cut", seq=2),
        "t_side": _rule("return_profile_forming", "side_forming", seq=4),
        "t_bond": _rule(
            "return_face_bonding",
            "return_face_bonding",
            deps=["face_cnc_cut", "side_forming"],
            seq=5,
        ),
        "t_pack": _rule("packaging", "packaging_letters", seq=14),
    }
    deps = _build_dependencies(tasks, rules_by_task_key=rules)
    bond = next(t for t in tasks if t.task_key == "t_bond")
    assert set(bond.depends_on_task_keys) == {"t_face", "t_side"}
    # Face and side must not be forced into a linear chain against each other.
    face = next(t for t in tasks if t.task_key == "t_face")
    side = next(t for t in tasks if t.task_key == "t_side")
    assert face.task_key not in side.depends_on_task_keys
    assert side.task_key not in face.depends_on_task_keys
    assert all(d.depends_on_task_key != d.task_key for d in deps)


def test_dag_no_universal_linear_fallback_when_deps_absent():
    """DEC-007 — missing process edges must not invent task[n]→task[n-1]."""
    tasks = [
        PlannedTaskPreview(
            task_key="t_a",
            label="A",
            canonical_task_type="cnc_routing",
            source_operation_code="face_cnc_cut",
            source_task_rule_code="a",
            sequence_index=1,
        ),
        PlannedTaskPreview(
            task_key="t_b",
            label="B",
            canonical_task_type="edge_bending",
            source_operation_code="side_forming",
            source_task_rule_code="b",
            sequence_index=2,
        ),
    ]
    rules = {
        "t_a": _rule("a", "face_cnc_cut", deps=[], seq=1),
        "t_b": _rule("b", "side_forming", deps=[], seq=2),
    }
    deps = _build_dependencies(tasks, rules_by_task_key=rules)
    assert deps == []
    assert all(not t.depends_on_task_keys for t in tasks)
    assert all("DAG_PROCESS_DEPENDENCIES_UNRESOLVED" in (t.warnings or []) for t in tasks)


def test_cycle_detection_clears_edges():
    tasks = [
        PlannedTaskPreview(
            task_key="a",
            label="A",
            canonical_task_type="cnc_routing",
            source_operation_code="face_cnc_cut",
            source_task_rule_code="a",
            sequence_index=1,
        ),
        PlannedTaskPreview(
            task_key="b",
            label="B",
            canonical_task_type="edge_bending",
            source_operation_code="side_forming",
            source_task_rule_code="b",
            sequence_index=2,
        ),
    ]
    rules = {
        "a": _rule("a", "face_cnc_cut", deps=["side_forming"], seq=1),
        "b": _rule("b", "side_forming", deps=["face_cnc_cut"], seq=2),
    }
    deps = _build_dependencies(tasks, rules_by_task_key=rules)
    assert deps == []
    assert all(not t.depends_on_task_keys for t in tasks)


def test_deterministic_dependency_order():
    tasks = [
        PlannedTaskPreview(
            task_key="t_bond",
            label="Bond",
            canonical_task_type="volumetric_letter_assembly",
            source_operation_code="return_face_bonding",
            source_task_rule_code="return_face_bonding",
            sequence_index=5,
        ),
        PlannedTaskPreview(
            task_key="t_face",
            label="Face",
            canonical_task_type="cnc_routing",
            source_operation_code="face_cnc_cut",
            source_task_rule_code="cnc_face_cut",
            sequence_index=2,
        ),
        PlannedTaskPreview(
            task_key="t_side",
            label="Side",
            canonical_task_type="edge_bending",
            source_operation_code="side_forming",
            source_task_rule_code="side",
            sequence_index=4,
        ),
    ]
    rules = {
        "t_bond": _rule(
            "return_face_bonding",
            "return_face_bonding",
            deps=["side_forming", "face_cnc_cut"],
            seq=5,
        ),
        "t_face": _rule("cnc_face_cut", "face_cnc_cut", seq=2),
        "t_side": _rule("side", "side_forming", seq=4),
    }
    a = _build_dependencies(tasks, rules_by_task_key=rules)
    b = _build_dependencies(tasks, rules_by_task_key=rules)
    bond = next(t for t in tasks if t.task_key == "t_bond")
    assert bond.depends_on_task_keys == sorted(bond.depends_on_task_keys)
    assert [(d.task_key, d.depends_on_task_key) for d in a] == [
        (d.task_key, d.depends_on_task_key) for d in b
    ]
