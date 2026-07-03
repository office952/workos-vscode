"""
Contract tests for the Execution Plan Generation Gate — Phase P1 (unit level).

Source of truth:
  - /workspace/docs/spec/spec__execution_plan_generation_gate.md
  - /workspace/docs/spec/spec__execution_plan_generation_gate_contract_tests.md

Scope (P1 only):
  BLK-01..BLK-11, BLK-20, BLK-21, WRN-01..WRN-03, envelope shape,
  trace_source mandatory, classify_writer_http_status mapping,
  BLK-12..BLK-19 remain warning-only / deferred.

These tests call the pure evaluator directly (no HTTP, no DB). HTTP / writer
amendment tests are covered by the existing test_execution_flow suite and
are deliberately NOT modified here to avoid breaking unrelated scenarios.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

import pytest

from services.execution_plan_gate_service import (
    CANONICAL_TASK_TYPES,
    GATE_SPEC_VERSION,
    GateEvaluation,
    RegistrySnapshot,
    classify_writer_http_status,
    evaluate_gate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@dataclass
class FakeOrderRow:
    id: int
    code: str
    snapshot_version: Optional[int]
    snapshot_line_items: Any


def _registry_live_m1_m2() -> RegistrySnapshot:
    return RegistrySnapshot(
        skills=["CNC_ROUTING", "ARTCAM", "LASER_CUTTING", "PRINT_LARGE_FORMAT"],
        workcenters=["WC_CNC", "WC_LASER", "WC_PRINT", "WC_INSTALLATION_PREP"],
        roles=["OP_CNC_ROUTER", "OP_LASER_CUTTER", "OP_HOTWIRE", "MGR_PRODUCTION"],
        product_system_available=False,
        materials_registry_available=False,
        machines_registry_available=False,
    )


def _good_snapshot() -> dict:
    return {
        "order_id": 1001,
        "product_definition": {
            "product_id": "PROD-TEST-001",
            "product_code": "PROD-TEST-001",
            "quantity": 2,
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
        "cost_result": {"estimated_time_minutes": 120, "total_cost": 100.0},
    }


def _good_order(snapshot: Optional[dict] = None) -> FakeOrderRow:
    snap = snapshot if snapshot is not None else _good_snapshot()
    return FakeOrderRow(
        id=1001,
        code="ORD-TEST-0001",
        snapshot_version=1,
        snapshot_line_items=json.dumps(snap),
    )


def _run(order: FakeOrderRow, plan_exists: bool = False) -> GateEvaluation:
    return evaluate_gate(
        order_row=order,
        registries=_registry_live_m1_m2(),
        plan_already_exists=plan_exists,
    )


def _blocker_codes(ev: GateEvaluation) -> set:
    return {b.get("code") for b in ev.blockers}


def _warning_codes(ev: GateEvaluation) -> set:
    return {w.get("code") for w in ev.warnings}


# ---------------------------------------------------------------------------
# §6 — Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_good_minimal_can_generate_true(self):
        ev = _run(_good_order())
        assert ev.can_generate is True, f"Expected can_generate=True, got blockers={ev.blockers}"
        assert ev.blockers == []

    def test_envelope_has_all_mandatory_fields(self):
        ev = _run(_good_order())
        d = ev.to_dict()
        for key in (
            "order_id",
            "order_code",
            "snapshot_version",
            "evaluated_at",
            "can_generate",
            "blockers",
            "warnings",
            "missing_links",
            "required_next_action",
            "trace_source",
        ):
            assert key in d, f"envelope missing mandatory key: {key}"

    def test_trace_source_always_populated(self):
        ev = _run(_good_order())
        ts = ev.trace_source
        assert ts["gate_spec_version"] == GATE_SPEC_VERSION
        assert ts["order"]["id"] == 1001
        assert ts["order"]["code"] == "ORD-TEST-0001"
        assert ts["order"]["snapshot_version"] == 1
        names = [r["name"] for r in ts["registries_consulted"]]
        assert "skills" in names
        assert "workcenters" in names
        assert "roles" in names
        assert set(ts["registries_unavailable"]) == {
            "product_system",
            "materials",
            "machines",
        }


# ---------------------------------------------------------------------------
# §10.1 structural blockers
# ---------------------------------------------------------------------------


class TestStructuralBlockers:
    def test_blk01_snapshot_null(self):
        order = FakeOrderRow(id=1, code="ORD-X", snapshot_version=1, snapshot_line_items=None)
        ev = _run(order)
        assert ev.can_generate is False
        assert "BLK-01" in _blocker_codes(ev)

    def test_blk01_snapshot_empty_string(self):
        order = FakeOrderRow(id=1, code="ORD-X", snapshot_version=1, snapshot_line_items="")
        ev = _run(order)
        assert "BLK-01" in _blocker_codes(ev)

    def test_blk01_snapshot_not_json(self):
        order = FakeOrderRow(
            id=1, code="ORD-X", snapshot_version=1, snapshot_line_items="not-a-json-object"
        )
        ev = _run(order)
        assert "BLK-01" in _blocker_codes(ev)

    def test_blk01_snapshot_array_not_object(self):
        order = FakeOrderRow(
            id=1, code="ORD-X", snapshot_version=1, snapshot_line_items="[1,2,3]"
        )
        ev = _run(order)
        assert "BLK-01" in _blocker_codes(ev)

    def test_blk02_product_definition_missing(self):
        snap = _good_snapshot()
        snap.pop("product_definition")
        ev = _run(_good_order(snap))
        assert "BLK-02" in _blocker_codes(ev)

    def test_blk03_cost_result_missing(self):
        snap = _good_snapshot()
        snap.pop("cost_result")
        ev = _run(_good_order(snap))
        assert "BLK-03" in _blocker_codes(ev)

    def test_blk04_quantity_missing(self):
        snap = _good_snapshot()
        snap["product_definition"].pop("quantity")
        ev = _run(_good_order(snap))
        assert "BLK-04" in _blocker_codes(ev)

    def test_blk04_quantity_zero(self):
        snap = _good_snapshot()
        snap["product_definition"]["quantity"] = 0
        ev = _run(_good_order(snap))
        assert "BLK-04" in _blocker_codes(ev)

    def test_blk04_quantity_negative(self):
        snap = _good_snapshot()
        snap["product_definition"]["quantity"] = -3
        ev = _run(_good_order(snap))
        assert "BLK-04" in _blocker_codes(ev)

    def test_blk04_quantity_string(self):
        snap = _good_snapshot()
        snap["product_definition"]["quantity"] = "seven"
        ev = _run(_good_order(snap))
        assert "BLK-04" in _blocker_codes(ev)

    def test_blk05_layers_missing(self):
        snap = _good_snapshot()
        snap["product_definition"].pop("layers")
        ev = _run(_good_order(snap))
        assert "BLK-05" in _blocker_codes(ev)

    def test_blk05_layers_empty(self):
        snap = _good_snapshot()
        snap["product_definition"]["layers"] = []
        ev = _run(_good_order(snap))
        assert "BLK-05" in _blocker_codes(ev)

    def test_blk06_all_zero_no_fallback(self):
        snap = _good_snapshot()
        snap["product_definition"]["layers"][0]["processes"][0]["estimated_time_minutes"] = 0
        snap["cost_result"].pop("estimated_time_minutes")
        ev = _run(_good_order(snap))
        assert "BLK-06" in _blocker_codes(ev)

    def test_blk06_zero_but_cost_result_fallback_present_does_not_block(self):
        snap = _good_snapshot()
        snap["product_definition"]["layers"][0]["processes"][0]["estimated_time_minutes"] = 0
        snap["cost_result"]["estimated_time_minutes"] = 240
        ev = _run(_good_order(snap))
        assert "BLK-06" not in _blocker_codes(ev)


# ---------------------------------------------------------------------------
# §10.2 / §10.3 — enum + traceability
# ---------------------------------------------------------------------------


class TestEnumAndTraceability:
    def test_blk07_plan_already_exists(self):
        ev = _run(_good_order(), plan_exists=True)
        assert ev.can_generate is False
        assert "BLK-07" in _blocker_codes(ev)

    def test_blk08_task_type_not_in_enum(self):
        snap = _good_snapshot()
        snap["product_definition"]["layers"][0]["processes"][0]["type"] = "unknown_random_string"
        ev = _run(_good_order(snap))
        assert "BLK-08" in _blocker_codes(ev)

    def test_blk08_task_type_empty(self):
        snap = _good_snapshot()
        snap["product_definition"]["layers"][0]["processes"][0]["type"] = ""
        ev = _run(_good_order(snap))
        assert "BLK-08" in _blocker_codes(ev)

    def test_blk08_all_20_canonical_task_types_accepted(self):
        # Every canonical task_type must pass BLK-08.
        for tt in CANONICAL_TASK_TYPES:
            snap = _good_snapshot()
            snap["product_definition"]["layers"][0]["processes"][0]["type"] = tt
            ev = _run(_good_order(snap))
            assert "BLK-08" not in _blocker_codes(ev), f"{tt} rejected by BLK-08"

    def test_blk09_snapshot_order_id_mismatch(self):
        snap = _good_snapshot()
        snap["order_id"] = 9999  # row.id is 1001
        ev = _run(_good_order(snap))
        assert "BLK-09" in _blocker_codes(ev)

    def test_blk09_snapshot_order_id_numeric_string_is_accepted(self):
        snap = _good_snapshot()
        snap["order_id"] = "1001"
        ev = _run(_good_order(snap))
        assert "BLK-09" not in _blocker_codes(ev)

    def test_blk09_order_row_missing_code(self):
        order = FakeOrderRow(
            id=1, code="", snapshot_version=1, snapshot_line_items=json.dumps(_good_snapshot())
        )
        ev = _run(order)
        assert "BLK-09" in _blocker_codes(ev)

    def test_blk09_order_row_missing_snapshot_version(self):
        order = FakeOrderRow(
            id=1,
            code="ORD-X",
            snapshot_version=None,
            snapshot_line_items=json.dumps(_good_snapshot()),
        )
        ev = _run(order)
        assert "BLK-09" in _blocker_codes(ev)

    def test_blk10_product_ref_missing(self):
        snap = _good_snapshot()
        snap["product_definition"].pop("product_id")
        snap["product_definition"].pop("product_code")
        ev = _run(_good_order(snap))
        assert "BLK-10" in _blocker_codes(ev)

    def test_blk10_product_ref_via_product_code_only_ok(self):
        snap = _good_snapshot()
        snap["product_definition"].pop("product_id")
        ev = _run(_good_order(snap))
        assert "BLK-10" not in _blocker_codes(ev)


# ---------------------------------------------------------------------------
# §11 — Warning-only (deferred) rules
# ---------------------------------------------------------------------------


class TestWarningOnlyDeferred:
    def test_wrn01_productsystem_not_live_warning(self):
        ev = _run(_good_order())
        assert "WRN-01" in _warning_codes(ev)
        # WRN-01 must NOT be promoted to a blocker in P1.
        for bk in ev.blockers:
            assert bk.get("code") != "WRN-01"

    def test_wrn02_materials_registry_not_live_warning(self):
        ev = _run(_good_order())
        assert "WRN-02" in _warning_codes(ev)

    def test_wrn03_machines_registry_not_live_warning(self):
        ev = _run(_good_order())
        assert "WRN-03" in _warning_codes(ev)

    @pytest.mark.parametrize(
        "deferred_code",
        ["BLK-12", "BLK-13", "BLK-14", "BLK-15", "BLK-16", "BLK-17", "BLK-18", "BLK-19"],
    )
    def test_deferred_blockers_never_promoted_in_p1(self, deferred_code):
        ev = _run(_good_order())
        assert deferred_code not in _blocker_codes(ev), (
            f"{deferred_code} MUST remain warning-only in P1 "
            "(spec__execution_plan_generation_gate.md §11.3)"
        )

    def test_missing_links_populated_when_registries_deferred(self):
        ev = _run(_good_order())
        links = {ml["link"] for ml in ev.missing_links}
        # At least the product-system-driven links must be reported.
        assert "task.required_skill_ids" in links
        assert "task.source_operation_id" in links


# ---------------------------------------------------------------------------
# §19 — writer HTTP classification
# ---------------------------------------------------------------------------


class TestWriterHttpClassification:
    def test_happy_path_maps_to_201(self):
        ev = _run(_good_order())
        assert classify_writer_http_status(ev) == 201

    def test_plan_already_exists_maps_to_409(self):
        ev = _run(_good_order(), plan_exists=True)
        assert classify_writer_http_status(ev) == 409

    def test_pure_structural_blocker_maps_to_422(self):
        snap = _good_snapshot()
        snap.pop("cost_result")  # BLK-03 only
        ev = _run(_good_order(snap))
        assert classify_writer_http_status(ev) == 422

    def test_non_structural_blocker_maps_to_412(self):
        snap = _good_snapshot()
        snap["product_definition"]["layers"][0]["processes"][0]["type"] = "not_in_enum"
        ev = _run(_good_order(snap))
        # BLK-08 is non-structural in the classification table.
        assert classify_writer_http_status(ev) == 412


# ---------------------------------------------------------------------------
# §19.4 — Invariants
# ---------------------------------------------------------------------------


class TestInvariants:
    def test_determinism_same_input_same_envelope_modulo_evaluated_at(self):
        order = _good_order()
        ev1 = _run(order).to_dict()
        ev2 = _run(order).to_dict()
        ev1.pop("evaluated_at")
        ev2.pop("evaluated_at")
        assert ev1 == ev2

    def test_can_generate_iff_no_blockers(self):
        # Any fixture.
        snap = _good_snapshot()
        snap["product_definition"]["quantity"] = -1
        ev = _run(_good_order(snap))
        assert ev.can_generate is (len(ev.blockers) == 0)

    def test_required_next_action_non_empty_when_blocked(self):
        snap = _good_snapshot()
        snap.pop("cost_result")
        ev = _run(_good_order(snap))
        assert ev.can_generate is False
        assert ev.required_next_action != ""

    def test_blocker_items_have_mandatory_fields(self):
        snap = _good_snapshot()
        snap["product_definition"]["quantity"] = 0
        ev = _run(_good_order(snap))
        for bk in ev.blockers:
            for key in ("code", "severity", "task_ref", "message", "details"):
                assert key in bk, f"blocker missing '{key}': {bk}"
            assert bk["severity"] == "blocker"

    def test_warning_items_have_mandatory_fields(self):
        ev = _run(_good_order())
        for wr in ev.warnings:
            for key in ("code", "severity", "task_ref", "message", "details"):
                assert key in wr, f"warning missing '{key}': {wr}"
            assert wr["severity"] == "warning"


# ---------------------------------------------------------------------------
# §21.1 — BLK-20 / BLK-21 static invariants (meta)
# ---------------------------------------------------------------------------


class TestStaticInvariants:
    def test_blk20_not_fired_on_current_gate_module(self):
        """The shipped gate module must not import forbidden upstream modules."""
        ev = _run(_good_order())
        codes = _blocker_codes(ev)
        assert "BLK-20" not in codes, (
            "BLK-20 fired — forbidden upstream import detected. "
            f"blockers={ev.blockers}"
        )

    def test_blk21_not_fired_on_current_gate_module(self):
        ev = _run(_good_order())
        codes = _blocker_codes(ev)
        assert "BLK-21" not in codes, (
            "BLK-21 fired — silent fallback token detected. "
            f"blockers={ev.blockers}"
        )