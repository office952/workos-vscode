import { useMemo, useState } from "react";
import type {
  IntakeV6MaterialBreakdownResponse,
  IntakeV6PricedQuoteDryRunResponse,
  IntakeV6PricingInputPreviewResponse,
} from "@/lib/intakeV6/intakeV6Api";
import {
  applyIntakeV6CommercialAdjustments,
  buildIntakeV6OfferModel,
  resolveIntakeV6OfferCommercialDefaults,
  type IntakeV6OfferCommercialInputs,
} from "@/lib/intakeV6/intakeV6OfferCalculator";
import {
  intakeV6HasOfficialCommercialTotals,
  intakeV6OfficialPricingBlockerMessage,
  intakeV6OperatorFacingPricingBlocker,
} from "@/lib/intakeV6/intakeV6OfficialPricing";
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

export default function IntakeV6PricingInputPanel(props: IntakeV6PricingInputPanelProps) {
  if (props.loading) {
    return (
      <div className={`${v6.card} mb-4`} data-testid="intake-v6-pricing-input-preview">
        <p className="text-[12px] text-slate-400">Încarc pricing input preview…</p>
      </div>
    );
  }

  if (!props.preview) {
    return (
      <div className={`${v6.card} mb-4`} data-testid="intake-v6-pricing-input-preview">
        <IntakeV6AggregateCostTruthNotice compact />
        <p className="text-[12px] text-slate-300">
          Product Truth incomplet — Oferta client apare după confirmarea operatorului.
        </p>
        <p className="mt-1 text-[11px] text-slate-500">
          Nu bloca pe registry intern: Pricing / Utilaje / Pontaj rămân helper, nu fluxul principal.
        </p>
      </div>
    );
  }

  return <IntakeV6PricingInputPanelReady {...props} preview={props.preview} />;
}

function IntakeV6PricingInputPanelReady({
  preview,
  breakdown,
  officialPricing,
  title = "Rezumat Ofertă client (V6)",
  showDebugPayload = false,
  commercialInputs,
  onCommercialInputsChange,
  eurToRonRate,
  onEditCommercialInReview,
  variant = "full",
}: Omit<IntakeV6PricingInputPanelProps, "preview" | "loading"> & {
  preview: IntakeV6PricingInputPreviewResponse;
}) {
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
  const hasOfficialTotals = intakeV6HasOfficialCommercialTotals(officialPricing);
  const officialPricingBlocker = intakeV6OfficialPricingBlockerMessage(officialPricing);
  const commercialBaseSubtotal =
    hasOfficialTotals &&
    officialTotals?.commercial_base_subtotal != null &&
    Number.isFinite(officialTotals.commercial_base_subtotal)
      ? officialTotals.commercial_base_subtotal
      : hasOfficialTotals &&
          officialTotals?.subtotal_net != null &&
          Number.isFinite(officialTotals.subtotal_net) &&
          (officialTotals.commercial_adjustment_trace?.markup_percent ?? 0) === 0 &&
          (officialTotals.commercial_adjustment_trace?.discount_percent ?? 0) === 0 &&
          (officialTotals.commercial_adjustment_trace?.manual_adjustment_ron ?? 0) === 0
        ? officialTotals.subtotal_net
        : null;
  const adjustedOfficialTotals =
    hasOfficialTotals && commercialBaseSubtotal != null
      ? applyIntakeV6CommercialAdjustments(commercialBaseSubtotal, activeCommercialInputs)
      : null;
  const displayOfficialNet = adjustedOfficialTotals?.subtotalNet ?? officialTotals?.subtotal_net ?? null;
  const displayOfficialVat = adjustedOfficialTotals?.vatValue ?? officialTotals?.vat_amount ?? null;
  const displayOfficialGross = adjustedOfficialTotals?.totalGross ?? officialTotals?.total_gross ?? null;
  const displayOfficialVatRate =
    adjustedOfficialTotals?.vatPercent ?? officialTotals?.vat_rate ?? activeCommercialInputs.vatPercent;
  const internalEstimateRon =
    offerModel.internalEstimateTotal != null
      ? roundMoney(
          offerModel.internalEstimateCurrency === "RON"
            ? offerModel.internalEstimateTotal
            : offerModel.internalEstimateTotal * offerModel.eurToRonRate,
        )
      : null;
  const officialNetRon = hasOfficialTotals ? displayOfficialNet : null;
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
        Cost intern estimativ {formatCurrency(internalEstimateRon as number)} depășește Oferta client (net) cu{" "}
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
    <div className="rounded border border-wo-border-strong/40 bg-wo-surface-inset/35 p-2.5">
      <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        Reglaje comerciale
      </h4>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-[11px] text-slate-300">
          <span className="mb-1 block text-slate-400">Adaos comercial % (pe baza 7G)</span>
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
            className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[12px] text-wo-text-primary outline-none"
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
            className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[12px] text-wo-text-primary outline-none"
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
            className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[12px] text-wo-text-primary outline-none"
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
            className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[12px] text-wo-text-primary outline-none"
            data-testid="intake-v6-offer-manual-adjustment"
          />
        </label>
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-2 border-t border-wo-border-strong pt-3 text-[11px]">
        <div className="flex justify-between gap-2 text-slate-400">
          <dt>Net</dt>
          <dd className="text-slate-200" data-testid="intake-v6-offer-net-price">
            {hasOfficialTotals && displayOfficialNet != null ? formatCurrency(displayOfficialNet) : "—"}
          </dd>
        </div>
        <div className="flex justify-between gap-2 font-semibold text-emerald-300">
          <dt>{hasOfficialTotals ? "Ofertă client" : "Ofertă client (estimată)"}</dt>
          <dd data-testid="intake-v6-offer-final-price">
            {hasOfficialTotals && displayOfficialGross != null ? formatCurrency(displayOfficialGross) : "—"}
          </dd>
        </div>
        {!hasOfficialTotals && officialPricingBlocker ? (
          <div className="col-span-2 text-[11px] text-amber-200/90" data-testid="intake-v6-official-pricing-blocker">
            {intakeV6OperatorFacingPricingBlocker(officialPricingBlocker) ?? officialPricingBlocker}
          </div>
        ) : null}
        {hasOfficialTotals ? (
          <div className="col-span-2 flex justify-between gap-2 text-[11px] text-slate-500">
            <dt>Sursă preț</dt>
            <dd data-testid="intake-v6-offer-price-source">
              Backend V6 · baza 7G + adaos · TVA{" "}
              {Number(displayOfficialVatRate ?? 0).toLocaleString("ro-RO", {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2,
              })}
              %
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
      <div
        className="rounded-md border border-wo-border-strong/40 bg-transparent p-0"
        data-testid="intake-v6-pricing-input-preview"
      >
        {commercialSlidersBlock}
      </div>
    );
  }

  if (variant === "confirmHero") {
    const heroNet = hasOfficialTotals ? officialTotals?.subtotal_net ?? null : null;
    const heroGross = hasOfficialTotals ? officialTotals?.total_gross ?? null : null;

    return (
      <div className={`${v6.cardCompact} !p-3`} data-testid="intake-v6-confirm-pricing-hero">
        <IntakeV6AggregateCostTruthNotice compact />
        <h3 className={`mb-2 ${v6.sectionTitle}`}>Ofertă client</h3>
        <p className={`mb-1 ${v6.metricLabel}`}>
          {hasOfficialTotals ? "Ofertă client cu TVA" : "Ofertă client"}
        </p>
        {hasOfficialTotals && heroGross != null ? (
          <p
            className="text-[28px] font-bold tabular-nums leading-none text-emerald-300"
            data-testid="intake-v6-confirm-pricing-hero-gross"
          >
            {formatCurrency(heroGross)}
          </p>
        ) : (
          <p
            className="text-[13px] leading-relaxed text-amber-200/90"
            data-testid="intake-v6-confirm-pricing-hero-blocked"
          >
            {officialPricingBlocker ?? "Oferta client nu este disponibilă."}
          </p>
        )}
        <div className="mt-2 flex flex-wrap items-baseline justify-between gap-2 border-t border-wo-border-strong/70 pt-2 text-[11px]">
          <span className="text-slate-500">Ofertă client netă</span>
          <span className="tabular-nums text-cyan-200" data-testid="intake-v6-confirm-pricing-hero-net">
            {heroNet != null ? formatCurrency(heroNet) : "—"}
          </span>
        </div>
        <div className="mt-1 flex flex-wrap items-baseline justify-between gap-2 text-[11px]">
          <span className="text-slate-500">Cost intern estimativ</span>
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
              ? `Ofertă client (backend V6) · TVA ${Number(officialTotals?.vat_rate ?? 0).toLocaleString("ro-RO", {
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 2,
                })}%`
              : `Ofertă client în RON · curs ${offerModel.eurToRonRate.toLocaleString("ro-RO", {
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
        <div className="rounded border border-wo-border-strong bg-wo-surface-inset/50 p-3">
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
              <section key={group.key} className="rounded border border-wo-border-subtle bg-wo-surface-inset/60 p-2.5">
                <div className="mb-2 flex items-center justify-between gap-3 border-b border-wo-border-subtle pb-2">
                  <h5 className={v6.zoneTitle}>{group.label}</h5>
                  <strong className="text-wo-text-primary">
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
                        <strong className="text-wo-text-primary">{formatCurrency(line.amount)}</strong>
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

        <div className="rounded border border-wo-border-strong bg-wo-surface-inset/50 p-3">
          <h4 className={`mb-3 ${v6.sectionTitle}`}>Setări comerciale</h4>
          <div className="space-y-3 text-[11px] text-slate-300">
            <label className="block">
              <span className="mb-1 block text-slate-400">Adaos comercial % (pe baza 7G)</span>
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
                className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[12px] text-wo-text-primary outline-none"
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
                className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[12px] text-wo-text-primary outline-none"
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
                className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[12px] text-wo-text-primary outline-none"
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
                className="w-full rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-1.5 text-[12px] text-wo-text-primary outline-none"
                data-testid="intake-v6-offer-manual-adjustment"
              />
            </label>
          </div>

          <dl className="mt-4 space-y-2 text-[11px]">
            {hasOfficialTotals ? (
              <>
                <div className="flex items-center justify-between gap-3 text-slate-300">
                  <dt>Ofertă client netă</dt>
                  <dd data-testid="intake-v6-offer-net-price">
                    {formatCurrency(displayOfficialNet ?? 0)}
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-3 text-slate-300">
                  <dt>TVA ({Number(displayOfficialVatRate)}%)</dt>
                  <dd data-testid="intake-v6-offer-vat-amount">
                    {formatCurrency(displayOfficialVat ?? 0)}
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-3 border-t border-wo-border-strong pt-2 text-[12px] font-semibold text-emerald-300">
                  <dt>Ofertă client cu TVA</dt>
                  <dd data-testid="intake-v6-offer-final-price">
                    {formatCurrency(displayOfficialGross ?? 0)}
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-3 text-[10px] text-slate-500">
                  <dt>Sursă Ofertă client</dt>
                  <dd data-testid="intake-v6-offer-price-source">Backend V6 · baza 7G + adaos</dd>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center justify-between gap-3 text-slate-300">
                  <dt>Ofertă client netă</dt>
                  <dd>—</dd>
                </div>
                <div className="flex items-center justify-between gap-3 border-t border-wo-border-strong pt-2 text-[12px] font-semibold text-amber-200/90">
                  <dt>Ofertă client</dt>
                  <dd data-testid="intake-v6-offer-final-price">—</dd>
                </div>
                {officialPricingBlocker ? (
                  <div className="text-[11px] text-amber-200/90" data-testid="intake-v6-official-pricing-blocker">
                    {officialPricingBlocker}
                  </div>
                ) : null}
                <div className="rounded border border-wo-border-subtle bg-wo-surface-inset/40 p-2 text-[10px] text-slate-500">
                  <p className="mb-1 font-semibold text-slate-400">Estimare locală (nu este Ofertă client)</p>
                  <div className="flex items-center justify-between gap-3 text-slate-400">
                    <span>Bază Cost intern estimativ × adaos</span>
                    <span>{formatCurrency(offerModel.totalGross)}</span>
                  </div>
                </div>
              </>
            )}
          </dl>
        </div>
      </div>

      <div className="mb-3 rounded border border-wo-border-strong bg-wo-surface-inset/40 p-3 text-[11px] text-slate-400">
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
          <pre className="mt-2 max-h-48 overflow-auto rounded border border-wo-border-strong bg-wo-surface-inset/60 p-2 text-[10px]">
            {JSON.stringify(preview.quote_input_payload, null, 2)}
          </pre>
        </details>
      ) : null}
    </div>
  );
}



