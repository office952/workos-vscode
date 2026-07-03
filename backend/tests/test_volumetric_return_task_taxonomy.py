"""Tests for volumetric return-profile execution task taxonomy."""

from __future__ import annotations

import json

import pytest

from services.volumetric_return_task_taxonomy_service import (
    BONDING_DISPLAY_NAME,
    BONDING_INSTRUCTIONS,
    BONDING_MACHINE_TYPE,
    BONDING_PROCESS_TYPE,
    MODELING_DISPLAY_NAME,
    MODELING_INSTRUCTIONS,
    MODELING_MACHINE_TYPE,
    MODELING_PROCESS_TYPE,
    RETURN_BONDING_PROCESS_ID,
    SIDE_FORMING_PROCESS_ID,
    apply_volumetric_return_taxonomy_to_plan_tasks,
    apply_volumetric_return_taxonomy_to_task,
    find_task_by_process_id,
    is_legacy_wrong_return_bonding_task,
)
from services.order_execution_snapshot_mapper import resolve_canonical_task_type


def test_legacy_wrong_bonding_task_detected():
    task = {
        "task_id": "T-005",
        "process_id": RETURN_BONDING_PROCESS_ID,
        "process_type": "welding",
        "machine_type": "RETURN_PROFILE_FACE_BONDING",
        "display_name": "Lipire cant pe față",
    }
    assert is_legacy_wrong_return_bonding_task(task) is True


def test_modeling_task_taxonomy():
    task = apply_volumetric_return_taxonomy_to_task(
        {
            "task_id": "T-004",
            "process_id": SIDE_FORMING_PROCESS_ID,
            "process_type": "edge_bending",
            "machine_type": "RETURN_PROFILE_MACHINE_FORMING",
        },
        set_owner_instructions=True,
    )
    assert task["display_name"] == MODELING_DISPLAY_NAME
    assert task["process_type"] == MODELING_PROCESS_TYPE
    assert task["machine_type"] == MODELING_MACHINE_TYPE
    assert task["instructions"] == MODELING_INSTRUCTIONS


def test_bonding_task_taxonomy_not_welding():
    task = apply_volumetric_return_taxonomy_to_task(
        {
            "task_id": "T-005",
            "process_id": RETURN_BONDING_PROCESS_ID,
            "process_type": "welding",
            "machine_type": "RETURN_PROFILE_FACE_BONDING",
            "display_name": "Lipire cant pe față",
        },
        set_owner_instructions=True,
    )
    assert task["display_name"] == BONDING_DISPLAY_NAME
    assert task["process_type"] == BONDING_PROCESS_TYPE
    assert task["process_type"] != "welding"
    assert task["machine_type"] == BONDING_MACHINE_TYPE
    assert task["machine_type"] != "RETURN_PROFILE_FACE_BONDING"
    assert task["instructions"] == BONDING_INSTRUCTIONS


def test_plan_tasks_idempotent():
    tasks = [
        {
            "task_id": "T-004",
            "process_id": SIDE_FORMING_PROCESS_ID,
            "process_type": "welding",
            "machine_type": "RETURN_PROFILE_FACE_BONDING",
        },
        {
            "task_id": "T-005",
            "process_id": RETURN_BONDING_PROCESS_ID,
            "process_type": "welding",
            "machine_type": "RETURN_PROFILE_FACE_BONDING",
        },
    ]
    updated, action = apply_volumetric_return_taxonomy_to_plan_tasks(tasks, set_owner_instructions=True)
    assert action == "updated"
    again, action2 = apply_volumetric_return_taxonomy_to_plan_tasks(updated, set_owner_instructions=True)
    assert action2 == "unchanged"
    modeling = find_task_by_process_id(again, SIDE_FORMING_PROCESS_ID)
    bonding = find_task_by_process_id(again, RETURN_BONDING_PROCESS_ID)
    assert modeling is not None
    assert bonding is not None
    assert modeling["machine_type"] == MODELING_MACHINE_TYPE
    assert bonding["machine_type"] == BONDING_MACHINE_TYPE


def test_return_face_bonding_maps_to_volumetric_assembly_canonical():
    assert (
        resolve_canonical_task_type(
            process_id=RETURN_BONDING_PROCESS_ID,
            legacy_type="return_profile_face_bonding",
        )
        == BONDING_PROCESS_TYPE
    )


def test_fixture_generated_plan_has_no_wrong_bonding_combo():
    tasks, _ = apply_volumetric_return_taxonomy_to_plan_tasks(
        [
            {
                "task_id": "T-004",
                "process_id": SIDE_FORMING_PROCESS_ID,
                "process_type": "welding",
                "machine_type": "RETURN_PROFILE_FACE_BONDING",
                "name": "Lipire cant pe față",
            }
        ],
        set_owner_instructions=True,
    )
    wrong = [
        t
        for t in tasks
        if isinstance(t, dict)
        and t.get("display_name") == "Lipire cant pe față"
        and t.get("process_type") == "welding"
        and t.get("machine_type") == "RETURN_PROFILE_FACE_BONDING"
    ]
    assert wrong == []
    modeling = find_task_by_process_id(tasks, SIDE_FORMING_PROCESS_ID)
    assert modeling is not None
    assert modeling["display_name"] == MODELING_DISPLAY_NAME
