export type SheetQuoteReviewStatusLevel = "ok_auto" | "review_recommended" | "review_required";

export interface SheetQuoteReviewStatusInput {
  requires_manual_review?: boolean;
  recommended_auto_candidate?: { confidence?: "low" | "medium" | "high" } | null;
}

export function resolveSheetQuoteReviewStatus(
  candidates: SheetQuoteReviewStatusInput | null | undefined,
): SheetQuoteReviewStatusLevel {
  if (!candidates) return "ok_auto";
  if (candidates.requires_manual_review) return "review_required";
  const confidence = candidates.recommended_auto_candidate?.confidence;
  if (confidence === "low" || confidence === "medium") return "review_recommended";
  return "ok_auto";
}

export const SHEET_QUOTE_REVIEW_STATUS_LABELS: Record<SheetQuoteReviewStatusLevel, string> = {
  ok_auto: "OK automat",
  review_recommended: "Verificare recomandată",
  review_required: "Verificare operator obligatorie",
};
