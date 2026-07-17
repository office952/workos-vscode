from services.intake_v6_product_composition_recommendation_service import (
    LETTERS_TEMPLATE_CODE,
    LOGO_TEMPLATE_CODE,
    SUPPORT_TEMPLATE_LEGACY_REDIRECT,
    SUPPORT_TEMPLATE_LIVE_CODE,
    build_layer_role_review,
    build_product_composition_recommendation,
)


def _payload(file_name: str, layers: list[dict]) -> dict:
    return {
        "svg_source": {"file_name": file_name, "file_size_bytes": 123, "upload_status": "analyzed"},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": layers,
            "layer_bindings": [],
            "warnings": [],
        },
    }


def _layer(key: str, name: str, role: str) -> dict:
    return {
        "layer_key": key,
        "layer_id": key,
        "layer_name": name,
        "auto_role": role,
        "confirmed_role": role,
        "confirmation_state": "confirmed",
        "auto_confidence": "high",
    }


def test_recommends_logo_template_for_logo_only_svg() -> None:
    payload = _payload("logo.svg", [_layer("logo-dreapta", "logo dreapta", "printed_artwork")])

    recommendation = build_product_composition_recommendation(payload)

    assert recommendation["composition_type"] == "logo_only"
    assert [item["template_code"] for item in recommendation["composition_items"]] == [LOGO_TEMPLATE_CODE]
    assert recommendation["blockers"] == []


def test_recommends_letters_template_for_letters_only_svg() -> None:
    payload = _payload("letters.svg", [_layer("letters", "Litere", "face")])

    recommendation = build_product_composition_recommendation(payload)

    assert recommendation["composition_type"] == "letters_only"
    assert [item["template_code"] for item in recommendation["composition_items"]] == [LETTERS_TEMPLATE_CODE]


def test_recommends_letters_plus_logo_for_gradi_mixed_roles() -> None:
    payload = _payload(
        "gradi-curat.svg",
        [
            _layer("letters", "Litere GRADI", "face"),
            _layer("logo-stanga", "logo stanga", "printed_artwork"),
            _layer("logo-dreapta", "logo dreapta", "printed_artwork"),
        ],
    )

    recommendation = build_product_composition_recommendation(payload)

    assert recommendation["composition_type"] == "letters_plus_logo"
    assert [item["template_code"] for item in recommendation["composition_items"]] == [
        LETTERS_TEMPLATE_CODE,
        LOGO_TEMPLATE_CODE,
    ]
    logo_item = next(item for item in recommendation["composition_items"] if item["component_role"] == "volumetric_logo")
    assert logo_item["source_layer_ids"] == ["logo-stanga", "logo-dreapta"]


def test_support_role_maps_to_live_acm_not_stale_bond() -> None:
    payload = _payload(
        "complex.svg",
        [
            _layer("letters", "Litere", "face"),
            _layer("logo", "Logo", "logo"),
            _layer("fundal", "Fundal caseta", "support_panel"),
        ],
    )

    recommendation = build_product_composition_recommendation(payload)

    assert recommendation["composition_type"] == "letters_plus_logo_plus_support"
    support = next(item for item in recommendation["composition_items"] if item["component_role"] == "support_panel")
    assert support["template_code"] == SUPPORT_TEMPLATE_LIVE_CODE
    assert support["status"] == "available_optional"
    assert support["template_code"] != "TPL-BOND-CASETAT"
    assert [warning["code"] for warning in recommendation["warnings"]] == [SUPPORT_TEMPLATE_LEGACY_REDIRECT]


def test_logo_svg_generated_side_label_is_neutral_for_operator() -> None:
    payload = _payload("logo.svg", [_layer("logo-dreapta", "logo dreapta", "printed_artwork")])

    review = build_layer_role_review(payload)

    assert review["roles"][0]["display_label"] == "Logo volumetric"


def test_support_from_svg_component_binding_without_layer_role() -> None:
    payload = _payload("letters-acp.svg", [_layer("letters", "Litere", "face")])
    payload["finish_setup"] = {
        "svg_component_bindings": [
            {
                "schema": "svg_component_bindings_v1",
                "binding_id": "bind_support_cc1",
                "geometry_role": "SUPPORT_CONTOUR",
                "component_template_code": SUPPORT_TEMPLATE_LIVE_CODE,
                "selection_mode": "CLOSED_CONTOUR",
                "selected_geometry": {
                    "layer_ids": [],
                    "group_ids": [],
                    "element_ids": ["cc_outer"],
                    "geometry_hashes": ["abc"],
                    "source_svg_hash": "h1",
                },
                "configuration": {},
                "status": "CONFIRMED",
            }
        ]
    }

    recommendation = build_product_composition_recommendation(payload)

    assert recommendation["composition_type"] == "letters_plus_support"
    support = next(item for item in recommendation["composition_items"] if item["component_role"] == "support_panel")
    assert support["template_code"] == SUPPORT_TEMPLATE_LIVE_CODE
    assert support["source_layer_ids"] == ["cc_outer"]