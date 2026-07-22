"""PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1 — contract assembly service."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from data.intake_v6_vl_form_field_ownership_map_v1 import (
    FIELD_OVERLAY,
    FINISH_LINE_FORM_MAP_VERSION,
    FORM_SYSTEM_CONTRACT_NOTES,
    default_overlay,
    resolve_source,
)
from data.product_system_reference_finish_line_v1 import (
    COUPLING_INVENTORY,
    EXTENSION_POINTS,
    FIELD_HARDCODING_INVENTORY,
    FINISH_LINE_CHECKLIST,
    FINISH_LINE_CONTRACT_VERSION,
    FINISH_LINE_NAME,
    FORMULA_DUPLICATION_INVENTORY,
    MANUAL_FILL_SEED,
    MATERIAL_CLASSIFICATION_POLICY,
    MODULARITY_MODEL,
    PAGE_SCOPE,
    PRODUCTION_COST_BOUNDARY,
    PRODUCTION_COST_EQUATION,
    TEMPLATE_CODE_BRANCH_INVENTORY,
)
from schemas.product_system_reference_finish_line import (
    CompoundEngineeringMapRow,
    CriticalMaterialPolicyItem,
    CriticalMaterialPolicyResponse,
    FinishLineChecklistItem,
    FinishLineContractResponse,
    FormFieldOwnershipMapResponse,
    FormFieldOwnershipRecord,
)
from schemas.workflow_adv_analyzer_io_contract_v1 import build_analyzer_io_contract_document
from services.intake_v6_modular_form_contract_service import (
    PILOT_TEMPLATE,
    VOLUMETRIC_FIELD_BINDINGS,
)
from services.material_market_price_registry_service import MaterialMarketPriceRegistryService


def _validation_rule(binding: Any) -> Optional[str]:
    parts: list[str] = []
    if binding.required:
        parts.append("required")
    if binding.min_value is not None:
        parts.append(f"min={binding.min_value}")
    if binding.max_value is not None:
        parts.append(f"max={binding.max_value}")
    if binding.unit:
        parts.append(f"unit={binding.unit}")
    return ";".join(parts) if parts else None


def build_form_field_ownership_map() -> FormFieldOwnershipMapResponse:
    fields: list[FormFieldOwnershipRecord] = []
    for binding in VOLUMETRIC_FIELD_BINDINGS:
        overlay = {**default_overlay(binding.canonical_key), **FIELD_OVERLAY.get(binding.canonical_key, {})}
        source = resolve_source(binding.decision, overlay)
        visibility = binding.visibility_rule
        if binding.visibility is not None and visibility is None:
            visibility = f"{binding.visibility.kind}:{binding.visibility.workspace_path}"
        options: list[Any] = []
        if binding.option_values:
            options = list(binding.option_values)
        elif binding.options:
            options = [o.value for o in binding.options]
        owner = binding.module_codes[0] if binding.module_codes else binding.field_role
        fields.append(
            FormFieldOwnershipRecord(
                field_id=binding.canonical_key,
                label=binding.label_ro,
                type=binding.field_type,
                unit=binding.unit,
                required=bool(binding.required),
                default=None,
                options=options,
                visibility_rule=visibility,
                validation_rule=_validation_rule(binding),
                owner=str(owner) if owner else None,
                source=source,
                destinations=list(overlay.get("destinations") or []),
                affects=list(overlay.get("affects") or []),
                version=FINISH_LINE_FORM_MAP_VERSION,
                workspace_path=binding.workspace_path,
                product_definition_keys=list(binding.product_definition_keys or []),
                child_template_codes=list(overlay.get("child_template_codes") or []),
                quantity_keys=list(overlay.get("quantity_keys") or []),
                cost_lines=list(overlay.get("cost_lines") or []),
                readiness_keys=list(overlay.get("readiness_keys") or []),
                analyzer_candidate=bool(overlay.get("analyzer_candidate")),
                analyzer_field=overlay.get("analyzer_field"),
                confirmation_required=bool(overlay.get("confirmation_required")),
                hardcoded_ui=bool(overlay.get("hardcoded_ui")),
                classification=str(overlay.get("classification") or "vl_specific_schema"),
                consumers=list(binding.consumers or []),
                decision=binding.decision,
            )
        )

    hardcoded = [f.field_id for f in fields if f.hardcoded_ui]
    analyzer_ids = [f.field_id for f in fields if f.analyzer_candidate]
    reusable = [f.field_id for f in fields if f.classification == "reusable_contract"]
    return FormFieldOwnershipMapResponse(
        contract_version=FINISH_LINE_FORM_MAP_VERSION,
        pilot_template=PILOT_TEMPLATE,
        form_system_verdict="USABLE_WITH_TEMPLATE_GAPS",
        fields=fields,
        classification_notes=dict(FORM_SYSTEM_CONTRACT_NOTES),
        hardcoded_ui_field_ids=hardcoded,
        analyzer_candidate_field_ids=analyzer_ids,
        reusable_field_ids=reusable,
    )


def build_compound_engineering_map(
    form_map: FormFieldOwnershipMapResponse,
    critical: CriticalMaterialPolicyResponse,
) -> list[CompoundEngineeringMapRow]:
    return [
        CompoundEngineeringMapRow(
            axis="modularity",
            entity="ProductTemplate root/child/roles",
            owner="Product System",
            current_state="root composes roles; child owns technical truth; add-child UI missing",
            reference_requirement="MODULAR_WITH_GAPS proven + authoring Option 2 documented",
            reusable_contract=True,
            template_specific=False,
            hardcoded=False,
            extension_point="product_template_module_links + usage_mode",
            input_schema="template identity/version/roles/links",
            output_contract="composition graph + formula ownership",
            PD_consumer="composition selected children",
            PT_consumer="confirmed child mappings",
            quantity_consumer="owning template formulas",
            cost_consumer="recipe / EIC lines",
            analyzer_relevance="suggested_roles only",
            handoff_status="gap",
            required_change="document Option 2; no Template Factory",
            proof="MODULARITY_MODEL + composition API",
            risk="medium",
            confidence="high",
        ),
        CompoundEngineeringMapRow(
            axis="form",
            entity="Intake/Form System field contract",
            owner="Form System contract + VL schema",
            current_state=f"{len(form_map.fields)} VL bindings mapped; specialized UI remains",
            reference_requirement="schema-driven contract frozen; VL is reference path",
            reusable_contract=True,
            template_specific=True,
            hardcoded=True,
            extension_point="field schema metadata source/destination/affects",
            input_schema=FINISH_LINE_FORM_MAP_VERSION,
            output_contract="PD → PT → quantity/cost",
            PD_consumer="product_definition_keys",
            PT_consumer="operator confirmation",
            quantity_consumer="quantity_keys",
            cost_consumer="cost_lines",
            analyzer_relevance="analyzer_candidate fields",
            handoff_status="gap",
            required_change="generalize beyond PILOT_TEMPLATE wiring",
            proof="GET .../form-field-ownership-map",
            risk="high",
            confidence="high",
        ),
        CompoundEngineeringMapRow(
            axis="pd_pt",
            entity="Product Definition vs Product Truth",
            owner="Workflow-ADV / operator confirmation",
            current_state="PARTIAL — PD draft vs PT confirmed must stay explicit",
            reference_requirement="PD intent; PT confirmed immutable snapshot",
            reusable_contract=True,
            template_specific=False,
            hardcoded=False,
            extension_point="confirmation + revision/hash",
            input_schema="Form destinations",
            output_contract="PT revision feeds formulas",
            PD_consumer="intake workspace",
            PT_consumer="quantity/cost",
            quantity_consumer="confirmed quantities",
            cost_consumer="confirmed recipe inputs",
            analyzer_relevance="proposals never auto-PT",
            handoff_status="gap",
            required_change="keep boundary labels in handoff docs",
            proof="finish-line checklist pd_pt",
            risk="medium",
            confidence="medium",
        ),
        CompoundEngineeringMapRow(
            axis="analyzer",
            entity="workflow_adv_analyzer_io_contract_v1",
            owner="Workflow-ADV Analyzer (external)",
            current_state="I/O frozen; no parser in WorkOS",
            reference_requirement="observe/propose + operator confirm",
            reusable_contract=True,
            template_specific=False,
            hardcoded=False,
            extension_point="observed_fields / proposed_fields bags",
            input_schema="AnalyzerIoHandoffPayloadV1",
            output_contract="PD candidates only",
            PD_consumer="mapped field_ids",
            PT_consumer="none until operator confirm",
            quantity_consumer="after PT",
            cost_consumer="none in Analyzer",
            analyzer_relevance="primary",
            handoff_status="ready",
            required_change="none for freeze",
            proof="GET .../analyzer-io-contract",
            risk="low",
            confidence="high",
        ),
        CompoundEngineeringMapRow(
            axis="cost",
            entity="EIC production cost finish line",
            owner="CostEngine / Price Breakdown adapter",
            current_state="VL breakdown reconciles EIC+CPP; lab stop = EIC",
            reference_requirement="production cost authority; CPP reconciliation only",
            reusable_contract=True,
            template_specific=False,
            hardcoded=False,
            extension_point="price-breakdown lines from recipe",
            input_schema="recipe + inventory unit_cost",
            output_contract="internal_production_cost",
            PD_consumer="n/a",
            PT_consumer="confirmed inputs",
            quantity_consumer="formula outputs",
            cost_consumer="Desfasurator",
            analyzer_relevance="none",
            handoff_status="ready",
            required_change="label Cost productie vs Pret comercial",
            proof="PriceBreakdownSection labels + ownership_note",
            risk="low",
            confidence="high",
        ),
        CompoundEngineeringMapRow(
            axis="materials",
            entity="critical material classification",
            owner="Inventory purchase truth + finish-line policy",
            current_state=(
                f"critical={critical.active_template_critical_codes}; "
                f"manual_fill={critical.manual_fill_required_codes}"
            ),
            reference_requirement="policy frozen; no invented prices; no supplier import",
            reusable_contract=True,
            template_specific=True,
            hardcoded=False,
            extension_point="MATERIAL_CLASSIFICATION_POLICY",
            input_schema="inventory_materials.unit_cost",
            output_contract="manual-fill checklist",
            PD_consumer="n/a",
            PT_consumer="n/a",
            quantity_consumer="n/a",
            cost_consumer="material lines",
            analyzer_relevance="none",
            handoff_status="gap",
            required_change="ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1 (follow-up)",
            proof="GET .../critical-materials",
            risk="medium",
            confidence="high",
        ),
        CompoundEngineeringMapRow(
            axis="scalability",
            entity="extension points without page copies",
            owner="Product System + Form System contracts",
            current_state="SCALABLE_WITH_KNOWN_LIMITS",
            reference_requirement="add template/child/field/analyzer field via contracts",
            reusable_contract=True,
            template_specific=False,
            hardcoded=True,
            extension_point="EXTENSION_POINTS list",
            input_schema="per-extension",
            output_contract="no duplicate calculators",
            PD_consumer="schema fields",
            PT_consumer="confirmation",
            quantity_consumer="declared keys",
            cost_consumer="recipe lines",
            analyzer_relevance="new analyzer fields via I/O contract",
            handoff_status="gap",
            required_change="close VL pilot hardwiring in Workflow-ADV",
            proof="extension_points + hardcoding inventories",
            risk="high",
            confidence="medium",
        ),
    ]


class ProductSystemReferenceFinishLineService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def build_critical_materials(self) -> CriticalMaterialPolicyResponse:
        registry = await MaterialMarketPriceRegistryService(self.db).build_registry(
            include_history=False,
            active_templates_only=False,
        )
        by_code = {r.material_code: r for r in registry.items}
        items: list[CriticalMaterialPolicyItem] = []
        for seed in MANUAL_FILL_SEED:
            code = str(seed["material_code"])
            row = by_code.get(code)
            missing = True if row is None else (row.raw_price is None)
            classification = str(seed["classification"])
            if not missing and classification == "ACTIVE_TEMPLATE_CRITICAL":
                classification = "ACTIVE_TEMPLATE_OPTIONAL"
            evidence = None
            if row is not None:
                evidence = (
                    f"inventory status={row.inventory_status}; "
                    f"unit_cost={row.raw_price}; source_type={row.source_type}"
                )
            items.append(
                CriticalMaterialPolicyItem(
                    material_code=code,
                    classification=classification,
                    unit_cost=None if row is None else row.raw_price,
                    currency=None if row is None else row.currency,
                    missing_price=missing,
                    templates=list(seed.get("templates") or []),
                    reason_ro=str(seed["reason_ro"]),
                    action="none_priced" if not missing else str(seed["action"]),
                    do_not=list(seed.get("do_not") or []),
                    evidence=evidence,
                )
            )

        # Registry may flag many VOLUMETRIC-linked missing prices as critical_missing.
        # Finish-line policy keeps ACTIVE_TEMPLATE_CRITICAL narrow (seed-driven);
        # extra registry gaps are ACTIVE_TEMPLATE_OPTIONAL unless already seeded.
        hard_critical = {
            str(s["material_code"])
            for s in MANUAL_FILL_SEED
            if s.get("classification") == "ACTIVE_TEMPLATE_CRITICAL"
        }
        for code in registry.critical_missing or []:
            if any(i.material_code == code for i in items):
                continue
            row = by_code.get(code)
            classification = (
                "ACTIVE_TEMPLATE_CRITICAL"
                if code in hard_critical
                else "ACTIVE_TEMPLATE_OPTIONAL"
            )
            items.append(
                CriticalMaterialPolicyItem(
                    material_code=code,
                    classification=classification,
                    unit_cost=None if row is None else row.raw_price,
                    currency=None if row is None else row.currency,
                    missing_price=True,
                    templates=list(row.active_templates) if row else [],
                    reason_ro=(
                        "Apare în critical_missing din Material Market Price Registry "
                        "(activ pe template + fără unit_cost). "
                        "Clasificare finish-line: critical doar dacă e în seed CRITICAL."
                    ),
                    action="manual_owner_fill_if_missing",
                    do_not=["invent_price", "supplier_import"],
                    evidence="material_market_price_registry.critical_missing",
                )
            )

        active_critical = [
            i.material_code
            for i in items
            if i.classification == "ACTIVE_TEMPLATE_CRITICAL" and i.missing_price
        ]
        manual = [i.material_code for i in items if i.missing_price]
        notes = [
            "Nu inventăm prețuri în acest build.",
            "Nu construim Supplier Import.",
            "Următorul fill dedicat: ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1 (owner GO).",
        ]
        if active_critical == ["MAT-LED-PSU-12V"]:
            notes.append("Confirmare runtime: singurul ACTIVE_TEMPLATE_CRITICAL rămâne MAT-LED-PSU-12V.")
        elif not active_critical:
            notes.append("Niciun ACTIVE_TEMPLATE_CRITICAL cu preț lipsă la runtime (verificați seed).")
        else:
            notes.append(f"ACTIVE_TEMPLATE_CRITICAL cu preț lipsă: {', '.join(active_critical)}")

        return CriticalMaterialPolicyResponse(
            contract_version=FINISH_LINE_CONTRACT_VERSION,
            policy=dict(MATERIAL_CLASSIFICATION_POLICY),
            items=items,
            active_template_critical_codes=active_critical,
            manual_fill_required_codes=manual,
            notes_ro=notes,
        )

    async def build_contract(self) -> FinishLineContractResponse:
        form_map = build_form_field_ownership_map()
        critical = await self.build_critical_materials()
        analyzer = build_analyzer_io_contract_document()
        ce_map = build_compound_engineering_map(form_map, critical)

        checklist: list[FinishLineChecklistItem] = []
        for raw in FINISH_LINE_CHECKLIST:
            entity = raw["entity"]
            status: str = "ready"
            proof = None
            notes = None
            if entity == "vl_ownership_map":
                proof = f"{len(form_map.fields)} fields"
                status = "ready" if form_map.fields else "gap"
            elif entity == "workflow_adv_analyzer_io_v1":
                proof = analyzer.contract_version
                status = "ready"
            elif entity == "critical_classification_policy":
                proof = ",".join(critical.active_template_critical_codes) or "none"
                status = "ready"
            elif entity == "authoring_option_2":
                proof = MODULARITY_MODEL["authoring_decision"]
                status = "ready"
                notes = MODULARITY_MODEL["authoring_note_ro"]
            elif entity == "eic_production_cost":
                proof = "production_cost_boundary.completion_authority"
                status = "ready"
            elif entity in {"field_schema_contract", "extension_points"}:
                status = "ready"
            elif entity in {
                "root_child_roles_usage_mode",
                "product_definition_vs_truth",
                "formula_ownership",
                "handoff_input_package",
            }:
                status = "gap"
                notes = "Documented in finish-line package; runtime UI proof in CP7 evidence."
            elif entity == "cpp_reconciliation":
                status = "ready"
                notes = "CPP visible for reconcile; not lab-stop for offer."
            checklist.append(
                FinishLineChecklistItem(
                    axis=raw["axis"],
                    entity=entity,
                    requirement=raw["requirement"],
                    status=status,  # type: ignore[arg-type]
                    proof=proof,
                    notes_ro=notes,
                )
            )

        warnings = [
            "Authoring Option 2: add-child UI deferred (API/seed only).",
            "Form System remains VL-pilot wired (USABLE_WITH_TEMPLATE_GAPS).",
            "Generic Form Builder deferred to Workflow-ADV.",
        ]
        if critical.active_template_critical_codes:
            warnings.append(
                "Critical materials missing price: "
                + ", ".join(critical.active_template_critical_codes)
            )

        return FinishLineContractResponse(
            contract_version=FINISH_LINE_CONTRACT_VERSION,
            finish_line_name=FINISH_LINE_NAME,
            production_cost_equation=PRODUCTION_COST_EQUATION,
            production_cost_boundary=dict(PRODUCTION_COST_BOUNDARY),
            modularity=dict(MODULARITY_MODEL),
            modularity_verdict="MODULAR_WITH_GAPS",
            form_system_verdict=form_map.form_system_verdict,
            scalability_verdict="SCALABLE_WITH_KNOWN_LIMITS",
            authoring_decision=str(MODULARITY_MODEL["authoring_decision"]),
            checklist=checklist,
            page_scope=dict(PAGE_SCOPE),
            extension_points=list(EXTENSION_POINTS),
            template_code_branch_inventory=list(TEMPLATE_CODE_BRANCH_INVENTORY),
            field_hardcoding_inventory=list(FIELD_HARDCODING_INVENTORY),
            formula_duplication_inventory=list(FORMULA_DUPLICATION_INVENTORY),
            coupling_inventory=list(COUPLING_INVENTORY),
            compound_engineering_map=ce_map,
            analyzer_contract=analyzer,
            form_field_map_summary={
                "field_count": len(form_map.fields),
                "reusable_count": len(form_map.reusable_field_ids),
                "hardcoded_ui_count": len(form_map.hardcoded_ui_field_ids),
                "analyzer_candidate_count": len(form_map.analyzer_candidate_field_ids),
            },
            critical_materials_summary={
                "active_template_critical": critical.active_template_critical_codes,
                "manual_fill_required": critical.manual_fill_required_codes,
            },
            overall_verdict="PASS_WITH_WARNINGS",
            warnings=warnings,
        )
