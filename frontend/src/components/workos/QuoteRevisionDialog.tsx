import { useEffect, useMemo, useState } from "react";

import { Link } from "react-router-dom";

import { Loader2, Percent, X, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";

import type { Quote } from "@/lib/mockData";

import { getQuote } from "@/lib/api";

import type { QuotePriceResponse } from "@/api/quotes";

import { LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO } from "@/lib/legacyQuotePriceRetirement";

import { LegacyQuotePriceRetiredBanner } from "@/components/workos/LegacyQuotePriceRetiredBanner";

import {

  LEGACY_REVISION_RECOVERY_MESSAGE,

  MAX_QUOTE_DISCOUNT_PCT,

  QUOTE_REVISION_MECHANISM_NOTICE,

  QUOTE_REVISION_RESEND_NOTICE,

  QUOTE_REVISION_SUCCESS_MESSAGE,

  resolveQuoteRevisionSource,

  type QuoteRevisionResolveResult,

  type QuoteRevisionSource,

  validateRevisionDiscountPct,

} from "@/lib/quoteRevision";
import { buildIntakeV6Path } from "@/lib/volumetricIntakeRoute";



function formatCurrency(val: number) {

  return val.toLocaleString("ro-RO", {

    minimumFractionDigits: 2,

    maximumFractionDigits: 2,

  });

}



export interface QuoteRevisionDialogProps {

  quote: Quote;

  open: boolean;

  onClose: () => void;

  onRevised: (result: QuotePriceResponse) => void | Promise<void>;

}



export default function QuoteRevisionDialog({

  quote,

  open,

  onClose,

  onRevised,

}: QuoteRevisionDialogProps) {

  const [loadingSource, setLoadingSource] = useState(false);

  const [resolveResult, setResolveResult] = useState<QuoteRevisionResolveResult | null>(null);

  const [revisionSource, setRevisionSource] = useState<QuoteRevisionSource | null>(null);

  const [legacyPricing, setLegacyPricing] =

    useState<QuoteRevisionSource["pricing"]>(undefined);

  const [intakeDbId, setIntakeDbId] = useState<number | null>(null);

  const [discountPct, setDiscountPct] = useState(String(quote.discountPct ?? 0));

  const [submitting, setSubmitting] = useState(false);

  const [submitError, setSubmitError] = useState<string | null>(null);

  const [success, setSuccess] = useState<QuotePriceResponse | null>(null);



  const blocked =

    resolveResult?.kind === "blocked" ? resolveResult : null;



  useEffect(() => {

    if (!open) return;

    setSuccess(null);

    setSubmitError(null);

    setResolveResult(null);

    setRevisionSource(null);

    setLegacyPricing(undefined);

    setIntakeDbId(null);

    setDiscountPct(String(quote.discountPct ?? 0));



    if (!quote.dbId) {

      setResolveResult({

        kind: "blocked",

        errorCode: "missing_db_quote",

        message:

          "Revizia necesită ofertă din baza de date live cu snapshot de pricing salvat.",

        recoveryMessage: LEGACY_REVISION_RECOVERY_MESSAGE,

      });

      return;

    }



    let alive = true;

    setLoadingSource(true);

    getQuote(quote.dbId)

      .then((row) => {

        if (!alive) return;

        setIntakeDbId(row.intake_id ?? null);

        const resolved = resolveQuoteRevisionSource(row.line_items, quote, row.notes);

        setResolveResult(resolved);

        if (resolved.kind === "embedded") {

          setRevisionSource(resolved.source);

        } else if (resolved.kind === "legacy_candidate") {

          setLegacyPricing(resolved.pricing);

        }

      })

      .catch((err: unknown) => {

        if (!alive) return;

        setResolveResult({

          kind: "blocked",

          errorCode: "legacy_revision_source_missing",

          message:

            err instanceof Error ? err.message : "Nu s-a putut încărca oferta.",

          recoveryMessage: LEGACY_REVISION_RECOVERY_MESSAGE,

        });

      })

      .finally(() => {

        if (alive) setLoadingSource(false);

      });



    return () => {

      alive = false;

    };

  }, [open, quote.dbId, quote.discountPct, quote]);



  const discountValidation = useMemo(() => {

    return validateRevisionDiscountPct(Number(discountPct));

  }, [discountPct]);



  const canSubmit = false;



  async function handleSubmit() {

    setSubmitError(LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO);

  }



  if (!open) return null;



  return (

    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">

      <div

        className="bg-wo-surface-raised border border-wo-border-subtle rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"

        data-testid="quote-revision-dialog"

      >

        <div className="flex items-center justify-between p-4 border-b border-wo-border-subtle">

          <div className="flex items-center gap-2">

            <Percent className="w-4 h-4 text-purple-400" />

            <h2 className="text-[14px] font-bold text-slate-100">

              Revizie comercială — ajustează discount

            </h2>

          </div>

          <button

            type="button"

            onClick={onClose}

            className="p-1 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-slate-200"

          >

            <X className="w-4 h-4" />

          </button>

        </div>



        <div className="p-4 space-y-4">

          <LegacyQuotePriceRetiredBanner testId="quote-revision-legacy-retired" />

          <div className="grid grid-cols-2 gap-3 text-[11px]">

            <div>

              <span className="text-slate-500">Ofertă</span>

              <p className="font-mono text-blue-400">{quote.id}</p>

            </div>

            <div>

              <span className="text-slate-500">Versiune curentă</span>

              <p data-testid="quote-revision-current-version">v{quote.version}</p>

            </div>

            <div>

              <span className="text-slate-500">Total cu TVA</span>

              <p>{formatCurrency(quote.grandTotal)} RON</p>

            </div>

            <div>

              <span className="text-slate-500">Marjă (rezultat)</span>

              <p data-testid="quote-revision-current-margin">{quote.marginPct}%</p>

            </div>

            <div>

              <span className="text-slate-500">Discount curent</span>

              <p data-testid="quote-revision-current-discount">{quote.discountPct}%</p>

            </div>

          </div>



          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 px-3 py-2 text-[10px] text-slate-400 space-y-1">

            <p data-testid="quote-revision-mechanism-notice">{QUOTE_REVISION_MECHANISM_NOTICE}</p>

            <p data-testid="quote-revision-resend-notice">{QUOTE_REVISION_RESEND_NOTICE}</p>

            {resolveResult?.kind === "legacy_candidate" && (

              <p data-testid="quote-revision-legacy-notice">

                Ofertă legacy — sursa de repricing va fi reconstruită din snapshot la aplicare,

                dacă datele sunt complete.

              </p>

            )}

          </div>



          {loadingSource && (

            <p className="text-[11px] text-slate-500 flex items-center gap-2">

              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Se încarcă snapshot-ul…

            </p>

          )}



          {blocked && (

            <div

              className="flex flex-col gap-2 rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2"

              data-testid="quote-revision-source-error"

            >

              <div className="flex items-start gap-2">

                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />

                <div className="space-y-1">

                  <p className="text-[11px] text-red-300" data-testid="quote-revision-blocked-message">

                    {blocked.message}

                  </p>

                  <p className="text-[11px] text-red-300/90" data-testid="quote-revision-recovery-message">

                    {blocked.recoveryMessage}

                  </p>

                </div>

              </div>

              {quote.intakeId ? (

                <Link

                  to={buildIntakeV6Path(quote.intakeId)}

                  className="inline-flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300"

                  data-testid="quote-revision-intake-recovery-link"

                >

                  <ArrowRight className="w-3 h-3" />

                  Deschide cererea sursă pentru ofertă nouă

                </Link>

              ) : null}

            </div>

          )}



          {!blocked && (revisionSource || resolveResult?.kind === "legacy_candidate") && (

            <div>

              <label

                htmlFor="quote-revision-discount-input"

                className="text-[11px] text-slate-400 block mb-1"

              >

                Discount nou (%)

              </label>

              <input

                id="quote-revision-discount-input"

                data-testid="quote-revision-discount-input"

                type="number"

                min={0}

                max={MAX_QUOTE_DISCOUNT_PCT}

                step={0.5}

                value={discountPct}

                onChange={(e) => setDiscountPct(e.target.value)}

                className="w-full px-3 py-2 rounded-lg border border-wo-border-strong bg-[#0f1524] text-slate-100 text-[13px]"

              />

              {discountValidation && (

                <p

                  className="text-[10px] text-red-400 mt-1"

                  data-testid="quote-revision-discount-error"

                >

                  {discountValidation}

                </p>

              )}

            </div>

          )}



          {submitError && (

            <div

              className="flex items-start gap-2 rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2"

              data-testid="quote-revision-submit-error"

            >

              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />

              <p className="text-[11px] text-red-300">{submitError}</p>

            </div>

          )}



          {success && (

            <div

              className="flex items-start gap-2 rounded-lg border border-emerald-900/40 bg-emerald-950/20 px-3 py-2"

              data-testid="quote-revision-success"

            >

              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />

              <p className="text-[11px] text-emerald-300" data-testid="quote-revision-success-message">

                {QUOTE_REVISION_SUCCESS_MESSAGE}

                {success.quote_version != null ? ` (v${success.quote_version})` : ""}

              </p>

            </div>

          )}

        </div>



        <div className="flex items-center justify-end gap-2 p-4 border-t border-wo-border-subtle">

          <button

            type="button"

            onClick={onClose}

            className="px-3 py-1.5 text-[12px] rounded border border-wo-border-strong text-slate-400 hover:text-slate-200"

          >

            Închide

          </button>

          <button

            type="button"

            data-testid="quote-revision-submit"

            disabled={!canSubmit}

            onClick={() => void handleSubmit()}

            className="px-4 py-1.5 text-[12px] font-semibold rounded bg-purple-600 text-white hover:bg-purple-500 disabled:opacity-40"

          >

            {submitting ? (

              <span className="inline-flex items-center gap-2">

                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Se recalculează…

              </span>

            ) : (

              "Aplică revizia"

            )}

          </button>

        </div>

      </div>

    </div>

  );

}


