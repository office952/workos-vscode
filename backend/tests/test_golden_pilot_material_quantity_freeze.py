"""Golden Pilot — material quantity freeze + Quote→Order semantic + projection."""

from __future__ import annotations

import json
from types import SimpleNamespace

from schemas.product_aggregate import ProductAggregate, ProductAggregateMaterial
from services.ops_graph_frozen_technical_materials import (
    project_frozen_technical_materials,
)
from services.order_snapshot_v2_convert_service import _component_scope_fields_from_quote
from services.technical_material_requirement_service import (
    apply_technical_material_requirements,
)


def _materials_wrap_and_refs() -> list[ProductAggregateMaterial]:
    return [
        ProductAggregateMaterial(
            material_code="MAT-PROFIL-LATERAL-LITERE-60MM",
            label="Profil lateral 60mm",
            unit="ml",
            component_ref="comp_volum",
            formula_id="return_profile_linear_meter",
            formula_params={"gate": {"return_depth_mm": 60}},
            provenance="linked_module",
            source_template_code="TPL-VOLUM",
        ),
        ProductAggregateMaterial(
            material_code="MAT-ORACAL-651",
            label="Folie wrap cant",
            unit="mp",
            component_ref="comp_volum",
            formula_id="return_wrap_area",
            formula_params={"gate": {"return_finish_type": "oracal_wrapped"}},
            provenance="linked_module",
            source_template_code="TPL-VOLUM",
        ),
        ProductAggregateMaterial(
            material_code="MAT-VOPSEA-RAL",
            label="Vopsea RAL",
            unit="buc",
            component_ref="comp_volum",
            formula_id="return_paint_consumption",
            formula_params={"gate": {"return_finish_type": "ral_paint"}},
            provenance="linked_module",
            source_template_code="TPL-VOLUM",
        ),
        ProductAggregateMaterial(
            material_code="MAT-CONSUMABILE",
            label="Consumabile",
            unit="set",
            component_ref="comp_finish",
            formula_id=None,
            provenance="parent",
            source_template_code="TPL-PARENT",
        ),
        ProductAggregateMaterial(
            material_code="MAT-ORACAL-651",
            label="Folie față",
            unit="mp",
            component_ref="comp_face",
            formula_id="letter_face_area",
            provenance="parent",
            source_template_code="TPL-PARENT",
        ),
    ]


def test_golden_pilot_statuses_and_no_default_depth():
    agg = ProductAggregate(
        template_id=1,
        template_code="TPL-TEST",
        business_name_ro="Test",
        materials=_materials_wrap_and_refs(),
    )
    wrap = apply_technical_material_requirements(
        agg,
        {
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 60,
            "letter_perimeter_m": 10.0,
            "letter_face_area_m2": 2.0,
            "face_finish_type": "oracal_651",
        },
    )
    by_code_prov = {
        (m.material_code, m.provenance): m for m in wrap.materials
    }
    assert "MAT-VOPSEA-RAL" not in {m.material_code for m in wrap.materials}
    profile = by_code_prov[("MAT-PROFIL-LATERAL-LITERE-60MM", "linked_module")]
    assert profile.quantity == 10.0
    assert profile.quantity_status == "derived"
    wrap_mat = by_code_prov[("MAT-ORACAL-651", "linked_module")]
    assert wrap_mat.quantity == 0.84
    assert wrap_mat.quantity_status == "derived"
    face = by_code_prov[("MAT-ORACAL-651", "parent")]
    assert face.quantity == 2.0
    assert face.quantity_status == "derived"
    ref = by_code_prov[("MAT-CONSUMABILE", "parent")]
    assert ref.quantity is None
    assert ref.quantity_status == "reference_only"

    missing_depth = apply_technical_material_requirements(
        agg,
        {
            "return_finish_type": "oracal_wrapped",
            "letter_perimeter_m": 10.0,
            "letter_face_area_m2": 2.0,
            "face_finish_type": "oracal_651",
        },
    )
    wrap_null = next(
        m
        for m in missing_depth.materials
        if m.material_code == "MAT-ORACAL-651" and m.provenance == "linked_module"
    )
    assert wrap_null.quantity is None
    assert wrap_null.quantity_status == "source_missing"

    paint = apply_technical_material_requirements(
        agg,
        {"return_finish_type": "ral_paint", "return_depth_mm": 60, "letter_perimeter_m": 10.0},
    )
    paint_row = next(m for m in paint.materials if m.material_code == "MAT-VOPSEA-RAL")
    assert paint_row.quantity is None
    assert paint_row.quantity_status == "source_missing"
    assert paint_row.quantity != 0


def test_quote_to_order_materials_copied_verbatim_and_projected():
    agg = ProductAggregate(
        template_id=1,
        template_code="TPL-TEST",
        business_name_ro="Test",
        materials=_materials_wrap_and_refs(),
    )
    frozen = apply_technical_material_requirements(
        agg,
        {
            "return_finish_type": "oracal_wrapped",
            "return_depth_mm": 60,
            "letter_perimeter_m": 10.0,
            "letter_face_area_m2": 2.0,
            "face_finish_type": "oracal_651",
        },
    )
    pa = frozen.model_dump(mode="json")
    quote = SimpleNamespace(
        product_aggregate_snapshot=pa,
        offer_scope_snapshot=None,
        active_scope_snapshot=None,
        component_instances=[],
        component_scope_version="component_scope/v1",
        geometry_input_snapshot=None,
    )
    order_fields = _component_scope_fields_from_quote(quote)
    assert order_fields["product_aggregate_snapshot"]["materials"] == pa["materials"]
    snap_json = json.dumps(
        {"product_aggregate_snapshot": order_fields["product_aggregate_snapshot"]}
    )
    proj = project_frozen_technical_materials(snap_json)
    assert proj["semantic_note"].startswith("Necesar tehnic înghețat")
    statuses = {e["quantity_status"] for e in proj["entries"]}
    assert "derived" in statuses
    assert "reference_only" in statuses
    assert all(e["quantity"] != 0 or e["quantity_status"] == "derived" for e in proj["entries"])
    nulls = [e for e in proj["entries"] if e["quantity"] is None]
    assert all(e["quantity_status"] != "derived" for e in nulls)
    assert any(e["quantity_status_label_ro"] == "Calculată" for e in proj["entries"])
    assert any(e["quantity_status_label_ro"] == "De referință" for e in proj["entries"])
    oracal_rows = [e for e in proj["entries"] if e["material_code"] == "MAT-ORACAL-651"]
    assert len(oracal_rows) == 2
