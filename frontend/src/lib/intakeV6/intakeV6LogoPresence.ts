/**
 * Domain-owned logo presence contract (R3).
 * Consumed by finish derivation, composition helpers, and operator UI.
 */

import type { LayerRoleConfirmation, SvgAnalysisCoreReport, SvgAnalysisLayer } from "@/lib/svgAnalyzer";
import { isArtworkOrLogoCandidateLayer } from "@/lib/svgAnalyzer/analyzer/artworkLogoCandidate";

export const LOGO_PRESENCE_VALUES = [
  "detected_confirmed",
  "optional_absent",
  "slot_available",
] as const;

export type LogoPresence = (typeof LOGO_PRESENCE_VALUES)[number];

const ARTWORK_ROLES = new Set(["printed_artwork", "logo", "cutout_logo"]);

const EXCLUDED_FINISH_ROLES = new Set([
  "support_panel",
  "face",
  "cutout_text",
  "ignore",
  "reference",
  "unknown",
]);

function layerEntry(
  confirmation: LayerRoleConfirmation,
  layer: SvgAnalysisLayer,
) {
  return (
    confirmation.layers.find((item) => item.layerKey === layer.id || item.layerKey === layer.name) ??
    confirmation.layers.find((item) => item.layerName === layer.name)
  );
}

export function isExcludedFromArtworkFinish(
  role: string | null | undefined,
): boolean {
  if (!role) return false;
  return EXCLUDED_FINISH_ROLES.has(role) || role === "support_panel" || role === "face";
}

export function layerQualifiesAsArtworkFinishSource(
  layer: SvgAnalysisLayer,
  role: string | null | undefined,
): boolean {
  if (isExcludedFromArtworkFinish(role)) return false;
  if (role && ARTWORK_ROLES.has(role)) return true;
  if (isArtworkOrLogoCandidateLayer(layer) && role !== "support_panel" && role !== "face") {
    return ARTWORK_ROLES.has(role ?? "") || layer.autoRole === "printed_artwork" || layer.autoRole === "logo";
  }
  return false;
}

/**
 * - detected_confirmed: at least one artwork/logo role confirmed OR pending with artwork auto-role from SVG
 * - optional_absent: no artwork/logo candidates in analysis
 * - slot_available: product may accept logo later; none detected in SVG (empty affordance only)
 */
export function resolveLogoPresence(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
): LogoPresence {
  if (!report?.layers?.length) return "optional_absent";

  const candidates = report.layers.filter((layer) => isArtworkOrLogoCandidateLayer(layer));
  if (candidates.length === 0) {
    // No SVG logo candidates → absent (not a priced/visible Vector Logo).
    // slot_available is reserved for explicit empty product affordance (composition-level).
    return "optional_absent";
  }

  if (!confirmation) return "detected_confirmed";

  let anyConfirmed = false;
  let anyPendingArtwork = false;
  for (const layer of candidates) {
    const entry = layerEntry(confirmation, layer);
    if (!entry || entry.confirmationState === "ignored") continue;
    const role = entry.confirmedRole ?? entry.autoRole;
    if (isExcludedFromArtworkFinish(role)) continue;
    if (entry.confirmationState === "confirmed" && ARTWORK_ROLES.has(role ?? "")) {
      anyConfirmed = true;
    }
    if (ARTWORK_ROLES.has(role ?? "") || ARTWORK_ROLES.has(entry.autoRole ?? "")) {
      anyPendingArtwork = true;
    }
  }

  if (anyConfirmed || anyPendingArtwork) return "detected_confirmed";
  return "optional_absent";
}

export function logoPresenceAllowsArtworkFinishRows(presence: LogoPresence): boolean {
  return presence === "detected_confirmed";
}
