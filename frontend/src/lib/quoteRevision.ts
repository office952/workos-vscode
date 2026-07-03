import type { Quote, QuoteStatus } from "@/lib/mockData";

import { isTerminalClosedQuoteStatus } from "@/lib/commercialSpineNavigation";

import type { QuotePriceRequest } from "@/api/quotes";
import { DEFAULT_VAT_PCT } from "@/lib/companyCommercialSettings";



/** Conservative UI limit — mirrors backend QUOTE_REVISION_MAX_DISCOUNT_PCT. */

export const MAX_QUOTE_DISCOUNT_PCT = 50;



export const QUOTE_REVISION_ELIGIBLE_STATUSES: QuoteStatus[] = [

  "draft",

  "priced",

  "sent",

  "viewed",

  "negotiating",

];



export const QUOTE_REVISION_RESEND_NOTICE =

  "După revizie, oferta revine la status Calculată și trebuie retrimisă clientului (trimitere asistată).";



export const QUOTE_REVISION_MECHANISM_NOTICE =

  "Revizia recalculează oferta prin mecanismul de pricing existent. Totalurile și marja nu se editează manual.";



export const LEGACY_REVISION_BLOCKED_MESSAGE =

  "Această ofertă a fost creată înainte de suportul pentru revizii și nu conține datele necesare pentru recalcul sigur.";



export const LEGACY_REVISION_RECOVERY_MESSAGE =

  "Creează o ofertă nouă din cerere pentru a modifica discountul.";



export const QUOTE_REVISION_SUCCESS_MESSAGE =

  "Revizie creată. Oferta a fost recalculată și trebuie retrimisă clientului.";



export interface QuoteRevisionSource {

  product_template?: Record<string, unknown>;

  user_config?: Record<string, unknown>;

  quote_input?: Record<string, unknown>;

  pricing?: {

    margin_pct?: number;

    discount_pct?: number;

    vat_pct?: number;

  };

  legacy_reconstructed?: boolean;

}



export type QuoteRevisionResolveResult =

  | { kind: "embedded"; source: QuoteRevisionSource }

  | { kind: "legacy_candidate"; pricing: QuoteRevisionSource["pricing"] }

  | {

      kind: "blocked";

      errorCode: "legacy_revision_source_missing" | "missing_db_quote";

      message: string;

      recoveryMessage: string;

    };



function isCanonicalSnapshot(obj: unknown): boolean {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return false;
  const snap = obj as Record<string, unknown>;
  return (
    "product_definition" in snap &&
    ("cost_result" in snap || "pricing" in snap || "price" in snap)
  );
}



export function extractCanonicalSnapshotFromLineItems(
  lineItemsRaw?: string | null
): Record<string, unknown> | null {
  if (!lineItemsRaw?.trim()) return null;
  try {
    const parsed: unknown = JSON.parse(lineItemsRaw);
    if (Array.isArray(parsed)) return null;
    if (!parsed || typeof parsed !== "object") return null;

    const root = parsed as Record<string, unknown>;
    if (root.revision_source) return null;
    if (isCanonicalSnapshot(root)) return root;

    const nestedLineItems = root["line_items"];
    return isCanonicalSnapshot(nestedLineItems)
      ? (nestedLineItems as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}



export function isQuoteRevisionEligible(status: QuoteStatus): boolean {

  if (isTerminalClosedQuoteStatus(status)) return false;

  if (status === "accepted") return false;

  return QUOTE_REVISION_ELIGIBLE_STATUSES.includes(status as QuoteStatus);

}



export function validateRevisionDiscountPct(value: number): string | null {

  if (!Number.isFinite(value)) return "Introdu un procent valid.";

  if (value < 0) return "Discountul nu poate fi negativ.";

  if (value > MAX_QUOTE_DISCOUNT_PCT) {

    return `Discountul maxim permis este ${MAX_QUOTE_DISCOUNT_PCT}%.`;

  }

  return null;

}



export function extractQuoteRevisionSource(

  lineItemsRaw?: string | null

): QuoteRevisionSource | null {

  if (!lineItemsRaw?.trim()) return null;

  try {

    const parsed = JSON.parse(lineItemsRaw) as Record<string, unknown>;

    if (parsed.revision_source && typeof parsed.revision_source === "object") {

      return parsed.revision_source as QuoteRevisionSource;

    }

    return null;

  } catch {

    return null;

  }

}


function extractLinkedQuoteRevisionHintFromNotes(
  notesRaw?: string | null
): Record<string, unknown> | null {
  if (!notesRaw?.trim()) return null;

  try {
    const parsed = JSON.parse(notesRaw) as Record<string, unknown>;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return null;
    }

    const v6Linkage = parsed["intake_v6_linkage_v1"];
    if (v6Linkage && typeof v6Linkage === "object" && !Array.isArray(v6Linkage)) {
      return v6Linkage as Record<string, unknown>;
    }

    const v4Linkage = parsed["intake_v4_linkage_v1"];
    if (v4Linkage && typeof v4Linkage === "object" && !Array.isArray(v4Linkage)) {
      return v4Linkage as Record<string, unknown>;
    }

    return null;
  } catch {
    return null;
  }
}



export function resolveQuoteRevisionSource(

  lineItemsRaw: string | null | undefined,

  quote: Quote,

  notesRaw?: string | null

): QuoteRevisionResolveResult {

  const embedded = extractQuoteRevisionSource(lineItemsRaw);

  if (embedded?.product_template && embedded.user_config) {

    return { kind: "embedded", source: embedded };

  }



  const snapshot = extractCanonicalSnapshotFromLineItems(lineItemsRaw);

  if (snapshot?.template_id != null) {

    const pricingSnap =

      snapshot.pricing && typeof snapshot.pricing === "object"

        ? (snapshot.pricing as QuoteRevisionSource["pricing"])

        : undefined;

    return {

      kind: "legacy_candidate",

      pricing: {

        margin_pct: pricingSnap?.margin_pct ?? quote.marginPct,

        discount_pct: pricingSnap?.discount_pct ?? quote.discountPct,

        vat_pct: pricingSnap?.vat_pct ?? quote.vat ?? DEFAULT_VAT_PCT,

      },

    };

  }


  const linkedRevisionHint = extractLinkedQuoteRevisionHintFromNotes(notesRaw);
  if (linkedRevisionHint) {
    return {
      kind: "legacy_candidate",
      pricing: {
        margin_pct: quote.marginPct,
        discount_pct: quote.discountPct,
        vat_pct: quote.vat ?? DEFAULT_VAT_PCT,
      },
    };
  }



  return {

    kind: "blocked",

    errorCode: "legacy_revision_source_missing",

    message: LEGACY_REVISION_BLOCKED_MESSAGE,

    recoveryMessage: LEGACY_REVISION_RECOVERY_MESSAGE,

  };

}



export function buildQuoteRevisionRequest(

  quote: Quote,

  source: QuoteRevisionSource,

  newDiscountPct: number,

  options?: { intakeDbId?: number | null }

): QuotePriceRequest | null {

  if (!source.product_template || !source.user_config) return null;



  const priorPricing = source.pricing ?? {};

  const margin_pct = Number(priorPricing.margin_pct ?? quote.marginPct ?? 0);

  const vat_pct = Number(priorPricing.vat_pct ?? quote.vat ?? DEFAULT_VAT_PCT);



  return {

    product_template: source.product_template as unknown as QuotePriceRequest["product_template"],

    user_config: source.user_config as unknown as QuotePriceRequest["user_config"],

    quote_input: source.quote_input as QuotePriceRequest["quote_input"],

    client_name: quote.client,

    intake_id: options?.intakeDbId ?? undefined,

    pricing: {

      margin_pct,

      vat_pct,

      discount_pct: newDiscountPct,

    },

  };

}



export function buildLegacyRevisionPriceRequest(

  quote: Quote,

  pricing: QuoteRevisionSource["pricing"] | undefined,

  newDiscountPct: number,

  options?: { intakeDbId?: number | null }

): QuotePriceRequest {

  return {

    client_name: quote.client,

    intake_id: options?.intakeDbId ?? undefined,

    pricing: {

      margin_pct: Number(pricing?.margin_pct ?? quote.marginPct ?? 0),

      vat_pct: Number(pricing?.vat_pct ?? quote.vat ?? DEFAULT_VAT_PCT),

      discount_pct: newDiscountPct,

    },

  } as QuotePriceRequest;

}



export function formatLegacyRevisionApiError(message: string): string {

  if (message.includes("legacy_revision_source_missing")) {

    return `${LEGACY_REVISION_BLOCKED_MESSAGE} ${LEGACY_REVISION_RECOVERY_MESSAGE}`;

  }

  return message;

}

export interface QuoteRevisionHistoryEntry {
  version: number;
  archivedAt: string;
  discountPct?: number;
  grandTotal?: number;
  totalBeforeVat?: number;
}

function readPricingFromArchivedLineItems(raw: unknown): {
  discountPct?: number;
  grandTotal?: number;
  totalBeforeVat?: number;
} {
  if (typeof raw !== "string" || !raw.trim()) return {};
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const inner =
      parsed.line_items && typeof parsed.line_items === "object"
        ? (parsed.line_items as Record<string, unknown>)
        : parsed;
    const pricing =
      inner.pricing && typeof inner.pricing === "object"
        ? (inner.pricing as Record<string, unknown>)
        : undefined;
    const price =
      inner.price && typeof inner.price === "object"
        ? (inner.price as Record<string, unknown>)
        : undefined;
    return {
      discountPct:
        typeof pricing?.discount_pct === "number" ? pricing.discount_pct : undefined,
      grandTotal: typeof price?.gross === "number" ? price.gross : undefined,
      totalBeforeVat: typeof price?.net === "number" ? price.net : undefined,
    };
  } catch {
    return {};
  }
}

export function extractQuoteRevisionHistory(
  lineItemsRaw?: string | null
): QuoteRevisionHistoryEntry[] {
  if (!lineItemsRaw?.trim()) return [];
  try {
    const parsed = JSON.parse(lineItemsRaw) as Record<string, unknown>;
    const history = parsed.revision_history;
    if (!Array.isArray(history)) return [];
    return history
      .filter((entry): entry is Record<string, unknown> => !!entry && typeof entry === "object")
      .map((entry) => {
        const metrics = readPricingFromArchivedLineItems(entry.line_items);
        return {
          version: Number(entry.version ?? 0),
          archivedAt: String(entry.archived_at ?? ""),
          discountPct: metrics.discountPct,
          grandTotal: metrics.grandTotal,
          totalBeforeVat: metrics.totalBeforeVat,
        };
      })
      .filter((entry) => entry.version > 0 && entry.archivedAt);
  } catch {
    return [];
  }
}


