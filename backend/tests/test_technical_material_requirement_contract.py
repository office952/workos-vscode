"""Upstream technical material quantity & ownership contract tests."""

from __future__ import annotations

import json

import pytest

from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateMaterial,
)
from services.ops_graph_frozen_technical_materials import (
    project_frozen_technical_materials,
)
from services.technical_material_requirement_service import (
    REJECTED_QUANTITY_SOURCES,
    apply_technical_material_requirements,
    assert_no_rejected_quantity_source,
)


def _agg(*materials: ProductAggregateMaterial) -> ProductAggregate:
    return ProductAggregate(
        template_id=1,
        template_code="TPL-TEST",
        business_name_ro="Test",
        materials=list(materials),
    )


def test_model_a_letter_face_area_derives_quantity():
    mat = ProductAggregateMaterial(
        material_code="MAT-ACP-FATA-LITERE",
        unit="mp",
        component_ref="comp_face_litere",
        formula_id="letter_face_area",
        provenance="parent",
        source_template_code="TPL-TEST",
    )
    out = apply_technical_material_requirements(
        _agg(mat),
        {"letter_face_area_m2": 2.5},
    )
    assert len(out.materials) == 1
    row = out.materials[0]
    assert row.quantity == 2.5
    assert row.quantity_status == "derived"
    assert row.quantity_model == "A"
    assert row.requirement_id
    assert row.owner_scope == "component_parent"


def test_missing_input_stays_null_not_zero():
    mat = ProductAggregateMaterial(
        material_code="MAT-ACP-FATA-LITERE",
        unit="mp",
        component_ref="comp_face_litere",
        formula_id="letter_face_area",
        provenance="parent",
        source_template_code="TPL-TEST",
    )
    out = apply_technical_material_requirements(_agg(mat), {})
    row = out.materials[0]
    assert row.quantity is None
    assert row.quantity != 0
    assert row.quantity_status == "source_missing"
    assert row.quantity_model == "A"


def test_model_d_formula_less_reference_only():
    mat = ProductAggregateMaterial(
        material_code="MAT-CONSUMABILE-MONTAJ",
        unit="set",
        component_ref="comp_finisaj_litere",
        formula_id=None,
        provenance="parent",
        source_template_code="TPL-TEST",
    )
    out = apply_technical_material_requirements(_agg(mat), {"letter_face_area_m2": 1.0})
    row = out.materials[0]
    assert row.quantity is None
    assert row.quantity_status == "reference_only"
    assert row.quantity_model == "D"


def test_active_depth_variant_emits_only_matching_profile():
    mats = [
        ProductAggregateMaterial(
            material_code="MAT-PROFIL-LATERAL-LITERE-30MM",
            unit="ml",
            component_ref="comp_volum",
            formula_id="return_profile_linear_meter",
            formula_params={"gate": {"return_depth_mm": 30}},
            provenance="linked_module",
            source_template_code="TPL-VOLUM",
        ),
        ProductAggregateMaterial(
            material_code="MAT-PROFIL-LATERAL-LITERE-60MM",
            unit="ml",
            component_ref="comp_volum",
            formula_id="return_profile_linear_meter",
            formula_params={"gate": {"return_depth_mm": 60}},
            provenance="linked_module",
            source_template_code="TPL-VOLUM",
        ),
        ProductAggregateMaterial(
            material_code="MAT-PROFIL-LATERAL-LITERE",
            unit="ml",
            component_ref="comp_lateral_litere",
            formula_id="letter_perimeter",
            provenance="parent",
            source_template_code="TPL-TEST",
        ),
    ]
    out = apply_technical_material_requirements(
        _agg(*mats),
        {"return_depth_mm": 60, "letter_perimeter_m": 12.5},
    )
    codes = [m.material_code for m in out.materials]
    assert codes == ["MAT-PROFIL-LATERAL-LITERE-60MM"]
    assert out.materials[0].quantity == 12.5
    assert out.materials[0].quantity_status == "derived"
    assert "return_depth_mm=60" in (out.materials[0].variant_discriminator or "")


def test_inactive_face_finish_does_not_emit():
    mats = [
        ProductAggregateMaterial(
            material_code="MAT-ORACAL-651",
            unit="mp",
            component_ref="comp_face_litere",
            formula_id="letter_face_area",
            provenance="parent",
            source_template_code="TPL-TEST",
        ),
        ProductAggregateMaterial(
            material_code="MAT-VINYL-PRINT",
            unit="mp",
            component_ref="comp_face_litere",
            formula_id="letter_face_area",
            provenance="parent",
            source_template_code="TPL-TEST",
        ),
        ProductAggregateMaterial(
            material_code="MAT-ACP-FATA-LITERE",
            unit="mp",
            component_ref="comp_face_litere",
            formula_id="letter_face_area",
            provenance="parent",
            source_template_code="TPL-TEST",
        ),
    ]
    out = apply_technical_material_requirements(
        _agg(*mats),
        {"face_finish_type": "oracal_651", "letter_face_area_m2": 1.2},
    )
    codes = [m.material_code for m in out.materials]
    assert "MAT-ORACAL-651" in codes
    assert "MAT-VINYL-PRINT" not in codes
    assert "MAT-ACP-FATA-LITERE" in codes


def test_same_code_different_provenance_preserved():
    mats = [
        ProductAggregateMaterial(
            material_code="MAT-ORACAL-651",
            unit="mp",
            component_ref="comp_face_litere",
            formula_id="letter_face_area",
            provenance="parent",
            source_template_code="TPL-PARENT",
        ),
        ProductAggregateMaterial(
            material_code="MAT-ORACAL-651",
            unit="mp",
            component_ref="comp_volum",
            formula_id="return_wrap_area",  # unregistered → source_missing if active
            formula_params={"gate": {"return_finish_type": "oracal_wrapped"}},
            provenance="linked_module",
            source_template_code="TPL-VOLUM",
        ),
    ]
    out = apply_technical_material_requirements(
        _agg(*mats),
        {
            "face_finish_type": "oracal_651",
            "return_finish_type": "oracal_wrapped",
            "letter_face_area_m2": 2.0,
        },
    )
    assert len(out.materials) == 2
    assert out.materials[0].provenance == "parent"
    assert out.materials[1].provenance == "linked_module"
    assert out.materials[0].requirement_id != out.materials[1].requirement_id
    assert out.materials[0].quantity == 2.0
    assert out.materials[1].quantity is None
    assert out.materials[1].quantity_status == "source_missing"


def test_unknown_formula_is_source_missing_not_zero():
    mat = ProductAggregateMaterial(
        material_code="MAT-VOPSEA-RAL",
        unit="buc",
        component_ref="comp_volum",
        formula_id="return_paint_consumption",
        formula_params={"gate": {"return_finish_type": "ral_paint"}},
        provenance="linked_module",
        source_template_code="TPL-VOLUM",
    )
    out = apply_technical_material_requirements(
        _agg(mat),
        {"return_finish_type": "ral_paint"},
    )
    assert len(out.materials) == 1
    assert out.materials[0].quantity is None
    assert out.materials[0].quantity_status == "source_missing"


def test_model_e_sources_are_rejected_by_guard():
    for src in REJECTED_QUANTITY_SOURCES:
        with pytest.raises(ValueError):
            assert_no_rejected_quantity_source(src)


def test_ops_graph_legacy_null_maps_to_legacy_unspecified():
    snap = json.dumps(
        {
            "product_aggregate_snapshot": {
                "materials": [
                    {
                        "material_code": "MAT-X",
                        "unit": "mp",
                        "quantity": None,
                        "provenance": "parent",
                    }
                ]
            }
        }
    )
    out = project_frozen_technical_materials(snap)
    assert out["entries"][0]["quantity"] is None
    assert out["entries"][0]["quantity_status"] == "legacy_unspecified"
    assert out["entries"][0]["quantity_status_label_ro"] == "Nespecificată"


def test_ops_graph_projects_derived_and_reference_statuses():
    snap = json.dumps(
        {
            "product_aggregate_snapshot": {
                "materials": [
                    {
                        "material_code": "MAT-A",
                        "unit": "mp",
                        "quantity": 1.5,
                        "quantity_status": "derived",
                        "quantity_model": "A",
                        "requirement_id": "r1",
                        "variant_discriminator": "face_finish_type=oracal_651",
                        "provenance": "parent",
                        "component_ref": "comp_face",
                        "unit_price": 99.0,
                    },
                    {
                        "material_code": "MAT-B",
                        "unit": "set",
                        "quantity": None,
                        "quantity_status": "reference_only",
                        "quantity_model": "D",
                        "requirement_id": "r2",
                        "provenance": "parent",
                    },
                ]
            }
        }
    )
    out = project_frozen_technical_materials(snap)
    assert out["entry_count"] == 2
    assert out["entries"][0]["quantity"] == 1.5
    assert out["entries"][0]["quantity_status"] == "derived"
    assert out["entries"][0]["variant_discriminator"] == "face_finish_type=oracal_651"
    assert "unit_price" not in out["entries"][0]
    assert out["entries"][1]["quantity"] is None
    assert out["entries"][1]["quantity_status_label_ro"] == "Referință (fără cantitate)"


def test_service_does_not_call_inventory_or_eic_heuristics():
    import services.technical_material_requirement_service as mod

    src = open(mod.__file__, encoding="utf-8").read()
    assert "from services.inventory" not in src
    assert "estimated_internal_cost_service" not in src
    assert "_estimate_material_quantity" not in src
    assert "import services.pricing" not in src
