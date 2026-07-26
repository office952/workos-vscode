"""LETTERS_CANONICAL_PRODUCT_SLICE_V1 — commercial measurement contract (non-monetary)."""

from __future__ import annotations

from schemas.commercial_measurement_contract import COMMERCIAL_MEASUREMENT_CONTRACT_VERSION
from schemas.product_definition import ProductDefinitionPreview, ProductDefinitionSourceContext
from services.letters_commercial_measurement_service import (
    build_letters_commercial_measurements,
    measurement_quantity_by_line_code,
)


def _pd(geometry: dict, canonical: dict) -> ProductDefinitionPreview:
    return ProductDefinitionPreview(
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        source_context=ProductDefinitionSourceContext(
            template_code="TPL-VOLUMETRIC-LETTERS_v2",
            source_payload_type="workspace_payload",
            workspace_id="test-ws",
        ),
        geometry_inputs=geometry,
        canonical_values=canonical,
    )


def test_measurements_are_non_monetary_and_versioned():
    pd = _pd(
        {
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.8,
            "letter_count": 7,
        },
        {"led_module_count": 40, "mounting_template_area_m2": 0.5},
    )
    quote_input = {
        "quote_geometry": {
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.8,
        },
        "finish_setup": {
            "led_module_count": 40,
            "letter_led_module_count": 40,
            "mounting_template_area_m2": 0.5,
            "mounting_template_enabled": True,
            "mounting_template_material": "forex",
        },
    }
    bundle = build_letters_commercial_measurements(
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        pd=pd,
        quote_input=quote_input,
        active_modules=None,
    )
    assert bundle is not None
    assert bundle.contract_version == COMMERCIAL_MEASUREMENT_CONTRACT_VERSION
    assert bundle.template_code == "TPL-VOLUMETRIC-LETTERS_v2"

    face_qty, src = measurement_quantity_by_line_code(bundle, "debitare_fata")
    assert face_qty == 12.5
    assert src == "product_aggregate.commercial_measurements"

    back_qty, _ = measurement_quantity_by_line_code(bundle, "debitare_spate")
    assert back_qty == 1.8

    led_qty, _ = measurement_quantity_by_line_code(bundle, "sistem_led_module")
    assert led_qty == 40.0

    forbidden = {
        "unit_price",
        "price",
        "subtotal",
        "total",
        "margin",
        "tax",
        "discount",
        "hourly_rate",
        "planned_minutes",
        "actual_minutes",
        "internal_cost",
    }
    for m in bundle.measurements:
        dumped = m.model_dump()
        assert forbidden.isdisjoint(dumped.keys())
        assert m.quantity is None or isinstance(m.quantity, float)
        assert "minute" not in (m.unit or "").lower()


def test_non_letters_template_returns_none():
    assert (
        build_letters_commercial_measurements(
            template_code="TPL-ACM-CASSETTED-PANEL",
            pd=None,
            quote_input={},
        )
        is None
    )


def test_missing_geometry_marks_missing_input():
    bundle = build_letters_commercial_measurements(
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        pd=None,
        quote_input={"quote_geometry": {}, "finish_setup": {}},
    )
    assert bundle is not None
    qty, tag = measurement_quantity_by_line_code(bundle, "debitare_fata")
    assert qty is None
    assert tag and "unresolved" in tag
