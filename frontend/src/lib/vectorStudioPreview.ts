import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { syncVectorAnalysisStatusFromParse } from "@/lib/intakeVectorLayerMapping";
import type { SvgLayerAnalysisResult } from "@/lib/svgLayerAnalysis";
import {
  hasGeometryEstimateInSpec,
  hasManualGeometryInSpec,
} from "@/lib/svgIntakeFlow";

const SCRIPT_TAG_RE = /<script\b[^>]*>[\s\S]*?<\/script>/gi;
const FOREIGN_OBJECT_RE = /<foreignObject\b[^>]*>[\s\S]*?<\/foreignObject>/gi;
const ON_EVENT_ATTR_RE = /\s+on[a-z]+\s*=\s*("([^"]*)"|'([^']*)')/gi;
const HREF_JS_RE = /(href|xlink:href)\s*=\s*"\s*javascript:[^"]*"/gi;

export const LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS";

/** Operator-facing parse status (raw codes stay in product_spec_json). */
export function humanizeVectorParseStatus(
  status: string | null | undefined
): string {
  switch (status) {
    case "parsed":
      return "SVG analizat";
    case "parsed_sanitized":
      return "SVG analizat în siguranță";
    case "failed":
      return "Analiză eșuată";
    default:
      return status?.trim() ? status : "—";
  }
}

/** Operator-facing vector analysis lifecycle status. */
export function humanizeVectorAnalysisStatus(
  status: string | null | undefined
): string {
  switch (status) {
    case "not_provided":
      return "Fără fișier";
    case "attached_unanalyzed":
      return "Fișier atașat — neanalizat";
    case "analyzed":
      return "Analizat";
    case "analysis_failed":
      return "Analiză eșuată";
    case "manual_review_approved":
      return "Review manual confirmat";
    default:
      return status?.trim() ? status : "—";
  }
}

/** Operator-facing layer mapping status from persisted summary. */
export function humanizeLayerMappingStatus(
  status: string | null | undefined,
  mappedBy?: string | null
): string {
  if (!status?.trim()) return "—";
  const base =
    status === "mapped"
      ? "Layer mapat"
      : status === "pending"
        ? "Mapare în așteptare"
        : status === "ignored"
          ? "Ignorat"
          : status;
  if (mappedBy === "manual") {
    return `${base} (manual)`;
  }
  return base;
}

export const MAPPING_ROLE_HELP: Record<string, string> = {
  "TPL-VOLUMETRIC-LETTERS":
    "Layer principal litere — folosit pentru gate vector litere (nu inventează metrici automat).",
  support_bars:
    "Bare/support spate — referință producție; nu intră în geometria literelor pentru ofertă.",
  mounting_reference:
    "Referință montaj/poziționare — orientativ, fără impact CostEngine.",
  ignore: "Layer ignorat (ghidaj/cote) — nu blochează maparea după confirmare explicită.",
};

export interface VectorDetectedLayerSummary {
  layer_name: string;
  mapping_status?: string;
  mapped_by?: string | null;
  mapped_target?: string | null;
  mapped_template_code?: string | null;
  detected_kind?: string | null;
}

export function buildSafeSvgPreview(svgText: string | null | undefined): string | null {
  if (!svgText?.trim()) return null;
  let cleaned = svgText.trim();
  cleaned = cleaned.replace(SCRIPT_TAG_RE, "");
  cleaned = cleaned.replace(FOREIGN_OBJECT_RE, "");
  cleaned = cleaned.replace(ON_EVENT_ATTR_RE, "");
  cleaned = cleaned.replace(HREF_JS_RE, "");
  const lowered = cleaned.toLowerCase();
  if (lowered.includes("<script") || lowered.includes("javascript:")) return null;
  if (lowered.includes("<!doctype") || lowered.includes("<!entity")) return null;
  if (!lowered.includes("<svg")) return null;
  return cleaned;
}

export function svgPreviewDataUrl(svgText: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgText)}`;
}

export function hasLettersLayerMapped(
  mappings: Record<string, string> | undefined
): boolean {
  return Object.values(mappings ?? {}).includes(LETTERS_TEMPLATE_CODE);
}

export function countSavedMappings(spec: IntakeProductSpec): number {
  return Object.keys(spec.svg_layer_mappings ?? {}).length;
}

export function formatSavedMappingsList(spec: IntakeProductSpec): string[] {
  if (!spec.svg_layer_mappings) return [];
  return Object.entries(spec.svg_layer_mappings).map(([k, v]) => `${k} → ${v}`);
}

export function buildDetectedLayersSummaryFromResult(
  result: SvgLayerAnalysisResult,
  mappings?: Record<string, string>
): VectorDetectedLayerSummary[] {
  return result.layers.map((layer) => ({
    layer_name: layer.svg_layer_name,
    mapping_status: layer.mapping_status,
    mapped_by: layer.mapped_by ?? null,
    mapped_target:
      mappings?.[layer.svg_layer_name] ??
      layer.mapped_template_code ??
      (layer.mapping_status === "ignored" ? "ignore" : null),
    mapped_template_code: layer.mapped_template_code,
    detected_kind: layer.detected_kind !== "unknown" ? layer.detected_kind : null,
  }));
}

/** Merge live analysis summary into spec for save — no raw SVG, no geometry invention. */
export function syncVectorAnalysisSummaryToSpec(
  spec: IntakeProductSpec,
  result: SvgLayerAnalysisResult
): IntakeProductSpec {
  const summary = buildDetectedLayersSummaryFromResult(result, spec.svg_layer_mappings);
  return {
    ...spec,
    vector_parse_status: result.parse_status,
    vector_analysis_warnings: result.warnings.length > 0 ? [...result.warnings] : undefined,
    vector_detected_layers_summary: summary.length > 0 ? summary : undefined,
    vector_preview_available: Boolean(result.preview_svg),
    vector_analysis_status: syncVectorAnalysisStatusFromParse(result.parse_status),
    vector_file_present: true,
    vector_file_type: spec.vector_file_type ?? "svg",
  };
}

export function extractTrustedMetrics(
  analysis: SvgLayerAnalysisResult | null
): { hasMetrics: boolean; labels: string[] } {
  if (!analysis) return { hasMetrics: false, labels: [] };
  const labels: string[] = [];
  for (const layer of analysis.layers) {
    const s = layer.quote_input_suggestions;
    if (s.letter_face_area_m2 != null) labels.push(`arie față: ${s.letter_face_area_m2} m²`);
    if (s.letter_perimeter_m != null) labels.push(`perimetru: ${s.letter_perimeter_m} m`);
    if (s.letter_count != null) labels.push(`număr litere: ${s.letter_count}`);
  }
  return { hasMetrics: labels.length > 0, labels };
}

export interface VectorStudioInfo {
  fileName: string;
  fileType: string;
  parseStatus: string | null;
  sanitized: boolean;
  analysisStatus: string;
  currentAnalysisLayersFound: number | null;
  savedMappingsCount: number;
  layersDetectedLabel: string;
  layersDetectedValue: string;
  savedMappingsList: string[];
  analysisDetailNote: string | null;
  lettersMapped: boolean;
  lettersLayerLabel: string;
  hasMetrics: boolean;
  metricLabels: string[];
  warnings: string[];
  previewUnavailableReason: string | null;
  hasLivePreview: boolean;
}

export function buildVectorStudioInfo(
  spec: IntakeProductSpec,
  analysis: SvgLayerAnalysisResult | null
): VectorStudioInfo {
  const metrics = extractTrustedMetrics(analysis);
  const savedMappingsCount = countSavedMappings(spec);
  const savedMappingsList = formatSavedMappingsList(spec);
  const persistedSummary = spec.vector_detected_layers_summary ?? [];
  const hasLiveAnalysis = Boolean(analysis && analysis.layers.length > 0);
  const hasPersistedSummary = persistedSummary.length > 0;

  const currentAnalysisLayersFound = hasLiveAnalysis
    ? (analysis!.summary?.layers_found ?? analysis!.layers.length)
    : hasPersistedSummary
      ? persistedSummary.length
      : null;

  let layersDetectedLabel = "Layere detectate (analiză curentă)";
  let layersDetectedValue: string;
  let analysisDetailNote: string | null = null;

  if (hasLiveAnalysis) {
    layersDetectedValue = String(currentAnalysisLayersFound);
  } else if (hasPersistedSummary) {
    layersDetectedValue = String(persistedSummary.length);
    analysisDetailNote =
      "Analiză efectuată anterior; reanalizează SVG-ul pentru detalii layer și preview.";
  } else if (savedMappingsCount > 0) {
    layersDetectedLabel = "Layere detectate (analiză curentă)";
    layersDetectedValue = "—";
    analysisDetailNote =
      "Rezultatul complet al analizei nu este salvat; reanalizează SVG-ul pentru detalii layer.";
  } else if (
    spec.vector_analysis_status === "analyzed" ||
    spec.vector_analysis_status === "manual_review_approved"
  ) {
    layersDetectedValue = "—";
    analysisDetailNote =
      "Analiză efectuată anterior; detaliile layerelor nu sunt disponibile în starea salvată.";
  } else {
    layersDetectedValue = "—";
  }

  const parseStatus =
    analysis?.parse_status ?? spec.vector_parse_status ?? null;
  const sanitized = Boolean(
    analysis?.sanitization?.analysis_sanitized ||
      spec.vector_analysis_warnings?.includes("svg_sanitized_doctype_removed")
  );

  const warnings: string[] = [];
  if (sanitized) {
    warnings.push("DOCTYPE eliminat pentru copia de analiză (fișierul sursă rămâne neschimbat).");
  }
  if (!hasLettersLayerMapped(spec.svg_layer_mappings)) {
    warnings.push("Layer principal litere nemapat.");
  }
  if (!metrics.hasMetrics && !hasGeometryEstimateInSpec(spec)) {
    warnings.push("Nu s-au extras metrici geometrice automat.");
  } else if (hasGeometryEstimateInSpec(spec) && !hasManualGeometryInSpec(spec)) {
    warnings.push(
      "Dimensiuni estimate din SVG — confirmă manual înainte de simulare dacă e necesar."
    );
  }
  if (
    spec.svg_layer_mappings &&
    Object.values(spec.svg_layer_mappings).includes("support_bars")
  ) {
    warnings.push("Layer support/bare nu este folosit ca geometrie litere.");
  }
  if (analysisDetailNote) {
    warnings.push(analysisDetailNote);
  }

  let previewUnavailableReason: string | null = null;
  if (!analysis?.preview_svg) {
    if (spec.vector_file_name && spec.vector_file_type === "svg") {
      if (spec.vector_preview_available) {
        previewUnavailableReason =
          "Preview-ul a fost disponibil la ultima analiză; reanalizează fișierul pentru preview.";
      } else {
        previewUnavailableReason =
          "Preview-ul nu este disponibil după refresh deoarece conținutul SVG nu este salvat în specificație. Reanalizează fișierul pentru preview.";
      }
    }
  }

  const lettersMapped = hasLettersLayerMapped(spec.svg_layer_mappings);
  const lettersLayerLabel = lettersMapped ? "mapat manual" : "lipsă";

  return {
    fileName: spec.vector_file_name ?? "—",
    fileType: spec.vector_file_type ?? "—",
    parseStatus,
    sanitized,
    analysisStatus: spec.vector_analysis_status ?? "not_provided",
    currentAnalysisLayersFound,
    savedMappingsCount,
    layersDetectedLabel,
    layersDetectedValue,
    savedMappingsList,
    analysisDetailNote,
    lettersMapped,
    lettersLayerLabel,
    hasMetrics: metrics.hasMetrics,
    metricLabels: metrics.labels,
    warnings,
    previewUnavailableReason,
    hasLivePreview: Boolean(analysis?.preview_svg),
  };
}

export function resolvePreviewUnavailableMessage(
  info: VectorStudioInfo,
  isSvg: boolean,
  hasPreviewUrl: boolean,
  pasteBlockedBySecurity: boolean
): string | null {
  if (hasPreviewUrl) return null;
  if (!isSvg) return null;
  if (pasteBlockedBySecurity) {
    return "Preview SVG indisponibil în siguranță. Fișierul poate fi folosit cu review manual.";
  }
  return (
    info.previewUnavailableReason ??
    "Preview-ul nu este disponibil după refresh deoarece conținutul SVG nu este salvat în specificație. Reanalizează fișierul pentru preview."
  );
}
