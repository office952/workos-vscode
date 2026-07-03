/**
 * Merge helpers — protect in-flight vector parse from stale server refresh.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { INTAKE_INPUT_PATHWAY_VECTOR } from "@/lib/volumetricIntakePathway";
import { isSameVectorFileIdentity } from "@/lib/vectorGeometryInvalidation";

type DetectedLayerList = NonNullable<IntakeProductSpec["vector_detected_layers"]>;

function isDetectedLayerList(value: unknown): value is DetectedLayerList {
  return (
    Array.isArray(value) &&
    value.every(
      (entry) =>
        typeof entry === "object" &&
        entry !== null &&
        typeof (entry as { id?: unknown }).id === "string"
    )
  );
}

function isStringRecord(value: unknown): value is Record<string, string> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    Object.values(value).every((entry) => typeof entry === "string")
  );
}

const VECTOR_MERGE_KEYS = [
  "vector_file_name",
  "vector_file_present",
  "vector_file_type",
  "vector_file_mime",
  "vector_file_size_bytes",
  "vector_file_extension",
  "vector_file_selected_at",
  "vector_file_source",
  "vector_analysis_status",
  "vector_parse_status",
  "vector_svg_analyzed",
  "vector_svg_width",
  "vector_svg_height",
  "vector_svg_viewbox",
  "vector_detected_layer_count",
  "vector_detected_layers",
  "vector_layer_analysis_warnings",
  "vector_detected_layers_summary",
  "svg_layer_mappings",
  "vector_layer_mapping_status",
  "vector_layer_mapping_confirmed",
  "vector_layer_mapping_confirmed_at",
  "vector_primary_letters_layer_id",
  "vector_primary_letters_layer_name",
  "vector_letters_layer_suggestion_confidence",
  "vector_geometry_analyzed",
  "vector_geometry_confidence",
  "vector_geometry_warnings",
  "vector_suggested_assembly_width_mm",
  "vector_suggested_assembly_height_mm",
  "vector_suggested_letter_layer_width_mm",
  "vector_suggested_letter_layer_height_mm",
  "vector_suggested_frame_width_mm",
  "vector_suggested_frame_height_mm",
  "vector_suggested_letter_element_count",
  "vector_suggested_letter_perimeter_m",
  "vector_suggested_letter_face_area_m2",
  "vector_suggested_letter_count",
  "vector_suggested_support_width_mm",
  "vector_suggested_support_height_mm",
  "vector_suggested_support_area_m2",
  "geometry_confirmed_for_file_name",
  "geometry_stale",
] as const satisfies readonly (keyof IntakeProductSpec)[];

export function shouldKeepLocalVectorSpec(input: {
  localFileAt: string | null;
  localPathwayIsVector: boolean;
  syncedFileAt?: string | null;
}): boolean {
  const syncedFileAt = input.syncedFileAt ?? "";
  return (
    input.localFileAt != null &&
    input.localPathwayIsVector &&
    (!syncedFileAt || input.localFileAt >= syncedFileAt)
  );
}

function layerCount(spec: IntakeProductSpec): number {
  return spec.vector_detected_layers?.length ?? 0;
}

/** Prefer richer local vector block when operator picked a file in this session. */
export function mergeLocalVectorSpecFields(
  prev: IntakeProductSpec,
  base: IntakeProductSpec
): IntakeProductSpec {
  const prevLayers = layerCount(prev);
  const baseLayers = layerCount(base);
  const sameFile =
    isSameVectorFileIdentity(
      prev,
      base.vector_file_name ?? "",
      base.vector_file_selected_at
    ) || !base.vector_file_name?.trim();
  const preferPrev =
    sameFile &&
    (prevLayers > baseLayers ||
      (prevLayers > 0 && prevLayers >= baseLayers && Boolean(prev.vector_file_selected_at)));

  const out: IntakeProductSpec = {
    ...base,
    intake_input_pathway: INTAKE_INPUT_PATHWAY_VECTOR,
  };

  for (const key of VECTOR_MERGE_KEYS) {
    const prevVal = prev[key];
    const baseVal = base[key];

    if (!sameFile) {
      if (key === "vector_detected_layers") {
        if (isDetectedLayerList(baseVal) && baseVal.length > 0) {
          out[key] = baseVal;
        }
        continue;
      }
      if (baseVal !== undefined && baseVal !== null && baseVal !== "") {
        (out as Record<string, unknown>)[key] = baseVal;
      }
      continue;
    }

    if (key === "vector_detected_layers") {
      if (preferPrev && isDetectedLayerList(prevVal) && prevVal.length > 0) {
        out[key] = prevVal;
      } else if (isDetectedLayerList(baseVal) && baseVal.length > 0) {
        out[key] = baseVal;
      } else if (isDetectedLayerList(prevVal) && prevVal.length > 0) {
        out[key] = prevVal;
      }
      continue;
    }

    if (key === "vector_detected_layers_summary" || key === "vector_layer_analysis_warnings") {
      const pv = prevVal as unknown[] | undefined;
      const bv = baseVal as unknown[] | undefined;
      if (preferPrev && pv && pv.length > 0) {
        (out as Record<string, unknown>)[key] = prevVal;
      } else if (bv && bv.length > 0) {
        (out as Record<string, unknown>)[key] = baseVal;
      } else if (pv && pv.length > 0) {
        (out as Record<string, unknown>)[key] = prevVal;
      }
      continue;
    }

    if (key === "svg_layer_mappings") {
      const pv = isStringRecord(prevVal) ? prevVal : undefined;
      const bv = isStringRecord(baseVal) ? baseVal : undefined;
      const pKeys = pv ? Object.keys(pv).length : 0;
      const bKeys = bv ? Object.keys(bv).length : 0;
      if (preferPrev && pKeys >= bKeys && pKeys > 0) {
        out[key] = pv;
      } else if (bKeys > 0) {
        out[key] = bv;
      } else if (pKeys > 0) {
        out[key] = pv;
      }
      continue;
    }

    if (preferPrev && prevVal !== undefined && prevVal !== null && prevVal !== "") {
      (out as Record<string, unknown>)[key] = prevVal;
    } else if (baseVal !== undefined && baseVal !== null && baseVal !== "") {
      (out as Record<string, unknown>)[key] = baseVal;
    } else if (prevVal !== undefined && prevVal !== null && prevVal !== "") {
      (out as Record<string, unknown>)[key] = prevVal;
    }
  }

  return out;
}
