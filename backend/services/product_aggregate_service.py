"""Read-only ProductAggregate builder — merges parent, dossier, and linked modules."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from schemas.product_aggregate import (
    AGGREGATE_VERSION,
    ProductAggregate,
    ProductAggregateComponent,
    ProductAggregateConflict,
    ProductAggregateCostContract,
    ProductAggregateFormContract,
    ProductAggregateFormField,
    ProductAggregateMaterial,
    ProductAggregateMiniModuleRegistrySummary,
    ProductAggregateModule,
    ProductAggregateModules,
    ProductAggregateOperation,
    ProductAggregateProvenanceSummary,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from services.canonical_template_contract_service import (
    get_canonical_template_contract_service,
)
from services.mini_module_registry_service import get_mini_module_registry_service
from services.template_architecture_scope import normalize_template_code, resolve_template_identity

logger = logging.getLogger(__name__)

TEMPLATE_NOT_FOUND = "template_not_found"

# Dossier component_id → mini-module code (volumetric letters v2)
# pricing stub + canonical BOM id both map to modelare_cant (explicit alias; no double count)
DOSSIER_COMPONENT_MINI_MODULE: dict[str, str] = {
    "comp_face_litere": "debitare_fata",
    "comp_lateral_litere": "modelare_cant",
    "comp_volum_aluminiu_module": "modelare_cant",
    "comp_spate_litere": "debitare_spate",
    "comp_led_litere": "sistem_led",
    "comp_finisaj_litere": "finisaje",
}

# Child template → mini-module code
CHILD_TEMPLATE_MINI_MODULE: dict[str, str] = {
    "TPL-VOLUMETRIC-FACE_v1": "debitare_fata",
    "TPL-VOLUMETRIC-BACK_v1": "debitare_spate",
    "TPL-VOLUM-ALUMINIU_v1": "modelare_cant",
    "TPL-VOLUMETRIC-LED_v1": "sistem_led",
    "TPL-VOLUMETRIC-FINISH_v1": "finisaje",
    "TPL-METAL-PREMOUNT-STRUCTURE_v1": "structura_suport",
    "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1": "structura_suport",
}

# Known trigger field mismatches (documented OPEN QUESTION in contract)
TRIGGER_FIELD_MISMATCHES: dict[str, str] = {
    "metal_support_required": "mounting_system",
}


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _material_code(row: dict[str, Any]) -> str | None:
    code = row.get("material_code") or row.get("materialCode")
    return str(code) if code else None


def _operation_code(row: dict[str, Any]) -> str | None:
    code = row.get("code") or row.get("operation_id") or row.get("operation_code")
    return str(code) if code else None


def _optional_float(raw: Any) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _dedupe_materials(items: list[ProductAggregateMaterial]) -> list[ProductAggregateMaterial]:
    seen: set[str] = set()
    out: list[ProductAggregateMaterial] = []
    for item in items:
        component_ref = str(item.component_ref or "").strip()
        key = f"{item.material_code}|{item.source_template_code}|{component_ref}|{item.provenance}"
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _dedupe_operations(items: list[ProductAggregateOperation]) -> list[ProductAggregateOperation]:
    seen: set[str] = set()
    out: list[ProductAggregateOperation] = []
    for item in items:
        component_ref = str(item.component_ref or "").strip()
        key = f"{item.operation_code}|{item.source_template_code}|{component_ref}|{item.provenance}"
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


class ProductAggregateService:
    """Build a read-only ProductAggregate for a template_code."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def build(
        self,
        template_code: str,
        *,
        process_bridge_payload: dict[str, Any] | None = None,
    ) -> ProductAggregate | None:
        """Compile ProductAggregate. Volumetric v2 overlays modular process resolver (task_contract)."""
        identity = resolve_template_identity(template_code)
        template = await self._load_template(template_code)
        if template is None:
            return None

        dossier = await self._load_dossier(template.id)
        canonical = get_canonical_template_contract_service()
        links = await self._load_module_links(template.id)
        child_templates = await self._load_child_templates(links)

        parent_components = _json_loads(template.components_json, [])
        parent_operations = _json_loads(template.operations_json, [])
        parent_materials = _json_loads(template.required_materials_json, [])

        conflicts: list[ProductAggregateConflict] = []
        warnings: list[ProductAggregateConflict] = []

        components = self._build_template_components(
            parent_components,
            template.template_code,
        )
        parent_direct_count = len(parent_components) if isinstance(parent_components, list) else 0

        if parent_direct_count == 0:
            warnings.append(
                ProductAggregateConflict(
                    code="PARENT_COMPONENTS_EMPTY",
                    severity="warning",
                    message=(
                        "Parent template has no direct components (components_json=[]); "
                        "aggregate uses linked modules only — dossier is not a behavior source."
                    ),
                    details={"parent_components_count": 0},
                )
            )

        modules = self._build_modules(links, child_templates, warnings)

        materials: list[ProductAggregateMaterial] = []
        operations: list[ProductAggregateOperation] = []

        materials.extend(
            self._materials_from_rows(
                parent_materials,
                provenance="parent",
                source_template_code=template.template_code,
            )
        )
        operations.extend(
            self._operations_from_rows(
                parent_operations,
                provenance="parent",
                source_template_code=template.template_code,
            )
        )

        for child_code, child_row in child_templates.items():
            mini = CHILD_TEMPLATE_MINI_MODULE.get(child_code)
            child_mats = _json_loads(child_row.required_materials_json, [])
            child_ops = _json_loads(child_row.operations_json, [])
            materials.extend(
                self._materials_from_rows(
                    child_mats,
                    provenance="linked_module",
                    source_template_code=child_code,
                    mini_module_code=mini,
                )
            )
            operations.extend(
                self._operations_from_rows(
                    child_ops,
                    provenance="linked_module",
                    source_template_code=child_code,
                    mini_module_code=mini,
                )
            )

        materials = _dedupe_materials(materials)
        operations = _dedupe_operations(operations)

        if canonical.has_canonical_contract(template.template_code):
            required_keys, optional_keys = canonical.get_form_contract_keys(template.template_code)
            form_contract = self._build_form_contract_from_canonical(required_keys, optional_keys)
        else:
            form_contract = self._build_form_contract({})
        cost_contract = self._build_cost_contract({}, materials, operations)
        dossier_task_rules = self._extract_dossier_task_rules(dossier)
        task_contract = self._build_task_contract(dossier_task_rules)

        business_name = template.family_name

        provenance_summary = ProductAggregateProvenanceSummary(
            parent={
                "components": parent_direct_count,
                "operations": len(parent_operations) if isinstance(parent_operations, list) else 0,
                "materials": len(parent_materials) if isinstance(parent_materials, list) else 0,
            },
            dossier={
                "components": 0,
                "material_keys": 0,
                "operation_keys": 0,
                "task_rules": len(dossier_task_rules),
            },
            linked_modules={
                "required": len(modules.required),
                "optional": len(modules.optional),
                "child_templates": len(child_templates),
            },
            aggregate_totals={
                "components": len(components),
                "materials": len(materials),
                "operations": len(operations),
            },
        )

        if not dossier:
            warnings.append(
                ProductAggregateConflict(
                    code="DOSSIER_MISSING",
                    severity="warning",
                    message="No product_blueprint_dossier row found for template.",
                    details={"template_id": template.id},
                )
            )
        else:
            warnings.append(
                ProductAggregateConflict(
                    code="DOSSIER_METADATA_ONLY",
                    severity="info",
                    message=(
                        "Blueprint dossier is metadata for BOM/ops; "
                        "task_rules_json is consumed into task_contract for ExecutionPlan V2."
                    ),
                    details={
                        "template_id": template.id,
                        "dossier_id": dossier.id,
                        "dossier_status": dossier.status,
                        "task_rules_count": len(dossier_task_rules),
                        "authority": "canonical_template_contract"
                        if canonical.has_canonical_contract(template.template_code)
                        else "parent_template",
                    },
                )
            )
        if canonical.has_canonical_contract(template.template_code):
            warnings.append(
                ProductAggregateConflict(
                    code="CANONICAL_CONTRACT_AUTHORITY",
                    severity="info",
                    message="ProductAggregate compiled from canonical template/component contracts.",
                    details={"template_code": template.template_code},
                )
            )

        # Bounded traceability: requested → canonical identity (no payloads).
        if identity.requested_template_code and identity.canonical_template_code:
            warnings.append(
                ProductAggregateConflict(
                    code="TEMPLATE_IDENTITY",
                    severity="info",
                    message="Template identity resolution trace.",
                    details={
                        "requested_template_code": identity.requested_template_code,
                        "canonical_template_code": identity.canonical_template_code,
                        "resolution_type": identity.resolution_type,
                        "legacy_alias_used": identity.legacy_alias_used,
                        "resolution_source": identity.resolution_source,
                    },
                )
            )

        registry_service = get_mini_module_registry_service()
        registry_refs = registry_service.get_refs_for_template(template.template_code)

        aggregate = ProductAggregate(
            aggregate_version=AGGREGATE_VERSION,
            template_code=template.template_code,
            template_id=template.id,
            family_id=template.family_id,
            family_name=template.family_name,
            status="active" if template.active else "inactive",
            business_name_ro=business_name,
            modules=modules,
            components=components,
            materials=materials,
            operations=operations,
            form_contract=form_contract,
            cost_contract=cost_contract,
            task_contract=task_contract,
            conflicts=conflicts,
            warnings=warnings,
            provenance_summary=provenance_summary,
            mini_module_registry=ProductAggregateMiniModuleRegistrySummary(
                module_refs=registry_refs,
                notes=[
                    "Full contracts: GET /api/v1/product-system/mini-modules/by-template/{template_code}",
                ],
            ),
        )
        # Live bridge: modular process resolver replaces dossier task_rules for pilot template only.
        from services.product_process_aggregate_bridge import apply_modular_process_graph_to_aggregate

        pd_canonical: dict[str, Any] | None = None
        if isinstance(process_bridge_payload, dict):
            raw_pd = process_bridge_payload.get("product_definition_canonical_values")
            if isinstance(raw_pd, dict):
                pd_canonical = raw_pd

        return apply_modular_process_graph_to_aggregate(
            aggregate,
            workspace_payload=process_bridge_payload,
            product_definition_canonical_values=pd_canonical,
        )

    async def build_for_workspace(self, template_code: str, workspace_id: str) -> ProductAggregate | None:
        from services.product_aggregate_workspace_composition_service import build_workspace_composed_aggregate

        return await build_workspace_composed_aggregate(
            self._db,
            template_code=template_code,
            workspace_id=workspace_id,
        )

    async def _load_template(self, template_code: str) -> Product_templates | None:
        normalized = normalize_template_code(template_code)
        result = await self._db.execute(
            select(Product_templates)
            .where(func.upper(Product_templates.template_code) == normalized)
            .order_by(Product_templates.id.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _load_dossier(self, template_id: int) -> ProductBlueprintDossier | None:
        result = await self._db.execute(
            select(ProductBlueprintDossier).where(
                ProductBlueprintDossier.template_id == template_id
            )
        )
        return result.scalar_one_or_none()

    async def _load_module_links(self, parent_template_id: int) -> list[ProductTemplateModuleLink]:
        result = await self._db.execute(
            select(ProductTemplateModuleLink).where(
                ProductTemplateModuleLink.parent_template_id == parent_template_id,
                ProductTemplateModuleLink.active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def _load_child_templates(
        self, links: list[ProductTemplateModuleLink]
    ) -> dict[str, Product_templates]:
        ids = {link.module_template_id for link in links}
        if not ids:
            return {}
        result = await self._db.execute(
            select(Product_templates).where(Product_templates.id.in_(ids))
        )
        rows = list(result.scalars().all())
        return {row.template_code: row for row in rows}

    def _build_template_components(
        self,
        parent_components: Any,
        source_template_code: str,
    ) -> list[ProductAggregateComponent]:
        canonical = get_canonical_template_contract_service()
        rows = canonical.build_components_from_template_rows(
            parent_components,
            source_template_code=source_template_code,
        )
        return [
            ProductAggregateComponent(
                component_id=row["component_id"],
                label_ro=row.get("label_ro"),
                role=row.get("role"),
                mini_module_code=row.get("mini_module_code"),
                provenance="parent",
                source_template_code=source_template_code,
                status="present",
            )
            for row in rows
        ]

    def _build_form_contract_from_canonical(
        self,
        required: list[str],
        optional: list[str],
    ) -> ProductAggregateFormContract:
        geometry_keys = {"width_mm", "height_mm", "depth_mm", "letter_count", "vector_file"}
        form_fields = [
            ProductAggregateFormField(
                canonical_key=key,
                workspace_path=f"finish_setup.{key}" if key not in geometry_keys else None,
                required=True,
                provenance="parent",
            )
            for key in required
        ]
        return ProductAggregateFormContract(
            required_quote_input_keys=required,
            optional_quote_input_keys=optional,
            form_fields=form_fields,
        )

    def _build_modules(
        self,
        links: list[ProductTemplateModuleLink],
        child_templates: dict[str, Product_templates],
        warnings: list[ProductAggregateConflict],
    ) -> ProductAggregateModules:
        required: list[ProductAggregateModule] = []
        optional: list[ProductAggregateModule] = []

        for link in links:
            trigger_value: Any = _json_loads(link.trigger_value_json, None)
            module_code = CHILD_TEMPLATE_MINI_MODULE.get(
                link.module_template_code,
                link.module_template_code,
            )
            mod = ProductAggregateModule(
                module_code=module_code,
                business_name_ro=child_templates.get(link.module_template_code).family_name
                if link.module_template_code in child_templates
                else None,
                child_template_code=link.module_template_code,
                child_template_id=link.module_template_id,
                relation_type=link.relation_type,
                trigger_field=link.trigger_field,
                trigger_value=trigger_value,
                pricing_mode=link.pricing_mode,
                execution_mode=link.execution_mode,
                provenance="linked_module",
                active=bool(link.active),
                notes=link.notes,
            )
            if link.relation_type == "required_module":
                required.append(mod)
            else:
                optional.append(mod)

            alt_field = TRIGGER_FIELD_MISMATCHES.get(link.trigger_field or "")
            if alt_field:
                warnings.append(
                    ProductAggregateConflict(
                        code="TRIGGER_FIELD_MISMATCH",
                        severity="warning",
                        message=(
                            f"Module link trigger_field '{link.trigger_field}' may not match "
                            f"Intake V6 field '{alt_field}' used in commercial quote flow."
                        ),
                        field=link.trigger_field,
                        details={
                            "module_template_code": link.module_template_code,
                            "link_trigger_field": link.trigger_field,
                            "intake_field_candidate": alt_field,
                        },
                    )
                )

        return ProductAggregateModules(required=required, optional=optional)

    def _materials_from_rows(
        self,
        rows: Any,
        *,
        provenance: str,
        source_template_code: str,
        mini_module_code: str | None = None,
    ) -> list[ProductAggregateMaterial]:
        if not isinstance(rows, list):
            return []
        out: list[ProductAggregateMaterial] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            code = _material_code(row)
            if not code:
                continue
            out.append(
                ProductAggregateMaterial(
                    material_code=code,
                    label=row.get("label") or row.get("name"),
                    unit=row.get("unit"),
                    component_ref=row.get("component_ref"),
                    formula_id=row.get("formula_id"),
                    provenance=provenance,  # type: ignore[arg-type]
                    source_template_code=source_template_code,
                    mini_module_code=mini_module_code,
                    status="present",
                )
            )
        return out

    def _operations_from_rows(
        self,
        rows: Any,
        *,
        provenance: str,
        source_template_code: str,
        mini_module_code: str | None = None,
    ) -> list[ProductAggregateOperation]:
        if not isinstance(rows, list):
            return []
        out: list[ProductAggregateOperation] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            code = _operation_code(row)
            if not code:
                continue
            formula_params = row.get("formula_params") or {}
            non_priced = bool(formula_params.get("non_priced"))
            estimated_minutes = _optional_float(
                row.get("estimated_minutes", row.get("estimatedMinutes"))
            )
            calculation_type = row.get("calculation_type") or row.get("calculationType")
            if calculation_type is not None:
                calculation_type = str(calculation_type).strip() or None
            out.append(
                ProductAggregateOperation(
                    operation_code=code,
                    label=row.get("label") or row.get("name"),
                    workcenter=row.get("workcenter"),
                    component_ref=row.get("component_ref"),
                    formula_id=row.get("formula_id"),
                    priced=not non_priced,
                    estimated_minutes=estimated_minutes,
                    calculation_type=calculation_type,
                    provenance=provenance,  # type: ignore[arg-type]
                    source_template_code=source_template_code,
                    mini_module_code=mini_module_code,
                    status="present",
                )
            )
        return out

    def _build_form_contract(self, mapping: dict[str, Any]) -> ProductAggregateFormContract:
        inputs = mapping.get("inputs") or {}
        required = list(inputs.get("required") or [])
        optional = list(inputs.get("optional") or [])
        form_fields = [
            ProductAggregateFormField(
                canonical_key=key,
                workspace_path=f"finish_setup.{key}" if key not in {"width_mm", "height_mm", "depth_mm", "letter_count", "vector_file"} else None,
                required=True,
                provenance="parent",
            )
            for key in required
        ]
        return ProductAggregateFormContract(
            required_quote_input_keys=required,
            optional_quote_input_keys=optional,
            form_fields=form_fields,
        )

    def _build_cost_contract(
        self,
        mapping: dict[str, Any],
        materials: list[ProductAggregateMaterial],
        operations: list[ProductAggregateOperation],
    ) -> ProductAggregateCostContract:
        formula_ids = sorted(
            {
                m.formula_id
                for m in materials
                if m.formula_id
            }
            | {
                o.formula_id
                for o in operations
                if o.formula_id
            }
        )
        registry_materials = sorted({m.material_code for m in materials if m.provenance in ("parent", "linked_module")})
        workcenters = sorted({o.workcenter for o in operations if o.workcenter})
        notes = [
            "Dossier costengine_mapping_json is audit contract; runtime pricing uses product_templates BOM.",
            "OPEN QUESTION: unify preview and /price via aggregate-expanded BOM in Step 7.",
        ]
        return ProductAggregateCostContract(
            formula_ids=formula_ids,
            registry_material_codes=registry_materials,
            registry_workcenter_codes=workcenters,
            notes=notes,
        )

    def _extract_dossier_task_rules(
        self, dossier: ProductBlueprintDossier | None
    ) -> list[dict[str, Any]]:
        """Load dossier task_rules_json for ExecutionPlan V2 (bounded dossier consume)."""
        if dossier is None:
            return []
        raw = getattr(dossier, "task_rules_json", None)
        if raw is None or raw == "":
            return []
        if isinstance(raw, (list, dict)):
            data = raw
        elif isinstance(raw, str):
            data = _json_loads(raw, None)
        else:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("rules", "items"):
                items = data.get(key)
                if isinstance(items, list):
                    return [item for item in items if isinstance(item, dict)]
        return []

    def _build_task_contract(self, rules: list[dict[str, Any]]) -> ProductAggregateTaskContract:
        task_rules: list[ProductAggregateTaskRule] = []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            priced_op = rule.get("priced_operation")
            task_name = rule.get("task_name") or rule.get("task_code") or ""
            # Prefer explicit dossier mini_module_code (Build 4A.1 FACE+CANT interface).
            mini = rule.get("mini_module_code")
            if mini is not None:
                mini = str(mini).strip() or None
            if not mini and priced_op:
                mini = {
                    "face_cnc_cut": "debitare_fata",
                    "back_cut": "debitare_spate",
                    "side_forming": "modelare_cant",
                    # Interface bonding owns under modelare_cant (FACE+CANT), not asamblare.
                    "return_face_bonding": "modelare_cant",
                    "RETURN_PROFILE_FACE_BONDING": "modelare_cant",
                    "painting": "finisaje",
                    "vinyl_application": "colantare_fata",
                    "led_install_letters": "sistem_led",
                    "electrical_letters": "electrica_litere",
                    "mounting_template_cnc_cut": "sablon_montaj",
                    "packaging_letters": "ambalare_livrare_montaj",
                }.get(str(priced_op))
            dep_ids = rule.get("depends_on_process_ids") or rule.get("depends_on") or []
            if not isinstance(dep_ids, list):
                dep_ids = []
            task_rules.append(
                ProductAggregateTaskRule(
                    task_name=str(task_name),
                    task_type=rule.get("task_type"),
                    priced_operation=str(priced_op) if priced_op else None,
                    sequence=rule.get("sequence"),
                    trigger_condition=rule.get("trigger_condition"),
                    provenance="dossier",
                    mini_module_code=mini,
                    depends_on_process_ids=[str(d) for d in dep_ids if str(d).strip()],
                    process_code=str(rule.get("process_code") or "") or None,
                )
            )
        notes = (
            [
                "task_contract.task_rules compiled from product_blueprint_dossier.task_rules_json for ExecutionPlan V2.",
                "process_graph_source=dossier_legacy",
            ]
            if task_rules
            else [
                "No dossier task_rules_json available; ExecutionPlan V2 will block on empty task_contract.",
                "process_graph_source=dossier_legacy",
            ]
        )
        return ProductAggregateTaskContract(
            task_rules=task_rules,
            notes=notes,
            process_graph_source="dossier_legacy",
        )
