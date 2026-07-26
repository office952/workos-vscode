"""Workflow-ADV Analyzer I/O contract — observe/propose only (no parser in WorkOS).

Analyzer observes and proposes.
Operator confirms.
Workflow-ADV owns Product Definition and Product Truth.
No price calculation in Analyzer.
No Product Truth authority in Analyzer.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

ANALYZER_IO_CONTRACT_VERSION = "workflow_adv_analyzer_io_contract_v1"

AnalyzerFieldSource = Literal["observed", "proposed"]
AnalyzerFieldCardinality = Literal["mandatory", "optional"]


class AnalyzerIoFieldSpecV1(BaseModel):
    field_id: str
    cardinality: AnalyzerFieldCardinality = "optional"
    unit: Optional[str] = None
    source: AnalyzerFieldSource = "observed"
    confidence_required: bool = False
    confirmation_required: bool = True
    destination: list[str] = Field(default_factory=list)
    consumer_templates: list[str] = Field(default_factory=list)
    quantity_formula_usage: list[str] = Field(default_factory=list)
    rejection_rules: list[str] = Field(default_factory=list)
    notes_ro: Optional[str] = None


class AnalyzerIoHandoffPayloadV1(BaseModel):
    """Candidate payload shape from desktop Analyzer → Workflow-ADV / WorkOS consume."""

    contract_version: str = ANALYZER_IO_CONTRACT_VERSION
    document_id: str
    file_id: str
    file_type: Literal["svg", "dwg", "dxf", "other", "unknown"] = "unknown"
    unit: str = "mm"
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    bounding_box: Optional[dict[str, Any]] = None
    filled_area_m2: Optional[float] = None
    total_perimeter_m: Optional[float] = None
    cut_path_length_m: Optional[float] = None
    element_count: Optional[int] = None
    closed_contour_count: Optional[int] = None
    internal_hole_count: Optional[int] = None
    group_count: Optional[int] = None
    minimum_feature_mm: Optional[float] = None
    complexity_class: Optional[str] = None
    suggested_groups: list[dict[str, Any]] = Field(default_factory=list)
    suggested_roles: list[dict[str, Any]] = Field(default_factory=list)
    suggested_material_mappings: list[dict[str, Any]] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    observed_fields: dict[str, Any] = Field(default_factory=dict)
    proposed_fields: dict[str, Any] = Field(default_factory=dict)


class AnalyzerIoContractDocumentV1(BaseModel):
    contract_version: str = ANALYZER_IO_CONTRACT_VERSION
    boundary_ro: str = (
        "Analyzer observă și propune. Operatorul confirmă. "
        "Workflow-ADV deține Product Definition și Product Truth. "
        "Fără calcul de preț în Analyzer. Fără autoritate Product Truth în Analyzer. "
        "WorkOS nu parsează SVG/DWG/DXF."
    )
    related_artwork_contract: str = "artwork_analysis_contract_v1"
    fields: list[AnalyzerIoFieldSpecV1] = Field(default_factory=list)
    example_payload: Optional[AnalyzerIoHandoffPayloadV1] = None
    do_not: list[str] = Field(
        default_factory=lambda: [
            "parse_svg_in_workos",
            "write_product_truth_from_analyzer",
            "calculate_price_in_analyzer",
            "auto_confirm_proposals",
        ]
    )


def build_analyzer_io_contract_document() -> AnalyzerIoContractDocumentV1:
    vl = ["TPL-VOLUMETRIC-LETTERS_v2"]
    fields = [
        AnalyzerIoFieldSpecV1(
            field_id="document_id",
            cardinality="mandatory",
            source="observed",
            confirmation_required=False,
            destination=["provenance"],
            rejection_rules=["empty_document_id"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="file_id",
            cardinality="mandatory",
            source="observed",
            confirmation_required=False,
            destination=["provenance"],
            rejection_rules=["empty_file_id"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="file_type",
            cardinality="mandatory",
            source="observed",
            confirmation_required=False,
            destination=["provenance"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="unit",
            cardinality="mandatory",
            unit="enum",
            source="observed",
            confirmation_required=True,
            destination=["product_definition", "quantity_compiler"],
            consumer_templates=vl,
            rejection_rules=["unit_not_mm_without_conversion"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="width_mm",
            cardinality="mandatory",
            unit="mm",
            source="observed",
            confidence_required=True,
            confirmation_required=True,
            destination=["product_definition", "product_truth", "quantity_compiler"],
            consumer_templates=vl,
            quantity_formula_usage=["width_mm"],
            rejection_rules=["width_mm <= 0"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="height_mm",
            cardinality="mandatory",
            unit="mm",
            source="observed",
            confidence_required=True,
            confirmation_required=True,
            destination=["product_definition", "product_truth", "quantity_compiler"],
            consumer_templates=vl,
            quantity_formula_usage=["height_mm"],
            rejection_rules=["height_mm <= 0"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="bounding_box",
            cardinality="optional",
            unit="mm",
            source="observed",
            confirmation_required=True,
            destination=["product_definition"],
            consumer_templates=vl,
        ),
        AnalyzerIoFieldSpecV1(
            field_id="filled_area_m2",
            cardinality="mandatory",
            unit="m2",
            source="observed",
            confidence_required=True,
            confirmation_required=True,
            destination=["product_definition", "product_truth", "quantity_compiler", "cost_recipe"],
            consumer_templates=vl,
            quantity_formula_usage=["letter_face_area_m2"],
            rejection_rules=["filled_area_m2 <= 0"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="total_perimeter_m",
            cardinality="mandatory",
            unit="m",
            source="observed",
            confidence_required=True,
            confirmation_required=True,
            destination=[
                "product_definition",
                "product_truth",
                "child_template_input",
                "quantity_compiler",
                "cost_recipe",
            ],
            consumer_templates=vl + ["TPL-VOLUM-ALUMINIU_v1"],
            quantity_formula_usage=["letter_perimeter_m", "return_profile_ml"],
            rejection_rules=["total_perimeter_m <= 0"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="cut_path_length_m",
            cardinality="optional",
            unit="m",
            source="observed",
            confirmation_required=True,
            destination=["quantity_compiler", "cost_recipe"],
            consumer_templates=vl,
            quantity_formula_usage=["cut_path_length_m"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="element_count",
            cardinality="mandatory",
            unit="count",
            source="observed",
            confirmation_required=True,
            destination=["product_definition", "product_truth", "quantity_compiler"],
            consumer_templates=vl,
            quantity_formula_usage=["letter_count"],
            rejection_rules=["element_count < 1"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="closed_contour_count",
            cardinality="optional",
            unit="count",
            source="observed",
            confirmation_required=True,
            destination=["product_definition"],
            consumer_templates=vl,
        ),
        AnalyzerIoFieldSpecV1(
            field_id="internal_hole_count",
            cardinality="optional",
            unit="count",
            source="observed",
            confirmation_required=True,
            destination=["product_definition", "quantity_compiler"],
            consumer_templates=vl,
        ),
        AnalyzerIoFieldSpecV1(
            field_id="group_count",
            cardinality="optional",
            unit="count",
            source="observed",
            confirmation_required=True,
            destination=["product_definition"],
            consumer_templates=vl,
        ),
        AnalyzerIoFieldSpecV1(
            field_id="minimum_feature_mm",
            cardinality="optional",
            unit="mm",
            source="observed",
            confirmation_required=True,
            destination=["readiness"],
            consumer_templates=vl,
            rejection_rules=["minimum_feature_mm below manufacturable threshold → warn"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="complexity_class",
            cardinality="optional",
            source="proposed",
            confirmation_required=True,
            destination=["product_definition"],
            consumer_templates=vl,
            notes_ro="Propunere — nu scrie Product Truth.",
        ),
        AnalyzerIoFieldSpecV1(
            field_id="suggested_groups",
            cardinality="optional",
            source="proposed",
            confirmation_required=True,
            destination=["product_definition"],
            consumer_templates=vl,
            rejection_rules=["auto_mix_by_layer_and_color_forbidden"],
            notes_ro="Operator declară by_layer sau by_color; Analyzer nu amestecă metode.",
        ),
        AnalyzerIoFieldSpecV1(
            field_id="suggested_roles",
            cardinality="optional",
            source="proposed",
            confirmation_required=True,
            destination=["product_definition", "child_template_input"],
            consumer_templates=vl,
        ),
        AnalyzerIoFieldSpecV1(
            field_id="suggested_material_mappings",
            cardinality="optional",
            source="proposed",
            confirmation_required=True,
            destination=["product_definition"],
            consumer_templates=vl,
            rejection_rules=["mapping_must_not_set_inventory_unit_cost"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="confidence",
            cardinality="optional",
            unit="0..1",
            source="observed",
            confirmation_required=False,
            destination=["provenance"],
        ),
        AnalyzerIoFieldSpecV1(
            field_id="observed_fields",
            cardinality="optional",
            source="observed",
            confirmation_required=True,
            destination=["product_definition"],
            notes_ro="Bagă extensibilă — chei mapate la Form System field_id.",
        ),
        AnalyzerIoFieldSpecV1(
            field_id="proposed_fields",
            cardinality="optional",
            source="proposed",
            confirmation_required=True,
            destination=["product_definition"],
            notes_ro="Propuneri — necesită confirmare operator înainte de Product Truth.",
        ),
    ]
    example = AnalyzerIoHandoffPayloadV1(
        document_id="doc-demo-vl-001",
        file_id="file-demo-svg-001",
        file_type="svg",
        unit="mm",
        width_mm=1200.0,
        height_mm=400.0,
        bounding_box={"x0": 0, "y0": 0, "x1": 1200, "y1": 400},
        filled_area_m2=0.28,
        total_perimeter_m=6.4,
        cut_path_length_m=7.1,
        element_count=5,
        closed_contour_count=5,
        internal_hole_count=2,
        group_count=2,
        minimum_feature_mm=2.5,
        complexity_class="moderate",
        suggested_groups=[{"group_id": "g1", "method": "by_layer", "status": "proposed"}],
        suggested_roles=[{"role": "FACE", "entity_ids": ["e1"], "status": "proposed"}],
        suggested_material_mappings=[],
        confidence=0.86,
        observed_fields={
            "width_mm": 1200.0,
            "height_mm": 400.0,
            "letter_count": 5,
            "letter_perimeter_m": 6.4,
            "letter_face_area_m2": 0.28,
        },
        proposed_fields={"complexity_class": "moderate"},
    )
    return AnalyzerIoContractDocumentV1(fields=fields, example_payload=example)
