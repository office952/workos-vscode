"""Ops-graph frozen technical materials — read-only projection honesty."""

from __future__ import annotations

import copy
import json

from services.ops_graph_frozen_technical_materials import (
    SEMANTIC_NOTE_RO,
    SEMANTIC_TITLE_RO,
    attach_frozen_technical_materials_to_plan_payload,
    project_frozen_technical_materials,
)


def _snapshot_with_materials(materials: list[dict]) -> str:
    return json.dumps(
        {
            "snapshot_code": "QSN-TEST",
            "product_aggregate_snapshot": {"materials": materials},
            "commercial_price_proposal_snapshot": {
                "commercial_total": 999.0,
                "currency": "EUR",
            },
            "estimated_internal_cost_snapshot": {
                "estimated_material_cost": 50.0,
            },
        }
    )


def test_projects_all_entries_preserving_order_and_duplicates():
    materials = [
        {
            "material_code": "MAT-A",
            "label": "Alpha",
            "unit": "mp",
            "quantity": None,
            "provenance": "parent",
            "component_ref": "comp_face",
            "source_template_code": "TPL-X",
        },
        {
            "material_code": "MAT-A",
            "label": "Alpha module",
            "unit": "mp",
            "quantity": None,
            "provenance": "linked_module",
            "component_ref": "comp_lateral",
            "source_template_code": "TPL-MOD",
        },
        {
            "material_code": "MAT-B-30MM",
            "label": "Variant 30",
            "unit": "ml",
            "quantity": None,
            "provenance": "linked_module",
            "component_ref": "comp_lateral",
        },
        {
            "material_code": "MAT-B-60MM",
            "label": "Variant 60",
            "unit": "ml",
            "quantity": None,
            "provenance": "linked_module",
            "component_ref": "comp_lateral",
        },
    ]
    out = project_frozen_technical_materials(_snapshot_with_materials(materials))
    assert out["status"] == "present"
    assert out["title"] == SEMANTIC_TITLE_RO
    assert out["semantic_note"] == SEMANTIC_NOTE_RO
    assert out["entry_count"] == 4
    assert [e["material_code"] for e in out["entries"]] == [
        "MAT-A",
        "MAT-A",
        "MAT-B-30MM",
        "MAT-B-60MM",
    ]
    assert out["entries"][0]["provenance"] == "parent"
    assert out["entries"][1]["provenance"] == "linked_module"
    assert all(e["quantity"] is None for e in out["entries"])
    assert "duplicate_material_codes_preserved:MAT-A" in out["warnings"]


def test_null_quantity_never_becomes_zero():
    out = project_frozen_technical_materials(
        _snapshot_with_materials(
            [{"material_code": "MAT-X", "label": "X", "unit": "buc", "quantity": None}]
        )
    )
    assert out["entries"][0]["quantity"] is None
    assert out["entries"][0]["quantity"] != 0


def test_preserves_numeric_quantity_when_present():
    out = project_frozen_technical_materials(
        _snapshot_with_materials(
            [{"material_code": "MAT-X", "label": "X", "unit": "buc", "quantity": 3}]
        )
    )
    assert out["entries"][0]["quantity"] == 3


def test_does_not_mutate_source_snapshot_json():
    raw = _snapshot_with_materials(
        [{"material_code": "MAT-X", "label": "X", "unit": "mp", "quantity": None}]
    )
    before = copy.deepcopy(json.loads(raw))
    project_frozen_technical_materials(raw)
    assert json.loads(raw) == before


def test_strips_pricing_fields_from_entries():
    out = project_frozen_technical_materials(
        _snapshot_with_materials(
            [
                {
                    "material_code": "MAT-X",
                    "label": "X",
                    "unit": "mp",
                    "quantity": None,
                    "unit_cost": 12.5,
                    "price": 99,
                    "commercial_total": 1,
                }
            ]
        )
    )
    entry = out["entries"][0]
    assert "unit_cost" not in entry
    assert "price" not in entry
    assert "commercial_total" not in entry
    blob = json.dumps(out)
    assert "unit_cost" not in blob
    assert "commercial_total" not in blob
    assert "estimated_material_cost" not in blob


def test_snapshot_missing_and_empty_states():
    missing = project_frozen_technical_materials(None)
    assert missing["status"] == "snapshot_missing"
    assert missing["entry_count"] == 0
    assert missing["entries"] == []

    empty = project_frozen_technical_materials(
        json.dumps({"product_aggregate_snapshot": {"materials": []}})
    )
    assert empty["status"] == "materials_empty"
    assert empty["entry_count"] == 0

    absent = project_frozen_technical_materials(
        json.dumps({"product_aggregate_snapshot": {}})
    )
    assert absent["status"] == "materials_absent"


def test_attach_to_plan_payload_does_not_touch_tasks():
    tasks = [{"task_id": "t1", "material_inputs": []}]
    payload = {"id": 1, "order_id": 9, "tasks": tasks}
    out = attach_frozen_technical_materials_to_plan_payload(
        payload,
        _snapshot_with_materials(
            [{"material_code": "MAT-X", "label": "X", "unit": "mp", "quantity": None}]
        ),
    )
    assert out["tasks"] is tasks
    assert out["tasks"][0]["material_inputs"] == []
    assert out["frozen_technical_materials"]["entry_count"] == 1
