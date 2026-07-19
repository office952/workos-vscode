/**
 * Frontend authority for legacy power_supply_service_corner vs segmented electrical.
 * Does not mutate backend contracts — only guides UI visibility.
 */

import { readSegmentedBackground } from "./segmentedBackground";

export type ServiceCornerUiMode =
  | "legacy_authoritative"
  | "legacy_hidden_segmented_confirmed"
  | "legacy_demoted_segmented_pending";

export function resolveServiceCornerUiMode(
  finish: Record<string, unknown> | null | undefined,
): ServiceCornerUiMode {
  const segmented = readSegmentedBackground(finish);
  if (!segmented) return "legacy_authoritative";

  const status = String(segmented.status || "").toUpperCase();
  const panelCount = Array.isArray(segmented.panels) ? segmented.panels.length : 0;
  const multiPanel = panelCount >= 2;

  if (status === "CONFIRMED" && multiPanel) {
    return "legacy_hidden_segmented_confirmed";
  }

  if (multiPanel && (status === "PROPOSED" || status === "DRAFT" || status === "REJECTED")) {
    return "legacy_demoted_segmented_pending";
  }

  return "legacy_authoritative";
}

export function shouldShowLegacyServiceCornerInput(
  finish: Record<string, unknown> | null | undefined,
): boolean {
  return resolveServiceCornerUiMode(finish) !== "legacy_hidden_segmented_confirmed";
}

export function legacyServiceCornerDemotedNoteRo(): string {
  return "Ansamblu multi-panou în curs — colțul service unic nu este autoritar. Confirmă panourile și alimentarea 220V pe panouri.";
}

export function legacyServiceCornerSupersededNoteRo(): string {
  return "Ansamblu multi-panou confirmat — alimentarea 220V pe panouri este autoritară. Colțul service unic nu se mai configurează aici.";
}
