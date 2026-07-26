"""PD observability for proposed ACM instance + nested panels (no pricing)."""

from services.product_definition_builder_service import _build_canonical_values


def test_proposed_acm_instance_projects_panels_without_technical_confirmed():
    payload = {
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_cc_1",
                "association_status": "proposed",
                "technical_configuration_status": "proposed",
                "composition_status": "unconfirmed",
                "capabilities": {
                    "active": ["boxed_returns", "segmented_panels"],
                    "inactive": ["led_system", "totem_face"],
                },
            },
            "svg_support_selection": {
                "schema": "svg_support_selection_v1",
                "status": "proposed",
                "role": "ALUCOBOND_CASED_PANEL",
                "contour_id": "cc_1",
                "svg_support_element_id": "el-1",
                "panel_geometry": {"width_mm": 1000, "height_mm": 350},
                "casing_profile": {
                    "fold_count": 2,
                    "l1_mm": 60,
                    "l2_mm": 25,
                    "finished_depth_mm": 60,
                },
                "field_authority": {
                    "panel_geometry": "detected",
                    "fold_count": "catalog_default",
                    "acm_thickness_mm": "catalog_default",
                },
                "technical_configuration_status": "proposed",
            },
            "svg_component_bindings": [
                {
                    "binding_id": "bind_support_cc_1",
                    "geometry_role": "SUPPORT_CONTOUR",
                    "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    "selection_mode": "CLOSED_CONTOUR",
                    "selected_geometry": {
                        "element_ids": ["cc_1"],
                        "geometry_hashes": ["h1"],
                    },
                    "status": "DRAFT",
                }
            ],
            "segmented_background": {
                "schema": "acm_segmented_background_v1",
                "status": "PROPOSED",
                "operator_confirmed": False,
                "assembly_id": "asm_1",
                "host_component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "panels": [
                    {"panel_id": "panel_1", "order": 1, "width_mm": 1000, "height_mm": 350},
                    {"panel_id": "panel_2", "order": 2, "width_mm": 1000, "height_mm": 350},
                ],
                "joints": [],
                "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
                "element_bindings": [],
                "detection": {"authority": "PROPOSAL_ONLY"},
            },
        }
    }
    values = _build_canonical_values([], payload)
    assert values["support_type"] == "alucobond_cased"
    assert values["acp_panel_active"] is True
    assert values["acp_panel_technical_confirmed"] is False
    assert values["acm_panel_composition_status"] == "unconfirmed"
    assert values["acp_panel_selection_status"] == "proposed"
    assert values["casing_profile_field_authority"]["acm_thickness_mm"] == "catalog_default"
    prop = values["segmented_background_proposal"]
    assert prop["status"] == "PROPOSED"
    assert len(prop["panels"]) == 2
    assert prop["downstream_effects"] is False
    assert prop["materials"] == []
    assert prop["task_rules"] == []
    # CONFIRMED-only authority must not leak
    assert "segmented_background" not in values or values.get("segmented_background") is None
    # Explicit assembly keys (not panel_* overload)
    assert values["assembly_width_mm"] == 2000
    assert values["assembly_height_mm"] == 350
    assert values.get("panel_width_mm") != 2000
