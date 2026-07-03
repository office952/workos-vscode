/**
 * SVG layer → template_code analysis (frontend types + UI helpers).
 * Canonical layer identity is ProductSystem template_code.
 */

import type { CostSimulationResponse } from "@/api/costSimulation";

export type SvgLayerMappingStatus =
  | "mapped"
  | "mapped_manual"
  | "ignored"
  | "unmapped"
  | "ambiguous"
  | "unsupported"
  | "suggested";

export interface SvgLayerMetricsPayload {
  bbox_width_mm?: number | null;
  bbox_height_mm?: number | null;
  bbox_area_m2?: number | null;
  path_perimeter_m?: number | null;
  path_area_m2?: number | null;
  metrics_confidence: "exact" | "estimated" | "unavailable";
}

export interface SvgLayerAnalysisRow {
  svg_layer_id: string;
  svg_layer_name: string;
  mapped_template_code: string | null;
  mapping_status: SvgLayerMappingStatus;
  suggested_template_code: string | null;
  human_description: string;
  detected_kind: string;
  metrics: SvgLayerMetricsPayload;
  quote_input_suggestions: Record<string, number | null>;
  blockers: string[];
  warnings: string[];
  mapped_by?: string | null;
}

export interface SvgLayerAnalysisResult {
  parse_status: "parsed" | "parsed_sanitized" | "failed";
  error_code?: string | null;
  error_detail?: string | null;
  layers: SvgLayerAnalysisRow[];
  summary: {
    layers_found?: number;
    layers_mapped?: number;
    layers_unmapped?: number;
    layers_calculable_preliminary?: number;
    layers_manual_geometry?: number;
  };
  warnings: string[];
  sanitization?: Record<string, unknown> | null;
  preview_svg?: string | null;
}

export interface SvgLayerSimulationRow {
  layer: SvgLayerAnalysisRow;
  template_id: number | null;
  simulation: CostSimulationResponse | null;
  error: string | null;
}

export interface SvgMultiLayerPreliminaryAggregate {
  layer_results: SvgLayerSimulationRow[];
  preliminary_total: number;
  is_partial: boolean;
  unmapped_count: number;
  blocked_count: number;
}

export function layerStatusLabel(row: SvgLayerAnalysisRow): string {
  if (row.mapping_status === "mapped_manual") {
    return row.mapped_by === "manual"
      ? "Mapat manual de operator"
      : "Mapat manual";
  }
  if (row.mapping_status === "ignored") {
    return "Layer ignorat";
  }
  if (row.mapping_status === "mapped") {
    if (row.blockers.includes("manual_geometry_required")) {
      return "Necesită date manuale";
    }
    if (row.blockers.includes("metrics_unavailable")) {
      return "Metrici SVG indisponibile";
    }
    return "Calcul preliminar disponibil";
  }
  if (row.blockers.includes("template_missing_for_svg_layer")) {
    return "Template lipsă";
  }
  if (row.mapping_status === "ambiguous") {
    return "Mapare ambiguă — verificare manuală";
  }
  return "Layer nemapat";
}

export function overallAnalysisWarning(): string {
  return (
    "Aceasta este analiză preliminară pe layere SVG. Nu creează ofertă finală și nu creează comandă."
  );
}

export function suggestionsToQuoteInputStrings(
  suggestions: Record<string, number | null>
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, val] of Object.entries(suggestions)) {
    if (val == null || !Number.isFinite(Number(val))) continue;
    out[key] = String(val);
  }
  return out;
}

export function aggregateLayerSimulations(
  rows: SvgLayerSimulationRow[]
): SvgMultiLayerPreliminaryAggregate {
  let total = 0;
  let blocked = 0;
  let unmapped = 0;
  for (const row of rows) {
    if (row.layer.mapping_status !== "mapped") {
      unmapped += 1;
      continue;
    }
    if (!row.simulation) {
      blocked += 1;
      continue;
    }
    const cost = row.simulation.cost_result?.total_cost;
    if (typeof cost === "number") {
      total += cost;
    }
    if (row.simulation.status === "blocked") {
      blocked += 1;
    }
  }
  return {
    layer_results: rows,
    preliminary_total: Math.round(total * 100) / 100,
    is_partial: unmapped > 0 || blocked > 0,
    unmapped_count: unmapped,
    blocked_count: blocked,
  };
}
