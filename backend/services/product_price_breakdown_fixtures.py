"""Built-in demo configurations for Product Price Breakdown Studio (no ProductInstance)."""

from __future__ import annotations

from typing import Any, Optional

VL = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = "TPL-VOLUMETRIC-LOGO_v1"
ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
VOLUM_AL = "TPL-VOLUM-ALUMINIU_v1"


def vl_letters_demo_quote_input() -> dict[str, Any]:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "letters-breakdown-demo.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "volum_aluminum_module_template_code": VOLUM_AL,
            "backing_mode": "closed_back",
            "mounting_system": "direct_wall",
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "led_module_count": 24,
            "letter_led_module_count": 24,
            "selected_psu_watts": 100,
            "psu_count": 1,
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.5,
            "mounting_template_material_type": "forex",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        },
    }


def acm_shell_demo_quote_input() -> dict[str, Any]:
    return {
        "finish_setup": {
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_breakdown_demo",
                "association_status": "proposed",
                "technical_configuration_status": "proposed",
                "composition_status": "unconfirmed",
                "geometry": {
                    "width_mm": 1000,
                    "height_mm": 350,
                    "panels": [
                        {
                            "panel_id": "p1",
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 0, "y_mm": 0},
                        }
                    ],
                    "joints": [],
                },
                "configuration": {
                    "finished_depth_mm": 60,
                    "fold_count": 1,
                    "l1_mm": 60,
                    "l2_mm": 0,
                    "field_authority": {"fold_count": "catalog_default"},
                },
            },
            "applied_content": "none",
        }
    }


def logo_demo_quote_input() -> dict[str, Any]:
    return {
        "analysis_ready": True,
        "client": {"width_mm": 800, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 1,
            "letter_perimeter_m": 4.0,
            "letter_face_area_m2": 0.6,
        },
        "finish_setup": {
            "illuminated": True,
            "letter_led_module_count": 12,
            "psu_count": 1,
        },
    }


def volum_aluminiu_demo_quote_input() -> dict[str, Any]:
    """Child-owned perimeter confirmation — not a root-product distortion."""
    return {
        "quote_geometry": {"letter_perimeter_m": 12.5},
        "layer_role_setup": {
            "layers": [
                {
                    "layer_key": "pseudo:maria",
                    "layer_id": "pseudo:maria",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ]
        },
        "finish_setup": {
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "letter_group_finishes": [
                {
                    "group_key": "pseudo:maria",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                }
            ],
            "return_cant_component_confirmation": {
                "instances": {
                    "letter_group:pseudo:maria": {
                        "confirmed_perimeter_m": 12.5,
                        "confirmed_perimeter_source": "operator_confirmed",
                        "confirmation_source": "operator_component_confirmation",
                    }
                }
            },
        },
    }


FIXTURES: dict[str, dict[str, Any]] = {
    "vl_letters_demo_v1": {
        "template_code": VL,
        "quote_input": vl_letters_demo_quote_input(),
        "label_ro": "VL litere demo (perimetru 12.5 ml, 24 module LED)",
    },
    "acm_shell_demo_v1": {
        "template_code": ACM,
        "quote_input": acm_shell_demo_quote_input(),
        "label_ro": "ACM shell panel-only (fără tratamente)",
    },
    "logo_demo_v1": {
        "template_code": LOGO,
        "quote_input": logo_demo_quote_input(),
        "label_ro": "Logo preview (poate fi parțial — PD lipsă)",
    },
    "volum_aluminiu_demo_v1": {
        "template_code": VOLUM_AL,
        "quote_input": volum_aluminiu_demo_quote_input(),
        "label_ro": "Volum Aluminiu — breakdown copil",
    },
}


def _canonical_declared_code(template_code: str) -> Optional[str]:
    """Map uppercased identity codes to the mixed-case catalog keys used in rules/DB."""
    needle = (template_code or "").strip().upper()
    for declared in (VL, ACM, LOGO, VOLUM_AL):
        if declared.upper() == needle:
            return declared
    return None


def resolve_fixture(
    template_code: str,
    fixture_id: Optional[str] = None,
) -> tuple[Optional[str], Optional[dict[str, Any]], Optional[str], Optional[str]]:
    """Return (fixture_id, quote_input, label, declared_template_code) or empties."""
    declared = _canonical_declared_code(template_code)
    if fixture_id and fixture_id in FIXTURES:
        f = FIXTURES[fixture_id]
        return (
            fixture_id,
            dict(f["quote_input"]),
            str(f["label_ro"]),
            str(f["template_code"]),
        )
    defaults = {
        VL: "vl_letters_demo_v1",
        ACM: "acm_shell_demo_v1",
        LOGO: "logo_demo_v1",
        VOLUM_AL: "volum_aluminiu_demo_v1",
    }
    if not declared:
        return None, None, None, None
    fid = defaults.get(declared)
    if not fid:
        return None, None, None, declared
    f = FIXTURES[fid]
    return fid, dict(f["quote_input"]), str(f["label_ro"]), declared
