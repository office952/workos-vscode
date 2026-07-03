from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_blueprint_dossier import ProductBlueprintDossier
from models.inventory_materials import Inventory_materials
from models.product_templates import Product_templates
from services.volumetric_vector_readiness_policy import (
    evaluate_volumetric_vector_readiness,
)
from services.volumetric_material_rate_resolver import (
    PROFILE_DEPTH_VARIANT_CODES,
    PSU_WATTAGE_VARIANT_CODES,
    READINESS_BLOCKER_PSU_VARIANT_INCOMPLETE,
    READINESS_BLOCKER_VARIANT_INCOMPLETE,
    READINESS_WARNING_PSU_VARIANT_PRICING_READY,
    READINESS_WARNING_VARIANT_PRICING_READY,
    TEMPLATE_PROFILE_CODE,
    TEMPLATE_PSU_CODE,
    evaluate_profile_depth_variant_registry,
    evaluate_psu_wattage_variant_registry,
    is_volumetric_template_code,
)


@dataclass
class ReadinessSection:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ReadinessPolicy:
    authority: str = "backend"
    compute_mode: str = "read_only"
    quote_gate: str = "enforced"
    order_snapshot: str = "quote_snapshot_frozen"
    requires_warning_acknowledgement: bool = True


@dataclass
class ProductReadinessResult:
    entity_type: str
    entity_id: str
    blueprint_id: str
    overall_status: str
    ready_for_quote: bool
    technical_readiness: ReadinessSection
    costengine_readiness: ReadinessSection
    document_output_readiness: ReadinessSection
    visual_prompt_readiness: ReadinessSection
    execution_preparation_readiness: ReadinessSection
    policy: ReadinessPolicy = field(default_factory=ReadinessPolicy)
    source: str = "backend"
    contract_version: str = "2026-05-15"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Valid caps spacings (canonical rule — banner & mesh)
# ---------------------------------------------------------------------------
VALID_CAPS_SPACINGS_CM = {15, 30, 50, 75, 100}

# Banner roll widths (canonical rule)
BANNER_ROLL_WIDTHS_MM = {1100, 1350, 1600}


class ProductReadinessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _parse_json(raw: str | None) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    @staticmethod
    def _section_status(blockers: list[str], warnings: list[str]) -> str:
        if blockers:
            return "blocked"
        if warnings:
            return "needs_review"
        return "ready"

    @staticmethod
    def _has_short_description(output_blocks: Any) -> bool:
        if isinstance(output_blocks, dict):
            short = output_blocks.get("short_description")
            return isinstance(short, str) and bool(short.strip())
        if isinstance(output_blocks, list):
            for row in output_blocks:
                if isinstance(row, dict):
                    if str(row.get("type") or "").strip().lower() in {"short_description", "summary"}:
                        text = str(row.get("text") or row.get("value") or "").strip()
                        if text:
                            return True
        return False

    @staticmethod
    def _extract_component_types(components: Any) -> set[str]:
        """Extract unique component types from components_json."""
        types: set[str] = set()
        if isinstance(components, list):
            for c in components:
                if isinstance(c, dict):
                    t = str(c.get("type") or "").strip()
                    if t:
                        types.add(t)
        return types

    @staticmethod
    def _extract_material_codes(materials: Any) -> set[str]:
        """Extract unique material codes from required_materials_json."""
        codes: set[str] = set()
        if isinstance(materials, list):
            for m in materials:
                if isinstance(m, dict):
                    code = str(
                        m.get("materialCode") or m.get("material_code") or ""
                    ).strip()
                    if code:
                        codes.add(code)
        return codes

    @staticmethod
    def _extract_material_codes_from_components(components: Any) -> set[str]:
        """Extract unique material codes from components_json nested materials."""
        codes: set[str] = set()
        if isinstance(components, list):
            for component in components:
                if not isinstance(component, dict):
                    continue
                nested_materials = component.get("materials")
                if not isinstance(nested_materials, list):
                    continue
                for material in nested_materials:
                    if not isinstance(material, dict):
                        continue
                    code = str(
                        material.get("materialCode")
                        or material.get("material_code")
                        or ""
                    ).strip()
                    if code:
                        codes.add(code)
        return codes

    @staticmethod
    def _extract_workcenter_codes(operations: Any) -> set[str]:
        """Extract quote-priced workcenter codes from operations_json."""
        from services.template_operation_policy import is_quote_priced_operation

        codes: set[str] = set()
        if isinstance(operations, list):
            for op in operations:
                if isinstance(op, dict) and is_quote_priced_operation(op):
                    wc = str(op.get("workcenter") or "").strip()
                    if wc:
                        codes.add(wc)
        return codes

    @staticmethod
    def _has_formula_param(materials: Any, param_key: str) -> bool:
        """Check if any material has a specific formula_params key."""
        if isinstance(materials, list):
            for m in materials:
                if isinstance(m, dict):
                    fp = m.get("formula_params")
                    if isinstance(fp, dict) and param_key in fp:
                        return True
        return False

    # ------------------------------------------------------------------
    # Template-specific readiness checks (BUILD 4)
    # ------------------------------------------------------------------
    def _check_banner_readiness(
        self,
        template: Any,
        components: Any,
        materials: Any,
        operations: Any,
    ) -> tuple[list[str], list[str]]:
        """Banner-specific blockers and warnings."""
        blockers: list[str] = []
        warnings: list[str] = []

        mat_codes = self._extract_material_codes(materials)
        wc_codes = self._extract_workcenter_codes(operations)

        # Must have banner material
        banner_mats = {c for c in mat_codes if "BANNER" in c.upper()}
        if not banner_mats:
            blockers.append("banner_material_missing")

        # Must have roll width mapping in formula params
        if not self._has_formula_param(materials, "roll_widths_mm"):
            warnings.append("banner_roll_width_mapping_missing")

        # Must have print work center
        if "LARGE_FORMAT_PRINT" not in wc_codes:
            blockers.append("banner_print_workcenter_missing")

        # Must have finishing operation
        finishing_wcs = {"WELDING_BANNER", "CAPSARE", "FINISHING"}
        if not finishing_wcs.intersection(wc_codes):
            blockers.append("banner_finishing_operation_missing")

        # Caps spacing validation (check formula_params)
        if isinstance(materials, list):
            for m in materials:
                if isinstance(m, dict):
                    fp = m.get("formula_params", {})
                    if isinstance(fp, dict) and "valid_spacings_cm" in fp:
                        spacings = fp["valid_spacings_cm"]
                        if isinstance(spacings, list):
                            invalid = [s for s in spacings if s not in VALID_CAPS_SPACINGS_CM]
                            if invalid:
                                blockers.append(f"banner_invalid_caps_spacing:{invalid}")

        return blockers, warnings

    def _check_plexi_readiness(
        self,
        template: Any,
        components: Any,
        materials: Any,
        operations: Any,
    ) -> tuple[list[str], list[str]]:
        """Plexiglass-specific blockers and warnings."""
        blockers: list[str] = []
        warnings: list[str] = []

        mat_codes = self._extract_material_codes(materials)
        wc_codes = self._extract_workcenter_codes(operations)

        # Must have plexiglass material
        plexi_mats = {c for c in mat_codes if "PLEXI" in c.upper()}
        if not plexi_mats:
            blockers.append("plexi_sheet_material_missing")

        # Must have thickness mapping
        if not self._has_formula_param(materials, "thickness_options_mm"):
            warnings.append("plexi_thickness_mapping_missing")

        # Must have cutting work center
        cutting_wcs = {"LASER_CUTTING", "CNC_ROUTER", "PANEL_CUTTING"}
        if not cutting_wcs.intersection(wc_codes):
            blockers.append("plexi_cutting_workcenter_missing")

        return blockers, warnings

    def _check_vinyl_readiness(
        self,
        template: Any,
        components: Any,
        materials: Any,
        operations: Any,
    ) -> tuple[list[str], list[str]]:
        """Vinyl/sticker-specific blockers and warnings."""
        blockers: list[str] = []
        warnings: list[str] = []

        mat_codes = self._extract_material_codes(materials)
        wc_codes = self._extract_workcenter_codes(operations)

        # Must have vinyl material
        vinyl_mats = {c for c in mat_codes if "VINYL" in c.upper()}
        if not vinyl_mats:
            blockers.append("vinyl_material_missing")

        # Must have print work center
        if "LARGE_FORMAT_PRINT" not in wc_codes:
            blockers.append("vinyl_print_workcenter_missing")

        # Lamination dependency: if lamination material exists, lamination WC must too
        lam_mats = {c for c in mat_codes if "LAMINARE" in c.upper()}
        if lam_mats and "LAMINATION" not in wc_codes:
            blockers.append("vinyl_lamination_workcenter_missing")

        # Contour cut: if contour cutting operation exists, vector path warning
        if "CONTOUR_CUTTING" in wc_codes:
            warnings.append("vinyl_contour_cut_requires_vector_path")

        return blockers, warnings

    def _check_lightbox_readiness(
        self,
        template: Any,
        components: Any,
        materials: Any,
        operations: Any,
    ) -> tuple[list[str], list[str]]:
        """Lightbox-specific blockers and warnings."""
        blockers: list[str] = []
        warnings: list[str] = []

        mat_codes = self._extract_material_codes(materials)
        wc_codes = self._extract_workcenter_codes(operations)
        comp_types = self._extract_component_types(components)

        # Must have frame profile material
        frame_mats = {c for c in mat_codes if "PROFIL" in c.upper()}
        if not frame_mats:
            blockers.append("lightbox_frame_profile_missing")

        # Must have face material
        face_mats = {c for c in mat_codes if "POLICARBONAT" in c.upper() or "PLEXI" in c.upper()}
        if not face_mats:
            blockers.append("lightbox_face_material_missing")

        # Must have LED material
        led_mats = {c for c in mat_codes if "LED" in c.upper()}
        if not led_mats:
            blockers.append("lightbox_led_material_missing")

        # Must have power supply rule
        psu_mats = {c for c in mat_codes if "PSU" in c.upper()}
        if not psu_mats:
            blockers.append("lightbox_power_supply_rule_missing")

        # Must have electrical work center
        if "ELECTRICAL_WIRING" not in wc_codes and "LED_ASSEMBLY" not in wc_codes:
            blockers.append("lightbox_electrical_workcenter_missing")

        return blockers, warnings

    def _check_volumetric_letters_readiness(
        self,
        template: Any,
        components: Any,
        materials: Any,
        operations: Any,
        product_spec: dict[str, Any] | None = None,
    ) -> tuple[list[str], list[str]]:
        """Volumetric letters-specific blockers and warnings."""
        blockers: list[str] = []
        warnings: list[str] = []

        mat_codes = self._extract_material_codes(materials)
        wc_codes = self._extract_workcenter_codes(operations)

        # Must have face material
        face_mats = {c for c in mat_codes if "FATA" in c.upper() or "ACP" in c.upper()}
        if not face_mats:
            blockers.append("letters_face_material_missing")

        # Must have lateral profile
        lateral_mats = {c for c in mat_codes if "LATERAL" in c.upper() or "PROFIL" in c.upper()}
        if not lateral_mats:
            blockers.append("letters_lateral_profile_missing")

        vector_result = evaluate_volumetric_vector_readiness(
            product_spec,
            template_level=product_spec is None,
        )
        warnings.extend(vector_result.warnings)
        blockers.extend(vector_result.blockers)
        if product_spec is not None and not vector_result.vector_gate_satisfied:
            for code in vector_result.warnings:
                if code in {
                    "letters_vector_file_required",
                    "vector_layer_mapping_pending",
                    "vector_manual_review_required",
                    "vector_analysis_failed",
                    "vector_layer_mapping_failed",
                }:
                    blockers.append(code)
            if not vector_result.vector_gate_satisfied and not any(
                b in blockers
                for b in (
                    "letters_vector_file_required",
                    "vector_layer_mapping_pending",
                    "vector_manual_review_required",
                )
            ):
                blockers.append("vector_gate_not_satisfied")

        # CNC/laser work center required
        cutting_wcs = {"CNC_ROUTER", "LASER_CUTTING"}
        if not cutting_wcs.intersection(wc_codes):
            blockers.append("letters_cnc_laser_workcenter_missing")

        # If LED components exist, check LED materials
        led_ops = {wc for wc in wc_codes if "LED" in wc.upper()}
        if led_ops:
            led_mats = {c for c in mat_codes if "LED" in c.upper()}
            if not led_mats:
                warnings.append("letters_illumination_led_mapping_missing")

        return blockers, warnings

    def _check_mesh_readiness(
        self,
        template: Any,
        components: Any,
        materials: Any,
        operations: Any,
    ) -> tuple[list[str], list[str]]:
        """Mesh externalized-specific blockers and warnings."""
        blockers: list[str] = []
        warnings: list[str] = []

        wc_codes = self._extract_workcenter_codes(operations)

        # Mesh MUST be externalized — check for EXTERNAL_SUBCONTRACT
        if "EXTERNAL_SUBCONTRACT" not in wc_codes:
            blockers.append("mesh_external_supplier_path_missing")

        # External supplier quote required
        warnings.append("mesh_requires_supplier_quote")

        # Mesh is NOT ready for internal production
        warnings.append("mesh_not_for_internal_production")

        # Caps spacing validation (same as banner)
        if isinstance(materials, list):
            for m in materials:
                if isinstance(m, dict):
                    fp = m.get("formula_params", {})
                    if isinstance(fp, dict) and "valid_spacings_cm" in fp:
                        spacings = fp["valid_spacings_cm"]
                        if isinstance(spacings, list):
                            invalid = [s for s in spacings if s not in VALID_CAPS_SPACINGS_CM]
                            if invalid:
                                blockers.append(f"mesh_invalid_caps_spacing:{invalid}")

        return blockers, warnings

    def _apply_template_specific_checks(
        self,
        template: Any,
        components: Any,
        materials: Any,
        operations: Any,
        product_spec: dict[str, Any] | None = None,
    ) -> tuple[list[str], list[str]]:
        """Dispatch template-specific readiness checks based on template_code."""
        code = str(getattr(template, "template_code", "") or "").strip().upper()

        if "BANNER" in code:
            return self._check_banner_readiness(template, components, materials, operations)
        elif "PLEXI" in code:
            return self._check_plexi_readiness(template, components, materials, operations)
        elif "VINYL" in code or "STICKER" in code:
            return self._check_vinyl_readiness(template, components, materials, operations)
        elif "LIGHTBOX" in code or "CASETA" in code:
            return self._check_lightbox_readiness(template, components, materials, operations)
        elif "VOLUMETRIC" in code or "LITERE" in code:
            return self._check_volumetric_letters_readiness(
                template, components, materials, operations, product_spec=product_spec,
            )
        elif "MESH" in code:
            return self._check_mesh_readiness(template, components, materials, operations)

        return [], []

    async def evaluate(
        self,
        template_id: int,
        product_spec: dict[str, Any] | None = None,
    ) -> ProductReadinessResult:
        template = (
            await self.db.execute(select(Product_templates).where(Product_templates.id == template_id).limit(1))
        ).scalars().first()
        if template is None:
            return ProductReadinessResult(
                entity_type="blueprint",
                entity_id=f"blueprint:{template_id}",
                blueprint_id=f"template:{template_id}",
                overall_status="blocked",
                ready_for_quote=False,
                technical_readiness=ReadinessSection(status="blocked", blockers=["template_not_found"], warnings=[]),
                costengine_readiness=ReadinessSection(status="blocked", blockers=["template_not_found"], warnings=[]),
                document_output_readiness=ReadinessSection(status="draft", blockers=[], warnings=["template_not_found"]),
                visual_prompt_readiness=ReadinessSection(status="draft", blockers=[], warnings=["template_not_found"]),
                execution_preparation_readiness=ReadinessSection(status="draft", blockers=[], warnings=["template_not_found"]),
            )

        dossier = (
            await self.db.execute(
                select(ProductBlueprintDossier).where(ProductBlueprintDossier.template_id == template.id).limit(1)
            )
        ).scalars().first()

        # --- Parse JSON fields ---
        components = self._parse_json(template.components_json)
        required_materials = self._parse_json(template.required_materials_json)
        operations = self._parse_json(template.operations_json)

        # --- Technical readiness ---
        technical_blockers: list[str] = []
        technical_warnings: list[str] = []
        if not str(template.template_code or "").strip():
            technical_blockers.append("identity_missing_template_code")
        if not str(template.family_id or "").strip() and not str(template.family_name or "").strip():
            technical_blockers.append("family_missing")
        if template.active is False:
            technical_blockers.append("template_inactive")

        if not isinstance(required_materials, list) or len(required_materials) == 0:
            technical_blockers.append("material_assumptions_missing")

        if not isinstance(operations, list) or len(operations) == 0:
            technical_warnings.append("operations_missing")

        if not isinstance(components, list) or len(components) == 0:
            technical_warnings.append("components_missing")

        if dossier is None:
            technical_warnings.append("blueprint_dossier_missing")
        else:
            if str(dossier.status or "").strip().lower() == "deprecated":
                technical_blockers.append("blueprint_deprecated")

        # --- Template-specific checks (BUILD 4) ---
        tpl_blockers, tpl_warnings = self._apply_template_specific_checks(
            template, components, required_materials, operations, product_spec=product_spec,
        )
        technical_blockers.extend(tpl_blockers)
        technical_warnings.extend(tpl_warnings)

        # --- Registry reference guard (v1.1) ---
        material_codes_flat = self._extract_material_codes(required_materials)
        material_codes_nested = self._extract_material_codes_from_components(components)
        all_material_codes = material_codes_flat.union(material_codes_nested)

        profile_variant_policy_ready = False
        profile_variant_incomplete: list[str] = []
        tpl_code = str(template.template_code or "")
        if (
            TEMPLATE_PROFILE_CODE in all_material_codes
            and is_volumetric_template_code(tpl_code)
        ):
            variant_rows = (
                await self.db.execute(
                    select(Inventory_materials).where(
                        Inventory_materials.code.in_(list(PROFILE_DEPTH_VARIANT_CODES))
                    )
                )
            ).scalars().all()
            profile_variant_policy_ready, profile_variant_incomplete = (
                evaluate_profile_depth_variant_registry(
                    {str(r.code): r for r in variant_rows}
                )
            )

        psu_variant_policy_ready = False
        psu_variant_incomplete: list[str] = []
        if (
            TEMPLATE_PSU_CODE in all_material_codes
            and is_volumetric_template_code(tpl_code)
        ):
            psu_variant_rows = (
                await self.db.execute(
                    select(Inventory_materials).where(
                        Inventory_materials.code.in_(list(PSU_WATTAGE_VARIANT_CODES))
                    )
                )
            ).scalars().all()
            psu_variant_policy_ready, psu_variant_incomplete = (
                evaluate_psu_wattage_variant_registry(
                    {str(r.code): r for r in psu_variant_rows}
                )
            )

        if all_material_codes:
            rows = (
                await self.db.execute(
                    select(Inventory_materials).where(
                        Inventory_materials.code.in_(list(all_material_codes))
                    )
                )
            ).scalars().all()
            by_code = {str(r.code): r for r in rows}

            missing_codes = sorted(all_material_codes.difference(by_code.keys()))
            for code in missing_codes:
                if template.active is True:
                    technical_blockers.append(f"material_registry_missing:{code}")
                else:
                    technical_warnings.append(f"material_registry_missing:{code}")

            for code in sorted(all_material_codes.intersection(by_code.keys())):
                row = by_code[code]
                row_status = str(row.status or "").strip().lower()
                is_price_complete = (
                    row.unit_cost is not None
                    and row.unit_cost > 0
                    and bool(str(row.currency or "").strip())
                    and row.vat_percent is not None
                    and row.valid_from is not None
                )

                if (
                    code == TEMPLATE_PROFILE_CODE
                    and is_volumetric_template_code(tpl_code)
                ):
                    if profile_variant_policy_ready:
                        technical_warnings.append(READINESS_WARNING_VARIANT_PRICING_READY)
                        continue
                    for item in profile_variant_incomplete:
                        technical_blockers.append(
                            f"{READINESS_BLOCKER_VARIANT_INCOMPLETE}:{item}"
                        )

                if (
                    code == TEMPLATE_PSU_CODE
                    and is_volumetric_template_code(tpl_code)
                ):
                    if psu_variant_policy_ready:
                        technical_warnings.append(READINESS_WARNING_PSU_VARIANT_PRICING_READY)
                        continue
                    for item in psu_variant_incomplete:
                        technical_blockers.append(
                            f"{READINESS_BLOCKER_PSU_VARIANT_INCOMPLETE}:{item}"
                        )

                if template.active is True:
                    if row_status != "active":
                        technical_blockers.append(
                            f"active_template_material_not_active:{code}:{row_status or 'unknown'}"
                        )
                    if not is_price_complete:
                        technical_blockers.append(
                            f"active_material_price_incomplete:{code}"
                        )
                else:
                    # Keep non-active template diagnostics as warnings to avoid
                    # forcing activation behavior changes.
                    if row_status == "active" and not is_price_complete:
                        technical_warnings.append(
                            f"active_material_price_incomplete:{code}"
                        )

        technical = ReadinessSection(
            status=self._section_status(technical_blockers, technical_warnings),
            blockers=technical_blockers,
            warnings=technical_warnings,
        )

        # --- CostEngine readiness ---
        cost_blockers: list[str] = []
        cost_warnings: list[str] = []
        if profile_variant_policy_ready:
            cost_warnings.append(
                "volumetric_profile_return_depth_required_at_quote:"
                f"{TEMPLATE_PROFILE_CODE}"
            )
        if psu_variant_policy_ready:
            cost_warnings.append(
                f"volumetric_psu_wattage_required_at_quote:{TEMPLATE_PSU_CODE}"
            )
        if dossier is None:
            cost_warnings.append("costengine_mapping_missing_no_dossier")
        else:
            cost_map = self._parse_json(dossier.costengine_mapping_json)
            if not cost_map:
                cost_blockers.append("costengine_mapping_missing")

        # For templates without dossier, check if materials have formula_params
        # (BUILD 4 templates define cost assumptions inline)
        has_formula_materials = False
        if isinstance(required_materials, list):
            for m in required_materials:
                if isinstance(m, dict) and m.get("calculation_type") == "formula_based":
                    has_formula_materials = True
                    break

        if not has_formula_materials and not dossier:
            cost_blockers.append("costengine_no_formula_or_dossier")

        costengine = ReadinessSection(
            status=self._section_status(cost_blockers, cost_warnings),
            blockers=cost_blockers,
            warnings=cost_warnings,
        )

        # --- Document output readiness ---
        doc_blockers: list[str] = []
        doc_warnings: list[str] = []
        output_blocks = self._parse_json(dossier.output_blocks_json) if dossier else None
        if not output_blocks:
            doc_warnings.append("output_blocks_missing")
        elif not self._has_short_description(output_blocks):
            doc_warnings.append("output_short_description_missing")

        document = ReadinessSection(
            status=self._section_status(doc_blockers, doc_warnings),
            blockers=doc_blockers,
            warnings=doc_warnings,
        )

        # --- Visual prompt readiness ---
        visual_blockers: list[str] = []
        visual_warnings: list[str] = []
        visual_blocks = self._parse_json(dossier.visual_prompt_blocks_json) if dossier else None
        if not visual_blocks:
            visual_warnings.append("visual_prompt_blocks_missing")
        visual = ReadinessSection(
            status=self._section_status(visual_blockers, visual_warnings),
            blockers=visual_blockers,
            warnings=visual_warnings,
        )

        # --- Execution preparation readiness ---
        exec_blockers: list[str] = []
        exec_warnings: list[str] = []
        task_rules = self._parse_json(dossier.task_rules_json) if dossier else None
        if not task_rules:
            exec_warnings.append("task_rules_missing")

        # BUILD 4: Check if operations define a production chain
        if isinstance(operations, list) and len(operations) > 0:
            # Has operations — execution preparation is at least partial
            pass
        else:
            exec_warnings.append("no_operations_for_execution")

        execution = ReadinessSection(
            status=self._section_status(exec_blockers, exec_warnings),
            blockers=exec_blockers,
            warnings=exec_warnings,
        )

        # --- Overall status ---
        statuses = [
            technical.status,
            costengine.status,
            document.status,
            visual.status,
            execution.status,
        ]

        dossier_status = str(dossier.status or "").strip().lower() if dossier else ""

        if "blocked" in statuses or dossier_status in {"blocked", "deprecated"}:
            overall = "blocked"
        elif dossier_status == "draft":
            overall = "draft"
        elif dossier_status == "needs_review":
            overall = "needs_review"
        elif "needs_review" in statuses:
            overall = "needs_review"
        elif dossier is not None and dossier_status != "approved":
            overall = "needs_review"
        else:
            overall = "ready"

        # BUILD 27.09T — quote readiness additionally requires lifecycle approval.
        ready_for_quote = (
            template.active is True
            and dossier_status == "approved"
            and overall == "ready"
        )

        return ProductReadinessResult(
            entity_type="blueprint",
            entity_id=f"blueprint:{template.id}",
            blueprint_id=f"template:{template.id}",
            overall_status=overall,
            ready_for_quote=ready_for_quote,
            technical_readiness=technical,
            costengine_readiness=costengine,
            document_output_readiness=document,
            visual_prompt_readiness=visual,
            execution_preparation_readiness=execution,
        )