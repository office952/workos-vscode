"""PRODUCT_SYSTEM_REFERENCE_COMPLETE — frozen closure contracts (no feature expansion)."""

from __future__ import annotations

from typing import Any

REFERENCE_COMPLETE_VERSION = "product_system_reference_complete_v1"
REFERENCE_COMPLETE_NAME = "PRODUCT_SYSTEM_REFERENCE_COMPLETE"

ACCEPTED_BUILD_CHAIN: list[dict[str, str]] = [
    {"build": "PRICING_FOUNDATION_V1", "role": "catalog rate ownership"},
    {"build": "TEMPLATE_PRICING_STUDIO_V1", "role": "recipe composition surface"},
    {"build": "LABOR_RECIPE_CONTRACT_V1", "role": "labor/service physical drivers"},
    {"build": "AI_OPERATIONAL_DEFAULTS_V1", "role": "AI defaults with provenance"},
    {"build": "TEMPLATE_ACTIVATION_V1", "role": "publication/readiness honesty"},
    {"build": "PRODUCT_PRICE_BREAKDOWN_V1", "role": "EIC/CPP explainable breakdown", "commit": "a243dd69"},
    {"build": "MATERIAL_MARKET_PRICE_REGISTRY_V1", "role": "purchase truth read-model", "commit": "f67d56a7"},
    {"build": "PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1", "role": "finish-line contracts", "commit": "8aac9eda"},
    {"build": "ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1", "role": "PSU selector closure", "commit": "7bdd9f61"},
]

# Static matrix rows — runtime service fills complete/proof fields.
COMPLETION_MATRIX_SPEC: list[dict[str, Any]] = [
    {"axis": "Product System", "required_verdict": "REFERENCE_COMPLETE", "required_for_reference": True},
    {"axis": "Modularity", "required_verdict": "ACCEPTED_WITH_LIMITS", "required_for_reference": True},
    {"axis": "Root ownership", "required_verdict": "COMPLETE", "required_for_reference": True},
    {"axis": "Child ownership", "required_verdict": "COMPLETE", "required_for_reference": True},
    {"axis": "Authoring", "required_verdict": "REFERENCE_LIMITATION_ACCEPTED", "required_for_reference": True},
    {"axis": "Form contract", "required_verdict": "COMPLETE_REFERENCE", "required_for_reference": True},
    {"axis": "VL schema", "required_verdict": "COMPLETE_REFERENCE", "required_for_reference": True},
    {"axis": "Product Definition", "required_verdict": "COMPLETE_REFERENCE", "required_for_reference": True},
    {"axis": "Product Truth", "required_verdict": "COMPLETE_REFERENCE", "required_for_reference": True},
    {"axis": "Quantities", "required_verdict": "COMPLETE_REFERENCE", "required_for_reference": True},
    {"axis": "Formula ownership", "required_verdict": "COMPLETE_REFERENCE", "required_for_reference": True},
    {"axis": "Inventory", "required_verdict": "COMPLETE_REFERENCE", "required_for_reference": True},
    {"axis": "Material price truth", "required_verdict": "COMPLETE_REFERENCE", "required_for_reference": True},
    {"axis": "Critical material coverage", "required_verdict": "COMPLETE", "required_for_reference": True},
    {"axis": "Operational-process boundary", "required_verdict": "CONTRACT_FROZEN", "required_for_reference": True},
    {"axis": "Labor/services", "required_verdict": "COMPLETE_REFERENCE", "required_for_reference": True},
    {"axis": "EIC", "required_verdict": "COMPLETE_AND_RECONCILED", "required_for_reference": True},
    {"axis": "CPP", "required_verdict": "RECONCILIATION_ONLY", "required_for_reference": True},
    {"axis": "Analyzer contract", "required_verdict": "CONTRACT_FROZEN", "required_for_reference": True},
    {"axis": "Scalability", "required_verdict": "ACCEPTED_WITH_LIMITS", "required_for_reference": True},
    {"axis": "UI target distinction", "required_verdict": "CONTRACT_FROZEN", "required_for_reference": True},
    {"axis": "Freeze governance", "required_verdict": "CONTRACT_FROZEN", "required_for_reference": True},
    {"axis": "Documentation input", "required_verdict": "READY", "required_for_reference": True},
]

ACCEPTED_LIMITATIONS: list[dict[str, str]] = [
    {
        "id": "form_builder",
        "text_ro": "Form Builder generic amânat la Workflow-ADV",
        "class": "accepted_reference_limitation",
        "deferred_to_adv": "yes",
    },
    {
        "id": "add_child_ui",
        "text_ro": "Add-child visual authoring Option 2 — API/seed only",
        "class": "accepted_reference_limitation",
        "deferred_to_adv": "yes",
    },
    {
        "id": "optional_consumables",
        "text_ro": "Consumabile opționale fără preț (adeziv/cabluri/laminare)",
        "class": "accepted_reference_limitation",
        "deferred_to_adv": "no",
    },
    {
        "id": "logo_incomplete",
        "text_ro": "Logo root incomplet ca traseu de referință",
        "class": "accepted_reference_limitation",
        "deferred_to_adv": "yes",
    },
    {
        "id": "acm_treatments",
        "text_ro": "Tratamente ACM opționale deferred",
        "class": "accepted_reference_limitation",
        "deferred_to_adv": "yes",
    },
    {
        "id": "lab_ui",
        "text_ro": "UI badge-heavy de laborator ≠ Platform UI țintă",
        "class": "accepted_reference_limitation",
        "deferred_to_adv": "yes",
    },
    {
        "id": "global_freeze_impl",
        "text_ro": "Implementarea globală FREEZE ON amânată — contract documentat",
        "class": "documentation_only_gap",
        "deferred_to_adv": "yes",
    },
    {
        "id": "process_catalog_ui",
        "text_ro": "UI catalog procese operaționale complete deferred",
        "class": "accepted_reference_limitation",
        "deferred_to_adv": "yes",
    },
    {
        "id": "supplier_import",
        "text_ro": "Supplier Import deferred / Workflow-ADV only",
        "class": "deferred_workflow_adv",
        "deferred_to_adv": "yes",
    },
]

DO_NOT_TRANSFER: list[str] = [
    "VL specialized UI as universal Form Generator",
    "Lab badge-heavy diagnostics as Platform operator UI",
    "Generic PSU selector priced as SKU",
    "Hardcoded template-code page copies as extension model",
    "Analyzer → Product Truth without operator confirmation",
    "CPP as offer completion authority",
    "Invented material prices / Supplier Import stubs",
    "Offer / Order / Execution / mobile paths as reference finish line",
    "In-place mutation of frozen operational versions",
]

JUST_IN_TIME_CATALOG_RULE = {
    "rule_id": "just_in_time_catalog_growth_v1",
    "summary_ro": (
        "Nu pre-creăm cataloage mari nefolosite. La un Product Template nou: "
        "identifică materiale/procese/manoperă/servicii necesare → verifică Inventory/Pricing → "
        "creează doar lipsa în catalogul canonic → apoi referă din Product System."
    ),
    "forbidden": [
        "local_pseudo_resource_as_price_authority",
        "invent_material_inside_template",
        "invent_process_rate_inside_template",
    ],
}

OPERATIONAL_PROCESS_CONTRACT = {
    "contract_id": "operational_process_catalog_boundary_v1",
    "status": "CONTRACT_FROZEN",
    "summary_ro": (
        "Procesele operaționale (CNC, Laser, Print, Laminare, Modelare cant, Vopsire) "
        "sunt first-class — nu linii generice de preț. Product System referă procesul "
        "și furnizează quantity/formula; catalogul deține tariful și compatibilitățile."
    ),
    "required_categories": [
        "CNC_mechanical",
        "CNC_laser",
        "Print",
        "Lamination",
        "Edge_return_forming",
        "Painting",
        "other_production_processes",
    ],
    "process_fields": [
        "process_code",
        "category",
        "machine_workcenter",
        "compatible_materials",
        "compatible_thicknesses",
        "input_unit",
        "cost_unit",
        "minimum",
        "setup",
        "active",
        "source",
        "version",
    ],
    "implementation_in_this_build": "boundary_only_no_new_catalog_ui",
}

UI_MODE_DISTINCTION = {
    "contract_id": "lab_admin_operator_ui_distinction_v1",
    "status": "CONTRACT_FROZEN",
    "lab_ui": "diagnostics, readiness, warnings, badges — current WorkOS laboratory",
    "platform_ui": "operator actions and valid operational choices — Workflow-ADV target",
    "admin_ui": "versioning, freeze, audit",
    "dev_ui": "diagnostics and experimental truth",
    "do_not_transfer": "current badge-heavy Lab UI as final Platform UI",
}

DEV_MODE_CONTRACT = {
    "contract_id": "dev_mode_draft_version_v1",
    "status": "CONTRACT_FROZEN",
    "summary_ro": (
        "DEV MODE deschide calea de dezvoltare pe un draft/versiune nouă "
        "(template, composition, materials, prices, processes, labor, services, "
        "Intake/Form, PD, PT, quantities, cost). Nu mută versiunea operațională înghețată."
    ),
    "forbidden": ["mutate_frozen_operational_version_in_place"],
}

FREEZE_GOVERNANCE_CONTRACT = {
    "contract_id": "freeze_and_version_governance_v1",
    "status": "CONTRACT_FROZEN",
    "rule": "FREEZE ON = immutable accepted operational version",
    "evolution_path": [
        "Frozen v1",
        "create DEV v2",
        "validate",
        "promote",
        "FREEZE ON",
    ],
    "forbidden": [
        "code_mutate_frozen",
        "agent_mutate_frozen",
        "seed_mutate_frozen",
        "migration_mutate_frozen",
        "automation_mutate_frozen",
        "generic_admin_write_mutate_frozen",
    ],
    "owner_only": "controlled_unfreeze_or_dev_branch",
    "implementation_in_this_build": "contract_documentation_only",
}

DOCUMENTATION_HANDOFF_DOCS: list[str] = [
    "WORKFLOW_ADV_PRODUCT_SYSTEM_OVERVIEW",
    "DOMAIN_MODEL",
    "PRODUCT_TEMPLATE_AUTHORING",
    "CHILD_TEMPLATE_COMPOSITION",
    "FORM_SCHEMA_CONTRACT",
    "PRODUCT_DEFINITION_CONTRACT",
    "PRODUCT_TRUTH_CONTRACT",
    "QUANTITY_AND_FORMULA_CONTRACT",
    "INVENTORY_AND_MATERIAL_CONTRACT",
    "MATERIAL_PRICE_SOURCE_CONTRACT",
    "OPERATIONAL_PROCESS_CONTRACT",
    "LABOR_AND_SERVICE_RECIPE_CONTRACT",
    "AI_OPERATIONAL_DEFAULTS_CONTRACT",
    "PRODUCTION_COST_BREAKDOWN_CONTRACT",
    "READINESS_AND_LIFECYCLE",
    "ANALYZER_DESKTOP_INTEGRATION_CONTRACT",
    "REQUEST_TO_COST_FLOW",
    "API_CONTRACTS",
    "UI_INFORMATION_ARCHITECTURE",
    "TEMPLATE_EXAMPLES",
    "TEST_FIXTURES",
    "DEV_TO_IMPLEMENTATION_PROMOTION_CONTRACT",
    "FREEZE_AND_VERSION_GOVERNANCE",
    "WORKFLOW_ADV_MIGRATION_AND_HANDOFF",
    "DEAD_AND_LEGACY_PATHS",
]
