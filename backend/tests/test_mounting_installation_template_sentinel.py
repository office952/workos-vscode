"""Installation-template mounting sentinel readiness."""

from __future__ import annotations

from services.intake_v4_finish_truth_service import mounting_solution_runtime_state
from services.mounting_solution_service import (
    INSTALLATION_TEMPLATE_KIND,
    is_installation_template_solution,
    is_mounting_solution_composition_active,
    is_mounting_template_fields_complete,
    read_mounting_solution,
)
from services.product_definition_composition_contract import freeze_mounting_resolution


def test_read_installation_template_sentinel() -> None:
    setup = {
        "mounting_solution": {
            "kind": INSTALLATION_TEMPLATE_KIND,
            "template_code": None,
            "configuration": {},
        }
    }
    solution = read_mounting_solution(setup)
    assert solution is not None
    assert is_installation_template_solution(solution)
    assert solution.get("template_code") is None


def test_installation_template_ready_when_template_fields_complete() -> None:
    setup = {
        "confirmed": True,
        "mounting_scope": "preparation_only",
        "mounting_template_enabled": True,
        "mounting_template_area_m2": 3.05,
        "mounting_template_material_type": "forex",
        "mounting_solution": {
            "kind": INSTALLATION_TEMPLATE_KIND,
            "template_code": None,
            "configuration": {},
        },
    }
    assert is_mounting_template_fields_complete(setup)
    state = mounting_solution_runtime_state(setup)
    assert state["status"] == "confirmed"
    assert state["blocker_code"] is None
    assert is_mounting_solution_composition_active(setup) is False


def test_installation_template_still_blocks_when_template_incomplete() -> None:
    setup = {
        "confirmed": True,
        "mounting_scope": "preparation_only",
        "mounting_template_enabled": True,
        "mounting_template_area_m2": None,
        "mounting_template_material_type": "forex",
        "mounting_solution": {
            "kind": INSTALLATION_TEMPLATE_KIND,
            "template_code": None,
            "configuration": {},
        },
    }
    state = mounting_solution_runtime_state(setup)
    assert state["blocker_code"] == "MOUNTING_SOLUTION_MISSING"


def test_null_mounting_solution_still_blocks_when_prep_active() -> None:
    setup = {
        "confirmed": True,
        "mounting_scope": "preparation_only",
        "mounting_template_enabled": True,
        "mounting_template_area_m2": 2.0,
        "mounting_template_material_type": "forex",
        "mounting_solution": None,
    }
    state = mounting_solution_runtime_state(setup)
    assert state["blocker_code"] == "MOUNTING_SOLUTION_MISSING"


def test_freeze_mounting_installation_template_has_no_product_system_child() -> None:
    finish = {
        "mounting_scope": "preparation_only",
        "mounting_template_enabled": True,
        "mounting_template_area_m2": 3.0,
        "mounting_template_material_type": "forex",
        "mounting_solution": {
            "kind": INSTALLATION_TEMPLATE_KIND,
            "template_code": None,
            "configuration": {},
        },
    }
    frozen = freeze_mounting_resolution(finish=finish, payload={})
    assert frozen.resolved_solution is not None
    assert frozen.resolved_solution.get("kind") == INSTALLATION_TEMPLATE_KIND
    assert frozen.selected_solution_id is None
