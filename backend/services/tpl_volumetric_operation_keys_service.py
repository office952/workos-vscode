"""Canonical operation keys registry for TPL-VOLUMETRIC-LETTERS.

Runtime canonical helper mirrors current TPL dossier / ProductSystem operation keys
until ProductSystem operation registry is made runtime-readable.

Read-only alignment pack — no ExecutionPlan / ExecutionTask writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

TPL_VOLUMETRIC_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"
REGISTRY_SOURCE = "TPL-VOLUMETRIC-LETTERS canonical operation registry"

# Dossier priced_operation keys — seed_tpl_volumetric_letters_dossier costengine_mapping
DOSSIER_OPERATION_KEYS = frozenset(
    {
        "vector_prep",
        "face_cnc_cut",
        "back_cut",
        "side_forming",
        "return_face_bonding",
        "led_install_letters",
        "electrical_letters",
        "painting",
        "vinyl_application",
        "packaging_letters",
        "mounting_template_cnc_cut",
        "qc_letters",
    }
)

# ProductSystem seed adds assembly_letters; runtime injects return_vinyl_application
PRODUCT_SYSTEM_OPERATION_KEYS = DOSSIER_OPERATION_KEYS | frozenset(
    {"assembly_letters", "return_vinyl_application"}
)

TemplateAlignmentStatus = Literal["aligned", "partial", "missing", "not_applicable"]


@dataclass(frozen=True)
class TplVolumetricOperationSpec:
    operation_key: str
    label: str
    station_hint: str
    role_hint: str
    dossier_operation_key: str | None
    future_execution_task_type: str
    future_process_id: str | None
    template_backed: bool
    dossier_backed: bool
    requires_material_job: bool
    requires_finish: bool
    requires_mounting_data: bool
    critical_for_execution: bool
    can_generate_task_candidate: bool
    provisional_reason: str | None
    dry_run_task_key: str | None
    handoff_group_keys: tuple[str, ...] = ()
    catalog_operation_codes: tuple[str, ...] = ()


def _spec(
    operation_key: str,
    *,
    label: str,
    station_hint: str,
    role_hint: str,
    dossier_operation_key: str | None,
    future_execution_task_type: str,
    future_process_id: str | None = None,
    template_backed: bool = True,
    dossier_backed: bool | None = None,
    requires_material_job: bool = False,
    requires_finish: bool = False,
    requires_mounting_data: bool = False,
    critical_for_execution: bool = True,
    can_generate_task_candidate: bool = True,
    provisional_reason: str | None = None,
    dry_run_task_key: str | None = None,
    handoff_group_keys: tuple[str, ...] = (),
    catalog_operation_codes: tuple[str, ...] = (),
) -> TplVolumetricOperationSpec:
    dossier_backed_resolved = (
        dossier_backed
        if dossier_backed is not None
        else bool(
            dossier_operation_key
            and dossier_operation_key in DOSSIER_OPERATION_KEYS
        )
    )
    if future_process_id is None and dossier_operation_key:
        future_process_id = dossier_operation_key
    if dry_run_task_key is None and can_generate_task_candidate:
        dry_run_task_key = operation_key
    return TplVolumetricOperationSpec(
        operation_key=operation_key,
        label=label,
        station_hint=station_hint,
        role_hint=role_hint,
        dossier_operation_key=dossier_operation_key,
        future_execution_task_type=future_execution_task_type,
        future_process_id=future_process_id,
        template_backed=template_backed,
        dossier_backed=dossier_backed_resolved,
        requires_material_job=requires_material_job,
        requires_finish=requires_finish,
        requires_mounting_data=requires_mounting_data,
        critical_for_execution=critical_for_execution,
        can_generate_task_candidate=can_generate_task_candidate,
        provisional_reason=provisional_reason,
        dry_run_task_key=dry_run_task_key,
        handoff_group_keys=handoff_group_keys,
        catalog_operation_codes=catalog_operation_codes,
    )


TPL_VOLUMETRIC_OPERATION_KEYS: dict[str, TplVolumetricOperationSpec] = {
    # Preflight
    "preflight_svg_review": _spec(
        "preflight_svg_review",
        label="Verificare SVG și roluri layere",
        station_hint="prepress",
        role_hint="operator_prepress",
        dossier_operation_key="vector_prep",
        future_execution_task_type="file_preparation",
        critical_for_execution=True,
        dry_run_task_key="preflight_vector_and_layers",
        handoff_group_keys=("preflight_qc",),
        catalog_operation_codes=("graphic_vector_preflight", "confirmed_production_model"),
    ),
    "production_file_preparation": _spec(
        "production_file_preparation",
        label="Pregătire fișiere producție / CNC",
        station_hint="cnc_preparation_station",
        role_hint="cnc_preparation",
        dossier_operation_key="vector_prep",
        future_execution_task_type="file_preparation",
        critical_for_execution=True,
        dry_run_task_key="cnc_file_preparation",
        handoff_group_keys=("preflight_qc", "cnc_cutting"),
        catalog_operation_codes=("cnc_file_preparation",),
    ),
    "artwork_print_preparation": _spec(
        "artwork_print_preparation",
        label="Pregătire artwork print",
        station_hint="prepress",
        role_hint="operator_prepress",
        dossier_operation_key="vector_prep",
        future_execution_task_type="file_preparation",
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="print artwork prep folded into vinyl/print material jobs — no separate dry-run candidate",
        dry_run_task_key=None,
        handoff_group_keys=("vinyl_print_finish",),
    ),
    # CNC / debitare
    "cnc_face_cutting": _spec(
        "cnc_face_cutting",
        label="Debitare fețe plexiglas",
        station_hint="cnc_router",
        role_hint="cnc_operator",
        dossier_operation_key="face_cnc_cut",
        future_execution_task_type="cnc_routing",
        requires_material_job=True,
        critical_for_execution=True,
        dry_run_task_key="cnc_face_cutting",
        handoff_group_keys=("cnc_cutting",),
        catalog_operation_codes=("face_and_backing_cnc_cut",),
    ),
    "cnc_face_bevel": _spec(
        "cnc_face_bevel",
        label="Șanfren față plexiglas",
        station_hint="cnc_router",
        role_hint="cnc_operator",
        dossier_operation_key="face_cnc_cut",
        future_execution_task_type="cnc_routing",
        dossier_backed=True,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="face bevel bundled in face_cnc_cut dossier pricing — no separate dry-run task",
        dry_run_task_key=None,
        handoff_group_keys=("cnc_cutting",),
    ),
    "cnc_backing_cutting": _spec(
        "cnc_backing_cutting",
        label="Debitare spate Forex",
        station_hint="cnc_router",
        role_hint="cnc_operator",
        dossier_operation_key="back_cut",
        future_execution_task_type="cnc_routing",
        requires_material_job=True,
        critical_for_execution=True,
        dry_run_task_key="cnc_backing_cutting",
        handoff_group_keys=("cnc_cutting",),
        catalog_operation_codes=("face_and_backing_cnc_cut",),
    ),
    "cnc_backing_bevel_optional": _spec(
        "cnc_backing_bevel_optional",
        label="Șanfren spate Forex (opțional)",
        station_hint="cnc_router",
        role_hint="cnc_operator",
        dossier_operation_key="back_cut",
        future_execution_task_type="cnc_routing",
        dossier_backed=True,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="back bevel optional input exists in dossier but V4 form does not capture back_bevel_enabled for task split",
        dry_run_task_key=None,
        handoff_group_keys=("cnc_cutting",),
    ),
    "mounting_template_cutting": _spec(
        "mounting_template_cutting",
        label="Debitare șablon montaj",
        station_hint="cnc_router",
        role_hint="cnc_operator",
        dossier_operation_key="mounting_template_cnc_cut",
        future_execution_task_type="cnc_routing",
        requires_mounting_data=True,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="mounting template job requires mounting_template_enabled — no dry-run candidate yet",
        dry_run_task_key=None,
        handoff_group_keys=("preflight_qc",),
    ),
    # Colant / print
    "vinyl_cutting": _spec(
        "vinyl_cutting",
        label="Tăiere colant Oracal",
        station_hint="workbench",
        role_hint="vinyl_operator",
        dossier_operation_key="vinyl_application",
        future_execution_task_type="vinyl_cutting",
        requires_material_job=True,
        requires_finish=True,
        critical_for_execution=True,
        dry_run_task_key="oracal_vinyl_cutting",
        handoff_group_keys=("vinyl_print_finish",),
        catalog_operation_codes=("return_vinyl_application_workbench", "face_vinyl_application_final"),
    ),
    "printed_artwork_production": _spec(
        "printed_artwork_production",
        label="Print artwork",
        station_hint="workbench",
        role_hint="vinyl_operator",
        dossier_operation_key="vinyl_application",
        future_execution_task_type="vinyl_cutting",
        requires_material_job=True,
        requires_finish=True,
        critical_for_execution=True,
        dry_run_task_key="print_artwork",
        handoff_group_keys=("vinyl_print_finish",),
    ),
    "print_lamination": _spec(
        "print_lamination",
        label="Laminare print",
        station_hint="workbench",
        role_hint="vinyl_operator",
        dossier_operation_key="vinyl_application",
        future_execution_task_type="vinyl_cutting",
        requires_material_job=True,
        requires_finish=True,
        critical_for_execution=True,
        dry_run_task_key="laminate_print",
        handoff_group_keys=("vinyl_print_finish",),
    ),
    "face_finish_application": _spec(
        "face_finish_application",
        label="Aplicare colant / print pe fețe",
        station_hint="workbench",
        role_hint="vinyl_operator",
        dossier_operation_key="vinyl_application",
        future_execution_task_type="vinyl_cutting",
        requires_finish=True,
        critical_for_execution=True,
        dry_run_task_key="face_vinyl_application",
        handoff_group_keys=("vinyl_print_finish",),
        catalog_operation_codes=("face_vinyl_application_final",),
    ),
    # Cant / lateral
    "return_side_forming": _spec(
        "return_side_forming",
        label="Modelare canturi",
        station_hint="return_forming_machine",
        role_hint="return_forming_operator",
        dossier_operation_key="side_forming",
        future_execution_task_type="edge_bending",
        requires_material_job=True,
        critical_for_execution=True,
        dry_run_task_key="return_side_forming",
        handoff_group_keys=("return_forming",),
        catalog_operation_codes=("return_forming_file_preparation", "return_side_forming"),
    ),
    "return_side_numbering": _spec(
        "return_side_numbering",
        label="Numerotare canturi",
        station_hint="return_forming_machine",
        role_hint="return_forming_operator",
        dossier_operation_key="side_forming",
        future_execution_task_type="edge_bending",
        dossier_backed=True,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="return numbering documented in catalog but not split from side_forming dossier op",
        dry_run_task_key=None,
        handoff_group_keys=("return_forming",),
    ),
    "return_side_bonding": _spec(
        "return_side_bonding",
        label="Lipire canturi pe fețe",
        station_hint="assembly_bench",
        role_hint="assembly_operator",
        dossier_operation_key="return_face_bonding",
        future_execution_task_type="welding",
        requires_material_job=True,
        critical_for_execution=True,
        dry_run_task_key="return_face_bonding",
        handoff_group_keys=("return_bonding",),
        catalog_operation_codes=("return_face_bonding",),
    ),
    # LED / electric
    "led_layout_preparation": _spec(
        "led_layout_preparation",
        label="Pregătire layout LED",
        station_hint="electrical_bench",
        role_hint="electrical_operator",
        dossier_operation_key="led_install_letters",
        future_execution_task_type="led_assembly",
        dossier_backed=True,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="LED pitch / module layout folded into led_install_letters — no separate dry-run task",
        dry_run_task_key=None,
        handoff_group_keys=("led_electrical",),
    ),
    "led_module_install": _spec(
        "led_module_install",
        label="Montaj module LED",
        station_hint="electrical_bench",
        role_hint="electrical_operator",
        dossier_operation_key="led_install_letters",
        future_execution_task_type="led_assembly",
        requires_material_job=True,
        critical_for_execution=True,
        dry_run_task_key="led_module_install",
        handoff_group_keys=("led_electrical",),
        catalog_operation_codes=("led_installation_wiring_and_light_test",),
    ),
    "electrical_wiring": _spec(
        "electrical_wiring",
        label="Cablaj electric",
        station_hint="electrical_bench",
        role_hint="electrical_operator",
        dossier_operation_key="electrical_letters",
        future_execution_task_type="led_wiring",
        requires_material_job=True,
        critical_for_execution=True,
        dry_run_task_key="psu_electrical_wiring",
        handoff_group_keys=("led_electrical",),
        catalog_operation_codes=("led_installation_wiring_and_light_test",),
    ),
    "psu_installation": _spec(
        "psu_installation",
        label="Montare surse LED",
        station_hint="electrical_bench",
        role_hint="electrical_operator",
        dossier_operation_key="electrical_letters",
        future_execution_task_type="led_wiring",
        dossier_backed=True,
        critical_for_execution=True,
        can_generate_task_candidate=False,
        provisional_reason="PSU install shares electrical_letters dossier op with wiring — dry-run uses psu_electrical_wiring task",
        dry_run_task_key=None,
        handoff_group_keys=("led_electrical",),
    ),
    "light_test": _spec(
        "light_test",
        label="Test lumină / verificare electrică",
        station_hint="electrical_bench",
        role_hint="qc_operator",
        dossier_operation_key="qc_letters",
        future_execution_task_type="quality_control",
        critical_for_execution=True,
        dry_run_task_key="light_test_qc",
        handoff_group_keys=("led_electrical", "preflight_qc"),
        catalog_operation_codes=("led_installation_wiring_and_light_test",),
    ),
    # Asamblare / QC / ambalare
    "letter_assembly": _spec(
        "letter_assembly",
        label="Asamblare litere",
        station_hint="assembly_bench",
        role_hint="assembly_operator",
        dossier_operation_key="assembly_letters",
        future_execution_task_type="volumetric_letter_assembly",
        future_process_id="assembly_letters",
        dossier_backed=False,
        template_backed=True,
        critical_for_execution=True,
        can_generate_task_candidate=True,
        provisional_reason="assembly_letters in ProductSystem but execution task schema mapping is not confirmed",
        dry_run_task_key="letter_assembly",
        handoff_group_keys=("assembly",),
        catalog_operation_codes=("letter_assembly_no_shared_support",),
    ),
    "quality_control": _spec(
        "quality_control",
        label="Verificare calitate finală",
        station_hint="qc_station",
        role_hint="qc_operator",
        dossier_operation_key="qc_letters",
        future_execution_task_type="quality_control",
        critical_for_execution=True,
        dry_run_task_key="light_test_qc",
        handoff_group_keys=("preflight_qc",),
    ),
    "cleaning": _spec(
        "cleaning",
        label="Curățare înainte de ambalare",
        station_hint="assembly_bench",
        role_hint="assembly_operator",
        dossier_operation_key=None,
        future_execution_task_type="volumetric_letter_assembly",
        template_backed=False,
        dossier_backed=False,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="cleaning step documented in catalog but not a priced dossier operation",
        dry_run_task_key=None,
        handoff_group_keys=("assembly",),
    ),
    "packaging": _spec(
        "packaging",
        label="Ambalare / pregătire livrare",
        station_hint="packing_area",
        role_hint="assembly_operator",
        dossier_operation_key="packaging_letters",
        future_execution_task_type="packaging",
        critical_for_execution=True,
        dry_run_task_key="packaging_delivery_prep",
        handoff_group_keys=("preflight_qc",),
        catalog_operation_codes=("stretch_wrap_and_delivery_mounting_package",),
    ),
    # Montaj / structură
    "mounting_template_preparation": _spec(
        "mounting_template_preparation",
        label="Pregătire șablon montaj",
        station_hint="cnc_router",
        role_hint="cnc_operator",
        dossier_operation_key="mounting_template_cnc_cut",
        future_execution_task_type="cnc_routing",
        requires_mounting_data=True,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="mounting template requires V4 mounting_template_enabled capture — partial handoff coverage",
        dry_run_task_key=None,
        handoff_group_keys=("preflight_qc",),
    ),
    "mounting_structure_preparation": _spec(
        "mounting_structure_preparation",
        label="Pregătire structură montaj (bare)",
        station_hint="assembly_bench",
        role_hint="assembly_operator",
        dossier_operation_key="mounting_template_cnc_cut",
        future_execution_task_type="cnc_routing",
        requires_mounting_data=True,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="mounting bar profile/count not captured in V4 form for task split",
        dry_run_task_key=None,
    ),
    "field_installation_preparation": _spec(
        "field_installation_preparation",
        label="Pregătire montaj pe teren",
        station_hint="packing_area",
        role_hint="assembly_operator",
        dossier_operation_key="packaging_letters",
        future_execution_task_type="packaging",
        dossier_backed=True,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="field install prep bundled in packaging/delivery catalog op — no separate task",
        dry_run_task_key=None,
        handoff_group_keys=("preflight_qc",),
        catalog_operation_codes=("stretch_wrap_and_delivery_mounting_package",),
    ),
    # Painting — dossier priced op without dedicated dry-run candidate
    "return_painting": _spec(
        "return_painting",
        label="Vopsire cant (RAL)",
        station_hint="paint_booth",
        role_hint="paint_operator",
        dossier_operation_key="painting",
        future_execution_task_type="volumetric_letter_assembly",
        requires_finish=True,
        critical_for_execution=False,
        can_generate_task_candidate=False,
        provisional_reason="painting dossier op exists but finish-dependent dry-run candidate not yet split",
        dry_run_task_key=None,
        catalog_operation_codes=("return_painting_after_assembly",),
    ),
}

# Catalog doc operation_code → canonical operation_key
CATALOG_TO_CANONICAL_OPERATIONS: dict[str, tuple[str, ...]] = {}
_catalog_to_canonical_sets: dict[str, list[str]] = {}
for _spec_obj in TPL_VOLUMETRIC_OPERATION_KEYS.values():
    for code in _spec_obj.catalog_operation_codes:
        keys = _catalog_to_canonical_sets.setdefault(code, [])
        if _spec_obj.operation_key not in keys:
            keys.append(_spec_obj.operation_key)
CATALOG_TO_CANONICAL_OPERATIONS = {
    code: tuple(keys) for code, keys in _catalog_to_canonical_sets.items()
}
CATALOG_TO_CANONICAL_OPERATION: dict[str, str] = {
    code: keys[0] for code, keys in CATALOG_TO_CANONICAL_OPERATIONS.items() if keys
}

# Legacy dossier key → canonical (primary) operation_key
DOSSIER_TO_CANONICAL_OPERATION: dict[str, str] = {}
for _spec_obj in TPL_VOLUMETRIC_OPERATION_KEYS.values():
    if _spec_obj.dossier_operation_key:
        DOSSIER_TO_CANONICAL_OPERATION.setdefault(
            _spec_obj.dossier_operation_key, _spec_obj.operation_key
        )

# dry_run task_key → canonical operation_key
DRY_RUN_TASK_TO_CANONICAL: dict[str, str] = {
    spec.dry_run_task_key: spec.operation_key
    for spec in TPL_VOLUMETRIC_OPERATION_KEYS.values()
    if spec.dry_run_task_key
}

# Material job → canonical operation_key (primary task for job)
MATERIAL_JOB_TO_CANONICAL: dict[str, str] = {
    "face_plexiglas_cutting": "cnc_face_cutting",
    "forex_backing_cutting": "cnc_backing_cutting",
    "oracal_vinyl_cutting": "vinyl_cutting",
    "print_vinyl_artwork": "printed_artwork_production",
    "laminate_vinyl_artwork": "print_lamination",
    "return_profile_material": "return_side_forming",
    "led_modules_install": "led_module_install",
    "psu_electrical": "electrical_wiring",
}

# Handoff group → expected canonical keys when group is active
HANDOFF_GROUP_CANONICAL_KEYS: dict[str, tuple[str, ...]] = {
    "preflight_qc": (
        "preflight_svg_review",
        "production_file_preparation",
        "packaging",
        "quality_control",
    ),
    "cnc_cutting": ("production_file_preparation", "cnc_face_cutting", "cnc_backing_cutting"),
    "vinyl_print_finish": (
        "vinyl_cutting",
        "printed_artwork_production",
        "print_lamination",
        "face_finish_application",
    ),
    "return_forming": ("return_side_forming",),
    "return_bonding": ("return_side_bonding",),
    "led_electrical": (
        "led_module_install",
        "electrical_wiring",
        "psu_installation",
        "light_test",
    ),
    "assembly": ("letter_assembly",),
}

# Explicit handoff → canonical → dry_run → future execution mapping rows
HANDOFF_CANONICAL_MAPPING_TABLE: list[dict[str, Any]] = []


def _build_mapping_table() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for group_key, canonical_keys in HANDOFF_GROUP_CANONICAL_KEYS.items():
        for canonical_key in canonical_keys:
            spec = TPL_VOLUMETRIC_OPERATION_KEYS[canonical_key]
            pair = (group_key, canonical_key)
            if pair in seen:
                continue
            seen.add(pair)
            if spec.can_generate_task_candidate and spec.dry_run_task_key:
                status = "confirmed"
                provisional = bool(spec.provisional_reason)
            elif spec.dossier_backed or spec.template_backed:
                status = "partial"
                provisional = True
            else:
                status = "missing"
                provisional = True
            rows.append(
                {
                    "handoff_group": group_key,
                    "canonical_operation_key": canonical_key,
                    "dry_run_task_key": spec.dry_run_task_key,
                    "future_execution_task_type": spec.future_execution_task_type,
                    "future_process_id": spec.future_process_id,
                    "dossier_operation_key": spec.dossier_operation_key,
                    "template_backed": spec.template_backed,
                    "dossier_backed": spec.dossier_backed,
                    "mapping_status": status,
                    "provisional": provisional,
                    "provisional_reason": spec.provisional_reason,
                }
            )
    return rows


HANDOFF_CANONICAL_MAPPING_TABLE = _build_mapping_table()


@dataclass
class TemplateAlignmentInfo:
    status: TemplateAlignmentStatus
    provisional: bool
    source: str = REGISTRY_SOURCE
    missing_keys: list[str] = field(default_factory=list)
    partial_keys: list[str] = field(default_factory=list)


def get_operation_spec(canonical_operation_key: str) -> TplVolumetricOperationSpec | None:
    return TPL_VOLUMETRIC_OPERATION_KEYS.get(canonical_operation_key)


def resolve_canonical_from_dossier(dossier_operation_key: str | None) -> str | None:
    if not dossier_operation_key:
        return None
    return DOSSIER_TO_CANONICAL_OPERATION.get(dossier_operation_key)


def resolve_canonical_from_catalog(catalog_code: str | None) -> str | None:
    if not catalog_code:
        return None
    return CATALOG_TO_CANONICAL_OPERATION.get(catalog_code)


def resolve_canonical_keys_from_catalog(catalog_code: str | None) -> list[str]:
    if not catalog_code:
        return []
    return list(CATALOG_TO_CANONICAL_OPERATIONS.get(catalog_code, ()))


def resolve_canonical_from_dry_run_task(task_key: str) -> str | None:
    return DRY_RUN_TASK_TO_CANONICAL.get(task_key)


def resolve_canonical_from_material_job(job_key: str) -> str | None:
    return MATERIAL_JOB_TO_CANONICAL.get(job_key)


def operation_alignment_status(spec: TplVolumetricOperationSpec) -> TemplateAlignmentStatus:
    if not spec.can_generate_task_candidate:
        if spec.dossier_backed or spec.template_backed:
            return "partial"
        return "missing"
    if spec.provisional_reason:
        return "partial"
    if spec.dossier_backed and spec.dry_run_task_key:
        return "aligned"
    if spec.template_backed:
        return "partial"
    return "missing"


def evaluate_handoff_group_alignment(
    group_key: str,
    *,
    active: bool,
    active_material_job_keys: set[str] | frozenset[str] | None = None,
) -> tuple[list[str], TemplateAlignmentInfo]:
    """Return canonical keys + alignment info for a handoff operation group."""
    if not active:
        return [], TemplateAlignmentInfo(
            status="not_applicable",
            provisional=False,
            source=REGISTRY_SOURCE,
        )

    expected = HANDOFF_GROUP_CANONICAL_KEYS.get(group_key, ())
    if not expected:
        return [], TemplateAlignmentInfo(
            status="missing",
            provisional=True,
            source=REGISTRY_SOURCE,
            missing_keys=[group_key],
        )

    jobs = active_material_job_keys or frozenset()
    applicable: list[str] = []
    missing: list[str] = []
    partial: list[str] = []

    for key in expected:
        spec = TPL_VOLUMETRIC_OPERATION_KEYS[key]
        if spec.requires_material_job:
            related_jobs = [
                j for j, c in MATERIAL_JOB_TO_CANONICAL.items() if c == key
            ]
            if related_jobs and not (jobs & set(related_jobs)):
                continue
        if spec.requires_mounting_data:
            partial.append(key)
            continue
        applicable.append(key)
        status = operation_alignment_status(spec)
        if status == "missing":
            missing.append(key)
        elif status == "partial":
            partial.append(key)

    if not applicable:
        return list(expected), TemplateAlignmentInfo(
            status="not_applicable",
            provisional=False,
            source=REGISTRY_SOURCE,
        )

    if missing:
        overall: TemplateAlignmentStatus = "missing"
    elif partial:
        overall = "partial"
    else:
        overall = "aligned"

    return list(applicable), TemplateAlignmentInfo(
        status=overall,
        provisional=overall in ("partial", "missing"),
        source=REGISTRY_SOURCE,
        missing_keys=missing,
        partial_keys=partial,
    )


def enrich_task_candidate_alignment(
    *,
    task_key: str,
    operation_key: str | None,
    catalog_code: str | None = None,
    provisional: bool,
) -> dict[str, Any]:
    """Derive canonical alignment fields for a dry-run task candidate."""
    canonical = (
        resolve_canonical_from_dry_run_task(task_key)
        or resolve_canonical_from_catalog(catalog_code)
        or resolve_canonical_from_dossier(operation_key)
        or operation_key
    )
    spec = get_operation_spec(canonical) if canonical else None
    if spec is None:
        return {
            "canonical_operation_key": canonical,
            "template_alignment_status": "missing",
            "dossier_backed": False,
            "critical_for_execution": False,
            "future_execution_task_type": None,
            "provisional_reason": "canonical operation key not in registry",
            "provisional": True,
        }

    alignment = operation_alignment_status(spec)
    resolved_provisional = provisional or bool(spec.provisional_reason)
    if alignment == "aligned" and not spec.provisional_reason:
        resolved_provisional = False

    return {
        "canonical_operation_key": spec.operation_key,
        "template_alignment_status": alignment,
        "dossier_backed": spec.dossier_backed,
        "critical_for_execution": spec.critical_for_execution,
        "future_execution_task_type": spec.future_execution_task_type,
        "provisional_reason": spec.provisional_reason if resolved_provisional else None,
        "provisional": resolved_provisional,
        "template_backed": spec.template_backed and alignment != "missing",
    }


@dataclass
class TemplateOperationAlignmentSummary:
    status: TemplateAlignmentStatus
    aligned_count: int
    partial_count: int
    missing_count: int
    not_applicable_count: int
    critical_missing_count: int
    critical_partial_count: int
    blocks_real_task_generation: bool
    provisional_critical_tasks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "aligned_count": self.aligned_count,
            "partial_count": self.partial_count,
            "missing_count": self.missing_count,
            "not_applicable_count": self.not_applicable_count,
            "critical_missing_count": self.critical_missing_count,
            "critical_partial_count": self.critical_partial_count,
            "blocks_real_task_generation": self.blocks_real_task_generation,
            "provisional_critical_tasks": self.provisional_critical_tasks,
            "source": REGISTRY_SOURCE,
        }


def summarize_template_operation_alignment(
    *,
    handoff_groups: list[dict[str, Any]] | None = None,
    task_candidates: list[dict[str, Any]] | None = None,
) -> TemplateOperationAlignmentSummary:
    """Aggregate alignment from handoff groups and/or dry-run candidates."""
    aligned = partial = missing = not_applicable = 0
    critical_missing = critical_partial = 0
    provisional_critical: list[str] = []

    if handoff_groups:
        for group in handoff_groups:
            alignment = group.get("template_alignment") or {}
            status = alignment.get("status", "missing")
            if status == "aligned":
                aligned += 1
            elif status == "partial":
                partial += 1
            elif status == "not_applicable":
                not_applicable += 1
            else:
                missing += 1

    if task_candidates:
        seen_keys: set[str] = set()
        for cand in task_candidates:
            key = cand.get("canonical_operation_key") or cand.get("task_key")
            if not key or key in seen_keys:
                continue
            seen_keys.add(key)
            spec = get_operation_spec(str(cand.get("canonical_operation_key") or ""))
            if spec is None:
                continue
            status = cand.get("template_alignment_status") or operation_alignment_status(spec)
            is_provisional = bool(cand.get("provisional"))
            if spec.critical_for_execution:
                if status == "missing":
                    critical_missing += 1
                elif status == "partial" or is_provisional:
                    critical_partial += 1
                    if is_provisional and spec.dry_run_task_key:
                        provisional_critical.append(spec.dry_run_task_key)

    blocks = critical_missing > 0 or critical_partial > 0

    if missing > 0 or critical_missing > 0:
        overall: TemplateAlignmentStatus = "missing" if critical_missing else "partial"
    elif partial > 0 or critical_partial > 0:
        overall = "partial"
    elif aligned > 0:
        overall = "aligned"
    else:
        overall = "partial"

    return TemplateOperationAlignmentSummary(
        status=overall,
        aligned_count=aligned,
        partial_count=partial,
        missing_count=missing,
        not_applicable_count=not_applicable,
        critical_missing_count=critical_missing,
        critical_partial_count=critical_partial,
        blocks_real_task_generation=blocks,
        provisional_critical_tasks=sorted(set(provisional_critical)),
    )


def list_critical_operation_keys() -> list[str]:
    return [
        key
        for key, spec in TPL_VOLUMETRIC_OPERATION_KEYS.items()
        if spec.critical_for_execution
    ]


def get_mapping_catalog() -> dict[str, Any]:
    """Read-only export for QA / template contract consumers."""
    return {
        "template_code": TPL_VOLUMETRIC_TEMPLATE_CODE,
        "registry_source": REGISTRY_SOURCE,
        "dossier_operation_keys": sorted(DOSSIER_OPERATION_KEYS),
        "product_system_operation_keys": sorted(PRODUCT_SYSTEM_OPERATION_KEYS),
        "canonical_operation_keys": sorted(TPL_VOLUMETRIC_OPERATION_KEYS.keys()),
        "handoff_group_canonical_keys": {
            k: list(v) for k, v in HANDOFF_GROUP_CANONICAL_KEYS.items()
        },
        "mapping_table": HANDOFF_CANONICAL_MAPPING_TABLE,
        "catalog_to_canonical": dict(CATALOG_TO_CANONICAL_OPERATION),
        "catalog_to_canonical_all": {
            key: list(value) for key, value in CATALOG_TO_CANONICAL_OPERATIONS.items()
        },
        "dossier_to_canonical": dict(DOSSIER_TO_CANONICAL_OPERATION),
    }
