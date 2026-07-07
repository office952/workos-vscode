"""Shared CNC operation preview model — reusable across ProductSystem templates.

Read-only quantity preview rows for cutting/bevel operations. Rows carry
production-resource bindings (workstation, machine, skill, catalog keys) so the
same normalized operations can feed production preview, task dry-run, and future
ExecutionTask assignment — not an isolated cost calculator.

Does not mutate Pricing Registry, CostEngine, inventory, quote/order/task lifecycle,
or assign employees/machines at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Mapping, Sequence

from services.intake_v4_cnc_router_pass_policy_service import resolve_cnc_cutting_perimeter_ml

DEFAULT_DEPTH_PER_PASS_MM = 3.5
DEFAULT_FACE_PLEXI_THICKNESS_MM = 3.0
DEFAULT_FOREX_BACKING_THICKNESS_MM = 10.0
DEFAULT_CNC_PRICING_RATE_KEY = "workcenter_rates:CNC_ROUTER:per_linear_meter"

# Owner decision: Forex 10 mm debitare uses 3 passes; bevel adds 2 more, for 5 total.
FOREX_10MM_CUTTING_PASSES_OWNER = 3
FOREX_10MM_BEVEL_PASSES_OWNER = 2


class CncOperationType(str, Enum):
    CUTTING = "cutting"
    BEVEL = "bevel"
    ENGRAVING = "engraving"
    POCKET = "pocket"
    DRILLING = "drilling"


class CncBasisType(str, Enum):
    PATH_PERIMETER = "path_perimeter"
    PATH_LENGTH = "path_length"
    AREA = "area"
    PIECE_COUNT = "piece_count"
    MACHINE_TIME = "machine_time"


class CncMaterialSource(str, Enum):
    INTERNAL_STOCK = "internal_stock"
    CLIENT_SUPPLIED = "client_supplied"


VolumetricBackingMode = Literal["none", "forex_10_no_bevel", "forex_10_with_bevel"]
ResourceMappingStatus = Literal["mapped", "pending_mapping"]

# Canonical operational workforce registry (seed_operational_workforce_registry).
REGISTRY_CNC_MACHINE_CODE = "MCH-CNC-4020"
REGISTRY_CNC_WORKCENTER_CODE = "WC_CNC_ROUTING"
REGISTRY_CNC_SKILL_CODE = "SK_CNC_OPERATOR"
REGISTRY_CNC_OPERATION_CODE = "cnc_cutting"
PRICING_CNC_WORKCENTER_CODE = "CNC_ROUTER"


@dataclass(frozen=True)
class CncProductionResourceBinding:
    """Links a CNC preview row to existing registries — keys must exist in repo docs/seeds."""

    tpl_operation_key: str | None = None
    dossier_operation_key: str | None = None
    operation_catalog_key: str | None = None
    production_task_type: str | None = None
    workstation_key: str | None = None
    required_skill_key: str | None = None
    registry_skill_code: str | None = None
    machine_type: str | None = None
    required_machine_key: str | None = None
    workcenter_code: str | None = None
    operational_operation_code: str | None = None
    resource_mapping_status: ResourceMappingStatus = "pending_mapping"
    mapping_gaps: tuple[str, ...] = ()


@dataclass(frozen=True)
class CncOperationRule:
    operation_key: str
    display_name: str
    operation_type: CncOperationType
    material_family: str | None
    material_name: str | None
    thickness_mm: float | None
    basis_type: CncBasisType
    basis_key: str
    basis_label: str
    passes: int
    depth_per_pass_mm: float | None = None
    owner_pass_override: bool = False
    unit: str = "ml"
    pricing_rate_key: str = DEFAULT_CNC_PRICING_RATE_KEY
    material_pricing_rate_key: str | None = None
    material_key: str | None = None
    requires_operator_confirmation: bool = False
    production_binding: CncProductionResourceBinding = field(
        default_factory=CncProductionResourceBinding
    )


@dataclass
class CncOperationPreviewRow:
    key: str
    display_name: str
    operation_type: str
    material_family: str | None = None
    material_name: str | None = None
    thickness_mm: float | None = None
    quantity: float = 0.0
    unit: str = "ml"
    basis_key: str = ""
    basis_label: str = ""
    passes: int = 1
    depth_per_pass_mm: float | None = None
    owner_pass_override: bool = False
    operation_equivalent_quantity: float | None = None
    operation_equivalent_unit: str | None = None
    pricing_rate_key: str | None = None
    unit_price: float | None = None
    estimated_cost: float | None = None
    pricing_status: str = "missing_rate"
    tpl_operation_key: str | None = None
    dossier_operation_key: str | None = None
    operation_catalog_key: str | None = None
    production_task_type: str | None = None
    workstation_key: str | None = None
    required_skill_key: str | None = None
    registry_skill_code: str | None = None
    machine_type: str | None = None
    required_machine_key: str | None = None
    workcenter_code: str | None = None
    operational_operation_code: str | None = None
    resource_mapping_status: ResourceMappingStatus = "pending_mapping"
    mapping_gaps: list[str] = field(default_factory=list)
    material_key: str | None = None
    consumes_stock_now: bool = False
    creates_task_now: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "operation_type": self.operation_type,
            "material_family": self.material_family,
            "material_name": self.material_name,
            "thickness_mm": self.thickness_mm,
            "quantity": self.quantity,
            "unit": self.unit,
            "basis_key": self.basis_key,
            "basis_label": self.basis_label,
            "passes": self.passes,
            "depth_per_pass_mm": self.depth_per_pass_mm,
            "owner_pass_override": self.owner_pass_override,
            "operation_equivalent_quantity": self.operation_equivalent_quantity,
            "operation_equivalent_unit": self.operation_equivalent_unit,
            "pricing_rate_key": self.pricing_rate_key,
            "unit_price": self.unit_price,
            "estimated_cost": self.estimated_cost,
            "pricing_status": self.pricing_status,
            "tpl_operation_key": self.tpl_operation_key,
            "dossier_operation_key": self.dossier_operation_key,
            "operation_catalog_key": self.operation_catalog_key,
            "production_task_type": self.production_task_type,
            "workstation_key": self.workstation_key,
            "required_skill_key": self.required_skill_key,
            "registry_skill_code": self.registry_skill_code,
            "machine_type": self.machine_type,
            "required_machine_key": self.required_machine_key,
            "workcenter_code": self.workcenter_code,
            "operational_operation_code": self.operational_operation_code,
            "resource_mapping_status": self.resource_mapping_status,
            "mapping_gaps": list(self.mapping_gaps),
            "material_key": self.material_key,
            "consumes_stock_now": self.consumes_stock_now,
            "creates_task_now": self.creates_task_now,
            "warnings": list(self.warnings),
        }


def _resolve_face_cnc_perimeter_ml(geometry: Mapping[str, Any]) -> float | None:
    for key in ("face_cutting_perimeter_ml", "cnc_cutting_perimeter_ml", "cutting_perimeter_ml"):
        raw = geometry.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return round(value, 4)
    return resolve_cnc_cutting_perimeter_ml(geometry)


def _resolve_backing_cnc_perimeter_ml(
    geometry: Mapping[str, Any],
    *,
    face_perimeter_ml: float | None,
) -> float | None:
    for key in ("backing_cnc_cutting_perimeter_ml", "back_cutting_perimeter_ml"):
        raw = geometry.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return round(value, 4)
    return face_perimeter_ml


def _row_from_rule(
    rule: CncOperationRule,
    quantity_ml: float,
    *,
    configured_rate_eur_per_ml_pass: float | None = None,
) -> CncOperationPreviewRow:
    op_equiv = round(quantity_ml * rule.passes, 4) if quantity_ml > 0 and rule.passes > 0 else None
    unit_price: float | None = None
    estimated_cost: float | None = None
    pricing_status = "missing_rate"
    if configured_rate_eur_per_ml_pass is not None and configured_rate_eur_per_ml_pass > 0:
        unit_price = configured_rate_eur_per_ml_pass
        if op_equiv is not None:
            estimated_cost = round(op_equiv * unit_price, 4)
            pricing_status = "configured_rate_preview"
    binding = rule.production_binding
    return CncOperationPreviewRow(
        key=rule.operation_key,
        display_name=rule.display_name,
        operation_type=rule.operation_type.value,
        material_family=rule.material_family,
        material_name=rule.material_name,
        thickness_mm=rule.thickness_mm,
        quantity=quantity_ml,
        unit=rule.unit,
        basis_key=rule.basis_key,
        basis_label=rule.basis_label,
        passes=rule.passes,
        depth_per_pass_mm=rule.depth_per_pass_mm,
        owner_pass_override=rule.owner_pass_override,
        operation_equivalent_quantity=op_equiv,
        operation_equivalent_unit="ml-pass" if op_equiv is not None else None,
        pricing_rate_key=rule.pricing_rate_key,
        unit_price=unit_price,
        estimated_cost=estimated_cost,
        pricing_status=pricing_status,
        tpl_operation_key=binding.tpl_operation_key,
        dossier_operation_key=binding.dossier_operation_key,
        operation_catalog_key=binding.operation_catalog_key,
        production_task_type=binding.production_task_type,
        workstation_key=binding.workstation_key,
        required_skill_key=binding.required_skill_key,
        registry_skill_code=binding.registry_skill_code,
        machine_type=binding.machine_type,
        required_machine_key=binding.required_machine_key,
        workcenter_code=binding.workcenter_code,
        operational_operation_code=binding.operational_operation_code,
        resource_mapping_status=binding.resource_mapping_status,
        mapping_gaps=list(binding.mapping_gaps),
        material_key=rule.material_key,
        consumes_stock_now=False,
        creates_task_now=False,
    )


VOLUMETRIC_CNC_ROUTER_BINDING_BASE = CncProductionResourceBinding(
    production_task_type="cnc_routing",
    workstation_key="cnc_router",
    required_skill_key="cnc_operator",
    registry_skill_code=REGISTRY_CNC_SKILL_CODE,
    machine_type="cnc_router",
    required_machine_key=REGISTRY_CNC_MACHINE_CODE,
    workcenter_code=REGISTRY_CNC_WORKCENTER_CODE,
    operational_operation_code=REGISTRY_CNC_OPERATION_CODE,
)

VOLUMETRIC_FACE_CUTTING_BINDING = CncProductionResourceBinding(
    tpl_operation_key="cnc_face_cutting",
    dossier_operation_key="face_cnc_cut",
    operation_catalog_key="face_and_backing_cnc_cut",
    production_task_type="cnc_routing",
    workstation_key="cnc_router",
    required_skill_key="cnc_operator",
    registry_skill_code=REGISTRY_CNC_SKILL_CODE,
    machine_type="cnc_router",
    required_machine_key=REGISTRY_CNC_MACHINE_CODE,
    workcenter_code=REGISTRY_CNC_WORKCENTER_CODE,
    operational_operation_code=REGISTRY_CNC_OPERATION_CODE,
    resource_mapping_status="mapped",
)

VOLUMETRIC_FACE_BEVEL_BINDING = CncProductionResourceBinding(
    tpl_operation_key="cnc_face_bevel",
    dossier_operation_key="face_cnc_cut",
    operation_catalog_key=None,
    production_task_type="cnc_routing",
    workstation_key="cnc_router",
    required_skill_key="cnc_operator",
    registry_skill_code=REGISTRY_CNC_SKILL_CODE,
    machine_type="cnc_router",
    required_machine_key=REGISTRY_CNC_MACHINE_CODE,
    workcenter_code=REGISTRY_CNC_WORKCENTER_CODE,
    operational_operation_code=REGISTRY_CNC_OPERATION_CODE,
    resource_mapping_status="pending_mapping",
    mapping_gaps=(
        "operation_catalog_key",
        "dry_run_task_key",
        "dossier_priced_operation_split",
    ),
)

VOLUMETRIC_BACKING_CUTTING_BINDING = CncProductionResourceBinding(
    tpl_operation_key="cnc_backing_cutting",
    dossier_operation_key="back_cut",
    operation_catalog_key="face_and_backing_cnc_cut",
    production_task_type="cnc_routing",
    workstation_key="cnc_router",
    required_skill_key="cnc_operator",
    registry_skill_code=REGISTRY_CNC_SKILL_CODE,
    machine_type="cnc_router",
    required_machine_key=REGISTRY_CNC_MACHINE_CODE,
    workcenter_code=REGISTRY_CNC_WORKCENTER_CODE,
    operational_operation_code=REGISTRY_CNC_OPERATION_CODE,
    resource_mapping_status="mapped",
)

VOLUMETRIC_BACKING_BEVEL_BINDING = CncProductionResourceBinding(
    tpl_operation_key="cnc_backing_bevel_optional",
    dossier_operation_key="back_cut",
    operation_catalog_key=None,
    production_task_type="cnc_routing",
    workstation_key="cnc_router",
    required_skill_key="cnc_operator",
    registry_skill_code=REGISTRY_CNC_SKILL_CODE,
    machine_type="cnc_router",
    required_machine_key=REGISTRY_CNC_MACHINE_CODE,
    workcenter_code=REGISTRY_CNC_WORKCENTER_CODE,
    operational_operation_code=REGISTRY_CNC_OPERATION_CODE,
    resource_mapping_status="pending_mapping",
    mapping_gaps=(
        "operation_catalog_key",
        "dry_run_task_key",
        "back_bevel_enabled_intake_capture",
    ),
)

CUTTING_SERVICE_CNC_BINDING = CncProductionResourceBinding(
    tpl_operation_key=None,
    dossier_operation_key=None,
    operation_catalog_key=None,
    production_task_type="cnc_routing",
    workstation_key="cnc_router",
    required_skill_key="cnc_operator",
    registry_skill_code=REGISTRY_CNC_SKILL_CODE,
    machine_type="cnc_router",
    required_machine_key=REGISTRY_CNC_MACHINE_CODE,
    workcenter_code=REGISTRY_CNC_WORKCENTER_CODE,
    operational_operation_code=REGISTRY_CNC_OPERATION_CODE,
    resource_mapping_status="pending_mapping",
    mapping_gaps=(
        "tpl_cnc_cutting_service_onboarding",
        "operation_catalog_key",
        "dossier_operation_key",
    ),
)


VOLUMETRIC_FACE_CUTTING_RULE = CncOperationRule(
    operation_key="cnc_face_cutting_plexiglas_3mm",
    display_name="Debitare CNC față Plexiglas 3 mm",
    operation_type=CncOperationType.CUTTING,
    material_family="plexiglas",
    material_name="Plexiglas 3 mm",
    thickness_mm=DEFAULT_FACE_PLEXI_THICKNESS_MM,
    basis_type=CncBasisType.PATH_PERIMETER,
    basis_key="face_cnc_cutting_perimeter",
    basis_label="Perimetru CNC față",
    passes=1,
    material_pricing_rate_key=None,
    material_key="plexiglas_3mm",
    production_binding=VOLUMETRIC_FACE_CUTTING_BINDING,
)

VOLUMETRIC_FACE_BEVEL_RULE = CncOperationRule(
    operation_key="cnc_face_bevel_plexiglas_3mm",
    display_name="Șanfren CNC față Plexiglas 3 mm",
    operation_type=CncOperationType.BEVEL,
    material_family="plexiglas",
    material_name="Plexiglas 3 mm",
    thickness_mm=DEFAULT_FACE_PLEXI_THICKNESS_MM,
    basis_type=CncBasisType.PATH_PERIMETER,
    basis_key="face_cnc_cutting_perimeter",
    basis_label="Perimetru CNC față",
    passes=1,
    material_pricing_rate_key=None,
    material_key="plexiglas_3mm",
    production_binding=VOLUMETRIC_FACE_BEVEL_BINDING,
)

VOLUMETRIC_BACKING_CUTTING_RULE = CncOperationRule(
    operation_key="cnc_backing_cutting_forex_10mm",
    display_name="Debitare CNC spate Forex 10 mm",
    operation_type=CncOperationType.CUTTING,
    material_family="forex",
    material_name="Forex 10 mm",
    thickness_mm=DEFAULT_FOREX_BACKING_THICKNESS_MM,
    basis_type=CncBasisType.PATH_PERIMETER,
    basis_key="backing_cnc_cutting_perimeter",
    basis_label="Perimetru CNC spate",
    passes=FOREX_10MM_CUTTING_PASSES_OWNER,
    depth_per_pass_mm=DEFAULT_DEPTH_PER_PASS_MM,
    owner_pass_override=True,
    material_pricing_rate_key=None,
    material_key="forex_10mm",
    production_binding=VOLUMETRIC_BACKING_CUTTING_BINDING,
)

VOLUMETRIC_BACKING_BEVEL_RULE = CncOperationRule(
    operation_key="cnc_backing_bevel_forex_10mm",
    display_name="Șanfren CNC spate Forex 10 mm",
    operation_type=CncOperationType.BEVEL,
    material_family="forex",
    material_name="Forex 10 mm",
    thickness_mm=DEFAULT_FOREX_BACKING_THICKNESS_MM,
    basis_type=CncBasisType.PATH_PERIMETER,
    basis_key="backing_cnc_cutting_perimeter",
    basis_label="Perimetru CNC spate",
    passes=FOREX_10MM_BEVEL_PASSES_OWNER,
    depth_per_pass_mm=DEFAULT_DEPTH_PER_PASS_MM,
    owner_pass_override=True,
    material_pricing_rate_key=None,
    material_key="forex_10mm",
    production_binding=VOLUMETRIC_BACKING_BEVEL_BINDING,
)


VOLUMETRIC_REQUIRED_CNC_OPERATION_KEYS: tuple[str, ...] = (
    "cnc_face_cutting_plexiglas_3mm",
    "cnc_face_bevel_plexiglas_3mm",
    "cnc_backing_cutting_forex_10mm",
    "cnc_backing_bevel_forex_10mm",
)


def build_volumetric_letters_cnc_operation_rows(
    geometry: Mapping[str, Any],
    *,
    backing_mode: VolumetricBackingMode = "none",
    configured_rate_eur_per_ml_pass: float | None = None,
) -> list[CncOperationPreviewRow]:
    """Preview CNC operation rows for TPL-VOLUMETRIC-LETTERS (not material rows)."""
    face_ml = _resolve_face_cnc_perimeter_ml(geometry)
    rows: list[CncOperationPreviewRow] = []

    if face_ml is not None:
        rows.append(
            _row_from_rule(
                VOLUMETRIC_FACE_CUTTING_RULE,
                face_ml,
                configured_rate_eur_per_ml_pass=configured_rate_eur_per_ml_pass,
            )
        )
        rows.append(
            _row_from_rule(
                VOLUMETRIC_FACE_BEVEL_RULE,
                face_ml,
                configured_rate_eur_per_ml_pass=configured_rate_eur_per_ml_pass,
            )
        )
    else:
        missing = CncOperationPreviewRow(
            key="cnc_face_cutting_plexiglas_3mm",
            display_name=VOLUMETRIC_FACE_CUTTING_RULE.display_name,
            operation_type=CncOperationType.CUTTING.value,
            material_family="plexiglas",
            material_name="Plexiglas 3 mm",
            thickness_mm=DEFAULT_FACE_PLEXI_THICKNESS_MM,
            basis_key="face_cnc_cutting_perimeter",
            basis_label="Perimetru CNC față",
            pricing_status="missing_geometry",
            warnings=["missing_face_cnc_perimeter"],
        )
        rows.append(missing)

    if backing_mode != "none":
        back_ml = _resolve_backing_cnc_perimeter_ml(geometry, face_perimeter_ml=face_ml)
        if back_ml is None:
            rows.append(
                CncOperationPreviewRow(
                    key=VOLUMETRIC_BACKING_CUTTING_RULE.operation_key,
                    display_name=VOLUMETRIC_BACKING_CUTTING_RULE.display_name,
                    operation_type=CncOperationType.CUTTING.value,
                    pricing_status="missing_geometry",
                    warnings=["missing_backing_cnc_perimeter"],
                )
            )
        else:
            rows.append(
                _row_from_rule(
                    VOLUMETRIC_BACKING_CUTTING_RULE,
                    back_ml,
                    configured_rate_eur_per_ml_pass=configured_rate_eur_per_ml_pass,
                )
            )
            if backing_mode == "forex_10_with_bevel":
                rows.append(
                    _row_from_rule(
                        VOLUMETRIC_BACKING_BEVEL_RULE,
                        back_ml,
                        configured_rate_eur_per_ml_pass=configured_rate_eur_per_ml_pass,
                    )
                )

    return rows


CLIENT_MATERIAL_CNC_WARNINGS: tuple[str, ...] = (
    "Material adus de client — nu se consumă stoc intern.",
    "Calitatea materialului clientului nu este garantată de atelier.",
    "Defecte ascunse, fisuri sau material nepotrivit CNC pot bloca lucrarea.",
    "Clientul trebuie să aducă material suplimentar pentru prindere/test/pierderi.",
)


def build_cutting_service_cnc_operation_rows(
    *,
    material_source: CncMaterialSource,
    perimeter_ml: float | None,
    thickness_mm: float,
    material_family: str,
    material_name: str,
    cutting_enabled: bool = True,
    bevel_enabled: bool = False,
    passes_override: int | None = None,
    owner_pass_override: bool = False,
    configured_rate_eur_per_ml_pass: float | None = None,
) -> tuple[list[CncOperationPreviewRow], list[str]]:
    """Foundation contract for future TPL-CNC-CUTTING-SERVICE — preview only."""
    warnings: list[str] = []
    if material_source == CncMaterialSource.CLIENT_SUPPLIED:
        warnings.extend(CLIENT_MATERIAL_CNC_WARNINGS)

    rows: list[CncOperationPreviewRow] = []
    if not cutting_enabled or perimeter_ml is None or perimeter_ml <= 0:
        return rows, warnings

    passes = passes_override if passes_override is not None else 1
    cut_rule = CncOperationRule(
        operation_key=f"cnc_cutting_{material_family}_{int(thickness_mm)}mm",
        display_name=f"Debitare CNC {material_name}",
        operation_type=CncOperationType.CUTTING,
        material_family=material_family,
        material_name=material_name,
        thickness_mm=thickness_mm,
        basis_type=CncBasisType.PATH_PERIMETER,
        basis_key="cutting_perimeter_ml",
        basis_label="Perimetru tăiere",
        passes=passes,
        depth_per_pass_mm=DEFAULT_DEPTH_PER_PASS_MM if owner_pass_override else None,
        owner_pass_override=owner_pass_override,
        material_pricing_rate_key=None,
        material_key=f"{material_family}_{int(thickness_mm)}mm",
        production_binding=CUTTING_SERVICE_CNC_BINDING,
    )
    rows.append(
        _row_from_rule(
            cut_rule,
            perimeter_ml,
            configured_rate_eur_per_ml_pass=configured_rate_eur_per_ml_pass,
        )
    )

    if bevel_enabled:
        bevel_rule = CncOperationRule(
            operation_key=f"cnc_bevel_{material_family}_{int(thickness_mm)}mm",
            display_name=f"Șanfren CNC {material_name}",
            operation_type=CncOperationType.BEVEL,
            material_family=material_family,
            material_name=material_name,
            thickness_mm=thickness_mm,
            basis_type=CncBasisType.PATH_PERIMETER,
            basis_key="cutting_perimeter_ml",
            basis_label="Perimetru tăiere",
            passes=1,
            material_pricing_rate_key=None,
            material_key=f"{material_family}_{int(thickness_mm)}mm",
            production_binding=CUTTING_SERVICE_CNC_BINDING,
        )
        rows.append(
            _row_from_rule(
                bevel_rule,
                perimeter_ml,
                configured_rate_eur_per_ml_pass=configured_rate_eur_per_ml_pass,
            )
        )

    return rows, warnings


def resolve_volumetric_backing_mode(
    *,
    backing_confirmed: bool,
    back_bevel_enabled: bool,
) -> VolumetricBackingMode:
    if not backing_confirmed:
        return "none"
    if back_bevel_enabled:
        return "forex_10_with_bevel"
    return "forex_10_no_bevel"


def rows_to_schema_dicts(rows: Sequence[CncOperationPreviewRow]) -> list[dict[str, Any]]:
    return [row.to_dict() for row in rows]


def cnc_preview_row_to_task_candidate_hints(row: CncOperationPreviewRow) -> dict[str, Any]:
    """Bridge shared CNC rows → task dry-run / production preview vocabulary (read-only).

    Intake V4 task generation today uses V3 operation catalog seeds and
    tpl_volumetric_operation_keys_service — this helper documents the target join
  point without creating ExecutionTask rows.
    """
    task_key = row.tpl_operation_key or row.key
    return {
        "task_key": task_key,
        "operation_key": row.dossier_operation_key,
        "operation_catalog_key": row.operation_catalog_key,
        "operation_group": "cnc_cutting",
        "station_hint": row.workstation_key,
        "role_hint": row.required_skill_key,
        "registry_skill_code": row.registry_skill_code,
        "required_machine_key": row.required_machine_key,
        "machine_type": row.machine_type,
        "workcenter_code": row.workcenter_code,
        "operational_operation_code": row.operational_operation_code,
        "production_task_type": row.production_task_type,
        "quantity_ml": row.quantity,
        "passes": row.passes,
        "operation_equivalent_quantity": row.operation_equivalent_quantity,
        "resource_mapping_status": row.resource_mapping_status,
        "mapping_gaps": list(row.mapping_gaps),
        "pricing_rate_key": row.pricing_rate_key,
        "pricing_status": row.pricing_status,
    }
