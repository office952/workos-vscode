import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import type { SvgLayerAnalysisResult } from "@/lib/svgLayerAnalysis";

export const MANUAL_SVG_LAYER_MAPPING_TARGETS = [
  { value: "", label: "— Nemapat" },
  { value: "TPL-VOLUMETRIC-LETTERS", label: "TPL-VOLUMETRIC-LETTERS (litere)" },
  { value: "support_bars", label: "support_bars (bare suport)" },
  { value: "mounting_reference", label: "mounting_reference (referință montaj)" },
  { value: "ignore", label: "ignore (ignoră layer)" },
] as const;

export type ManualSvgLayerMappingTarget =
  | "TPL-VOLUMETRIC-LETTERS"
  | "support_bars"
  | "mounting_reference"
  | "ignore";

const LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS";

export function deriveVectorLayerMappingStatus(
  mappings: Record<string, string> | undefined
): IntakeProductSpec["vector_layer_mapping_status"] {
  if (!mappings || Object.keys(mappings).length === 0) {
    return "pending";
  }
  if (Object.values(mappings).includes(LETTERS_TEMPLATE_CODE)) {
    return "mapped";
  }
  return "pending";
}

export function syncVectorAnalysisStatusFromParse(
  parseStatus: SvgLayerAnalysisResult["parse_status"]
): IntakeProductSpec["vector_analysis_status"] {
  if (parseStatus === "failed") {
    return "analysis_failed";
  }
  return "analyzed";
}

export function updateSvgLayerMapping(
  spec: IntakeProductSpec,
  layerName: string,
  target: string | undefined
): IntakeProductSpec {
  const current = { ...(spec.svg_layer_mappings ?? {}) };
  const trimmed = layerName.trim();
  if (!trimmed) return spec;
  if (!target) {
    delete current[trimmed];
  } else {
    current[trimmed] = target;
  }
  const mappings = Object.keys(current).length > 0 ? current : undefined;
  return {
    ...spec,
    svg_layer_mappings: mappings,
    vector_layer_mapping_status: deriveVectorLayerMappingStatus(mappings),
  };
}
