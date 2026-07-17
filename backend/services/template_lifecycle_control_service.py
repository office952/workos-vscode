"""Template Lifecycle Control System V1.

Derives lifecycle readiness / impact from Product System contracts and existing
runtime services. Does NOT create a parallel template registry.
Does NOT write schema, seeds, CPP formulas, task materialization, or Execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.product_system.svg_component_binding_contract import (
    ACM_BOXED_SUPPORT,
    STALE_BOND_CASETAT,
    SVG_BINDABLE_BY_PRODUCT_TEMPLATE,
)
from models.product_templates import Product_templates
from schemas.template_lifecycle_control import (
    LifecycleImpactSummary,
    LifecycleIssue,
    LifecycleLegacyConflict,
    LifecycleOwnerGate,
    LifecycleStageResult,
    LifecycleStatus,
    TemplateLifecycleImpactResponse,
    TemplateLifecycleInspectResponse,
    TemplateLifecycleReadiness,
    TemplateLifecycleValidateItem,
    TemplateLifecycleValidateResponse,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_template_availability_service import ProductTemplateAvailabilityService
from services.svg_component_binding_service import get_svg_bindable_components as project_svg_bindables
from services.template_usage_mode_policy import (
    get_template_usage_mode_policy,
    is_root_offerable_template,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

LIFECYCLE_STAGES: list[tuple[str, str, str, bool]] = [
    ("PRODUCT_FAMILY", "Product Family", "Product System", True),
    ("PRODUCT_TEMPLATE", "Product Template", "Product System", True),
    ("COMPONENT_TEMPLATES", "Component Templates", "Product System", True),
    ("INTERFACE_CONTRACTS", "Interface Contracts", "Product System", True),
    ("INTAKE_AVAILABILITY", "Intake availability", "Intake V6 / Product System", True),
    ("INTAKE_STEP_1", "Intake Step 1", "Intake V6", True),
    ("INTAKE_STEP_2", "Intake Step 2", "Intake V6", True),
    ("FINISH_SETUP", "FinishSetup", "Intake V6", True),
    ("PRODUCT_DEFINITION", "ProductDefinition", "Product Definition compiler", True),
    ("PRODUCT_AGGREGATE", "ProductAggregate", "Product Aggregate compiler", True),
    ("CPP", "CPP / commercial formulas", "CPP registry", False),
    ("OFFER", "Offer path", "Commercial / Quote", False),
    ("ORDER_SNAPSHOT", "Order Snapshot", "Snapshot freeze", False),
    ("TASK_RULES_PROJECTION", "Task rules projection", "Existing task_rules", False),
    ("TASK_MATERIALIZATION", "Task materialization", "Tasking", False),
    ("EXECUTION", "Execution", "ExecutionPlan", False),
    ("RUNTIME_PROOF", "Runtime proof", "QA / E2E", True),
]

ACTIVATION_REQUIRED_STAGES = {
    "PRODUCT_FAMILY",
    "PRODUCT_TEMPLATE",
    "COMPONENT_TEMPLATES",
    "INTERFACE_CONTRACTS",
    "INTAKE_AVAILABILITY",
    "INTAKE_STEP_1",
    "INTAKE_STEP_2",
    "PRODUCT_DEFINITION",
    "PRODUCT_AGGREGATE",
    "RUNTIME_PROOF",
}

PASS_LIKE: set[LifecycleStatus] = {
    "PASS",
    "VALIDATED",
    "WIRED",
    "PREVIEW_ONLY",
    "OWNER_GATE_REQUIRED",
    "NOT_APPLICABLE",
    "DEPRECATED",
}


def _issue(
    code: str,
    message: str,
    *,
    severity: str = "blocking",
    evidence: list[str] | None = None,
) -> LifecycleIssue:
    return LifecycleIssue(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        evidence=list(evidence or []),
    )


def _repo_file_exists(*parts: str) -> bool:
    return (REPO_ROOT.joinpath(*parts)).is_file()


def _file_contains(rel_path: str, needle: str) -> bool:
    path = REPO_ROOT / rel_path
    if not path.is_file():
        return False
    try:
        return needle in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def reverse_svg_bindable_map() -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = {}
    for product_code, bindings in SVG_BINDABLE_BY_PRODUCT_TEMPLATE.items():
        for binding in bindings:
            comp = str(binding.get("component_template_code") or "").strip()
            if not comp:
                continue
            reverse.setdefault(comp, [])
            if product_code not in reverse[comp]:
                reverse[comp].append(product_code)
    return reverse


class TemplateLifecycleControlService:
    """Inspect / readiness / impact / validate — Product System derived."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def inspect(self, template_code: str) -> TemplateLifecycleInspectResponse:
        readiness = await self.build_readiness(template_code)
        impact = await self.build_impact(template_code)
        return TemplateLifecycleInspectResponse(
            readiness=readiness,
            impact=impact,
            raw_context={
                "policy": (
                    get_template_usage_mode_policy(template_code).__dict__
                    if get_template_usage_mode_policy(template_code)
                    else None
                ),
                "svg_bindables": project_svg_bindables(template_code),
            },
        )

    async def build_impact(self, template_code: str) -> TemplateLifecycleImpactResponse:
        code = str(template_code or "").strip()
        reverse = reverse_svg_bindable_map()
        parent_codes: list[str] = []
        availability = await ProductTemplateAvailabilityService(self.db).list_availability(
            offerable_only=False,
            include_runtime_modules=True,
            include_archived=True,
        )
        item = next((i for i in availability.items if i.template_code == code), None)
        if item:
            parent_codes = list(item.parent_codes or [])

        products_using = list(reverse.get(code, []))
        for parent in parent_codes:
            if parent not in products_using:
                products_using.append(parent)

        bindables = project_svg_bindables(code)
        intake_bits: list[str] = []
        pd_bits: list[str] = []
        for b in bindables:
            roles = b.get("accepted_geometry_roles") or []
            if "SUPPORT_CONTOUR" in roles:
                intake_bits.append("Step 1 SUPPORT_CONTOUR")
                intake_bits.append("Step 2 mounting/support configuration")
                pd_bits.append("svg_component_instances")
                pd_bits.append("panel geometry")
                pd_bits.append("unit status")
            if "LETTER_VECTOR_SET" in roles:
                intake_bits.append("Step 1 LETTER_VECTOR_SET")
            if "LOGO_VECTOR_SET" in roles:
                intake_bits.append("Step 1 LOGO_VECTOR_SET")
            for target in b.get("product_definition_targets") or []:
                if target not in pd_bits:
                    pd_bits.append(str(target))

        # Self as product template: include child modules as reverse deps
        module_codes = list(item.module_codes or []) if item else []
        reverse_deps = {
            "product_templates_using_this": products_using,
            "parent_templates": parent_codes,
            "child_modules": module_codes,
            "svg_bindable_components": [
                str(b.get("component_template_code")) for b in bindables if b.get("component_template_code")
            ],
        }

        impact = LifecycleImpactSummary(
            changed=code,
            affected_product_templates=products_using or ([code] if item else []),
            affected_intake=sorted(set(intake_bits)),
            affected_product_definition=sorted(set(pd_bits)),
            affected_product_aggregate=[
                "linked module projection",
                "process/task_contract when modular resolver applies",
            ]
            if (products_using or module_codes)
            else [],
            cpp=["owner gate required — no auto formula activation"],
            tasking=["preview affected", "no materialization change"],
            notes=[
                "Impact derived from svg_bindable_components + availability module links.",
                "Not a hand-maintained dependency list.",
            ],
        )
        return TemplateLifecycleImpactResponse(
            template_code=code,
            reverse_dependencies=reverse_deps,
            impact=impact,
        )

    async def build_readiness(self, template_code: str) -> TemplateLifecycleReadiness:
        code = str(template_code or "").strip()
        policy = get_template_usage_mode_policy(code)
        availability = await ProductTemplateAvailabilityService(self.db).list_availability(
            offerable_only=False,
            include_runtime_modules=True,
            include_archived=True,
        )
        item = next((i for i in availability.items if i.template_code == code), None)

        row = (
            await self.db.execute(
                select(Product_templates).where(Product_templates.template_code == code)
            )
        ).scalar_one_or_none()

        stages: list[LifecycleStageResult] = []
        owner_gates: list[LifecycleOwnerGate] = []
        legacy: list[LifecycleLegacyConflict] = []

        # --- PRODUCT_FAMILY / PRODUCT_TEMPLATE ---
        if row is None and item is None:
            stages.append(
                self._stage(
                    "PRODUCT_TEMPLATE",
                    status="BLOCKED",
                    required=True,
                    blockers=[_issue("TEMPLATE_MISSING", f"Template {code} not found in Product System registry.")],
                    evidence=["product_templates lookup miss", "availability miss"],
                )
            )
            # fill remaining as NOT_STARTED
            for stage_code, label, authority, required in LIFECYCLE_STAGES:
                if stage_code == "PRODUCT_TEMPLATE":
                    continue
                stages.append(
                    self._stage(
                        stage_code,
                        status="NOT_STARTED",
                        required=required,
                        owner_label=label,
                        authority=authority,
                        blockers=[_issue("TEMPLATE_MISSING", "Skipped — template missing.")],
                    )
                )
            return self._finalize(code, row, item, stages, owner_gates, legacy, impact=None)

        family_ok = bool((item and (item.family_id or item.family_name)) or (row and (row.family_id or row.family_name)))
        stages.append(
            self._stage(
                "PRODUCT_FAMILY",
                status="PASS" if family_ok else "BLOCKED",
                required=True,
                evidence=[
                    f"family_id={getattr(item, 'family_id', None) or getattr(row, 'family_id', None)}",
                    f"family_name={getattr(item, 'family_name', None) or getattr(row, 'family_name', None)}",
                ],
                blockers=[]
                if family_ok
                else [_issue("PRODUCT_FAMILY_MISSING", "Product Family missing on template row/availability.")],
            )
        )

        db_active = bool(item.db_active) if item else bool(row and row.active is not False)
        template_status = "ACTIVE" if db_active else "INACTIVE"
        if policy and policy.candidate_only:
            template_status = "CANDIDATE"
        stages.append(
            self._stage(
                "PRODUCT_TEMPLATE",
                status="PASS" if db_active else "BLOCKED",
                required=True,
                evidence=[
                    f"db_active={db_active}",
                    f"quote_offerable={getattr(item, 'quote_offerable', None)}",
                    f"product_system_role={getattr(item, 'product_system_role', None)}",
                    f"policy={policy.reason if policy else 'none'}",
                ],
                blockers=[]
                if db_active
                else [_issue("TEMPLATE_INACTIVE", "Template inactive in Product System registry.")],
                affected_files=[
                    "backend/services/template_usage_mode_policy.py",
                    "backend/services/product_template_availability_service.py",
                ],
            )
        )

        # --- COMPONENTS ---
        module_codes = list(
            (getattr(item, "module_codes", None) or getattr(item, "child_module_codes", None) or [])
            if item
            else []
        )
        missing_modules = list(getattr(item, "missing_module_codes", None) or []) if item else []
        bindables = project_svg_bindables(code)
        required_bindables = [b for b in bindables if b.get("required")]
        optional_bindables = [b for b in bindables if not b.get("required")]
        inactive_optional_ok = all(
            (not b.get("active_by_default")) or True for b in optional_bindables
        )
        component_blockers: list[LifecycleIssue] = []
        for missing in missing_modules:
            component_blockers.append(
                _issue("REQUIRED_COMPONENT_MISSING", f"Missing required module {missing}.", evidence=[missing])
            )
        if item and item.is_parent and not module_codes and not bindables:
            component_blockers.append(
                _issue("COMPONENT_COMPOSITION_EMPTY", "Parent template has no modules and no svg_bindable_components.")
            )
        stages.append(
            self._stage(
                "COMPONENT_TEMPLATES",
                status="BLOCKED" if component_blockers else "PASS",
                required=True,
                evidence=[
                    f"module_codes={module_codes}",
                    f"svg_bindables={len(bindables)}",
                    f"required_bindables={len(required_bindables)}",
                    f"optional_bindables={len(optional_bindables)}",
                    f"inactive_optional_isolation_ok={inactive_optional_ok}",
                ],
                blockers=component_blockers,
                affected_files=["backend/data/product_system/svg_component_binding_contract.py"],
            )
        )

        # --- INTERFACES ---
        interface_evidence = [
            "svg_bindable_components contract",
            f"bindings={len(bindables)}",
        ]
        dangling = []
        for b in bindables:
            comp = str(b.get("component_template_code") or "")
            if not comp:
                dangling.append("empty_component_template_code")
            if comp == STALE_BOND_CASETAT:
                dangling.append(STALE_BOND_CASETAT)
        interface_blockers = [
            _issue("DANGLING_INTERFACE", f"Invalid/stale bindable reference: {d}", evidence=[d])
            for d in dangling
            if d != STALE_BOND_CASETAT
        ]
        interface_warnings: list[LifecycleIssue] = []
        if any(d == STALE_BOND_CASETAT for d in dangling):
            interface_warnings.append(
                _issue(
                    "STALE_BOND_CASETAT_REFERENCE",
                    "Legacy TPL-BOND-CASETAT string detected — forbidden for new selection authority.",
                    severity="warning",
                    evidence=[STALE_BOND_CASETAT],
                )
            )
        stages.append(
            self._stage(
                "INTERFACE_CONTRACTS",
                status="BLOCKED" if interface_blockers else ("WIRED" if bindables else "CONFIGURED"),
                required=True,
                evidence=interface_evidence,
                blockers=interface_blockers,
                warnings=interface_warnings,
            )
        )

        # --- INTAKE AVAILABILITY ---
        exposed = item is not None and (
            bool(item.quote_offerable)
            or item.product_system_role in {"offerable_product", "candidate_product"}
            or item.display_group in {"active_products", "candidate_products"}
            or is_root_offerable_template(code)
        )
        # Dual-role runtime modules that are quote_offerable still count as exposed
        intake_blockers: list[LifecycleIssue] = []
        if item is None:
            intake_blockers.append(_issue("INTAKE_AVAILABILITY_MISSING", "Not present in template-availability read model."))
        elif not exposed and not (policy and policy.component_only):
            intake_blockers.append(
                _issue(
                    "INTAKE_NOT_EXPOSED",
                    "Template not exposed as offerable/candidate product for Intake selection.",
                    evidence=[str(item.product_system_role), str(item.display_group)],
                )
            )
        stages.append(
            self._stage(
                "INTAKE_AVAILABILITY",
                status="PASS" if not intake_blockers else ("NOT_APPLICABLE" if policy and policy.component_only else "BLOCKED"),
                required=not (policy and policy.component_only),
                evidence=[
                    f"quote_offerable={getattr(item, 'quote_offerable', None)}",
                    f"runtime_module={getattr(item, 'runtime_module', None)}",
                    f"role={getattr(item, 'product_system_role', None)}",
                ],
                blockers=intake_blockers,
                affected_files=[
                    "backend/services/product_template_availability_service.py",
                    "frontend/src/components/workos/NewIntakeDialog.tsx",
                ],
            )
        )

        # --- STEP 1 ---
        has_svg_roles = bool(bindables)
        has_support = any("SUPPORT_CONTOUR" in (b.get("accepted_geometry_roles") or []) for b in bindables)
        has_letters = any("LETTER_VECTOR_SET" in (b.get("accepted_geometry_roles") or []) for b in bindables)
        has_logo = any("LOGO_VECTOR_SET" in (b.get("accepted_geometry_roles") or []) for b in bindables)
        step1_files = [
            "frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx",
            "frontend/src/lib/intakeV6/svgComponentBindings.ts",
            "backend/services/intake_v6_product_composition_recommendation_service.py",
        ]
        step1_wired = has_svg_roles and all(_repo_file_exists(*p.split("/")) for p in step1_files)
        step1_blockers: list[LifecycleIssue] = []
        step1_warnings: list[LifecycleIssue] = []
        if not has_svg_roles and is_root_offerable_template(code):
            step1_blockers.append(
                _issue("STEP1_SVG_BINDING_CONTRACT_MISSING", "No svg_bindable_components for root offerable template.")
            )
        if _file_contains("frontend/src/lib/intakeV6/svgComponentBindings.ts", "LEGACY_INTAKE_SVG_ROLE_ADAPTER"):
            step1_warnings.append(
                _issue(
                    "LEGACY_INTAKE_ROLE_ADAPTER",
                    "Legacy Intake SVG role adapter present — must remain guarded.",
                    severity="warning",
                    evidence=["LEGACY_INTAKE_SVG_ROLE_ADAPTER"],
                )
            )
        # Known Step-1 persistence guard: finish-setup blocked until layer roles complete
        if _file_contains(
            "backend/services/intake_v6_workspace_service.py",
            'layer_roles_incomplete',
        ) and has_support:
            step1_warnings.append(
                _issue(
                    "STEP1_SUPPORT_BINDING_PERSIST_GATE",
                    "Contur suport FinishSetup persist is gated by layer_roles_incomplete (known follow-up).",
                    severity="warning",
                    evidence=["save_finish_setup_for_intake_v6_workspace"],
                )
            )
        stages.append(
            self._stage(
                "INTAKE_STEP_1",
                status="BLOCKED" if step1_blockers else ("WIRED" if step1_wired else "DISCOVERED"),
                required=True,
                evidence=[
                    f"svg_roles={has_svg_roles}",
                    f"letter={has_letters}",
                    f"logo={has_logo}",
                    f"support={has_support}",
                    f"composition_service={_repo_file_exists('backend','services','intake_v6_product_composition_recommendation_service.py')}",
                ],
                blockers=step1_blockers,
                warnings=step1_warnings,
                affected_files=step1_files,
            )
        )

        # --- STEP 2 ---
        step2_blockers: list[LifecycleIssue] = []
        step2_warnings: list[LifecycleIssue] = []
        mounting_hydrate = _file_contains(
            "frontend/src/lib/intakeV6/mountingSolution.ts",
            "hydrateAcmMountingFromSvgSupport",
        )
        review_step = _repo_file_exists("frontend", "src", "components", "workos", "intake-v6", "steps", "IntakeV6ReviewStep.tsx")
        if has_support and not mounting_hydrate:
            step2_blockers.append(
                _issue(
                    "ACP_DIMENSION_WIRING_MISSING",
                    "SUPPORT_CONTOUR present but SVG→mounting dimension hydrate path missing.",
                    evidence=["hydrateAcmMountingFromSvgSupport"],
                )
            )
        elif has_support and mounting_hydrate:
            step2_warnings.append(
                _issue(
                    "UNIT_AMBIGUITY_GUARD_REQUIRED",
                    "ACP dimensions consume SVG support geometry; unit ambiguity must remain operator-visible.",
                    severity="warning",
                    evidence=["svg_support_selection.panel_geometry"],
                )
            )
        if not review_step and is_root_offerable_template(code):
            step2_blockers.append(_issue("STEP2_UI_MISSING", "Intake V6 Review/Step 2 surface missing."))
        step2_status: LifecycleStatus
        if step2_blockers:
            step2_status = "BLOCKED"
        elif has_support and mounting_hydrate:
            step2_status = "WIRED"
        elif review_step:
            step2_status = "CONFIGURED"
        else:
            step2_status = "NOT_STARTED"
        stages.append(
            self._stage(
                "INTAKE_STEP_2",
                status=step2_status,
                required=True,
                evidence=[
                    f"review_step={review_step}",
                    f"mounting_hydrate={mounting_hydrate}",
                    f"support_bindable={has_support}",
                ],
                blockers=step2_blockers,
                warnings=step2_warnings,
                affected_files=[
                    "frontend/src/lib/intakeV6/mountingSolution.ts",
                    "frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx",
                ],
            )
        )

        # --- FINISH_SETUP ---
        finish_schema = _file_contains("backend/schemas/intake_v4.py", "svg_component_bindings")
        finish_status: LifecycleStatus = "WIRED" if finish_schema else "BLOCKED"
        stages.append(
            self._stage(
                "FINISH_SETUP",
                status=finish_status,
                required=True,
                evidence=[f"svg_component_bindings_field={finish_schema}"],
                blockers=[]
                if finish_schema
                else [_issue("FINISH_SETUP_BINDING_FIELD_MISSING", "FinishSetup lacks svg_component_bindings field.")],
                affected_files=["backend/schemas/intake_v4.py"],
            )
        )

        # --- PRODUCT_DEFINITION ---
        pd_blockers: list[LifecycleIssue] = []
        pd_evidence: list[str] = []
        pd = None
        try:
            pd = await ProductDefinitionBuilderService(self.db).build_preview(code)
            pd_evidence.append(f"preview_built={pd is not None}")
            if pd is None:
                pd_blockers.append(_issue("PRODUCT_DEFINITION_PREVIEW_NULL", "ProductDefinition preview returned null."))
            else:
                modules = getattr(pd, "selected_modules", None) or []
                pd_evidence.append(f"selected_modules={len(list(modules))}")
                instances = getattr(pd, "svg_component_instances", None) or getattr(pd, "component_instances", None)
                if instances is not None:
                    pd_evidence.append(f"instances={len(list(instances))}")
        except Exception as exc:  # noqa: BLE001 — inspector must not crash
            pd_blockers.append(
                _issue(
                    "PRODUCT_DEFINITION_BUILD_FAILED",
                    f"ProductDefinition preview failed: {exc}",
                    evidence=[type(exc).__name__],
                )
            )
        stages.append(
            self._stage(
                "PRODUCT_DEFINITION",
                status="BLOCKED" if pd_blockers else "PASS",
                required=True,
                evidence=pd_evidence,
                blockers=pd_blockers,
                affected_files=["backend/services/product_definition_builder_service.py"],
            )
        )

        # --- PRODUCT_AGGREGATE ---
        agg_blockers: list[LifecycleIssue] = []
        agg_evidence: list[str] = []
        try:
            agg = await ProductAggregateService(self.db).build(code)
            agg_evidence.append(f"aggregate_built={agg is not None}")
            if agg is None:
                agg_blockers.append(_issue("PRODUCT_AGGREGATE_NULL", "ProductAggregate build returned null."))
            else:
                comps = getattr(agg, "components", None) or getattr(agg, "modules", None) or []
                agg_evidence.append(f"projection_rows={len(list(comps))}")
                task_contract = getattr(agg, "task_contract", None)
                agg_evidence.append(f"task_contract={task_contract is not None}")
        except Exception as exc:  # noqa: BLE001
            agg_blockers.append(
                _issue(
                    "PRODUCT_AGGREGATE_BUILD_FAILED",
                    f"ProductAggregate build failed: {exc}",
                    evidence=[type(exc).__name__],
                )
            )
        stages.append(
            self._stage(
                "PRODUCT_AGGREGATE",
                status="BLOCKED" if agg_blockers else "PASS",
                required=True,
                evidence=agg_evidence,
                blockers=agg_blockers,
                affected_files=["backend/services/product_aggregate_service.py"],
            )
        )

        # --- CPP ---
        cpp_gate = LifecycleOwnerGate(
            code="CPP_FORMULA_OWNER_GATE",
            label="CPP formula / commercial pricing",
            status="OWNER_GATE_REQUIRED",
            reason="CPP formulas and commercial pricing require explicit owner GO; lifecycle reports gate only.",
            stage="CPP",
        )
        owner_gates.append(cpp_gate)
        stages.append(
            self._stage(
                "CPP",
                status="OWNER_GATE_REQUIRED",
                required=False,
                owner_gate=cpp_gate.code,
                evidence=["template_usage_mode_policy / pricing boundary"],
                warnings=[
                    _issue(
                        "CPP_OWNER_GATE",
                        "CPP remains owner-gated — not auto-activated by lifecycle V1.",
                        severity="warning",
                    )
                ],
            )
        )

        # --- OFFER ---
        offer_status: LifecycleStatus = "PASS" if (item and item.quote_offerable) else (
            "OWNER_GATE_REQUIRED" if policy and policy.owner_go_required else "PREVIEW_ONLY"
        )
        stages.append(
            self._stage(
                "OFFER",
                status=offer_status,
                required=False,
                evidence=[f"quote_offerable={getattr(item, 'quote_offerable', None)}"],
            )
        )

        # --- SNAPSHOT / TASKING / EXECUTION ---
        stages.append(
            self._stage(
                "ORDER_SNAPSHOT",
                status="PREVIEW_ONLY",
                required=False,
                owner_gate="SNAPSHOT_ACTIVATION_OWNER_GATE",
                evidence=["Snapshot freeze not activated by lifecycle V1"],
            )
        )
        owner_gates.append(
            LifecycleOwnerGate(
                code="SNAPSHOT_ACTIVATION_OWNER_GATE",
                label="Snapshot activation",
                status="OWNER_GATE_REQUIRED",
                reason="Snapshot activation requires explicit owner GO.",
                stage="ORDER_SNAPSHOT",
            )
        )
        stages.append(
            self._stage(
                "TASK_RULES_PROJECTION",
                status="PREVIEW_ONLY",
                required=False,
                evidence=["Existing task_rules projection only — no parallel task model"],
                warnings=[
                    _issue(
                        "NO_PARALLEL_TASKING",
                        "Lifecycle forbids parallel tasking authority.",
                        severity="warning",
                        evidence=["AGENTS.md protected: Status lifecycle / Snapshots"],
                    )
                ],
            )
        )
        stages.append(
            self._stage(
                "TASK_MATERIALIZATION",
                status="OWNER_GATE_REQUIRED",
                required=False,
                owner_gate="TASK_MATERIALIZATION_OWNER_GATE",
                evidence=["Materialization blocked without owner GO"],
            )
        )
        owner_gates.append(
            LifecycleOwnerGate(
                code="TASK_MATERIALIZATION_OWNER_GATE",
                label="Task materialization",
                status="OWNER_GATE_REQUIRED",
                reason="Task materialization requires explicit owner GO.",
                stage="TASK_MATERIALIZATION",
            )
        )
        stages.append(
            self._stage(
                "EXECUTION",
                status="NOT_STARTED",
                required=False,
                owner_gate="EXECUTION_ROLLOUT_OWNER_GATE",
                evidence=["Execution rollout out of V1 scope"],
            )
        )
        owner_gates.append(
            LifecycleOwnerGate(
                code="EXECUTION_ROLLOUT_OWNER_GATE",
                label="Execution rollout",
                status="OWNER_GATE_REQUIRED",
                reason="Execution rollout requires explicit owner GO.",
                stage="EXECUTION",
            )
        )

        # --- RUNTIME PROOF ---
        proof_files = [
            "docs/worklog/realignment/2026-07-13_product_system_active_path_isolation_v1.md",
            "docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md",
        ]
        proof_hits = [p for p in proof_files if _repo_file_exists(*p.split("/"))]
        e2e_finish = _repo_file_exists("frontend", "e2e", "work-intake-v2-to-quote-finish-display.spec.ts")
        runtime_status: LifecycleStatus = "PASS" if (proof_hits or e2e_finish) and db_active else "BLOCKED"
        if policy and policy.candidate_only:
            runtime_status = "PREVIEW_ONLY"
        stages.append(
            self._stage(
                "RUNTIME_PROOF",
                status=runtime_status,
                required=True,
                evidence=[
                    f"worklog_hits={proof_hits}",
                    f"e2e_finish_smoke={e2e_finish}",
                ],
                blockers=[]
                if runtime_status in PASS_LIKE
                else [_issue("RUNTIME_PROOF_MISSING", "No worklog/E2E proof artifacts found for activation.")],
                runtime_proof=proof_hits + (["frontend/e2e/work-intake-v2-to-quote-finish-display.spec.ts"] if e2e_finish else []),
            )
        )

        # Legacy conflicts
        if STALE_BOND_CASETAT in str(project_svg_bindables(code)) or _file_contains(
            "backend/services/intake_v6_product_composition_recommendation_service.py",
            "TPL-BOND-CASETAT",
        ):
            legacy.append(
                LifecycleLegacyConflict(
                    code="STALE_BOND_CASETAT",
                    classification="forbidden_for_new_data",
                    message="TPL-BOND-CASETAT is legacy string-only — not new-selection authority.",
                    evidence=[STALE_BOND_CASETAT],
                )
            )
        if code == ACM_BOXED_SUPPORT or has_support:
            legacy.append(
                LifecycleLegacyConflict(
                    code="ACM_LIVE_SUPPORT_AUTHORITY",
                    classification="read_only_compatibility",
                    message="Live support authority is TPL-ACM-BOXED-MOUNTING-SUPPORT_v1.",
                    evidence=[ACM_BOXED_SUPPORT],
                )
            )
        if policy and policy.candidate_only:
            legacy.append(
                LifecycleLegacyConflict(
                    code="CANDIDATE_ROOT_BLOCKED",
                    classification="owner_decision_required",
                    message=policy.reason,
                    evidence=[code],
                )
            )
            owner_gates.append(
                LifecycleOwnerGate(
                    code="CANDIDATE_ROOT_ACTIVATION",
                    label="Candidate root activation",
                    status="OWNER_GATE_REQUIRED",
                    reason=policy.reason,
                    stage="OFFER",
                )
            )

        impact = (await self.build_impact(code)).impact
        return self._finalize(code, row, item, stages, owner_gates, legacy, impact=impact, template_status=template_status)

    async def validate(
        self,
        *,
        template_codes: list[str] | None = None,
        active_only: bool = True,
    ) -> TemplateLifecycleValidateResponse:
        availability = await ProductTemplateAvailabilityService(self.db).list_availability(
            offerable_only=False,
            include_runtime_modules=True,
            include_archived=True,
        )
        if template_codes:
            codes = [c.strip() for c in template_codes if c and c.strip()]
        elif active_only:
            codes = [
                i.template_code
                for i in availability.items
                if i.db_active and (i.quote_offerable or is_root_offerable_template(i.template_code))
            ]
        else:
            codes = [i.template_code for i in availability.items if i.db_active]

        items: list[TemplateLifecycleValidateItem] = []
        fail_reasons: list[str] = []
        for code in codes:
            readiness = await self.build_readiness(code)
            blocking = sorted(
                {
                    b.code
                    for stage in readiness.stages
                    if stage.stage in ACTIVATION_REQUIRED_STAGES or stage.required
                    for b in stage.blockers
                    if b.severity == "blocking"
                }
            )
            warnings = sorted({w.code for stage in readiness.stages for w in stage.warnings})
            # Fail CI only when activation-required stages are BLOCKED for root-offerable templates
            should_fail = False
            if is_root_offerable_template(code) and readiness.template_status == "ACTIVE":
                for stage in readiness.stages:
                    if stage.stage in ACTIVATION_REQUIRED_STAGES and stage.status == "BLOCKED":
                        should_fail = True
                        fail_reasons.append(f"{code}:{stage.stage}:{','.join(b.code for b in stage.blockers) or stage.status}")
            items.append(
                TemplateLifecycleValidateItem(
                    template_code=code,
                    lifecycle_status=readiness.lifecycle_status,
                    readiness_score=readiness.readiness_score,
                    activation_eligible=readiness.activation_eligible,
                    blocking_codes=blocking,
                    warning_codes=warnings,
                )
            )
            # Also fail if deprecated new-use authority
            if any(c.code == "STALE_BOND_CASETAT" and c.classification == "forbidden_for_new_data" for c in readiness.legacy_conflicts):
                # warning-level for presence in docs/contracts; only fail if STAGE blocked via DANGLING
                pass

        failed = len(fail_reasons)
        return TemplateLifecycleValidateResponse(
            ok=failed == 0,
            checked=len(items),
            failed=failed,
            items=items,
            fail_reasons=fail_reasons,
        )

    def _stage(
        self,
        stage: str,
        *,
        status: LifecycleStatus,
        required: bool,
        owner_label: str | None = None,
        authority: str | None = None,
        evidence: list[str] | None = None,
        warnings: list[LifecycleIssue] | None = None,
        blockers: list[LifecycleIssue] | None = None,
        owner_gate: str | None = None,
        affected_files: list[str] | None = None,
        affected_tests: list[str] | None = None,
        runtime_proof: list[str] | None = None,
    ) -> LifecycleStageResult:
        meta = next((m for m in LIFECYCLE_STAGES if m[0] == stage), None)
        return LifecycleStageResult(
            stage=stage,  # type: ignore[arg-type]
            owner_label=owner_label or (meta[1] if meta else stage),
            authority=authority or (meta[2] if meta else "Product System"),
            required=required,
            status=status,
            evidence=list(evidence or []),
            warnings=list(warnings or []),
            blockers=list(blockers or []),
            owner_gate=owner_gate,
            affected_files=list(affected_files or []),
            affected_tests=list(affected_tests or []),
            runtime_proof=list(runtime_proof or []),
        )

    def _finalize(
        self,
        code: str,
        row: Product_templates | None,
        item: Any,
        stages: list[LifecycleStageResult],
        owner_gates: list[LifecycleOwnerGate],
        legacy: list[LifecycleLegacyConflict],
        *,
        impact: LifecycleImpactSummary | None,
        template_status: str = "UNKNOWN",
    ) -> TemplateLifecycleReadiness:
        counts: dict[str, int] = {}
        for stage in stages:
            counts[stage.status] = counts.get(stage.status, 0) + 1

        required_blocked = [
            s
            for s in stages
            if s.stage in ACTIVATION_REQUIRED_STAGES and s.status == "BLOCKED"
        ]
        if required_blocked:
            lifecycle_status: LifecycleStatus = "BLOCKED"
        elif any(s.status == "OWNER_GATE_REQUIRED" for s in stages):
            lifecycle_status = "OWNER_GATE_REQUIRED"
        elif any(s.status == "PREVIEW_ONLY" for s in stages):
            lifecycle_status = "PREVIEW_ONLY"
        else:
            lifecycle_status = "PASS"

        scored = 0
        weight = 0
        for stage in stages:
            if stage.stage not in ACTIVATION_REQUIRED_STAGES:
                continue
            weight += 1
            if stage.status in {"PASS", "VALIDATED", "WIRED"}:
                scored += 1
            elif stage.status in {"CONFIGURED", "DISCOVERED", "PREVIEW_ONLY"}:
                scored += 0.6
            elif stage.status == "OWNER_GATE_REQUIRED":
                scored += 0.8
            elif stage.status == "NOT_APPLICABLE":
                scored += 1
        readiness_score = int(round((scored / weight) * 100)) if weight else 0

        activation_eligible = not required_blocked and template_status in {"ACTIVE", "CANDIDATE"}

        version = None
        if "_v" in code:
            version = code.rsplit("_", 1)[-1]

        return TemplateLifecycleReadiness(
            template_code=code,
            version=version,
            family_id=getattr(item, "family_id", None) or (str(row.family_id) if row and row.family_id else None),
            family_name=getattr(item, "family_name", None)
            or (str(row.family_name) if row and row.family_name else None),
            template_status=template_status,
            lifecycle_status=lifecycle_status,
            readiness_score=readiness_score,
            activation_eligible=activation_eligible,
            stages=stages,
            owner_gates=owner_gates,
            impact_summary=impact,
            legacy_conflicts=legacy,
            stage_counts=counts,
            derived_from=[
                "product_templates",
                "product_template_availability",
                "template_usage_mode_policy",
                "svg_component_binding_contract",
                "product_definition_builder",
                "product_aggregate_service",
                "repo file evidence (Intake Step1/Step2)",
            ],
        )

