/**
 * Single ACM/support-panel inclusion-state model.
 *
 * F7E F1/B-F005 remediation: before this module, "is the ACM/Alucobond panel
 * actually in the offer" was answered independently (and inconsistently) by
 * the composition-card chip, the out-of-scope layer warning, and the raw
 * payload fields. This module is the one place that answers that question —
 * every surface must read `resolveAcmInclusionState()` / `isAcmPricedIntoOffer()`
 * instead of re-deriving it from raw payload fields.
 *
 * `isAcmPricedIntoOffer` mirrors the backend CPP authority (read-only mirror,
 * not a new truth): `services/letters_acm_composition_commercial_v1.py:is_letters_acm_composition_active`
 * gates the `letters_acm_conn_*` commercial lines on
 * `is_acm_boxed_mounting_payload(payload) && read_applied_content(payload) == "letters"`
 * (`services/acm_quote_input_helpers.py`, `services/acm_boxed_support_composition_v1.py`).
 * This frontend cannot import that Python module, so the exact same field
 * reads are reproduced here — do not diverge from the backend condition
 * without re-checking both sides.
 */

import { ACM_PANEL_TEMPLATE_CODE } from "./types";

export type AcmInclusionState =
  | "inactive"
  | "selected_incomplete"
  | "active_blocked"
  | "active_priced"
  | "included_in_base";

export type AcmInclusionStateResult = {
  state: AcmInclusionState;
  /** Mirrors backend is_letters_acm_composition_active(payload). */
  pricedIntoOffer: boolean;
  hasComponent: boolean;
  blocked: boolean;
};

type AppliedContent = "none" | "letters" | "logo";

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function readMountingSolution(container: Record<string, unknown> | null): Record<string, unknown> | null {
  return container ? asRecord(container.mounting_solution) : null;
}

/** Mirrors services/acm_quote_input_helpers.py:is_acm_boxed_mounting_payload (composition path only). */
function isAcmBoxedMountingPayload(payload: Record<string, unknown> | null): boolean {
  if (!payload) return false;
  const finish = asRecord(payload.finish_setup);
  const solution = readMountingSolution(finish) ?? readMountingSolution(payload);
  return String(solution?.template_code ?? "").trim() === ACM_PANEL_TEMPLATE_CODE;
}

function hasMeaningfulValue(raw: unknown): boolean {
  if (raw == null) return false;
  return String(raw).trim().length > 0;
}

function normalizeAppliedContent(raw: unknown): AppliedContent | null {
  if (raw == null) return "none";
  const text = String(raw).trim().toLowerCase();
  if (!text || text === "none" || text === "null" || text === "panel_only") return "none";
  if (text === "letters") return "letters";
  if (text === "logo") return "logo";
  return null;
}

/** Mirrors services/acm_boxed_support_composition_v1.py:read_applied_content. */
function readAppliedContent(payload: Record<string, unknown> | null): AppliedContent | null {
  if (!payload) return "none";
  const sources: unknown[] = [];
  if ("applied_content" in payload) sources.push(payload.applied_content);
  const finish = asRecord(payload.finish_setup);
  if (finish && "applied_content" in finish) sources.push(finish.applied_content);
  const quoteInput = asRecord(payload.quote_input);
  if (quoteInput && "applied_content" in quoteInput) sources.push(quoteInput.applied_content);
  const confirmed = asRecord(payload.product_composition_confirmed);
  if (confirmed && "applied_content" in confirmed) sources.push(confirmed.applied_content);

  const meaningful = sources.filter(hasMeaningfulValue).map(normalizeAppliedContent);
  const decisive = meaningful.find((value) => value === "letters" || value === "logo");
  if (decisive) return decisive;
  if (meaningful.length > 0) return meaningful[0] ?? null;
  return "none";
}

/** True when CPP prices the Letters↔ACM connection lines into the visible commercial total. */
export function isAcmPricedIntoOffer(payload: Record<string, unknown> | null | undefined): boolean {
  const rec = asRecord(payload);
  if (!rec) return false;
  if (!isAcmBoxedMountingPayload(rec)) return false;
  return readAppliedContent(rec) === "letters";
}

export function resolveAcmInclusionState(args: {
  payload: Record<string, unknown> | null | undefined;
  hasComponent: boolean;
  blocked: boolean;
}): AcmInclusionStateResult {
  const pricedIntoOffer = isAcmPricedIntoOffer(args.payload);
  if (!args.hasComponent) {
    return { state: "inactive", pricedIntoOffer: false, hasComponent: false, blocked: false };
  }
  if (pricedIntoOffer) {
    return {
      state: args.blocked ? "active_blocked" : "active_priced",
      pricedIntoOffer: true,
      hasComponent: true,
      blocked: args.blocked,
    };
  }
  return {
    state: "selected_incomplete",
    pricedIntoOffer: false,
    hasComponent: true,
    blocked: args.blocked,
  };
}

export type AcmInclusionTone = "ok" | "pending" | "blocker" | "muted";

export function acmInclusionStateLabelRo(state: AcmInclusionState): string {
  switch (state) {
    case "inactive":
      return "Neselectat";
    case "selected_incomplete":
      return "Selectat — nu este încă inclus în ofertă";
    case "active_blocked":
      return "Inclus, dar blocat — necesită rezolvare";
    case "active_priced":
      return "Inclus activ în ofertă";
    case "included_in_base":
      return "Inclus în prețul de bază";
    default: {
      const exhaustive: never = state;
      return exhaustive;
    }
  }
}

export function acmInclusionStateTone(state: AcmInclusionState): AcmInclusionTone {
  switch (state) {
    case "inactive":
      return "muted";
    case "selected_incomplete":
      return "pending";
    case "active_blocked":
      return "blocker";
    case "active_priced":
      return "ok";
    case "included_in_base":
      return "ok";
    default: {
      const exhaustive: never = state;
      return exhaustive;
    }
  }
}
