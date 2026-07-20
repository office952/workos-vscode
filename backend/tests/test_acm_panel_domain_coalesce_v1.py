"""ACM panel domain action: preserve | upsert | clear."""

from services.acm_panel_domain_service import coalesce_acm_panel_domain_for_finish


def _support_binding():
    return {
        "schema": "svg_component_bindings_v1",
        "binding_id": "bind_support_x",
        "geometry_role": "SUPPORT_CONTOUR",
        "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        "status": "DRAFT",
    }


def test_preserve_restores_support_when_letter_bindings_omit_it():
    existing = {
        "svg_component_bindings": [_support_binding()],
        "svg_support_selection": {
            "schema": "svg_support_selection_v1",
            "status": "proposed",
            "role": "ALUCOBOND_CASED_PANEL",
        },
        "mounting_solution": {"template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"},
        "acm_panel_instance": {"schema": "acm_panel_component_instance_v1", "association_status": "proposed"},
    }
    incoming = {
        "acm_panel_domain_action": "preserve",
        "svg_component_bindings": [
            {
                "schema": "svg_component_bindings_v1",
                "binding_id": "bind_letters",
                "geometry_role": "LETTER_VECTOR_SET",
                "status": "CONFIRMED",
            }
        ],
    }
    layer_roles = {
        "layers": [
            {"confirmed_role": "support_panel", "confirmation_state": "confirmed"},
            {"confirmed_role": "face", "confirmation_state": "confirmed"},
        ]
    }
    out = coalesce_acm_panel_domain_for_finish(incoming, existing, layer_role_setup=layer_roles)
    roles = [b.get("geometry_role") for b in out["svg_component_bindings"]]
    assert "SUPPORT_CONTOUR" in roles
    assert "LETTER_VECTOR_SET" in roles
    assert out["svg_support_selection"]["status"] == "proposed"
    assert out["mounting_solution"] is not None
    assert out["acm_panel_instance"] is not None


def test_clear_removes_acm_shell():
    existing = {
        "svg_component_bindings": [_support_binding()],
        "svg_support_selection": {"schema": "svg_support_selection_v1", "status": "proposed"},
        "mounting_solution": {"template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"},
        "acm_panel_instance": {"schema": "acm_panel_component_instance_v1"},
    }
    incoming = {
        "acm_panel_domain_action": "clear",
        "svg_component_bindings": [_support_binding()],
    }
    out = coalesce_acm_panel_domain_for_finish(incoming, existing, layer_role_setup=None)
    assert out["acm_panel_instance"] is None
    assert out["mounting_solution"] is None
    assert out["svg_support_selection"]["status"] == "none"
    assert not any(b.get("geometry_role") == "SUPPORT_CONTOUR" for b in out["svg_component_bindings"])


def test_upsert_keeps_incoming_shell():
    incoming = {
        "acm_panel_domain_action": "upsert",
        "svg_support_selection": {
            "schema": "svg_support_selection_v1",
            "status": "proposed",
            "role": "ALUCOBOND_CASED_PANEL",
        },
        "acm_panel_instance": {
            "schema": "acm_panel_component_instance_v1",
            "association_status": "proposed",
            "composition_status": "unconfirmed",
        },
        "svg_component_bindings": [_support_binding()],
    }
    out = coalesce_acm_panel_domain_for_finish(incoming, {}, layer_role_setup=None)
    assert out["svg_support_selection"]["status"] == "proposed"
    assert out["acm_panel_instance"]["composition_status"] == "unconfirmed"


def _measured_instance():
    return {
        "schema": "acm_panel_component_instance_v1",
        "component_instance_id": "acm_qa_double_fold_2000x300",
        "association_status": "confirmed",
        "production_geometry": {
            "schema": "acm_panel_production_geometry_bundle_v1",
            "attachments": [
                {
                    "attachment_id": "att_golden",
                    "measurement_status": "measured",
                    "panel_id": "p1",
                    "metrics_snapshot": {
                        "cut_length_ml": 5.499412,
                        "v_groove_total_ml": 10.000004,
                    },
                }
            ],
        },
    }


def test_upsert_omitting_instance_preserves_existing_and_other_finish_fields():
    """Review autosave without hydrate must not wipe measured AcmPanel or unrelated finish fields."""
    existing = {
        "face_finish_type": "oracal_651",
        "return_depth_mm": 60,
        "illuminated": True,
        "mounting_system": "acm_panel",
        "acm_panel_instance": _measured_instance(),
        "svg_support_selection": {
            "schema": "svg_support_selection_v1",
            "status": "confirmed",
            "role": "SUPPORT_CONTOUR",
        },
    }
    incoming = {
        # svg_support confirmed → inferred upsert; instance omitted (pre-hydrate FE bug).
        "face_finish_type": "oracal_651",
        "return_depth_mm": 60,
        "illuminated": True,
        "return_finish_type": "ral_paint",
        "svg_support_selection": {
            "schema": "svg_support_selection_v1",
            "status": "confirmed",
            "role": "SUPPORT_CONTOUR",
        },
    }
    out = coalesce_acm_panel_domain_for_finish(incoming, existing, layer_role_setup=None)
    assert out["acm_panel_instance"]["component_instance_id"] == "acm_qa_double_fold_2000x300"
    att = out["acm_panel_instance"]["production_geometry"]["attachments"][0]
    assert att["measurement_status"] == "measured"
    assert att["metrics_snapshot"]["cut_length_ml"] == 5.499412
    assert out["face_finish_type"] == "oracal_651"
    assert out["return_depth_mm"] == 60
    assert out["illuminated"] is True
    assert out["return_finish_type"] == "ral_paint"


def test_placeholder_analysis_autosave_does_not_delete_measured_instance():
    """Empty-ish finish PUT after placeholder SVG / analysis-bundle must keep measured instance."""
    existing = {
        "face_finish_type": "oracal_651",
        "acm_panel_instance": _measured_instance(),
        "svg_support_selection": {"schema": "svg_support_selection_v1", "status": "confirmed"},
        "mounting_solution": {"template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"},
    }
    # Layers rewritten away from support_panel (analysis race) + omit ACM shell fields.
    incoming = {
        "acm_panel_domain_action": "preserve",
        "face_finish_type": None,
        "return_depth_mm": None,
        "illuminated": True,
        "confirmed": True,
    }
    layer_roles = {
        "layers": [
            {
                "layer_key": "logo_instance_001",
                "confirmed_role": None,
                "confirmation_state": "pending",
            }
        ]
    }
    out = coalesce_acm_panel_domain_for_finish(incoming, existing, layer_role_setup=layer_roles)
    assert out["acm_panel_instance"] is not None
    assert out["acm_panel_instance"]["production_geometry"]["attachments"][0]["attachment_id"] == (
        "att_golden"
    )
    # Unrelated incoming fields still win (not clobbered by existing).
    assert out["illuminated"] is True
    assert out["confirmed"] is True
    assert out["face_finish_type"] is None
