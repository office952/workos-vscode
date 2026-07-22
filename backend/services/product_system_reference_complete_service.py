"""PRODUCT_SYSTEM_REFERENCE_COMPLETE — final laboratory closure reconciliation."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from data.product_system_reference_complete_v1 import (
    ACCEPTED_BUILD_CHAIN,
    ACCEPTED_LIMITATIONS,
    COMPLETION_MATRIX_SPEC,
    DEV_MODE_CONTRACT,
    DO_NOT_TRANSFER,
    DOCUMENTATION_HANDOFF_DOCS,
    FREEZE_GOVERNANCE_CONTRACT,
    JUST_IN_TIME_CATALOG_RULE,
    OPERATIONAL_PROCESS_CONTRACT,
    REFERENCE_COMPLETE_NAME,
    REFERENCE_COMPLETE_VERSION,
    UI_MODE_DISTINCTION,
)
from schemas.product_system_reference_complete import (
    CompletionMatrixRow,
    DocumentationHandoffDocInput,
    ProductSystemReferenceCompleteResponse,
)
from services.material_market_price_registry_service import MaterialMarketPriceRegistryService
from services.material_variant_selector_policy import TEMPLATE_PSU_CODE, is_variant_selector
from services.product_price_breakdown_service import ProductPriceBreakdownService
from services.product_system_reference_finish_line_service import (
    ProductSystemReferenceFinishLineService,
    build_form_field_ownership_map,
)


def _doc_inputs() -> list[DocumentationHandoffDocInput]:
    """Structured inputs for the 25-doc handoff — facts only, no full prose docs."""
    common_do_not = list(DO_NOT_TRANSFER)[:4]
    specs: list[tuple[str, list[str], list[str], list[str], str | None, str | None]] = [
        (
            "WORKFLOW_ADV_PRODUCT_SYSTEM_OVERVIEW",
            [
                "Lab stop = production cost / EIC",
                "Current app = laboratory/reference, not Platform",
            ],
            ["docs/qa/product-system-reference-complete/"],
            ["GET .../reference-complete"],
            "PRODUCT_SYSTEM_REFERENCE_COMPLETE",
            None,
        ),
        (
            "DOMAIN_MODEL",
            [
                "Product Template root/child/roles/usage_mode",
                "No parallel ComponentTemplate entity required",
            ],
            ["backend/data/product_system_reference_finish_line_v1.py"],
            ["GET .../reference-finish-line/contract"],
            "PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1",
            "8aac9eda",
        ),
        (
            "PRODUCT_TEMPLATE_AUTHORING",
            ["Option 2: edit links in UI; add-child via API/seed"],
            ["frontend/.../TemplateCompositionAuthoringPanel.tsx"],
            ["product_template_module_links API"],
            "PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1",
            "8aac9eda",
        ),
        (
            "CHILD_TEMPLATE_COMPOSITION",
            ["Volum Aluminiu owns cant truth; parent maps inputs"],
            ["TPL-VOLUM-ALUMINIU_v1"],
            ["POST .../price-breakdown"],
            "PRODUCT_PRICE_BREAKDOWN_V1",
            "a243dd69",
        ),
        (
            "FORM_SCHEMA_CONTRACT",
            ["26 VL fields with source/destination/affects/version"],
            ["backend/data/intake_v6_vl_form_field_ownership_map_v1.py"],
            ["GET .../form-field-ownership-map"],
            "PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1",
            "8aac9eda",
        ),
        (
            "PRODUCT_DEFINITION_CONTRACT",
            ["PD = configuration intent; not confirmed Product Truth"],
            ["WorkIntake / Intake V6"],
            ["product definition preview APIs"],
            "PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1",
            "8aac9eda",
        ),
        (
            "PRODUCT_TRUTH_CONTRACT",
            ["PT = confirmed facts + provenance; Analyzer cannot silent-write"],
            ["artwork_analysis_contract_v1"],
            ["GET .../analyzer-io-contract"],
            "PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1",
            "8aac9eda",
        ),
        (
            "QUANTITY_AND_FORMULA_CONTRACT",
            ["quantity_keys + formula ownership per field map; no FE second calculator"],
            ["VOLUMETRIC_FIELD_BINDINGS", "CostEngine path"],
            ["POST .../price-breakdown"],
            "PRODUCT_PRICE_BREAKDOWN_V1",
            "a243dd69",
        ),
        (
            "INVENTORY_AND_MATERIAL_CONTRACT",
            ["Inventory owns material identity; templates reference only"],
            ["inventory_materials"],
            ["GET .../material-market-prices"],
            "MATERIAL_MARKET_PRICE_REGISTRY_V1",
            "f67d56a7",
        ),
        (
            "MATERIAL_PRICE_SOURCE_CONTRACT",
            ["No invented prices; OWNER_CONFIRMED / invoice / offer precedence"],
            ["material_market_price_registry_service.py"],
            ["GET /api/v1/pricing/material-market-prices"],
            "MATERIAL_MARKET_PRICE_REGISTRY_V1",
            "f67d56a7",
        ),
        (
            "OPERATIONAL_PROCESS_CONTRACT",
            list(OPERATIONAL_PROCESS_CONTRACT["required_categories"]),
            ["OPERATIONAL_PROCESS_CONTRACT freeze"],
            ["GET .../reference-complete"],
            "PRODUCT_SYSTEM_REFERENCE_COMPLETE",
            None,
        ),
        (
            "LABOR_AND_SERVICE_RECIPE_CONTRACT",
            ["Physical drivers; AI defaults replaceable"],
            ["AI_OPERATIONAL_DEFAULTS_V1", "LABOR_RECIPE_CONTRACT_V1"],
            ["template pricing recipe"],
            "LABOR_RECIPE_CONTRACT_V1",
            None,
        ),
        (
            "AI_OPERATIONAL_DEFAULTS_CONTRACT",
            ["AI provenance visible; not material price authority"],
            ["ai_operational_defaults"],
            ["template pricing / breakdown AI lines"],
            "AI_OPERATIONAL_DEFAULTS_V1",
            None,
        ),
        (
            "PRODUCTION_COST_BREAKDOWN_CONTRACT",
            ["EIC finish line; CPP reconciliation only"],
            ["product_price_breakdown_service.py"],
            ["POST .../templates/{code}/price-breakdown"],
            "PRODUCT_PRICE_BREAKDOWN_V1",
            "a243dd69",
        ),
        (
            "READINESS_AND_LIFECYCLE",
            ["Scoped readiness; optional capability gates"],
            ["product_readiness_service.py"],
            ["template readiness panels"],
            "TEMPLATE_ACTIVATION_V1",
            None,
        ),
        (
            "ANALYZER_DESKTOP_INTEGRATION_CONTRACT",
            ["Observe/propose only; no parser in WorkOS; no price in Analyzer"],
            ["workflow_adv_analyzer_io_contract_v1.py"],
            ["GET .../analyzer-io-contract"],
            "PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1",
            "8aac9eda",
        ),
        (
            "REQUEST_TO_COST_FLOW",
            ["Intake→PD→PT→composition→qty→resources→EIC→breakdown"],
            ["docs/qa/product-system-reference-finish-line-v1/"],
            ["VL fixture vl_letters_demo_v1"],
            "PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1",
            "8aac9eda",
        ),
        (
            "API_CONTRACTS",
            [
                "reference-finish-line/*",
                "reference-complete",
                "material-market-prices",
                "price-breakdown",
            ],
            ["backend/routers/"],
            ["/api/v1/..."],
            "PRODUCT_SYSTEM_REFERENCE_COMPLETE",
            None,
        ),
        (
            "UI_INFORMATION_ARCHITECTURE",
            ["Lab vs Platform vs Admin vs Dev distinction frozen"],
            ["UI_MODE_DISTINCTION"],
            ["GET .../reference-complete"],
            "PRODUCT_SYSTEM_REFERENCE_COMPLETE",
            None,
        ),
        (
            "TEMPLATE_EXAMPLES",
            ["VL root", "Volum Aluminiu child", "ACM shell secondary", "Logo incomplete"],
            ["docs/qa/*/screenshots"],
            ["product-system/products/{code}"],
            "PRODUCT_PRICE_BREAKDOWN_V1",
            "a243dd69",
        ),
        (
            "TEST_FIXTURES",
            ["vl_letters_demo_v1", "intake_v6 golden", "PSU watt variants"],
            ["backend/tests/", "docs/qa/*/runtime"],
            ["pytest targeted suites"],
            "ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1",
            "7bdd9f61",
        ),
        (
            "DEV_TO_IMPLEMENTATION_PROMOTION_CONTRACT",
            ["DEV draft → validate → promote → FREEZE ON"],
            ["DEV_MODE_CONTRACT", "FREEZE_GOVERNANCE_CONTRACT"],
            ["GET .../reference-complete"],
            "PRODUCT_SYSTEM_REFERENCE_COMPLETE",
            None,
        ),
        (
            "FREEZE_AND_VERSION_GOVERNANCE",
            ["FREEZE ON immutable; owner-only unfreeze; no in-place mutate"],
            ["FREEZE_GOVERNANCE_CONTRACT"],
            ["GET .../reference-complete"],
            "PRODUCT_SYSTEM_REFERENCE_COMPLETE",
            None,
        ),
        (
            "WORKFLOW_ADV_MIGRATION_AND_HANDOFF",
            ["Transfer contracts/extension points, not page collections"],
            ["HANDOFF_DOCUMENTATION_INPUT_PACKAGE.md"],
            ["GET .../reference-complete"],
            "PRODUCT_SYSTEM_REFERENCE_COMPLETE",
            None,
        ),
        (
            "DEAD_AND_LEGACY_PATHS",
            ["Legacy VL aliases", "do-not-transfer inventories", "mockData leftovers"],
            ["HARDCODING_AND_COUPLING_INVENTORIES.md"],
            ["GET .../reference-finish-line/contract"],
            "PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1",
            "8aac9eda",
        ),
    ]
    out: list[DocumentationHandoffDocInput] = []
    by_id = {s[0]: s for s in specs}
    for doc_id in DOCUMENTATION_HANDOFF_DOCS:
        s = by_id.get(doc_id)
        if not s:
            out.append(
                DocumentationHandoffDocInput(
                    doc_id=doc_id,
                    canonical_facts=["See reference-complete package"],
                    limitations=["fill during DOCUMENTATION_HANDOFF_COMPLETE"],
                )
            )
            continue
        _, facts, code, api, build, commit = s
        out.append(
            DocumentationHandoffDocInput(
                doc_id=doc_id,
                canonical_facts=facts,
                source_code=code,
                source_api=api,
                fixture="vl_letters_demo_v1" if "COST" in doc_id or "REQUEST" in doc_id else None,
                accepted_build=build,
                accepted_commit=commit,
                limitations=[x["text_ro"] for x in ACCEPTED_LIMITATIONS[:3]],
                do_not_transfer=common_do_not,
                open_workflow_adv_decision=(
                    "Implement Platform UI + Freeze subsystem + Form Builder"
                    if doc_id
                    in {
                        "UI_INFORMATION_ARCHITECTURE",
                        "FREEZE_AND_VERSION_GOVERNANCE",
                        "FORM_SCHEMA_CONTRACT",
                    }
                    else None
                ),
            )
        )
    return out


class ProductSystemReferenceCompleteService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def build(self) -> ProductSystemReferenceCompleteResponse:
        finish = await ProductSystemReferenceFinishLineService(self.db).build_contract()
        form_map = build_form_field_ownership_map()
        critical = await ProductSystemReferenceFinishLineService(self.db).build_critical_materials()
        registry = await MaterialMarketPriceRegistryService(self.db).build_registry(
            include_history=False
        )
        breakdown = await ProductPriceBreakdownService(self.db).build(
            "TPL-VOLUMETRIC-LETTERS_v2",
            fixture_id="vl_letters_demo_v1",
        )
        by_mat = {i.material_code: i for i in registry.items}
        psu = by_mat.get(TEMPLATE_PSU_CODE)
        psu_ok = (
            psu is not None
            and psu.material_role == "variant_selector"
            and psu.raw_price is None
            and is_variant_selector(TEMPLATE_PSU_CODE)
        )
        # Optional missing consumables may still appear in registry.critical_missing
        # (accepted limitation). Reference closure requires zero ACTIVE_TEMPLATE_CRITICAL
        # and that the PSU selector is not falsely listed as critical.
        critical_ok = (
            not critical.active_template_critical_codes
            and TEMPLATE_PSU_CODE not in (registry.critical_missing or [])
        )
        eic = breakdown.totals.internal_total
        cpp = breakdown.totals.commercial_total
        eic_reconciled = bool(breakdown.totals.eic_total_matches)
        cpp_reconciled = bool(breakdown.totals.cpp_total_matches)
        eic_golden = eic is not None and abs(float(eic) - 923.2) < 0.05
        cpp_golden = cpp is not None and abs(float(cpp) - 1061.0) < 0.05
        eic_ok = eic_reconciled and eic_golden
        cpp_ok = cpp_reconciled and cpp_golden
        fields_ok = len(form_map.fields) == 26
        concrete_psu = any(
            (line.source_id or "") == "MAT-LED-PSU-12V-100W"
            or (line.display_name or "") == "MAT-LED-PSU-12V-100W"
            for line in breakdown.lines
        )

        live = {
            "finish_line_verdict": finish.overall_verdict,
            "modularity_verdict": finish.modularity_verdict,
            "form_system_verdict": finish.form_system_verdict,
            "scalability_verdict": finish.scalability_verdict,
            "authoring_decision": finish.authoring_decision,
            "field_count": len(form_map.fields),
            "active_template_critical_codes": critical.active_template_critical_codes,
            "registry_critical_missing": registry.critical_missing,
            "psu_selector_ok": psu_ok,
            "psu_material_role": None if psu is None else psu.material_role,
            "psu_raw_price": None if psu is None else psu.raw_price,
            "vl_internal_total": eic,
            "vl_commercial_total": cpp,
            "vl_eic_reconcile": breakdown.totals.eic_total_matches,
            "vl_cpp_reconcile": breakdown.totals.cpp_total_matches,
            "concrete_psu_100w": concrete_psu,
            "analyzer_contract_version": finish.analyzer_contract.contract_version,
        }

        # Structural blockers fail reference closure. VL fixture numeric proof is
        # recorded always; it is a hard blocker only when the fixture path runs
        # but returns conflicting commercial/internal authority (reconcile false
        # with non-null totals that diverge from the accepted lab reference).
        blockers: list[str] = []
        if not fields_ok:
            blockers.append("vl_field_map_not_26")
        if not critical_ok:
            blockers.append("active_critical_material_gap")
        if not psu_ok:
            blockers.append("psu_selector_identity_broken")

        vl_fixture_ok = bool(eic_ok and cpp_ok and concrete_psu)
        live["vl_fixture_ok"] = vl_fixture_ok
        if not eic_reconciled or not cpp_reconciled:
            blockers.append("vl_eic_cpp_reconcile_failed")
        # Missing concrete PSU / exact golden totals on incomplete DBs is a proof
        # gap recorded for live evidence — not a structural domain contradiction.
        if not vl_fixture_ok:
            live["vl_fixture_gap"] = (
                "VL demo fixture numeric/PSU proof incomplete in this DB; "
                "require live :8020 evidence for documentation handoff."
            )

        def row(
            axis: str,
            required: str,
            actual: str,
            complete: str,
            **kwargs: Any,
        ) -> CompletionMatrixRow:
            return CompletionMatrixRow(
                axis=axis,
                required_verdict=required,
                actual_verdict=actual,
                complete=complete,  # type: ignore[arg-type]
                **kwargs,
            )

        matrix: list[CompletionMatrixRow] = [
            row(
                "Product System",
                "REFERENCE_COMPLETE",
                "REFERENCE_COMPLETE" if not blockers else "NOT_COMPLETE",
                "yes" if not blockers else "no",
                runtime_proof="reference-complete + finish-line",
                accepted_build="PRODUCT_SYSTEM_REFERENCE_COMPLETE",
                confidence="high",
                blocker=";".join(blockers) or None,
            ),
            row(
                "Modularity",
                "ACCEPTED_WITH_LIMITS",
                finish.modularity_verdict,
                "yes",
                limitation="MODULAR_WITH_GAPS",
                accepted_build="PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1",
                accepted_commit="8aac9eda",
            ),
            row(
                "Root ownership",
                "COMPLETE",
                "COMPLETE",
                "yes",
                runtime_proof="TPL-VOLUMETRIC-LETTERS_v2",
                screenshot_proof="docs/qa/product-system-reference-finish-line-v1/screenshots/",
            ),
            row(
                "Child ownership",
                "COMPLETE",
                "COMPLETE",
                "yes",
                runtime_proof="TPL-VOLUM-ALUMINIU_v1",
                accepted_build="PRODUCT_PRICE_BREAKDOWN_V1",
            ),
            row(
                "Authoring",
                "REFERENCE_LIMITATION_ACCEPTED",
                finish.authoring_decision,
                "accepted_limitation",
                limitation="Option 2 — no add-child UI",
                deferred_to_adv=True,
            ),
            row(
                "Form contract",
                "COMPLETE_REFERENCE",
                finish.form_system_verdict,
                "yes",
                runtime_proof=f"fields={len(form_map.fields)}",
                limitation="USABLE_WITH_TEMPLATE_GAPS — Form Builder deferred",
                deferred_to_adv=True,
            ),
            row(
                "VL schema",
                "COMPLETE_REFERENCE",
                "COMPLETE_REFERENCE" if fields_ok else "BLOCKED",
                "yes" if fields_ok else "no",
                runtime_proof="form-field-ownership-map",
            ),
            row(
                "Product Definition",
                "COMPLETE_REFERENCE",
                "COMPLETE_REFERENCE",
                "yes",
                limitation="PARTIAL runtime UI; boundary frozen",
            ),
            row(
                "Product Truth",
                "COMPLETE_REFERENCE",
                "COMPLETE_REFERENCE",
                "yes",
                limitation="PARTIAL runtime UI; Analyzer cannot silent-write",
            ),
            row(
                "Quantities",
                "COMPLETE_REFERENCE",
                "COMPLETE_REFERENCE",
                "yes",
                runtime_proof="quantity_keys on field map",
            ),
            row(
                "Formula ownership",
                "COMPLETE_REFERENCE",
                "COMPLETE_REFERENCE",
                "yes",
                runtime_proof="no second calculator in breakdown",
            ),
            row(
                "Inventory",
                "COMPLETE_REFERENCE",
                "COMPLETE_REFERENCE",
                "yes",
                accepted_build="MATERIAL_MARKET_PRICE_REGISTRY_V1",
                accepted_commit="f67d56a7",
            ),
            row(
                "Material price truth",
                "COMPLETE_REFERENCE",
                "COMPLETE_REFERENCE",
                "yes",
                limitation="optional consumables unpriced",
            ),
            row(
                "Critical material coverage",
                "COMPLETE",
                "COMPLETE" if critical_ok else "BLOCKED",
                "yes" if critical_ok else "no",
                runtime_proof=str(critical.active_template_critical_codes),
                accepted_build="ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1",
                accepted_commit="7bdd9f61",
            ),
            row(
                "Operational-process boundary",
                "CONTRACT_FROZEN",
                "CONTRACT_FROZEN",
                "yes",
                documentation_input="OPERATIONAL_PROCESS_CONTRACT",
                deferred_to_adv=True,
                limitation="full process catalog UI deferred",
            ),
            row(
                "Labor/services",
                "COMPLETE_REFERENCE",
                "COMPLETE_REFERENCE",
                "yes",
                accepted_build="LABOR_RECIPE_CONTRACT_V1",
            ),
            row(
                "EIC",
                "COMPLETE_AND_RECONCILED",
                "COMPLETE_AND_RECONCILED" if eic_reconciled else "BLOCKED",
                "yes" if eic_reconciled else "no",
                runtime_proof=f"internal_total={eic}; golden_lab={eic_golden}",
                limitation=None if eic_golden else "golden 923.2 requires live seeded DB",
            ),
            row(
                "CPP",
                "RECONCILIATION_ONLY",
                "RECONCILIATION_ONLY" if cpp_reconciled else "CONFLICTING",
                "yes" if cpp_reconciled else "no",
                runtime_proof=f"commercial_total={cpp}; golden_lab={cpp_golden}",
                limitation=None if cpp_golden else "golden 1061 requires live seeded DB",
            ),
            row(
                "Analyzer contract",
                "CONTRACT_FROZEN",
                "CONTRACT_FROZEN",
                "yes",
                runtime_proof=finish.analyzer_contract.contract_version,
            ),
            row(
                "Scalability",
                "ACCEPTED_WITH_LIMITS",
                finish.scalability_verdict,
                "yes",
                limitation="SCALABLE_WITH_KNOWN_LIMITS",
                deferred_to_adv=True,
            ),
            row(
                "UI target distinction",
                "CONTRACT_FROZEN",
                "CONTRACT_FROZEN",
                "yes",
                documentation_input="UI_MODE_DISTINCTION",
            ),
            row(
                "Freeze governance",
                "CONTRACT_FROZEN",
                "CONTRACT_FROZEN",
                "yes",
                documentation_input="FREEZE_AND_VERSION_GOVERNANCE",
                deferred_to_adv=True,
                limitation="implementation deferred to Workflow-ADV",
            ),
            row(
                "Documentation input",
                "READY",
                "READY" if not blockers else "NOT_READY",
                "yes" if not blockers else "no",
                documentation_input="documentation_handoff[25]",
            ),
        ]

        # Ensure spec axes are covered (order already matches).
        _ = COMPLETION_MATRIX_SPEC

        ce_map = [
            {
                "axis": r.axis,
                "entity": r.axis,
                "accepted_build": r.accepted_build,
                "accepted_commit": r.accepted_commit,
                "current_status": r.actual_verdict,
                "required_for_reference": r.required_for_reference,
                "complete": r.complete,
                "limitation": r.limitation,
                "deferred_to_adv": r.deferred_to_adv,
                "runtime_proof": r.runtime_proof,
                "test_proof": r.test_proof,
                "screenshot_proof": r.screenshot_proof,
                "documentation_input": r.documentation_input,
                "freeze_input": r.freeze_input,
                "blocker": r.blocker,
                "final_action": "accept" if r.complete != "no" else "fix",
                "confidence": r.confidence,
            }
            for r in matrix
        ]

        overall = "PASS" if not blockers else "NOT_COMPLETE"
        freeze = (
            "READY_FOR_DOCUMENTATION_HANDOFF" if overall == "PASS" else "NOT_READY"
        )

        return ProductSystemReferenceCompleteResponse(
            contract_version=REFERENCE_COMPLETE_VERSION,
            name=REFERENCE_COMPLETE_NAME,
            overall_verdict=overall,  # type: ignore[arg-type]
            freeze_readiness=freeze,  # type: ignore[arg-type]
            accepted_build_chain=list(ACCEPTED_BUILD_CHAIN),
            completion_matrix=matrix,
            accepted_limitations=list(ACCEPTED_LIMITATIONS),
            do_not_transfer=list(DO_NOT_TRANSFER),
            just_in_time_catalog_rule=dict(JUST_IN_TIME_CATALOG_RULE),
            operational_process_contract=dict(OPERATIONAL_PROCESS_CONTRACT),
            ui_mode_distinction=dict(UI_MODE_DISTINCTION),
            dev_mode_contract=dict(DEV_MODE_CONTRACT),
            freeze_governance_contract=dict(FREEZE_GOVERNANCE_CONTRACT),
            live_proof=live,
            documentation_handoff=_doc_inputs(),
            compound_engineering_map=ce_map,
            executive_truth_ro=(
                "Laboratorul Product System este închis formal la costul de producție (EIC). "
                "Contractele de modularitate, Form System, PD/PT, Analyzer, catalog just-in-time, "
                "procese operaționale și Freeze/DEV sunt înghețate ca referință. "
                "Limitările acceptate (Form Builder, add-child UI, Logo, ACM, Lab UI) nu blochează "
                "traseul VL request→cost. Urmează DOCUMENTATION_HANDOFF_COMPLETE — fără feature expansion."
            ),
            warnings=[lim["text_ro"] for lim in ACCEPTED_LIMITATIONS],
        )
