"""Segmented ACM/ACP electrical connection management contract tests."""

from __future__ import annotations

from services.acm_segmented_background_service import (
    normalize_segmented_background,
    persist_segmented_background_on_finish,
    project_segmented_background_for_aggregate,
    project_segmented_background_for_product_definition,
)
from services.acm_segmented_electrical_service import (
    electrical_confirmation_blockers,
    normalize_electrical_connection_management,
    project_electrical_for_product_definition,
)


def _two_panel_confirmed(**elec_kwargs):
    base = {
        "schema": "acm_segmented_background_v1",
        "status": "CONFIRMED",
        "operator_confirmed": True,
        "assembly_id": "asm_elec_test",
        "panels": [
            {"panel_id": "panel_1", "order": 1, "width_mm": 1000, "height_mm": 350, "position": {"x_mm": 0, "y_mm": 0}},
            {"panel_id": "panel_2", "order": 2, "width_mm": 1000, "height_mm": 350, "position": {"x_mm": 1000, "y_mm": 0}},
        ],
        "joints": [
            {
                "joint_id": "joint_panel_1_panel_2",
                "left_panel_id": "panel_1",
                "right_panel_id": "panel_2",
                "orientation": "VERTICAL",
            }
        ],
        "element_bindings": [],
    }
    if elec_kwargs:
        base["electrical_connection_management"] = elec_kwargs.get("electrical") or elec_kwargs
    return base


def test_single_panel_has_no_electrical_projection():
    raw = {
        "status": "CONFIRMED",
        "operator_confirmed": True,
        "panels": [
            {"panel_id": "panel_1", "order": 1, "width_mm": 500, "height_mm": 500, "position": {"x_mm": 0, "y_mm": 0}}
        ],
        "electrical_connection_management": {
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [{"panel_id": "panel_1", "supply_mode": "DIRECT_220V", "service_point_position": "TOP_RIGHT"}],
        },
    }
    norm = normalize_segmented_background(raw)
    assert "electrical_connection_management" not in (norm or {})


def test_direct_220v_per_panel_confirms_and_projects():
    raw = _two_panel_confirmed(
        electrical={
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [
                {
                    "panel_id": "panel_1",
                    "supply_mode": "DIRECT_220V",
                    "service_point_position": "TOP_RIGHT",
                    "routing_direction_note_ro": "spre dreapta sus",
                    "workshop_prep": {"cables_routed_toward_service": True, "reserve_required": True},
                    "installation": {"connect_to_client_220v": True},
                },
                {
                    "panel_id": "panel_2",
                    "supply_mode": "DIRECT_220V",
                    "service_point_position": "TOP_LEFT",
                    "routing_direction_note_ro": "spre stanga sus",
                },
            ],
            "inter_panel_connections": [],
        }
    )
    finish = persist_segmented_background_on_finish({"segmented_background": raw})
    seg = finish["segmented_background"]
    assert seg["electrical_connection_management"]["status"] == "CONFIRMED"
    pd = project_segmented_background_for_product_definition(seg)
    assert pd is not None
    elec = pd["electrical_connection_management"]
    assert elec["operator_confirmed"] is True
    positions = {p["panel_id"]: p["service_point_position"] for p in elec["panels"]}
    assert positions["panel_1"] == "TOP_RIGHT"
    assert positions["panel_2"] == "TOP_LEFT"
    agg = project_segmented_background_for_aggregate(seg)
    assert agg["electrical_connection_management"]["status"] == "CONFIRMED"
    assert agg["electrical_connection_management"]["materials"] == []
    assert agg["electrical_connection_management"]["task_rules"] == []
    assert agg["electrical_connection_management"]["future_task_intent_authority"] == "INFORMATIONAL_ONLY"


def test_shared_supply_and_inter_panel_link():
    raw = _two_panel_confirmed(
        electrical={
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [
                {"panel_id": "panel_1", "supply_mode": "DIRECT_220V", "service_point_position": "TOP_RIGHT"},
                {
                    "panel_id": "panel_2",
                    "supply_mode": "SHARED_FROM_PANEL",
                    "shared_from_panel_id": "panel_1",
                    "installation": {"finalize_after_alignment": True},
                },
            ],
            "inter_panel_connections": [
                {
                    "connection_id": "ec_panel_1_panel_2",
                    "source_panel_id": "panel_1",
                    "destination_panel_id": "panel_2",
                    "alignment_dependent": True,
                    "prepared_in_workshop": True,
                    "completed_on_site": True,
                    "reserve_required": True,
                    "estimated_length_m": 0.8,
                    "length_is_estimate": True,
                }
            ],
        }
    )
    finish = persist_segmented_background_on_finish({"segmented_background": raw})
    elec = finish["segmented_background"]["electrical_connection_management"]
    assert elec["panels"][1]["shared_from_panel_id"] == "panel_1"
    assert elec["inter_panel_connections"][0]["length_is_estimate"] is True


def test_unconfirmed_is_non_authoritative_on_pd():
    raw = _two_panel_confirmed(
        electrical={
            "status": "DRAFT",
            "operator_confirmed": False,
            "panels": [
                {"panel_id": "panel_1", "supply_mode": "UNCONFIRMED"},
                {"panel_id": "panel_2", "supply_mode": "UNCONFIRMED"},
            ],
        }
    )
    norm = normalize_segmented_background(raw)
    pd = project_segmented_background_for_product_definition(norm)
    assert "electrical_connection_management" not in pd
    assert pd["electrical_connection_management_draft"]["authoritative"] is False
    assert pd["electrical_connection_management_draft"]["downstream_effects"] is False
    agg = project_segmented_background_for_aggregate(norm)
    assert "electrical_connection_management" not in agg


def test_invalid_shared_self_reference_blocks_confirm():
    elec = normalize_electrical_connection_management(
        {
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [
                {"panel_id": "panel_1", "supply_mode": "DIRECT_220V", "service_point_position": "TOP_RIGHT"},
                {
                    "panel_id": "panel_2",
                    "supply_mode": "SHARED_FROM_PANEL",
                    "shared_from_panel_id": "panel_2",
                },
            ],
        },
        assembly_panel_ids={"panel_1", "panel_2"},
    )
    blockers = electrical_confirmation_blockers(elec, assembly_panel_ids={"panel_1", "panel_2"})
    assert any(b["code"] == "ELEC_SELF_SHARED" for b in blockers)


def test_invalid_shared_panel_blocks_confirm():
    elec = normalize_electrical_connection_management(
        {
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [
                {"panel_id": "panel_1", "supply_mode": "DIRECT_220V", "service_point_position": "TOP_RIGHT"},
                {
                    "panel_id": "panel_2",
                    "supply_mode": "SHARED_FROM_PANEL",
                    "shared_from_panel_id": "panel_99",
                },
            ],
        },
        assembly_panel_ids={"panel_1", "panel_2"},
    )
    blockers = electrical_confirmation_blockers(elec, assembly_panel_ids={"panel_1", "panel_2"})
    assert any(b["code"] == "ELEC_INVALID_SHARED" for b in blockers)


def test_custom_position_requires_note_when_confirmed():
    elec = normalize_electrical_connection_management(
        {
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [
                {
                    "panel_id": "panel_1",
                    "supply_mode": "DIRECT_220V",
                    "service_point_position": "CUSTOM",
                },
                {"panel_id": "panel_2", "supply_mode": "NO_LOCAL_220V"},
            ],
        },
        assembly_panel_ids={"panel_1", "panel_2"},
    )
    blockers = electrical_confirmation_blockers(elec, assembly_panel_ids={"panel_1", "panel_2"})
    assert any(b["code"] == "ELEC_CUSTOM_NOTE" for b in blockers)


def test_proposed_assembly_zero_electrical_projection():
    raw = {
        "status": "PROPOSED",
        "operator_confirmed": False,
        "panels": [
            {"panel_id": "panel_1", "order": 1, "width_mm": 1000, "height_mm": 350, "position": {"x_mm": 0, "y_mm": 0}},
            {"panel_id": "panel_2", "order": 2, "width_mm": 1000, "height_mm": 350, "position": {"x_mm": 1000, "y_mm": 0}},
        ],
        "electrical_connection_management": {
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [
                {"panel_id": "panel_1", "supply_mode": "DIRECT_220V", "service_point_position": "TOP_RIGHT"},
                {"panel_id": "panel_2", "supply_mode": "DIRECT_220V", "service_point_position": "TOP_LEFT"},
            ],
        },
    }
    norm = normalize_segmented_background(raw)
    assert project_segmented_background_for_product_definition(norm) is None
    assert project_electrical_for_product_definition(
        norm.get("electrical_connection_management") if norm else None,
        assembly_confirmed=False,
    ) is None


def test_persist_rejects_confirmed_electrical_with_blockers():
    raw = _two_panel_confirmed(
        electrical={
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [
                {"panel_id": "panel_1", "supply_mode": "UNCONFIRMED"},
                {"panel_id": "panel_2", "supply_mode": "UNCONFIRMED"},
            ],
        }
    )
    try:
        persist_segmented_background_on_finish({"segmented_background": raw})
        raised = False
    except ValueError as exc:
        raised = True
        detail = exc.args[0]
        assert detail["error"] == "segmented_electrical_confirmation_blocked"
    assert raised
