"""Read-only assembly preview compiler for Intake V6.

This service derives a composed assembly state and preview-only operational
grouping from the current workspace payload. It does not write to the database
or create execution tasks.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from schemas.intake_v4 import (
    IntakeV4LayerBindingContract,
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialQuantityRow,
    IntakeV4NestingPreviewPartRow,
    IntakeV4WorkspacePayload,
)
from schemas.intake_v6_assembly import (
    AssemblyDraft,
    AssemblyDraftChangeLogEntry,
    ComponentInstance,
    ConsolidatedTask,
    OperationCandidate,
    OperationCandidateMeasure,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown_with_registry

PRIMARY_FAMILY = "volumetric_signage"
LETTERS_COMPONENT_ID = "cmp_volumetric_letters"
LOGO_COMPONENT_ID = "cmp_volumetric_logo"
LOGO_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO_v1"
LOGO_ROLES = frozenset({"logo", "printed_artwork"})
DEFAULT_FACE_MATERIAL_CODE = "PLEXI_FACE_3MM"
DEFAULT_FACE_THICKNESS_MM = 3.0
DEFAULT_FINISH_CODE = "face_standard"
DEFAULT_COLOR_CODE = "shared_default"
DEFAULT_MACHINE_TYPE = "cnc_router"
DEFAULT_WORKCENTER = "WC_CNC"
DEFAULT_SETUP_GROUP_KEY = "cnc_router|plexi|3mm|shared_default"
DEFAULT_DEPENDENCY_GROUP = "pre_assembly_faces"
PRINT_WORKCENTER = "LARGE_FORMAT_PRINT"


def _slug(value: str | None) -> str:
    if not value:
        return ""
    return str(value).strip().lower().replace(" ", "-")


def _component_layer_slugs(component: ComponentInstance, payload: IntakeV4WorkspacePayload) -> set[str]:
    slugs = {_slug(key) for key in component.source_layer_keys}
    layer_setup = payload.layer_role_setup
    if layer_setup is None:
        return {slug for slug in slugs if slug}
    for layer in layer_setup.layers:
        if layer.layer_key in component.source_layer_keys or (layer.layer_id and layer.layer_id in component.source_layer_keys):
            slugs.add(_slug(layer.layer_name))
            slugs.add(_slug(layer.layer_key))
    return {slug for slug in slugs if slug}


def _parts_for_component(
    component: ComponentInstance,
    payload: IntakeV4WorkspacePayload,
    breakdown: IntakeV4MaterialBreakdownResponse | None,
) -> list[IntakeV4NestingPreviewPartRow]:
    if breakdown is None or breakdown.nesting_preview is None:
        return []
    component_slugs = _component_layer_slugs(component, payload)
    out: list[IntakeV4NestingPreviewPartRow] = []
    for part in breakdown.nesting_preview.parts:
        if _slug(part.source_layer_name) in component_slugs:
            out.append(part)
    return out


def _sum_or_none(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return round(sum(present), 6)


def _find_material_row(
    component: ComponentInstance,
    payload: IntakeV4WorkspacePayload,
    breakdown: IntakeV4MaterialBreakdownResponse | None,
) -> IntakeV4MaterialQuantityRow | None:
    if breakdown is None:
        return None
    if component.component_type == "volumetric_letters":
        return next((row for row in breakdown.material_rows if row.material_key == "plexiglas_face"), None)

    parts = _parts_for_component(component, payload, breakdown)
    if any("plexiglas_face" in part.counted_in_material_lines for part in parts):
        row = next((item for item in breakdown.material_rows if item.material_key == "plexiglas_face"), None)
        if row is not None:
            return row

    component_slugs = _component_layer_slugs(component, payload)
    for layer_slug in component_slugs:
        prefixed = f"artwork_{layer_slug}_print_vinyl"
        row = next((item for item in breakdown.material_rows if item.material_key == prefixed), None)
        if row is not None:
            return row

    for layer_slug in component_slugs:
        prefixed = f"artwork_{layer_slug}_plexiglas_face"
        row = next((item for item in breakdown.material_rows if item.material_key == prefixed), None)
        if row is not None:
            return row
    return None


def _find_operation_metadata(
    component: ComponentInstance,
    material_row: IntakeV4MaterialQuantityRow | None,
    parts: list[IntakeV4NestingPreviewPartRow],
    breakdown: IntakeV4MaterialBreakdownResponse | None,
) -> dict[str, Any]:
    if breakdown is None:
        return {}
    if component.component_type == "volumetric_letters" or (
        material_row is not None and material_row.material_key == "plexiglas_face"
    ) or any("plexiglas_face" in part.counted_in_material_lines for part in parts):
        row = next(
            (
                item for item in breakdown.operation_rows
                if item.material_key == "plexiglas_3mm" and item.operation_type == "cutting"
            ),
            None,
        )
        return {
            "machine_type": getattr(row, "machine_type", None),
            "workcenter": getattr(row, "workcenter_code", None),
            "estimated_time": getattr(row, "quantity", None),
            "estimated_time_unit": getattr(row, "unit", "ml"),
        }

    has_artwork_parts = any(part.part_kind == "artwork_part" for part in parts)
    if has_artwork_parts or (material_row and material_row.material_key.endswith("_print_vinyl")):
        row = next((item for item in breakdown.operation_rows if item.operation_type == "print_vinyl"), None)
        return {
            "machine_type": getattr(row, "machine_type", None),
            "workcenter": getattr(row, "workcenter_code", None) or PRINT_WORKCENTER,
            "estimated_time": getattr(row, "quantity", None),
            "estimated_time_unit": getattr(row, "unit", "m2"),
        }
    return {}


def _resolve_candidate_shape(
    component: ComponentInstance,
    payload: IntakeV4WorkspacePayload,
    breakdown: IntakeV4MaterialBreakdownResponse | None,
) -> dict[str, Any]:
    parts = _parts_for_component(component, payload, breakdown)
    material_row = _find_material_row(component, payload, breakdown)
    operation_meta = _find_operation_metadata(component, material_row, parts, breakdown)
    warnings: list[str] = []

    geometry_refs = [part.part_id for part in parts]
    geometry_source = "nesting_preview_parts"
    if not geometry_refs:
        geometry_refs = list(component.source_layer_keys)
        geometry_source = "layer_key_fallback"
        warnings.append("geometry_fallback_used")

    total_area = _sum_or_none([part.area_sqm for part in parts])
    total_perimeter = _sum_or_none([part.perimeter_ml for part in parts])
    if total_area is None and material_row is not None and material_row.unit in {"m2", "sqm"}:
        total_area = material_row.base_quantity or material_row.quantity or material_row.priced_quantity
    if total_area is None:
        warnings.append("total_area_missing")

    process_type = "cnc_sheet_cutting"
    operation_type = "logo_face_cut" if component.component_type == "volumetric_logo" else "face_cnc_cut"
    material_family: str | None = None
    material_code: str | None = None
    thickness_mm: float | None = None
    finish_code: str | None = None
    color_code: str | None = None
    machine_type = operation_meta.get("machine_type")
    workcenter = operation_meta.get("workcenter")
    setup_group_key: str | None = None
    quantity = OperationCandidateMeasure(unit="sqm", value=total_area)
    estimated_time = OperationCandidateMeasure(unit="min", value=None)
    consolidation_allowed = False
    separation_reason: str | None = None

    if material_row is not None:
        material_code = material_row.material_code or material_row.registry_code
        if material_row.material_key == "plexiglas_face":
            material_family = "plexiglass"
            thickness_mm = 3.0
            finish_code = DEFAULT_FINISH_CODE
            color_code = DEFAULT_COLOR_CODE
            process_type = "cnc_sheet_cutting"
            operation_type = "logo_face_cut" if component.component_type == "volumetric_logo" else "face_cnc_cut"
            machine_type = machine_type or DEFAULT_MACHINE_TYPE
            workcenter = workcenter or DEFAULT_WORKCENTER
            setup_group_key = f"{machine_type or DEFAULT_MACHINE_TYPE}|plexi|{thickness_mm}|{color_code}"
            consolidation_allowed = bool(material_code and thickness_mm and machine_type and workcenter)
            if not consolidation_allowed:
                separation_reason = "candidate_not_consolidated_missing_material"
        elif material_row.material_key.endswith("_print_vinyl"):
            material_family = "vinyl"
            finish_code = "print"
            color_code = _slug(component.source_layer_keys[0] if component.source_layer_keys else "artwork") or None
            process_type = "print_vinyl"
            operation_type = "logo_print_vinyl"
            machine_type = machine_type
            workcenter = workcenter or PRINT_WORKCENTER
            setup_group_key = None
            consolidation_allowed = False
            separation_reason = "candidate_not_consolidated_missing_material"
        else:
            warnings.append("material_default_used")
            separation_reason = "candidate_not_consolidated_missing_material"
    else:
        separation_reason = "candidate_not_consolidated_missing_material"

    if component.component_type == "volumetric_logo" and component.template_code != payload.product_binding.template_code:
        warnings.append("logo_template_not_product_system_live")

    if material_code is None:
        warnings.append("candidate_not_consolidated_missing_material")
    if geometry_source == "layer_key_fallback":
        warnings.append("geometry_fallback_used")

    quantity_unit = "sqm" if total_area is not None else (material_row.unit if material_row is not None else "count")
    quantity_value = total_area if total_area is not None else (
        (material_row.base_quantity or material_row.quantity) if material_row is not None else None
    )
    quantity = OperationCandidateMeasure(unit=quantity_unit, value=quantity_value)

    estimated_raw = operation_meta.get("estimated_time")
    estimated_unit = operation_meta.get("estimated_time_unit", "min")
    estimated_time = OperationCandidateMeasure(unit=estimated_unit, value=estimated_raw)

    return {
        "parts": parts,
        "material_row": material_row,
        "operation_type": operation_type,
        "process_type": process_type,
        "material_family": material_family,
        "material_code": material_code,
        "thickness_mm": thickness_mm,
        "finish_code": finish_code,
        "color_code": color_code,
        "machine_type": machine_type,
        "workcenter": workcenter,
        "setup_group_key": setup_group_key,
        "geometry_refs": geometry_refs,
        "geometry_source": geometry_source,
        "quantity": quantity,
        "total_area": total_area,
        "total_perimeter": total_perimeter,
        "estimated_time": estimated_time,
        "consolidation_allowed": consolidation_allowed,
        "separation_reason": separation_reason,
        "warnings": list(dict.fromkeys(warnings)),
    }


def _binding_role(binding: IntakeV4LayerBindingContract) -> str:
    return str(
        binding.confirmed_semantic_role
        or binding.suggested_semantic_role
        or binding.detected_kind
        or ""
    ).strip().lower()


def _is_logo_binding(binding: IntakeV4LayerBindingContract, primary_template_code: str) -> bool:
    role = _binding_role(binding)
    if role in LOGO_ROLES:
        return True
    return bool(binding.target_template_code and binding.target_template_code != primary_template_code)


def _component_binding_status(bindings: list[IntakeV4LayerBindingContract]) -> str:
    statuses = {binding.binding_status for binding in bindings}
    if not statuses:
        return "pending"
    if "suggested" in statuses:
        return "suggested"
    if statuses == {"confirmed"}:
        return "confirmed"
    if statuses == {"ignored"}:
        return "ignored"
    return "pending"


def _component_required_fields_status(component_type: str, binding_status: str, primary_template_code: str, template_code: str) -> str:
    if component_type == "volumetric_logo" and template_code != primary_template_code:
        return "partial"
    if binding_status == "confirmed":
        return "complete"
    if binding_status == "ignored":
        return "missing"
    return "partial"


def _component_operation_roles(component_type: str) -> list[str]:
    if component_type == "volumetric_logo":
        return ["logo_face_cut"]
    return ["face_cnc_cut"]


def _component_material_roles(component_type: str) -> list[str]:
    if component_type in {"volumetric_letters", "volumetric_logo"}:
        return ["plexiglass_face"]
    return []


def _synthetic_bindings_from_layers(payload: IntakeV4WorkspacePayload) -> list[IntakeV4LayerBindingContract]:
    layer_setup = payload.layer_role_setup
    if layer_setup is None:
        return []
    primary_template_code = payload.product_binding.template_code
    out: list[IntakeV4LayerBindingContract] = []
    for layer in layer_setup.layers:
        role = str(layer.confirmed_role or layer.auto_role or "").strip()
        target_template_code = primary_template_code
        binding_status = "pending"
        if role.lower() in LOGO_ROLES:
            target_template_code = LOGO_TEMPLATE_CODE
            binding_status = "suggested"
        elif layer.confirmation_state == "confirmed":
            binding_status = "confirmed"
        elif layer.confirmation_state == "ignored":
            binding_status = "ignored"
        out.append(
            IntakeV4LayerBindingContract(
                layer_key=layer.layer_key,
                source_layer_name=layer.layer_name,
                suggested_semantic_role=layer.auto_role,
                confirmed_semantic_role=layer.confirmed_role,
                target_template_code=target_template_code,
                binding_status=binding_status,  # type: ignore[arg-type]
            )
        )
    return out


def _classify_assembly_type(has_letters: bool, has_logo: bool) -> str:
    if has_letters and has_logo:
        return "letters_logo"
    if has_logo:
        return "logo_only"
    if has_letters:
        return "letters_only"
    return "mixed_custom"


def _derive_assembly_status(components: list[ComponentInstance]) -> str:
    if not components:
        return "draft"
    if any(component.required_fields_status == "missing" for component in components):
        return "needs_input"
    if any(component.required_fields_status == "partial" for component in components):
        return "needs_input"
    return "ready_for_task_preview"


def build_intake_v6_assembly_draft_preview(
    *,
    workspace_id: str,
    payload: IntakeV4WorkspacePayload,
) -> tuple[AssemblyDraft, list[str]]:
    primary_template_code = payload.product_binding.template_code
    layer_setup = payload.layer_role_setup
    bindings = list(layer_setup.layer_bindings) if layer_setup and layer_setup.layer_bindings else []
    if not bindings:
        bindings = _synthetic_bindings_from_layers(payload)

    active_bindings = [binding for binding in bindings if binding.binding_status != "ignored"]
    logo_bindings = [binding for binding in active_bindings if _is_logo_binding(binding, primary_template_code)]
    letters_bindings = [binding for binding in active_bindings if binding not in logo_bindings]
    warnings: list[str] = []
    components: list[ComponentInstance] = []
    change_log: list[AssemblyDraftChangeLogEntry] = []

    if letters_bindings:
        binding_status = _component_binding_status(letters_bindings)
        components.append(
            ComponentInstance(
                component_id=LETTERS_COMPONENT_ID,
                component_type="volumetric_letters",
                template_code=primary_template_code,
                source="svg_detected",
                source_layer_keys=[binding.layer_key for binding in letters_bindings],
                binding_status=binding_status,  # type: ignore[arg-type]
                required_fields_status=_component_required_fields_status(
                    "volumetric_letters",
                    binding_status,
                    primary_template_code,
                    primary_template_code,
                ),  # type: ignore[arg-type]
                material_roles=_component_material_roles("volumetric_letters"),
                operation_roles=_component_operation_roles("volumetric_letters"),
                depends_on_component_ids=[],
                enabled=True,
            )
        )
        change_log.append(
            AssemblyDraftChangeLogEntry(
                at="derived",
                source="assembly_preview_builder",
                event="component_added",
                component_id=LETTERS_COMPONENT_ID,
                details={"source_layer_count": len(letters_bindings)},
            )
        )

    if logo_bindings:
        logo_template_code = str(
            next(
                (
                    binding.target_template_code
                    for binding in logo_bindings
                    if binding.target_template_code and binding.target_template_code != primary_template_code
                ),
                primary_template_code,
            )
        )
        binding_status = _component_binding_status(logo_bindings)
        required_fields_status = _component_required_fields_status(
            "volumetric_logo",
            binding_status,
            primary_template_code,
            logo_template_code,
        )
        components.append(
            ComponentInstance(
                component_id=LOGO_COMPONENT_ID,
                component_type="volumetric_logo",
                template_code=logo_template_code,
                source="svg_detected",
                source_layer_keys=[binding.layer_key for binding in logo_bindings],
                binding_status=binding_status,  # type: ignore[arg-type]
                required_fields_status=required_fields_status,  # type: ignore[arg-type]
                material_roles=_component_material_roles("volumetric_logo"),
                operation_roles=_component_operation_roles("volumetric_logo"),
                depends_on_component_ids=[],
                enabled=True,
            )
        )
        warnings.append("component:cmp_volumetric_logo:runtime_target_not_product_template_live")
        change_log.append(
            AssemblyDraftChangeLogEntry(
                at="derived",
                source="assembly_preview_builder",
                event="component_added",
                component_id=LOGO_COMPONENT_ID,
                details={
                    "source_layer_count": len(logo_bindings),
                    "warning": "runtime_target_not_product_template_live",
                },
            )
        )

    assembly = AssemblyDraft(
        assembly_id=f"asm_{workspace_id}_v1",
        workspace_id=workspace_id,
        primary_family=PRIMARY_FAMILY,
        assembly_type=_classify_assembly_type(bool(letters_bindings), bool(logo_bindings)),  # type: ignore[arg-type]
        primary_template_code=primary_template_code,
        component_instances=components,
        version=1,
        change_log=change_log,
        status=_derive_assembly_status(components),  # type: ignore[arg-type]
    )
    return assembly, warnings


def compile_intake_v6_operation_candidates_preview(
    assembly: AssemblyDraft,
    payload: IntakeV4WorkspacePayload,
    breakdown: IntakeV4MaterialBreakdownResponse | None = None,
) -> tuple[list[OperationCandidate], list[str]]:
    candidates: list[OperationCandidate] = []
    warnings: list[str] = []

    for component in assembly.component_instances:
        if not component.enabled:
            continue
        source_layer_key = component.source_layer_keys[0] if component.source_layer_keys else None
        resolved = _resolve_candidate_shape(component, payload, breakdown)

        if not component.source_layer_keys:
            candidate = OperationCandidate(
                candidate_id=f"opc_{component.component_id}_missing_material",
                assembly_id=assembly.assembly_id,
                component_id=component.component_id,
                source_template_code=component.template_code,
                source_layer_key=source_layer_key,
                operation_type="logo_face_cut" if component.component_type == "volumetric_logo" else "face_cnc_cut",
                process_type="cnc_sheet_cutting",
                material_family=None,
                material_code=None,
                thickness_mm=None,
                finish_code=None,
                color_code=None,
                machine_type=None,
                workcenter=None,
                setup_group_key=None,
                dependency_group=DEFAULT_DEPENDENCY_GROUP,
                geometry_refs=[],
                geometry_source="layer_key_fallback",
                quantity=OperationCandidateMeasure(unit="sqm", value=None),
                total_area=None,
                total_perimeter=None,
                estimated_time=OperationCandidateMeasure(unit="min", value=None),
                consolidation_allowed=False,
                separation_reason="missing_source_layers_for_face_candidate",
                provenance={
                    "component_type": component.component_type,
                    "preview_only": True,
                },
                warnings=["geometry_fallback_used", "candidate_not_consolidated_missing_material", "total_area_missing"],
            )
            candidates.append(candidate)
            warnings.append(f"candidate:{candidate.candidate_id}:missing_source_layers_for_face_candidate")
            continue

        candidate = OperationCandidate(
            candidate_id=f"opc_{component.component_id}_face",
            assembly_id=assembly.assembly_id,
            component_id=component.component_id,
            source_template_code=component.template_code,
            source_layer_key=source_layer_key,
            operation_type=resolved["operation_type"],
            process_type=resolved["process_type"],
            material_family=resolved["material_family"],
            material_code=resolved["material_code"],
            thickness_mm=resolved["thickness_mm"],
            finish_code=resolved["finish_code"],
            color_code=resolved["color_code"],
            machine_type=resolved["machine_type"],
            workcenter=resolved["workcenter"],
            setup_group_key=resolved["setup_group_key"],
            dependency_group=DEFAULT_DEPENDENCY_GROUP,
            geometry_refs=resolved["geometry_refs"],
            geometry_source=resolved["geometry_source"],
            quantity=resolved["quantity"],
            total_area=resolved["total_area"],
            total_perimeter=resolved["total_perimeter"],
            estimated_time=resolved["estimated_time"],
            consolidation_allowed=resolved["consolidation_allowed"],
            separation_reason=resolved["separation_reason"],
            provenance={
                "component_type": component.component_type,
                "preview_only": True,
                "binding_status": component.binding_status,
                "geometry_source": resolved["geometry_source"],
                "material_source": (
                    f"material_breakdown:{resolved['material_row'].material_key}"
                    if resolved["material_row"] is not None
                    else "missing"
                ),
            },
            warnings=resolved["warnings"],
        )
        if component.component_type == "volumetric_logo" and component.template_code != assembly.primary_template_code:
            candidate.provenance["warning"] = "runtime_target_not_product_template_live"
        warnings.extend(f"candidate:{candidate.candidate_id}:{warning}" for warning in candidate.warnings)
        candidates.append(candidate)

    return candidates, list(dict.fromkeys(warnings))


def build_nesting_group_key(candidate: OperationCandidate) -> str | None:
    required = [
        candidate.assembly_id,
        candidate.process_type,
        candidate.material_code,
        candidate.thickness_mm,
        candidate.finish_code,
        candidate.color_code,
        candidate.machine_type,
        candidate.workcenter,
        candidate.setup_group_key,
    ]
    if any(value is None or value == "" for value in required):
        return None
    return "|".join(
        [
            candidate.assembly_id,
            candidate.process_type,
            str(candidate.material_code),
            str(candidate.thickness_mm),
            str(candidate.finish_code),
            str(candidate.color_code),
            str(candidate.machine_type),
            str(candidate.workcenter),
            str(candidate.setup_group_key),
        ]
    )


def compile_intake_v6_consolidated_tasks_preview(
    candidates: list[OperationCandidate],
) -> tuple[list[ConsolidatedTask], list[str]]:
    grouped: dict[tuple[Any, ...], list[OperationCandidate]] = defaultdict(list)
    tasks: list[ConsolidatedTask] = []
    warnings: list[str] = []

    for candidate in candidates:
        if not candidate.consolidation_allowed:
            warnings.append(
                f"candidate:{candidate.candidate_id}:{candidate.separation_reason or 'consolidation_not_allowed'}"
            )
            tasks.append(
                ConsolidatedTask(
                    task_id=f"ctk_{candidate.candidate_id}",
                    assembly_id=candidate.assembly_id,
                    task_type=candidate.operation_type,
                    process_type=candidate.process_type,
                    material_code=candidate.material_code,
                    thickness_mm=candidate.thickness_mm,
                    finish_code=candidate.finish_code,
                    color_code=candidate.color_code,
                    machine_type=candidate.machine_type,
                    workcenter=candidate.workcenter,
                    nesting_group_key=build_nesting_group_key(candidate),
                    consolidated_from_candidates=[candidate.candidate_id],
                    consolidated_from_components=[candidate.component_id],
                    geometry_refs=list(candidate.geometry_refs),
                    total_quantity=candidate.quantity,
                    total_area=candidate.total_area,
                    total_perimeter=candidate.total_perimeter,
                    sheet_plan_id=None,
                    dependencies=[],
                    qc_rules=[],
                    separation_notes=[candidate.separation_reason or "consolidation_not_allowed"],
                )
            )
            continue

        key = (
            candidate.assembly_id,
            candidate.process_type,
            candidate.material_code,
            candidate.thickness_mm,
            candidate.finish_code,
            candidate.color_code,
            candidate.machine_type,
            candidate.workcenter,
            candidate.setup_group_key,
        )
        grouped[key].append(candidate)

    for key, group in grouped.items():
        first = group[0]
        tasks.append(
            ConsolidatedTask(
                task_id=f"ctk_{first.assembly_id}_{len(tasks) + 1}",
                assembly_id=first.assembly_id,
                task_type=first.process_type,
                process_type=first.process_type,
                material_code=first.material_code,
                thickness_mm=first.thickness_mm,
                finish_code=first.finish_code,
                color_code=first.color_code,
                machine_type=first.machine_type,
                workcenter=first.workcenter,
                nesting_group_key=build_nesting_group_key(first),
                consolidated_from_candidates=[candidate.candidate_id for candidate in group],
                consolidated_from_components=sorted({candidate.component_id for candidate in group}),
                geometry_refs=[ref for candidate in group for ref in candidate.geometry_refs],
                total_quantity=OperationCandidateMeasure(
                    unit=first.quantity.unit,
                    value=round(
                        sum(candidate.quantity.value or 0.0 for candidate in group if candidate.quantity.unit == first.quantity.unit),
                        6,
                    ),
                ),
                total_area=_sum_or_none([candidate.total_area for candidate in group]),
                total_perimeter=_sum_or_none([candidate.total_perimeter for candidate in group]),
                sheet_plan_id=None,
                dependencies=sorted({candidate.dependency_group for candidate in group if candidate.dependency_group}),
                qc_rules=["verify_material_code", "verify_sheet_thickness", "verify_cut_alignment"],
                separation_notes=[],
            )
        )

    for task in tasks:
        if task.total_area is None:
            warnings.append(f"task:{task.task_id}:total_area_missing")

    return tasks, list(dict.fromkeys(warnings))


def build_intake_v6_assembly_preview_bundle(
    *,
    workspace_id: str,
    payload: IntakeV4WorkspacePayload,
    breakdown: IntakeV4MaterialBreakdownResponse | None = None,
) -> tuple[AssemblyDraft, list[OperationCandidate], list[ConsolidatedTask], list[str]]:
    assembly, assembly_warnings = build_intake_v6_assembly_draft_preview(
        workspace_id=workspace_id,
        payload=payload,
    )
    candidates, candidate_warnings = compile_intake_v6_operation_candidates_preview(assembly, payload, breakdown)
    tasks, task_warnings = compile_intake_v6_consolidated_tasks_preview(candidates)
    return assembly, candidates, tasks, [*assembly_warnings, *candidate_warnings, *task_warnings]


async def build_intake_v6_assembly_preview_bundle_from_payload_raw(
    *,
    db: Any,
    workspace_id: str,
    payload: IntakeV4WorkspacePayload,
    payload_raw: dict[str, Any],
) -> tuple[AssemblyDraft, list[OperationCandidate], list[ConsolidatedTask], list[str]]:
    breakdown: IntakeV4MaterialBreakdownResponse | None = None
    warnings: list[str] = []
    try:
        breakdown = await build_intake_v4_material_breakdown_with_registry(db, workspace_id, payload_raw)
    except Exception:
        warnings.append("material_breakdown_unavailable")
    assembly, candidates, tasks, bundle_warnings = build_intake_v6_assembly_preview_bundle(
        workspace_id=workspace_id,
        payload=payload,
        breakdown=breakdown,
    )
    return assembly, candidates, tasks, [*bundle_warnings, *warnings]