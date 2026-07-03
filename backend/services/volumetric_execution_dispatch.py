"""
Volumetric execution dispatch helpers — TPL-VOLUMETRIC-LETTERS.

Read-only enrichment for order → execution plan → operator visibility:
  - Romanian display labels from stable process_id keys
  - Template-aligned scheduling minutes when priced breakdown lists an op
    but CostEngine stored line_total without explicit minutes (no formula change)
  - Compact snapshot context for operator/tablet payloads
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

# Stable process_id → operator-facing Romanian label.
VOLUMETRIC_PROCESS_LABELS_RO: Dict[str, str] = {
    "vector_prep": "Verificare grafică / vectorizare",
    "face_cnc_cut": "Debitare față plexiglas (inclusiv șanfren)",
    "back_cut": "Debitare spate Forex",
    "side_forming": "Modelare canturi litere volumetrice",
    "return_face_bonding": "Lipire canturi pe fețele literelor",
    "return_vinyl_application": "Colantare cant",
    "vinyl_application": "Colantare fețe litere",
    "led_install_letters": "Montaj LED",
    "electrical_letters": "Cablare / surse",
    "mounting_template_cnc_cut": "Pregătire montaj / bare / șablon",
    "painting": "Protejare față, vopsire cant litere și îndepărtare protecție după uscare",
    "assembly_letters": "Asamblare litere volumetrice",
    "qc_letters": "Verificare finală lucrare",
    "packaging_letters": "Infoliere cu folie stretch și pregătire colet pentru livrare / montaj",
}

# Template-seed aligned scheduling defaults (minutes) — used only when a priced
# operation appears in component_breakdown but lacks explicit timing fields.
VOLUMETRIC_PRICED_OP_SCHEDULING_MINUTES: Dict[str, float] = {
    "vector_prep": 15.0,
    "face_cnc_cut": 45.0,
    "return_vinyl_application": 20.0,
    "vinyl_application": 20.0,
    "side_forming": 30.0,
    "return_face_bonding": 25.0,
    "back_cut": 40.0,
    "led_install_letters": 30.0,
    "electrical_letters": 20.0,
    "mounting_template_cnc_cut": 25.0,
    "painting": 15.0,
    "assembly_letters": 60.0,
    "qc_letters": 15.0,
    "packaging_letters": 10.0,
}

CANONICAL_PROCESS_LABELS_RO: Dict[str, str] = {
    "file_preparation": "Pregătire fișier",
    "cnc_routing": "Debitare CNC",
    "edge_bending": "Modelare cant",
    "welding": "Lipire / sudură",
    "vinyl_cutting": "Colantare / vinyl",
    "led_assembly": "Montaj LED",
    "led_wiring": "Cablare / surse",
    "volumetric_letter_assembly": "Asamblare litere",
    "quality_control": "Verificare finală lucrare",
    "packaging": "Infoliere cu folie stretch și pregătire colet pentru livrare / montaj",
    "produce_order": "Producție comandă",
}


def resolve_execution_task_display_name(
    *,
    process_id: str,
    process_type: str,
    product_id: Optional[str] = None,
) -> str:
    """Return operator-facing task label; keep process_id/type as stable keys elsewhere."""
    code_key = (process_id or "").strip().lower()
    if code_key in VOLUMETRIC_PROCESS_LABELS_RO:
        return VOLUMETRIC_PROCESS_LABELS_RO[code_key]

    type_key = (process_type or "").strip().lower()
    if type_key in CANONICAL_PROCESS_LABELS_RO:
        return CANONICAL_PROCESS_LABELS_RO[type_key]

    if product_id and "VOLUMETRIC" in product_id.upper() and code_key:
        return code_key.replace("_", " ")

    if type_key and code_key:
        return f"{type_key} — {code_key}"
    return process_type or process_id or "Task producție"


def enrich_operation_time_index_from_breakdown(
    index: Dict[str, float],
    component_breakdown: Optional[List[Dict[str, Any]]],
) -> Dict[str, float]:
    """Fill missing minutes for priced volumetric ops listed in breakdown."""
    if not component_breakdown:
        return index

    enriched = dict(index)
    priced_codes: set[str] = set()

    for comp in component_breakdown:
        if not isinstance(comp, dict):
            continue
        for op in comp.get("operations_detail") or []:
            if not isinstance(op, dict):
                continue
            code = op.get("code")
            if not isinstance(code, str) or not code.strip():
                continue
            code_key = code.strip().lower()
            if enriched.get(code_key, 0) > 0:
                continue

            mins = op.get("estimated_minutes")
            hours = op.get("hours")
            minutes_alt = op.get("minutes")
            derived = 0.0
            if isinstance(mins, (int, float)) and not isinstance(mins, bool) and float(mins) > 0:
                derived = float(mins)
            elif isinstance(minutes_alt, (int, float)) and not isinstance(minutes_alt, bool) and float(minutes_alt) > 0:
                derived = float(minutes_alt)
            elif isinstance(hours, (int, float)) and not isinstance(hours, bool) and float(hours) > 0:
                derived = float(hours) * 60.0

            if derived > 0:
                enriched[code_key] = derived
                continue

            line_total = op.get("line_total")
            if isinstance(line_total, (int, float)) and not isinstance(line_total, bool) and float(line_total) > 0:
                priced_codes.add(code_key)

    for code_key in priced_codes:
        if enriched.get(code_key, 0) > 0:
            continue
        fallback = VOLUMETRIC_PRICED_OP_SCHEDULING_MINUTES.get(code_key)
        if fallback and fallback > 0:
            enriched[code_key] = fallback

    return enriched


def parse_snapshot_dict(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def extract_order_snapshot_context(
    snapshot_raw: Any,
    *,
    client_name: str = "",
    quote_code: str = "",
    intake_code: str = "",
) -> Dict[str, Any]:
    """Compact read-only context from frozen order snapshot for operator payloads."""
    snapshot = parse_snapshot_dict(snapshot_raw)
    pd = snapshot.get("product_definition") if isinstance(snapshot.get("product_definition"), dict) else {}
    qs = snapshot.get("quote_snapshot") if isinstance(snapshot.get("quote_snapshot"), dict) else {}

    product_id = str(pd.get("product_id") or qs.get("product_id") or "")
    product_type = str(pd.get("product_type") or "")

    layer_context: List[Dict[str, Any]] = []
    layers = pd.get("layers") if isinstance(pd.get("layers"), list) else []
    for layer in layers[:4]:
        if not isinstance(layer, dict):
            continue
        material = layer.get("material") if isinstance(layer.get("material"), dict) else {}
        layer_context.append(
            {
                "layer_id": layer.get("layer_id"),
                "material": material.get("name") or material.get("material_id") or "",
                "finish": layer.get("finish") or "",
                "thickness_mm": layer.get("thickness_mm"),
            }
        )

    return {
        "client": client_name or "",
        "product": product_type or product_id or "",
        "product_template": product_id,
        "quote_code": quote_code or "",
        "intake_code": intake_code or "",
        "layer_context": layer_context,
        "work_intake_v2": bool(intake_code),
    }
