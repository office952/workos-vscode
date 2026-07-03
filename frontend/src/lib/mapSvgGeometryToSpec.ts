/**
 * Map SVG geometry parser suggestions into product_spec_json — suggestions only.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import {
  SVG_GEOMETRY_PARSER_VERSION,
  type SvgGeometryParseResult,
} from "@/lib/svgGeometryParser";

export function mapSvgGeometrySuggestionsToSpec(
  spec: IntakeProductSpec,
  result: SvgGeometryParseResult
): IntakeProductSpec {
  if (!result.parseOk) {
    return {
      ...spec,
      vector_geometry_analyzed: false,
      vector_geometry_warnings: result.warnings.length ? result.warnings : undefined,
    };
  }

  const next: IntakeProductSpec = {
    ...spec,
    vector_geometry_analyzed: true,
    vector_geometry_confidence: result.confidence,
    vector_geometry_parser_version: SVG_GEOMETRY_PARSER_VERSION,
    vector_geometry_warnings:
      result.warnings.length > 0 ? [...result.warnings] : undefined,
  };

  const s = result.suggestions;
  if (s.assemblyWidthMm != null) next.vector_suggested_assembly_width_mm = s.assemblyWidthMm;
  if (s.assemblyHeightMm != null) next.vector_suggested_assembly_height_mm = s.assemblyHeightMm;
  if (s.letterLayerWidthMm != null) {
    next.vector_suggested_letter_layer_width_mm = s.letterLayerWidthMm;
  }
  if (s.letterLayerHeightMm != null) {
    next.vector_suggested_letter_layer_height_mm = s.letterLayerHeightMm;
  }
  if (s.supportWidthMm != null) next.vector_suggested_support_width_mm = s.supportWidthMm;
  if (s.supportHeightMm != null) next.vector_suggested_support_height_mm = s.supportHeightMm;
  if (s.supportAreaM2 != null) next.vector_suggested_support_area_m2 = s.supportAreaM2;
  if (s.frameWidthMm != null) next.vector_suggested_frame_width_mm = s.frameWidthMm;
  if (s.frameHeightMm != null) next.vector_suggested_frame_height_mm = s.frameHeightMm;
  if (s.letterElementCount != null) {
    next.vector_suggested_letter_element_count = s.letterElementCount;
  }
  if (s.letterPerimeterM != null) {
    next.vector_suggested_letter_perimeter_m = s.letterPerimeterM;
  }
  if (s.letterFaceAreaM2 != null) {
    next.vector_suggested_letter_face_area_m2 = s.letterFaceAreaM2;
  }
  if (s.letterCount != null) {
    next.vector_suggested_letter_count = s.letterCount;
  }

  return next;
}

export type GeometrySuggestionApplyKind =
  | "dimensions"
  | "support_area"
  | "letter_count"
  | "quote_metrics"
  | "ignore";

/** Apply operator-confirmed suggestions to quote-relevant fields. */
export function applySvgGeometrySuggestionsToSpec(
  spec: IntakeProductSpec,
  kind: GeometrySuggestionApplyKind
): IntakeProductSpec {
  if (kind === "ignore") {
    return { ...spec, vector_geometry_suggestions_ignored: true };
  }

  const next: IntakeProductSpec = {
    ...spec,
    geometry_source: "svg_suggestion_confirmed",
  };

  if (kind === "dimensions") {
    const w =
      spec.vector_suggested_letter_layer_width_mm ??
      spec.vector_suggested_assembly_width_mm;
    const h =
      spec.vector_suggested_letter_layer_height_mm ??
      spec.vector_suggested_assembly_height_mm;
    if (w != null && w > 0) next.width_mm = w;
    if (h != null && h > 0) {
      next.height_mm = h;
      next.letter_height_mm = h;
    }
  }

  if (kind === "support_area") {
    const area = spec.vector_suggested_support_area_m2;
    if (area != null && area > 0) {
      next.mounting_template_area_m2 = area;
      next.mounting_template_enabled = true;
    }
  }

  if (kind === "letter_count") {
    const count = spec.vector_suggested_letter_count ?? spec.vector_suggested_letter_element_count;
    if (count != null && count >= 1) {
      next.letter_count = count;
    }
  }

  if (kind === "quote_metrics") {
    const w =
      spec.vector_suggested_letter_layer_width_mm ??
      spec.vector_suggested_assembly_width_mm;
    const h =
      spec.vector_suggested_letter_layer_height_mm ??
      spec.vector_suggested_assembly_height_mm;
    if (w != null && w > 0) next.width_mm = w;
    if (h != null && h > 0) {
      next.height_mm = h;
      next.letter_height_mm = h;
    }
    const perimeter = spec.vector_suggested_letter_perimeter_m;
    if (perimeter != null && perimeter > 0) {
      next.letter_perimeter_m = perimeter;
    }
    const area = spec.vector_suggested_letter_face_area_m2;
    if (area != null && area > 0) {
      next.letter_face_area_m2 = area;
    }
    const count = spec.vector_suggested_letter_count ?? spec.vector_suggested_letter_element_count;
    if (count != null && count >= 1) {
      next.letter_count = count;
    }
    next.vector_metrics_source = "svg_analysis";
  }

  return next;
}

export function rehydrateGeometryFromSpec(
  spec: IntakeProductSpec | null | undefined
): SvgGeometryParseResult | null {
  if (!spec?.vector_geometry_analyzed) return null;
  return {
    parseOk: true,
    units: null,
    layers: [],
    suggestions: {
      assemblyWidthMm: spec.vector_suggested_assembly_width_mm,
      assemblyHeightMm: spec.vector_suggested_assembly_height_mm,
      letterLayerWidthMm: spec.vector_suggested_letter_layer_width_mm,
      letterLayerHeightMm: spec.vector_suggested_letter_layer_height_mm,
      supportWidthMm: spec.vector_suggested_support_width_mm,
      supportHeightMm: spec.vector_suggested_support_height_mm,
      supportAreaM2: spec.vector_suggested_support_area_m2,
      frameWidthMm: spec.vector_suggested_frame_width_mm,
      frameHeightMm: spec.vector_suggested_frame_height_mm,
      letterElementCount: spec.vector_suggested_letter_element_count,
      letterPerimeterM: spec.vector_suggested_letter_perimeter_m,
      letterFaceAreaM2: spec.vector_suggested_letter_face_area_m2,
      letterCount: spec.vector_suggested_letter_count,
    },
    warnings: spec.vector_geometry_warnings ?? [],
    unsupported: [],
    confidence: spec.vector_geometry_confidence ?? "low",
  };
}
