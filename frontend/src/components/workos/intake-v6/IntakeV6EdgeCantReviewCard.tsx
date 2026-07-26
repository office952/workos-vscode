import type {

  IntakeV6EdgeCantLayerBreakdown,

  IntakeV6EdgeCantViewModel,

} from "@/lib/intakeV6/intakeV6EdgeCantDisplay";

import {

  formatEdgeCantCostFormula,

  formatEdgeCantDepthMm,

  formatEdgeCantLayerPerimeter,

  formatEdgeCantM,

  formatEdgeCantMl,

  formatEdgeCantOperatorPerimeter,
  normalizeIntakeV6EdgeCantGroupsToTotal,
} from "@/lib/intakeV6/intakeV6EdgeCantDisplay";

import type { IntakeV6OperatorCantPerimeterDisplay } from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";

import { INTAKE_V6_CANT_VOLUM_LABEL } from "@/lib/intakeV6/intakeV6ReturnFinishOptions";

import { v6 } from "./atoms/intakeV6Presentation";

import IntakeV6EdgeCantQuoteImpactPanel from "./IntakeV6EdgeCantQuoteImpactPanel";

import IntakeV6TechnicalDetailsAccordion from "./atoms/IntakeV6TechnicalDetailsAccordion";



function MainRow({ label, value, testId }: { label: string; value: string; testId?: string }) {

  return (

    <div className="flex justify-between gap-4 border-b border-wo-border-strong/60 py-2.5 text-[12px] last:border-b-0">

      <dt className="text-slate-400">{label}</dt>

      <dd className={`${v6.mono} text-right text-wo-text-primary`} data-testid={testId}>

        {value}

      </dd>

    </div>

  );

}



function DebugRow({ label, value, testId }: { label: string; value: string; testId?: string }) {

  return (

    <div className="flex justify-between gap-4 border-b border-wo-border-strong/40 py-2 text-[11px] last:border-b-0">

      <dt className="text-slate-500">{label}</dt>

      <dd className={`${v6.mono} text-right text-slate-400`} data-testid={testId}>

        {value}

      </dd>

    </div>

  );

}



type EdgeCantDisplayGroups = ReturnType<typeof normalizeIntakeV6EdgeCantGroupsToTotal>;

function edgeCantGroupScopeLabel(scope: "letters" | "artwork" | "mixed"): string {
  if (scope === "letters") return "Litere";
  if (scope === "artwork") return "Emblemă";
  return "Mixt";
}

function formatCantGroupedSummary(displayGroups: EdgeCantDisplayGroups): string {
  const groups = displayGroups.groups;
  if (groups.length === 0) return "n/a";
  return groups
    .map(
      (group) =>
        `${edgeCantGroupScopeLabel(group.scope)} ${formatEdgeCantDepthMm(group.depthMm)} · ${
          group.finishLabel
        }: ${formatEdgeCantM(group.perimeterM)}`,
    )
    .join(" | ");
}

function formatDepthDistribution(displayGroups: EdgeCantDisplayGroups): string {
  const depthTotals = new Map<string, { depth: number | null; total: number }>();
  for (const group of displayGroups.groups) {
    const key = group.depthMm != null ? String(Math.round(group.depthMm)) : "unknown";
    const prior = depthTotals.get(key);
    if (prior) {
      prior.total += group.perimeterM;
    } else {
      depthTotals.set(key, { depth: group.depthMm, total: group.perimeterM });
    }
  }
  const values = [...depthTotals.values()];
  if (values.length === 0) return "n/a";
  return values
    .sort((a, b) => (a.depth ?? 0) - (b.depth ?? 0))
    .map((item) => `${formatEdgeCantDepthMm(item.depth)}: ${formatEdgeCantM(item.total)}`)
    .join(" | ");
}

export default function IntakeV6EdgeCantReviewCard({
  model,

  loading,

  operatorCantPerimeterM,

  cantPerimeterDisplay,

  layerBreakdown,

}: {

  model: IntakeV6EdgeCantViewModel | null;

  loading?: boolean;

  operatorCantPerimeterM?: number | null;

  cantPerimeterDisplay?: IntakeV6OperatorCantPerimeterDisplay | null;

  layerBreakdown?: IntakeV6EdgeCantLayerBreakdown | null;

}) {

  if (loading) {

    return (

      <div className={`${v6.card} mb-4`} data-testid="intake-v6-edge-cant-review-card">

        <p className="text-[12px] text-slate-400">Calculez cant / volum…</p>

      </div>

    );

  }



  const hasOperatorPerimeter = operatorCantPerimeterM != null && operatorCantPerimeterM > 0;

  const hasLayerBreakdown = (layerBreakdown?.layers.length ?? 0) > 0;



  if (!model?.hasEdgeCantData && !hasOperatorPerimeter && !hasLayerBreakdown) {

    return (

      <div className={`${v6.card} mb-4`} data-testid="intake-v6-edge-cant-review-card">

        <h2 className="mb-2 text-[13px] font-bold uppercase tracking-wide">{INTAKE_V6_CANT_VOLUM_LABEL}</h2>

        <p className="text-[12px] text-slate-400">Calcul indisponibil — salvați finisajele și analiza SVG.</p>

      </div>

    );

  }



  const operatorPerimeterM = hasOperatorPerimeter ? operatorCantPerimeterM : null;

  const perimeterText = formatEdgeCantOperatorPerimeter(operatorPerimeterM);

  const wasteLabel = model?.wastePercent != null ? `+${model.wastePercent.toFixed(0)}%` : "n/a";

  const displayGroups = normalizeIntakeV6EdgeCantGroupsToTotal({
    groups: layerBreakdown?.groups ?? [],
    targetTotalM: operatorPerimeterM,
  });

  const groupedSummary = formatCantGroupedSummary(displayGroups);

  const depthDistribution = formatDepthDistribution(displayGroups);
  const costFormula = formatEdgeCantCostFormula({

    perimeterM: operatorPerimeterM,

    unitPrice: model?.cantUnitPrice ?? null,

    currency: model?.cantCurrency ?? "EUR",

    pricingMissing: model?.cantPricingMissing ?? true,

  });

  const showDetailsAccordion =

    hasLayerBreakdown ||

    cantPerimeterDisplay != null ||

    model?.calculatedCantM != null ||

    model?.pricedCantM != null ||

    model?.adhesiveMl != null ||

    model?.oracal651.present ||

    (model?.operations.length ?? 0) > 0;



  return (

    <div className={`${v6.card} mb-4`} data-testid="intake-v6-edge-cant-review-card">

      <h2 className="mb-3 text-[13px] font-bold uppercase tracking-wide text-wo-text-primary">

        {INTAKE_V6_CANT_VOLUM_LABEL}

      </h2>



      <dl className="rounded border border-wo-border-strong bg-wo-surface-inset/60 px-3 py-1">

        <MainRow

          label="Perimetru cant total"

          value={perimeterText}

          testId="intake-v6-edge-cant-operator-perimeter"

        />

        <MainRow

          label="Finisaj"

          value={groupedSummary !== "n/a" ? groupedSummary : model?.finishLabel ?? "necesită decizie"}
          testId="intake-v6-edge-cant-finish"

        />

        <MainRow

          label="Adâncime"

          value={depthDistribution !== "n/a" ? depthDistribution : formatEdgeCantDepthMm(model?.returnDepthMm ?? null)}
          testId="intake-v6-edge-cant-depth"

        />

        <MainRow

          label="Preț cant"

          value={model?.cantPriceLabel ?? "tarif lipsă"}

          testId="intake-v6-edge-cant-price"

        />

        <MainRow label="Cost cant" value={costFormula} testId="intake-v6-edge-cant-cost-formula" />

      </dl>



      {showDetailsAccordion ? (

        <div className="mt-3">

          <IntakeV6TechnicalDetailsAccordion

            title="Detalii cant"

            testId="intake-v6-edge-cant-technical-details"

          >

            {hasLayerBreakdown && layerBreakdown ? (

              <div className="mb-3" data-testid="intake-v6-edge-cant-layer-breakdown">

                <h3 className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">

                  Distribuție pe adâncime / finisaj

                </h3>

                {displayGroups.groups.length > 0 ? (

                  <dl className="mb-3 grid gap-0">

                    {displayGroups.groups.map((group) => (

                      <DebugRow

                        key={group.key}

                        label={`${group.scope === "letters" ? "Litere" : "Emblemă"} · ${formatEdgeCantDepthMm(group.depthMm)} · ${group.finishLabel}`}

                        value={`${formatEdgeCantM(group.perimeterM)} · ${group.layerCount} layer${group.layerCount === 1 ? "" : "e"}`}

                        testId={`intake-v6-edge-cant-group-${group.key}`}

                      />

                    ))}

                  </dl>

                ) : null}

                {displayGroups.normalized ? (
                  <dl className="mb-3 grid gap-0 rounded border border-amber-500/25 bg-amber-500/5 px-2 py-1">
                    <DebugRow
                      label="Total brut distributie vector"
                      value={formatEdgeCantM(displayGroups.rawTotalM)}
                      testId="intake-v6-edge-cant-raw-group-total"
                    />
                    <DebugRow
                      label="Total canonic folosit in ofertare"
                      value={formatEdgeCantM(displayGroups.targetTotalM)}
                      testId="intake-v6-edge-cant-normalized-group-total"
                    />
                  </dl>
                ) : null}

                <h3 className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">

                  Per layer
                </h3>

                <dl className="grid gap-0">

                  {layerBreakdown.layers.map((row) => (

                    <DebugRow

                      key={row.key}

                      label={`${row.scope === "letters" ? "Litere" : "Emblemă"} · ${row.label}`}
                      value={
                        row.cantActive
                          ? `${formatEdgeCantLayerPerimeter(row)} · ${formatEdgeCantDepthMm(row.depthMm)} · ${row.finishLabel}`
                          : formatEdgeCantLayerPerimeter(row)
                      }
                      testId={`intake-v6-edge-cant-layer-${row.key}`}

                    />

                  ))}

                  <DebugRow

                    label="Total litere"

                    value={formatEdgeCantM(layerBreakdown.totalLettersM)}

                    testId="intake-v6-edge-cant-total-letters"

                  />

                  <DebugRow

                    label="Total emblemă cu cant"

                    value={formatEdgeCantM(layerBreakdown.totalEmblemM)}

                    testId="intake-v6-edge-cant-total-emblem"

                  />

                  <DebugRow

                    label="Total cant"

                    value={formatEdgeCantM(layerBreakdown.totalCantM)}

                    testId="intake-v6-edge-cant-total-cant"

                  />

                </dl>

              </div>

            ) : null}



            <h3 className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">

              Debug / backend

            </h3>

            <dl className="grid gap-0">

              {cantPerimeterDisplay ? (

                <>

                  <DebugRow

                    label="Perimetru vector litere (layere față)"

                    value={formatEdgeCantM(cantPerimeterDisplay.letterVectorPerimeterM)}

                    testId="intake-v6-edge-cant-letter-vector"

                  />

                  {cantPerimeterDisplay.artworkVectorPerimeterM != null &&

                  cantPerimeterDisplay.artworkVectorPerimeterM > 0 ? (

                    <DebugRow

                      label="Perimetru emblemă cu cant"

                      value={formatEdgeCantM(cantPerimeterDisplay.artworkVectorPerimeterM)}

                      testId="intake-v6-edge-cant-artwork-vector"

                    />

                  ) : null}

                  <DebugRow

                    label="LED exterior — nu este perimetru cant"

                    value={formatEdgeCantM(cantPerimeterDisplay.ledExteriorPerimeterM)}

                    testId="intake-v6-edge-cant-led-outer"

                  />

                  <DebugRow

                    label="Quote geometry (cant canonic)"
                    value={formatEdgeCantM(cantPerimeterDisplay.quoteGeometryCantM)}

                    testId="intake-v6-edge-cant-quote-geometry"

                  />

                </>

              ) : null}

              <DebugRow

                label="Cant calculat (breakdown)"

                value={formatEdgeCantM(model?.calculatedCantM ?? null)}

                testId="intake-v6-edge-cant-calculated"

              />

              <DebugRow

                label="Cant pentru preț (+ pierdere) — nu este perimetru real"

                value={formatEdgeCantM(model?.pricedCantM ?? null)}

                testId="intake-v6-edge-cant-priced"

              />

              <DebugRow label="Pierdere ofertare" value={wasteLabel} testId="intake-v6-edge-cant-waste" />

              <DebugRow

                label="Material cant"

                value={model?.cantMaterialLabel ?? "n/a"}

                testId="intake-v6-edge-cant-material"

              />

              <DebugRow

                label="Adeziv cant"

                value={formatEdgeCantMl(model?.adhesiveMl ?? null)}

                testId="intake-v6-edge-cant-adhesive"

              />

            </dl>

            {model?.oracal651.present ? (

              <IntakeV6EdgeCantQuoteImpactPanel oracal={model.oracal651} className="mt-3" />

            ) : null}

            {(model?.operations.length ?? 0) > 0 ? (

              <div className="mt-3 border-t border-wo-border-strong pt-3" data-testid="intake-v6-edge-cant-review-ops">

                <h3 className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">

                  Operații preview cant / volum

                </h3>

                <ul className="space-y-2 text-[10px] text-slate-400">

                  {model.operations.map((op) => (

                    <li key={op.key} data-testid={`intake-v6-edge-cant-review-op-${op.key}`}>

                      {op.label} — {op.quantity.toFixed(2)} {op.unit === "linear_meter" ? "m" : op.unit}

                      {op.pricingStatus === "missing_rate" ? " · tarif lipsă" : ""}

                    </li>

                  ))}

                </ul>

              </div>

            ) : null}

          </IntakeV6TechnicalDetailsAccordion>

        </div>

      ) : null}

    </div>

  );

}





