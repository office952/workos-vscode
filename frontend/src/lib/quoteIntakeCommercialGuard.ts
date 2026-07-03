import type { Quote } from "@/lib/mockData";

const GUARDED_INTAKE_PREFIX = "IV3-";
const LEGACY_LINKAGE_KEY = "intake_v3_linkage_v1";

export interface QuoteIntakeCommercialGuard {
  isGuardedQuote: boolean;
  requiresPricingReview: boolean;
  pricingReviewCompleted: boolean;
  pricedDraft: boolean;
  guardedAcceptReady: boolean;
  guardedAcceptCompleted: boolean;
  guardedConvertReady: boolean;
  orderCreated: boolean;
  handoffPreviewReady: boolean;
  productionReadinessAuditRequired: boolean;
  acceptBlocked: boolean;
  convertBlocked: boolean;
  blockedMessage: string | null;
  acceptBlockedMessage: string | null;
  convertBlockedMessage: string | null;
}

export function parseQuoteIntakeLinkageFromNotes(
  notes: string | undefined,
): Record<string, unknown> | null {
  if (!notes?.trim()) return null;
  try {
    const payload = JSON.parse(notes) as unknown;
    if (!payload || typeof payload !== "object") return null;
    const linkage = (payload as Record<string, unknown>)[LEGACY_LINKAGE_KEY];
    return linkage && typeof linkage === "object"
      ? (linkage as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

export function isGuardedQuotePricingReviewCompleted(
  linkage: Record<string, unknown> | null,
): boolean {
  if (!linkage) return false;
  if (linkage.priced_draft === true) return true;
  const pricingReview = linkage.pricing_review;
  if (pricingReview && typeof pricingReview === "object") {
    return (pricingReview as Record<string, unknown>).status === "completed";
  }
  return false;
}

function isGuardedAcceptCompleted(
  linkage: Record<string, unknown> | null,
  quoteStatus: Quote["status"],
): boolean {
  const record = linkage?.accept_decision;
  if (record && typeof record === "object") {
    if ((record as Record<string, unknown>).status === "approved") return true;
  }
  return quoteStatus === "accepted" && isGuardedQuotePricingReviewCompleted(linkage);
}

function isGuardedConvertCompleted(linkage: Record<string, unknown> | null): boolean {
  const record = linkage?.convert_decision;
  if (record && typeof record === "object") {
    const typed = record as Record<string, unknown>;
    return typed.status === "approved" && typed.order_created === true;
  }
  return false;
}

function isGuardedHandoffPreviewReady(linkage: Record<string, unknown> | null): boolean {
  if (!isGuardedConvertCompleted(linkage)) return false;
  const sections = (linkage?.snapshot as Record<string, unknown> | undefined)?.sections;
  if (!sections || typeof sections !== "object") return false;
  const confirmed = (sections as Record<string, unknown>).confirmed_production_model_snapshot;
  const finish = (sections as Record<string, unknown>).finish_assignment_snapshot;
  return Boolean(confirmed) && Boolean(finish);
}

export function getQuoteIntakeCommercialGuard(quote: Quote): QuoteIntakeCommercialGuard {
  const intakeCode = quote.intakeId?.trim() ?? "";
  const linkage = parseQuoteIntakeLinkageFromNotes(quote.notes);
  const isGuardedQuote = intakeCode.startsWith(GUARDED_INTAKE_PREFIX) && linkage != null;
  const pricingReviewCompleted = isGuardedQuotePricingReviewCompleted(linkage);
  const pricedDraft = pricingReviewCompleted || linkage?.priced_draft === true;
  const requiresPricingReview =
    isGuardedQuote &&
    Boolean(linkage?.requires_pricing_review ?? true) &&
    !pricingReviewCompleted;
  const guardedAcceptCompleted = isGuardedQuote && isGuardedAcceptCompleted(linkage, quote.status);
  const orderCreated = isGuardedQuote && isGuardedConvertCompleted(linkage);
  const handoffPreviewReady = isGuardedQuote && isGuardedHandoffPreviewReady(linkage);
  const productionReadinessAuditRequired = orderCreated && !handoffPreviewReady;
  const guardedAcceptReady =
    isGuardedQuote &&
    pricingReviewCompleted &&
    !requiresPricingReview &&
    quote.status === "draft" &&
    !guardedAcceptCompleted;
  const guardedConvertReady =
    isGuardedQuote && guardedAcceptCompleted && quote.status === "accepted" && !orderCreated;

  const acceptBlocked = isGuardedQuote;
  const convertBlocked = isGuardedQuote;

  let blockedMessage: string | null = null;
  let acceptBlockedMessage: string | null = null;
  let convertBlockedMessage: string | null = null;

  if (isGuardedQuote) {
    if (requiresPricingReview) {
      blockedMessage = "This Intake V3 draft quote requires pricing review before accept/convert.";
      acceptBlockedMessage = "Pricing review is required before accept/convert can be considered.";
      convertBlockedMessage = acceptBlockedMessage;
    } else if (handoffPreviewReady) {
      blockedMessage = "Production handoff is preview-ready. Production task dry-run is available as a preview. Real task generation remains blocked.";
      acceptBlockedMessage = "Quote accepted and converted via IV3 guarded flows.";
      convertBlockedMessage = "Order created. Production task dry-run is available as a preview. Real task generation remains blocked.";
    } else if (orderCreated) {
      blockedMessage = "Order created. Production readiness audit, material breakdown, and production task dry-run preview are available before real task generation.";
      acceptBlockedMessage = "Quote accepted and converted via IV3 guarded flows.";
      convertBlockedMessage = "Order created. Use Intake V3 workspace for production readiness audit.";
    } else if (guardedConvertReady) {
      blockedMessage = "Quote accepted. Convert to order requires guarded IV3 conversion.";
      acceptBlockedMessage = "Quote accepted via IV3 guarded accept.";
      convertBlockedMessage =
        "Convert ready in Intake V3 workspace — generic Quotes convert remains blocked.";
    } else if (guardedAcceptCompleted) {
      blockedMessage = "Intake V3 quote accepted — convert uses guarded IV3 flow.";
      acceptBlockedMessage = "Use Intake V3 workspace for accept; generic accept remains blocked.";
      convertBlockedMessage = "Convert to order requires guarded IV3 conversion.";
    } else if (guardedAcceptReady) {
      blockedMessage =
        "Pricing review completed — use Intake V3 guarded accept; generic accept remains blocked.";
      acceptBlockedMessage =
        "Accept ready in Intake V3 workspace — generic Quotes accept remains blocked for IV3.";
      convertBlockedMessage = "Convert to order requires accept and guarded IV3 conversion.";
    } else {
      blockedMessage = "Pricing review completed; accept/convert uses separate guarded IV3 flows.";
      acceptBlockedMessage = "Use Intake V3 guarded accept — generic accept remains blocked.";
      convertBlockedMessage = "Convert to order requires guarded IV3 conversion.";
    }
  }

  return {
    isGuardedQuote,
    requiresPricingReview,
    pricingReviewCompleted,
    pricedDraft: Boolean(pricedDraft),
    guardedAcceptReady,
    guardedAcceptCompleted,
    guardedConvertReady,
    orderCreated,
    handoffPreviewReady,
    productionReadinessAuditRequired,
    acceptBlocked,
    convertBlocked,
    blockedMessage,
    acceptBlockedMessage,
    convertBlockedMessage,
  };
}

export function isGuardedDraftQuoteForDisplay(quote: Quote): boolean {
  return getQuoteIntakeCommercialGuard(quote).isGuardedQuote;
}

export function getQuoteIntakeCommercialGuidanceDescription(quote: Quote): string | null {
  const guard = getQuoteIntakeCommercialGuard(quote);
  if (!guard.isGuardedQuote) return null;
  if (guard.requiresPricingReview) {
    return "Pricing review is required before accept/convert can be considered.";
  }
  if (guard.handoffPreviewReady) {
    return "Production handoff is preview-ready. Production task dry-run is available as a preview. Real task generation remains blocked.";
  }
  if (guard.orderCreated) {
    return "Order created. Production readiness audit, material breakdown, and production task dry-run preview are available before real task generation.";
  }
  if (guard.guardedConvertReady) {
    return "Quote accepted. Convert to order requires guarded IV3 conversion.";
  }
  if (guard.guardedAcceptCompleted) {
    return "Intake V3 quote accepted. Convert to order requires guarded IV3 conversion.";
  }
  if (guard.guardedAcceptReady) {
    return "Pricing review completed. Use Intake V3 guarded accept — generic accept remains blocked.";
  }
  return "Pricing review completed. Accept/convert uses separate guarded IV3 flows.";
}