import { Link } from "react-router-dom";
import type { Quote } from "@/lib/mockData";
import {
  formatQuoteStatusLabel,
  getQuoteCommercialGuidance,
  QUOTE_REVISION_MECHANISM_NOTICE,
} from "@/lib/quoteCommercialGuidance";
import { isQuoteRevisionEligible } from "@/lib/quoteRevision";
import { ArrowRight, Clock, History, Info, Percent, TrendingUp } from "lucide-react";
import { formatSendChannelLabel } from "@/lib/quoteSendLog";
import { DEFAULT_QUOTE_CURRENCY, formatQuoteMoney } from "@/lib/quoteCurrency";
import { StatusBadge } from "@/components/workos/design-system/StatusBadge";
import { buildIntakeV6Path } from "@/lib/volumetricIntakeRoute";

export interface QuoteCommercialActionPanelProps {
  quote: Quote;
  testId?: string;
  onOpenRevision?: () => void;
}

export default function QuoteCommercialActionPanel({
  quote,
  testId = "quote-commercial-action-panel",
  onOpenRevision,
}: QuoteCommercialActionPanelProps) {
  const guidance = getQuoteCommercialGuidance(quote.status, quote);
  const currency = quote.currency ?? DEFAULT_QUOTE_CURRENCY;

  return (
    <div
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4 space-y-3"
      data-testid={testId}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-wide text-slate-500">
            Stare comercială
          </p>
          <h3 className="text-[14px] font-semibold text-slate-100 mt-0.5">
            {guidance.title}
          </h3>
        </div>
        <span data-testid="quote-commercial-status-label">
          <StatusBadge
            domain="quote"
            status={quote.status}
            label={formatQuoteStatusLabel(quote.status)}
            className="text-[11px]"
          />
        </span>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
        <div>
          <span className="text-slate-500">Cod ofertă</span>
          <p className="font-mono text-blue-400">{quote.id}</p>
        </div>
        <div>
          <span className="text-slate-500">Versiune</span>
          <p className="text-slate-200" data-testid="quote-commercial-version">
            v{quote.version}
          </p>
        </div>
        <div>
          <span className="text-slate-500">Client</span>
          <p className="text-slate-200">{quote.client}</p>
        </div>
        {quote.intakeId ? (
          <div>
            <span className="text-slate-500">Cerere sursă</span>
            <p>
              <Link
                to={buildIntakeV6Path(quote.intakeId)}
                className="text-blue-400 hover:text-blue-300 font-mono"
                data-testid="quote-commercial-intake-link"
              >
                {quote.intakeId}
              </Link>
            </p>
          </div>
        ) : null}
      </div>

      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-wo-border-subtle text-[11px]">
        <div>
          <span className="text-slate-500">Total fără TVA</span>
          <p className="text-slate-200 font-medium">
            {formatQuoteMoney(quote.totalBeforeVAT, currency)}
          </p>
        </div>
        <div>
          <span className="text-slate-500">TVA</span>
          <p className="text-slate-200">{formatQuoteMoney(quote.vat, currency)}</p>
        </div>
        <div>
          <span className="text-slate-500">Total cu TVA</span>
          <p className="text-slate-100 font-semibold">
            {formatQuoteMoney(quote.grandTotal, currency)}
          </p>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-slate-500 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> Marjă
          </span>
          <p
            className="text-slate-200 font-medium"
            data-testid="quote-commercial-margin"
          >
            {quote.marginPct}%
          </p>
          <span className="text-slate-500 flex items-center gap-1">
            <Percent className="w-3 h-3" /> Discount
          </span>
          <p
            className="text-slate-200 font-medium"
            data-testid="quote-commercial-discount"
          >
            {quote.discountPct}%
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-blue-900/30 bg-blue-950/20 px-3 py-2">
        <p className="text-[11px] text-blue-200/90">{guidance.description}</p>
        <p
          className="text-[10px] text-blue-300/70 mt-1 flex items-center gap-1"
          data-testid="quote-commercial-next-action"
        >
          <ArrowRight className="w-3 h-3 shrink-0" />
          Următorul pas recomandat: {guidance.nextAction}
        </p>
      </div>

      {quote.revisionHistory && quote.revisionHistory.length > 0 && (
        <div
          className="rounded-lg border border-slate-700/40 bg-slate-900/40 px-3 py-2 space-y-2"
          data-testid="quote-revision-history-panel"
        >
          <p className="text-[10px] uppercase tracking-wide text-slate-500 flex items-center gap-1">
            <History className="w-3 h-3" /> Istoric revizii comerciale
          </p>
          <p className="text-[10px] text-slate-400">
            Versiune activă: v{quote.version}
          </p>
          {quote.revisionHistory
            .slice()
            .reverse()
            .slice(0, 3)
            .map((entry) => (
              <div
                key={`${entry.version}-${entry.archivedAt}`}
                className="text-[10px] text-slate-300 border-t border-slate-800/80 pt-2 first:border-t-0 first:pt-0"
                data-testid={`quote-revision-history-v${entry.version}`}
              >
                <p>
                  v{entry.version} ·{" "}
                  {entry.archivedAt
                    ? new Date(entry.archivedAt).toLocaleString("ro-RO")
                    : "—"}
                  {entry.discountPct != null ? ` · discount ${entry.discountPct}%` : ""}
                </p>
                {entry.grandTotal != null ? (
                  <p className="text-slate-500">
                    Total cu TVA: {formatQuoteMoney(entry.grandTotal ?? 0, currency)}
                  </p>
                ) : null}
              </div>
            ))}
        </div>
      )}

      {quote.commercialDeliveryLog && quote.commercialDeliveryLog.length > 0 && (
        <div
          className="rounded-lg border border-slate-700/40 bg-slate-900/40 px-3 py-2 space-y-2"
          data-testid="quote-send-history-panel"
        >
          <p className="text-[10px] uppercase tracking-wide text-slate-500 flex items-center gap-1">
            <Clock className="w-3 h-3" /> Istoric trimitere asistată
          </p>
          {quote.commercialDeliveryLog.slice(0, 3).map((entry, index) => (
            <div
              key={entry.id ?? `${entry.sent_at}-${index}`}
              className="text-[10px] text-slate-300 border-t border-slate-800/80 pt-2 first:border-t-0 first:pt-0"
              data-testid={index === 0 ? "quote-send-history-latest" : undefined}
            >
              <p>
                {new Date(entry.sent_at).toLocaleString("ro-RO")} ·{" "}
                {formatSendChannelLabel(entry.channel)} · v{entry.quote_version ?? quote.version}
              </p>
              {entry.recipient ? (
                <p className="text-slate-500">Destinatar: {entry.recipient}</p>
              ) : null}
              {entry.note ? <p className="text-slate-500">Notiță: {entry.note}</p> : null}
            </div>
          ))}
        </div>
      )}

      <div className="flex items-start gap-2 rounded-lg border border-slate-700/40 bg-slate-900/40 px-3 py-2">
        <Info className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
        <div className="space-y-2 text-[10px] text-slate-400 leading-relaxed">
          <p data-testid="quote-revision-mechanism-notice">{QUOTE_REVISION_MECHANISM_NOTICE}</p>
          {isQuoteRevisionEligible(quote.status) ? (
            onOpenRevision ? (
              <button
                type="button"
                data-testid="quote-revision-open-action"
                onClick={onOpenRevision}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border border-purple-700/50 text-purple-300 hover:bg-purple-950/30 text-[11px] font-semibold"
              >
                Creează revizie / ajustează discount
              </button>
            ) : null
          ) : (
            <p data-testid="quote-revision-unavailable-notice">
              Revizia nu este permisă pentru statusul curent al ofertei.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
