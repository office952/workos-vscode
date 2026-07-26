"""Segmented ACM/ACP background contract — PD/Aggregate projection + joint rules."""

from __future__ import annotations

from data.product_system.acm_segmented_background_v1 import (
    CONSTRUCTION_ACRYLIC_INSERT,
    CONSTRUCTION_APPLIED_VOLUMETRIC,
    CONSTRUCTION_CUTOUT,
    CROSSING_APPLIED_VOLUMETRIC_JOINT,
    MOUNT_TWO_STAGE_JOINT,
    MSG_APPLIED_CROSSING,
    MSG_CUTOUT_CROSSING_BLOCKER,
    MSG_DUPLICATE_PANEL_ID,
    MSG_INSERT_CROSSING_BLOCKER,
    MSG_INVALID_PANEL_REF,
    MSG_SEGMENTATION_PROPOSAL,
    SCHEMA,
    STATUS_CONFIRMED,
    STATUS_INACTIVE,
    STATUS_PROPOSED,
    STATUS_SINGLE_PANEL,
    operator_message,
)
from data.product_system.svg_component_binding_contract import (
    ACM_BOXED_SUPPORT,
    CARDINALITY_MAX_ONE,
    LETTERS_PRODUCT,
)
from services.acm_segmented_background_service import (
    apply_segmented_panel_context_to_applied_interface,
    empty_single_panel_assembly,
    normalize_segmented_background,
    project_segmented_background_for_aggregate,
    project_segmented_background_for_product_definition,
    propose_segmented_assembly,
    validate_segmented_background,
)
from services.acp_local_face_module_service import empty_applied_interface
from services.product_definition_builder_service import _build_canonical_values
from services.svg_component_binding_service import get_svg_bindable_components


def _pd(finish: dict) -> dict:
    return _build_canonical_values([], {"finish_setup": finish})


def _two_panel_confirmed(**extra) -> dict:
    base = {
        "schema": SCHEMA,
        "status": STATUS_CONFIRMED,
        "operator_confirmed": True,
        "assembly_id": "asm_test_two",
        "graphic_continuity": True,
        "panels": [
            {
                "panel_id": "panel_left",
                "order": 1,
                "width_mm": 1000,
                "height_mm": 1000,
                "position": {"x_mm": 0, "y_mm": 0},
                "contour_element_id": "c1",
            },
            {
                "panel_id": "panel_right",
                "order": 2,
                "width_mm": 1000,
                "height_mm": 1000,
                "position": {"x_mm": 1000, "y_mm": 0},
                "contour_element_id": "c2",
            },
        ],
        "joints": [
            {
                "joint_id": "joint_left_right",
                "left_panel_id": "panel_left",
                "right_panel_id": "panel_right",
                "orientation": "VERTICAL",
            }
        ],
        "assembly_dimensions": {"width_mm": 2000, "height_mm": 1000},
        "element_bindings": [],
    }
    base.update(extra)
    return normalize_segmented_background(base)


def test_support_contour_remains_max_one_envelope():
    acm = next(
        c
        for c in get_svg_bindable_components(LETTERS_PRODUCT)
        if c["component_template_code"] == ACM_BOXED_SUPPORT
    )
    assert acm["cardinality"] == CARDINALITY_MAX_ONE
    req = acm["svg_binding"]["geometry_requirements"]
    assert req["support_contour_cardinality"] == CARDINALITY_MAX_ONE
    assert req["segmented_background_nested_panels"] is True
    assert "segmented_background_assembly" in acm["capabilities"]


def test_single_panel_unchanged_empty_finish():
    values = _pd({})
    assert "segmented_background" not in values
    assert "segmented_background_aggregate_projection" not in values
    assert "segmented_background_proposal" not in values


def test_single_panel_explicit_assembly_no_multi_projection():
    # SINGLE_PANEL mode stays compatible; only CONFIRMED multi-panel projects assembly truth.
    finish = {"segmented_background": empty_single_panel_assembly(width_mm=1000, height_mm=800)}
    values = _pd(finish)
    assert "segmented_background" not in values
    assert values.get("segmented_background_proposal") is None


def test_proposed_assembly_zero_downstream_leakage():
    proposal = propose_segmented_assembly(
        nearby_supports=[
            {"contour_element_id": "a", "width_mm": 1000, "height_mm": 1000},
            {"contour_element_id": "b", "width_mm": 1000, "height_mm": 1000},
        ]
    )
    assert proposal["status"] == STATUS_PROPOSED
    assert proposal["operator_confirmed"] is False
    assert proposal["detection"]["authority"] == "PROPOSAL_ONLY"
    assert MSG_SEGMENTATION_PROPOSAL in (proposal["detection"]["message_code"] or "")

    assert project_segmented_background_for_product_definition(proposal) is None
    assert project_segmented_background_for_aggregate(proposal) is None

    values = _pd({"segmented_background": proposal})
    assert "segmented_background" not in values
    assert "segmented_background_aggregate_projection" not in values
    prop = values.get("segmented_background_proposal")
    assert prop is not None
    assert prop["downstream_effects"] is False
    assert prop["materials"] == []
    assert prop["processes"] == []
    assert prop["task_rules"] == []


def test_inactive_segmented_zero_effects():
    raw = _two_panel_confirmed()
    raw["status"] = STATUS_INACTIVE
    raw["operator_confirmed"] = False
    normalized = normalize_segmented_background(raw)
    assert project_segmented_background_for_product_definition(normalized) is None
    assert project_segmented_background_for_aggregate(normalized) is None
    values = _pd({"segmented_background": normalized})
    assert "segmented_background" not in values
    assert values["segmented_background_proposal"]["status"] == STATUS_INACTIVE


def test_confirmed_two_panel_stable_ids_order_dims():
    cfg = _two_panel_confirmed()
    pd = project_segmented_background_for_product_definition(cfg)
    assert pd is not None
    assert pd["assembly_id"] == "asm_test_two"
    assert [p["panel_id"] for p in pd["panels"]] == ["panel_left", "panel_right"]
    assert [p["order"] for p in pd["panels"]] == [1, 2]
    assert pd["assembly_dimensions"]["width_mm"] == 2000
    assert pd["panels"][0]["width_mm"] == 1000

    values = _pd({"segmented_background": cfg})
    assert values["segmented_background"]["assembly_id"] == "asm_test_two"
    agg = values["segmented_background_aggregate_projection"]
    assert agg["kind"] == "acm_segmented_background"
    assert agg["materials"] == []
    assert agg["task_rules"] == []
    assert agg["execution_effects"] == []
    assert "panel_alignment_required" in agg["future_task_intent"]


def test_graphic_distributed_no_blocker():
    cfg = _two_panel_confirmed(
        element_bindings=[
            {
                "binding_id": "eb_a",
                "element_ref": "letter_A",
                "construction_type": CONSTRUCTION_APPLIED_VOLUMETRIC,
                "primary_panel_id": "panel_left",
                "crosses_joint": False,
            },
            {
                "binding_id": "eb_b",
                "element_ref": "letter_B",
                "construction_type": CONSTRUCTION_APPLIED_VOLUMETRIC,
                "primary_panel_id": "panel_right",
                "crosses_joint": False,
            },
        ]
    )
    v = validate_segmented_background(cfg)
    assert v["blockers"] == []
    codes = {i["code"] for i in v["infos"]}
    assert "GRAPHIC_DISTRIBUTED" in codes


def test_applied_letter_on_single_panel_normal():
    cfg = _two_panel_confirmed(
        element_bindings=[
            {
                "binding_id": "eb_p1",
                "element_ref": "letter_P",
                "construction_type": CONSTRUCTION_APPLIED_VOLUMETRIC,
                "primary_panel_id": "panel_left",
                "crosses_joint": False,
            }
        ]
    )
    b = cfg["element_bindings"][0]
    assert b["crosses_joint"] is False
    assert b["mount_strategy"] == "STANDARD"
    assert b["does_not_absorb_letter_ownership"] is True
    assert validate_segmented_background(cfg)["blockers"] == []


def test_applied_letter_crossing_two_stage():
    cfg = _two_panel_confirmed(
        element_bindings=[
            {
                "binding_id": "eb_cross",
                "element_ref": "letter_over_joint",
                "construction_type": CONSTRUCTION_APPLIED_VOLUMETRIC,
                "primary_panel_id": "panel_left",
                "secondary_panel_id": "panel_right",
                "crosses_joint": True,
                "joint_id": "joint_left_right",
                "applied_component_template_code": "TPL-VOLUMETRIC-FACE_v1",
            }
        ]
    )
    b = cfg["element_bindings"][0]
    assert b["crossing_classification"] == CROSSING_APPLIED_VOLUMETRIC_JOINT
    assert b["mount_strategy"] == MOUNT_TWO_STAGE_JOINT
    assert b["panel_alignment_dependency"] is True
    assert b["primary_panel_id"] == "panel_left"
    assert b["secondary_panel_id"] == "panel_right"
    v = validate_segmented_background(cfg)
    assert v["blockers"] == []
    assert any(i["code"] == MSG_APPLIED_CROSSING for i in v["infos"])
    assert "imbinare" in operator_message(MSG_APPLIED_CROSSING).lower() or "imbinare" in operator_message(
        MSG_APPLIED_CROSSING
    )

    agg = project_segmented_background_for_aggregate(cfg)
    assert agg is not None
    assert len(agg["allowed_applied_crossings"]) == 1
    assert "two_stage_applied_letter_mounting" in agg["future_task_intent"]

    iface = empty_applied_interface("bind_x", "TPL-VOLUMETRIC-FACE_v1")
    merged = apply_segmented_panel_context_to_applied_interface(iface, element_binding=b)
    assert merged["mount_strategy"] == MOUNT_TWO_STAGE_JOINT
    assert merged["does_not_absorb_letter_ownership"] is True


def test_cutout_crossing_blocker():
    cfg = _two_panel_confirmed(
        element_bindings=[
            {
                "binding_id": "eb_cut",
                "element_ref": "cut_shape",
                "construction_type": CONSTRUCTION_CUTOUT,
                "primary_panel_id": "panel_left",
                "secondary_panel_id": "panel_right",
                "crosses_joint": True,
            }
        ]
    )
    v = validate_segmented_background(cfg)
    assert any(b["code"] == MSG_CUTOUT_CROSSING_BLOCKER for b in v["blockers"])
    agg = project_segmented_background_for_aggregate(cfg)
    assert agg is not None
    assert agg["blockers"]
    assert "cutout_or_insert_crossing_blocked" in agg["future_task_intent"]


def test_acrylic_insert_crossing_blocker():
    cfg = _two_panel_confirmed(
        element_bindings=[
            {
                "binding_id": "eb_ins",
                "element_ref": "insert_10",
                "construction_type": CONSTRUCTION_ACRYLIC_INSERT,
                "primary_panel_id": "panel_left",
                "secondary_panel_id": "panel_right",
                "crosses_joint": True,
            }
        ]
    )
    v = validate_segmented_background(cfg)
    assert any(b["code"] == MSG_INSERT_CROSSING_BLOCKER for b in v["blockers"])


def test_invalid_panel_reference():
    cfg = _two_panel_confirmed(
        element_bindings=[
            {
                "binding_id": "eb_bad",
                "element_ref": "x",
                "construction_type": CONSTRUCTION_APPLIED_VOLUMETRIC,
                "primary_panel_id": "panel_missing",
                "crosses_joint": False,
            }
        ]
    )
    v = validate_segmented_background(cfg)
    assert any(b["code"] == MSG_INVALID_PANEL_REF for b in v["blockers"])


def test_duplicate_panel_ids_rejected():
    cfg = normalize_segmented_background(
        {
            "status": STATUS_CONFIRMED,
            "operator_confirmed": True,
            "panels": [
                {"panel_id": "panel_dup", "order": 1, "width_mm": 500, "height_mm": 500},
                {"panel_id": "panel_dup", "order": 2, "width_mm": 500, "height_mm": 500},
            ],
            "element_bindings": [],
        }
    )
    v = validate_segmented_background(cfg)
    assert any(b["code"] == MSG_DUPLICATE_PANEL_ID for b in v["blockers"])


def test_crossing_on_single_panel_normalized():
    cfg = normalize_segmented_background(
        {
            "status": STATUS_SINGLE_PANEL,
            "panels": [{"panel_id": "panel_1", "order": 1, "width_mm": 1000, "height_mm": 1000}],
            "element_bindings": [
                {
                    "binding_id": "eb_bad_cross",
                    "construction_type": CONSTRUCTION_APPLIED_VOLUMETRIC,
                    "primary_panel_id": "panel_1",
                    "secondary_panel_id": "panel_2",
                    "crosses_joint": True,
                }
            ],
        }
    )
    assert cfg is not None
    b = cfg["element_bindings"][0]
    assert b["crosses_joint"] is False
    assert b["secondary_panel_id"] is None
    assert b["mount_strategy"] == "STANDARD"


def test_face_treatment_composition_still_valid_with_segmented():
    from data.product_system.acp_face_treatment_registry_v1 import FACE_TREATMENT_ROUTED_BACKLIT
    from services.svg_component_binding_persistence import persist_normalized_bindings_on_finish

    finish = persist_normalized_bindings_on_finish(
        {
            "svg_component_bindings": [
                {
                    "binding_id": "bind_support",
                    "geometry_role": "SUPPORT_CONTOUR",
                    "component_template_code": ACM_BOXED_SUPPORT,
                    "selection_mode": "CLOSED_CONTOUR",
                    "selected_geometry": {
                        "layer_ids": [],
                        "group_ids": [],
                        "element_ids": ["env"],
                        "geometry_hashes": [],
                        "source_svg_hash": "h",
                    },
                    "configuration": {},
                    "status": "CONFIRMED",
                    "face_treatment_code": "NOT_APPLICABLE",
                },
                {
                    "binding_id": "bind_cut",
                    "geometry_role": "CUTOUT_TEXT",
                    "component_template_code": ACM_BOXED_SUPPORT,
                    "selection_mode": "LAYER_OR_GROUP",
                    "selected_geometry": {
                        "layer_ids": ["C1"],
                        "group_ids": [],
                        "element_ids": [],
                        "geometry_hashes": [],
                        "source_svg_hash": "h",
                    },
                    "configuration": {},
                    "status": "CONFIRMED",
                    "face_treatment_code": FACE_TREATMENT_ROUTED_BACKLIT,
                },
            ],
            "segmented_background": _two_panel_confirmed(),
        }
    )
    values = _pd(finish)
    assert values.get("face_treatment_instances")
    assert values.get("segmented_background")
    assert values.get("acp_local_face_module_instances")


def test_no_duplicate_letter_template_ownership():
    cfg = _two_panel_confirmed(
        element_bindings=[
            {
                "binding_id": "eb_l",
                "construction_type": CONSTRUCTION_APPLIED_VOLUMETRIC,
                "primary_panel_id": "panel_left",
                "secondary_panel_id": "panel_right",
                "crosses_joint": True,
                "applied_component_template_code": "TPL-VOLUMETRIC-FACE_v1",
            }
        ]
    )
    b = cfg["element_bindings"][0]
    assert b["does_not_absorb_letter_ownership"] is True
    assert b["applied_component_template_code"] == "TPL-VOLUMETRIC-FACE_v1"
    # Shell host remains ACM — letter template only referenced
    assert cfg["host_component_template_code"] == ACM_BOXED_SUPPORT
