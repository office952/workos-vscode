import type { IntakeV6EdgeCantOracalImpact } from "@/lib/intakeV6/intakeV6EdgeCantDisplay";
import { formatEdgeCantM2 } from "@/lib/intakeV6/intakeV6EdgeCantDisplay";
import { v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6EdgeCantQuoteImpactPanel({
  oracal,
  className = "",
}: {
  oracal: IntakeV6EdgeCantOracalImpact;
  className?: string;
}) {
  if (!oracal.present) return null;

  const priceLabel =
    oracal.unitPrice != null && !oracal.pricingMissing
      ? `${oracal.unitPrice} ${oracal.currency}/m²`
      : "lipsă — nu afișat";

  const costLabel =
    oracal.estimatedCost != null && !oracal.pricingMissing
      ? `${oracal.estimatedCost.toFixed(2)} ${oracal.currency} (înainte de TVA, din breakdown)`
      : "calcul indisponibil / preț lipsă";

  const sourceLabel = oracal.priceSource?.includes("oracal_651")
    ? "shared vinyl catalog / intake_v6_owner_oracal_651"
    : oracal.priceSource ?? "shared vinyl catalog";

  return (
    <div
      className={`rounded border border-[#334155]/80 bg-[#0A0F1A]/70 px-3 py-3 ${className}`}
      data-testid="intake-v6-oracal-cant-impact"
    >
      <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-300">
        Impact Oracal 651 pe cant / volum
      </h4>
      <dl className="space-y-1 text-[11px]">
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Material suplimentar</dt>
          <dd className={v6.mono}>Oracal 651 / cant volum</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Suprafață estimată</dt>
          <dd className={v6.mono} data-testid="intake-v6-oracal-cant-area">
            {formatEdgeCantM2(oracal.areaM2)}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Preț material</dt>
          <dd className={v6.mono} data-testid="intake-v6-oracal-cant-unit-price">
            {priceLabel}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Cost estimat material</dt>
          <dd className={v6.mono} data-testid="intake-v6-oracal-cant-cost">
            {costLabel}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Baza calcul</dt>
          <dd className="text-right text-slate-400">
            {oracal.basisNote ?? "cant pentru aplicare + adâncime + adaos 10 mm"}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt className="text-slate-500">Sursă preț</dt>
          <dd className="text-right text-slate-400" data-testid="intake-v6-oracal-cant-price-source">
            {sourceLabel}
          </dd>
        </div>
      </dl>
    </div>
  );
}



