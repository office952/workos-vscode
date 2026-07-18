/**
 * Typed SVG support selection → finish_setup / mounting_solution wiring.
 * Inactive role ⇒ zero casing leakage.
 */

import type { ClosedContourCandidate } from "./closedContourTypes";
import type {
  AlucobondCasingProfile,
  ContourRoleOption,
  SvgSupportSelectionState,
} from "./closedContourTypes";

export const SVG_SUPPORT_SELECTION_SCHEMA = "svg_support_selection_v1" as const;
export const ACM_BOXED_MOUNTING_TEMPLATE_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";

export function emptySvgSupportSelection(): SvgSupportSelectionState {
  return {
    schema: SVG_SUPPORT_SELECTION_SCHEMA,
    status: "none",
    role: null,
    contour_id: null,
    svg_support_element_id: null,
    geometry_hash: null,
    svg_source_hash: null,
    panel_geometry: null,
    casing_profile: null,
    service_corner: null,
    internal_frame_enabled: false,
    candidate_explanation: [],
    unit_ambiguity: false,
    confirmed_at: null,
  };
}

export function isAlucobondCasedRole(role: ContourRoleOption | null | undefined): boolean {
  return role === "ALUCOBOND_CASED_PANEL";
}

export function buildCasingProfile(args: {
  fold_count: 1 | 2;
  l1_mm: number;
  l2_mm?: number | null;
}): AlucobondCasingProfile {
  const l1 = Number(args.l1_mm);
  const fold = args.fold_count;
  const l2 = fold === 2 ? Number(args.l2_mm ?? NaN) : null;
  return {
    fold_count: fold,
    l1_mm: l1,
    l2_mm: fold === 2 ? l2 : null,
    // Authority: finished depth = L1 for this product path (no dual truth).
    finished_depth_mm: l1,
  };
}

export function validateCasingProfile(profile: AlucobondCasingProfile | null): string[] {
  const blockers: string[] = [];
  if (!profile) {
    blockers.push("Profilul de casetare lipsește.");
    return blockers;
  }
  if (profile.fold_count !== 1 && profile.fold_count !== 2) {
    blockers.push("Numărul de întoarceri trebuie să fie 1 sau 2.");
  }
  if (!(profile.l1_mm > 0)) {
    blockers.push("Prima întoarcere (L1) trebuie să fie > 0.");
  }
  if (profile.fold_count === 2 && !(profile.l2_mm != null && profile.l2_mm > 0)) {
    blockers.push("A doua întoarcere (L2) este obligatorie pentru 2 întoarceri.");
  }
  if (profile.fold_count === 1 && profile.l2_mm != null && profile.l2_mm !== 0) {
    blockers.push("L2 trebuie să lipsească pentru 1 întoarcere.");
  }
  if (profile.finished_depth_mm !== profile.l1_mm) {
    blockers.push("Adâncimea casetei trebuie să coincidă cu L1.");
  }
  return blockers;
}

export function blankPreviewMm(args: {
  width_mm: number;
  height_mm: number;
  fold_count: 1 | 2;
  l1_mm: number;
  l2_mm: number | null;
}): { blank_width_mm: number; blank_height_mm: number; fold_sum_mm: number } {
  const foldSum = args.fold_count === 2 ? args.l1_mm + Number(args.l2_mm ?? 0) : args.l1_mm;
  return {
    fold_sum_mm: foldSum,
    blank_width_mm: args.width_mm + 2 * foldSum,
    blank_height_mm: args.height_mm + 2 * foldSum,
  };
}

export function confirmAlucobondSelection(args: {
  candidate: ClosedContourCandidate;
  svg_source_hash: string;
  fold_count: 1 | 2;
  l1_mm: number;
  l2_mm?: number | null;
  service_corner: SvgSupportSelectionState["service_corner"];
  internal_frame_enabled: boolean;
  unit_ambiguity: boolean;
}): { selection: SvgSupportSelectionState; blockers: string[] } {
  const casing_profile = buildCasingProfile({
    fold_count: args.fold_count,
    l1_mm: args.l1_mm,
    l2_mm: args.l2_mm,
  });
  const blockers = [
    ...validateCasingProfile(casing_profile),
  ];
  if (!(args.candidate.width_mm > 0) || !(args.candidate.height_mm > 0)) {
    blockers.push("Geometria panoului este invalidă.");
  }
  if (!(args.candidate.area_mm2 > 0) || !(args.candidate.perimeter_mm > 0)) {
    blockers.push("Aria/perimetrul panoului sunt invalide.");
  }
  if (blockers.length > 0) {
    return { selection: emptySvgSupportSelection(), blockers };
  }
  return {
    blockers: [],
    selection: {
      schema: SVG_SUPPORT_SELECTION_SCHEMA,
      status: "confirmed",
      role: "ALUCOBOND_CASED_PANEL",
      contour_id: args.candidate.contour_id,
      svg_support_element_id: args.candidate.element_id,
      geometry_hash: args.candidate.geometry_hash,
      svg_source_hash: args.svg_source_hash,
      panel_geometry: {
        width_mm: args.candidate.width_mm,
        height_mm: args.candidate.height_mm,
        area_mm2: args.candidate.area_mm2,
        perimeter_mm: args.candidate.perimeter_mm,
        geometry_hash: args.candidate.geometry_hash,
      },
      casing_profile,
      service_corner: args.service_corner,
      internal_frame_enabled: args.internal_frame_enabled,
      candidate_explanation: args.candidate.reasons,
      unit_ambiguity: args.unit_ambiguity,
      confirmed_at: new Date().toISOString(),
    },
  };
}

export function reconcileSelectionAfterReanalysis(args: {
  previous: SvgSupportSelectionState | null | undefined;
  current_svg_source_hash: string;
  candidates: ClosedContourCandidate[];
}): SvgSupportSelectionState {
  const prev = args.previous && prevHasSchema(args.previous) ? args.previous : emptySvgSupportSelection();
  if (prev.status === "none" || !prev.contour_id || !prev.geometry_hash) {
    return emptySvgSupportSelection();
  }
  if (prev.svg_source_hash && prev.svg_source_hash !== args.current_svg_source_hash) {
    return { ...prev, status: "reconfirm_required" };
  }
  const match = args.candidates.find(
    (c) => c.contour_id === prev.contour_id && c.geometry_hash === prev.geometry_hash,
  );
  if (!match) {
    return { ...prev, status: "reconfirm_required" };
  }
  return prev;
}

function prevHasSchema(value: SvgSupportSelectionState): boolean {
  return value.schema === SVG_SUPPORT_SELECTION_SCHEMA;
}

/**
 * Maps confirmed Alucobond selection into mounting_solution configuration
 * using existing ACM boxed fields (return_depth_mm=L1, rear_lip_mm=L2).
 */
export function buildAcmMountingSolutionFromSelection(
  selection: SvgSupportSelectionState,
): Record<string, unknown> | null {
  if (!isAlucobondCasedRole(selection.role) || selection.status !== "confirmed") {
    return null;
  }
  if (!selection.panel_geometry || !selection.casing_profile) return null;
  const fold = selection.casing_profile.fold_count;
  return {
    kind: "product_system_template",
    template_code: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    configuration: {
      panel_width_mm: selection.panel_geometry.width_mm,
      panel_height_mm: selection.panel_geometry.height_mm,
      return_depth_mm: selection.casing_profile.l1_mm,
      rear_lip_mm: fold === 2 ? selection.casing_profile.l2_mm ?? 0 : 0,
      fold_count: fold,
      finished_depth_mm: selection.casing_profile.finished_depth_mm,
      svg_support_element_id: selection.svg_support_element_id,
      geometry_hash: selection.geometry_hash,
      contour_id: selection.contour_id,
      panel_area_mm2: selection.panel_geometry.area_mm2,
      panel_perimeter_mm: selection.panel_geometry.perimeter_mm,
      internal_frame_enabled: selection.internal_frame_enabled,
      // Legacy frame_clearance_mm is not fit-allowance authority (OWNER: fixed 2 mm total).
      frame_clearance_mm: 0,
      internal_frame: {
        enabled: selection.internal_frame_enabled,
        total_fit_allowance_mm: 2,
        confirmation_status: selection.internal_frame_enabled ? "INCOMPLETE" : "NOT_APPLICABLE",
      },
      acm_thickness_mm: 3,
      fold_sides: "all",
      v_groove_angle_deg: 135,
    },
  };
}

export function readSvgSupportSelection(finish: Record<string, unknown> | null | undefined): SvgSupportSelectionState {
  if (!finish || typeof finish !== "object") return emptySvgSupportSelection();
  const raw = finish.svg_support_selection;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return emptySvgSupportSelection();
  const s = raw as Partial<SvgSupportSelectionState>;
  if (s.schema !== SVG_SUPPORT_SELECTION_SCHEMA) return emptySvgSupportSelection();
  return {
    ...emptySvgSupportSelection(),
    ...s,
    schema: SVG_SUPPORT_SELECTION_SCHEMA,
  } as SvgSupportSelectionState;
}

/** Inactive isolation: non-Alucobond roles produce zero casing requirements. */
export function casingRequirementsActive(selection: SvgSupportSelectionState | null | undefined): boolean {
  return Boolean(
    selection &&
      selection.status === "confirmed" &&
      isAlucobondCasedRole(selection.role),
  );
}
