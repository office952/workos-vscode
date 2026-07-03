/**
 * Product 001 / litere volumetrice — per-intake customer specification (capture only).
 * Persisted as intake_requests.product_spec_json via the intake CRUD API.
 */

import { normalizeVolumetricIntakeSpecForSave } from "./intakeVolumetricSpec";
import type {
  LetterGroupFinishAssignment,
  SvgArtworkLayerPending,
  SvgLetterGroup,
} from "./intakeSvgContracts";
import type { SvgArtworkFinishAssignment } from "./svgArtworkContracts";
import type { WorkFileAttachment } from "./workFileAttachments";

export type IlluminationType = "frontlit" | "backlit" | "halo" | "non_illuminated";
export type FaceFinish =
  | "plexi"
  | "oracal_651"
  | "oracal_8500_translucent"
  | "print_laminated"
  | "other";
export type IndoorOutdoor = "indoor" | "outdoor";
export type MountingType = "direct_wall" | "premounted";
export type PremountingType = "none" | "metal_structure" | "acm_casetted_panel";
export type PremountBarMaterial = "steel" | "aluminum";
/** Volum aluminiu — colantare înainte de modelare sau vopsire după lipire pe față. */
export type VolumeFinish =
  | "oracal_651_before_forming"
  | "paint_after_face_miter_bond"
  | "none";

export type IntakeCanonicalFaceFinishType =
  | "none"
  | "oracal_651"
  | "oracal_8500"
  | "printed_vinyl"
  | "printed_laminated_vinyl";

export type IntakeCanonicalMountingSystem =
  | "direct_wall"
  | "steel_bars"
  | "aluminum_bars"
  | "acm_panel";

export type PaintFinishType = "matte" | "gloss" | "satin" | "not_specified";
export type FaceVinylFinish = "gloss" | "matte" | "translucent_matte" | "satin";

export interface IntakeProductSpec {
  text?: string;
  font?: string;
  /** Assembly width when known — not invented. */
  width_mm?: number;
  /** Letter / assembly height when known. */
  height_mm?: number;
  letter_height_mm?: number;
  depth_mm?: number;
  return_depth_mm?: number;
  /** Geometry when operator truly has metrics — never auto-derived in intake. */
  letter_face_area_m2?: number;
  letter_perimeter_m?: number;
  letter_count?: number;
  illumination_type?: IlluminationType;
  /** Legacy face finish enum — prefer face_finish_type when set. */
  face_finish?: FaceFinish;
  /** Canonical face finish for quote alignment. */
  face_finish_type?: IntakeCanonicalFaceFinishType;
  face_vinyl_color_code?: string;
  face_vinyl_color_name?: string;
  face_vinyl_roll_width_mm?: 1000 | 1260;
  face_vinyl_finish?: FaceVinylFinish;
  face_vinyl_notes?: string;
  /** Finisaj lateral volum aluminiu (mutually exclusive paths in production). */
  volume_finish?: VolumeFinish;
  /** Legacy RAL text — prefer paint_ral_code when set. */
  ral_color?: string;
  paint_ral_code?: string;
  paint_ral_name?: string;
  paint_finish?: PaintFinishType;
  paint_tube_count?: number;
  selected_psu_watts?: 60 | 100 | 160 | 200;
  lighting_notes?: string;
  indoor_outdoor?: IndoorOutdoor;
  /** Legacy mounting capture — prefer mounting_system when set. */
  mounting_type?: MountingType;
  premounting_type?: PremountingType;
  premount_bar_material?: PremountBarMaterial;
  /** Canonical mounting for quote alignment. */
  mounting_system?: IntakeCanonicalMountingSystem;
  mounting_template_enabled?: boolean;
  mounting_template_material_type?: "none" | "paper" | "forex";
  mounting_template_area_m2?: number;
  mounting_bar_profile?: string;
  mounting_bar_count?: number;
  mounting_bar_length_m?: number;
  mounting_notes?: string;
  backing_chamfer?: boolean;
  back_bevel_enabled?: boolean;
  /** Șanfren vizual — obligatoriu, mereu inclus. */
  visual_chamfer_included?: boolean;
  /** Iluminare față — singura familie pe acest template. */
  illumination_family?: "front_lit";
  /** Fața se colantează? */
  face_vinyl_enabled?: boolean;
  /** @deprecated — mirror of face_vinyl_enabled */
  face_wrap_enabled?: boolean;
  /** Cant aluminiu stoc — alb / negru. */
  return_color?: "white" | "black";
  /** @deprecated — mirror of return_color */
  return_edge_color?: "white" | "black";
  /** Return/cant finish system — standard stock, RAL paint, or Oracal vinyl. */
  return_finish_system?: "standard" | "RAL" | "ORACAL";
  return_ral_code?: string;
  return_ral_name?: string;
  return_ral_preview_hex?: string;
  return_oracal_series?: "651" | "8500";
  return_oracal_code?: string;
  return_oracal_name?: string;
  return_oracal_preview_hex?: string;
  /** Face vinyl series when colantare față is enabled. */
  face_vinyl_series?: "651" | "8500";
  face_vinyl_code?: string;
  face_vinyl_name?: string;
  face_vinyl_preview_hex?: string;
  /** led_modules | led_strip (led_module legacy → led_modules). */
  lighting_system_type?: "led_modules" | "led_strip" | "led_module";
  led_module_power_w?: 0.72 | 1 | 1.44;
  /** @deprecated — mirror of led_module_power_w */
  led_module_wattage?: 0.72 | 1 | 1.44;
  led_strip_density?: "60_led_per_m" | "120_led_per_m" | "60_5w" | "120_10w";
  led_strip_power_w_per_ml?: 5 | 10;
  light_color?: "warm" | "cold";
  /** @deprecated — mirror of light_color (cool = cold) */
  led_color_temperature?: "warm" | "cool";
  total_led_watts?: number;
  required_psu_watts?: number;
  psu_sizing_status?: "ok" | "pending_geometry" | "insufficient_capacity";
  psu_sizing_warning?: string;
  /** V2 planning — auto vs manual PSU pick. */
  psu_selection_mode?: "auto" | "manual";
  /** V2 — ordered PSU units (e.g. [200, 160]). */
  psu_configuration?: Array<60 | 100 | 160 | 200>;
  psu_total_capacity_watts?: number;
  psu_reserve_margin_watts?: number;
  psu_allocation_status?:
    | "ok"
    | "underpowered"
    | "needs_stock_override"
    | "manual_review"
    | "impossible";
  psu_allocation_warning?: string;
  psu_override_reason?: string;
  /** V2 — named lighting circuits / transformer zones. */
  lighting_groups?: Array<{
    id: string;
    label: string;
    estimated_led_watts?: number;
    required_psu_watts?: number;
    psu_selection_mode?: "auto" | "manual";
    assigned_psu_configuration?: Array<60 | 100 | 160 | 200>;
    psu_total_capacity_watts?: number;
    psu_allocation_status?:
      | "ok"
      | "underpowered"
      | "needs_stock_override"
      | "manual_review"
      | "impossible";
    psu_allocation_warning?: string;
    psu_override_reason?: string;
    notes?: string;
  }>;
  lighting_groups_total_watts?: number;
  lighting_groups_total_psu_capacity?: number;
  /** Șanfren pe vizual față — lipire volum aluminiu (mereu true). */
  face_miter_chamfer?: boolean;
  notes?: string;
  /** Vector / production file metadata — geometry never invented from filename alone. */
  vector_file_present?: boolean;
  vector_file_name?: string;
  vector_file_url?: string;
  vector_attachment_id?: number;
  vector_file_type?: "svg" | "dxf" | "dwg" | "other";
  /** How the vector file was attached — metadata-only until storage endpoint exists. */
  vector_file_source?: "local_manual" | "server_upload";
  vector_file_mime?: string;
  vector_file_size_bytes?: number;
  vector_file_selected_at?: string;
  vector_file_extension?: string;
  vector_analysis_status?:
    | "not_provided"
    | "attached_unanalyzed"
    | "analyzed"
    | "analysis_failed"
    | "manual_review_approved";
  vector_manual_review_approved?: boolean;
  vector_manual_review_notes?: string;
  vector_metrics_source?: "manual" | "svg_analysis" | "dxf_analysis" | "dwg_manual";
  vector_layer_mapping_status?: "not_required" | "pending" | "mapped" | "failed";
  /** Operator manual SVG layer name → mapping target (no geometry invention). */
  svg_layer_mappings?: Record<string, string>;
  /** Safe analysis summary persisted on save — no raw SVG, no geometry metrics. */
  vector_parse_status?: "parsed" | "parsed_sanitized" | "failed";
  vector_analysis_warnings?: string[];
  vector_detected_layers_summary?: Array<{
    layer_name: string;
    mapping_status?: string;
    mapped_by?: string | null;
    mapped_target?: string | null;
    mapped_template_code?: string | null;
    detected_kind?: string | null;
  }>;
  vector_preview_available?: boolean;
  /** Operator UI pathway — progressive disclosure only; does not change costing formulas. */
  intake_input_pathway?: "vector" | "manual" | "quick_estimate";
  /** ISO timestamp when vector fast ask prefill was applied (UI assist only). */
  vector_fast_ask_applied_at?: string;
  /** Fast ask: layer alignment self-assessment. */
  vector_layer_alignment_status?: "aligned" | "needs_review" | "unknown";
  /** Optional notes about vector file quality from fast ask. */
  vector_file_quality_notes?: string;
  /** Client-side SVG metadata — no raw SVG content. */
  vector_svg_analyzed?: boolean;
  vector_svg_width?: string;
  vector_svg_height?: string;
  vector_svg_viewbox?: string;
  vector_detected_layer_count?: number;
  vector_detected_layers?: Array<{
    id: string;
    label: string;
    element_count: number;
    suggested_role: string;
    confirmed_role: string;
  }>;
  vector_layer_mapping_confirmed?: boolean;
  /** Primary letters layer chosen by operator after SVG parse. */
  vector_primary_letters_layer_id?: string;
  vector_primary_letters_layer_name?: string;
  vector_letters_layer_suggestion_confidence?: "high" | "medium" | "low";
  vector_layer_mapping_confirmed_at?: string;
  vector_layer_analysis_warnings?: string[];
  /** SVG geometry parser MVP — suggestions only until operator confirms. */
  vector_geometry_analyzed?: boolean;
  vector_geometry_confidence?: "high" | "medium" | "low";
  vector_geometry_warnings?: string[];
  vector_geometry_parser_version?: string;
  vector_geometry_suggestions_ignored?: boolean;
  vector_suggested_assembly_width_mm?: number;
  vector_suggested_assembly_height_mm?: number;
  vector_suggested_letter_layer_width_mm?: number;
  vector_suggested_letter_layer_height_mm?: number;
  vector_suggested_support_width_mm?: number;
  vector_suggested_support_height_mm?: number;
  vector_suggested_support_area_m2?: number;
  vector_suggested_frame_width_mm?: number;
  vector_suggested_frame_height_mm?: number;
  vector_suggested_letter_element_count?: number;
  vector_suggested_letter_perimeter_m?: number;
  vector_suggested_letter_face_area_m2?: number;
  vector_suggested_letter_count?: number;
  /** Set when operator explicitly applies SVG geometry suggestions. */
  geometry_source?: "manual" | "svg_suggestion_confirmed";
  /** Vector file name geometry was last confirmed/saved for (quote alignment). */
  geometry_confirmed_for_file_name?: string;
  /** True when vector file changed but geometry not yet reconfirmed for the new file. */
  geometry_stale?: boolean;
  /** Visual letter groups suggested from SVG fill colors (operator-confirmed finishes). */
  svgLetterGroups?: SvgLetterGroup[];
  /** Per-group face / return / backing finish assignments. */
  letterGroupFinishAssignments?: LetterGroupFinishAssignment[];
  /** Multicolor artwork layers needing operator decision — not auto Oracal groups. */
  svgArtworkLayersPending?: SvgArtworkLayerPending[];
  /** Operator execution decisions for multicolor artwork layers. */
  svgArtworkFinishAssignments?: SvgArtworkFinishAssignment[];
  /** Production master work files (CDR, PDF, DXF, etc.) — not auto-parsed. */
  workFileAttachments?: WorkFileAttachment[];
}

export const LITERE_VOLUMETRICE_FAMILY_ID = "litere_volumetrice";

const LEGACY_LITERE_LABELS = [
  "litere volumetrice",
  "litere volumetrice luminoase",
  "litere volumetrice",
];

export function isLitereVolumetriceFamily(productFamily: string | undefined | null): boolean {
  if (!productFamily) return false;
  const norm = productFamily.trim().toLowerCase();
  if (norm === LITERE_VOLUMETRICE_FAMILY_ID) return true;
  return LEGACY_LITERE_LABELS.some((label) => norm === label || norm.includes("litere volumetrice"));
}

export function parseIntakeProductSpec(
  raw: IntakeProductSpec | string | null | undefined
): IntakeProductSpec | null {
  if (raw == null || raw === "") return null;
  if (typeof raw === "object") return { ...raw };
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as IntakeProductSpec;
    }
  } catch {
    return null;
  }
  return null;
}

export function emptyIntakeProductSpec(): IntakeProductSpec {
  return {};
}

/** Drop empty strings / undefined for API payload. */
export function normalizeIntakeProductSpecForSave(
  spec: IntakeProductSpec
): IntakeProductSpec | null {
  return normalizeVolumetricIntakeSpecForSave(spec);
}
