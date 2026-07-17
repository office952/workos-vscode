"""Shared Quote Snapshot component-scope freeze helper.

Single entry point for both QuoteSnapshotV2Service and Intake V6 official snapshot paths.
Does not reprice — only freezes workspace aggregate, offer_scope, and component identity.
"""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.offer_scope_canonical_map import runtime_to_canonical
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.offer_scope import OFFER_SCOPE_CONTRACT_VERSION
from schemas.product_aggregate import ProductAggregate
from schemas.quote_snapshot_v2 import (
    COMPONENT_SCOPE_VERSION,
    ComponentScopeClassification,
    FrozenComponentScope,
    QuoteSnapshotComponentInstance,
    QuoteSnapshotGeometryInput,
    QuoteSnapshotOfferScope,
)
from services.offer_scope_resolver_service import (
    extract_offer_scope,
    merge_scope_payload,
    resolve_offer_scope,
)
from services.product_aggregate_planning_duration_service import (
    apply_planning_duration_resolution,
    collect_planning_duration_facts,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_aggregate_workspace_composition_service import SEGMENT_NAMESPACE_SEP
from services.product_definition_builder_service import ProductDefinitionBuilderService

SCOPE_WARNING_UNMAPPED_COMPONENT = "COMPONENT_INSTANCE_CANONICAL_UNMAPPED"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _parse_segment_key(instance_id: str) -> str | None:
    if SEGMENT_NAMESPACE_SEP not in instance_id:
        return None
    return instance_id.split(SEGMENT_NAMESPACE_SEP, 1)[1] or None


def _is_linked_neutral(instance_id: str) -> bool:
    return SEGMENT_NAMESPACE_SEP in instance_id


def _build_offer_scope_snapshot(scope_input: Any, resolved: Any, payload_raw: dict[str, Any] | None = None) -> QuoteSnapshotOfferScope:
    sold_modules: list[str] = []
    if scope_input is not None:
        sold_modules = list(scope_input.sold_modules)

    runtime_sorted = sorted(resolved.runtime_sold_modules) if resolved.runtime_sold_modules else []

    dependency_confirmations: list[str] = []
    if isinstance(payload_raw, dict):
        from services.sold_scope_dependency_validator_service import _read_dependency_confirmations

        dependency_confirmations = sorted(_read_dependency_confirmations(payload_raw))

    return QuoteSnapshotOfferScope(
        contract_version=OFFER_SCOPE_CONTRACT_VERSION,
        mode=resolved.mode,
        sold_modules=sold_modules,
        resolved_runtime_sold_modules=runtime_sorted,
        use_legacy=resolved.use_legacy,
        resolver_contract_version=OFFER_SCOPE_CONTRACT_VERSION,
        validation_errors=list(resolved.validation_errors),
        dependency_confirmations=dependency_confirmations,
    )


def _classify_component(
    *,
    instance_id: str,
    runtime_module: str | None,
    offer_scope: QuoteSnapshotOfferScope,
    resolved_runtime: set[str],
) -> ComponentScopeClassification:
    if _is_linked_neutral(instance_id):
        return "linked_neutral"

    if offer_scope.use_legacy:
        return "sold"

    if runtime_module and runtime_module in resolved_runtime:
        return "sold"

    if runtime_module:
        return "calc_only"

    return "unspecified"


def _derive_component_instances(
    aggregate: ProductAggregate,
    offer_scope: QuoteSnapshotOfferScope,
) -> tuple[list[QuoteSnapshotComponentInstance], list[str]]:
    resolved_runtime = set(offer_scope.resolved_runtime_sold_modules)
    instances: list[QuoteSnapshotComponentInstance] = []
    warnings: list[str] = []

    for component in aggregate.components:
        instance_id = _text(component.component_id)
        if not instance_id:
            continue

        runtime_module = _text(component.mini_module_code) or None
        canonical = runtime_to_canonical(runtime_module) if runtime_module else None
        classification = _classify_component(
            instance_id=instance_id,
            runtime_module=runtime_module,
            offer_scope=offer_scope,
            resolved_runtime=resolved_runtime,
        )

        if classification == "unspecified" and runtime_module and not _is_linked_neutral(instance_id):
            warnings.append(f"{SCOPE_WARNING_UNMAPPED_COMPONENT}:{instance_id}")

        source_template = _text(component.source_template_code) or aggregate.template_code
        instances.append(
            QuoteSnapshotComponentInstance(
                instance_id=instance_id,
                canonical_component_code=canonical,
                runtime_module_code=runtime_module,
                source_template_code=source_template,
                segment_key=_parse_segment_key(instance_id),
                classification=classification,
            )
        )

    return instances, warnings


def _build_geometry_snapshot(
    merged_payload: dict[str, Any],
    *,
    raw_payload_json: str | None = None,
) -> QuoteSnapshotGeometryInput:
    quote_geometry = _as_dict(merged_payload.get("quote_geometry"))
    svg_source = _as_dict(merged_payload.get("svg_source"))
    analysis_ready = merged_payload.get("analysis_ready")
    parsed_ready = analysis_ready if isinstance(analysis_ready, bool) else None

    payload_hash: str | None = None
    if raw_payload_json:
        payload_hash = hashlib.sha256(raw_payload_json.encode()).hexdigest()[:32]

    return QuoteSnapshotGeometryInput(
        quote_geometry=quote_geometry,
        svg_source=svg_source,
        analysis_ready=parsed_ready,
        workspace_payload_hash=payload_hash,
    )


async def build_frozen_component_scope(
    db: AsyncSession,
    *,
    template_code: str,
    workspace_id: str | None = None,
    quote_input: dict[str, Any] | None = None,
) -> FrozenComponentScope | None:
    """Build frozen component scope — no repricing."""
    pd_builder = ProductDefinitionBuilderService(db)
    aggregate_svc = ProductAggregateService(db)

    workspace_payload: dict[str, Any] = {}
    raw_payload_json: str | None = None

    if workspace_id:
        ws_payload, ws_error = await pd_builder._load_workspace_payload(workspace_id, template_code)
        if ws_error == "workspace_not_found":
            return None
        if ws_error != "workspace_template_mismatch":
            workspace_payload = ws_payload or {}

        record_result = await db.execute(
            select(IntakeV6WorkspaceRecord.payload_json).where(
                IntakeV6WorkspaceRecord.id == workspace_id
            ).limit(1)
        )
        raw_payload_json = record_result.scalar_one_or_none()

    merged_payload = merge_scope_payload(workspace_payload, quote_input)

    scope_input = extract_offer_scope(workspace_payload, quote_input)
    resolved = resolve_offer_scope(scope_input)
    offer_scope_snapshot = _build_offer_scope_snapshot(scope_input, resolved, workspace_payload)

    from services.sold_scope_dependency_validator_service import validate_sold_graph_from_payload

    dependency = validate_sold_graph_from_payload(workspace_payload)
    if not dependency.valid_for_confirmation:
        extra_errors = [issue.code for issue in dependency.blockers]
        extra_errors.extend(issue.code for issue in dependency.confirmations_required)
        if extra_errors:
            offer_scope_snapshot = offer_scope_snapshot.model_copy(
                update={
                    "validation_errors": list(offer_scope_snapshot.validation_errors or []) + extra_errors,
                }
            )

    if workspace_id:
        aggregate = await aggregate_svc.build_for_workspace(template_code, workspace_id)
    else:
        aggregate = await aggregate_svc.build(template_code)

    if aggregate is None:
        return None

    # TE2E-028B: resolve formula duration from freeze-time product facts.
    # Workspace composition may already have resolved from ProductDefinition;
    # re-apply only when freeze payload supplies duration inputs (or no workspace).
    duration_facts = collect_planning_duration_facts(merged_payload)
    duration_input_keys = {"letter_count", "letter_perimeter_m", "cnc_cutting_perimeter_ml"}
    if not workspace_id:
        aggregate = apply_planning_duration_resolution(aggregate, duration_facts)
    elif duration_input_keys.intersection(duration_facts.keys()):
        aggregate = apply_planning_duration_resolution(aggregate, duration_facts)

    component_instances, scope_warnings = _derive_component_instances(aggregate, offer_scope_snapshot)
    geometry_input_snapshot = _build_geometry_snapshot(
        merged_payload,
        raw_payload_json=raw_payload_json if workspace_id else None,
    )

    return FrozenComponentScope(
        product_aggregate=aggregate,
        offer_scope_snapshot=offer_scope_snapshot,
        component_instances=component_instances,
        geometry_input_snapshot=geometry_input_snapshot,
        scope_warnings=scope_warnings,
    )


def apply_component_scope_to_snapshot_fields(
    scope: FrozenComponentScope,
) -> dict[str, Any]:
    """Map FrozenComponentScope onto QuoteSnapshotV2 optional field values."""
    return {
        "component_scope_version": COMPONENT_SCOPE_VERSION,
        "offer_scope_snapshot": scope.offer_scope_snapshot,
        "component_instances": scope.component_instances,
        "geometry_input_snapshot": scope.geometry_input_snapshot,
        "product_aggregate_snapshot": scope.product_aggregate,
    }
