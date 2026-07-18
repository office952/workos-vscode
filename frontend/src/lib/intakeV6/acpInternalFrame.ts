/**
 * ACP internal frame — client helpers mirroring OWNER_CONFIRMED domain rules.
 * Authority for persistence remains backend normalize; UI displays / proposes only.
 */

export const STRUCTURAL_RO_REGISTRY_VERSION = "structural_resource_options/v1";
export const ACM_BOXED_MOUNTING_TEMPLATE_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
export const MAT_STRUCT_STEEL = "MAT-STRUCT-STEEL";
export const MAT_STRUCT_ALUMINIUM = "MAT-STRUCT-ALUMINIUM";
export const TOTAL_FIT_ALLOWANCE_MM = 2;
export const CROSSBAR_SPACING_STEEL_MM = 1000;
export const CROSSBAR_SPACING_ALUMINIUM_MM = 750;

export type CrossbarOrientation = "VERTICAL" | "HORIZONTAL";

export type InternalFrameConfig = {
  enabled: boolean;
  material_code: string | null;
  profile_code: string | null;
  panel_outer_width_mm: number | null;
  panel_outer_height_mm: number | null;
  panel_material_thickness_mm: number | null;
  total_fit_allowance_mm: number;
  frame_outer_width_mm: number | null;
  frame_outer_height_mm: number | null;
  crossbar_rule_code: string;
  max_crossbar_spacing_mm: number | null;
  crossbar_orientation: CrossbarOrientation | null;
  suggested_crossbar_count: number | null;
  confirmed_crossbar_count: number | null;
  override_reason: string | null;
  structural_review_required: boolean;
  confirmation_status: string;
  quantity_status?: string;
  blockers?: string[];
  provenance?: Record<string, unknown>;
};

export function computeFrameOuterDimensions(args: {
  panelOuterWidthMm: number;
  panelOuterHeightMm: number;
  panelMaterialThicknessMm: number;
  totalFitAllowanceMm?: number;
}): { frameOuterWidthMm: number; frameOuterHeightMm: number; valid: boolean } {
  const fit = args.totalFitAllowanceMm ?? TOTAL_FIT_ALLOWANCE_MM;
  const w = args.panelOuterWidthMm - 2 * args.panelMaterialThicknessMm - fit;
  const h = args.panelOuterHeightMm - 2 * args.panelMaterialThicknessMm - fit;
  return {
    frameOuterWidthMm: w,
    frameOuterHeightMm: h,
    valid: w > 0 && h > 0 && args.panelMaterialThicknessMm > 0,
  };
}

export function maxCrossbarSpacingMm(materialCode: string | null | undefined): number | null {
  if (materialCode === MAT_STRUCT_STEEL) return CROSSBAR_SPACING_STEEL_MM;
  if (materialCode === MAT_STRUCT_ALUMINIUM) return CROSSBAR_SPACING_ALUMINIUM_MM;
  return null;
}

export function suggestCrossbarCount(lengthMm: number, maxSpacingMm: number): number {
  if (!(lengthMm > 0) || !(maxSpacingMm > 0)) return 0;
  const spans = Math.ceil(lengthMm / maxSpacingMm);
  return Math.max(0, spans - 1);
}

export function emptyInternalFrame(): InternalFrameConfig {
  return {
    enabled: false,
    material_code: null,
    profile_code: null,
    panel_outer_width_mm: null,
    panel_outer_height_mm: null,
    panel_material_thickness_mm: null,
    total_fit_allowance_mm: TOTAL_FIT_ALLOWANCE_MM,
    frame_outer_width_mm: null,
    frame_outer_height_mm: null,
    crossbar_rule_code: "MATERIAL_SPACING_V1",
    max_crossbar_spacing_mm: null,
    crossbar_orientation: null,
    suggested_crossbar_count: null,
    confirmed_crossbar_count: null,
    override_reason: null,
    structural_review_required: false,
    confirmation_status: "NOT_APPLICABLE",
    blockers: [],
    provenance: { resource_registry_version: STRUCTURAL_RO_REGISTRY_VERSION },
  };
}

export function proposeInternalFrame(args: {
  enabled: boolean;
  materialCode?: string | null;
  profileCode?: string | null;
  panelWidthMm: number;
  panelHeightMm: number;
  panelThicknessMm: number;
  orientation?: CrossbarOrientation | null;
  confirmedCrossbarCount?: number | null;
  overrideReason?: string | null;
}): InternalFrameConfig {
  if (!args.enabled) return emptyInternalFrame();
  const dims = computeFrameOuterDimensions({
    panelOuterWidthMm: args.panelWidthMm,
    panelOuterHeightMm: args.panelHeightMm,
    panelMaterialThicknessMm: args.panelThicknessMm,
  });
  const spacing = maxCrossbarSpacingMm(args.materialCode);
  const orientation = args.orientation ?? null;
  const axisLength =
    orientation === "VERTICAL"
      ? dims.frameOuterWidthMm
      : orientation === "HORIZONTAL"
        ? dims.frameOuterHeightMm
        : null;
  const suggested =
    spacing != null && axisLength != null ? suggestCrossbarCount(axisLength, spacing) : null;
  const blockers: string[] = [];
  if (!args.materialCode) blockers.push("internal_frame_material_missing");
  // Profiles empty in V1 until owner confirms — always gate complete confirmation.
  blockers.push("internal_frame_profile_catalog_empty");
  if (!args.profileCode) blockers.push("internal_frame_profile_missing");
  if (!orientation) blockers.push("internal_frame_crossbar_unconfirmed");
  if (args.confirmedCrossbarCount == null) blockers.push("internal_frame_crossbar_unconfirmed");
  if (
    suggested != null &&
    args.confirmedCrossbarCount != null &&
    args.confirmedCrossbarCount !== suggested &&
    !args.overrideReason
  ) {
    blockers.push("internal_frame_crossbar_override_reason_required");
  }
  return {
    enabled: true,
    material_code: args.materialCode ?? null,
    profile_code: args.profileCode ?? null,
    panel_outer_width_mm: args.panelWidthMm,
    panel_outer_height_mm: args.panelHeightMm,
    panel_material_thickness_mm: args.panelThicknessMm,
    total_fit_allowance_mm: TOTAL_FIT_ALLOWANCE_MM,
    frame_outer_width_mm: dims.frameOuterWidthMm,
    frame_outer_height_mm: dims.frameOuterHeightMm,
    crossbar_rule_code: "MATERIAL_SPACING_V1",
    max_crossbar_spacing_mm: spacing,
    crossbar_orientation: orientation,
    suggested_crossbar_count: suggested,
    confirmed_crossbar_count: args.confirmedCrossbarCount ?? null,
    override_reason: args.overrideReason ?? null,
    structural_review_required: false,
    confirmation_status: blockers.length ? "INCOMPLETE" : "CONFIRMED",
    quantity_status: "GUARDED",
    blockers,
    provenance: {
      source: "INTAKE_STEP_2",
      resource_registry_version: STRUCTURAL_RO_REGISTRY_VERSION,
    },
  };
}
