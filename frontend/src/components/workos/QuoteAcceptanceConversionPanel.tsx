import { Link } from "react-router-dom";
import type { Quote } from "@/lib/mockData";
import {
  formatQuoteConversionSummary,
  QUOTE_ACCEPTANCE_NEXT_STEP_NOTICE,
  QUOTE_CONVERT_SNAPSHOT_NOTICE,
  QUOTE_DUPLICATE_ORDER_MESSAGE,
  QUOTE_INTERNAL_ACCEPTANCE_NOTICE,
  QUOTE_PRICED_CONVERT_GUIDANCE,
  showsConversionSummary,
  showsInternalAcceptanceGuidance,
} from "@/lib/quoteAcceptanceConversion";
import { DEFAULT_QUOTE_CURRENCY, formatQuoteMoney } from "@/lib/quoteCurrency";
import { estimateOrderRonFromEurQuote, formatOrderMoney, formatExchangeRate } from "@/lib/orderCurrency";
import { buildIntakeV6Path } from "@/lib/volumetricIntakeRoute";

export interface QuoteAcceptanceConversionPanelProps {
  quote: Quote;
  duplicateOrderCode?: string | null;
  eurToRonRate?: number | null;
}

export default function QuoteAcceptanceConversionPanel({
  quote,
  duplicateOrderCode,
  eurToRonRate,
}: QuoteAcceptanceConversionPanelProps) {
  const quoteCurrency = quote.currency ?? DEFAULT_QUOTE_CURRENCY;
  const roundedEurTotal =
    quoteCurrency === "EUR" ? Math.round(quote.grandTotal) : quote.grandTotal;
  const estimatedRonTotal =
    quoteCurrency === "EUR" && eurToRonRate && eurToRonRate > 0
      ? estimateOrderRonFromEurQuote(quote.grandTotal, eurToRonRate)
      : null;
  return (
    <div className="space-y-3">
      {showsInternalAcceptanceGuidance(quote.status) && (
        <div
          className="rounded-lg border border-emerald-900/30 bg-emerald-950/20 px-3 py-2 space-y-1"
          data-testid="quote-acceptance-clarity-notice"
        >
          <p className="text-[11px] text-emerald-200/90">{QUOTE_INTERNAL_ACCEPTANCE_NOTICE}</p>
          <p className="text-[10px] text-emerald-300/80">{QUOTE_ACCEPTANCE_NEXT_STEP_NOTICE}</p>
        </div>
      )}

      {showsConversionSummary(quote.status) && (
        <div
          className="rounded-lg border border-purple-900/30 bg-purple-950/20 px-3 py-2 space-y-2"
          data-testid="quote-conversion-summary-panel"
        >
          <p className="text-[10px] uppercase tracking-wide text-purple-300/80">
            Conversie în comandă
          </p>
          <p className="text-[11px] text-slate-200 font-medium" data-testid="quote-conversion-summary-line">
            {formatQuoteConversionSummary(quote)}
          </p>
          <p className="text-[11px] text-slate-300" data-testid="quote-conversion-total-eur">
            Total ofertă: {formatQuoteMoney(roundedEurTotal, quoteCurrency)} (rotunjit comercial)
          </p>
          {estimatedRonTotal != null && eurToRonRate ? (
            <div className="text-[11px] text-slate-300 space-y-1" data-testid="quote-conversion-estimated-ron">
              <p>Curs EUR/RON (Setări): {formatExchangeRate(eurToRonRate)}</p>
              <p>Total comandă estimat: {formatOrderMoney(estimatedRonTotal, "RON")}</p>
            </div>
          ) : (
            <p className="text-[11px] text-slate-300">
              Total activ: {formatQuoteMoney(quote.grandTotal, quoteCurrency)} (cu TVA)
            </p>
          )}
          {quote.intakeId ? (
            <p className="text-[10px] text-slate-400">
              Cerere sursă:{" "}
              <Link
                to={buildIntakeV6Path(quote.intakeId)}
                className="text-blue-400 hover:text-blue-300 font-mono"
              >
                {quote.intakeId}
              </Link>
            </p>
          ) : null}
          {quote.revisionHistory && quote.revisionHistory.length > 0 ? (
            <p className="text-[10px] text-slate-400" data-testid="quote-conversion-active-version">
              Se folosește versiunea activă v{quote.version}. Istoric:{" "}
              {quote.revisionHistory.length} revizii arhivate.
            </p>
          ) : (
            <p className="text-[10px] text-slate-400" data-testid="quote-conversion-active-version">
              Versiune activă: v{quote.version}
            </p>
          )}
          <p className="text-[10px] text-purple-200/80">{QUOTE_CONVERT_SNAPSHOT_NOTICE}</p>
          {quote.status === "priced" ? (
            <p className="text-[10px] text-amber-300/90" data-testid="quote-priced-convert-guidance">
              {QUOTE_PRICED_CONVERT_GUIDANCE}
            </p>
          ) : null}
        </div>
      )}

      {duplicateOrderCode ? (
        <div
          className="rounded-lg border border-amber-900/40 bg-amber-950/20 px-3 py-2"
          data-testid="quote-duplicate-order-notice"
        >
          <p className="text-[11px] text-amber-200">{QUOTE_DUPLICATE_ORDER_MESSAGE}</p>
          <Link
            to={`/orders/${encodeURIComponent(duplicateOrderCode)}`}
            className="text-[11px] text-blue-400 hover:text-blue-300 font-mono"
            data-testid="quote-duplicate-order-link"
          >
            Deschide comanda {duplicateOrderCode}
          </Link>
        </div>
      ) : null}
    </div>
  );
}
