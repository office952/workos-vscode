/** Step 7D — discrete truth label for Intake V6 offer preview (no layout redesign). */

import {
  COST_INTERN_ESTIMATIV_LABEL,
  OFERTA_CLIENT_LABEL,
  OFERTA_VS_COST_BOUNDARY_HELP,
  REGISTRY_INTERN_HELP,
} from "@/lib/intakeV6/intakeV6OfferCostChromeVocabulary";

export function IntakeV6AggregateCostTruthNotice({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <p
        className="mb-2 text-[10px] leading-relaxed text-slate-500"
        data-testid="intake-v6-aggregate-cost-truth-notice"
      >
        {OFERTA_CLIENT_LABEL} = preț pentru client. {COST_INTERN_ESTIMATIV_LABEL} = doar referință
        atelier — nu înlocuiește oferta.
      </p>
    );
  }

  return (
    <div
      className="mb-3 rounded border border-sky-900/40 bg-sky-950/30 px-2.5 py-2 text-[10px] leading-relaxed text-sky-200/90"
      data-testid="intake-v6-aggregate-cost-truth-notice"
    >
      <p className="font-semibold text-sky-100">{OFERTA_VS_COST_BOUNDARY_HELP}</p>
      <p className="mt-1">
        Estimare operațională Intake V6 / dry-run — nu creează comandă sau taskuri. {OFERTA_CLIENT_LABEL}{" "}
        validată vine din Product Compiler + reguli comerciale (intern: CPP).{" "}
        {COST_INTERN_ESTIMATIV_LABEL} rămâne canal separat (intern: EIC / breakdown).
      </p>
      <p className="mt-1 text-sky-300/80">{REGISTRY_INTERN_HELP}</p>
    </div>
  );
}
