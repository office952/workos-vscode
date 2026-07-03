export interface ManualReviewReasonContext {
  orphan_defs_split_placement_sqm?: number | null;
  manual_review_reason?: string | null;
}

export function humanizeManualReviewReason(token: string): string {
  if (token.startsWith("candidateSpread=")) {
    return `Metrici divergente (${token}) — compară candidații din tabel.`;
  }
  if (token === "stale_orphan_defs_split_placement") {
    return "Snapshot posibil învechit — orphan defs/clipPath în nesting (nu e material face real).";
  }
  if (token === "orphan_defs_parts_in_analysis") {
    return "Piese orphan defs detectate în analiză — re-analiză recomandată.";
  }
  if (token.startsWith("layoutOccupied/childPartBBox")) {
    return "Shelf nesting mult mai mare decât suma bbox piese — nu folosi shelf ca preț.";
  }
  if (token === "pseudo_layer_or_unlayered_complexity") {
    return "Fișier fără straturi Corel / pseudo-layer — verificare manuală recomandată.";
  }
  if (token === "face_layer_filled_area_missing") {
    return "Lipsă filled area pe straturi face — candidatul eligibil poate fi incomplet.";
  }
  if (token === "operator_manual_corel_measurement_present") {
    return "Footprint manual Corel salvat — folosit doar ca preview intern.";
  }
  return token;
}

export function isStaleSvgSnapshotReview(
  candidates: ManualReviewReasonContext | null | undefined,
): boolean {
  if (!candidates) return false;
  return (candidates.orphan_defs_split_placement_sqm ?? 0) > 0;
}

export function isFreshSvgSnapshotAfterReanalysis(
  candidates: (ManualReviewReasonContext & { requires_manual_review?: boolean }) | null | undefined,
): boolean {
  if (!candidates?.requires_manual_review) return false;
  if (isStaleSvgSnapshotReview(candidates)) return false;
  const reason = candidates.manual_review_reason ?? "";
  return reason.includes("pseudo_layer_or_unlayered_complexity");
}

export function filterActiveManualReviewReasonTokens(
  reason: string | null | undefined,
  candidates: ManualReviewReasonContext | null | undefined,
): string[] {
  const parts = (reason ?? "")
    .split(";")
    .map((part) => part.trim())
    .filter(Boolean);
  if (!candidates) return parts;
  const orphanSqm = candidates.orphan_defs_split_placement_sqm ?? 0;
  const stale = isStaleSvgSnapshotReview(candidates);
  return parts.filter((token) => {
    if (!stale && (token === "stale_orphan_defs_split_placement" || token === "orphan_defs_parts_in_analysis")) {
      return false;
    }
    if (orphanSqm <= 0 && token.includes("orphan_defs")) return false;
    return true;
  });
}

export function formatManualReviewReasons(reason: string | null | undefined): string[] {
  if (!reason?.trim()) return [];
  return reason
    .split(";")
    .map((part) => part.trim())
    .filter(Boolean)
    .map(humanizeManualReviewReason);
}

export function formatActiveManualReviewReasons(
  reason: string | null | undefined,
  candidates: ManualReviewReasonContext | null | undefined,
): string[] {
  return filterActiveManualReviewReasonTokens(reason, candidates).map(humanizeManualReviewReason);
}

export const SHEET_QUOTE_FRESH_SNAPSHOT_OWNER_NOTE =
  "Snapshot SVG actualizat. Geometria orphan defs veche a fost eliminată. Verificarea operator poate rămâne recomandată dacă metricile încă diverg.";
