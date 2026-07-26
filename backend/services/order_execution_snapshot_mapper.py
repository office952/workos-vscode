"""
Order execution snapshot mapper — normalizes quote-derived product_definition
layers for the strict execution plan gate contract (BLK-08 canonical task types).

Applied at order conversion only. Does NOT recalculate costs or weaken gate rules.
Maps priced operation codes (CostEngine v2 component_breakdown) and legacy
ProductSystem process types to the 20-value CANONICAL_TASK_TYPES enum.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from services.volumetric_execution_dispatch import enrich_operation_time_index_from_breakdown

from data_models.product_contracts import ProductDefinition, ProductLayer, ProductProcess

# Mirror execution_plan_gate_service.CANONICAL_TASK_TYPES — no import to avoid
# coupling gate static-analysis paths to conversion-time normalization.
_CANONICAL_TASK_TYPES = frozenset(
    {
        "file_preparation",
        "cnc_routing",
        "laser_cutting",
        "print_large_format",
        "laminating",
        "vinyl_cutting",
        "edge_bending",
        "plexi_cutting",
        "welding",
        "led_assembly",
        "led_wiring",
        "power_testing",
        "volumetric_letter_assembly",
        "casette_assembly",
        "final_assembly",
        "packaging",
        "installation_prep",
        "installation_onsite",
        "quality_control",
        "measurement",
    }
)

# TPL-VOLUMETRIC-LETTERS priced operation codes → canonical task_type.
# Aligned with seed_tpl_volumetric_letters_dossier _task_rules() semantics.
_OPERATION_CODE_TO_CANONICAL: Dict[str, str] = {
    "vector_prep": "file_preparation",
    "face_cnc_cut": "cnc_routing",
    "back_cut": "cnc_routing",
    "mounting_template_cnc_cut": "cnc_routing",
    "side_forming": "edge_bending",
    "return_face_bonding": "volumetric_letter_assembly",
    "painting": "volumetric_letter_assembly",
    "vinyl_application": "vinyl_cutting",
    "led_install_letters": "led_assembly",
    "electrical_letters": "led_wiring",
    "assembly_letters": "volumetric_letter_assembly",
    "qc_letters": "quality_control",
    "packaging_letters": "packaging",
    "cut_acm_panel": "cnc_routing",
    "v_groove_router": "cnc_routing",
    "fold_cassette": "casette_assembly",
    "mount_acm_panel": "installation_prep",
}

# Legacy ProductSystem _build_layers heuristics → canonical task_type.
_LEGACY_PROCESS_TYPE_TO_CANONICAL: Dict[str, str] = {
    "prepress": "file_preparation",
    "cnc": "cnc_routing",
    "cut": "cnc_routing",
    "print": "print_large_format",
    "assembly": "final_assembly",
    "wiring": "led_wiring",
    "painting": "volumetric_letter_assembly",
    "vinyl_application": "vinyl_cutting",
    "packaging": "packaging",
    "qc_inspection": "quality_control",
    "return_profile_machine_forming": "edge_bending",
    "return_profile_face_bonding": "volumetric_letter_assembly",
}


def resolve_canonical_task_type(*, process_id: str, legacy_type: str) -> Optional[str]:
    """Map a process to a canonical task_type, or None when unmappable."""
    code_key = (process_id or "").strip().lower()
    if code_key in _OPERATION_CODE_TO_CANONICAL:
        return _OPERATION_CODE_TO_CANONICAL[code_key]

    type_key = (legacy_type or "").strip().lower()
    if type_key in _CANONICAL_TASK_TYPES:
        return type_key
    if type_key in _LEGACY_PROCESS_TYPE_TO_CANONICAL:
        return _LEGACY_PROCESS_TYPE_TO_CANONICAL[type_key]

    return None


def _build_operation_time_index(
    component_breakdown: Optional[List[Dict[str, Any]]],
) -> Dict[str, float]:
    """Index priced operation estimated minutes from CostEngine v2 breakdown."""
    index: Dict[str, float] = {}
    if not component_breakdown:
        return index
    for comp in component_breakdown:
        if not isinstance(comp, dict):
            continue
        for op in comp.get("operations_detail") or []:
            if not isinstance(op, dict):
                continue
            code = op.get("code")
            if not isinstance(code, str) or not code.strip():
                continue
            mins = op.get("estimated_minutes")
            hours = op.get("hours")
            derived = 0.0
            if isinstance(mins, (int, float)) and not isinstance(mins, bool) and float(mins) > 0:
                derived = float(mins)
            elif isinstance(hours, (int, float)) and not isinstance(hours, bool) and float(hours) > 0:
                derived = float(hours) * 60.0
            if derived > 0:
                index[code.strip().lower()] = derived
    return enrich_operation_time_index_from_breakdown(index, component_breakdown)


def normalize_product_definition_for_execution(
    product_definition: ProductDefinition,
    *,
    component_breakdown: Optional[List[Dict[str, Any]]] = None,
) -> ProductDefinition:
    """Return a copy of product_definition with execution-ready process types.

    - Remaps non-canonical process.type values using operation code + legacy type.
    - Enriches estimated_time_minutes from component_breakdown when still zero.
    - Leaves already-canonical types unchanged.
    """
    pd = copy.deepcopy(product_definition)
    op_times = _build_operation_time_index(component_breakdown)

    normalized_layers: List[ProductLayer] = []
    for layer in pd.layers:
        normalized_processes: List[ProductProcess] = []
        for proc in layer.processes:
            canonical = resolve_canonical_task_type(
                process_id=proc.process_id,
                legacy_type=proc.type,
            )
            est = float(proc.estimated_time_minutes or 0)
            if est <= 0:
                code_key = (proc.process_id or "").strip().lower()
                est = op_times.get(code_key, est)

            normalized_processes.append(
                ProductProcess(
                    process_id=proc.process_id,
                    type=canonical if canonical is not None else proc.type,
                    machine_type=proc.machine_type,
                    estimated_time_minutes=est,
                )
            )
        normalized_layers.append(
            ProductLayer(
                layer_id=layer.layer_id,
                layer_type=layer.layer_type,
                material=layer.material,
                thickness_mm=layer.thickness_mm,
                finish=layer.finish,
                components=layer.components,
                processes=normalized_processes,
            )
        )

    pd.layers = normalized_layers
    return pd
