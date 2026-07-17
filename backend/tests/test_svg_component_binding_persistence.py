"""FinishSetup durability + SVG component bindings."""

from __future__ import annotations

from schemas.intake_v4 import IntakeV4FinishSetup
from services.svg_component_binding_persistence import (
    build_svg_component_instances,
    sync_support_selection_from_bindings,
    validate_bindings_for_new_selection,
)


def test_finish_setup_preserves_svg_support_selection_and_bindings() -> None:
    raw = {
        "svg_support_selection": {
            "schema": "svg_support_selection_v1",
            "status": "confirmed",
            "role": "ALUCOBOND_CASED_PANEL",
            "contour_id": "cc_60db6024",
            "geometry_hash": "60db6024",
            "svg_source_hash": "abc",
        },
        "svg_component_bindings": [
            {
                "binding_id": "bind_support_cc_60db6024",
                "geometry_role": "SUPPORT_CONTOUR",
                "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "selection_mode": "CLOSED_CONTOUR",
                "selected_geometry": {
                    "layer_ids": [],
                    "group_ids": [],
                    "element_ids": ["cc_60db6024"],
                    "geometry_hashes": ["60db6024"],
                    "source_svg_hash": "abc",
                },
                "configuration": {
                    "fold_count": 2,
                    "l1_mm": 60,
                    "l2_mm": 25,
                    "finished_depth_mm": 60,
                    "service_corner": "TOP_RIGHT",
                    "internal_frame_enabled": True,
                },
                "status": "CONFIRMED",
            }
        ],
    }
    model = IntakeV4FinishSetup.model_validate(raw)
    dumped = model.model_dump(mode="json")
    assert dumped["svg_support_selection"]["contour_id"] == "cc_60db6024"
    assert dumped["svg_component_bindings"][0]["component_template_code"] == (
        "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
    )


def test_stale_bond_blocked_for_new_selection() -> None:
    blockers = validate_bindings_for_new_selection(
        [
            {
                "component_template_code": "TPL-BOND-CASETAT",
                "geometry_role": "SUPPORT_CONTOUR",
                "status": "CONFIRMED",
            }
        ]
    )
    assert any("TPL-BOND-CASETAT" in b for b in blockers)


def test_sync_and_instances_from_bindings() -> None:
    finish = {
        "svg_component_bindings": [
            {
                "binding_id": "b1",
                "geometry_role": "SUPPORT_CONTOUR",
                "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "selection_mode": "CLOSED_CONTOUR",
                "selected_geometry": {
                    "element_ids": ["cc_1"],
                    "geometry_hashes": ["h1"],
                    "source_svg_hash": "s1",
                    "layer_ids": [],
                    "group_ids": [],
                },
                "configuration": {
                    "fold_count": 2,
                    "l1_mm": 60,
                    "l2_mm": 25,
                    "finished_depth_mm": 60,
                    "service_corner": "TOP_RIGHT",
                    "internal_frame_enabled": True,
                },
                "status": "CONFIRMED",
            }
        ]
    }
    synced = sync_support_selection_from_bindings(finish)
    assert synced["svg_support_selection"]["status"] == "confirmed"
    assert synced["svg_support_selection"]["role"] == "ALUCOBOND_CASED_PANEL"
    instances = build_svg_component_instances(synced)
    assert len(instances) == 1
    assert instances[0]["component_template_code"] == "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
    assert instances[0]["geometry_role"] == "SUPPORT_CONTOUR"
