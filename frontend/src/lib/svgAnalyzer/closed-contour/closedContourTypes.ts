/**
 * Closed-contour candidates for operator panel selection.
 * Analyzer proposes; operator confirms. Not commercial / tasking authority.
 */

export type ClosedContourSourceType =
  | "path_subpath"
  | "path"
  | "polygon"
  | "rect"
  | "circle"
  | "ellipse"
  | "polyline_closed";

export type ClosureMethod =
  | "explicit_z"
  | "geometric_endpoints"
  | "primitive_closed"
  | "polygon"
  | "polyline_endpoints";

export type ContourRoleOption =
  | "ALUCOBOND_CASED_PANEL"
  | "FLAT_BACKGROUND"
  | "DECORATIVE_CONTOUR"
  | "GRAPHIC_ELEMENT"
  | "IGNORE";

export interface ClosedContourBBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ClosedContourCandidate {
  /** Stable across reanalysis of the same geometry (primary identity). */
  contour_id: string;
  element_id: string;
  source_element_type: ClosedContourSourceType;
  source_index: number;
  source_subpath_index: number | null;
  is_closed: true;
  closure_method: ClosureMethod;
  geometry_hash: string;
  bbox: ClosedContourBBox;
  width_mm: number;
  height_mm: number;
  area_mm2: number;
  perimeter_mm: number;
  centroid: { x: number; y: number };
  orientation: "landscape" | "portrait" | "square";
  contains_count: number;
  contained_area_ratio: number;
  is_outer_candidate: boolean;
  rectangularity_score: number;
  confidence: number;
  reasons: string[];
  warnings: string[];
  /** Path data or points used for overlay (display only; never written back to SVG). */
  overlay_d?: string | null;
  overlay_points?: string | null;
}

export interface ClosedContourDetectionReport {
  schema: "closed_contour_candidates_v1";
  candidate_count: number;
  closed_contour_count: number;
  unit_ambiguity: boolean;
  mm_per_vbu_used: number;
  mm_per_vbu_raw: number;
  scale_correction: "none" | "viewbox_as_mm_corel_cm_guard";
  warnings: string[];
  candidates: ClosedContourCandidate[];
}

export interface AlucobondCasingProfile {
  fold_count: 1 | 2;
  l1_mm: number;
  l2_mm: number | null;
  finished_depth_mm: number;
}

export interface AlucobondPanelGeometry {
  width_mm: number;
  height_mm: number;
  area_mm2: number;
  perimeter_mm: number;
  geometry_hash: string;
}

export type SvgSupportSelectionStatus =
  | "none"
  | "proposed"
  | "confirmed"
  | "reconfirm_required";

export interface SvgSupportSelectionState {
  schema: "svg_support_selection_v1";
  status: SvgSupportSelectionStatus;
  role: ContourRoleOption | null;
  contour_id: string | null;
  svg_support_element_id: string | null;
  geometry_hash: string | null;
  svg_source_hash: string | null;
  panel_geometry: AlucobondPanelGeometry | null;
  casing_profile: AlucobondCasingProfile | null;
  service_corner: "TOP_LEFT" | "TOP_RIGHT" | "BOTTOM_LEFT" | "BOTTOM_RIGHT" | null;
  internal_frame_enabled: boolean;
  candidate_explanation: string[];
  unit_ambiguity: boolean;
  confirmed_at: string | null;
  /** Optional authority axes — catalog defaults are never operator_confirmed. */
  field_authority?: Record<string, string>;
  field_class?: Record<string, string>;
  association_status?: "unconfirmed" | "proposed" | "confirmed" | "unknown";
  technical_configuration_status?: "unconfirmed" | "proposed" | "confirmed" | "unknown";
}
