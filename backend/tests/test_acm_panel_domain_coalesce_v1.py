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
