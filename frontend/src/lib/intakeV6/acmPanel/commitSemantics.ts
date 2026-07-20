/**
 * AcmPanel operator field commit semantics — debounce constant + parse/flush types.
 * Draft ownership lives in useAcmPanelOperatorDrafts; writes stay on operatorPatch.
 */

import type { AcmOperatorFieldKey } from "./operatorPatch";

/** Single debounce window for numeric AcmPanel drafts (ms). */
export const ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS = 500;

export type AcmPanelFlushStatus =
  | "nothing_to_commit"
  | "committed"
  | "blocked_invalid";

export type AcmPanelFieldUpdate = {
  field: AcmOperatorFieldKey;
  value: number | boolean | 1 | 2;
};

export type AcmPanelFlushResult = {
  status: AcmPanelFlushStatus;
  updates: AcmPanelFieldUpdate[];
  invalidFields: AcmOperatorFieldKey[];
};

export const ACM_PANEL_DRAFT_NUMERIC_FIELDS = [
  "panel_width_mm",
  "panel_height_mm",
  "acm_thickness_mm",
  "l1_mm",
  "l2_mm",
  "fold_count",
] as const satisfies ReadonlyArray<AcmOperatorFieldKey>;

export type AcmPanelDraftNumericField = (typeof ACM_PANEL_DRAFT_NUMERIC_FIELDS)[number];

export function isAcmPanelDraftNumericField(
  field: string,
): field is AcmPanelDraftNumericField {
  return (ACM_PANEL_DRAFT_NUMERIC_FIELDS as readonly string[]).includes(field);
}

/** Incomplete typing — keep local; do not commit. */
export function isIncompleteNumericDraft(text: string): boolean {
  const t = text.trim();
  if (t === "" || t === "-" || t === "." || t === "-.") return true;
  if (t.endsWith(".")) return true;
  return false;
}

export type ParseAcmPanelDraftResult =
  | { ok: true; value: number | 1 | 2 }
  | { ok: false; reason: "empty" | "incomplete" | "invalid" };

export function parseAcmPanelNumericDraft(
  field: AcmOperatorFieldKey,
  text: string,
): ParseAcmPanelDraftResult {
  const t = text.trim().replace(",", ".");
  if (t === "") return { ok: false, reason: "empty" };
  if (isIncompleteNumericDraft(t)) return { ok: false, reason: "incomplete" };
  const n = Number(t);
  if (!Number.isFinite(n)) return { ok: false, reason: "invalid" };

  if (field === "fold_count") {
    if (n === 1 || n === 2) return { ok: true, value: n };
    return { ok: false, reason: "invalid" };
  }

  if (field === "internal_frame_enabled") {
    return { ok: false, reason: "invalid" };
  }

  // mm dimensions / thickness — must be positive finite
  if (n <= 0) return { ok: false, reason: "invalid" };
  return { ok: true, value: n };
}

export function canonicalNumberToDraftText(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "";
  return String(value);
}

export function valuesEqualForCommit(
  field: AcmOperatorFieldKey,
  parsed: number | boolean | 1 | 2,
  canonical: number | boolean | null | undefined,
): boolean {
  if (typeof parsed === "boolean") return parsed === Boolean(canonical);
  if (canonical === null || canonical === undefined) return false;
  if (field === "fold_count") return Number(parsed) === Number(canonical);
  return Number(parsed) === Number(canonical);
}

export function emptyFlushResult(
  status: AcmPanelFlushStatus = "nothing_to_commit",
): AcmPanelFlushResult {
  return { status, updates: [], invalidFields: [] };
}
