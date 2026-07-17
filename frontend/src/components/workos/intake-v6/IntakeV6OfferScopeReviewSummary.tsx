import { Package } from "lucide-react";
import { useMemo } from "react";
import { readPersistedOfferScope } from "@/lib/intakeV6/intakeV6OfferScopeState";
import { describeOfferScopeSummary } from "@/lib/intakeV6/intakeV6OfferScopePresets";
import { v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6OfferScopeReviewSummary({
  payload,
}: {
  payload: Record<string, unknown> | null | undefined;
}) {
  const summary = useMemo(() => {
    const persisted = readPersistedOfferScope(payload);
    return describeOfferScopeSummary(persisted.mode, persisted.soldModules);
  }, [payload]);

  return (
    <section
      className={`${v6.cardCompact} border-violet-500/20 bg-violet-500/5`}
      data-testid="intake-v6-review-offer-scope-summary"
    >
      <p className="flex items-center gap-2 text-[12px] font-semibold text-slate-100">
        <Package className="h-3.5 w-3.5 text-violet-300" aria-hidden />
        Scope ofertă
      </p>
      <p className="mt-1.5 text-[11px] text-slate-300" data-testid="intake-v6-review-offer-scope-mode">
        Mod: {summary.requestModeLabelRo}
      </p>
      {summary.activeLabelsRo.length > 0 ? (
        <p className="mt-1 text-[11px] text-slate-300" data-testid="intake-v6-review-offer-scope-active">
          Componente active: {summary.activeLabelsRo.join(", ")}
        </p>
      ) : null}
      {summary.excludedLabelsRo.length > 0 ? (
        <p className="mt-1 text-[11px] text-slate-400" data-testid="intake-v6-review-offer-scope-excluded">
          Nu sunt incluse: {summary.excludedLabelsRo.join(", ")}
        </p>
      ) : (
        <p className="mt-1 text-[11px] text-slate-400" data-testid="intake-v6-review-offer-scope-full">
          Toate componentele produsului sunt în scope.
        </p>
      )}
    </section>
  );
}
