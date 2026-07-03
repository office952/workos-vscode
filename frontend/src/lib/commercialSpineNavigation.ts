/**
 * Commercial runtime spine — URL targets and QuoteWizard navigation state.
 * Display/routing only; does not change quote/order policy or CostEngine.
 */

import type { NavigateFunction } from "react-router-dom";
import type { QuoteCreatedPayload } from "@/api/quotes";
import type { IntakeRequest, QuoteStatus } from "@/lib/mockData";
import type { VolumetricQuoteNavState } from "@/lib/volumetricQuoteFlowState";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

/** Terminal closed — no reopen or mutate (view only). */
export const TERMINAL_CLOSED_QUOTE_STATUSES: QuoteStatus[] = [
  "rejected",
  "expired",
];

export function isTerminalClosedQuoteStatus(status: QuoteStatus): boolean {
  return status === "rejected" || status === "expired";
}

export function terminalClosedQuoteMessage(status: QuoteStatus): string {
  if (status === "rejected") {
    return "Ofertă respinsă — nu mai sunt acțiuni comerciale disponibile.";
  }
  if (status === "expired") {
    return "Ofertă expirată — nu mai sunt acțiuni comerciale disponibile.";
  }
  return "Ofertă terminală — nu mai sunt acțiuni disponibile.";
}

export function buildQuoteWizardNavStateFromIntake(
  intake: Pick<
    IntakeRequest,
    | "id"
    | "client"
    | "status"
    | "deliveryType"
    | "productSpec"
    | "confirmedTemplateCode"
    | "siteAudit"
  >,
  options?: { openWizard?: boolean }
): VolumetricQuoteNavState {
  const templateCode =
    (intake.confirmedTemplateCode ?? "").trim() || TPL_VOLUMETRIC_LETTERS;
  return {
    openWizard: options?.openWizard ?? true,
    templateCode,
    productSpec: intake.productSpec ?? null,
    clientName: intake.client,
    intakeRequestId: intake.id,
    fromIntake: true,
    confirmedTemplateCode: templateCode,
    deliveryType: intake.deliveryType,
    siteAudit: intake.siteAudit ?? null,
    intakeStatus: intake.status,
  };
}

export function quoteDetailPath(quoteId: string): string {
  return `/quotes/${encodeURIComponent(quoteId)}`;
}

/** Route key for Quotes detail — prefers commercial quote_code over numeric id. */
export function resolveCreatedQuoteRouteId(created: QuoteCreatedPayload): string {
  const code = created.quoteCode?.trim();
  if (code) return code;
  return String(created.quoteId);
}

export function orderDetailPath(orderId: string): string {
  return `/orders/${encodeURIComponent(orderId)}`;
}

export function executionDetailPath(orderId: string): string {
  return `/execution/${encodeURIComponent(orderId)}`;
}

/** Open quote list with optional wizard prefill (intake handoff). */
export function navigateToQuotesList(
  navigate: NavigateFunction,
  state?: VolumetricQuoteNavState
): void {
  navigate("/quotes", state ? { state } : undefined);
}

/** Open a specific quote by code (QT-*). */
export function navigateToQuoteDetail(
  navigate: NavigateFunction,
  quoteId: string,
  state?: VolumetricQuoteNavState
): void {
  navigate(quoteDetailPath(quoteId), state ? { state } : undefined);
}

export function navigateToOrderDetail(
  navigate: NavigateFunction,
  orderId: string
): void {
  navigate(orderDetailPath(orderId));
}
