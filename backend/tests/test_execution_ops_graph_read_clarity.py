"""Capacity Batch 17 Track B — ops-graph read-clarity honesty (no invent)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.execution_ops_graph_read_clarity import (
    FIELD_HONESTY_VERSION,
    apply_ops_graph_read_clarity_to_plan_payload,
    build_task_read_clarity,
    enrich_operational_tasks_for_ops_graph,
)

FIXTURE_PLAN = Path(
    r"C:\w\workos-atoms-ui-chrome-handoff\evidence\capacity-batch-16"
    r"\execution_plan_973010_after.json"
)


def _sample_pending_task(**overrides):
    base = {
        "task_id": "node:root_product:TPL:vector_prep",
        "display_name": "Pregatire vector",
        "technical_name": "vector_prep",
        "process_type": "file_preparation",
        "machine_type": "PREPRESS",
        "depends_on_task_ids": [],
        "sequence_index": 1,
        "estimated_time_minutes": None,
        "planning_minutes_source": None,
        "quantity": 1.0,
        "assigned_employee_id": None,
        "operational_status": "pending",
        "source_operation_code": "vector_prep",
        "warnings": ["PLANNING_MINUTES_SOURCE_REQUIRED"],
    }
    base.update(overrides)
    return base


def test_lifecycle_surfaces_operational_status_not_invented_reality():
    clarity = build_task_read_clarity(_sample_pending_task())
    assert clarity["lifecycle"]["value"] == "pending"
    assert clarity["lifecycle"]["display_label"] == "materialized_pending_execution"
    assert clarity["lifecycle"]["source_field"] == "operational_status"
    assert clarity["lifecycle"]["classification"] == "present"


def test_machine_code_null_not_coalesced_from_machine_type():
    clarity = build_task_read_clarity(_sample_pending_task())
    assert clarity["machine_code"]["value"] is None
    assert clarity["machine_code"]["classification"] == "owner_accepted_risk"
    assert clarity["machine_code"]["owner_lock"] == "CAP-012"
    assert clarity["machine_type"]["value"] == "PREPRESS"
    assert clarity["machine_type"]["role"] == "planning_requirement_class"
    assert clarity["workcenter"]["value"] is None
    assert clarity["workcenter"]["classification"] == "owner_accepted_risk"
    assert (
        clarity["display_hints"]["do_not_coalesce_machine_code_from_machine_type"] is True
    )


def test_unit_absent_is_unknown_quantity_present():
    clarity = build_task_read_clarity(_sample_pending_task())
    assert clarity["quantity"]["value"] == 1.0
    assert clarity["quantity"]["classification"] == "present"
    assert clarity["unit"]["value"] is None
    assert clarity["unit"]["classification"] == "unknown"


def test_minutes_null_owner_accepted_not_zero():
    clarity = build_task_read_clarity(_sample_pending_task())
    assert clarity["estimated_time_minutes"]["value"] is None
    assert clarity["estimated_time_minutes"]["classification"] == "owner_accepted_risk"
    assert clarity["estimated_time_minutes"]["owner_lock"] == "CAP-004"


def test_warning_buckets_collapse_accepted_gaps():
    clarity = build_task_read_clarity(_sample_pending_task())
    assert "CAP-004" in clarity["warnings"]["accepted_gap_codes"]
    assert "CAP-012" in clarity["warnings"]["accepted_gap_codes"]
    assert "F7_OD1" in clarity["warnings"]["accepted_gap_codes"]
    assert "PLANNING_MINUTES_SOURCE_REQUIRED" not in clarity["warnings"]["active_warnings"]
    assert "PLANNING_MINUTES_SOURCE_REQUIRED" in clarity["warnings"]["raw_warnings"]


def test_enrichment_preserves_count_and_raw_fields():
    t1 = _sample_pending_task(sequence_index=1)
    t2 = _sample_pending_task(
        task_id="node:root_product:TPL:cnc_face_cut",
        technical_name="cnc_face_cut",
        sequence_index=2,
        depends_on_task_ids=["node:root_product:TPL:vector_prep"],
        machine_type="CNC_ROUTER",
    )
    enriched, summary = enrich_operational_tasks_for_ops_graph([t1, t2])
    assert len(enriched) == 2
    assert summary["counts_guard"]["input_count"] == 2
    assert summary["counts_guard"]["output_count"] == 2
    assert summary["version"] == FIELD_HONESTY_VERSION
    # Raw fields unchanged (no invent workcenter / machine_code).
    assert "machine_code" not in enriched[0] or enriched[0].get("machine_code") is None
    assert enriched[0].get("workcenter") is None
    assert enriched[0]["machine_type"] == "PREPRESS"
    assert enriched[1]["read_clarity"]["depends_on"]["short_codes"] == ["vector_prep"]


def test_sequence_gaps_reported_not_densified():
    tasks = [
        _sample_pending_task(sequence_index=1, task_id="a", technical_name="a"),
        _sample_pending_task(sequence_index=10, task_id="b", technical_name="b"),
        _sample_pending_task(sequence_index=13, task_id="c", technical_name="c"),
        _sample_pending_task(sequence_index=14, task_id="d", technical_name="d"),
    ]
    # Make ids unique
    for i, t in enumerate(tasks):
        t["task_id"] = f"node:t:{t['technical_name']}"
    _enriched, summary = enrich_operational_tasks_for_ops_graph(tasks)
    assert summary["sequence"]["gaps"] == [2, 3, 4, 5, 6, 7, 8, 9, 11, 12]
    assert "no invent" in summary["sequence"]["display_order_basis"]


def test_apply_to_plan_payload_adds_summary():
    payload = {
        "id": 12,
        "order_id": 973010,
        "tasks": [_sample_pending_task()],
        "operational_tasks_count": 1,
    }
    out = apply_ops_graph_read_clarity_to_plan_payload(payload)
    assert out["ops_graph_read_clarity"]["operational_tasks_count"] == 1
    assert "read_clarity" in out["tasks"][0]
    assert out["tasks"][0]["operational_status"] == "pending"


def test_fix_dec009_fixture_snapshot_counts_and_honesty():
    if not FIXTURE_PLAN.is_file():
        pytest.skip("Batch 16 evidence fixture snapshot not available")
    plan = json.loads(FIXTURE_PLAN.read_text(encoding="utf-8-sig"))
    assert plan["id"] == 12
    assert plan["order_id"] == 973010
    assert len(plan["tasks"]) == 12
    enriched, summary = enrich_operational_tasks_for_ops_graph(plan["tasks"])
    assert len(enriched) == 12
    assert summary["sequence"]["gaps"] == [11, 12]
    assert summary["sequence"]["observed_indices"] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14]
    for task, row in zip(plan["tasks"], enriched, strict=True):
        # No invent of machine_code / workcenter / unit / minutes.
        assert row.get("machine_code") == task.get("machine_code")
        assert row.get("workcenter") == task.get("workcenter")
        assert row.get("estimated_time_minutes") == task.get("estimated_time_minutes")
        assert "unit" not in row or row.get("unit") == task.get("unit")
        clarity = row["read_clarity"]
        assert clarity["lifecycle"]["value"] == "pending"
        assert clarity["machine_code"]["classification"] == "owner_accepted_risk"
        assert clarity["workcenter"]["classification"] == "owner_accepted_risk"
        assert clarity["machine_type"]["classification"] == "present"
        assert clarity["unit"]["classification"] == "unknown"
