"""ProductSystem contract — TPL-VOLUMETRIC-FACE-BACK-PREP (partial volumetric template).

Canonical metadata, components, operations, material mappings, and draft task
ordering. Intake V4 cost draft and future CostEngine/production adapters consume
this module — not the reverse.

Does NOT create real tasks, quotes, stock consumption, or CostEngine pricing.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from schemas.intake_v4 import (
    TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE,
    TPL_VOLUMETRIC_FACE_BACK_PREP_V1_VERSION,
)

FULL_VOLUMETRIC_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"

CNC_RATE_EUR_PER_ML = 1.5

# Owner-confirmed CNC pass counts (per vector perimeter ml × pass × rate).
FACE_CNC_CUT_PASS_COUNT = 1
FACE_CNC_SHANFREN_PASS_COUNT = 1
BACK_FOREX_CNC_CUT_PASS_COUNT = 3
BACK_FOREX_CNC_SHANFREN_PASS_COUNT = 2

VECTOR_FACE_PERIMETER_KEYS: tuple[str, ...] = (
    "cnc_cutting_perimeter_ml",
    "face_cutting_perimeter_ml",
    "cutting_perimeter_ml",
)
VECTOR_BACK_PERIMETER_KEYS: tuple[str, ...] = (
    "backing_cnc_cutting_perimeter_ml",
    "back_cutting_perimeter_ml",
)
TaskStation = Literal["prepress", "cnc", "finishing", "packing"]

# Material logical keys → inventory registry codes (historic names preserved).
MATERIAL_REGISTRY_BY_LOGICAL_KEY: dict[str, str] = {
    "plexiglas_3mm": "MAT-ACP-FATA-LITERE",
    "forex_10mm": "MAT-SPATE-PVC-LITERE",
}

# Maps to shared_cnc_operation_model operation keys (preview / future handoff).
SHARED_CNC_OPERATION_KEY_BY_TASK: dict[str, str] = {
    "CUT_FACE_PLEXI": "cnc_face_cutting_plexiglas_3mm",
    "SHANFREN_FACE_PLEXI": "cnc_face_bevel_plexiglas_3mm",
    "CUT_BACK_FOREX": "cnc_backing_cutting_forex_10mm",
    "SHANFREN_BACK_FOREX": "cnc_backing_bevel_forex_10mm",
}

TEMPLATE_INCLUDES: tuple[str, ...] = (
    "FACE_PLEXI",
    "BACK_FOREX",
    "CNC_CUT_FACE",
    "CNC_SHANFREN_FACE",
    "CNC_CUT_BACK",
    "OPTIONAL_CNC_SHANFREN_BACK",
)

TEMPLATE_EXCLUDES: tuple[str, ...] = (
    "EDGE_CANT",
    "EDGE_FORMING",
    "EDGE_VINYL",
    "EDGE_TO_FACE_BONDING",
    "LIGHTING",
    "WIRING",
    "PSU",
    "SUPPORT",
    "MOUNTING",
    "FINAL_ASSEMBLY",
    "STOCK_CONSUMPTION",
    "REAL_TASK_CREATION",
    "FINAL_QUOTE",
    "FINISH_ORACAL",
    "FINISH_PRINT",
    "FINISH_LAMINATION",
    "FINISH_POLICROMIE",
)

TEMPLATE_METADATA: dict[str, Any] = {
    "key": TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE,
    "label": "Pregătire fețe plexiglas + spate Forex",
    "family": "volumetric_letters",
    "family_id": "litere_volumetrice",
    "family_name": "Litere volumetrice — pregătire față/spate",
    "scope": "partial_template",
    "version": TPL_VOLUMETRIC_FACE_BACK_PREP_V1_VERSION,
    "status": "draft_internal",
    "active_for_commercial_quote": False,
    "reusable_module_of": FULL_VOLUMETRIC_TEMPLATE_CODE,
    "description": (
        "Template parțial pentru pregătirea fețelor din plexiglas 3 mm "
        "și a spatelui Forex 10 mm pentru litere volumetrice."
    ),
    "includes": list(TEMPLATE_INCLUDES),
    "excludes": list(TEMPLATE_EXCLUDES),
}


class ProductSystemComponentSpec(TypedDict, total=False):
    key: str
    label: str
    materialDefault: str
    thicknessMm: float
    required: bool
    requiresShanfren: bool
    shanfrenType: str
    component_type: str


PRODUCTSYSTEM_COMPONENTS: dict[str, ProductSystemComponentSpec] = {
    "FACE_PLEXI": {
        "key": "FACE_PLEXI",
        "label": "Față plexiglas",
        "materialDefault": "plexiglas_3mm",
        "thicknessMm": 3.0,
        "required": True,
        "requiresShanfren": True,
        "shanfrenType": "cnc_channel",
        "component_type": "PLEXI_PANEL",
    },
    "BACK_FOREX": {
        "key": "BACK_FOREX",
        "label": "Spate Forex",
        "materialDefault": "forex_10mm",
        "thicknessMm": 10.0,
        "required": True,
        "requiresShanfren": False,
        "shanfrenType": "cnc_channel_optional",
        "component_type": "STRUCTURA",
    },
}


class ProductSystemOperationSpec(TypedDict, total=False):
    key: str
    label: str
    component: ComponentKey
    station: TaskStation
    unit: str
    unitPrice: float
    currency: str
    priceSource: str
    required: bool
    appearsWhen: str | None
    createsRealTask: bool
    operation_key: str
    shared_cnc_operation_key: str | None


# Canonical V1 operations (ProductSystem operation catalog).
PRODUCTSYSTEM_OPERATIONS: tuple[ProductSystemOperationSpec, ...] = (
    {
        "key": "PREPARE_CNC_FILES",
        "label": "Pregătire fișiere CNC",
        "component": "GENERAL",
        "station": "prepress",
        "unit": "job",
        "unitPrice": 0.0,
        "currency": "EUR",
        "priceSource": "draft_internal",
        "required": True,
        "appearsWhen": None,
        "createsRealTask": False,
        "operation_key": "prepare_cnc_files",
        "shared_cnc_operation_key": None,
    },
    {
        "key": "CUT_FACE_PLEXI",
        "label": "Debitare CNC față plexiglas 3 mm",
        "component": "FACE_PLEXI",
        "station": "cnc",
        "unit": "ml",
        "unitPrice": CNC_RATE_EUR_PER_ML,
        "currency": "EUR",
        "priceSource": "fixed_rule",
        "required": True,
        "appearsWhen": None,
        "createsRealTask": False,
        "operation_key": "cnc_cut_face_plexi",
        "shared_cnc_operation_key": "cnc_face_cutting_plexiglas_3mm",
    },
    {
        "key": "SHANFREN_FACE_PLEXI",
        "label": "Șanfren/canal CNC față plexiglas",
        "component": "FACE_PLEXI",
        "station": "cnc",
        "unit": "ml",
        "unitPrice": CNC_RATE_EUR_PER_ML,
        "currency": "EUR",
        "priceSource": "fixed_rule",
        "required": True,
        "appearsWhen": None,
        "createsRealTask": False,
        "operation_key": "cnc_shanfren_face_plexi",
        "shared_cnc_operation_key": "cnc_face_bevel_plexiglas_3mm",
    },
    {
        "key": "CUT_BACK_FOREX",
        "label": "Debitare CNC spate Forex 10 mm",
        "component": "BACK_FOREX",
        "station": "cnc",
        "unit": "ml",
        "unitPrice": CNC_RATE_EUR_PER_ML,
        "currency": "EUR",
        "priceSource": "fixed_rule",
        "required": True,
        "appearsWhen": None,
        "createsRealTask": False,
        "operation_key": "cnc_cut_back_forex",
        "shared_cnc_operation_key": "cnc_backing_cutting_forex_10mm",
    },
    {
        "key": "SHANFREN_BACK_FOREX",
        "label": "Șanfren/canal CNC spate Forex",
        "component": "BACK_FOREX",
        "station": "cnc",
        "unit": "ml",
        "unitPrice": CNC_RATE_EUR_PER_ML,
        "currency": "EUR",
        "priceSource": "fixed_rule",
        "required": False,
        "appearsWhen": "shanfren_forex=true",
        "createsRealTask": False,
        "operation_key": "cnc_shanfren_back_forex",
        "shared_cnc_operation_key": "cnc_backing_bevel_forex_10mm",
    },
    {
        "key": "CLEAN_AND_CHECK_PARTS",
        "label": "Curățare și verificare piese",
        "component": "GENERAL",
        "station": "finishing",
        "unit": "job",
        "unitPrice": 0.0,
        "currency": "EUR",
        "priceSource": "draft_internal",
        "required": True,
        "appearsWhen": None,
        "createsRealTask": False,
        "operation_key": "clean_and_check_parts",
        "shared_cnc_operation_key": None,
    },
    {
        "key": "PACKAGE_FACE_BACK_PARTS",
        "label": "Ambalare piese față + spate",
        "component": "GENERAL",
        "station": "packing",
        "unit": "job",
        "unitPrice": 0.0,
        "currency": "EUR",
        "priceSource": "draft_internal",
        "required": True,
        "appearsWhen": None,
        "createsRealTask": False,
        "operation_key": "package_face_back_parts",
        "shared_cnc_operation_key": None,
    },
)

OPERATION_BY_KEY: dict[str, ProductSystemOperationSpec] = {
    op["key"]: op for op in PRODUCTSYSTEM_OPERATIONS  # type: ignore[misc]
}

# Cost-draft service aliases (stable operation_key strings).
OP_CNC_CUT_FACE = OPERATION_BY_KEY["CUT_FACE_PLEXI"]["operation_key"]  # type: ignore[index]
OP_CNC_SHANFREN_FACE = OPERATION_BY_KEY["SHANFREN_FACE_PLEXI"]["operation_key"]  # type: ignore[index]
OP_CNC_CUT_BACK = OPERATION_BY_KEY["CUT_BACK_FOREX"]["operation_key"]  # type: ignore[index]
OP_CNC_SHANFREN_BACK = OPERATION_BY_KEY["SHANFREN_BACK_FOREX"]["operation_key"]  # type: ignore[index]

TASK_PREPARE_CNC = "PREPARE_CNC_FILES"
TASK_CUT_FACE = "CUT_FACE_PLEXI"
TASK_SHANFREN_FACE = "SHANFREN_FACE_PLEXI"
TASK_CUT_BACK = "CUT_BACK_FOREX"
TASK_SHANFREN_BACK = "SHANFREN_BACK_FOREX"
TASK_CLEAN = "CLEAN_AND_CHECK_PARTS"
TASK_PACKAGE = "PACKAGE_FACE_BACK_PARTS"

REGISTRY_PLEXI_FACE_CODE = MATERIAL_REGISTRY_BY_LOGICAL_KEY["plexiglas_3mm"]
REGISTRY_FOREX_BACK_CODE = MATERIAL_REGISTRY_BY_LOGICAL_KEY["forex_10mm"]
MATERIAL_KEY_PLEXI_3MM = "plexiglas_3mm"
MATERIAL_KEY_FOREX_10MM = "forex_10mm"


def task_draft_order(*, shanfren_forex_enabled: bool) -> list[str]:
    """Logical task key order for V1 draft preview."""
    order = [
        TASK_PREPARE_CNC,
        TASK_CUT_FACE,
        TASK_SHANFREN_FACE,
        TASK_CUT_BACK,
    ]
    if shanfren_forex_enabled:
        order.append(TASK_SHANFREN_BACK)
    order.extend([TASK_CLEAN, TASK_PACKAGE])
    return order


def get_operation_spec(task_key: str) -> ProductSystemOperationSpec | None:
    return OPERATION_BY_KEY.get(task_key)


def is_template_excluded_capability(token: str) -> bool:
    return token.upper() in {t.upper() for t in TEMPLATE_EXCLUDES}


def productsystem_template_notes() -> str:
    return (
        f"scope={TEMPLATE_METADATA['scope']}; "
        f"version={TEMPLATE_METADATA['version']}; "
        f"status={TEMPLATE_METADATA['status']}; "
        f"reusable_module_of={FULL_VOLUMETRIC_TEMPLATE_CODE}; "
        "cost_draft_only=true; quote_priced=false; creates_real_tasks=false."
    )
