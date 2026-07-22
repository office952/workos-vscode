"""PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1 — frozen contracts and inventories."""

from __future__ import annotations

from typing import Any

FINISH_LINE_CONTRACT_VERSION = "product_system_reference_finish_line_v1"
FINISH_LINE_NAME = "PRODUCT_SYSTEM_REFERENCE_COMPLETE"

# --- Production cost boundary ---
PRODUCTION_COST_EQUATION = (
    "materials + machine_operations + labor + services + consumables + packaging "
    "= internal_production_cost (EIC)"
)

PRODUCTION_COST_BOUNDARY = {
    "completion_authority": "EIC_production_cost",
    "cpp_role": "reconciliation_visible_not_lab_stop",
    "excluded": [
        "markup",
        "profit",
        "offer",
        "discount",
        "negotiation",
        "order",
        "invoicing",
        "execution_materialization",
        "shopfloor",
        "employee_mobile",
        "svg_dxf_dwg_parsing",
        "supplier_import",
    ],
    "label_production_ro": "Cost producție (EIC)",
    "label_commercial_ro": "Preț comercial (CPP)",
    "ownership_note_ro": (
        "Linia de referință a laboratorului se oprește la costul de producție intern (EIC). "
        "CPP rămâne vizibil pentru reconciliere, nu ca cerință de ofertă. "
        "Fără adaos, ofertă, comandă sau execuție în finish line."
    ),
}

# --- Modularity ---
MODULARITY_MODEL = {
    "root": "Product Template root → composes roles",
    "child": "Child/component Product Template → owns its own technical truth",
    "role": "Role → placement/function",
    "usage_mode": "root | child | dual-role",
    "resources": "Inventory / Pricing references (not ownership of Inventory truth)",
    "formula_ownership": "template that owns the truth",
    "no_parallel_entity": "ComponentTemplate parallel entity not required",
    "authoring_decision": "OPTION_2_DOCUMENTED_LAB_LIMITATION",
    "authoring_note_ro": (
        "Create/edit/publish există. Add-child UI lipsește — legăturile se creează via API/seed. "
        "Composition panel este update-only. Nu construim Template Factory în acest build."
    ),
    "verdict_target": "MODULAR_WITH_GAPS",
}

# --- Critical material classification policy ---
MATERIAL_CLASSIFICATION_POLICY = {
    "ACTIVE_TEMPLATE_CRITICAL": (
        "Referenced by an owner-valid active template recipe/path AND unit_cost missing "
        "AND absence blocks or materially distorts production-cost truth for that path."
    ),
    "ACTIVE_TEMPLATE_OPTIONAL": (
        "Referenced by active template but optional capability / alternate path; "
        "missing price warns, does not block root readiness alone."
    ),
    "VARIANT_SELECTOR": (
        "Family/selector code that must not own a direct purchase price. "
        "Resolves to concrete priced variants via quote selection keys."
    ),
    "UNUSED_ACTIVE": "Present in Inventory active set but not referenced by active templates.",
    "LEGACY": "Legacy code retained for history; not in finish-line path.",
    "DUPLICATE_ALIAS": "Alias/duplicate of a canonical material code.",
    "FUTURE_ONLY": "Reserved for future templates; not finish-line critical.",
    "UNKNOWN": "Insufficient evidence to classify.",
}

# Seeded critical shortlist for manual fill (no invented prices).
# Runtime finish-line service reconciles against market registry.
MANUAL_FILL_SEED: list[dict[str, Any]] = [
    {
        "material_code": "MAT-LED-PSU-12V",
        "classification": "VARIANT_SELECTOR",
        "reason_ro": (
            "Selector familie PSU 12V — nu SKU de achiziție. "
            "Prețul stă pe MAT-LED-PSU-12V-{60|100|160|200}W (OWNER_CONFIRMED). "
            "Nu inventăm preț generic pe codul selector."
        ),
        "templates": ["TPL-VOLUMETRIC-LETTERS_v2"],
        "action": "resolve_to_variant",
        "do_not": ["invent_price", "supplier_import", "price_selector"],
    },
    {
        "material_code": "MAT-ADEZIV-CANT-LITERE",
        "classification": "ACTIVE_TEMPLATE_OPTIONAL",
        "reason_ro": "În CRITICAL_VL_GAPS seed; adeziv FACE+CANT — completează manual dacă lipsește.",
        "templates": ["TPL-VOLUMETRIC-LETTERS_v2"],
        "action": "manual_owner_fill_if_missing",
        "do_not": ["invent_price", "supplier_import"],
    },
    {
        "material_code": "MAT-CABLU-MYYUP-2X075",
        "classification": "ACTIVE_TEMPLATE_OPTIONAL",
        "reason_ro": "Cablu opțional pe căi de livrare iluminate.",
        "templates": ["TPL-VOLUMETRIC-LETTERS_v2"],
        "action": "manual_owner_fill_if_missing",
        "do_not": ["invent_price", "supplier_import"],
    },
    {
        "material_code": "MAT-CABLU-MYYUP-2X15",
        "classification": "ACTIVE_TEMPLATE_OPTIONAL",
        "reason_ro": "Cablu opțional pe căi de livrare iluminate.",
        "templates": ["TPL-VOLUMETRIC-LETTERS_v2"],
        "action": "manual_owner_fill_if_missing",
        "do_not": ["invent_price", "supplier_import"],
    },
    {
        "material_code": "SVC-LAMINATION-SERVICE",
        "classification": "ACTIVE_TEMPLATE_OPTIONAL",
        "reason_ro": "Serviciu laminare — seed gap; nu blochează root fără finisaj laminat.",
        "templates": ["TPL-VOLUMETRIC-LETTERS_v2"],
        "action": "manual_owner_fill_if_missing",
        "do_not": ["invent_price", "supplier_import"],
    },
]

# --- Hardcoding inventories (classified, not auto-fixed) ---
TEMPLATE_CODE_BRANCH_INVENTORY: list[dict[str, Any]] = [
    {
        "location": "backend/services/form_system_contract_backbone_service.py",
        "pattern": "VOLUMETRIC_* / LOGO template code sets",
        "classification": "valid_product_specific_adapter",
        "handoff": "ready",
        "note": "Scope allowlists for owner-valid roots — transfer as template registry, not page.",
    },
    {
        "location": "backend/services/intake_v6_modular_form_contract_service.py",
        "pattern": "PILOT_TEMPLATE = TPL-VOLUMETRIC-LETTERS_v2",
        "classification": "technical_debt",
        "handoff": "gap",
        "note": "VL pilot binding — Form System contract must generalize via schema, not code branch.",
    },
    {
        "location": "frontend Intake V6 routes / specialized renderers",
        "pattern": "dedicated VL Intake V6 UI",
        "classification": "valid_product_specific_adapter",
        "handoff": "gap",
        "note": "Reference path only — not universal Form Generator.",
    },
    {
        "location": "ACM boxed mounting offer/process adapters",
        "pattern": "ACM template code branches",
        "classification": "technical_debt",
        "handoff": "do_not_transfer_as_universal",
        "note": "Secondary shell reference; keep as optional capability adapter.",
    },
]

FIELD_HARDCODING_INVENTORY: list[dict[str, Any]] = [
    {
        "location": "VOLUMETRIC_FIELD_BINDINGS",
        "pattern": "fixed field list for VL",
        "classification": "vl_specific_schema",
        "handoff": "ready_as_template_schema",
    },
    {
        "location": "specialized_letter_groups / specialized_montaj renderers",
        "pattern": "UI tied to VL fields",
        "classification": "vl_specific_ui",
        "handoff": "gap",
    },
    {
        "location": "CostEngine Step 7 field name consumers",
        "pattern": "undeclared field names in formulas",
        "classification": "technical_debt",
        "handoff": "gap",
        "note": "Finish line requires declared destination/affects; do not broaden CostEngine here.",
    },
]

FORMULA_DUPLICATION_INVENTORY: list[dict[str, Any]] = [
    {
        "topic": "CPP vs EIC totals",
        "classification": "intentional_dual_readmodel",
        "handoff": "ready",
        "note": "Breakdown reconciles both; EIC is lab stop authority.",
    },
    {
        "topic": "Frontend finish display vs backend quantities",
        "classification": "display_only_ok",
        "handoff": "ready",
        "note": "Display must not become second calculator.",
    },
    {
        "topic": "Parent duplicating child return-profile truth",
        "classification": "watch",
        "handoff": "gap",
        "note": "Volum Aluminiu must own cant truth; parent maps inputs only.",
    },
]

COUPLING_INVENTORY: list[dict[str, Any]] = [
    {
        "topic": "Product System → Inventory",
        "classification": "reference_only",
        "handoff": "ready",
        "note": "Must not write Inventory purchase truth from Product System.",
    },
    {
        "topic": "Pricing → template truth",
        "classification": "readmodel_ok",
        "handoff": "ready",
        "note": "Pricing rates consumed; template owns composition truth.",
    },
    {
        "topic": "Intake owning formulas",
        "classification": "blocker_if_expanded",
        "handoff": "gap",
        "note": "Intake captures inputs; formulas stay on owning template/CostEngine path.",
    },
    {
        "topic": "Analyzer assumptions inside WorkOS",
        "classification": "boundary_frozen",
        "handoff": "ready",
        "note": "Consume-only artwork + Analyzer I/O contracts; no parser.",
    },
]

# --- Extension points ---
EXTENSION_POINTS: list[dict[str, Any]] = [
    {
        "extension": "new_root_product_template",
        "path": "Product Template authoring + publish + fixture + form schema registration",
        "requires_page_copy": False,
        "current_limit": "Form schema still VL-pilot wired; new root needs schema entry + readiness.",
    },
    {
        "extension": "new_child_product_template",
        "path": "Create template + module_link (API/seed) + usage_mode + own formulas",
        "requires_page_copy": False,
        "current_limit": "No add-child UI (Option 2).",
    },
    {
        "extension": "new_form_field",
        "path": "Declare in template field schema with source/destination/affects",
        "requires_page_copy": False,
        "current_limit": "VL specialized UI fields still need adapter if not generic renderer.",
    },
    {
        "extension": "new_analyzer_field",
        "path": "Add to Analyzer I/O contract + map to Form field_id + confirmation",
        "requires_page_copy": False,
        "current_limit": "No parser coupling allowed.",
    },
    {
        "extension": "new_price_breakdown_line",
        "path": "Emit from recipe/EIC/CPP provenance — breakdown adapter only",
        "requires_page_copy": False,
        "current_limit": "No frontend calculator.",
    },
]

# --- Finish-line checklist entities ---
FINISH_LINE_CHECKLIST: list[dict[str, Any]] = [
    {"axis": "modularity", "entity": "root_child_roles_usage_mode", "requirement": "canonical_model_proven"},
    {"axis": "modularity", "entity": "authoring_option_2", "requirement": "lab_limitation_documented"},
    {"axis": "form", "entity": "field_schema_contract", "requirement": "source_destination_affects_version"},
    {"axis": "form", "entity": "vl_ownership_map", "requirement": "complete_for_VOLUMETRIC_FIELD_BINDINGS"},
    {"axis": "pd_pt", "entity": "product_definition_vs_truth", "requirement": "boundary_explicit"},
    {"axis": "quantity", "entity": "formula_ownership", "requirement": "owner_template_declared"},
    {"axis": "analyzer", "entity": "workflow_adv_analyzer_io_v1", "requirement": "frozen_no_parser"},
    {"axis": "cost", "entity": "eic_production_cost", "requirement": "lab_stop_authority"},
    {"axis": "cost", "entity": "cpp_reconciliation", "requirement": "visible_not_required_for_offer"},
    {"axis": "materials", "entity": "critical_classification_policy", "requirement": "frozen"},
    {"axis": "scalability", "entity": "extension_points", "requirement": "enumerated_with_limits"},
    {"axis": "docs", "entity": "handoff_input_package", "requirement": "structured_facts_for_24doc_build"},
]

PAGE_SCOPE: dict[str, list[str]] = {
    "in_reference_scope": [
        "Product System index",
        "template list",
        "template detail",
        "authoring",
        "composition",
        "Intake V6",
        "Product Definition preview",
        "Product Truth display",
        "Inventory",
        "Pricing Materiale",
        "Pricing Operatii",
        "Pricing Manopera/Servicii",
        "Preturi template",
        "Desfasurator pret",
        "lifecycle/readiness",
    ],
    "excluded_from_completion": [
        "Quotes",
        "Offers",
        "Orders",
        "Execution",
        "Shopfloor",
        "Employee Mobile",
        "markup/commercial policy",
    ],
}
