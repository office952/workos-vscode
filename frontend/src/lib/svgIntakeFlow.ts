/**
 * TPL-VOLUMETRIC-LETTERS — SVG intake flow helpers (parse status, letters layer, repair hints).
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { hasLettersLayerMapped, LETTERS_TEMPLATE_CODE } from "@/lib/vectorStudioPreview";
import type { SvgVectorDetectedLayer } from "@/lib/svgVectorAnalysis";
import {
  isSafeRoleSuggestion,
  suggestLayerRole,
  type VectorLayerRole,
} from "@/lib/svgLayerRoleSuggestion";

function isBlockedPrimaryLettersLayer(layer: SvgVectorDetectedLayer): boolean {
  const role =
    layer.confirmed_role !== "unknown" ? layer.confirmed_role : layer.suggested_role;
  return (
    role === "ignore" ||
    role === "guide_reference" ||
    role === "support_panel" ||
    role === "metal_frame"
  );
}

export type SvgParseUiStatus =
  | "not_selected"
  | "parsing"
  | "parsed"
  | "parsed_with_warnings"
  | "failed";

export type LettersLayerSuggestionConfidence = "high" | "medium" | "low";

const LETTERS_NAME_RE =
  /\b(litere|letters|text|logo|face|fata|față|front|literele|corp\s*litere)\b/i;
const AVOID_NAME_RE =
  /\b(cadru|frame|support|panel|dibond|back|fundal|outline|background|aux|emblema|emblem|logo|artwork|sigla|siglă)\b/i;

export interface PrimaryLettersLayerSuggestion {
  layerId: string;
  layerLabel: string;
  confidence: LettersLayerSuggestionConfidence;
  reason: string;
}

export function deriveSvgParseUiStatus(input: {
  fileName?: string;
  analyzing?: boolean;
  parseOk?: boolean;
  parseError?: string | null;
  warningCount?: number;
}): SvgParseUiStatus {
  if (input.analyzing) return "parsing";
  if (!input.fileName?.trim()) return "not_selected";
  if (input.parseError || input.parseOk === false) return "failed";
  if (input.parseOk) {
    return (input.warningCount ?? 0) > 0 ? "parsed_with_warnings" : "parsed";
  }
  return "not_selected";
}

export function parseStatusLabel(status: SvgParseUiStatus): string {
  switch (status) {
    case "not_selected":
      return "Neselectat";
    case "parsing":
      return "Se analizează…";
    case "parsed":
      return "Analizat cu succes";
    case "parsed_with_warnings":
      return "Analizat cu avertismente";
    case "failed":
      return "Analiză eșuată";
  }
}

export function scoreLettersLayerCandidate(layer: SvgVectorDetectedLayer): number {
  const name = `${layer.label} ${layer.id}`.replace(/[_-]/g, " ");
  if (isBlockedPrimaryLettersLayer(layer)) return -100;
  let score = 0;
  if (layer.suggested_role === "volumetric_letters") score += 40;
  if (layer.suggested_role === "letter_face") score += 30;
  if (LETTERS_NAME_RE.test(name)) score += 35;
  if (AVOID_NAME_RE.test(name)) score -= 50;
  score += Math.min(layer.element_count, 20);
  return score;
}

export function suggestPrimaryLettersLayer(
  layers: SvgVectorDetectedLayer[]
): PrimaryLettersLayerSuggestion | null {
  if (layers.length === 0) return null;

  const ranked = [...layers]
    .map((layer) => ({ layer, score: scoreLettersLayerCandidate(layer) }))
    .sort((a, b) => b.score - a.score);

  const best = ranked[0];
  if (!best || best.score <= 0) {
    const fallback = [...layers]
      .filter((layer) => !isBlockedPrimaryLettersLayer(layer))
      .sort((a, b) => b.element_count - a.element_count)[0];
    if (!fallback) return null;
    return {
      layerId: fallback.id,
      layerLabel: fallback.label,
      confidence: "low",
      reason: "Niciun nume clar pentru litere — sugestie după număr elemente.",
    };
  }

  let confidence: LettersLayerSuggestionConfidence = "low";
  if (best.score >= 60 && isSafeRoleSuggestion(best.layer.suggested_role)) {
    confidence = "high";
  } else if (best.score >= 35) {
    confidence = "medium";
  }

  const reason =
    best.layer.suggested_role === "volumetric_letters"
      ? `Nume/sugestie: layer litere volumetrice (${best.layer.label}).`
      : LETTERS_NAME_RE.test(best.layer.label)
        ? `Nume layer: „${best.layer.label}”.`
        : `Layer cu cele mai multe elemente relevante (${best.layer.element_count}).`;

  return {
    layerId: best.layer.id,
    layerLabel: best.layer.label,
    confidence,
    reason,
  };
}

/** Pre-fill confirmed_role from name heuristics (operator can override). */
export function applySuggestedLayerRoles(
  layers: SvgVectorDetectedLayer[]
): SvgVectorDetectedLayer[] {
  return layers.map((layer) => {
    if (layer.confirmed_role !== "unknown") return layer;
    const suggested = suggestLayerRole(layer.label);
    return {
      ...layer,
      suggested_role: suggested,
      confirmed_role: isSafeRoleSuggestion(suggested) ? suggested : "unknown",
    };
  });
}

export function confirmPrimaryLettersLayer(
  layers: SvgVectorDetectedLayer[],
  primaryLayerId: string
): SvgVectorDetectedLayer[] {
  return layers.map((layer) => {
    if (layer.id !== primaryLayerId) return layer;
    return {
      ...layer,
      confirmed_role: "volumetric_letters" as VectorLayerRole,
      suggested_role:
        layer.suggested_role === "unknown" ? "volumetric_letters" : layer.suggested_role,
    };
  });
}

export function isLettersLayerRole(role: VectorLayerRole): boolean {
  return role === "volumetric_letters" || role === "letter_face";
}

export function hasGeometryEstimateInSpec(spec: IntakeProductSpec | null | undefined): boolean {
  if (!spec) return false;
  if (spec.vector_geometry_analyzed !== true) return false;
  return (
    spec.vector_suggested_assembly_width_mm != null ||
    spec.vector_suggested_letter_layer_width_mm != null ||
    spec.vector_suggested_letter_element_count != null ||
    spec.vector_suggested_letter_perimeter_m != null ||
    spec.vector_suggested_letter_face_area_m2 != null ||
    spec.vector_suggested_support_area_m2 != null
  );
}

export function hasManualGeometryInSpec(spec: IntakeProductSpec | null | undefined): boolean {
  if (!spec) return false;
  return (
    (spec.letter_face_area_m2 ?? 0) > 0 ||
    (spec.letter_perimeter_m ?? 0) > 0 ||
    (spec.letter_count ?? 0) >= 1
  );
}

export function buildVectorIntakeRepairMissing(
  spec: IntakeProductSpec | null | undefined
): string[] {
  const missing: string[] = [];
  const s = spec ?? {};
  const pathway = s.intake_input_pathway;

  if (pathway !== "vector") return missing;

  if (!s.vector_file_name?.trim()) {
    missing.push("Încarcă/selectează SVG");
    return missing;
  }

  if (s.vector_analysis_status === "analysis_failed" || s.vector_parse_status === "failed") {
    missing.push("Verifică fișierul SVG — analiza a eșuat");
  }

  if (!hasLettersLayerMapped(s.svg_layer_mappings) && s.vector_layer_mapping_confirmed !== true) {
    missing.push("Confirmă layerul principal pentru litere");
  }

  if (
    !hasGeometryEstimateInSpec(s) &&
    !hasManualGeometryInSpec(s) &&
    s.vector_svg_analyzed === true
  ) {
    missing.push(
      "Verifică dimensiunile extrase sau completează manual dacă SVG-ul nu conține unități"
    );
  }

  if (!s.vector_fast_ask_applied_at) {
    missing.push("Aplică răspunsurile rapide vector (Aplică și salvează)");
  }

  if (
    s.vector_file_name &&
    !s.vector_layer_mapping_confirmed &&
    (s.vector_detected_layer_count ?? 0) > 0
  ) {
    missing.push("Confirmă maparea layerelor SVG");
  }

  return missing;
}

export function primaryLettersLayerFromSpec(
  spec: IntakeProductSpec | null | undefined,
  layers: SvgVectorDetectedLayer[]
): string | null {
  const id = spec?.vector_primary_letters_layer_id?.trim();
  if (id && layers.some((l) => l.id === id)) return id;
  const mapped = layers.find((l) => isLettersLayerRole(l.confirmed_role));
  return mapped?.id ?? null;
}

export function hasLocalLettersLayerMapped(
  layers: SvgVectorDetectedLayer[],
  primaryLettersLayerId?: string | null
): boolean {
  if (primaryLettersLayerId && layers.some((l) => l.id === primaryLettersLayerId)) {
    return true;
  }
  return layers.some((l) => isLettersLayerRole(l.confirmed_role));
}

/** Hide persisted-spec warnings superseded by live client-side parse state. */
export function filterVectorReviewWarningsForLocalParse(
  warnings: string[],
  context: {
    detectedLayers: SvgVectorDetectedLayer[];
    primaryLettersLayerId?: string | null;
    geometryParseOk?: boolean;
    mappingConfirmed?: boolean;
  }
): string[] {
  const lettersMapped =
    context.mappingConfirmed ||
    hasLocalLettersLayerMapped(context.detectedLayers, context.primaryLettersLayerId);
  const hasGeometry = context.geometryParseOk === true;

  return warnings.filter((w) => {
    if (lettersMapped && w.includes("Layer principal litere nemapat")) return false;
    if (hasGeometry && w.includes("Nu s-au extras metrici geometrice automat")) return false;
    return true;
  });
}

export function isFilenameOnlyWithoutSvgParse(input: {
  fileName?: string;
  hasFilePickMetadata?: boolean;
  parseOk?: boolean;
}): boolean {
  return (
    Boolean(input.fileName?.trim()) &&
    !input.hasFilePickMetadata &&
    input.parseOk !== true
  );
}

export { LETTERS_TEMPLATE_CODE };
