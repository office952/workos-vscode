import type { Quote, QuoteStatus } from "@/lib/mockData";
import { isTerminalClosedQuoteStatus } from "@/lib/commercialSpineNavigation";

export const QUOTE_INTERNAL_ACCEPTANCE_BUTTON_LABEL = "Marchează acceptată intern";

export const QUOTE_INTERNAL_ACCEPTANCE_NOTICE =
  "Această acțiune marchează acceptarea internă a operatorului. Nu trimite un link clientului și nu creează automat comanda.";

export const QUOTE_ACCEPTANCE_NEXT_STEP_NOTICE =
  "După acceptare, convertește oferta în comandă pentru a continua fluxul comercial.";

export const QUOTE_PRICED_CONVERT_GUIDANCE =
  "Poți converti o ofertă calculată sau acceptată. Recomandat: marchează acceptarea internă înainte de conversie.";

export const QUOTE_CONVERT_BUTTON_LABEL = "Creează comandă din oferta activă";

export const QUOTE_CONVERT_SNAPSHOT_NOTICE =
  "Comanda va fi creată din snapshot-ul ofertei active (versiunea curentă). Totalurile ofertei nu se modifică la conversie.";

export const QUOTE_DUPLICATE_ORDER_MESSAGE =
  "Există deja o comandă pentru această ofertă.";

export const ACCEPT_ELIGIBLE_STATUSES: QuoteStatus[] = [
  "sent",
  "viewed",
  "negotiating",
];

export const CONVERT_ELIGIBLE_STATUSES: QuoteStatus[] = ["priced", "accepted"];

export function showsInternalAcceptanceGuidance(status: QuoteStatus): boolean {
  return ACCEPT_ELIGIBLE_STATUSES.includes(status);
}

export function showsConversionSummary(status: QuoteStatus): boolean {
  return CONVERT_ELIGIBLE_STATUSES.includes(status);
}

export function showsConvertAction(status: QuoteStatus): boolean {
  return !isTerminalClosedQuoteStatus(status) && CONVERT_ELIGIBLE_STATUSES.includes(status);
}

export interface ParsedOrderConversionError {
  error?: string;
  existingOrderCode?: string;
  existingOrderId?: number;
  message?: string;
}

export function parseOrderConversionError(raw: unknown): ParsedOrderConversionError {
  if (!raw) return {};
  try {
    const parsed =
      typeof raw === "string"
        ? (JSON.parse(raw) as Record<string, unknown>)
        : (raw as Record<string, unknown>);
    const detail =
      parsed.detail && typeof parsed.detail === "object"
        ? (parsed.detail as Record<string, unknown>)
        : parsed;
    return {
      error: typeof detail.error === "string" ? detail.error : undefined,
      existingOrderCode:
        typeof detail.existing_order_code === "string"
          ? detail.existing_order_code
          : undefined,
      existingOrderId:
        typeof detail.existing_order_id === "number"
          ? detail.existing_order_id
          : undefined,
      message:
        typeof detail.message === "string"
          ? detail.message
          : typeof parsed.message === "string"
            ? parsed.message
            : undefined,
    };
  } catch {
    return { message: typeof raw === "string" ? raw : undefined };
  }
}

export function formatQuoteConversionSummary(quote: Quote): string {
  const intake = quote.intakeId ? ` · cerere ${quote.intakeId}` : "";
  return `${quote.id} · v${quote.version} · ${quote.client}${intake}`;
}
