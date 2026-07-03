/**
 * Merge client-side SVG analysis into product_spec_json — metadata only.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import type { SvgVectorAnalysis, SvgVectorDetectedLayer } from "@/lib/svgVectorAnalysis";
import type { VectorLayerRole } from "@/lib/svgLayerRoleSuggestion";
import { preservePathwayForVectorMetadata } from "@/lib/volumetricIntakePathway";
import { LETTERS_TEMPLATE_CODE } from "@/lib/vectorStudioPreview";

function roleToLegacyMappingTarget(role: VectorLayerRole): string | undefined {
  switch (role) {
    case "volumetric_letters":
    case "letter_face":
      return LETTERS_TEMPLATE_CODE;
    case "support_panel":
    case "metal_frame":
      return "support_bars";
    case "guide_reference":
      return "mounting_reference";
    case "ignore":
      return "ignore";
    default:
      return undefined;
  }
}

function buildSvgLayerMappings(
  layers: SvgVectorDetectedLayer[]
): Record<string, string> | undefined {
  const mappings: Record<string, string> = {};
  for (const layer of layers) {
    const target = roleToLegacyMappingTarget(layer.confirmed_role);
    if (target) {
      mappings[layer.label] = target;
    }
  }
  return Object.keys(mappings).length > 0 ? mappings : undefined;
}

function buildDetectedLayersSummary(layers: SvgVectorDetectedLayer[]) {
  return layers.map((layer) => ({
    layer_name: layer.label,
    mapping_status: layer.confirmed_role === "unknown" ? "unmapped" : "mapped_manual",
    mapped_by: layer.confirmed_role !== "unknown" ? "manual" : null,
    mapped_target: roleToLegacyMappingTarget(layer.confirmed_role) ?? null,
    mapped_template_code:
      layer.confirmed_role === "volumetric_letters" ||
      layer.confirmed_role === "letter_face"
        ? LETTERS_TEMPLATE_CODE
        : null,
    detected_kind: layer.suggested_role !== "unknown" ? layer.suggested_role : null,
  }));
}

export function mapSvgVectorAnalysisToProductSpec(
  spec: IntakeProductSpec,
  analysis: SvgVectorAnalysis,
  options?: {
    layerMappingConfirmed?: boolean;
    primaryLettersLayerId?: string;
    lettersLayerConfidence?: "high" | "medium" | "low";
  }
): IntakeProductSpec {
  const next: IntakeProductSpec = { ...spec };

  if (!analysis.vector_svg_analyzed || !analysis.parse_ok) {
    if (analysis.parse_error) {
      next.vector_analysis_status = "analysis_failed";
      next.vector_parse_status = "failed";
      next.vector_analysis_warnings = [
        ...(spec.vector_analysis_warnings ?? []),
        analysis.parse_error,
        ...analysis.warnings,
      ].filter(Boolean);
    }
    return preservePathwayForVectorMetadata(next);
  }

  next.vector_svg_analyzed = true;
  next.vector_svg_width = analysis.width;
  next.vector_svg_height = analysis.height;
  next.vector_svg_viewbox = analysis.view_box;
  next.vector_detected_layer_count = analysis.layers.length;
  next.vector_detected_layers = analysis.layers.map((l) => ({
    id: l.id,
    label: l.label,
    element_count: l.element_count,
    suggested_role: l.suggested_role,
    confirmed_role: l.confirmed_role,
  }));
  next.vector_layer_analysis_warnings =
    analysis.warnings.length > 0 ? [...analysis.warnings] : undefined;
  next.vector_analysis_status = "analyzed";
  next.vector_parse_status = "parsed";
  next.vector_detected_layers_summary = buildDetectedLayersSummary(analysis.layers);

  const mappings = buildSvgLayerMappings(analysis.layers);
  if (mappings) {
    next.svg_layer_mappings = { ...(spec.svg_layer_mappings ?? {}), ...mappings };
    next.vector_layer_mapping_status = Object.values(mappings).includes(LETTERS_TEMPLATE_CODE)
      ? "mapped"
      : "pending";
  }

  if (options?.primaryLettersLayerId) {
    const primary = analysis.layers.find((l) => l.id === options.primaryLettersLayerId);
    if (primary) {
      next.vector_primary_letters_layer_id = primary.id;
      next.vector_primary_letters_layer_name = primary.label;
      if (options.lettersLayerConfidence) {
        next.vector_letters_layer_suggestion_confidence = options.lettersLayerConfidence;
      }
    }
  }

  if (options?.layerMappingConfirmed) {
    next.vector_layer_mapping_confirmed = true;
    next.vector_layer_mapping_confirmed_at = new Date().toISOString();
    if (analysis.layers.length > 0) {
      next.vector_layer_alignment_status = "aligned";
    }
  }

  return preservePathwayForVectorMetadata(next);
}

export function rehydrateLayersFromSpec(
  spec: IntakeProductSpec | null | undefined
): SvgVectorDetectedLayer[] {
  if (!spec?.vector_detected_layers?.length) return [];
  return spec.vector_detected_layers.map((row) => ({
    id: row.id,
    label: row.label,
    element_count: row.element_count,
    suggested_role: row.suggested_role as VectorLayerRole,
    confirmed_role: row.confirmed_role as VectorLayerRole,
    is_inkscape_layer: false,
  }));
}
