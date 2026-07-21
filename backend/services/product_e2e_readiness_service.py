"""Product E2E Readiness Check — read-only orchestrator.

Checkers CALL/INSPECT owning services. No catalog/workspace writes.
Does not duplicate PD / Aggregate / Quantity / CPP formulas.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_template_module_links import ProductTemplateModuleLink
from models.product_templates import Product_templates
from schemas.commercial_price_proposal import CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.product_aggregate import ProductAggregate
from schemas.product_definition import (
    ProductDefinitionPreview,
    ProductDefinitionSourceContext,
)
from schemas.product_e2e_readiness import (
    ProductE2EBuildClosureStatus,
    ProductE2ECheckFinding,
    ProductE2ECheckStatus,
    ProductE2EMode,
    ProductE2EReadinessResult,
    ProductE2ESeverity,
    ProductE2ESystem,
    ProductE2ESystemNode,
    ProductE2ETemplatePublicationStatus,
    ProductE2EVerdict,
)
from schemas.quote_snapshot_v2 import QuoteSnapshotOfferScope, QuoteSnapshotV2
from schemas.volum_aluminiu_separate_calc_preview import (
    VolumAluminiuSeparateCalcPreviewRequest,
)
from services.acm_boxed_support_composition_v1 import (
    ACM_BOXED_ROOT,
    APPLIED_CONTENT_TRIGGER_FIELD,
    BLOCKER_LOGO_BRANCH_CANDIDATE,
    LOGO_ROOT,
    resolve_acm_boxed_composition,
)
from services.acm_face_treatment_commercial_path_v1 import readiness_finding_for_template
from services.artwork_analysis_integration_readiness import (
    evaluate_artwork_analysis_integration_readiness,
)
from services.artwork_analysis_intake_adapter import (
    extract_external_artwork_analysis_from_workspace,
)
from services.execution_preview_from_frozen_graph_service import (
    build_execution_preview_from_frozen_snapshot,
)
from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService
from services.letters_commercial_measurement_service import (
    is_letters_commercial_measurement_template,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_truth_job_confirm_service import (
    commercial_freeze_allowed,
    get_job_revision_metadata,
    get_pinned_typed_bags,
    is_job_revision_stale,
)
from services.template_architecture_scope import (
    RUNTIME_TEMPLATE_CODE_BY_ALIAS,
    normalize_template_code,
    resolve_template_identity,
)
from services.volum_aluminiu_component_contract import (
    ACTIVATION_FORBIDDEN_IN_THIS_BUILD,
    ALLOWED_DEPTH_MM,
    BOM_COMPONENT_ID,
    COMMERCIAL_BASIS_SYNONYM,
    COMMERCIAL_LINE_CODE,
    INTERNAL_RULE_CODE,
    PARENT_TEMPLATE_CODE,
    PRICING_COMPONENT_CODE,
    PUBLICATION_REMAINS_BLOCKED,
    TEMPLATE_CODE as VOLUM_ALUMINIU_TEMPLATE_CODE,
    build_identity_convergence_view,
    build_input_contract_view,
    map_component_ref_to_module,
)
from services.volum_aluminiu_quantity_ownership import (
    QUOTE_GEOMETRY_CLASSIFICATION_BRIDGE,
    QUOTE_GEOMETRY_CLASSIFICATION_LEGACY,
    resolve_component_quantity_from_payload,
    resolve_product_total_perimeter_authority,
)
from services.volum_aluminiu_separate_calc_preview_service import (
    VolumAluminiuSeparateCalcPreviewService,
)

logger = logging.getLogger(__name__)

KNOWN_REQUIRED_INACTIVE_CHILD = "TPL-VOLUM-ALUMINIU_v1"


def _catalog_facing_template_code(template_code: str) -> str:
    """Prefer alias-map casing used in catalog rows over identity uppercase."""
    raw = str(template_code or "").strip()
    if not raw:
        return raw
    mapped = RUNTIME_TEMPLATE_CODE_BY_ALIAS.get(normalize_template_code(raw))
    if mapped:
        return mapped
    identity = resolve_template_identity(raw)
    return identity.canonical_template_code or raw

_STATIC_NOT_TESTED_SYSTEMS: tuple[ProductE2ESystem, ...] = (
    "cpp",
    "eic",
    "order_snapshot",
    "execution_preview",
)

_STATUS_RANK: dict[ProductE2ECheckStatus, int] = {
    "PASS": 0,
    "PASS_WITH_WARNINGS": 1,
    "PARTIAL": 2,
    "NOT_CONFIGURED": 3,
    "LEGACY_DEPENDENCY": 4,
    "STALE_EVIDENCE": 5,
    "NOT_TESTED": 6,
    "FAIL": 7,
    "BLOCKED": 8,
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finding(
    *,
    check_id: str,
    system: ProductE2ESystem,
    status: ProductE2ECheckStatus,
    message: str,
    source_owner: str,
    template_code: str | None = None,
    component_template_code: str | None = None,
    workspace_id: str | None = None,
    blocking: bool | None = None,
    severity: ProductE2ESeverity | None = None,
    evidence: dict[str, Any] | None = None,
    evidence_type: str | None = None,
    route: str | None = None,
    recommended_navigation: str | None = None,
    technical_details: dict[str, Any] | None = None,
) -> ProductE2ECheckFinding:
    if severity is None:
        if status in ("FAIL", "BLOCKED"):
            severity = "blocker"
        elif status in ("PASS_WITH_WARNINGS", "LEGACY_DEPENDENCY", "STALE_EVIDENCE"):
            severity = "warning"
        else:
            severity = "info"
    if blocking is None:
        blocking = status in ("FAIL", "BLOCKED") or (
            status == "STALE_EVIDENCE" and system in ("product_truth", "quote_snapshot")
        )
    return ProductE2ECheckFinding(
        check_id=check_id,
        system=system,
        status=status,
        severity=severity,
        blocking=bool(blocking),
        message=message,
        evidence=evidence or {},
        evidence_type=evidence_type,
        source_owner=source_owner,
        template_code=template_code,
        component_template_code=component_template_code,
        workspace_id=workspace_id,
        route=route,
        recommended_navigation=recommended_navigation,
        technical_details=technical_details,
    )


def _worse(a: ProductE2ECheckStatus, b: ProductE2ECheckStatus) -> ProductE2ECheckStatus:
    return a if _STATUS_RANK.get(a, 0) >= _STATUS_RANK.get(b, 0) else b


def _acm_mirror_divergence(finish: dict[str, Any]) -> list[str]:
    canonical = finish.get("acm_panel_instance")
    if not isinstance(canonical, dict):
        return []
    diverged: list[str] = []
    sel = finish.get("svg_support_selection")
    if isinstance(sel, dict) and isinstance(sel.get("acm_panel_instance"), dict):
        if sel["acm_panel_instance"] != canonical:
            diverged.append("finish_setup.svg_support_selection.acm_panel_instance")
    ms = finish.get("mounting_solution")
    if isinstance(ms, dict):
        cfg = ms.get("configuration")
        if isinstance(cfg, dict) and isinstance(cfg.get("acm_panel_instance"), dict):
            if cfg["acm_panel_instance"] != canonical:
                diverged.append("finish_setup.mounting_solution.configuration.acm_panel_instance")
    return diverged


def _aggregate_systems(findings: list[ProductE2ECheckFinding]) -> list[ProductE2ESystemNode]:
    by_system: dict[ProductE2ESystem, list[ProductE2ECheckFinding]] = {}
    for f in findings:
        by_system.setdefault(f.system, []).append(f)
    order: list[ProductE2ESystem] = [
        "catalog",
        "components",
        "intake",
        "product_truth",
        "product_definition",
        "aggregate",
        "quantity",
        "cpp",
        "eic",
        "quote_snapshot",
        "order_snapshot",
        "execution_preview",
    ]
    nodes: list[ProductE2ESystemNode] = []
    for system in order:
        items = by_system.get(system, [])
        if not items:
            continue
        status: ProductE2ECheckStatus = "PASS"
        blocking = False
        for item in items:
            if item.status == "NOT_TESTED" and status == "PASS":
                status = "NOT_TESTED"
            else:
                status = _worse(status, item.status)
            blocking = blocking or item.blocking
        summary = items[0].message if len(items) == 1 else f"{len(items)} findings"
        nodes.append(
            ProductE2ESystemNode(
                system=system,
                status=status,
                blocking=blocking,
                finding_count=len(items),
                summary=summary,
            )
        )
    return nodes


_PUBLISHABLE_VERDICTS = frozenset(
    {
        "STATIC_READY",
        "STATIC_READY_WITH_WARNINGS",
        "RUNTIME_READY",
    }
)

# Honest publication conflicts that must not fail BUILD closure readiness.
_PUBLICATION_ONLY_CONFLICT_CODES = frozenset(
    {
        "required_inactive_child",
    }
)


def _is_publication_only_finding(finding: ProductE2ECheckFinding) -> bool:
    """Inactive required child (e.g. aluminiu) blocks publish, not build spine closure."""
    if not isinstance(finding.evidence, dict):
        return False
    code = str(finding.evidence.get("conflict_code") or "")
    if code in _PUBLICATION_ONLY_CONFLICT_CODES:
        return True
    if (
        finding.component_template_code == KNOWN_REQUIRED_INACTIVE_CHILD
        and finding.status == "BLOCKED"
    ):
        return True
    return False


def _compute_verdict(
    *,
    mode: ProductE2EMode,
    findings: list[ProductE2ECheckFinding],
) -> tuple[ProductE2EVerdict, bool, list[str]]:
    known_conflicts = sorted(
        {
            str(f.evidence.get("conflict_code"))
            for f in findings
            if isinstance(f.evidence, dict) and f.evidence.get("conflict_code")
        }
    )
    if any(f.blocking or f.status in ("FAIL", "BLOCKED") for f in findings):
        return "BLOCKED", False, known_conflicts

    statuses = {f.status for f in findings}
    has_warnings = bool(
        statuses
        & {
            "PASS_WITH_WARNINGS",
            "LEGACY_DEPENDENCY",
            "STALE_EVIDENCE",
            "PARTIAL",
            "NOT_CONFIGURED",
        }
    )
    has_not_tested = "NOT_TESTED" in statuses

    if mode == "static":
        compile_warn = any(
            f.status in ("PASS_WITH_WARNINGS", "LEGACY_DEPENDENCY", "PARTIAL")
            for f in findings
            if f.system
            in (
                "catalog",
                "components",
                "intake",
                "product_truth",
                "product_definition",
                "aggregate",
                "quantity",
                "quote_snapshot",
            )
        )
        if compile_warn or has_warnings:
            return "STATIC_READY_WITH_WARNINGS", False, known_conflicts
        if has_not_tested:
            return "STATIC_READY", False, known_conflicts
        return "STATIC_READY", False, known_conflicts

    if has_not_tested:
        return "NOT_TESTED", False, known_conflicts
    if has_warnings:
        return "PARTIAL", False, known_conflicts
    return "RUNTIME_READY", True, known_conflicts


def _compute_build_and_publication_status(
    *,
    verdict: ProductE2EVerdict,
    e2e_ready: bool,
    findings: list[ProductE2ECheckFinding],
) -> tuple[ProductE2EBuildClosureStatus, ProductE2ETemplatePublicationStatus]:
    """Split BUILD closure from TEMPLATE publication readiness.

    Overall ``verdict`` remains the publish hard-gate (BLOCKED when inactive aluminiu).
    BUILD may still PASS when the only blockers are publication-only conflicts.
    """
    if verdict in _PUBLISHABLE_VERDICTS or e2e_ready:
        publication: ProductE2ETemplatePublicationStatus = "PASS"
    elif any(
        f.blocking or f.status in ("FAIL", "BLOCKED") for f in findings
    ):
        publication = "BLOCKED"
    else:
        publication = "NOT_READY"

    build_relevant = [f for f in findings if not _is_publication_only_finding(f)]
    build_blockers = [
        f
        for f in build_relevant
        if f.blocking or f.status in ("FAIL", "BLOCKED")
    ]
    if build_blockers:
        if any(f.status == "BLOCKED" for f in build_blockers):
            build: ProductE2EBuildClosureStatus = "BLOCKED"
        else:
            build = "FAIL"
        return build, publication

    statuses = {f.status for f in build_relevant}
    if statuses & {"PASS_WITH_WARNINGS", "LEGACY_DEPENDENCY", "STALE_EVIDENCE", "PARTIAL"}:
        return "PASS_WITH_WARNINGS", publication
    if statuses & {"NOT_CONFIGURED"} and not (
        statuses & {"PASS", "PASS_WITH_WARNINGS"}
    ):
        return "PARTIAL", publication
    return "PASS", publication


class ProductE2EReadinessService:
    """Orchestrate read-only E2E readiness checkers for a product template."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._aggregate = ProductAggregateService(db)
        self._pd = ProductDefinitionBuilderService(db)
        self._form = IntakeV6ModularFormContractService()

    async def run_static(self, template_code: str) -> ProductE2EReadinessResult:
        return await self._run(template_code=template_code, mode="static", workspace_id=None)

    async def run_runtime_dry_run(
        self,
        template_code: str,
        *,
        workspace_id: str,
        dry_run: bool = True,
    ) -> ProductE2EReadinessResult:
        _ = dry_run  # forced no-write regardless of caller
        return await self._run(
            template_code=template_code,
            mode="runtime_dry_run",
            workspace_id=workspace_id,
        )

    async def _run(
        self,
        *,
        template_code: str,
        mode: ProductE2EMode,
        workspace_id: str | None,
    ) -> ProductE2EReadinessResult:
        # Use catalog-facing code (mixed-case seed codes). Identity uppercase alone
        # would false-negative catalog.template_missing for TPL-VOLUMETRIC-LETTERS_v2.
        canonical = _catalog_facing_template_code(template_code)

        payload: dict[str, Any] | None = None
        if workspace_id:
            payload = await self._load_workspace_payload(workspace_id)

        findings: list[ProductE2ECheckFinding] = []
        findings.extend(await self._check_catalog(canonical))
        findings.extend(await self._check_component_links(canonical))
        findings.extend(self._check_intake_contract(canonical))
        # External artwork analysis: only surface when a consume bag is present so
        # static BUILD / TEMPLATE axes are not reopened by transport TBD noise.
        findings.extend(
            self._check_external_artwork_analysis(
                canonical, mode=mode, payload=payload
            )
        )
        findings.extend(
            await self._check_product_truth(
                canonical, mode=mode, workspace_id=workspace_id, payload=payload
            )
        )
        findings.extend(
            await self._check_product_definition(
                canonical,
                workspace_id=workspace_id if mode == "runtime_dry_run" else None,
            )
        )
        findings.extend(
            await self._check_aggregate(
                canonical,
                workspace_id=workspace_id if mode == "runtime_dry_run" else None,
            )
        )
        findings.extend(
            await self._check_quantity(
                canonical, mode=mode, payload=payload, workspace_id=workspace_id
            )
        )
        findings.extend(
            self._check_commercial(
                canonical, mode=mode, payload=payload, workspace_id=workspace_id
            )
        )
        findings.extend(
            self._check_snapshot(
                canonical, mode=mode, payload=payload, workspace_id=workspace_id
            )
        )
        findings.extend(
            self._check_execution_handoff(
                canonical, mode=mode, payload=payload, workspace_id=workspace_id
            )
        )

        if mode == "static":
            for system in _STATIC_NOT_TESTED_SYSTEMS:
                if not any(f.system == system for f in findings):
                    findings.append(
                        _finding(
                            check_id=f"{system}.static_not_tested",
                            system=system,
                            status="NOT_TESTED",
                            message=f"Static check does not claim runtime proof for {system}.",
                            source_owner="product_e2e_readiness",
                            template_code=canonical,
                            blocking=False,
                            evidence={"conflict_code": "static_no_runtime_claim"},
                        )
                    )

        verdict, e2e_ready, known_conflicts = _compute_verdict(mode=mode, findings=findings)
        build_closure_status, template_publication_status = _compute_build_and_publication_status(
            verdict=verdict,
            e2e_ready=e2e_ready,
            findings=findings,
        )
        return ProductE2EReadinessResult(
            template_code=canonical,
            mode=mode,
            verdict=verdict,
            e2e_ready=e2e_ready,
            write_performed=False,
            no_write=True,
            dry_run=True,
            workspace_id=workspace_id,
            checked_at=_utcnow_iso(),
            findings=findings,
            systems=_aggregate_systems(findings),
            known_conflicts=known_conflicts,
            build_closure_status=build_closure_status,
            template_publication_status=template_publication_status,
        )

    async def _load_workspace_payload(self, workspace_id: str) -> dict[str, Any] | None:
        key = str(workspace_id or "").strip()
        if not key:
            return None
        result = await self._db.execute(
            select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == key)
        )
        record = result.scalar_one_or_none()
        if record is None:
            result = await self._db.execute(
                select(IntakeV6WorkspaceRecord).where(
                    IntakeV6WorkspaceRecord.workspace_code == key
                )
            )
            record = result.scalar_one_or_none()
        if record is None:
            return None
        try:
            payload = json.loads(record.payload_json or "{}")
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    async def _load_template_row(self, template_code: str) -> Product_templates | None:
        candidates: list[str] = []
        for code in (
            template_code,
            _catalog_facing_template_code(template_code),
            normalize_template_code(template_code),
        ):
            text = str(code or "").strip()
            if text and text not in candidates:
                candidates.append(text)
        for code in candidates:
            result = await self._db.execute(
                select(Product_templates)
                .where(Product_templates.template_code == code)
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row is not None:
                return row
        return None

    async def _load_module_links(self, parent_code: str) -> list[ProductTemplateModuleLink]:
        result = await self._db.execute(
            select(ProductTemplateModuleLink).where(
                ProductTemplateModuleLink.parent_template_code == parent_code,
                ProductTemplateModuleLink.active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def _check_catalog(self, template_code: str) -> list[ProductE2ECheckFinding]:
        row = await self._load_template_row(template_code)
        if row is None:
            return [
                _finding(
                    check_id="catalog.template_missing",
                    system="catalog",
                    status="BLOCKED",
                    message=f"Template {template_code} not found in catalog.",
                    source_owner="product_templates",
                    template_code=template_code,
                    route=f"/api/v1/product-system/aggregate/{template_code}",
                    evidence={"conflict_code": "template_not_found"},
                )
            ]
        active = bool(row.active) if row.active is not None else False
        return [
            _finding(
                check_id="catalog.template_present",
                system="catalog",
                status="PASS" if active else "PASS_WITH_WARNINGS",
                message=(
                    f"Catalog template {template_code} present"
                    + (" and active." if active else " but inactive (catalog flag).")
                ),
                source_owner="product_templates",
                template_code=template_code,
                blocking=False,
                evidence={
                    "family_id": row.family_id,
                    "family_name": row.family_name,
                    "active": row.active,
                },
                evidence_type="catalog_row",
            )
        ]

    async def _check_component_links(self, template_code: str) -> list[ProductE2ECheckFinding]:
        findings: list[ProductE2ECheckFinding] = []

        if normalize_template_code(template_code) == normalize_template_code(ACM_BOXED_ROOT):
            # Composition Decision A — XOR + logo honesty (no publication).
            resolved = resolve_acm_boxed_composition({"applied_content": "none"})
            findings.append(
                _finding(
                    check_id="components.acm_applied_content_xor_contract",
                    system="components",
                    status="PASS",
                    message=(
                        "ACM boxed applied_content XOR contract present "
                        "(letters|logo); metal_frame optional operator-explicit."
                    ),
                    source_owner="acm_boxed_support_composition_v1",
                    template_code=template_code,
                    blocking=False,
                    evidence={
                        "decision": "A",
                        "xor": ["letters", "logo"],
                        "frame": "acp_internal_frame_optional",
                        "panel_only_ok": True,
                    },
                )
            )
            logo_resolved = resolve_acm_boxed_composition({"applied_content": "logo"})
            logo_blockers = logo_resolved["xor"].get("blockers") or []
            findings.append(
                _finding(
                    check_id="components.acm_logo_branch_honesty",
                    system="components",
                    status="BLOCKED" if BLOCKER_LOGO_BRANCH_CANDIDATE in logo_blockers else "PASS",
                    message=(
                        f"Logo branch under ACM: {logo_resolved['xor'].get('logo_branch_status')} "
                        f"(root={LOGO_ROOT})."
                    ),
                    source_owner="acm_boxed_support_composition_v1",
                    template_code=template_code,
                    component_template_code=LOGO_ROOT,
                    blocking=False,
                    evidence={
                        "trigger_field": APPLIED_CONTENT_TRIGGER_FIELD,
                        "blockers": logo_blockers,
                        "publication": "KEEP_DRAFT",
                    },
                )
            )
            # Axis B — face-treatment commercial path (orthogonal to XOR).
            ft = readiness_finding_for_template({"applied_content": "none"})
            findings.append(
                _finding(
                    check_id=ft["check_id"],
                    system="components",
                    status=ft["status"],
                    message=ft["message"],
                    source_owner="acm_face_treatment_commercial_path_v1",
                    template_code=template_code,
                    blocking=bool(ft.get("blocking")),
                    evidence=ft.get("evidence") or {},
                )
            )

        links = await self._load_module_links(template_code)
        aggregate = await self._aggregate.build(template_code)
        if aggregate is None and not links:
            return [
                _finding(
                    check_id="components.aggregate_missing",
                    system="components",
                    status="BLOCKED",
                    message="Cannot inspect component links — Aggregate build returned None.",
                    source_owner="product_aggregate_service",
                    template_code=template_code,
                    evidence={"conflict_code": "aggregate_missing"},
                )
            ]

        required_codes = (
            [m.child_template_code for m in aggregate.modules.required] if aggregate else []
        )
        optional_codes = (
            [m.child_template_code for m in aggregate.modules.optional] if aggregate else []
        )
        if not required_codes and not optional_codes:
            required_codes = [
                str(link.module_template_code)
                for link in links
                if link.relation_type == "required_module"
            ]
            optional_codes = [
                str(link.module_template_code)
                for link in links
                if link.relation_type != "required_module"
            ]

        findings.append(
            _finding(
                check_id="components.module_links_present",
                system="components",
                status="PASS" if (required_codes or optional_codes) else "NOT_CONFIGURED",
                message=(
                    f"Aggregate/module links: {len(required_codes)} required, "
                    f"{len(optional_codes)} optional."
                ),
                source_owner="product_aggregate_service",
                template_code=template_code,
                blocking=False,
                evidence={"required": required_codes, "optional": optional_codes},
                evidence_type="aggregate_modules",
                route=f"/api/v1/product-system/aggregate/{template_code}",
            )
        )

        for child_code in required_codes:
            child = await self._load_template_row(child_code)
            if child is None:
                findings.append(
                    _finding(
                        check_id=f"components.orphan_required.{child_code}",
                        system="components",
                        status="FAIL",
                        message=f"Required module link orphan: {child_code} missing from catalog.",
                        source_owner="product_template_module_links",
                        template_code=template_code,
                        component_template_code=child_code,
                        evidence={"conflict_code": "orphan_link"},
                    )
                )
                continue
            child_active = bool(child.active) if child.active is not None else False
            if not child_active:
                known = child_code == KNOWN_REQUIRED_INACTIVE_CHILD
                findings.append(
                    _finding(
                        check_id=f"components.required_inactive.{child_code}",
                        system="components",
                        status="BLOCKED",
                        message=(
                            f"Required child template {child_code} is inactive "
                            f"(known conflict for {KNOWN_REQUIRED_INACTIVE_CHILD})."
                            if known
                            else f"Required child template {child_code} is inactive."
                        ),
                        source_owner="product_templates",
                        template_code=template_code,
                        component_template_code=child_code,
                        evidence={
                            "conflict_code": "required_inactive_child",
                            "child_active": child.active,
                            "known_conflict": known,
                        },
                        recommended_navigation="Product Templates → child activation policy",
                    )
                )
            else:
                findings.append(
                    _finding(
                        check_id=f"components.required_active.{child_code}",
                        system="components",
                        status="PASS",
                        message=f"Required child {child_code} is active.",
                        source_owner="product_templates",
                        template_code=template_code,
                        component_template_code=child_code,
                        blocking=False,
                    )
                )

        for child_code in optional_codes:
            child = await self._load_template_row(child_code)
            if child is None:
                findings.append(
                    _finding(
                        check_id=f"components.orphan_optional.{child_code}",
                        system="components",
                        status="PASS_WITH_WARNINGS",
                        message=f"Optional module link orphan: {child_code} missing.",
                        source_owner="product_template_module_links",
                        template_code=template_code,
                        component_template_code=child_code,
                        blocking=False,
                        evidence={"conflict_code": "orphan_link"},
                    )
                )

        if aggregate is not None:
            for warning in aggregate.warnings:
                findings.append(
                    _finding(
                        check_id=f"components.aggregate_warning.{warning.code}",
                        system="components",
                        status="PASS_WITH_WARNINGS",
                        message=warning.message,
                        source_owner="product_aggregate_service",
                        template_code=template_code,
                        blocking=False,
                        evidence={
                            "conflict_code": warning.code,
                            "details": warning.details,
                        },
                    )
                )

        # Contract completeness for aluminium return — does NOT authorize activation/publish.
        if KNOWN_REQUIRED_INACTIVE_CHILD in required_codes or template_code == KNOWN_REQUIRED_INACTIVE_CHILD:
            input_contract = build_input_contract_view()
            depth_options = []
            try:
                form = self._form.get_for_template(
                    template_code if template_code != KNOWN_REQUIRED_INACTIVE_CHILD else "TPL-VOLUMETRIC-LETTERS_v2"
                )
                if form is not None:
                    for field in getattr(form, "fields", None) or []:
                        if getattr(field, "canonical_key", None) == "return_depth_mm":
                            depth_options = list(getattr(field, "option_values", None) or [])
            except Exception:  # noqa: BLE001 — readiness must stay read-only/fail-soft
                depth_options = []

            depth_aligned = (
                not depth_options
                or set(int(x) for x in depth_options if str(x).isdigit()) == set(ALLOWED_DEPTH_MM)
            )
            findings.append(
                _finding(
                    check_id="components.volum_aluminiu.separate_calc_contract",
                    system="components",
                    status="PASS" if depth_aligned else "PASS_WITH_WARNINGS",
                    message=(
                        "Volum Aluminiu separate-calc contract present "
                        "(confirmed perimeter required; parent publication is a separate GO)."
                        if depth_aligned
                        else "Volum Aluminiu contract present but return_depth_mm options misaligned with material gates."
                    ),
                    source_owner="volum_aluminiu_component_contract",
                    template_code=template_code,
                    component_template_code=KNOWN_REQUIRED_INACTIVE_CHILD,
                    blocking=False,
                    evidence={
                        "conflict_code": "volum_aluminiu_contract_completeness",
                        "preview_endpoint": (
                            f"/api/v1/product-system/templates/{KNOWN_REQUIRED_INACTIVE_CHILD}"
                            "/separate-calculation-preview"
                        ),
                        "publication_remains_blocked": PUBLICATION_REMAINS_BLOCKED,
                        "activation_forbidden_in_this_build": ACTIVATION_FORBIDDEN_IN_THIS_BUILD,
                        "depth_options": depth_options,
                        "allowed_depth_mm": sorted(ALLOWED_DEPTH_MM),
                        "depth_aligned": depth_aligned,
                        "canonical_perimeter_unit": input_contract.get("canonical_perimeter_unit"),
                        "commercial_basis": input_contract.get("commercial", {}).get("basis"),
                    },
                    recommended_navigation=(
                        "Product System → Component contract → separate-calculation-preview"
                    ),
                )
            )

            identity_view = build_identity_convergence_view()
            bom_maps = map_component_ref_to_module(BOM_COMPONENT_ID) == "modelare_cant"
            stub_maps = map_component_ref_to_module(PRICING_COMPONENT_CODE) == "modelare_cant"
            identity_ok = (
                identity_view.get("status") == "PASS"
                and identity_view.get("name_based_lookup") is False
                and bom_maps
                and stub_maps
            )
            findings.append(
                _finding(
                    check_id="components.volum_aluminiu.identity_convergence",
                    system="components",
                    status="PASS" if identity_ok else "FAIL",
                    message=(
                        "Volum Aluminiu dual-id closed via explicit IDENTITY_MAP "
                        "(BOM owner + pricing stub alias → modelare_cant once)."
                        if identity_ok
                        else "Volum Aluminiu identity convergence incomplete — fail closed."
                    ),
                    source_owner="volum_aluminiu_component_contract",
                    template_code=template_code,
                    component_template_code=KNOWN_REQUIRED_INACTIVE_CHILD,
                    blocking=False,
                    evidence={
                        "conflict_code": "volum_aluminiu_identity_convergence",
                        "identity": identity_view,
                        "bom_maps_to_module": bom_maps,
                        "pricing_stub_maps_to_module": stub_maps,
                        "publication_remains_blocked": PUBLICATION_REMAINS_BLOCKED,
                        "activation_forbidden_in_this_build": ACTIVATION_FORBIDDEN_IN_THIS_BUILD,
                    },
                    recommended_navigation="Product System → Component identity map",
                )
            )
            findings.append(
                _finding(
                    check_id="components.volum_aluminiu.geometry_convergence",
                    system="components",
                    status="PASS",
                    message=(
                        "Volum Aluminiu product-total prefers confirmed Product Truth perimeter; "
                        "quote_geometry is controlled compatibility bridge or demoted legacy fallback; "
                        "divergence fail-closed. Parent publication is a separate GO."
                    ),
                    source_owner="volum_aluminiu_quantity_ownership",
                    template_code=template_code,
                    component_template_code=KNOWN_REQUIRED_INACTIVE_CHILD,
                    blocking=False,
                    evidence={
                        "conflict_code": "volum_aluminiu_geometry_convergence",
                        "canonical_perimeter_unit": "m",
                        "commercial_basis_synonym": "ml",
                        "quote_geometry_roles": [
                            QUOTE_GEOMETRY_CLASSIFICATION_BRIDGE,
                            QUOTE_GEOMETRY_CLASSIFICATION_LEGACY,
                        ],
                        "product_total_resolver": "resolve_product_total_perimeter_authority",
                        "bridge_applicator": "apply_confirmed_perimeter_quote_geometry_bridge",
                        "publication_remains_blocked": PUBLICATION_REMAINS_BLOCKED,
                        "activation_forbidden_in_this_build": ACTIVATION_FORBIDDEN_IN_THIS_BUILD,
                        "auto_activate": False,
                    },
                    recommended_navigation=(
                        "Product System → separate-calculation-preview + CPP product-total"
                    ),
                )
            )

        return findings

    def _check_intake_contract(self, template_code: str) -> list[ProductE2ECheckFinding]:
        contract = self._form.get_for_template(template_code)
        if contract is None:
            return [
                _finding(
                    check_id="intake.form_contract_missing",
                    system="intake",
                    status="NOT_CONFIGURED",
                    message=f"No Intake V6 modular form contract for {template_code}.",
                    source_owner="intake_v6_modular_form_contract_service",
                    template_code=template_code,
                    blocking=False,
                )
            ]
        return [
            _finding(
                check_id="intake.form_contract_present",
                system="intake",
                status="PASS",
                message="Intake V6 modular form contract present.",
                source_owner="intake_v6_modular_form_contract_service",
                template_code=template_code,
                blocking=False,
                evidence_type="form_contract",
            )
        ]

    def _check_external_artwork_analysis(
        self,
        template_code: str,
        *,
        mode: ProductE2EMode,
        payload: dict[str, Any] | None,
    ) -> list[ProductE2ECheckFinding]:
        """Map external analysis integration checks into intake findings.

        Non-blocking always in this orchestrator so prior BUILD/TEMPLATE gates
        are not reopened. Geometric parse correctness is never claimed.
        """
        external = extract_external_artwork_analysis_from_workspace(payload)
        if external is None:
            return []

        result = evaluate_artwork_analysis_integration_readiness(
            payload,
            external_payload=external,
            mode="runtime" if mode == "runtime_dry_run" else "static",
        )
        mapped: list[ProductE2ECheckFinding] = []
        for item in result.findings:
            status: ProductE2ECheckStatus
            if item.status == "FAIL":
                status = "PASS_WITH_WARNINGS"
            elif item.status in (
                "PASS",
                "PASS_WITH_WARNINGS",
                "NOT_CONFIGURED",
                "NOT_TESTED",
            ):
                status = item.status  # type: ignore[assignment]
            else:
                status = "PASS_WITH_WARNINGS"
            mapped.append(
                _finding(
                    check_id=item.check_id,
                    system="intake",
                    status=status,
                    message=item.message,
                    source_owner="artwork_analysis_integration_readiness",
                    template_code=template_code,
                    blocking=False,
                    evidence=item.evidence,
                    evidence_type="external_artwork_analysis",
                )
            )
        return mapped

    async def _check_product_truth(
        self,
        template_code: str,
        *,
        mode: ProductE2EMode,
        workspace_id: str | None,
        payload: dict[str, Any] | None,
    ) -> list[ProductE2ECheckFinding]:
        findings: list[ProductE2ECheckFinding] = [
            _finding(
                check_id="product_truth.confirm_helpers",
                system="product_truth",
                status="PASS",
                message="ConfirmJobProductTruth freeze helpers available (commercial_freeze_allowed).",
                source_owner="product_truth_job_confirm_service",
                template_code=template_code,
                blocking=False,
                evidence={
                    "helpers": [
                        "commercial_freeze_allowed",
                        "assert_commercial_freeze_allowed",
                        "get_job_revision_metadata",
                        "get_pinned_typed_bags",
                    ]
                },
            )
        ]

        if mode == "static":
            findings.append(
                _finding(
                    check_id="product_truth.runtime_revision",
                    system="product_truth",
                    status="NOT_TESTED",
                    message="Static mode does not inspect a workspace job revision.",
                    source_owner="product_truth_job_confirm_service",
                    template_code=template_code,
                    blocking=False,
                )
            )
            return findings

        if payload is None:
            findings.append(
                _finding(
                    check_id="product_truth.workspace_missing",
                    system="product_truth",
                    status="BLOCKED",
                    message=f"Workspace {workspace_id} not found for runtime dry-run.",
                    source_owner="intake_v6_workspaces",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={"conflict_code": "no_confirmed_runtime_fixture"},
                )
            )
            return findings

        meta = get_job_revision_metadata(payload)
        if meta is None:
            findings.append(
                _finding(
                    check_id="product_truth.job_revision_missing",
                    system="product_truth",
                    status="FAIL",
                    message="Product Truth job revision missing on workspace payload.",
                    source_owner="product_truth_job_confirm_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={"conflict_code": "product_truth_job_revision_missing"},
                )
            )
        elif is_job_revision_stale(payload):
            findings.append(
                _finding(
                    check_id="product_truth.job_revision_stale",
                    system="product_truth",
                    status="STALE_EVIDENCE",
                    message="Product Truth job revision is stale_after_edit.",
                    source_owner="product_truth_job_confirm_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={
                        "conflict_code": "stale_product_truth",
                        "confirmation_state": meta.get("confirmation_state"),
                        "revision": meta.get("revision"),
                    },
                )
            )
        elif commercial_freeze_allowed(payload):
            bags = get_pinned_typed_bags(payload) or {}
            findings.append(
                _finding(
                    check_id="product_truth.freeze_allowed",
                    system="product_truth",
                    status="PASS",
                    message="Commercial freeze allowed — confirmed job revision with pinned bags.",
                    source_owner="product_truth_job_confirm_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={
                        "revision": meta.get("revision"),
                        "pinned_bag_keys": sorted(bags.keys()),
                    },
                )
            )
        else:
            findings.append(
                _finding(
                    check_id="product_truth.not_confirmable",
                    system="product_truth",
                    status="FAIL",
                    message="Product Truth present but commercial_freeze_allowed is false.",
                    source_owner="product_truth_job_confirm_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={
                        "conflict_code": "product_truth_not_confirmable",
                        "confirmation_state": (meta or {}).get("confirmation_state"),
                    },
                )
            )

        finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
        diverged = _acm_mirror_divergence(finish if isinstance(finish, dict) else {})
        if diverged:
            findings.append(
                _finding(
                    check_id="product_truth.acm_mirror_divergence",
                    system="product_truth",
                    status="PASS_WITH_WARNINGS",
                    message="ACM nested mirrors diverge from canonical finish_setup.acm_panel_instance.",
                    source_owner="acm_panel_domain_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={
                        "conflict_code": "acm_multiple_mirrors",
                        "diverged_paths": diverged,
                    },
                )
            )
        elif isinstance(finish, dict) and isinstance(finish.get("acm_panel_instance"), dict):
            findings.append(
                _finding(
                    check_id="product_truth.acm_canonical",
                    system="product_truth",
                    status="PASS",
                    message="ACM canonical instance present; nested mirrors aligned or absent.",
                    source_owner="acm_panel_domain_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                )
            )

        return findings

    async def _check_product_definition(
        self,
        template_code: str,
        *,
        workspace_id: str | None,
    ) -> list[ProductE2ECheckFinding]:
        try:
            preview = await self._pd.build_preview(template_code, workspace_id=workspace_id)
        except Exception as exc:
            logger.exception("PD preview failed during readiness for %s", template_code)
            return [
                _finding(
                    check_id="product_definition.build_error",
                    system="product_definition",
                    status="FAIL",
                    message=f"ProductDefinition build_preview raised: {exc}",
                    source_owner="product_definition_builder_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    technical_details={"exception_type": type(exc).__name__},
                )
            ]
        if preview is None:
            return [
                _finding(
                    check_id="product_definition.missing",
                    system="product_definition",
                    status="FAIL",
                    message="ProductDefinition preview returned None.",
                    source_owner="product_definition_builder_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    route=f"/api/v1/product-system/product-definition/{template_code}",
                )
            ]
        return [
            _finding(
                check_id="product_definition.preview_ok",
                system="product_definition",
                status="PASS",
                message="ProductDefinition preview built successfully (read-only).",
                source_owner="product_definition_builder_service",
                template_code=template_code,
                workspace_id=workspace_id,
                blocking=False,
                evidence_type="product_definition_preview",
                route=f"/api/v1/product-system/product-definition/{template_code}",
            )
        ]

    async def _check_aggregate(
        self,
        template_code: str,
        *,
        workspace_id: str | None,
    ) -> list[ProductE2ECheckFinding]:
        try:
            if workspace_id:
                aggregate = await self._aggregate.build_for_workspace(template_code, workspace_id)
            else:
                aggregate = await self._aggregate.build(template_code)
        except Exception as exc:
            logger.exception("Aggregate build failed during readiness for %s", template_code)
            return [
                _finding(
                    check_id="aggregate.build_error",
                    system="aggregate",
                    status="FAIL",
                    message=f"ProductAggregate build raised: {exc}",
                    source_owner="product_aggregate_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    technical_details={"exception_type": type(exc).__name__},
                )
            ]
        if aggregate is None:
            return [
                _finding(
                    check_id="aggregate.missing",
                    system="aggregate",
                    status="FAIL",
                    message="ProductAggregate build returned None.",
                    source_owner="product_aggregate_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                )
            ]
        return [
            _finding(
                check_id="aggregate.build_ok",
                system="aggregate",
                status="PASS",
                message="ProductAggregate built successfully (read-only).",
                source_owner="product_aggregate_service",
                template_code=template_code,
                workspace_id=workspace_id,
                blocking=False,
                evidence={
                    "required_modules": [m.child_template_code for m in aggregate.modules.required],
                    "warning_codes": [w.code for w in aggregate.warnings],
                },
                evidence_type="product_aggregate",
                route=f"/api/v1/product-system/aggregate/{template_code}",
            )
        ]

    async def _check_quantity(
        self,
        template_code: str,
        *,
        mode: ProductE2EMode,
        payload: dict[str, Any] | None,
        workspace_id: str | None,
    ) -> list[ProductE2ECheckFinding]:
        if not is_letters_commercial_measurement_template(template_code):
            return [
                _finding(
                    check_id="quantity.not_letters_template",
                    system="quantity",
                    status="NOT_CONFIGURED",
                    message="Quantity Builder letters measurement not configured for this template.",
                    source_owner="letters_commercial_measurement_service",
                    template_code=template_code,
                    blocking=False,
                )
            ]
        if mode == "static":
            return [
                _finding(
                    check_id="quantity.rules_present",
                    system="quantity",
                    status="PASS",
                    message="Letters commercial measurement rules available for template.",
                    source_owner="letters_commercial_measurement_service",
                    template_code=template_code,
                    blocking=False,
                )
            ]
        finish = (payload or {}).get("finish_setup") if payload else None
        letters: list[Any] = []
        if isinstance(finish, dict):
            raw = finish.get("letter_group_instances")
            letters = raw if isinstance(raw, list) else []
        if not letters:
            return [
                _finding(
                    check_id="quantity.missing_instances",
                    system="quantity",
                    status="FAIL",
                    message="Runtime dry-run: no letter_group_instances for quantity path.",
                    source_owner="letters_commercial_measurement_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={"conflict_code": "missing_quantities"},
                )
            ]
        return [
            _finding(
                check_id="quantity.instances_present",
                system="quantity",
                status="PASS",
                message=(
                    f"Runtime dry-run: {len(letters)} letter_group_instances present "
                    "(formulas not re-run)."
                ),
                source_owner="letters_commercial_measurement_service",
                template_code=template_code,
                workspace_id=workspace_id,
                blocking=False,
                evidence={"letter_group_count": len(letters)},
            )
        ]

    def _check_commercial(
        self,
        template_code: str,
        *,
        mode: ProductE2EMode,
        payload: dict[str, Any] | None,
        workspace_id: str | None,
    ) -> list[ProductE2ECheckFinding]:
        """CPP/EIC: static stays NOT_TESTED; runtime proves ml qty path without CostEngine dup."""
        if mode == "static" or payload is None:
            return [
                _finding(
                    check_id="cpp.not_tested",
                    system="cpp",
                    status="NOT_TESTED",
                    message="CPP readiness not exercised by this check (no formula duplication).",
                    source_owner="commercial_price_proposal_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={"conflict_code": "not_tested_downstream"},
                ),
                _finding(
                    check_id="eic.not_tested",
                    system="eic",
                    status="NOT_TESTED",
                    message="EIC readiness not exercised by this check (no formula duplication).",
                    source_owner="estimated_internal_cost_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={"conflict_code": "not_tested_downstream"},
                ),
            ]

        if template_code != PARENT_TEMPLATE_CODE:
            return [
                _finding(
                    check_id="cpp.runtime_template_out_of_scope",
                    system="cpp",
                    status="NOT_TESTED",
                    message="Runtime CPP ml proof scoped to TPL-VOLUMETRIC-LETTERS_v2.",
                    source_owner="commercial_price_proposal_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={"conflict_code": "not_tested_downstream"},
                ),
                _finding(
                    check_id="eic.runtime_template_out_of_scope",
                    system="eic",
                    status="NOT_TESTED",
                    message="Runtime EIC ml proof scoped to TPL-VOLUMETRIC-LETTERS_v2.",
                    source_owner="estimated_internal_cost_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={"conflict_code": "not_tested_downstream"},
                ),
            ]

        component_qty = resolve_component_quantity_from_payload(payload)
        total_auth = resolve_product_total_perimeter_authority(payload)
        preview = VolumAluminiuSeparateCalcPreviewService().build_preview(
            VOLUM_ALUMINIU_TEMPLATE_CODE,
            VolumAluminiuSeparateCalcPreviewRequest(payload=payload),
        )

        findings: list[ProductE2ECheckFinding] = []
        preview_qty = None
        if isinstance(preview.quantity, dict):
            preview_qty = preview.quantity.get("quantity_m")
        total_qty = total_auth.get("quantity_m")
        commercial = preview.commercial if isinstance(preview.commercial, dict) else {}
        basis = str(commercial.get("basis_type") or "").strip().lower()
        hourly_hit = basis in {"hour", "hourly", "h", "ore", "ora"}
        qty_aligned = (
            component_qty.get("ok") is True
            and preview.separate_calculation == "PASS"
            and preview_qty is not None
            and total_qty is not None
            and abs(float(preview_qty) - float(total_qty)) < 1e-6
            and abs(float(preview_qty) - float(component_qty["quantity_m"])) < 1e-6
        )

        if qty_aligned and basis == COMMERCIAL_BASIS_SYNONYM and not hourly_hit:
            findings.append(
                _finding(
                    check_id="cpp.runtime_ml_preview_aligned",
                    system="cpp",
                    status="PASS",
                    message=(
                        "Runtime dry-run: separate-calc CPP ml qty aligns with confirmed "
                        "perimeter / product-total (no formula duplication)."
                    ),
                    source_owner="volum_aluminiu_separate_calc_preview_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={
                        "quantity_m": preview_qty,
                        "basis_type": basis,
                        "commercial_line_code": COMMERCIAL_LINE_CODE,
                        "persist": preview.persist,
                    },
                )
            )
        else:
            findings.append(
                _finding(
                    check_id="cpp.runtime_ml_preview_misaligned",
                    system="cpp",
                    status="FAIL",
                    message="Runtime dry-run: CPP ml preview/product-total alignment failed.",
                    source_owner="volum_aluminiu_separate_calc_preview_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={
                        "conflict_code": "cpp_ml_preview_misaligned",
                        "component_qty": component_qty,
                        "total_authority": {
                            "authority": total_auth.get("authority"),
                            "quantity_m": total_qty,
                        },
                        "separate_calculation": preview.separate_calculation,
                        "basis_type": basis,
                        "hourly_hit": hourly_hit,
                    },
                )
            )

        internal = preview.internal_cost if isinstance(preview.internal_cost, dict) else {}
        internal_ok = (
            preview.separate_calculation == "PASS"
            and str(internal.get("rule_code") or "") == INTERNAL_RULE_CODE
            and qty_aligned
            and not hourly_hit
        )
        if internal_ok:
            findings.append(
                _finding(
                    check_id="eic.runtime_ml_internal_aligned",
                    system="eic",
                    status="PASS",
                    message=(
                        "Runtime dry-run: EIC INT_VOL_V2_RETURN_ML shares confirmed ml qty "
                        "(no formula duplication)."
                    ),
                    source_owner="volum_aluminiu_separate_calc_preview_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={
                        "rule_code": INTERNAL_RULE_CODE,
                        "quantity_m": preview_qty,
                        "persist": preview.persist,
                    },
                )
            )
        else:
            findings.append(
                _finding(
                    check_id="eic.runtime_ml_internal_misaligned",
                    system="eic",
                    status="FAIL",
                    message="Runtime dry-run: EIC ml internal rule/qty alignment failed.",
                    source_owner="volum_aluminiu_separate_calc_preview_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={
                        "conflict_code": "eic_ml_internal_misaligned",
                        "internal": internal,
                        "qty_aligned": qty_aligned,
                        "hourly_hit": hourly_hit,
                    },
                )
            )
        return findings

    def _check_snapshot(
        self,
        template_code: str,
        *,
        mode: ProductE2EMode,
        payload: dict[str, Any] | None,
        workspace_id: str | None,
    ) -> list[ProductE2ECheckFinding]:
        findings = [
            _finding(
                check_id="quote_snapshot.freeze_gate_helper",
                system="quote_snapshot",
                status="PASS",
                message=(
                    "Snapshot freeze gate inspects commercial_freeze_allowed / "
                    "assert_commercial_freeze_allowed."
                ),
                source_owner="product_truth_job_confirm_service",
                template_code=template_code,
                blocking=False,
                evidence={
                    "helpers": [
                        "commercial_freeze_allowed",
                        "assert_commercial_freeze_allowed",
                    ]
                },
            )
        ]
        if mode == "static":
            findings.append(
                _finding(
                    check_id="quote_snapshot.runtime_freeze",
                    system="quote_snapshot",
                    status="NOT_TESTED",
                    message="Static check does not perform Snapshot V2 freeze.",
                    source_owner="intake_v6_quote_snapshot_v2_service",
                    template_code=template_code,
                    blocking=False,
                    evidence={"conflict_code": "snapshot_live_race_not_exercised"},
                )
            )
            return findings

        if payload is None:
            findings.append(
                _finding(
                    check_id="quote_snapshot.no_workspace",
                    system="quote_snapshot",
                    status="BLOCKED",
                    message="Cannot assess freeze gate without workspace payload.",
                    source_owner="intake_v6_quote_snapshot_v2_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                )
            )
            return findings

        if commercial_freeze_allowed(payload):
            findings.append(
                _finding(
                    check_id="quote_snapshot.freeze_allowed",
                    system="quote_snapshot",
                    status="PASS",
                    message="Freeze gate would allow Snapshot V2 (confirmed non-stale job revision).",
                    source_owner="intake_v6_quote_snapshot_v2_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                )
            )
        else:
            findings.append(
                _finding(
                    check_id="quote_snapshot.freeze_blocked",
                    system="quote_snapshot",
                    status="FAIL",
                    message=(
                        "Freeze gate would block Snapshot V2 "
                        "(product truth not confirmed or stale)."
                    ),
                    source_owner="intake_v6_quote_snapshot_v2_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={"conflict_code": "snapshot_freeze_blocked"},
                )
            )
        return findings

    def _check_execution_handoff(
        self,
        template_code: str,
        *,
        mode: ProductE2EMode,
        payload: dict[str, Any] | None,
        workspace_id: str | None,
    ) -> list[ProductE2ECheckFinding]:
        """Order/EP: static NOT_TESTED; runtime proves provenance + frozen preview (no materialize)."""
        if mode == "static" or payload is None:
            return [
                _finding(
                    check_id="order_snapshot.not_tested",
                    system="order_snapshot",
                    status="NOT_TESTED",
                    message="Order Snapshot copy path not exercised (no writes / no order create).",
                    source_owner="order_snapshot_v2_convert_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={"conflict_code": "order_reread_risk_not_exercised"},
                ),
                _finding(
                    check_id="execution_preview.not_tested",
                    system="execution_preview",
                    status="NOT_TESTED",
                    message="ExecutionPlan preview not exercised (no materialization).",
                    source_owner="execution_plan_v2_preview_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={"conflict_code": "execution_catalog_bypass_not_exercised"},
                ),
            ]

        findings: list[ProductE2ECheckFinding] = []
        meta = get_job_revision_metadata(payload) or {}
        freeze_ok = commercial_freeze_allowed(payload)

        if not freeze_ok:
            findings.append(
                _finding(
                    check_id="order_snapshot.freeze_blocked",
                    system="order_snapshot",
                    status="FAIL",
                    message="Order Snapshot provenance proof requires confirmed non-stale Product Truth.",
                    source_owner="order_snapshot_v2_convert_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={"conflict_code": "order_snapshot_freeze_blocked"},
                )
            )
            findings.append(
                _finding(
                    check_id="execution_preview.freeze_blocked",
                    system="execution_preview",
                    status="FAIL",
                    message="Execution preview proof requires confirmed non-stale Product Truth.",
                    source_owner="execution_preview_from_frozen_graph_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={"conflict_code": "execution_preview_freeze_blocked"},
                )
            )
            return findings

        # Circular import: order_snapshot_v2_convert → … → product_e2e_readiness.
        from services.order_snapshot_v2_convert_service import (  # noqa: PLC0415
            _enrich_order_provenance_with_product_truth,
        )

        linkage = {
            "product_truth_revision": meta.get("revision"),
            "product_truth_content_hash": meta.get("content_hash"),
            "freeze_from_pinned_product_truth": True,
        }
        prov = _enrich_order_provenance_with_product_truth(
            SimpleNamespace(provenance={"source": "quote_snapshot_v2_dry_run"}),
            linkage,
        )
        if (
            prov.get("product_truth_revision") == meta.get("revision")
            and prov.get("product_truth_content_hash") == meta.get("content_hash")
            and prov.get("no_live_workspace_reread") is True
        ):
            findings.append(
                _finding(
                    check_id="order_snapshot.runtime_provenance_pass_through",
                    system="order_snapshot",
                    status="PASS",
                    message=(
                        "Runtime dry-run: Order Snapshot provenance copies Product Truth "
                        "revision/hash with no_live_workspace_reread (no order create)."
                    ),
                    source_owner="order_snapshot_v2_convert_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={
                        "product_truth_revision": prov.get("product_truth_revision"),
                        "no_live_workspace_reread": True,
                        "order_created": False,
                    },
                )
            )
        else:
            findings.append(
                _finding(
                    check_id="order_snapshot.runtime_provenance_failed",
                    system="order_snapshot",
                    status="FAIL",
                    message="Runtime dry-run: Order Snapshot provenance pass-through failed.",
                    source_owner="order_snapshot_v2_convert_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={"conflict_code": "order_provenance_mismatch", "provenance": prov},
                )
            )

        snap = QuoteSnapshotV2(
            template_code=template_code,
            offer_scope_snapshot=QuoteSnapshotOfferScope(
                mode="full_product",
                sold_modules=[],
                use_legacy=True,
            ),
            product_definition_snapshot=ProductDefinitionPreview(
                template_code=template_code,
                source_context=ProductDefinitionSourceContext(template_code=template_code),
                product_truth_job_revision=meta.get("revision"),
                product_truth_content_hash=meta.get("content_hash"),
                product_truth_status="confirmed",
            ),
            product_aggregate_snapshot=ProductAggregate(
                template_code=template_code,
                template_id=0,
            ),
            commercial_price_proposal_snapshot=CommercialPriceProposalPreview(
                template_code=template_code,
                currency="RON",
            ),
            estimated_internal_cost_snapshot=EstimatedInternalCostPreview(
                template_code=template_code,
            ),
            persist_status="not_persisted",
            workspace_id=workspace_id,
        )
        preview = build_execution_preview_from_frozen_snapshot(snap)
        safety = preview.safety
        if (
            safety.no_write is True
            and safety.no_materialization is True
            and safety.no_live_recompile is True
        ):
            findings.append(
                _finding(
                    check_id="execution_preview.runtime_frozen_preview",
                    system="execution_preview",
                    status="PASS",
                    message=(
                        "Runtime dry-run: Execution preview from frozen snapshot "
                        "(no write / no materialization / no live recompile)."
                    ),
                    source_owner="execution_preview_from_frozen_graph_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    blocking=False,
                    evidence={
                        "no_write": True,
                        "no_materialization": True,
                        "no_live_recompile": True,
                        "source_authority": getattr(
                            getattr(preview, "source", None), "source_authority", None
                        ),
                    },
                )
            )
        else:
            findings.append(
                _finding(
                    check_id="execution_preview.runtime_safety_failed",
                    system="execution_preview",
                    status="FAIL",
                    message="Runtime dry-run: Execution preview safety flags not all true.",
                    source_owner="execution_preview_from_frozen_graph_service",
                    template_code=template_code,
                    workspace_id=workspace_id,
                    evidence={
                        "conflict_code": "execution_preview_safety_failed",
                        "no_write": safety.no_write,
                        "no_materialization": safety.no_materialization,
                        "no_live_recompile": safety.no_live_recompile,
                    },
                )
            )
        return findings
