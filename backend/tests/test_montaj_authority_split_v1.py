"""Montaj authority split — ACM vs commercial mounting vs electrical (D1–D5)."""

from __future__ import annotations

import pytest

from services.acm_segmented_background_service import coalesce_segmented_background_for_finish
from services.mounting_solution_service import ACM_BOXED_MOUNTING_TEMPLATE_CODE
from services.product_definition_composition_contract import (
    BLOCKER_MOUNTING_SCOPE_INACTIVE,
    build_product_definition_composition,
)
from services.product_process_resolve_input_adapter import (
    _segmented_electrical_authority_complete,
    build_resolve_input_from_active_config,
)
from services.product_process_resolver_service import resolve_product_process_graph
from schemas.product_process_contract import ProductProcessResolveInput


TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _acm_finish(**extra):
    base = {
        "mounting_scope": "none",
        "mounting_solution": {
            "kind": "product_system_template",
            "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
            "configuration": {
                "panel_width_mm": 1000,
                "panel_height_mm": 350,
                "acm_thickness_mm": 3,
                "return_depth_mm": 60,
                "rear_lip_mm": 25,
                "fold_sides": "all",
                "v_groove_angle_deg": 135,
            },
        },
        "mounting_template_enabled": True,
        "mounting_template_area_m2": 0.7,
        "mounting_template_material_type": "forex",
        "confirmed": True,
        "lighting_system_type": "led_modules",
        "illuminated": True,
        "return_finish_type": "white_aluminum",
        "svg_support_selection": {
            "schema": "svg_support_selection_v1",
            "status": "confirmed",
            "role": "ALUCOBOND_CASED_PANEL",
        },
    }
    base.update(extra)
    return base


def test_composition_acm_scope_none_no_mounting_scope_inactive():
    payload = {
        "quote_geometry": {"letter_count": 3, "confirmed": True},
        "finish_setup": _acm_finish(),
    }
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=payload,
        source_payload_type="workspace_payload",
    )
    assert BLOCKER_MOUNTING_SCOPE_INACTIVE not in comp.blockers
    assert any(
        n.template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE and n.included_in_graph
        for n in comp.nodes
    )


def test_template_inactive_under_scope_none_in_process_adapter():
    finish = _acm_finish()
    inp, _warnings, _blockers, _meta = build_resolve_input_from_active_config(
        template_code=TEMPLATE,
        workspace_payload={"finish_setup": finish, "quote_geometry": {"confirmed": True}},
    )
    assert inp.template_selected is False


def test_template_active_under_preparation():
    finish = _acm_finish(mounting_scope="preparation_only")
    inp, _warnings, _blockers, _meta = build_resolve_input_from_active_config(
        template_code=TEMPLATE,
        workspace_payload={"finish_setup": finish, "quote_geometry": {"confirmed": True}},
    )
    assert inp.template_selected is True


def test_coalesce_protects_confirmed_from_proposed_overwrite():
    existing = {
        "segmented_background": {
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [{"panel_id": "panel_1"}, {"panel_id": "panel_2"}],
        }
    }
    incoming = {
        "segmented_background": {
            "status": "PROPOSED",
            "panels": [{"panel_id": "panel_1"}, {"panel_id": "panel_2"}],
        }
    }
    out = coalesce_segmented_background_for_finish(incoming, existing)
    assert str(out["segmented_background"]["status"]).upper() == "CONFIRMED"


def test_coalesce_allows_force_repropose():
    existing = {
        "segmented_background": {
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": [{"panel_id": "panel_1"}, {"panel_id": "panel_2"}],
        }
    }
    incoming = {
        "segmented_background": {
            "status": "PROPOSED",
            "force_repropose": True,
            "panels": [{"panel_id": "panel_1"}, {"panel_id": "panel_2"}],
        }
    }
    out = coalesce_segmented_background_for_finish(incoming, existing)
    assert str(out["segmented_background"]["status"]).upper() == "PROPOSED"


def test_segmented_electrical_complete_helper():
    finish = {
        "segmented_background": {
            "status": "CONFIRMED",
            "panels": [{"panel_id": "panel_1"}, {"panel_id": "panel_2"}],
            "electrical_connection_management": {
                "status": "CONFIRMED",
                "panels": [
                    {
                        "panel_id": "panel_1",
                        "supply_mode": "DIRECT_220V",
                        "service_point_position": "BOTTOM_RIGHT",
                    },
                    {
                        "panel_id": "panel_2",
                        "supply_mode": "SHARED_FROM_PANEL",
                        "shared_from_panel_id": "panel_1",
                    },
                ],
            },
        }
    }
    assert _segmented_electrical_authority_complete(finish) is True


def test_resolver_skips_legacy_corner_when_segmented_electrical_complete():
    inp = ProductProcessResolveInput(
        product_template_code=TEMPLATE,
        support_type="alucobond_cased",
        power_supply_service_corner=None,
        segmented_electrical_authority_complete=True,
        illuminated=True,
        geometry_confirmed=True,
        led_layout_confirmed=True,
        active_components=["FACE", "CANT", "BACK", "LIGHTING", "ALUCOBOND_CASED_PANEL"],
    )
    graph = resolve_product_process_graph(inp)
    assert not any(b.code == "service_corner_required" for b in graph.blockers)


def test_resolver_requires_legacy_corner_for_single_panel_alucobond():
    inp = ProductProcessResolveInput(
        product_template_code=TEMPLATE,
        support_type="alucobond_cased",
        power_supply_service_corner=None,
        segmented_electrical_authority_complete=False,
        illuminated=True,
        geometry_confirmed=True,
        led_layout_confirmed=True,
        active_components=["FACE", "CANT", "BACK", "LIGHTING", "ALUCOBOND_CASED_PANEL"],
    )
    graph = resolve_product_process_graph(inp)
    assert any(b.code == "service_corner_required" for b in graph.blockers)


def test_adapter_skips_legacy_corner_when_segmented_confirmed_even_if_ecm_draft():
    from services.product_process_resolve_input_adapter import (
        _segmented_owns_service_corner_authority,
        build_resolve_input_from_active_config,
    )

    finish = _acm_finish(
        segmented_background={
            "status": "CONFIRMED",
            "panels": [{"panel_id": "panel_1"}, {"panel_id": "panel_2"}],
            "electrical_connection_management": {"status": "DRAFT", "panels": []},
        }
    )
    assert _segmented_owns_service_corner_authority(finish) is True
    assert _segmented_electrical_authority_complete(finish) is False
    inp, _w, _b, _m = build_resolve_input_from_active_config(
        template_code=TEMPLATE,
        workspace_payload={"finish_setup": finish, "quote_geometry": {"confirmed": True}},
    )
    assert inp.segmented_electrical_authority_complete is True
    graph = resolve_product_process_graph(inp)
    assert not any(b.code == "service_corner_required" for b in graph.blockers)
