/**
 * Invalidate SVG-derived geometry when the vector file identity changes.
 * Keeps manual production fields (depth, face finish, etc.) intact.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";

export const VECTOR_GEOMETRY_SUGGESTION_KEYS = [
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
] as const satisfies readonly (keyof IntakeProductSpec)[];

const QUOTE_GEOMETRY_KEYS = [
  "width_mm",
  "height_mm",
  "letter_height_mm",
  "letter_perimeter_m",
  "letter_face_area_m2",
  "letter_count",
] as const satisfies readonly (keyof IntakeProductSpec)[];

function normFileName(name: string | undefined | null): string {
  return (name ?? "").trim().toLowerCase();
}

/** True when the picked file is the same identity as the spec's current vector file. */
export function isSameVectorFileIdentity(
  spec: IntakeProductSpec,
  newFileName: string,
  newSelectedAt?: string | null
): boolean {
  const prevName = normFileName(spec.vector_file_name);
  const nextName = normFileName(newFileName);
  if (!prevName || !nextName || prevName !== nextName) return false;
  const prevAt = spec.vector_file_selected_at ?? "";
  const nextAt = newSelectedAt ?? "";
  if (prevAt && nextAt && prevAt !== nextAt) return false;
  return true;
}

function geometryWasSvgDerived(spec: IntakeProductSpec): boolean {
  return (
    spec.vector_metrics_source === "svg_analysis" ||
    spec.geometry_source === "svg_suggestion_confirmed"
  );
}

function geometryWasConfirmedForFile(spec: IntakeProductSpec): boolean {
  return Boolean(spec.geometry_confirmed_for_file_name?.trim());
}

function clearKeys(
  spec: IntakeProductSpec,
  keys: readonly (keyof IntakeProductSpec)[]
): IntakeProductSpec {
  const next: IntakeProductSpec = { ...spec };
  for (const key of keys) {
    delete next[key];
  }
  return next;
}

/** Clear SVG layer mapping, suggestions, and quote metrics tied to a previous file. */
export function invalidateVectorDerivedGeometry(
  spec: IntakeProductSpec
): IntakeProductSpec {
  let next = clearKeys(spec, VECTOR_GEOMETRY_SUGGESTION_KEYS);

  if (geometryWasSvgDerived(next) || geometryWasConfirmedForFile(next)) {
    next = clearKeys(next, QUOTE_GEOMETRY_KEYS);
    if (next.vector_metrics_source === "svg_analysis") {
      delete next.vector_metrics_source;
    }
    if (next.geometry_source === "svg_suggestion_confirmed") {
      delete next.geometry_source;
    }
  }

  next.vector_layer_mapping_confirmed = false;
  delete next.vector_layer_mapping_confirmed_at;
  delete next.vector_primary_letters_layer_id;
  delete next.vector_primary_letters_layer_name;
  delete next.vector_letters_layer_suggestion_confidence;
  delete next.vector_layer_alignment_status;
  delete next.svg_layer_mappings;
  delete next.vector_detected_layers_summary;
  delete next.vector_geometry_confidence;
  delete next.vector_geometry_warnings;
  delete next.vector_geometry_parser_version;
  delete next.vector_geometry_suggestions_ignored;
  next.vector_geometry_analyzed = false;
  next.geometry_stale = true;
  delete next.geometry_confirmed_for_file_name;
  delete next.svgLetterGroups;
  delete next.letterGroupFinishAssignments;
  delete next.svgArtworkLayersPending;

  if (next.vector_detected_layers?.length) {
    next.vector_detected_layers = next.vector_detected_layers.map((layer) => ({
      ...layer,
      confirmed_role: layer.suggested_role,
    }));
  }

  return next;
}

/** Apply invalidation only when the vector file identity actually changed. */
export function applyVectorFileChangeToSpec(
  spec: IntakeProductSpec,
  newFileName: string,
  newSelectedAt?: string | null
): IntakeProductSpec {
  if (isSameVectorFileIdentity(spec, newFileName, newSelectedAt)) {
    return spec;
  }
  return invalidateVectorDerivedGeometry(spec);
}

export function markVectorGeometryConfirmedForFile(
  spec: IntakeProductSpec
): IntakeProductSpec {
  const file = spec.vector_file_name?.trim();
  if (!file) return { ...spec, geometry_stale: false };
  return {
    ...spec,
    geometry_confirmed_for_file_name: file,
    geometry_stale: false,
  };
}

/** Whether quote/simulation may treat current geometry metrics as valid for the active vector file. */
export function isVectorGeometryCurrentForQuote(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  if (spec.geometry_stale === true) return false;

  const file = spec.vector_file_name?.trim();
  if (!file) return true;

  const confirmedFor = spec.geometry_confirmed_for_file_name?.trim();
  if (confirmedFor) {
    return confirmedFor.toLowerCase() === file.toLowerCase();
  }

  // Manual / legacy intake geometry is not tied to SVG auto-apply metadata.
  if (
    spec.vector_metrics_source !== "svg_analysis" &&
    spec.geometry_source !== "svg_suggestion_confirmed"
  ) {
    return true;
  }

  // Legacy svg-derived specs saved before geometry_confirmed_for_file_name metadata.
  if (
    spec.vector_layer_mapping_confirmed === true &&
    spec.vector_geometry_analyzed === true
  ) {
    return true;
  }

  return false;
}

/** Strip stale SVG-tied quote metrics before classic quote/simulation prefill. */
export function getEffectiveQuoteGeometrySpec(
  spec: IntakeProductSpec | null | undefined
): IntakeProductSpec | null | undefined {
  if (!spec) return spec;
  if (isVectorGeometryCurrentForQuote(spec)) return spec;

  const next: IntakeProductSpec = { ...spec };
  for (const key of QUOTE_GEOMETRY_KEYS) {
    delete next[key];
  }
  for (const key of VECTOR_GEOMETRY_SUGGESTION_KEYS) {
    delete next[key];
  }
  if (next.vector_metrics_source === "svg_analysis") {
    delete next.vector_metrics_source;
  }
  if (next.geometry_source === "svg_suggestion_confirmed") {
    delete next.geometry_source;
  }
  return next;
}
