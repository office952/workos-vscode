/**
 * TPL-VOLUMETRIC-LETTERS — canonical Work Intake spec fields and Intake → QuoteWizard mapping.
 * Geometry metrics are never invented; only explicit operator-provided values prefill.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";

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

export type PremountBarMaterial = "steel" | "aluminum";

export type PaintFinishType = "matte" | "gloss" | "satin" | "not_specified";

export type FaceVinylFinish = "gloss" | "matte" | "translucent_matte" | "satin";

export const INTAKE_FACE_FINISH_OPTIONS: {
  value: IntakeCanonicalFaceFinishType;
  label: string;
}[] = [
  { value: "none", label: "Fără autocolant" },
  { value: "oracal_651", label: "Oracal 651" },
  { value: "oracal_8500", label: "Oracal 8500 translucent" },
  { value: "printed_vinyl", label: "Autocolant printat" },
  { value: "printed_laminated_vinyl", label: "Autocolant printat + laminat" },
];

export const INTAKE_MOUNTING_SYSTEM_OPTIONS: {
  value: IntakeCanonicalMountingSystem;
  label: string;
}[] = [
  { value: "direct_wall", label: "Montaj direct pe perete" },
  { value: "steel_bars", label: "Bare oțel premontaj" },
  { value: "aluminum_bars", label: "Bare aluminiu premontaj" },
  { value: "acm_panel", label: "Panou ACM casetat (template separat)" },
];

export const INTAKE_PSU_OPTIONS = [60, 100, 160, 200] as const;

export type VectorFileType = "svg" | "dxf" | "dwg" | "other";

export type VectorAnalysisStatus =
  | "not_provided"
  | "attached_unanalyzed"
  | "analyzed"
  | "analysis_failed"
  | "manual_review_approved";

export const VECTOR_FILE_TYPE_OPTIONS: { value: VectorFileType; label: string }[] = [
  { value: "svg", label: "SVG (analiză layere dacă disponibilă)" },
  { value: "dxf", label: "DXF (fără analiză automată — review manual)" },
  { value: "dwg", label: "DWG (fișier sursă — fără analiză automată)" },
  { value: "other", label: "Alt tip" },
];

export function inferVectorFileType(filename: string): VectorFileType | undefined {
  const ext = filename.trim().toLowerCase().split(".").pop();
  if (ext === "svg") return "svg";
  if (ext === "dxf") return "dxf";
  if (ext === "dwg") return "dwg";
  if (ext) return "other";
  return undefined;
}

const GENERIC_VECTOR_FILENAME_STEMS = new Set([
  "logo",
  "logotip",
  "vector",
  "untitled",
  "document",
  "file",
  "export",
  "artboard",
  "design",
  "draft",
  "new",
  "copy",
  "layer",
  "shape",
]);

/**
 * Suggest production work title from vector filename — never invents geometry.
 * Skips generic stems (logo.svg, vector.dxf). Does not overwrite explicit spec.text.
 */
export function suggestWorkTitleFromVectorFilename(
  filename: string
): string | undefined {
  const trimmed = filename.trim();
  if (!trimmed) return undefined;
  const stem = trimmed.replace(/\.[^.]+$/i, "").trim();
  if (!stem) return undefined;
  const normalized = stem.replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
  const lower = normalized.toLowerCase();
  if (lower.length < 3 || /^\d+$/.test(lower)) return undefined;
  if (GENERIC_VECTOR_FILENAME_STEMS.has(lower)) return undefined;
  return normalized;
}

/** Derive vector metadata when operator records a filename — no geometry invented. */
export function deriveVectorMetadataFromFilename(
  spec: IntakeProductSpec,
  filename: string
): IntakeProductSpec {
  const trimmed = filename.trim();
  if (!trimmed) {
    return {
      ...spec,
      vector_file_name: undefined,
      vector_file_present: false,
      vector_analysis_status: "not_provided",
    };
  }
  const fileType = spec.vector_file_type ?? inferVectorFileType(trimmed) ?? "other";
  let analysisStatus: VectorAnalysisStatus = "attached_unanalyzed";
  if (spec.vector_manual_review_approved) {
    analysisStatus = "manual_review_approved";
  } else if (spec.vector_analysis_status === "analyzed") {
    analysisStatus = "analyzed";
  } else if (spec.vector_analysis_status === "analysis_failed") {
    analysisStatus = "analysis_failed";
  }
  const suggestedTitle = spec.text?.trim()
    ? undefined
    : suggestWorkTitleFromVectorFilename(trimmed);

  return {
    ...spec,
    ...(suggestedTitle ? { text: suggestedTitle } : {}),
    vector_file_name: trimmed,
    vector_file_present: true,
    vector_file_type: fileType,
    vector_analysis_status: analysisStatus,
    vector_metrics_source:
      fileType === "dwg" && spec.vector_manual_review_approved
        ? "dwg_manual"
        : spec.vector_metrics_source,
  };
}

export const INTAKE_ROLL_WIDTH_OPTIONS = [
  { value: 1000, label: "1000 mm" },
  { value: 1260, label: "1260 mm" },
] as const;

/** Legacy face_finish → canonical face_finish_type. */
export function legacyFaceFinishToCanonical(
  faceFinish: IntakeProductSpec["face_finish"] | undefined
): IntakeCanonicalFaceFinishType | undefined {
  switch (faceFinish) {
    case "plexi":
      return "none";
    case "oracal_651":
      return "oracal_651";
    case "oracal_8500_translucent":
      return "oracal_8500";
    case "print_laminated":
      return "printed_laminated_vinyl";
    default:
      return undefined;
  }
}

/** Canonical intake face finish → quote costing face_finish_type (no invented 8500 price). */
export function intakeFaceFinishToQuoteCostingType(
  canonical: IntakeCanonicalFaceFinishType | undefined
): "none" | "oracal_651" | "printed_vinyl" | "printed_laminated_vinyl" | undefined {
  if (!canonical || canonical === "none") return canonical === "none" ? "none" : undefined;
  if (canonical === "oracal_8500") return "oracal_651";
  return canonical;
}

export function resolveIntakeFaceFinishType(
  spec: IntakeProductSpec
): IntakeCanonicalFaceFinishType | undefined {
  if (spec.face_finish_type) return spec.face_finish_type;
  return legacyFaceFinishToCanonical(spec.face_finish);
}

/** Legacy mounting_type + premounting_type → canonical mounting_system. */
export function legacyMountingToCanonical(
  spec: Pick<IntakeProductSpec, "mounting_type" | "premounting_type" | "premount_bar_material">
): IntakeCanonicalMountingSystem | undefined {
  if (spec.mounting_type === "direct_wall") return "direct_wall";
  if (spec.mounting_type !== "premounted") return undefined;
  switch (spec.premounting_type) {
    case "none":
    case undefined:
      return "direct_wall";
    case "metal_structure":
      return spec.premount_bar_material === "aluminum" ? "aluminum_bars" : "steel_bars";
    case "acm_casetted_panel":
      return "acm_panel";
    default:
      return undefined;
  }
}

export function resolveIntakeMountingSystem(
  spec: IntakeProductSpec
): IntakeCanonicalMountingSystem | undefined {
  if (spec.mounting_system) return spec.mounting_system;
  return legacyMountingToCanonical(spec);
}

export function resolveIntakeBackBevelEnabled(spec: IntakeProductSpec): boolean {
  if (typeof spec.back_bevel_enabled === "boolean") return spec.back_bevel_enabled;
  return spec.backing_chamfer === true;
}

export function resolveIntakeMountingTemplateEnabled(
  spec: IntakeProductSpec
): boolean | undefined {
  if (typeof spec.mounting_template_enabled === "boolean") {
    return spec.mounting_template_enabled;
  }
  if (spec.mounting_type === "premounted" && spec.premounting_type === "none") {
    return true;
  }
  if (spec.mounting_type === "premounted" && spec.premounting_type === undefined) {
    return true;
  }
  return undefined;
}

/** Sync legacy intake keys from canonical fields for backward-compatible storage. */
export function syncLegacyIntakeFields(spec: IntakeProductSpec): IntakeProductSpec {
  const out: IntakeProductSpec = { ...spec };
  const face = resolveIntakeFaceFinishType(spec);
  if (face === "none") out.face_finish = "plexi";
  else if (face === "oracal_651") out.face_finish = "oracal_651";
  else if (face === "oracal_8500") out.face_finish = "oracal_8500_translucent";
  else if (face === "printed_laminated_vinyl") out.face_finish = "print_laminated";

  const mount = resolveIntakeMountingSystem(spec);
  if (mount === "direct_wall") {
    out.mounting_type = "direct_wall";
    out.premounting_type = undefined;
  } else if (mount === "steel_bars" || mount === "aluminum_bars") {
    out.mounting_type = "premounted";
    out.premounting_type = "metal_structure";
    out.premount_bar_material = mount === "aluminum_bars" ? "aluminum" : "steel";
  } else if (mount === "acm_panel") {
    out.mounting_type = "premounted";
    out.premounting_type = "acm_casetted_panel";
  }

  if (typeof spec.back_bevel_enabled === "boolean") {
    out.backing_chamfer = spec.back_bevel_enabled;
  }

  if (spec.paint_ral_code?.trim()) {
    out.ral_color = spec.paint_ral_code.trim();
  }

  if (spec.height_mm != null && spec.height_mm > 0) {
    out.letter_height_mm = spec.height_mm;
  } else if (spec.letter_height_mm != null && spec.letter_height_mm > 0) {
    out.height_mm = spec.letter_height_mm;
  }

  return out;
}

/** Normalize volumetric intake spec for API save — drops empty, syncs legacy. */
export function normalizeVolumetricIntakeSpecForSave(
  spec: IntakeProductSpec
): IntakeProductSpec | null {
  const synced = syncLegacyIntakeFields(spec);
  const out: IntakeProductSpec = {};

  const assignStr = (key: keyof IntakeProductSpec, val: string | undefined) => {
    const t = val?.trim();
    if (t) (out as Record<string, unknown>)[key] = t;
  };

  assignStr("text", synced.text);
  assignStr("font", synced.font);
  assignStr("notes", synced.notes);
  assignStr("mounting_notes", synced.mounting_notes);
  assignStr("lighting_notes", synced.lighting_notes);
  assignStr("face_vinyl_notes", synced.face_vinyl_notes);
  assignStr("paint_ral_code", synced.paint_ral_code);
  assignStr("paint_ral_name", synced.paint_ral_name);
  assignStr("face_vinyl_color_code", synced.face_vinyl_color_code);
  assignStr("face_vinyl_color_name", synced.face_vinyl_color_name);
  assignStr("return_ral_code", synced.return_ral_code);
  assignStr("return_ral_name", synced.return_ral_name);
  assignStr("return_ral_preview_hex", synced.return_ral_preview_hex);
  assignStr("return_oracal_code", synced.return_oracal_code);
  assignStr("return_oracal_name", synced.return_oracal_name);
  assignStr("return_oracal_preview_hex", synced.return_oracal_preview_hex);
  assignStr("face_vinyl_code", synced.face_vinyl_code);
  assignStr("face_vinyl_name", synced.face_vinyl_name);
  assignStr("face_vinyl_preview_hex", synced.face_vinyl_preview_hex);
  assignStr("ral_color", synced.ral_color);
  assignStr("vector_file_name", synced.vector_file_name);
  assignStr("vector_file_url", synced.vector_file_url);
  assignStr("vector_manual_review_notes", synced.vector_manual_review_notes);
  assignStr("vector_file_mime", synced.vector_file_mime);
  assignStr("vector_file_selected_at", synced.vector_file_selected_at);
  assignStr("vector_file_extension", synced.vector_file_extension);
  assignStr("vector_file_quality_notes", synced.vector_file_quality_notes);
  assignStr("vector_svg_width", synced.vector_svg_width);
  assignStr("vector_svg_height", synced.vector_svg_height);
  assignStr("vector_svg_viewbox", synced.vector_svg_viewbox);
  assignStr("vector_geometry_parser_version", synced.vector_geometry_parser_version);
  assignStr("vector_primary_letters_layer_id", synced.vector_primary_letters_layer_id);
  assignStr("vector_primary_letters_layer_name", synced.vector_primary_letters_layer_name);
  assignStr("vector_layer_mapping_confirmed_at", synced.vector_layer_mapping_confirmed_at);

  const assignPosNum = (key: keyof IntakeProductSpec, val: number | undefined) => {
    if (val != null && val > 0) (out as Record<string, unknown>)[key] = val;
  };

  for (const key of [
    "width_mm",
    "height_mm",
    "letter_height_mm",
    "depth_mm",
    "return_depth_mm",
    "letter_face_area_m2",
    "letter_perimeter_m",
    "letter_count",
    "mounting_template_area_m2",
    "paint_tube_count",
    "mounting_bar_count",
    "mounting_bar_length_m",
    "face_vinyl_roll_width_mm",
    "selected_psu_watts",
    "vector_attachment_id",
    "vector_file_size_bytes",
    "vector_detected_layer_count",
    "vector_suggested_assembly_width_mm",
    "vector_suggested_assembly_height_mm",
    "vector_suggested_letter_layer_width_mm",
    "vector_suggested_letter_layer_height_mm",
    "vector_suggested_support_width_mm",
    "vector_suggested_support_height_mm",
    "vector_suggested_support_area_m2",
    "vector_suggested_frame_width_mm",
    "vector_suggested_frame_height_mm",
    "vector_suggested_letter_element_count",
    "vector_suggested_letter_perimeter_m",
    "vector_suggested_letter_face_area_m2",
    "vector_suggested_letter_count",
  ] as const) {
    assignPosNum(key, synced[key] as number | undefined);
  }

  assignStr("mounting_bar_profile", synced.mounting_bar_profile);

  if (synced.vector_file_type) out.vector_file_type = synced.vector_file_type;
  if (synced.vector_file_source === "local_manual") {
    out.vector_file_source = synced.vector_file_source;
  }
  if (synced.vector_layer_alignment_status) {
    out.vector_layer_alignment_status = synced.vector_layer_alignment_status;
  }
  if (synced.vector_fast_ask_applied_at) {
    out.vector_fast_ask_applied_at = synced.vector_fast_ask_applied_at;
  }
  if (synced.vector_analysis_status) out.vector_analysis_status = synced.vector_analysis_status;
  if (synced.vector_metrics_source) out.vector_metrics_source = synced.vector_metrics_source;
  if (synced.vector_layer_mapping_status) {
    out.vector_layer_mapping_status = synced.vector_layer_mapping_status;
  }
  if (synced.svg_layer_mappings && Object.keys(synced.svg_layer_mappings).length > 0) {
    out.svg_layer_mappings = synced.svg_layer_mappings;
  }
  if (synced.vector_parse_status) {
    out.vector_parse_status = synced.vector_parse_status;
  }
  if (synced.vector_analysis_warnings && synced.vector_analysis_warnings.length > 0) {
    out.vector_analysis_warnings = synced.vector_analysis_warnings;
  }
  if (
    synced.vector_detected_layers_summary &&
    synced.vector_detected_layers_summary.length > 0
  ) {
    out.vector_detected_layers_summary = synced.vector_detected_layers_summary;
  }
  if (synced.vector_detected_layers && synced.vector_detected_layers.length > 0) {
    out.vector_detected_layers = synced.vector_detected_layers;
  }
  if (typeof synced.vector_svg_analyzed === "boolean") {
    out.vector_svg_analyzed = synced.vector_svg_analyzed;
  }
  if (typeof synced.vector_layer_mapping_confirmed === "boolean") {
    out.vector_layer_mapping_confirmed = synced.vector_layer_mapping_confirmed;
  }
  if (typeof synced.vector_geometry_analyzed === "boolean") {
    out.vector_geometry_analyzed = synced.vector_geometry_analyzed;
  }
  if (synced.vector_geometry_confidence) {
    out.vector_geometry_confidence = synced.vector_geometry_confidence;
  }
  if (
    synced.vector_letters_layer_suggestion_confidence === "high" ||
    synced.vector_letters_layer_suggestion_confidence === "medium" ||
    synced.vector_letters_layer_suggestion_confidence === "low"
  ) {
    out.vector_letters_layer_suggestion_confidence =
      synced.vector_letters_layer_suggestion_confidence;
  }
  if (synced.vector_geometry_warnings && synced.vector_geometry_warnings.length > 0) {
    out.vector_geometry_warnings = synced.vector_geometry_warnings;
  }
  if (typeof synced.vector_geometry_suggestions_ignored === "boolean") {
    out.vector_geometry_suggestions_ignored = synced.vector_geometry_suggestions_ignored;
  }
  if (synced.geometry_source) {
    out.geometry_source = synced.geometry_source;
  }
  if (synced.vector_layer_analysis_warnings && synced.vector_layer_analysis_warnings.length > 0) {
    out.vector_layer_analysis_warnings = synced.vector_layer_analysis_warnings;
  }
  if (typeof synced.vector_preview_available === "boolean") {
    out.vector_preview_available = synced.vector_preview_available;
  }
  if (typeof synced.vector_file_present === "boolean") {
    out.vector_file_present = synced.vector_file_present;
  }
  if (typeof synced.vector_manual_review_approved === "boolean") {
    out.vector_manual_review_approved = synced.vector_manual_review_approved;
    if (synced.vector_manual_review_approved) {
      out.vector_analysis_status = "manual_review_approved";
    }
  }

  if (synced.illumination_type) out.illumination_type = synced.illumination_type;
  if (synced.volume_finish) out.volume_finish = synced.volume_finish;
  if (synced.indoor_outdoor) out.indoor_outdoor = synced.indoor_outdoor;
  if (synced.face_finish) out.face_finish = synced.face_finish;
  if (synced.mounting_type) out.mounting_type = synced.mounting_type;
  if (synced.premounting_type) out.premounting_type = synced.premounting_type;
  if (synced.premount_bar_material) out.premount_bar_material = synced.premount_bar_material;
  if (synced.face_finish_type) out.face_finish_type = synced.face_finish_type;
  if (synced.mounting_system) out.mounting_system = synced.mounting_system;
  if (synced.paint_finish) out.paint_finish = synced.paint_finish;
  if (synced.face_vinyl_finish) out.face_vinyl_finish = synced.face_vinyl_finish;

  if (typeof synced.mounting_template_enabled === "boolean") {
    out.mounting_template_enabled = synced.mounting_template_enabled;
  }
  const templateMaterial = synced.mounting_template_material_type;
  if (templateMaterial === "none" || templateMaterial === "paper" || templateMaterial === "forex") {
    out.mounting_template_material_type = templateMaterial;
  } else if (synced.mounting_template_enabled === false) {
    out.mounting_template_material_type = "none";
  } else if (synced.mounting_template_enabled === true) {
    out.mounting_template_material_type = "forex";
  }
  if (typeof synced.back_bevel_enabled === "boolean") {
    out.back_bevel_enabled = synced.back_bevel_enabled;
  }
  if (typeof synced.backing_chamfer === "boolean") {
    out.backing_chamfer = synced.backing_chamfer;
  }
  if (typeof synced.face_miter_chamfer === "boolean") {
    out.face_miter_chamfer = synced.face_miter_chamfer;
  }
  if (typeof synced.visual_chamfer_included === "boolean") {
    out.visual_chamfer_included = synced.visual_chamfer_included;
  }
  if (synced.illumination_family === "front_lit") {
    out.illumination_family = synced.illumination_family;
  }
  if (typeof synced.face_vinyl_enabled === "boolean") {
    out.face_vinyl_enabled = synced.face_vinyl_enabled;
  }
  if (typeof synced.face_wrap_enabled === "boolean") {
    out.face_wrap_enabled = synced.face_wrap_enabled;
  }
  if (synced.return_color === "white" || synced.return_color === "black") {
    out.return_color = synced.return_color;
  }
  if (synced.return_edge_color === "white" || synced.return_edge_color === "black") {
    out.return_edge_color = synced.return_edge_color;
  }
  if (
    synced.return_finish_system === "standard" ||
    synced.return_finish_system === "RAL" ||
    synced.return_finish_system === "ORACAL"
  ) {
    out.return_finish_system = synced.return_finish_system;
  }
  if (synced.return_oracal_series === "651" || synced.return_oracal_series === "8500") {
    out.return_oracal_series = synced.return_oracal_series;
  }
  if (synced.face_vinyl_series === "651" || synced.face_vinyl_series === "8500") {
    out.face_vinyl_series = synced.face_vinyl_series;
  }
  const lightingType = synced.lighting_system_type;
  if (
    lightingType === "led_modules" ||
    lightingType === "led_strip" ||
    lightingType === "led_module"
  ) {
    out.lighting_system_type = lightingType;
  }
  const modulePower = synced.led_module_power_w ?? synced.led_module_wattage;
  if (modulePower === 0.72 || modulePower === 1 || modulePower === 1.44) {
    out.led_module_power_w = modulePower;
    out.led_module_wattage = modulePower;
  }
  const stripDensity = synced.led_strip_density;
  if (
    stripDensity === "60_led_per_m" ||
    stripDensity === "120_led_per_m" ||
    stripDensity === "60_5w" ||
    stripDensity === "120_10w"
  ) {
    out.led_strip_density = stripDensity;
  }
  if (synced.led_strip_power_w_per_ml === 5 || synced.led_strip_power_w_per_ml === 10) {
    out.led_strip_power_w_per_ml = synced.led_strip_power_w_per_ml;
  }
  if (synced.light_color === "warm" || synced.light_color === "cold") {
    out.light_color = synced.light_color;
  }
  if (synced.led_color_temperature === "warm" || synced.led_color_temperature === "cool") {
    out.led_color_temperature = synced.led_color_temperature;
  }
  if (synced.total_led_watts != null && synced.total_led_watts > 0) {
    out.total_led_watts = synced.total_led_watts;
  }
  if (synced.required_psu_watts != null && synced.required_psu_watts > 0) {
    out.required_psu_watts = synced.required_psu_watts;
  }
  if (synced.psu_sizing_status) {
    out.psu_sizing_status = synced.psu_sizing_status;
  }
  assignStr("psu_sizing_warning", synced.psu_sizing_warning);
  assignStr("psu_allocation_warning", synced.psu_allocation_warning);
  assignStr("psu_override_reason", synced.psu_override_reason);
  if (synced.psu_selection_mode === "auto" || synced.psu_selection_mode === "manual") {
    out.psu_selection_mode = synced.psu_selection_mode;
  }
  if (synced.psu_allocation_status) {
    out.psu_allocation_status = synced.psu_allocation_status;
  }
  if (synced.psu_configuration?.length) {
    out.psu_configuration = synced.psu_configuration.filter((w) =>
      INTAKE_PSU_OPTIONS.includes(w as (typeof INTAKE_PSU_OPTIONS)[number])
    );
  }
  assignPosNum("psu_total_capacity_watts", synced.psu_total_capacity_watts);
  assignPosNum("psu_reserve_margin_watts", synced.psu_reserve_margin_watts);
  assignPosNum("lighting_groups_total_watts", synced.lighting_groups_total_watts);
  assignPosNum("lighting_groups_total_psu_capacity", synced.lighting_groups_total_psu_capacity);
  if (synced.lighting_groups?.length) {
    out.lighting_groups = synced.lighting_groups.map((g) => ({
      id: g.id,
      label: g.label?.trim() || "Grup iluminare",
      estimated_led_watts: g.estimated_led_watts,
      required_psu_watts: g.required_psu_watts,
      psu_selection_mode: g.psu_selection_mode,
      assigned_psu_configuration: g.assigned_psu_configuration,
      psu_total_capacity_watts: g.psu_total_capacity_watts,
      psu_allocation_status: g.psu_allocation_status,
      psu_allocation_warning: g.psu_allocation_warning,
      psu_override_reason: g.psu_override_reason,
      notes: g.notes,
    }));
  }
  if (
    synced.intake_input_pathway === "vector" ||
    synced.intake_input_pathway === "manual" ||
    synced.intake_input_pathway === "quick_estimate"
  ) {
    out.intake_input_pathway = synced.intake_input_pathway;
  }

  if (synced.svgLetterGroups && synced.svgLetterGroups.length > 0) {
    out.svgLetterGroups = synced.svgLetterGroups;
  }
  if (synced.letterGroupFinishAssignments && synced.letterGroupFinishAssignments.length > 0) {
    out.letterGroupFinishAssignments = synced.letterGroupFinishAssignments;
  }
  if (synced.svgArtworkLayersPending && synced.svgArtworkLayersPending.length > 0) {
    out.svgArtworkLayersPending = synced.svgArtworkLayersPending;
  }
  if (synced.svgArtworkFinishAssignments && synced.svgArtworkFinishAssignments.length > 0) {
    out.svgArtworkFinishAssignments = synced.svgArtworkFinishAssignments;
  }
  if (synced.workFileAttachments && synced.workFileAttachments.length > 0) {
    out.workFileAttachments = synced.workFileAttachments;
  }

  return Object.keys(out).length > 0 ? out : null;
}
