"""Artwork complexity assessments from persisted SVG analysis — classification preview only."""

from __future__ import annotations

from typing import Any, Literal

from schemas.intake_v4 import IntakeV4CncOperationRow, IntakeV4MaterialBreakdownWarning

ArtworkRecommendedApplication = Literal["vinyl_cut", "print_on_vinyl_laminated", "manual_review"]


def read_artwork_complexity_block(payload_raw: dict[str, Any]) -> dict[str, Any]:
    analysis = payload_raw.get("svg_analysis_json") or {}
    if not isinstance(analysis, dict):
        return {}
    block = analysis.get("artworkComplexity") or {}
    return block if isinstance(block, dict) else {}


def list_artwork_complexity_assessments(payload_raw: dict[str, Any]) -> list[dict[str, Any]]:
    block = read_artwork_complexity_block(payload_raw)
    rows = block.get("assessments") or []
    return [row for row in rows if isinstance(row, dict)]


def operator_artwork_application_map(payload_raw: dict[str, Any]) -> dict[str, str]:
    finish = payload_raw.get("finish_setup") or {}
    if not isinstance(finish, dict):
        return {}
    decisions = finish.get("artwork_complexity_decisions") or []
    mapping: dict[str, str] = {}
    for row in decisions:
        if not isinstance(row, dict):
            continue
        artwork_id = str(row.get("artwork_id") or "").strip()
        application = str(row.get("operator_application") or "").strip()
        if artwork_id and application:
            mapping[artwork_id] = application
    return mapping


def effective_artwork_application(
    assessment: dict[str, Any],
    operator_map: dict[str, str],
) -> ArtworkRecommendedApplication:
    artwork_id = str(assessment.get("artwork_id") or "")
    operator = operator_map.get(artwork_id)
    if operator in {"vinyl_cut", "print_on_vinyl_laminated", "manual_review"}:
        return operator
    recommended = str(assessment.get("recommended_application") or "manual_review")
    if recommended in {"vinyl_cut", "print_on_vinyl_laminated", "manual_review"}:
        return recommended
    return "manual_review"


def append_artwork_complexity_warnings(
    assessments: list[dict[str, Any]],
    warnings: list[IntakeV4MaterialBreakdownWarning],
) -> None:
    for item in assessments:
        artwork_id = str(item.get("artwork_id") or "artwork")
        for code in item.get("warnings") or []:
            if not isinstance(code, str) or not code.strip():
                continue
            warnings.append(
                IntakeV4MaterialBreakdownWarning(
                    code=code,
                    message=_warning_message(code),
                    source=f"artwork_complexity:{artwork_id}",
                    severity="warning",
                )
            )


def _warning_message(code: str) -> str:
    messages = {
        "external_image_detected": "External raster image reference detected in SVG.",
        "missing_external_image_asset": "External image asset must be provided for production.",
        "raster_image_not_attached_to_production_geometry": "Raster image is not attached to production geometry.",
        "raster_artwork_area_approximated_by_covered_vector_geometry": "Print area approximated from covered vector geometry.",
    }
    return messages.get(code, code.replace("_", " "))


def build_artwork_print_operation_preview_rows(
    assessment: dict[str, Any],
    key_prefix: str,
    display_suffix: str,
    area_m2: float,
) -> list[IntakeV4CncOperationRow]:
    return [
        IntakeV4CncOperationRow(
            key=f"{key_prefix}_print_vinyl_op",
            display_name=f"Serviciu print — {display_suffix}",
            operation_type="print_vinyl",
            quantity=area_m2,
            unit="m2",
            basis_key="print_area",
            basis_label="Print area (artwork complexity)",
            pricing_status="missing_rate",
            estimated_cost=None,
            tpl_operation_key="PRINT_SOLVENT",
            operation_catalog_key="print_vinyl_artwork",
            resource_mapping_status="pending_mapping",
            mapping_gaps=["artwork_complexity_preview"],
            consumes_stock_now=False,
        ),
        IntakeV4CncOperationRow(
            key=f"{key_prefix}_laminate_op",
            display_name=f"Serviciu laminare X-PRO — {display_suffix}",
            operation_type="lamination",
            quantity=area_m2,
            unit="m2",
            basis_key="laminate_area",
            basis_label="Laminate area (artwork complexity)",
            pricing_status="missing_rate",
            estimated_cost=None,
            tpl_operation_key="LAMINATION",
            operation_catalog_key="lamination",
            resource_mapping_status="pending_mapping",
            mapping_gaps=["artwork_complexity_preview"],
            consumes_stock_now=False,
        ),
        IntakeV4CncOperationRow(
            key=f"{key_prefix}_apply_printed_vinyl_op",
            display_name=f"Serviciu aplicare — {display_suffix}",
            operation_type="vinyl_application",
            quantity=area_m2,
            unit="m2",
            basis_key="apply_area",
            basis_label="Apply printed vinyl (artwork complexity)",
            pricing_status="missing_rate",
            estimated_cost=None,
            tpl_operation_key="APPLY_VINYL",
            operation_catalog_key="vinyl_application",
            resource_mapping_status="pending_mapping",
            mapping_gaps=["artwork_complexity_preview"],
            consumes_stock_now=False,
        ),
    ]
