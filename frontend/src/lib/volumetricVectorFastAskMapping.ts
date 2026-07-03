/**
 * TPL-VOLUMETRIC-LETTERS — vector intake fast ask → product_spec_json prefill.
 * Pure mapping only; no geometry invention, no CostEngine changes.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { deriveVectorMetadataFromFilename, inferVectorFileType } from "@/lib/intakeVolumetricSpec";
import {
  getVectorFileExtension,
  mapVectorFilePickToProductSpec,
} from "@/lib/vectorFileSelection";
import {
  mapSvgVectorAnalysisToProductSpec,
  rehydrateLayersFromSpec,
} from "@/lib/mapSvgVectorAnalysisToSpec";
import type { SvgVectorAnalysis, SvgVectorDetectedLayer } from "@/lib/svgVectorAnalysis";
import {
  applyFrontlitConstructionDefaults,
  isFaceVinylEnabled,
  type CanonicalLightingSystemType,
  type LedModulePowerW,
  type LedStripDensity,
  type LightColor,
  type ReturnColor,
} from "@/lib/volumetricFrontlitIntake";

export type LayerAlignmentAnswer = "aligned" | "needs_review" | "unknown";
export type FaceWrapAnswer = "yes" | "no" | "unknown";
export type FaceColantareTypeAnswer = "oracal_colored" | "print_laminated" | "unknown";

export type LetterDepthAnswer = 30 | 60 | 80 | 100 | "custom";

export interface VolumetricVectorFastAskAnswers {
  vectorFileName: string;
  vectorFileMime?: string;
  vectorFileSizeBytes?: number;
  vectorFileExtension?: string;
  vectorFileSelectedAt?: string;
  fileQualityNotes?: string;
  layerAlignment: LayerAlignmentAnswer;
  layerNotes?: string;
  /** Prima întrebare — colantare față da/nu. */
  faceWrap: FaceWrapAnswer;
  /** Doar când faceWrap === yes. */
  faceColantareType: FaceColantareTypeAnswer;
  returnEdgeColor: ReturnColor | "unknown";
  letterDepth: LetterDepthAnswer;
  customDepthMm?: number;
  lightingSystemType: CanonicalLightingSystemType | "unknown";
  ledModulePowerW: LedModulePowerW | "unknown";
  ledStripDensity: LedStripDensity | "unknown";
  lightColor: LightColor | "unknown";
  /** Client-side SVG layer detection (SVG only). */
  svgAnalysis?: SvgVectorAnalysis | null;
  detectedLayers?: SvgVectorDetectedLayer[];
  layerMappingConfirmed?: boolean;
}

export interface VectorFastAskPrefillResult {
  spec: IntakeProductSpec;
  prefilledSectionNumbers: number[];
  messages: string[];
}

/** Sections touched by fast ask apply (for UI highlight). */
export const VECTOR_FAST_ASK_SECTIONS = [1, 2, 4, 5, 7] as const;

export function deriveFastAskFromSpec(
  spec: IntakeProductSpec | null | undefined
): Partial<VolumetricVectorFastAskAnswers> {
  if (!spec) return {};
  const depth = spec.depth_mm ?? spec.return_depth_mm;
  let letterDepth: LetterDepthAnswer | undefined;
  let customDepthMm: number | undefined;
  if (depth === 30 || depth === 60 || depth === 80 || depth === 100) {
    letterDepth = depth;
  } else if (depth != null && depth > 0) {
    letterDepth = "custom";
    customDepthMm = depth;
  }

  let faceWrap: FaceWrapAnswer | undefined;
  if (typeof spec.face_vinyl_enabled === "boolean") {
    faceWrap = spec.face_vinyl_enabled ? "yes" : "no";
  } else if (typeof spec.face_wrap_enabled === "boolean") {
    faceWrap = spec.face_wrap_enabled ? "yes" : "no";
  } else if (isFaceVinylEnabled(spec)) {
    faceWrap = "yes";
  }

  let faceColantareType: FaceColantareTypeAnswer | undefined;
  switch (spec.face_finish_type) {
    case "oracal_651":
    case "oracal_8500":
      faceColantareType = "oracal_colored";
      break;
    case "printed_laminated_vinyl":
      faceColantareType = "print_laminated";
      break;
    default:
      break;
  }

  let layerAlignment: LayerAlignmentAnswer | undefined;
  if (spec.vector_layer_alignment_status) {
    layerAlignment = spec.vector_layer_alignment_status;
  } else if (spec.vector_manual_review_approved) {
    layerAlignment = "aligned";
  } else if (spec.vector_layer_mapping_status === "pending") {
    layerAlignment = "needs_review";
  }

  return {
    vectorFileName: spec.vector_file_name ?? "",
    vectorFileMime: spec.vector_file_mime,
    vectorFileSizeBytes: spec.vector_file_size_bytes,
    vectorFileExtension: spec.vector_file_extension,
    vectorFileSelectedAt: spec.vector_file_selected_at,
    fileQualityNotes: spec.vector_file_quality_notes ?? "",
    layerAlignment,
    layerNotes: spec.vector_manual_review_notes ?? "",
    faceWrap,
    faceColantareType,
    returnEdgeColor: spec.return_color ?? spec.return_edge_color,
    letterDepth,
    customDepthMm,
    lightingSystemType:
      spec.lighting_system_type === "led_module"
        ? "led_modules"
        : spec.lighting_system_type === "led_modules" || spec.lighting_system_type === "led_strip"
          ? spec.lighting_system_type
          : undefined,
    ledModulePowerW: spec.led_module_power_w ?? spec.led_module_wattage,
    ledStripDensity: spec.led_strip_density,
    lightColor:
      spec.light_color ??
      (spec.led_color_temperature === "cool" ? "cold" : spec.led_color_temperature),
    detectedLayers: rehydrateLayersFromSpec(spec),
    layerMappingConfirmed: spec.vector_layer_mapping_confirmed,
    svgAnalysis: spec.vector_svg_analyzed
      ? {
          file_name: spec.vector_file_name ?? "",
          parse_ok: true,
          width: spec.vector_svg_width,
          height: spec.vector_svg_height,
          view_box: spec.vector_svg_viewbox,
          layers: rehydrateLayersFromSpec(spec),
          warnings: spec.vector_layer_analysis_warnings ?? [],
          has_embedded_raster: false,
          vector_svg_analyzed: true,
        }
      : undefined,
  };
}

/**
 * Legacy / smoke intakes with vector file + construction fields skip the fast-ask gate.
 */
export function isVectorFastAskComplete(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  if (spec.vector_fast_ask_applied_at) return true;
  const hasFile = Boolean(spec.vector_file_name?.trim());
  const hasDepth = (spec.depth_mm ?? spec.return_depth_mm ?? 0) > 0;
  const hasFinish =
    typeof spec.face_wrap_enabled === "boolean" ||
    Boolean(spec.return_edge_color) ||
    Boolean(spec.lighting_system_type);
  const hasLegacySmokeGeometry =
    (spec.letter_face_area_m2 ?? 0) > 0 && (spec.letter_perimeter_m ?? 0) > 0;
  return hasFile && hasDepth && (hasFinish || hasLegacySmokeGeometry);
}

export function mapVectorFastAskToProductSpec(
  existingSpec: IntakeProductSpec,
  answers: VolumetricVectorFastAskAnswers,
  options?: { overwrite?: boolean }
): VectorFastAskPrefillResult {
  const overwrite = options?.overwrite ?? false;
  const messages: string[] = [];
  const prefilledSectionNumbers: number[] = [];
  let next: IntakeProductSpec = { ...existingSpec, intake_input_pathway: "vector" };

  const fileName = answers.vectorFileName.trim();
  if (fileName) {
    const hasPickMetadata =
      answers.vectorFileSelectedAt != null ||
      answers.vectorFileSizeBytes != null ||
      answers.vectorFileMime != null;
    if (hasPickMetadata) {
      next = mapVectorFilePickToProductSpec(next, {
        fileName,
        extension: answers.vectorFileExtension ?? getVectorFileExtension(fileName),
        mime: answers.vectorFileMime ?? "",
        sizeBytes: answers.vectorFileSizeBytes ?? 0,
        fileType: inferVectorFileType(fileName) ?? "other",
        selectedAt: answers.vectorFileSelectedAt ?? new Date().toISOString(),
      });
    } else {
      next = deriveVectorMetadataFromFilename(next, fileName);
      if (!next.vector_analysis_status || next.vector_analysis_status === "not_provided") {
        next.vector_analysis_status = "attached_unanalyzed";
      }
      next.vector_file_present = true;
      next.vector_file_source = next.vector_file_source ?? "local_manual";
    }
    messages.push("Fișier vector înregistrat — geometria rămâne de confirmat manual.");
  }

  if (answers.fileQualityNotes?.trim()) {
    next.vector_file_quality_notes = answers.fileQualityNotes.trim();
  }

  if (answers.svgAnalysis?.parse_ok && answers.detectedLayers?.length) {
    const analysisForSpec: SvgVectorAnalysis = {
      ...answers.svgAnalysis,
      layers: answers.detectedLayers,
    };
    next = mapSvgVectorAnalysisToProductSpec(next, analysisForSpec, {
      layerMappingConfirmed: answers.layerMappingConfirmed ?? false,
    });
    messages.push(
      `Am detectat ${answers.detectedLayers.length} layere în fișier — confirmă rolurile înainte de salvare.`
    );
  } else if (answers.svgAnalysis && !answers.svgAnalysis.parse_ok) {
    next = mapSvgVectorAnalysisToProductSpec(next, answers.svgAnalysis);
    messages.push(
      answers.svgAnalysis.parse_error ??
        "Analiza SVG nu a reușit — poți continua manual."
    );
  }

  switch (answers.layerAlignment) {
    case "aligned":
      next.vector_layer_alignment_status = "aligned";
      next.vector_layer_mapping_status = "mapped";
      next.vector_manual_review_approved = true;
      break;
    case "needs_review":
      next.vector_layer_alignment_status = "needs_review";
      next.vector_layer_mapping_status = "pending";
      next.vector_manual_review_approved = false;
      break;
    case "unknown":
      next.vector_layer_alignment_status = "unknown";
      next.vector_layer_mapping_status = "pending";
      break;
  }

  if (answers.layerNotes?.trim()) {
    const prev = next.vector_manual_review_notes?.trim();
    next.vector_manual_review_notes = prev
      ? `${prev}\n${answers.layerNotes.trim()}`
      : answers.layerNotes.trim();
  }

  if (answers.faceWrap !== "unknown") {
    const canWrite =
      overwrite || next.face_wrap_enabled == null || next.face_wrap_enabled === undefined;
    if (canWrite) {
      const wrap = answers.faceWrap === "yes";
      next.face_vinyl_enabled = wrap;
      next.face_wrap_enabled = wrap;
      if (!wrap) {
        next.face_finish_type = "none";
      } else if (answers.faceColantareType !== "unknown") {
        switch (answers.faceColantareType) {
          case "oracal_colored":
            next.face_finish_type = "oracal_651";
            break;
          case "print_laminated":
            next.face_finish_type = "printed_laminated_vinyl";
            break;
          default:
            break;
        }
      }
      prefilledSectionNumbers.push(1);
      if (wrap) prefilledSectionNumbers.push(5);
    }
  }

  if (answers.returnEdgeColor !== "unknown") {
    const canWrite = overwrite || !next.return_edge_color;
    if (canWrite) {
      next.return_color = answers.returnEdgeColor;
      next.return_edge_color = answers.returnEdgeColor;
      next.volume_finish = "none";
      prefilledSectionNumbers.push(4);
    }
  }

  const resolvedDepth =
    answers.letterDepth === "custom"
      ? answers.customDepthMm
      : typeof answers.letterDepth === "string"
        ? Number(answers.letterDepth)
        : answers.letterDepth;

  let depthMm: number | undefined;
  if (answers.letterDepth === "custom") {
    depthMm =
      answers.customDepthMm != null && answers.customDepthMm > 0
        ? answers.customDepthMm
        : undefined;
  } else if (
    resolvedDepth === 30 ||
    resolvedDepth === 60 ||
    resolvedDepth === 80 ||
    resolvedDepth === 100
  ) {
    depthMm = resolvedDepth;
  }

  if (depthMm != null && depthMm > 0) {
    const canWrite =
      overwrite ||
      (next.depth_mm == null && next.return_depth_mm == null);
    if (canWrite) {
      next.depth_mm = depthMm;
      next.return_depth_mm = depthMm;
      prefilledSectionNumbers.push(2);
    }
  }

  if (answers.lightingSystemType !== "unknown") {
    const canWrite = overwrite || !next.lighting_system_type;
    if (canWrite) {
      next.lighting_system_type = answers.lightingSystemType;
      prefilledSectionNumbers.push(7);
    }
  }
  if (answers.ledModulePowerW !== "unknown") {
    const canWrite = overwrite || !(next.led_module_power_w ?? next.led_module_wattage);
    if (canWrite) {
      next.led_module_power_w = answers.ledModulePowerW;
      next.led_module_wattage = answers.ledModulePowerW;
    }
  }
  if (answers.ledStripDensity !== "unknown") {
    const canWrite = overwrite || !next.led_strip_density;
    if (canWrite) {
      next.led_strip_density = answers.ledStripDensity;
    }
  }
  if (answers.lightColor !== "unknown") {
    const canWrite = overwrite || !(next.light_color ?? next.led_color_temperature);
    if (canWrite) {
      next.light_color = answers.lightColor;
      next.led_color_temperature = answers.lightColor === "cold" ? "cool" : "warm";
    }
  }

  next.vector_fast_ask_applied_at = new Date().toISOString();
  next.vector_metrics_source = next.vector_metrics_source ?? "manual";
  next = applyFrontlitConstructionDefaults(next);

  return {
    spec: next,
    prefilledSectionNumbers: [...new Set(prefilledSectionNumbers)],
    messages,
  };
}

export function emptyVectorFastAskAnswers(): VolumetricVectorFastAskAnswers {
  return {
    vectorFileName: "",
    layerAlignment: "unknown",
    faceWrap: "unknown",
    faceColantareType: "unknown",
    returnEdgeColor: "white",
    letterDepth: 60,
    lightingSystemType: "led_modules",
    ledModulePowerW: 1.44,
    ledStripDensity: "60_led_per_m",
    lightColor: "warm",
  };
}
