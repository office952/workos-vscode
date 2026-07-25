"""Dry-run quote_input must bridge composition_confirmed.applied_content for CPP conn lines."""

from __future__ import annotations

from services.intake_v6_priced_quote_dry_run_service import _enrich_quote_input_linked_logo_geometry
from services.letters_acm_composition_commercial_v1 import is_letters_acm_composition_active
from services.mounting_solution_service import ACM_BOXED_MOUNTING_TEMPLATE_CODE


def test_enrich_bridges_confirmed_applied_content_when_finish_bag_empty() -> None:
    payload_raw = {
        "finish_setup": {
            "applied_content": None,
            "mounting_template_area_m2": 0.35,
            "mounting_solution": {
                "kind": "product_system_template",
                "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
                "configuration": {
                    "panel_width_mm": 2000,
                    "panel_height_mm": 500,
                    "acm_thickness_mm": 3,
                    "return_depth_mm": 60,
                    "fold_sides": "all",
                },
            },
        },
        "product_composition_confirmed": {
            "confirmed": True,
            "applied_content": "letters",
            "items": [{"composition_item_id": "letters"}, {"composition_item_id": "support"}],
        },
    }
    quote_input = {
        "finish_setup": {
            "mounting_solution": payload_raw["finish_setup"]["mounting_solution"],
        }
    }
    enriched = _enrich_quote_input_linked_logo_geometry(payload_raw, quote_input)
    assert enriched.get("applied_content") == "letters"
    assert (enriched.get("finish_setup") or {}).get("applied_content") == "letters"
    assert enriched.get("product_composition_confirmed", {}).get("applied_content") == "letters"
    assert is_letters_acm_composition_active(enriched) is True
