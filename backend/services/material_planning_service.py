"""Material planning hints — read-only derived view for execution orders."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

CATEGORY_PROJECT_CRITICAL = "project_critical"
CATEGORY_STANDARD_LOW_COST = "standard_low_cost_stock"
CATEGORY_INDIRECT = "indirect_consumable"
CATEGORY_INTERNAL_SEMIFINISHED = "internal_semifinished_output"

POLICY_VERIFY_BEFORE_START = "verify_before_start"
POLICY_KEEP_MIN_STOCK = "keep_min_stock"
POLICY_CHECKLIST_ONLY = "checklist_only"
POLICY_BUY_AFTER_ADVANCE = "buy_after_advance"
POLICY_OPERATOR_DECISION = "operator_decision_required"

IMPACT_CAN_BLOCK = "can_block_if_missing"
IMPACT_SUGGEST_REPLENISH = "suggest_replenishment"
IMPACT_CHECKLIST_ONLY = "checklist_only"
IMPACT_HANDLED_BY_DEPENDENCY = "handled_by_dependency"
IMPACT_NO_TASK_BLOCK = "no_task_block"

CONFIDENCE_ESTIMATED = "estimated"
SOURCE_TEMPLATE_RULE = "template_rule"

VOLUMETRIC_TEMPLATE = "TPL-VOLUMETRIC-LETTERS"

VOLUMETRIC_PROCESS_IDS = frozenset(
    {
        "face_cnc_cut",
        "side_forming",
        "return_face_bonding",
        "back_cut",
        "led_install_letters",
        "electrical_letters",
        "mounting_template_cnc_cut",
        "assembly_letters",
        "qc_letters",
        "packaging_letters",
    }
)

# process_id → list of item templates (task_id resolved at derive time)
VOLUMETRIC_PROCESS_MATERIAL_RULES: Dict[str, List[Dict[str, Any]]] = {
    "face_cnc_cut": [
        {
            "code": "PLEXI_FACE",
            "name": "Plexiglas față",
            "category": CATEGORY_PROJECT_CRITICAL,
            "unit": "mp",
            "planning_policy": POLICY_VERIFY_BEFORE_START,
            "procurement_policy": POLICY_BUY_AFTER_ADVANCE,
            "readiness_impact": IMPACT_CAN_BLOCK,
            "display_note": "Verifică plexiglasul pentru fețele literelor.",
        },
    ],
    "side_forming": [
        {
            "code": "ALU_RETURN_PROFILE",
            "name": "Cant aluminiu pentru litere volumetrice",
            "category": CATEGORY_PROJECT_CRITICAL,
            "unit": "ml",
            "planning_policy": POLICY_VERIFY_BEFORE_START,
            "procurement_policy": POLICY_OPERATOR_DECISION,
            "readiness_impact": IMPACT_CAN_BLOCK,
            "display_note": "Verifică adâncimea, culoarea și cantitatea de cant aluminiu.",
        },
    ],
    "return_face_bonding": [
        {
            "code": "ASSEMBLY_ADHESIVE",
            "name": "Adeziv / lipire cant",
            "category": CATEGORY_STANDARD_LOW_COST,
            "unit": "set",
            "planning_policy": POLICY_KEEP_MIN_STOCK,
            "procurement_policy": POLICY_OPERATOR_DECISION,
            "readiness_impact": IMPACT_SUGGEST_REPLENISH,
            "display_note": "Verifică adezivul și consumabilele de lipire.",
        },
    ],
    "back_cut": [
        {
            "code": "FOREX_BACKING_10MM",
            "name": "Forex 10 mm pentru spate",
            "category": CATEGORY_PROJECT_CRITICAL,
            "unit": "mp",
            "planning_policy": POLICY_VERIFY_BEFORE_START,
            "procurement_policy": POLICY_BUY_AFTER_ADVANCE,
            "readiness_impact": IMPACT_CAN_BLOCK,
            "display_note": "Verifică Forex 10 mm pentru spatele literelor.",
        },
    ],
    "led_install_letters": [
        {
            "code": "LED_MODULE",
            "name": "Module LED",
            "category": CATEGORY_PROJECT_CRITICAL,
            "unit": "buc",
            "planning_policy": POLICY_VERIFY_BEFORE_START,
            "procurement_policy": POLICY_BUY_AFTER_ADVANCE,
            "readiness_impact": IMPACT_CAN_BLOCK,
            "display_note": "Verifică disponibilitatea modulelor LED înainte de montaj.",
        },
        {
            "code": "LED_FIXING_CONSUMABLES",
            "name": "Consumabile fixare LED",
            "category": CATEGORY_STANDARD_LOW_COST,
            "unit": "set",
            "planning_policy": POLICY_KEEP_MIN_STOCK,
            "procurement_policy": POLICY_OPERATOR_DECISION,
            "readiness_impact": IMPACT_SUGGEST_REPLENISH,
            "display_note": "Verifică consumabilele de fixare LED.",
        },
    ],
    "electrical_letters": [
        {
            "code": "LED_POWER_SUPPLY",
            "name": "Surse LED",
            "category": CATEGORY_PROJECT_CRITICAL,
            "unit": "buc",
            "planning_policy": POLICY_VERIFY_BEFORE_START,
            "procurement_policy": POLICY_BUY_AFTER_ADVANCE,
            "readiness_impact": IMPACT_CAN_BLOCK,
            "display_note": "Verifică sursele LED înainte de cablare.",
        },
        {
            "code": "ELECTRICAL_CONSUMABLES",
            "name": "Cablu / conectori / cleme",
            "category": CATEGORY_STANDARD_LOW_COST,
            "unit": "set",
            "planning_policy": POLICY_KEEP_MIN_STOCK,
            "procurement_policy": POLICY_OPERATOR_DECISION,
            "readiness_impact": IMPACT_SUGGEST_REPLENISH,
            "display_note": "Verifică cablul, conectorii și clemele — alimentare preventivă dacă nivel scăzut.",
        },
    ],
    "mounting_template_cnc_cut": [
        {
            "code": "FOREX_TEMPLATE_3MM",
            "name": "Forex 3 mm pentru șablon",
            "category": CATEGORY_STANDARD_LOW_COST,
            "unit": "mp",
            "planning_policy": POLICY_VERIFY_BEFORE_START,
            "procurement_policy": POLICY_OPERATOR_DECISION,
            "readiness_impact": IMPACT_SUGGEST_REPLENISH,
            "display_note": "Verifică Forex pentru șablon montaj.",
        },
        {
            "code": "MOUNTING_PROFILE_OR_BARS",
            "name": "Bare/profile montaj",
            "category": CATEGORY_PROJECT_CRITICAL,
            "unit": "ml",
            "planning_policy": POLICY_VERIFY_BEFORE_START,
            "procurement_policy": POLICY_BUY_AFTER_ADVANCE,
            "readiness_impact": IMPACT_CAN_BLOCK,
            "display_note": "Verifică barele/profilele de montaj comandate pe proiect.",
        },
        {
            "code": "MOUNTING_CONSUMABLES",
            "name": "Șuruburi / distanțieri / canal cablu",
            "category": CATEGORY_STANDARD_LOW_COST,
            "unit": "set",
            "planning_policy": POLICY_KEEP_MIN_STOCK,
            "procurement_policy": POLICY_OPERATOR_DECISION,
            "readiness_impact": IMPACT_SUGGEST_REPLENISH,
            "display_note": "Verifică șuruburi, distanțieri și canal cablu — alimentare preventivă.",
        },
    ],
    "assembly_letters": [
        {
            "code": "ASSEMBLY_CONSUMABLES",
            "name": "Consumabile asamblare",
            "category": CATEGORY_STANDARD_LOW_COST,
            "unit": "set",
            "planning_policy": POLICY_KEEP_MIN_STOCK,
            "procurement_policy": POLICY_OPERATOR_DECISION,
            "readiness_impact": IMPACT_SUGGEST_REPLENISH,
            "display_note": "Verifică consumabilele de asamblare — alimentare preventivă.",
        },
    ],
    "qc_letters": [
        {
            "code": "QC_TEST_SETUP",
            "name": "Checklist test / electric",
            "category": CATEGORY_INDIRECT,
            "unit": "set",
            "planning_policy": POLICY_CHECKLIST_ONLY,
            "procurement_policy": POLICY_OPERATOR_DECISION,
            "readiness_impact": IMPACT_NO_TASK_BLOCK,
            "display_note": "Checklist QC electric — fără urmărire stoc strictă.",
        },
    ],
    "packaging_letters": [
        {
            "code": "PACKAGING_CONSUMABLES",
            "name": "Ambalare / folie / carton / etichete",
            "category": CATEGORY_STANDARD_LOW_COST,
            "unit": "set",
            "planning_policy": POLICY_KEEP_MIN_STOCK,
            "procurement_policy": POLICY_OPERATOR_DECISION,
            "readiness_impact": IMPACT_SUGGEST_REPLENISH,
            "display_note": "Verifică materialele de ambalare — alimentare preventivă.",
        },
    ],
}


def _normalize_process_id(task: dict) -> str:
    return str(task.get("process_id") or "").strip().lower()


def _build_process_index(plan_tasks: List[Any]) -> Dict[str, str]:
    index: Dict[str, str] = {}
    for entry in plan_tasks:
        if not isinstance(entry, dict):
            continue
        process_id = _normalize_process_id(entry)
        task_id = str(entry.get("task_id") or "").strip()
        if process_id and task_id and process_id not in index:
            index[process_id] = task_id
    return index


def _is_volumetric_plan(plan_tasks: List[Any], product_context: Optional[str]) -> bool:
    if product_context and str(product_context).strip().upper() == VOLUMETRIC_TEMPLATE:
        return True
    process_ids = {_normalize_process_id(t) for t in plan_tasks if isinstance(t, dict)}
    return bool(process_ids & VOLUMETRIC_PROCESS_IDS)


def _material_item_from_template(
    template: Dict[str, Any],
    *,
    task_id: str,
) -> Dict[str, Any]:
    return {
        "code": str(template["code"]),
        "name": str(template["name"]),
        "category": str(template["category"]),
        "quantity_estimate": None,
        "unit": str(template.get("unit") or "set"),
        "confidence": CONFIDENCE_ESTIMATED,
        "source": SOURCE_TEMPLATE_RULE,
        "required_for_task_ids": [task_id],
        "planning_policy": str(template.get("planning_policy") or POLICY_VERIFY_BEFORE_START),
        "procurement_policy": str(template.get("procurement_policy") or POLICY_OPERATOR_DECISION),
        "readiness_impact": str(template.get("readiness_impact") or IMPACT_CHECKLIST_ONLY),
        "display_note": str(template.get("display_note") or ""),
    }


def _merge_material_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for item in items:
        code = str(item.get("code") or "")
        if not code:
            continue
        if code not in merged:
            merged[code] = {**item, "required_for_task_ids": list(item.get("required_for_task_ids") or [])}
            continue
        existing = merged[code]
        for task_id in item.get("required_for_task_ids") or []:
            tid = str(task_id)
            if tid and tid not in existing["required_for_task_ids"]:
                existing["required_for_task_ids"].append(tid)
    return list(merged.values())


def derive_material_planning_items(
    plan_tasks: List[Any],
    *,
    product_context: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Derive read-only material planning hints for an execution plan."""
    if not plan_tasks or not _is_volumetric_plan(plan_tasks, product_context):
        return []

    process_index = _build_process_index(plan_tasks)
    raw_items: List[Dict[str, Any]] = []

    for process_id, templates in VOLUMETRIC_PROCESS_MATERIAL_RULES.items():
        task_id = process_index.get(process_id)
        if not task_id:
            continue
        for template in templates:
            raw_items.append(_material_item_from_template(template, task_id=task_id))

    return _merge_material_items(raw_items)


def derive_task_material_hints(
    plan_tasks: List[Any],
    *,
    product_context: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Map task_id → material planning items affecting that task."""
    by_task: Dict[str, List[Dict[str, Any]]] = {}
    for item in derive_material_planning_items(plan_tasks, product_context=product_context):
        for task_id in item.get("required_for_task_ids") or []:
            key = str(task_id)
            by_task.setdefault(key, []).append(dict(item))
    return by_task


def summarize_material_planning(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Order-level summary counts for operator blueprint."""
    project_critical_count = sum(
        1 for item in items if item.get("category") == CATEGORY_PROJECT_CRITICAL
    )
    suggest_replenishment_count = sum(
        1 for item in items if item.get("readiness_impact") == IMPACT_SUGGEST_REPLENISH
    )
    checklist_count = sum(
        1
        for item in items
        if item.get("readiness_impact") in (IMPACT_CHECKLIST_ONLY, IMPACT_NO_TASK_BLOCK)
    )
    has_procurement_sensitive = any(
        item.get("category") == CATEGORY_PROJECT_CRITICAL
        and item.get("procurement_policy") == POLICY_BUY_AFTER_ADVANCE
        for item in items
    )
    return {
        "project_critical_count": project_critical_count,
        "suggest_replenishment_count": suggest_replenishment_count,
        "checklist_count": checklist_count,
        "has_procurement_sensitive_items": has_procurement_sensitive,
    }


def _employee_label_for_category(category: str) -> str:
    if category == CATEGORY_PROJECT_CRITICAL:
        return "Verifică material"
    if category == CATEGORY_INDIRECT:
        return "Checklist"
    return "Verificare preventivă"


def employee_safe_material_hints_for_task(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Employee-safe, compact hints (max 2) without price/supplier/qty."""
    if not items:
        return []

    critical = [item for item in items if item.get("category") == CATEGORY_PROJECT_CRITICAL]
    low_cost = [
        item
        for item in items
        if item.get("category") in (CATEGORY_STANDARD_LOW_COST, CATEGORY_INDIRECT)
    ]

    hints: List[Dict[str, Any]] = []
    for item in critical[:1]:
        hints.append(
            {
                "name": str(item.get("name") or ""),
                "category": str(item.get("category") or ""),
                "label": _employee_label_for_category(str(item.get("category") or "")),
                "display_note": str(item.get("display_note") or ""),
            }
        )

    if low_cost:
        if len(low_cost) == 1:
            item = low_cost[0]
            hints.append(
                {
                    "name": str(item.get("name") or ""),
                    "category": str(item.get("category") or ""),
                    "label": _employee_label_for_category(str(item.get("category") or "")),
                    "display_note": str(item.get("display_note") or ""),
                }
            )
        else:
            hints.append(
                {
                    "name": "Consumabile montaj",
                    "category": CATEGORY_STANDARD_LOW_COST,
                    "label": "Verificare preventivă",
                    "display_note": (
                        "Verifică consumabile montaj: adeziv, șuruburi, cablu, conectori — "
                        "alimentare preventivă dacă nivel scăzut."
                    ),
                }
            )

    return hints[:2]
