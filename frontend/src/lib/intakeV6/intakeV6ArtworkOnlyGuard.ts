import type { LayerRoleConfirmation, SvgAnalysisCoreReport, SvgAnalysisLayer } from "@/lib/svgAnalyzer";
import type { LayerAutoRole } from "@/lib/svgAnalyzer/analyzer/layerRoleTypes";
import { isArtworkOrLogoCandidateLayer } from "@/lib/svgAnalyzer/analyzer/artworkLogoCandidate";
import { isArtworkLayerName } from "@/lib/intakeSvgContracts";

export const ARTWORK_ONLY_REQUIRES_DECISION_CODE = "artwork_only_requires_decision";

export const ARTWORK_ONLY_STEP1_MESSAGE =
  "Fișierul pare să conțină logo/vector constructiv fără straturi de litere volumetrice.";

export const ARTWORK_ONLY_REVIEW_TITLE = "Logo / vector constructiv necesită confirmare";

export const ARTWORK_ONLY_CONFIRM_MESSAGES = [
  "Nu există straturi de litere volumetrice confirmate.",
  "Logo/vector constructiv necesită confirmare operator.",
  "Analyzer-ul va recomanda compoziția de produs înainte de Review.",
] as const;

export function layerHasLetterPathGeometry(layer: SvgAnalysisLayer): boolean {
  if (layer.pathElementCount > 0 && (layer.closedSubPathCount > 0 || layer.subPathCount > 0)) {
    return true;
  }
  if (layer.layerKind === "pseudo" && layer.pathElementCount > 0) {
    return true;
  }
  return false;
}

export function layerIsArtworkCandidate(layer: SvgAnalysisLayer): boolean {
  if (isArtworkOrLogoCandidateLayer(layer)) return true;
  if (layer.autoRole === "support_panel" || layer.autoRole === "face") return false;
  if (layer.autoRole === "printed_artwork" || layer.autoRole === "logo") return true;
  if (isArtworkLayerName(layer.name) || isArtworkLayerName(layer.id)) return true;

  const paint = layer.paintEvidence;
  // Real policromie only (fill+stroke technical contour is "solid" after paint fix).
  if (paint?.paintKind === "policromie" || paint?.hasGradient || paint?.hasPattern || paint?.hasImage) {
    return true;
  }

  const colors = layer.colors ?? [];
  if (colors.some((color) => /^url\(#/i.test(color))) return true;

  if (
    layer.pathElementCount === 0 &&
    layer.elementCount > 0 &&
    (layer.autoRole === "unknown" || layer.autoRole === "reference")
  ) {
    if (
      paint?.hasGradient ||
      paint?.paintKind === "policromie" ||
      (paint?.gradientRefs?.length ?? 0) > 0 ||
      colors.some((color) => /^url\(#/i.test(color))
    ) {
      return true;
    }
  }

  if (layer.pathElementCount === 0 && layer.elementCount > 0 && layer.autoRole === "unknown") {
    return true;
  }

  return false;
}

function layerEntry(
  confirmation: LayerRoleConfirmation,
  layer: SvgAnalysisLayer,
) {
  return (
    confirmation.layers.find((item) => item.layerKey === layer.id || item.layerKey === layer.name) ??
    confirmation.layers.find((item) => item.layerName === layer.name)
  );
}

export function hasConfirmedLetterLayers(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
): boolean {
  if (!report || !confirmation) return false;

  for (const layer of report.layers) {
    const entry = layerEntry(confirmation, layer);
    if (!entry || entry.confirmationState === "ignored") continue;
    const role = entry.confirmedRole ?? entry.autoRole;
    if (role === "face" && layerHasLetterPathGeometry(layer)) return true;
  }
  return false;
}

export function detectArtworkOnlyRequiresDecision(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
): boolean {
  if (!report?.layers.length || !confirmation) return false;
  if (hasConfirmedLetterLayers(report, confirmation)) return false;

  const drawableLayers = report.layers.filter((layer) => layer.elementCount > 0);
  if (drawableLayers.length === 0) return false;

  return drawableLayers.every((layer) => !layerHasLetterPathGeometry(layer));
}

export function resolveConfirmAllSuggestedRole(
  layer: LayerRoleConfirmation["layers"][number],
  reportLayer: SvgAnalysisLayer | undefined,
): LayerAutoRole | null {
  // Never bulk-accept Contur suport on artwork/logo candidates (R2 / R4).
  if (
    layer.autoRole === "support_panel" &&
    reportLayer &&
    isArtworkOrLogoCandidateLayer(reportLayer)
  ) {
    return null;
  }
  // Do not bulk-accept low-confidence or contradictory support proposals.
  if (layer.autoRole === "support_panel" && layer.autoConfidence === "low") {
    return null;
  }
  if (layer.autoRole !== "unknown") return layer.autoRole;
  if (reportLayer && layerHasLetterPathGeometry(reportLayer)) return "face";
  if (reportLayer && layerIsArtworkCandidate(reportLayer)) return null;
  return null;
}

export function artworkOnlyDecisionPending(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
): boolean {
  if (!detectArtworkOnlyRequiresDecision(report, confirmation) || !report || !confirmation) {
    return false;
  }

  for (const layer of report.layers) {
    const entry = layerEntry(confirmation, layer);
    if (!entry || entry.confirmationState === "ignored") continue;
    if (!layerIsArtworkCandidate(layer)) continue;

    const role = entry.confirmedRole ?? entry.autoRole;
    if (entry.confirmationState === "pending") return true;
    if (role === "face") return true;
    if (role === "unknown") return true;
  }
  return false;
}

export function formatArtworkOnlyBlocker(code: string): string | null {
  if (code !== ARTWORK_ONLY_REQUIRES_DECISION_CODE) return null;
  return ARTWORK_ONLY_CONFIRM_MESSAGES.join(" ");
}

export function sanitizeLetterGroupsForArtworkOnlyGuard<T extends { group_key: string }>(
  groups: T[],
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
): T[] {
  if (detectArtworkOnlyRequiresDecision(report, confirmation)) return [];
  return groups;
}

export function resolveArtworkOnlyReviewWarnings(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
  existing: string[] | null | undefined,
): string[] {
  const warnings = [...(existing ?? [])];
  if (detectArtworkOnlyRequiresDecision(report, confirmation)) {
    if (!warnings.includes(ARTWORK_ONLY_REQUIRES_DECISION_CODE)) {
      warnings.unshift(ARTWORK_ONLY_REQUIRES_DECISION_CODE);
    }
  }
  return warnings;
}

export function resolveArtworkOnlyFatalBlockers(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
  existing: string[] | null | undefined,
): string[] {
  const blockers = [...(existing ?? [])];
  if (detectArtworkOnlyRequiresDecision(report, confirmation)) {
    if (!blockers.includes(ARTWORK_ONLY_REQUIRES_DECISION_CODE)) {
      blockers.unshift(ARTWORK_ONLY_REQUIRES_DECISION_CODE);
    }
    return blockers.filter(
      (code) => !code.startsWith("missing_face_oracal_color:") && !code.startsWith("missing_ral_color:"),
    );
  }
  return blockers;
}

export function artworkOnlyLayerDisplayType(layer: SvgAnalysisLayer): string {
  const paint = layer.paintEvidence;
  if (paint?.paintKind === "policromie" || paint?.hasGradient) return "vector constructiv / finisaj complex";
  if (layer.autoRole === "printed_artwork") return "logo / vector constructiv";
  if (isArtworkLayerName(layer.name) || isArtworkLayerName(layer.id)) return "logo / vector constructiv";
  return "vector constructiv";
}
