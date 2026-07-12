"""Workspace-aware ProductAggregate composition via ProductDefinition preview."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateComponent,
    ProductAggregateConflict,
    ProductAggregateMaterial,
    ProductAggregateOperation,
    ProductAggregateProvenanceSummary,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_definition import ProductDefinitionPreview
from services.logo_artwork_cost_ownership import (
    include_material_in_composed_aggregate,
    include_operation_in_composed_aggregate,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService

SEGMENT_NAMESPACE_SEP = "::"
LINKED_SEGMENT_COMPONENT_REF_PREFIX = "linked_segment"
WARNING_FINISH_PARTIAL = "LINKED_SEGMENT_FINISH_PARTIAL"
WARNING_COMPOSITION_APPLIED = "WORKSPACE_LINKED_LOGO_COMPOSITION_APPLIED"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _namespace_component(component_id: str, segment_key: str) -> str:
    if SEGMENT_NAMESPACE_SEP in component_id:
        return component_id
    return f"{component_id}{SEGMENT_NAMESPACE_SEP}{segment_key}"


def _segment_component_ref(segment_key: str) -> str:
    return f"{LINKED_SEGMENT_COMPONENT_REF_PREFIX}{SEGMENT_NAMESPACE_SEP}{segment_key}"


def _confirmed_linked_segments(pd: ProductDefinitionPreview) -> list[dict[str, Any]]:
    linked = _as_dict(pd.linked_template_runtime_segments)
    segments = [
        _as_dict(segment)
        for segment in _as_list(linked.get("segments"))
        if isinstance(segment, dict) and _text(segment.get("binding_status")) == "confirmed"
    ]
    return sorted(segments, key=lambda segment: _text(segment.get("segment_key")))


def _segment_finish_confirmed(segment: dict[str, Any]) -> bool:
    finish = _as_dict(segment.get("finish"))
    return finish.get("confirmed") is True


def _dedupe_materials(items: list[ProductAggregateMaterial]) -> list[ProductAggregateMaterial]:
    seen: set[str] = set()
    out: list[ProductAggregateMaterial] = []
    for item in items:
        key = "|".join(
            [
                item.material_code,
                _text(item.source_template_code),
                _text(item.component_ref),
                item.provenance,
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _dedupe_operations(items: list[ProductAggregateOperation]) -> list[ProductAggregateOperation]:
    seen: set[str] = set()
    out: list[ProductAggregateOperation] = []
    for item in items:
        key = "|".join(
            [
                item.operation_code,
                _text(item.source_template_code),
                _text(item.component_ref),
                item.provenance,
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _dedupe_task_rules(items: list[ProductAggregateTaskRule]) -> list[ProductAggregateTaskRule]:
    seen: set[str] = set()
    out: list[ProductAggregateTaskRule] = []
    for item in items:
        key = "|".join(
            [
                item.task_name,
                _text(item.priced_operation),
                _text(item.trigger_condition),
                item.provenance,
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _expand_logo_components(
    logo_aggregate: ProductAggregate,
    *,
    segment_key: str,
    include_materials_operations: bool,
) -> list[ProductAggregateComponent]:
    status = "present" if include_materials_operations else "partial"
    provenance = "linked_module" if include_materials_operations else "derived"
    expanded: list[ProductAggregateComponent] = []
    for component in logo_aggregate.components:
        expanded.append(
            component.model_copy(
                update={
                    "component_id": _namespace_component(component.component_id, segment_key),
                    "source_template_code": logo_aggregate.template_code,
                    "provenance": provenance,
                    "status": status,
                    "materials": [],
                    "operations": [],
                }
            )
        )
    return expanded


def _namespace_material(
    material: ProductAggregateMaterial,
    *,
    segment_key: str,
    source_template_code: str,
) -> ProductAggregateMaterial:
    component_ref = _text(material.component_ref) or _segment_component_ref(segment_key)
    if SEGMENT_NAMESPACE_SEP not in component_ref and not component_ref.startswith(LINKED_SEGMENT_COMPONENT_REF_PREFIX):
        component_ref = _namespace_component(component_ref, segment_key)
    return material.model_copy(
        update={
            "component_ref": component_ref,
            "source_template_code": source_template_code,
            "provenance": "linked_module",
            "status": "present",
        }
    )


def _namespace_operation(
    operation: ProductAggregateOperation,
    *,
    segment_key: str,
    source_template_code: str,
) -> ProductAggregateOperation:
    component_ref = _text(operation.component_ref) or _segment_component_ref(segment_key)
    if SEGMENT_NAMESPACE_SEP not in component_ref and not component_ref.startswith(LINKED_SEGMENT_COMPONENT_REF_PREFIX):
        component_ref = _namespace_component(component_ref, segment_key)
    return operation.model_copy(
        update={
            "component_ref": component_ref,
            "source_template_code": source_template_code,
            "provenance": "linked_module",
            "status": "present",
        }
    )


def _expand_logo_task_rules(
    logo_aggregate: ProductAggregate,
    *,
    segment_key: str,
) -> list[ProductAggregateTaskRule]:
    expanded: list[ProductAggregateTaskRule] = []
    for rule in logo_aggregate.task_contract.task_rules:
        expanded.append(
            rule.model_copy(
                update={
                    "trigger_condition": f"linked_segment:{segment_key}",
                    "provenance": "linked_module",
                }
            )
        )
    return expanded


def _expand_logo_segment_aggregate(
    logo_aggregate: ProductAggregate,
    *,
    segment_key: str,
    include_materials_operations: bool,
) -> tuple[list[ProductAggregateComponent], list[ProductAggregateMaterial], list[ProductAggregateOperation], list[ProductAggregateTaskRule]]:
    components = _expand_logo_components(
        logo_aggregate,
        segment_key=segment_key,
        include_materials_operations=include_materials_operations,
    )
    if not include_materials_operations:
        return components, [], [], []

    materials = [
        _namespace_material(material, segment_key=segment_key, source_template_code=logo_aggregate.template_code)
        for material in logo_aggregate.materials
    ]
    operations = [
        _namespace_operation(operation, segment_key=segment_key, source_template_code=logo_aggregate.template_code)
        for operation in logo_aggregate.operations
    ]
    task_rules = _expand_logo_task_rules(logo_aggregate, segment_key=segment_key)
    return components, materials, operations, task_rules


def compose_from_product_definition(
    *,
    pd: ProductDefinitionPreview,
    letters_aggregate: ProductAggregate,
    logo_aggregates_by_segment: dict[str, ProductAggregate],
    workspace_id: str | None = None,
) -> ProductAggregate:
    """Merge letters template aggregate with per-segment linked logo template expansions."""
    segments = _confirmed_linked_segments(pd)
    if not segments:
        return letters_aggregate

    components = list(letters_aggregate.components)
    materials = list(letters_aggregate.materials)
    operations = list(letters_aggregate.operations)
    task_rules = list(letters_aggregate.task_contract.task_rules)
    warnings = list(letters_aggregate.warnings)

    linked_segment_count = 0
    for segment in segments:
        segment_key = _text(segment.get("segment_key"))
        template_code = _text(segment.get("owning_template_code"))
        if not segment_key or not template_code:
            continue
        logo_aggregate = logo_aggregates_by_segment.get(segment_key)
        if logo_aggregate is None:
            continue

        include_materials_operations = _segment_finish_confirmed(segment)
        expanded_components, expanded_materials, expanded_operations, expanded_task_rules = _expand_logo_segment_aggregate(
            logo_aggregate,
            segment_key=segment_key,
            include_materials_operations=include_materials_operations,
        )
        components.extend(expanded_components)
        materials.extend(expanded_materials)
        operations.extend(expanded_operations)
        task_rules.extend(expanded_task_rules)
        linked_segment_count += 1

        if not include_materials_operations:
            warnings.append(
                ProductAggregateConflict(
                    code=WARNING_FINISH_PARTIAL,
                    severity="warning",
                    message=(
                        f"Linked logo segment '{segment_key}' is composed with structure only; "
                        "finish is missing or not confirmed — logo materials and operations omitted."
                    ),
                    field=segment_key,
                    details={
                        "segment_key": segment_key,
                        "owning_template_code": template_code,
                        "workspace_id": workspace_id,
                    },
                )
            )

    if linked_segment_count:
        warnings.append(
            ProductAggregateConflict(
                code=WARNING_COMPOSITION_APPLIED,
                severity="info",
                message=(
                    f"Workspace-linked logo composition applied for {linked_segment_count} confirmed segment(s) "
                    "via ProductDefinition preview."
                ),
                details={
                    "workspace_id": workspace_id,
                    "segment_keys": [_text(segment.get("segment_key")) for segment in segments],
                    "compiler": "product_definition_preview",
                },
            )
        )

    materials = _dedupe_materials(materials)
    operations = _dedupe_operations(operations)
    materials = [
        mat
        for mat in materials
        if include_material_in_composed_aggregate(
            material_code=mat.material_code,
            component_ref=mat.component_ref,
            provenance=mat.provenance,
            status=mat.status,
            source_template_code=mat.source_template_code,
        )
    ]
    operations = [
        op
        for op in operations
        if include_operation_in_composed_aggregate(
            operation_code=op.operation_code,
            component_ref=op.component_ref,
            provenance=op.provenance,
            status=op.status,
            source_template_code=op.source_template_code,
        )
    ]
    task_rules = _dedupe_task_rules(task_rules)

    provenance_summary = ProductAggregateProvenanceSummary(
        parent=dict(letters_aggregate.provenance_summary.parent),
        dossier=dict(letters_aggregate.provenance_summary.dossier),
        linked_modules=dict(letters_aggregate.provenance_summary.linked_modules),
        aggregate_totals={
            "components": len(components),
            "materials": len(materials),
            "operations": len(operations),
            "linked_logo_segments": linked_segment_count,
        },
    )

    return letters_aggregate.model_copy(
        update={
            "components": components,
            "materials": materials,
            "operations": operations,
            "task_contract": ProductAggregateTaskContract(
                task_rules=task_rules,
                notes=[
                    *letters_aggregate.task_contract.notes,
                    "Workspace-linked logo segments composed from ProductDefinition preview (read-only).",
                ],
            ),
            "warnings": warnings,
            "provenance_summary": provenance_summary,
        }
    )


async def build_workspace_composed_aggregate(
    db: AsyncSession,
    *,
    template_code: str,
    workspace_id: str,
) -> ProductAggregate | None:
    """Build workspace-aware aggregate: ProductDefinition compiler + letters/logo merge."""
    pd_builder = ProductDefinitionBuilderService(db)
    pd = await pd_builder.build_preview(template_code, workspace_id=workspace_id)
    if pd is None:
        return None

    aggregate_svc = ProductAggregateService(db)
    letters_aggregate = await aggregate_svc.build(template_code)
    if letters_aggregate is None:
        return None

    segments = _confirmed_linked_segments(pd)
    if not segments:
        return letters_aggregate

    logo_aggregates_by_segment: dict[str, ProductAggregate] = {}
    for segment in segments:
        segment_key = _text(segment.get("segment_key"))
        owning_template_code = _text(segment.get("owning_template_code"))
        if not segment_key or not owning_template_code:
            continue
        if segment_key in logo_aggregates_by_segment:
            continue
        logo_aggregate = await aggregate_svc.build(owning_template_code)
        if logo_aggregate is not None:
            logo_aggregates_by_segment[segment_key] = logo_aggregate

    return compose_from_product_definition(
        pd=pd,
        letters_aggregate=letters_aggregate,
        logo_aggregates_by_segment=logo_aggregates_by_segment,
        workspace_id=workspace_id,
    )
