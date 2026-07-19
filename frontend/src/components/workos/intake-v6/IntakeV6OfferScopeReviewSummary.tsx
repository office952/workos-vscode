import { ChevronDown, Package } from "lucide-react";
import { useMemo, useState } from "react";
import { readPersistedOfferScope } from "@/lib/intakeV6/intakeV6OfferScopeState";
import { describeOfferScopeSummary } from "@/lib/intakeV6/intakeV6OfferScopePresets";

export default function IntakeV6OfferScopeReviewSummary({
  payload,
}: {
  payload: Record<string, unknown> | null | undefined;
}) {
  const summary = useMemo(() => {
    const persisted = readPersistedOfferScope(payload);
    return describeOfferScopeSummary(persisted.mode, persisted.soldModules);
  }, [payload]);
  const [open, setOpen] = useState(false);
  const hasExcluded = summary.excludedLabelsRo.length > 0;

  return (
    <section
      className="rounded-md border border-[#2A3548]/55 bg-[#111827]/40 px-3 py-2"
      data-testid="intake-v6-review-offer-scope-summary"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            <Package className="h-3 w-3 text-slate-500" aria-hidden />
            Scope ofertă
          </p>
          <p
            className="mt-1 text-[12px] text-slate-300"
            data-testid="intake-v6-review-offer-scope-mode"
          >
            {summary.requestModeLabelRo}
            {summary.activeLabelsRo.length > 0 ? (
              <span className="text-slate-500">
                {" "}
                ·{" "}
                <span data-testid="intake-v6-review-offer-scope-active">
                  {summary.activeLabelsRo.join(", ")}
                </span>
              </span>
            ) : null}
          </p>
          {!hasExcluded ? (
            <p
              className="mt-0.5 text-[11px] text-slate-600"
              data-testid="intake-v6-review-offer-scope-full"
            >
              Toate componentele produsului sunt în scope.
            </p>
          ) : null}
        </div>
        {hasExcluded ? (
          <button
            type="button"
            className="inline-flex shrink-0 items-center gap-1 rounded border border-[#2A3548]/70 px-2 py-1 text-[10px] font-semibold text-slate-400 hover:text-slate-200"
            onClick={() => setOpen((value) => !value)}
            aria-expanded={open}
            data-testid="intake-v6-review-offer-scope-disclosure"
          >
            Detalii
            <ChevronDown className={`h-3 w-3 transition ${open ? "rotate-180" : ""}`} aria-hidden />
          </button>
        ) : null}
      </div>
      {open && hasExcluded ? (
        <p
          className="mt-2 border-t border-[#2A3548]/50 pt-2 text-[11px] text-slate-500"
          data-testid="intake-v6-review-offer-scope-excluded"
        >
          Nu sunt incluse: {summary.excludedLabelsRo.join(", ")}
        </p>
      ) : null}
    </section>
  );
}
