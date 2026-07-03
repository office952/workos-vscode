"""
Phase 4 — ProductSystem Registry Linkage Validator (S27).

Read-only service that cross-validates task_templates linkage fields
against the live Foundation Registries (Skills, Workcenters) and
canonical enums (machine_type, material_code).

Safety guarantees:
  - No DB writes. No mutations. No side effects.
  - Idempotent: same input + same registry state → same output.
  - Consumes registries via internal M2 service calls (not HTTP).

Forbidden imports (spec §24 FP-02):
  - cost_engine_service
  - quote_orchestrator
  - ExecutionPlanService
  - MaterialRate
  - execution_plan_service
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from data_models.linkage_contracts import LinkageIssue, LinkageValidationResult
from services.foundation_registries import (
    SkillsReadService,
    WorkcentersReadService,
)
from services.machines_read_service import MachinesReadService
from services.materials_read_service import MaterialsReadService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Canonical enums (spec-locked, no DB dependency)
# ---------------------------------------------------------------------------

# 11-value machine_type enum from spec__machine_skill_requirements.md §6.2
CANONICAL_MACHINE_TYPES: frozenset[str] = frozenset(
    {
        "cnc_router",
        "laser_cutter",
        "printer_large_format",
        "printer_uv_flatbed",
        "laminator",
        "edge_bander",
        "assembly_station",
        "led_station",
        "welding_station",
        "paint_booth",
        "packaging_machine",
    }
)

# Canonical ~30-code material enum (interim, until M22 ships).
# From spec__machine_skill_requirements.md §10.3 + seeded data.
CANONICAL_MATERIAL_CODES: frozenset[str] = frozenset(
    {
        "MAT-PROFIL-ALU",
        "MAT-SURUBURI-GEN",
        "MAT-ADEZIV-SILICON",
        "MAT-ACP-3MM",
        "MAT-ACP-4MM",
        "MAT-PLEXI-OPAL-3MM",
        "MAT-PLEXI-OPAL-10MM",
        "MAT-PLEXI-CLEAR-3MM",
        "MAT-PLEXI-CLEAR-5MM",
        "MAT-LED-MODULE",
        "MAT-LED-PSU-12V",
        "MAT-LED-PSU-24V",
        "MAT-CONSUMABILE-MONTAJ",
        "MAT-VINYL-PRINT",
        "MAT-VINYL-CUT",
        "MAT-LAMINATE-GLOSS",
        "MAT-LAMINATE-MATTE",
        "MAT-FOAM-PVC-10MM",
        "MAT-FOAM-PVC-19MM",
        "MAT-DIBOND-3MM",
        "MAT-MDF-18MM",
        "MAT-PAL-18MM",
        "MAT-STEEL-SHEET-2MM",
        "MAT-STEEL-TUBE-40X40",
        "MAT-PAINT-RAL",
        "MAT-NEON-FLEX",
        "MAT-CABLU-ELECTRIC",
        "MAT-BANDA-LED-12V",
        "MAT-BANDA-LED-24V",
        "MAT-SPACER-DISTANTIER",
    }
)

# Task types exempt from requiring skill_ids (Rule TT-02).
SKILL_EXEMPT_TASK_TYPES: frozenset[str] = frozenset(
    {"file_preparation", "measurement", "quality_control"}
)

# Task types that allow NULL workcenter (zero-machine tasks).
WORKCENTER_EXEMPT_TASK_TYPES: frozenset[str] = frozenset(
    {"file_preparation", "measurement", "mounting", "installation", "quality_control"}
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TemplateNotFoundError(Exception):
    """Raised when template_id does not exist in product_templates."""

    def __init__(self, template_id: int):
        super().__init__(f"Template {template_id} not found")
        self.template_id = template_id


class TemplateInactiveError(Exception):
    """Raised when template exists but active=false."""

    def __init__(self, template_id: int, template_code: str):
        super().__init__(f"Template {template_id} ({template_code}) is inactive")
        self.template_id = template_id
        self.template_code = template_code


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ProductSystemLinkageValidator:
    """
    Read-only service that validates linkage between task_templates
    and Foundation Registries (Skills, Workcenters, Materials, Machines).

    No writes. No mutations. Pure read.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._skills_svc = SkillsReadService(db)
        self._workcenters_svc = WorkcentersReadService(db)
        self._materials_svc = MaterialsReadService(db)
        self._machines_svc = MachinesReadService(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def validate_template_linkage(
        self, template_id: int
    ) -> LinkageValidationResult:
        """
        Validate all task_template linkage fields for a given template.

        Reads:
          - product_templates (existence + active check)
          - task_templates (all rows for template_id)
          - Skills Registry (M2 internal service)
          - Workcenters Registry (M2 internal service)
          - Config flags (registry_materials_live, registry_machines_live)

        Writes: NOTHING.
        """
        # 1. Resolve template
        template_row = await self._get_template(template_id)

        # 2. Read task_templates for this template
        task_rows = await self._get_task_templates(template_id)

        # 3. Validate each task_template
        blockers: List[LinkageIssue] = []
        warnings: List[LinkageIssue] = []
        registries_consulted: List[str] = []
        registries_unavailable: List[str] = []

        # Pre-fetch all skills and workcenters for batch validation
        skills_cache = await self._fetch_all_skills()
        workcenters_cache = await self._fetch_all_workcenters()

        if skills_cache is not None:
            registries_consulted.append("skills")
        else:
            registries_unavailable.append("skills")

        if workcenters_cache is not None:
            registries_consulted.append("workcenters")
        else:
            registries_unavailable.append("workcenters")

        # Materials and machines registries status
        if not settings.registry_materials_live:
            registries_unavailable.append("materials")
        else:
            registries_consulted.append("materials")

        if not settings.registry_machines_live:
            registries_unavailable.append("machines")
        else:
            registries_consulted.append("machines")

        for idx, task_row in enumerate(task_rows):
            issues = self._validate_single_task(
                task_row=task_row,
                idx=idx,
                skills_cache=skills_cache,
                workcenters_cache=workcenters_cache,
            )
            for issue in issues:
                if issue.severity == "blocker":
                    blockers.append(issue)
                else:
                    warnings.append(issue)

            # M22: async materials validation when registry is live
            if settings.registry_materials_live:
                mat_issues = await self._validate_materials_async(
                    task_id=str(task_row.get("task_template_id", f"task_{idx}")),
                    material_requirements=task_row.get("material_requirements"),
                    prefix=f"task_templates[{idx}]",
                )
                for issue in mat_issues:
                    if issue.severity == "blocker":
                        blockers.append(issue)
                    else:
                        warnings.append(issue)

            # M19: async machine validation when registry is live
            if settings.registry_machines_live:
                machine_issues = await self._validate_machine_async(
                    task_id=str(task_row.get("task_template_id", f"task_{idx}")),
                    required_machine_id=task_row.get("required_machine_id"),
                    required_machine_type=task_row.get("required_machine_type"),
                    prefix=f"task_templates[{idx}]",
                )
                for issue in machine_issues:
                    if issue.severity == "blocker":
                        blockers.append(issue)
                    else:
                        warnings.append(issue)

        return LinkageValidationResult.build(
            template_id=template_id,
            template_code=str(template_row["template_code"]),
            blockers=blockers,
            warnings=warnings,
            registries_consulted=registries_consulted,
            registries_unavailable=registries_unavailable,
            task_template_count=len(task_rows),
        )

    async def validate_single_task_template(
        self, task_template: Dict[str, Any]
    ) -> List[LinkageIssue]:
        """
        Validate a single task_template's linkage fields.
        Used by write-path integration (POST/PUT of task_templates).
        """
        skills_cache = await self._fetch_all_skills()
        workcenters_cache = await self._fetch_all_workcenters()
        return self._validate_single_task(
            task_row=task_template,
            idx=0,
            skills_cache=skills_cache,
            workcenters_cache=workcenters_cache,
        )

    # ------------------------------------------------------------------
    # Internal: DB reads (read-only)
    # ------------------------------------------------------------------

    async def _get_template(self, template_id: int) -> Dict[str, Any]:
        """Read product_template by id. Raises if not found or inactive."""
        sql = text(
            "SELECT id, template_code, family_name, active "
            "FROM product_templates WHERE id = :template_id LIMIT 1"
        )
        result = await self._db.execute(sql, {"template_id": template_id})
        row = result.mappings().first()
        if not row:
            raise TemplateNotFoundError(template_id)
        if not row.get("active", True):
            raise TemplateInactiveError(template_id, str(row.get("template_code", "")))
        return dict(row)

    async def _get_task_templates(self, template_id: int) -> List[Dict[str, Any]]:
        """Read all task_templates for a given template_id."""
        sql = text(
            "SELECT task_template_id, source_operation_id, task_type, "
            "required_skill_ids, required_workcenter_id, "
            "required_machine_type, required_machine_id, "
            "material_requirements, estimated_duration "
            "FROM task_templates WHERE template_id = :template_id "
            "ORDER BY id ASC"
        )
        try:
            result = await self._db.execute(sql, {"template_id": template_id})
        except OperationalError as exc:
            if "no such table: task_templates" in str(exc).lower():
                logger.info(
                    "task_templates table is not present; skipping legacy task linkage validation for template %s",
                    template_id,
                )
                return []
            raise
        return [dict(r) for r in result.mappings().all()]

    async def _fetch_all_skills(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """Fetch all skills into a code->row dict for batch lookup."""
        try:
            result = await self._skills_svc.list(active=None, limit=200, offset=0)
            items = result.get("items", [])
            return {item["skill_code"]: item for item in items}
        except Exception as exc:
            logger.warning("Skills registry unavailable: %s", exc)
            return None

    async def _fetch_all_workcenters(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """Fetch all workcenters into a code->row dict for batch lookup."""
        try:
            result = await self._workcenters_svc.list(active=None, limit=200, offset=0)
            items = result.get("items", [])
            return {item["workcenter_code"]: item for item in items}
        except Exception as exc:
            logger.warning("Workcenters registry unavailable: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Internal: validation logic (pure, no I/O)
    # ------------------------------------------------------------------

    def _validate_single_task(
        self,
        *,
        task_row: Dict[str, Any],
        idx: int,
        skills_cache: Optional[Dict[str, Dict[str, Any]]],
        workcenters_cache: Optional[Dict[str, Dict[str, Any]]],
    ) -> List[LinkageIssue]:
        """Validate all linkage fields for a single task_template row."""
        issues: List[LinkageIssue] = []
        task_id = str(task_row.get("task_template_id", f"task_{idx}"))
        task_type = str(task_row.get("task_type", ""))
        prefix = f"task_templates[{idx}]"

        # --- Skills validation ---
        issues.extend(
            self._validate_skills(
                task_id=task_id,
                task_type=task_type,
                required_skill_ids=task_row.get("required_skill_ids"),
                prefix=prefix,
                skills_cache=skills_cache,
            )
        )

        # --- Workcenters validation ---
        issues.extend(
            self._validate_workcenter(
                task_id=task_id,
                task_type=task_type,
                required_workcenter_id=task_row.get("required_workcenter_id"),
                required_machine_type=task_row.get("required_machine_type"),
                required_machine_id=task_row.get("required_machine_id"),
                prefix=prefix,
                workcenters_cache=workcenters_cache,
            )
        )

        # --- Machine type validation ---
        issues.extend(
            self._validate_machine_type(
                task_id=task_id,
                required_machine_type=task_row.get("required_machine_type"),
                prefix=prefix,
            )
        )

        # --- Machine ID validation ---
        issues.extend(
            self._validate_machine_id(
                task_id=task_id,
                required_machine_id=task_row.get("required_machine_id"),
                prefix=prefix,
            )
        )

        # --- Materials validation ---
        issues.extend(
            self._validate_materials(
                task_id=task_id,
                material_requirements=task_row.get("material_requirements"),
                prefix=prefix,
            )
        )

        return issues

    def _validate_skills(
        self,
        *,
        task_id: str,
        task_type: str,
        required_skill_ids: Any,
        prefix: str,
        skills_cache: Optional[Dict[str, Dict[str, Any]]],
    ) -> List[LinkageIssue]:
        """Validate required_skill_ids against Skills Registry."""
        issues: List[LinkageIssue] = []

        # Normalize skill_ids
        skill_ids: List[str] = []
        if isinstance(required_skill_ids, list):
            skill_ids = [str(s) for s in required_skill_ids if s]
        elif isinstance(required_skill_ids, str):
            # Could be a PostgreSQL array literal like {A,B,C}
            cleaned = required_skill_ids.strip("{}")
            if cleaned:
                skill_ids = [s.strip() for s in cleaned.split(",") if s.strip()]

        # Check empty skills for non-exempt task types
        if not skill_ids and task_type not in SKILL_EXEMPT_TASK_TYPES:
            issues.append(
                LinkageIssue(
                    severity="blocker",
                    task_template_id=task_id,
                    path=f"{prefix}.required_skill_ids",
                    code="PS-BLK-05",
                    message=f"Task template '{task_id}' has empty required_skill_ids for non-exempt task_type '{task_type}'",
                    details={"task_type": task_type, "reason": "missing_skills"},
                )
            )
            return issues

        # If skills registry unavailable, skip resolution checks
        if skills_cache is None:
            return issues

        # Validate each skill_code
        for skill_idx, skill_code in enumerate(skill_ids):
            skill_entry = skills_cache.get(skill_code)
            if skill_entry is None:
                issues.append(
                    LinkageIssue(
                        severity="blocker",
                        task_template_id=task_id,
                        path=f"{prefix}.required_skill_ids[{skill_idx}]",
                        code="PS-BLK-09",
                        message=f"Skill code '{skill_code}' not found in Skills Registry",
                        details={"skill_code": skill_code, "reason": "not_found"},
                    )
                )
            elif not skill_entry.get("active", True):
                issues.append(
                    LinkageIssue(
                        severity="blocker",
                        task_template_id=task_id,
                        path=f"{prefix}.required_skill_ids[{skill_idx}]",
                        code="PS-BLK-09",
                        message=f"Skill code '{skill_code}' is inactive in Skills Registry",
                        details={"skill_code": skill_code, "reason": "skill_inactive"},
                    )
                )

        return issues

    def _validate_workcenter(
        self,
        *,
        task_id: str,
        task_type: str,
        required_workcenter_id: Any,
        required_machine_type: Any,
        required_machine_id: Any,
        prefix: str,
        workcenters_cache: Optional[Dict[str, Dict[str, Any]]],
    ) -> List[LinkageIssue]:
        """Validate required_workcenter_id against Workcenters Registry."""
        issues: List[LinkageIssue] = []
        wc_code = str(required_workcenter_id).strip() if required_workcenter_id else ""

        # NULL workcenter check
        if not wc_code:
            # For non-exempt task types, check Rule TT-03
            if task_type not in WORKCENTER_EXEMPT_TASK_TYPES:
                has_machine = bool(required_machine_type) or bool(required_machine_id)
                if not has_machine:
                    issues.append(
                        LinkageIssue(
                            severity="blocker",
                            task_template_id=task_id,
                            path=f"{prefix}.required_workcenter_id",
                            code="PS-BLK-06",
                            message=f"Task template '{task_id}' has NULL workcenter and no machine assignment for task_type '{task_type}'",
                            details={"task_type": task_type, "reason": "missing_machine_or_workcenter"},
                        )
                    )
            return issues

        # If workcenters registry unavailable, skip resolution checks
        if workcenters_cache is None:
            return issues

        # Resolution check
        wc_entry = workcenters_cache.get(wc_code)
        if wc_entry is None:
            issues.append(
                LinkageIssue(
                    severity="blocker",
                    task_template_id=task_id,
                    path=f"{prefix}.required_workcenter_id",
                    code="PS-BLK-10",
                    message=f"Workcenter code '{wc_code}' not found in Workcenters Registry",
                    details={"workcenter_code": wc_code, "reason": "not_found"},
                )
            )
        elif wc_entry.get("operational_status") != "active":
            issues.append(
                LinkageIssue(
                    severity="blocker",
                    task_template_id=task_id,
                    path=f"{prefix}.required_workcenter_id",
                    code="PS-BLK-10",
                    message=f"Workcenter code '{wc_code}' is not active (status: {wc_entry.get('operational_status')})",
                    details={
                        "workcenter_code": wc_code,
                        "reason": "workcenter_not_active",
                        "operational_status": wc_entry.get("operational_status"),
                    },
                )
            )

        return issues

    def _validate_machine_type(
        self,
        *,
        task_id: str,
        required_machine_type: Any,
        prefix: str,
    ) -> List[LinkageIssue]:
        """Validate required_machine_type against canonical 11-value enum."""
        issues: List[LinkageIssue] = []
        mt = str(required_machine_type).strip() if required_machine_type else ""

        if not mt:
            return issues  # NULL is acceptable (handled by workcenter check)

        if mt not in CANONICAL_MACHINE_TYPES:
            issues.append(
                LinkageIssue(
                    severity="blocker",
                    task_template_id=task_id,
                    path=f"{prefix}.required_machine_type",
                    code="PS-BLK-12",
                    message=f"Machine type '{mt}' is not in the canonical 11-value enum",
                    details={
                        "machine_type": mt,
                        "reason": "not_in_enum",
                        "allowed_values": sorted(CANONICAL_MACHINE_TYPES),
                    },
                )
            )

        return issues

    def _validate_machine_id(
        self,
        *,
        task_id: str,
        required_machine_id: Any,
        prefix: str,
    ) -> List[LinkageIssue]:
        """Validate required_machine_id (config-gated, sync fallback).

        When registry_machines_live=false: emit WRN-03.
        When registry_machines_live=true: the async path (_validate_machine_async)
        handles full FK validation. This sync method emits WRN-03 as fallback.
        """
        issues: List[LinkageIssue] = []
        mid = str(required_machine_id).strip() if required_machine_id else ""

        if not mid:
            return issues  # NULL is acceptable

        if not settings.registry_machines_live:
            # M19 not live — emit warning only
            issues.append(
                LinkageIssue(
                    severity="warning",
                    task_template_id=task_id,
                    path=f"{prefix}.required_machine_id",
                    code="PS-WRN-03",
                    message=f"Machines registry not live; machine_id '{mid}' cannot be FK-validated",
                    details={"machine_id": mid, "registry": "machines", "reason": "registry_not_live"},
                )
            )
        else:
            # Registry is live — sync path cannot resolve FK, emit blocker.
            # The async path (_validate_machine_async) would do full DB lookup;
            # in sync context we conservatively block unresolvable machine_ids.
            issues.append(
                LinkageIssue(
                    severity="blocker",
                    task_template_id=task_id,
                    path=f"{prefix}.required_machine_id",
                    code="PS-BLK-12",
                    message=f"Machine '{mid}' cannot be resolved against live machines registry",
                    details={"machine_id": mid, "registry": "machines", "reason": "unresolvable"},
                )
            )

        return issues

    async def _validate_materials_async(
        self,
        *,
        task_id: str,
        material_requirements: Any,
        prefix: str,
    ) -> List[LinkageIssue]:
        """Validate material_requirements entries (async — uses MaterialsReadService when live)."""
        issues: List[LinkageIssue] = []

        # Normalize material_requirements (may be JSONB list or string)
        materials: List[Dict[str, Any]] = []
        if isinstance(material_requirements, list):
            materials = material_requirements
        elif isinstance(material_requirements, str):
            import json
            try:
                parsed = json.loads(material_requirements)
                if isinstance(parsed, list):
                    materials = parsed
            except (json.JSONDecodeError, TypeError):
                pass

        # Empty materials is acceptable (some tasks consume no materials)
        if not materials:
            return issues

        for mat_idx, mat in enumerate(materials):
            if not isinstance(mat, dict):
                continue

            mat_code = str(mat.get("material_code", "") or mat.get("materialCode", "")).strip()
            mat_path = f"{prefix}.material_requirements[{mat_idx}]"

            # Material code validation
            if mat_code:
                if not settings.registry_materials_live:
                    # Interim: enum membership check + WRN-02
                    if mat_code not in CANONICAL_MATERIAL_CODES:
                        issues.append(
                            LinkageIssue(
                                severity="warning",
                                task_template_id=task_id,
                                path=f"{mat_path}.material_code",
                                code="PS-WRN-02",
                                message=f"Materials registry not live; material_code '{mat_code}' cannot be FK-validated",
                                details={
                                    "material_code": mat_code,
                                    "registry": "materials",
                                    "reason": "registry_not_live",
                                },
                            )
                        )
                else:
                    # M22 LIVE: FK-validate against Materials Registry via MaterialsReadService
                    availability = await self._materials_svc.material_available(mat_code)
                    if not availability["found"]:
                        issues.append(
                            LinkageIssue(
                                severity="blocker",
                                task_template_id=task_id,
                                path=f"{mat_path}.material_code",
                                code="PS-BLK-14",
                                message=f"Material code '{mat_code}' not found in Materials Registry",
                                details={"material_code": mat_code, "reason": "not_found"},
                            )
                        )
                    elif not availability["active"]:
                        issues.append(
                            LinkageIssue(
                                severity="blocker",
                                task_template_id=task_id,
                                path=f"{mat_path}.material_code",
                                code="PS-BLK-14",
                                message=f"Material code '{mat_code}' is inactive in Materials Registry",
                                details={"material_code": mat_code, "reason": "material_inactive"},
                            )
                        )

            # Quantity validation (always, regardless of config)
            has_formula = bool(mat.get("quantity_formula"))
            has_static = mat.get("quantity_static") is not None or mat.get("quantity") is not None

            # XOR check: exactly one of quantity_formula / quantity_static
            if has_formula and has_static:
                static_val = mat.get("quantity_static") if mat.get("quantity_static") is not None else mat.get("quantity")
                if static_val is not None and static_val != 0:
                    issues.append(
                        LinkageIssue(
                            severity="blocker",
                            task_template_id=task_id,
                            path=f"{mat_path}",
                            code="PS-BLK-13",
                            message=f"Material entry has both quantity_formula and quantity_static (XOR violation)",
                            details={"material_code": mat_code, "reason": "quantity_xor_violation"},
                        )
                    )

            # Static quantity > 0 check
            if has_static and not has_formula:
                qty = mat.get("quantity_static") if mat.get("quantity_static") is not None else mat.get("quantity")
                if qty is not None:
                    try:
                        qty_val = float(qty)
                        if qty_val <= 0:
                            issues.append(
                                LinkageIssue(
                                    severity="blocker",
                                    task_template_id=task_id,
                                    path=f"{mat_path}.quantity",
                                    code="PS-BLK-14",
                                    message=f"Material quantity must be > 0 (got {qty_val})",
                                    details={"material_code": mat_code, "quantity": qty_val, "reason": "non_positive"},
                                )
                            )
                    except (TypeError, ValueError):
                        pass

        return issues

    async def _validate_machine_async(
        self,
        *,
        task_id: str,
        required_machine_id: Any,
        required_machine_type: Any,
        prefix: str,
    ) -> List[LinkageIssue]:
        """Validate machine linkage (async — uses MachinesReadService when live).

        BLK-19 paths:
          - machine_id specified but not found → BLK-19
          - machine_id found but inactive → BLK-19
          - machine_id found but unavailable → BLK-19
          - machine_id found but operational_status != active → BLK-19
          - machine_type specified, no machines of that type available → BLK-19
        """
        issues: List[LinkageIssue] = []

        mid = str(required_machine_id).strip() if required_machine_id else ""
        mtype = str(required_machine_type).strip() if required_machine_type else ""

        # Validate specific machine_id if provided
        if mid:
            availability = await self._machines_svc.machine_available(mid)
            if not availability["found"]:
                issues.append(
                    LinkageIssue(
                        severity="blocker",
                        task_template_id=task_id,
                        path=f"{prefix}.required_machine_id",
                        code="PS-BLK-19",
                        message=f"Machine code '{mid}' not found in Machines Registry",
                        details={"machine_id": mid, "reason": "not_found"},
                    )
                )
            elif not availability["active"]:
                issues.append(
                    LinkageIssue(
                        severity="blocker",
                        task_template_id=task_id,
                        path=f"{prefix}.required_machine_id",
                        code="PS-BLK-19",
                        message=f"Machine code '{mid}' is inactive in Machines Registry",
                        details={"machine_id": mid, "reason": "machine_inactive"},
                    )
                )
            elif not availability["available"]:
                issues.append(
                    LinkageIssue(
                        severity="blocker",
                        task_template_id=task_id,
                        path=f"{prefix}.required_machine_id",
                        code="PS-BLK-19",
                        message=f"Machine code '{mid}' is not available in Machines Registry",
                        details={"machine_id": mid, "reason": "machine_unavailable"},
                    )
                )
            elif not availability["operational"]:
                issues.append(
                    LinkageIssue(
                        severity="blocker",
                        task_template_id=task_id,
                        path=f"{prefix}.required_machine_id",
                        code="PS-BLK-19",
                        message=f"Machine code '{mid}' is not operational (status: {availability['machine'].get('operational_status')})",
                        details={
                            "machine_id": mid,
                            "reason": "machine_not_operational",
                            "operational_status": availability["machine"].get("operational_status"),
                        },
                    )
                )

        # Validate machine_type has at least one available machine (when no specific machine_id)
        if mtype and not mid:
            type_machines = await self._machines_svc.get_by_type(mtype)
            available_machines = [
                m for m in type_machines
                if m.get("is_active") and m.get("is_available") and m.get("operational_status") == "active"
            ]
            if not type_machines:
                issues.append(
                    LinkageIssue(
                        severity="blocker",
                        task_template_id=task_id,
                        path=f"{prefix}.required_machine_type",
                        code="PS-BLK-19",
                        message=f"No machines of type '{mtype}' exist in Machines Registry",
                        details={"machine_type": mtype, "reason": "no_machines_of_type"},
                    )
                )
            elif not available_machines:
                issues.append(
                    LinkageIssue(
                        severity="blocker",
                        task_template_id=task_id,
                        path=f"{prefix}.required_machine_type",
                        code="PS-BLK-19",
                        message=f"No available machines of type '{mtype}' in Machines Registry",
                        details={
                            "machine_type": mtype,
                            "reason": "no_available_machines_of_type",
                            "total_of_type": len(type_machines),
                        },
                    )
                )

        return issues

    def _validate_materials(
        self,
        *,
        task_id: str,
        material_requirements: Any,
        prefix: str,
    ) -> List[LinkageIssue]:
        """Validate material_requirements entries (sync fallback for non-async callers).

        When registry_materials_live=false, performs local enum check only.
        When registry_materials_live=true, this sync method falls back to enum check.
        The async path (_validate_materials_async) should be preferred.
        """
        issues: List[LinkageIssue] = []

        # Normalize material_requirements (may be JSONB list or string)
        materials: List[Dict[str, Any]] = []
        if isinstance(material_requirements, list):
            materials = material_requirements
        elif isinstance(material_requirements, str):
            import json
            try:
                parsed = json.loads(material_requirements)
                if isinstance(parsed, list):
                    materials = parsed
            except (json.JSONDecodeError, TypeError):
                pass

        # Empty materials is acceptable (some tasks consume no materials)
        if not materials:
            return issues

        for mat_idx, mat in enumerate(materials):
            if not isinstance(mat, dict):
                continue

            mat_code = str(mat.get("material_code", "") or mat.get("materialCode", "")).strip()
            mat_path = f"{prefix}.material_requirements[{mat_idx}]"

            # Material code validation
            if mat_code:
                if not settings.registry_materials_live:
                    # Interim: enum membership check
                    if mat_code not in CANONICAL_MATERIAL_CODES:
                        issues.append(
                            LinkageIssue(
                                severity="warning",
                                task_template_id=task_id,
                                path=f"{mat_path}.material_code",
                                code="PS-WRN-02",
                                message=f"Materials registry not live; material_code '{mat_code}' cannot be FK-validated",
                                details={
                                    "material_code": mat_code,
                                    "registry": "materials",
                                    "reason": "registry_not_live",
                                },
                            )
                        )
                else:
                    # M22 live but sync path — use enum check as fallback
                    if mat_code not in CANONICAL_MATERIAL_CODES:
                        issues.append(
                            LinkageIssue(
                                severity="blocker",
                                task_template_id=task_id,
                                path=f"{mat_path}.material_code",
                                code="PS-BLK-11",
                                message=f"Material code '{mat_code}' not found in Materials Registry",
                                details={"material_code": mat_code, "reason": "not_found"},
                            )
                        )

            # Quantity validation (always, regardless of config)
            has_formula = bool(mat.get("quantity_formula"))
            has_static = mat.get("quantity_static") is not None or mat.get("quantity") is not None

            # XOR check: exactly one of quantity_formula / quantity_static
            if has_formula and has_static:
                static_val = mat.get("quantity_static") if mat.get("quantity_static") is not None else mat.get("quantity")
                if static_val is not None and static_val != 0:
                    issues.append(
                        LinkageIssue(
                            severity="blocker",
                            task_template_id=task_id,
                            path=f"{mat_path}",
                            code="PS-BLK-13",
                            message=f"Material entry has both quantity_formula and quantity_static (XOR violation)",
                            details={"material_code": mat_code, "reason": "quantity_xor_violation"},
                        )
                    )

            # Static quantity > 0 check
            if has_static and not has_formula:
                qty = mat.get("quantity_static") if mat.get("quantity_static") is not None else mat.get("quantity")
                if qty is not None:
                    try:
                        qty_val = float(qty)
                        if qty_val <= 0:
                            issues.append(
                                LinkageIssue(
                                    severity="blocker",
                                    task_template_id=task_id,
                                    path=f"{mat_path}.quantity",
                                    code="PS-BLK-14",
                                    message=f"Material quantity must be > 0 (got {qty_val})",
                                    details={"material_code": mat_code, "quantity": qty_val, "reason": "non_positive"},
                                )
                            )
                    except (TypeError, ValueError):
                        pass

        return issues