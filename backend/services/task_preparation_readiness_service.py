"""Preparation readiness gates — template, print/vinyl metadata (execution layer)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from services.volumetric_quote_input_policy import (
    MAT_MOUNTING_TEMPLATE_FOREX,
    normalize_face_finish_type,
    normalize_mounting_template_material_type,
)

CODE_VECTOR_PREP_NOT_DONE = "vector_prep_not_done"
CODE_TEMPLATE_PAPER_NO_CNC = "template_paper_no_cnc"
CODE_TEMPLATE_NONE_NO_CNC = "template_none_no_cnc"
CODE_TEMPLATE_FOREX_AREA_MISSING = "template_forex_area_missing"
CODE_TEMPLATE_DECISION_MISSING = "template_decision_missing"
CODE_VINYL_COLOR_MISSING = "vinyl_color_code_missing"
CODE_VINYL_ROLL_WIDTH_MISSING = "vinyl_roll_width_missing"

VECTOR_PREP_PROCESS_ID = "vector_prep"
MOUNTING_TEMPLATE_CNC_PROCESS_ID = "mounting_template_cnc_cut"
VINYL_APPLICATION_PROCESS_ID = "vinyl_application"

CNC_PROCESS_IDS_REQUIRING_VECTOR_PREP = frozenset(
    {
        "face_cnc_cut",
        "back_cut",
        "mounting_template_cnc_cut",
    }
)
CNC_MACHINE_TYPES_REQUIRING_VECTOR_PREP = frozenset({"CNC_ROUTER", "CNC"})


def extract_quote_input_from_snapshot(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return {}
    direct = snapshot.get("quote_input")
    if isinstance(direct, dict):
        return dict(direct)
    quote_snapshot = snapshot.get("quote_snapshot")
    if isinstance(quote_snapshot, dict):
        nested = quote_snapshot.get("quote_input")
        if isinstance(nested, dict):
            return dict(nested)
    return {}


def is_cnc_task_requiring_vector_prep(plan_task: Mapping[str, Any]) -> bool:
    process_id = str(plan_task.get("process_id") or "").strip().lower()
    machine_type = str(plan_task.get("machine_type") or "").strip().upper()
    if process_id in CNC_PROCESS_IDS_REQUIRING_VECTOR_PREP:
        return True
    if machine_type in CNC_MACHINE_TYPES_REQUIRING_VECTOR_PREP and process_id not in (
        "produce_order",
        "",
    ):
        return True
    return False


def evaluate_mounting_template_cnc_gate(
    quote_input: Mapping[str, Any] | None,
) -> List[dict[str, Any]]:
    """Gate mounting_template_cnc_cut by template type and Forex area."""
    qi = quote_input or {}
    material_type = normalize_mounting_template_material_type(qi)

    if material_type == "none":
        return [
            {
                "code": CODE_TEMPLATE_NONE_NO_CNC,
                "label": "Șablon montaj dezactivat",
                "blocking": True,
                "responsible_domain": "instrumentation",
                "missing_item": "mounting_template_material_type=none",
                "message": "Tip șablon none — debitarea CNC pentru șablon nu este necesară.",
            }
        ]

    if material_type == "paper":
        return [
            {
                "code": CODE_TEMPLATE_PAPER_NO_CNC,
                "label": "Șablon hârtie — fără CNC",
                "blocking": True,
                "responsible_domain": "instrumentation",
                "missing_item": "mounting_template_material_type=paper",
                "message": "Șablon hârtie — nu se debitează CNC (Forex).",
            }
        ]

    if material_type == "forex":
        area_raw = qi.get("mounting_template_area_m2")
        try:
            area = float(area_raw) if area_raw not in (None, "") else 0.0
        except (TypeError, ValueError):
            area = 0.0
        if area <= 0:
            return [
                {
                    "code": CODE_TEMPLATE_FOREX_AREA_MISSING,
                    "label": "Arie șablon Forex lipsă",
                    "blocking": True,
                    "responsible_domain": "instrumentation",
                    "missing_item": "mounting_template_area_m2",
                    "material_code": MAT_MOUNTING_TEMPLATE_FOREX,
                    "message": "Șablon Forex necesită mounting_template_area_m2 valid.",
                }
            ]
        return []

    return [
        {
            "code": CODE_TEMPLATE_DECISION_MISSING,
            "label": "Decizie tip șablon",
            "blocking": True,
            "responsible_domain": "instrumentation",
            "missing_item": "mounting_template_material_type",
            "message": "Așteaptă decizia tipului de șablon (paper / forex / none).",
        }
    ]


def evaluate_vinyl_application_gate(
    quote_input: Mapping[str, Any] | None,
) -> List[dict[str, Any]]:
    """Gate vinyl_application when quote_input exposes missing critical print metadata."""
    qi = quote_input or {}
    face = normalize_face_finish_type(qi.get("face_finish_type"))
    if face == "none":
        return []

    reasons: List[dict[str, Any]] = []
    color = str(qi.get("face_vinyl_color_code") or "").strip()
    if face in {"oracal_651", "printed_vinyl", "printed_laminated_vinyl"} and not color:
        reasons.append(
            {
                "code": CODE_VINYL_COLOR_MISSING,
                "label": "Culoare vinyl/print lipsă",
                "blocking": True,
                "responsible_domain": "print",
                "missing_item": "face_vinyl_color_code",
                "message": "Colantarea/printul necesită face_vinyl_color_code.",
            }
        )

    if face == "oracal_651":
        roll = qi.get("face_vinyl_roll_width_mm")
        if roll not in (1000, 1260):
            reasons.append(
                {
                    "code": CODE_VINYL_ROLL_WIDTH_MISSING,
                    "label": "Lățime rolă vinyl lipsă",
                    "blocking": True,
                    "responsible_domain": "print",
                    "missing_item": "face_vinyl_roll_width_mm",
                    "message": "Oracal 651 necesită face_vinyl_roll_width_mm (1000 sau 1260).",
                }
            )
    return reasons


def classify_predecessor_readiness_status(
    blocking_reasons: List[dict],
    plan_by_id: Mapping[str, dict],
) -> Optional[str]:
    """Map unsatisfied vector_prep predecessor to waiting_file."""
    from services.task_readiness_service import READINESS_WAITING_FILE

    for reason in blocking_reasons:
        task_id = str(reason.get("task_id") or reason.get("depends_on_task_id") or "")
        plan_task = plan_by_id.get(task_id) or {}
        if str(plan_task.get("process_id") or "").strip().lower() == VECTOR_PREP_PROCESS_ID:
            return READINESS_WAITING_FILE
    return None
