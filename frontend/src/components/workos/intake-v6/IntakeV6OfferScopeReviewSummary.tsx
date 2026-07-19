import { ChevronDown, Package } from "lucide-react";
import { useMemo, useState } from "react";
import { readPersistedOfferScope } from "@/lib/intakeV6/intakeV6OfferScopeState";
import { describeOfferScopeSummary } from "@/lib/intakeV6/intakeV6OfferScopePresets";

/** Compact scope chip — must not compete with the active form. */
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
      className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-[#2A3548]/55 bg-[#111827]/30 px-2.5 py-1"
      data-testid="intake-v6-review-offer-scope-summary"
      data-scope-weight="chip"
    >
      <Package className="h-3 w-3 shrink-0 text-slate-500" aria-hidden />
      <p
        className="min-w-0 truncate text-[11px] text-slate-400"
        data-testid="intake-v6-review-offer-scope-mode"
      >
        <span className="font-semibold text-slate-500">Scope</span>
        {" · "}
        {summary.requestModeLabelRo}
        {summary.activeLabelsRo.length > 0 ? (
          <span data-testid="intake-v6-review-offer-scope-active">
            {" · "}
            {summary.activeLabelsRo.join(", ")}
          </span>
        ) : null}
      </p>
      {!hasExcluded ? (
        <span className="sr-only" data-testid="intake-v6-review-offer-scope-full">
          Toate componentele produsului sunt în scope.
        </span>
      ) : (
        <button
          type="button"
          className="inline-flex shrink-0 items-center gap-0.5 text-[10px] font-semibold text-slate-500 hover:text-slate-300"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          data-testid="intake-v6-review-offer-scope-disclosure"
        >
          Detalii
          <ChevronDown className={`h-3 w-3 transition ${open ? "rotate-180" : ""}`} aria-hidden />
        </button>
      )}
      {open && hasExcluded ? (
        <p
          className="basis-full text-[10px] text-slate-500"
          data-testid="intake-v6-review-offer-scope-excluded"
        >
          Nu sunt incluse: {summary.excludedLabelsRo.join(", ")}
        </p>
      ) : null}
    </section>
  );
}
