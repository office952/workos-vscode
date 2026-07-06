import { useMemo, useState } from "react";
import type {
  IntakeV6MaterialBreakdownResponse,
  IntakeV6PricedQuoteDryRunResponse,
  IntakeV6PricingInputPreviewResponse,
} from "@/lib/intakeV6/intakeV6Api";
import {
  buildIntakeV6OfferModel,
  resolveIntakeV6OfferCommercialDefaults,
  type IntakeV6OfferCommercialInputs,
} from "@/lib/intakeV6/intakeV6OfferCalculator";
import { formatFaceBackPrepMoney } from "@/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";
import { IntakeV6AggregateCostTruthNotice } from "./IntakeV6AggregateCostTruthNotice";

interface IntakeV6PricingInputPanelProps {
  preview: IntakeV6PricingInputPreviewResponse | null;
  breakdown?: IntakeV6MaterialBreakdownResponse | null;
  officialPricing?: IntakeV6PricedQuoteDryRunResponse | null;
  loading: boolean;
  title?: string;
  showDebugPayload?: boolean;
  commercialInputs?: IntakeV6OfferCommercialInputs;
  onCommercialInputsChange?: (next: IntakeV6OfferCommercialInputs) => void;
  eurToRonRate?: number | null;
  onEditCommercialInReview?: () => void;
  /** Sliders + totals only — no cost structure breakdown. */
  variant?: "full" | "commercialSliders" | "confirmHero";
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("ro-RO", {
    style: "currency",
    currency: "RON",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value: number, digits = 2): string {
  return new Intl.NumberFormat("ro-RO", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

export default function IntakeV6PricingInputPanel({
  preview,
  breakdown,
  officialPricing,
  loading,
  title = "Rezumat ofertare V6",
  showDebugPayload = false,
  commercialInputs,
  onCommercialInputsChange,
  eurToRonRate,
  onEditCommercialInReview,
  variant = "full",
}: IntakeV6PricingInputPanelProps) {
  if (loading) {
    return (
      <div className={`${v6.card} mb-4`} data-testid="intake-v6-pricing-input-preview">
        <p className="text-[12px] text-slate-400">Încarc pricing input preview…</p>
      </div>
    );
  }

  if (!preview) {
    return (
      <div className={`${v6.card} mb-4`} data-testid="intake-v6-pricing-input-preview">
        <p className="text-[12px] text-slate-400">Pricing input preview indisponibil.</p>
      </div>
    );
  }

  const quoteInput = preview.quote_input_payload;
  const [localCommercialInputs, setLocalCommercialInputs] = useState<IntakeV6OfferCommercialInputs>(() =>
    resolveIntakeV6OfferCommercialDefaults(preview),
  );
  const activeCommercialInputs = commercialInputs ?? localCommercialInputs;
  const setCommercialInputs = (next: IntakeV6OfferCommercialInputs) => {
    onCommercialInputsChange?.(next);
    if (!commercialInputs) {
      setLocalCommercialInputs(next);
    }
  };

  const offerModel = useMemo(
    () =>
      buildIntakeV6OfferModel({
        preview,
        breakdown,
        commercialInputs: activeCommercialInputs,
        eurToRonRate,
      }),
    [preview, breakdown, activeCommercialInputs, eurToRonRate],
  );

  if (!offerModel) {
    return null;
  }

  const officialTotals = officialPricing?.commercial_totals ?? null;
  const hasOfficialTotals =
    officialPricing?.pricing_status === "V6_PRICED_DRY_RUN_READY" &&
    officialTotals?.subtotal_net != null &&
    officialTotals?.total_gross != null;
  const internalEstimateRon =
    offerModel.internalEstimateTotal != null
      ? roundMoney(
          offerModel.internalEstimateCurrency === "RON"
            ? offerModel.internalEstimateTotal
            : offerModel.internalEstimateTotal * offerModel.eurToRonRate,
        )
      : null;
  const officialNetRon = hasOfficialTotals ? officialTotals.subtotal_net : offerModel.subtotalNet;
  const internalMarginVsNetRon =
    internalEstimateRon != null && officialNetRon != null ? roundMoney(officialNetRon - internalEstimateRon) : null;
  const hasNegativeInternalMargin =
    hasOfficialTotals && internalMarginVsNetRon != null && internalMarginVsNetRon < 0;
  const negativeInternalMarginAlert = hasNegativeInternalMargin ? (
    <div
      className="mt-3 rounded border border-red-500/40 bg-red-500/10 px-3 py-2 text-[11px] text-red-100"
      data-testid="intake-v6-negative-margin-warning"
    >
      <p className="font-semibold">Marjă internă negativă</p>
      <p className="mt-1 text-red-100/90">
        Cost intern referință {formatCurrency(internalEstimateRon as number)} depășește prețul net oficial cu{" "}
        {formatCurrency(Math.abs(internalMarginVsNetRon as number))}.
      </p>
    </div>
  ) : null;

  const groupedCostLines = offerModel.costLines.reduce<
    Array<{ key: string; label: string; items: typeof offerModel.costLines }>
  >((groups, line) => {
    const groupKey = line.groupKey ?? line.key;
    const groupLabel = line.groupLabel ?? line.label;
    const existing = groups.find((group) => group.key === groupKey);
    if (existing) {
      existing.items.push(line);
      return groups;
    }
    groups.push({ key: groupKey, label: groupLabel, items: [line] });
    return groups;
  }, []);

  const shouldRenderGroupItems = (group: (typeof groupedCostLines)[number]) =>
    !(group.items.length === 1 && group.items[0]?.label === group.label);

  const commercialSlidersBlock = (
    <div className="rounded border border-[#2A3548] bg-[#0A0F1A]/50 p-3">
      <h4 className="mb-3 text-[12px] font-semibold text-slate-200">Reglaje comerciale</h4>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-[11px] text-slate-300">
          <span className="mb-1 block text-slate-400">Adaos %</span>
          <input
            type="number"
            min={0}
            max={400}
            step={1}
            value={activeCommercialInputs.markupPercent}
            onChange={(event) =>
              setCommercialInputs({
                ...activeCommercialInputs,
                markupPercent: Number(event.target.value) || 0,
              })
            }
            className="w-full rounded border border-[#2A3548] bg-[#0F1724] px-2 py-1.5 text-[12px] text-slate-100 outline-none"
            data-testid="intake-v6-offer-markup"
          />
        </label>
        <label className="block text-[11px] text-slate-300">
          <span className="mb-1 block text-slate-400">Discount %</span>
          <input
            type="number"
            min={0}
            max={100}
            step={1}
            value={activeCommercialInputs.discountPercent}
            onChange={(event) =>
              setCommercialInputs({
                ...activeCommercialInputs,
                discountPercent: Number(event.target.value) || 0,
              })
            }
            className="w-full rounded border border-[#2A3548] bg-[#0F1724] px-2 py-1.5 text-[12px] text-slate-100 outline-none"
            data-testid="intake-v6-offer-discount"
          />
        </label>
        <label className="block text-[11px] text-slate-300">
          <span className="mb-1 block text-slate-400">TVA %</span>
          <input
            type="number"
            min={0}
            max={100}
            step={1}
            value={activeCommercialInputs.vatPercent}
            readOnly
            disabled
            className="w-full rounded border border-[#2A3548] bg-[#0F1724] px-2 py-1.5 text-[12px] text-slate-100 outline-none"
            data-testid="intake-v6-offer-vat"
          />
        </label>
        <label className="block text-[11px] text-slate-300">
          <span className="mb-1 block text-slate-400">Ajustare manuală (RON)</span>
          <input
            type="number"
            step={10}
            value={activeCommercialInputs.manualAdjustmentRon}
            onChange={(event) =>
              setCommercialInputs({
                ...activeCommercialInputs,
                manualAdjustmentRon: Number(event.target.value) || 0,
              })
            }
            className="w-full rounded border border-[#2A3548] bg-[#0F1724] px-2 py-1.5 text-[12px] text-slate-100 outline-none"
            data-testid="intake-v6-offer-manual-adjustment"
          />
        </label>
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-2 border-t border-[#2A3548] pt-3 text-[11px]">
        <div className="flex justify-between gap-2 text-slate-400">
          <dt>Net</dt>
          <dd className="text-slate-200">
            {formatCurrency(hasOfficialTotals ? officialTotals.subtotal_net : offerModel.subtotalNet)}
          </dd>
        </div>
        <div className="flex justify-between gap-2 font-semibold text-emerald-300">
          <dt>{hasOfficialTotals ? "Preț oficial" : "Cu TVA"}</dt>
          <dd data-testid="intake-v6-offer-final-price">
            {formatCurrency(hasOfficialTotals ? officialTotals.total_gross : offerModel.totalGross)}
          </dd>
        </div>
        {hasOfficialTotals ? (
          <div className="col-span-2 flex justify-between gap-2 text-[11px] text-slate-500">
            <dt>Sursă preț</dt>
            <dd data-testid="intake-v6-offer-price-source">
              Backend V6 · TVA {Number(officialTotals.vat_rate ?? 0).toLocaleString("ro-RO", {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2,
              })}%
            </dd>
          </div>
        ) : offerModel.internalEstimateCurrency === "EUR" ? (
          <div className="col-span-2 flex justify-between gap-2 text-[11px] text-slate-500">
            <dt>Curs cost intern</dt>
            <dd data-testid="intake-v6-offer-eur-ron-rate">
              1 EUR = {offerModel.eurToRonRate.toLocaleString("ro-RO", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 4,
              })}{" "}
              RON
            </dd>
          </div>
        ) : null}
      </dl>
      {negativeInternalMarginAlert}
    </div>
  );

  if (variant === "commercialSliders") {
    return (
      <div className={`${v6.cardCompact} mb-3 !p-3`} data-testid="intake-v6-pricing-input-preview">
        {commercialSlidersBlock}
      </div>
    );
  }

  if (variant === "confirmHero") {
    const heroNet = hasOfficialTotals ? officialTotals.subtotal_net : offerModel.subtotalNet;
    const heroGross = hasOfficialTotals ? officialTotals.total_gross : offerModel.totalGross;

    return (
      <div className={`${v6.cardCompact} !p-3`} data-testid="intake-v6-confirm-pricing-hero">
        <IntakeV6AggregateCostTruthNotice compact />
        <h3 className={`mb-2 ${v6.sectionTitle}`}>Ofertă comercială</h3>
        <p className={`mb-1 ${v6.metricLabel}`}>{hasOfficialTotals ? "Preț oficial cu TVA" : "Total cu TVA"}</p>
        <p
          className="text-[28px] font-bold tabular-nums leading-none text-emerald-300"
          data-testid="intake-v6-confirm-pricing-hero-gross"
        >
          {formatCurrency(heroGross)}
        </p>
        <div className="mt-2 flex flex-wrap items-baseline justify-between gap-2 border-t border-[#243044]/70 pt-2 text-[11px]">
          <span className="text-slate-500">Net</span>
          <span className="tabular-nums text-cyan-200" data-testid="intake-v6-confirm-pricing-hero-net">
            {formatCurrency(heroNet)}
          </span>
        </div>
        <div className="mt-1 flex flex-wrap items-baseline justify-between gap-2 text-[11px]">
          <span className="text-slate-500">Cost intern referință</span>
          <span className="tabular-nums text-slate-200">
            {breakdown?.totals.estimated_cost_total != null
              ? formatFaceBackPrepMoney(
                  breakdown.totals.estimated_cost_total,
                  breakdown.totals.currency ?? "EUR",
                )
              : "—"}
          </span>
        </div>
        {offerModel.internalEstimateCurrency === "EUR" ? (
          <p className="mt-1 text-[10px] text-slate-500" data-testid="intake-v6-confirm-pricing-hero-fx">
            {hasOfficialTotals
              ? `Preț oficial backend V6 · TVA ${Number(officialTotals?.vat_rate ?? 0).toLocaleString("ro-RO", {
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 2,
                })}%`
              : `Oferta în RON · curs ${offerModel.eurToRonRate.toLocaleString("ro-RO", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 4,
                })} RON/EUR`}
          </p>
        ) : null}
        {negativeInternalMarginAlert}
        {onEditCommercialInReview ? (
          <button
            type="button"
            className="mt-2 text-[11px] font-semibold text-cyan-300 hover:text-cyan-200"
            onClick={onEditCommercialInReview}
            data-testid="intake-v6-confirm-edit-commercial-review"
          >
            Modifică adaos / discount în Review →
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-pricing-input-preview">
      <h3 className={`mb-3 ${v6.sectionTitle}`}>
        {title}
      </h3>
      <IntakeV6AggregateCostTruthNotice />
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <AtomsBadge tone={preview.is_ready_for_quote ? "ok" : "pending"}>
          {preview.adapter_status}
        </AtomsBadge>
        {preview.readiness_status ? (
          <span className="text-[11px] text-slate-500">readiness: {preview.readiness_status}</span>
        ) : null}
      </div>

      <dl className="mb-3 grid gap-1 text-[11px] text-slate-400 sm:grid-cols-2">
        <div>
          <dt>Litere</dt>
          <dd className="text-slate-200">{offerModel.letterCount ?? "—"}</dd>
        </div>
        <div>
          <dt>Perimetru litere</dt>
          <dd className="text-slate-200">
            {offerModel.perimeterM > 0 ? `${Number(offerModel.perimeterM).toFixed(2)} m` : "—"}
          </dd>
        </div>
        <div>
          <dt>Suprafață față</dt>
          <dd className="text-slate-200">
            {offerModel.faceAreaM2 > 0 ? `${Number(offerModel.faceAreaM2).toFixed(3)} m²` : "—"}
          </dd>
        </div>
        <div>
          <dt>Iluminat</dt>
          <dd className="text-slate-200">{offerModel.illuminated ? "Da" : "Nu"}</dd>
        </div>
      </dl>

      <div className="mb-4 grid gap-3 lg:grid-cols-[1.3fr_0.9fr]">
        <div className="rounded border border-[#2A3548] bg-[#0A0F1A]/50 p-3">
          <div className="mb-2 flex items-center justify-between gap-3">
            <h4 className={`${v6.zoneTitle} text-slate-200`}>Structura cost V6</h4>
            <span className="text-[10px] text-slate-500">
              {offerModel.fallbackCount === 0
                ? "costuri extrase din payload"
                : `${offerModel.fallbackCount} linii estimate local`}
            </span>
          </div>
          <div className="space-y-3 text-[11px]">
            {groupedCostLines.map((group) => (
              <section key={group.key} className="rounded border border-[#1C2433] bg-[#0F1724]/60 p-2.5">
                <div className="mb-2 flex items-center justify-between gap-3 border-b border-[#1C2433] pb-2">
                  <h5 className={v6.zoneTitle}>{group.label}</h5>
                  <strong className="text-slate-100">
                    {formatCurrency(group.items.reduce((sum, item) => sum + item.amount, 0))}
                  </strong>
                </div>
                {shouldRenderGroupItems(group) ? (
                  <ul className="space-y-2">
                    {group.items.map((line) => (
                      <li key={line.key} className="flex items-center justify-between gap-3 last:pb-0">
                        <div>
                          <p className="text-slate-200">{line.label}</p>
                          <p className="text-[10px] text-slate-500">
                            {line.source === "payload" ? "sursa: breakdown ofertare" : "sursa: estimare V6 locala"}
                          </p>
                        </div>
                        <strong className="text-slate-100">{formatCurrency(line.amount)}</strong>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-[10px] text-slate-500">
                    {group.items[0]?.source === "payload" ? "sursa: breakdown ofertare" : "sursa: estimare V6 locala"}
                  </p>
                )}
              </section>
            ))}
          </div>
        </div>

        <div className="rounded border border-[#2A3548] bg-[#0A0F1A]/50 p-3">
          <h4 className={`mb-3 ${v6.sectionTitle}`}>Setări comerciale</h4>
          <div className="space-y-3 text-[11px] text-slate-300">
            <label className="block">
              <span className="mb-1 block text-slate-400">Adaos comercial %</span>
              <input
                type="number"
                min={0}
                max={400}
                step={1}
                value={activeCommercialInputs.markupPercent}
                onChange={(event) =>
                  setCommercialInputs({
                    ...activeCommercialInputs,
                    markupPercent: Number(event.target.value) || 0,
                  })
                }
                className="w-full rounded border border-[#2A3548] bg-[#0F1724] px-2 py-1.5 text-[12px] text-slate-100 outline-none"
                data-testid="intake-v6-offer-markup"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-slate-400">Discount comercial %</span>
              <input
                type="number"
                min={0}
                max={100}
                step={1}
                value={activeCommercialInputs.discountPercent}
                onChange={(event) =>
                  setCommercialInputs({
                    ...activeCommercialInputs,
                    discountPercent: Number(event.target.value) || 0,
                  })
                }
                className="w-full rounded border border-[#2A3548] bg-[#0F1724] px-2 py-1.5 text-[12px] text-slate-100 outline-none"
                data-testid="intake-v6-offer-discount"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-slate-400">TVA %</span>
              <input
                type="number"
                min={0}
                max={100}
                step={1}
                value={activeCommercialInputs.vatPercent}
                readOnly
                disabled
                className="w-full rounded border border-[#2A3548] bg-[#0F1724] px-2 py-1.5 text-[12px] text-slate-100 outline-none"
                data-testid="intake-v6-offer-vat"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-slate-400">Ajustare manuala (RON)</span>
              <input
                type="number"
                step={10}
                value={activeCommercialInputs.manualAdjustmentRon}
                onChange={(event) =>
                  setCommercialInputs({
                    ...activeCommercialInputs,
                    manualAdjustmentRon: Number(event.target.value) || 0,
                  })
                }
                className="w-full rounded border border-[#2A3548] bg-[#0F1724] px-2 py-1.5 text-[12px] text-slate-100 outline-none"
                data-testid="intake-v6-offer-manual-adjustment"
              />
            </label>
          </div>

          <dl className="mt-4 space-y-2 text-[11px]">
            <div className="flex items-center justify-between gap-3 text-slate-300">
              <dt>Baza productie</dt>
              <dd>{formatCurrency(offerModel.productionBase)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3 text-slate-300">
              <dt>Adaos</dt>
              <dd>{formatCurrency(offerModel.markupValue)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3 text-slate-300">
              <dt>Ajustare manuala</dt>
              <dd>{formatCurrency(offerModel.manualAdjustmentRon)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3 text-slate-300">
              <dt>Discount</dt>
              <dd>-{formatCurrency(offerModel.discountValue)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3 text-slate-300">
              <dt>Total net</dt>
              <dd>{formatCurrency(offerModel.subtotalNet)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3 text-slate-300">
              <dt>TVA ({activeCommercialInputs.vatPercent}%)</dt>
              <dd>{formatCurrency(offerModel.vatValue)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3 border-t border-[#2A3548] pt-2 text-[12px] font-semibold text-emerald-300">
              <dt>Total cu TVA</dt>
              <dd data-testid="intake-v6-offer-final-price">{formatCurrency(offerModel.totalGross)}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="mb-3 rounded border border-[#2A3548] bg-[#0A0F1A]/40 p-3 text-[11px] text-slate-400">
        <h4 className={`mb-2 ${v6.sectionTitle}`}>Bază tehnică pentru ofertă</h4>
        <div className="grid gap-2 sm:grid-cols-3">
          <div>
            <dt>Perimetru utilizat</dt>
            <dd className="text-slate-200">{offerModel.perimeterM > 0 ? `${formatNumber(offerModel.perimeterM)} m` : "—"}</dd>
          </div>
          <div>
            <dt>Suprafata utilizata</dt>
            <dd className="text-slate-200">{offerModel.faceAreaM2 > 0 ? `${formatNumber(offerModel.faceAreaM2, 3)} m²` : "—"}</dd>
          </div>
          <div>
            <dt>Review finisaje grupate</dt>
            <dd className="text-slate-200">{preview.requires_grouped_finish_review ? "Necesar" : "Nu"}</dd>
          </div>
        </div>
      </div>

      {(preview.adapter_blockers.length > 0 || preview.adapter_warnings.length > 0) && (
        <ul className="mb-3 space-y-1 text-[11px]">
          {preview.adapter_blockers.map((item) => (
            <li key={`b-${item}`} className="text-red-300">
              {item}
            </li>
          ))}
          {preview.adapter_warnings.map((item) => (
            <li key={`w-${item}`} className="text-amber-200">
              {item}
            </li>
          ))}
        </ul>
      )}

      {showDebugPayload ? (
        <details className="text-[11px] text-slate-400">
          <summary className="cursor-pointer text-slate-300">quote_input_payload (debug)</summary>
          <pre className="mt-2 max-h-48 overflow-auto rounded border border-[#2A3548] bg-[#0A0F1A]/60 p-2 text-[10px]">
            {JSON.stringify(preview.quote_input_payload, null, 2)}
          </pre>
        </details>
      ) : null}
    </div>
  );
}



