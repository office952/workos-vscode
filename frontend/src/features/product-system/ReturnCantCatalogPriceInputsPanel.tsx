import {
  buildReturnCantCatalogPriceSummary,
  catalogPriceInputStatusLabel,
  catalogPriceInputStatusTone,
  formatCatalogPriceConfirmedValue,
  getReturnCantCatalogPriceInputsByCategory,
  RETURN_CANT_CATALOG_PRICE_INPUTS,
  RETURN_CANT_CATALOG_PRICE_SECTIONS,
  type ReturnCantCatalogPriceInput,
} from "./componentFirstReturnCantCatalogPriceInputs";

function StatusChip({
  label,
  tone,
  testId,
}: {
  label: string;
  tone: "emerald" | "amber" | "rose" | "slate" | "cyan";
  testId?: string;
}) {
  const toneClass =
    tone === "emerald"
      ? "border-emerald-800/40 bg-emerald-950/25 text-emerald-200"
      : tone === "cyan"
        ? "border-cyan-800/40 bg-cyan-950/25 text-cyan-200"
        : tone === "amber"
          ? "border-amber-800/40 bg-amber-950/25 text-amber-200"
          : tone === "rose"
            ? "border-rose-800/40 bg-rose-950/25 text-rose-200"
            : "border-slate-700 bg-slate-900 text-slate-400";

  return (
    <span
      data-testid={testId}
      className={`rounded border px-1.5 py-0.5 text-[9px] font-bold uppercase ${toneClass}`}
    >
      {label}
    </span>
  );
}

function CatalogPriceInputRow({ input }: { input: ReturnCantCatalogPriceInput }) {
  return (
    <tr data-testid={`product-system-return-cant-catalog-price-row-${input.key}`}>
      <td className="px-2 py-2 align-top text-[10px] text-slate-300">{input.labelRo}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip
          label={catalogPriceInputStatusLabel(input.status)}
          tone={catalogPriceInputStatusTone(input.status)}
          testId={`product-system-return-cant-catalog-price-status-${input.key}`}
        />
      </td>
      <td
        data-testid={`product-system-return-cant-catalog-price-known-${input.key}`}
        className="px-2 py-2 align-top text-[10px] text-slate-300"
      >
        {input.knownSoFarRo}
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">
        <ul className="space-y-0.5">
          {input.stillMissingRo.map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
      </td>
      <td
        data-testid={`product-system-return-cant-catalog-price-value-${input.key}`}
        className="px-2 py-2 align-top text-[10px] font-semibold text-slate-200"
      >
        {formatCatalogPriceConfirmedValue(input)}
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">{input.ownerQuestionRo}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip label="NO" tone="slate" testId={`product-system-return-cant-catalog-price-active-${input.key}`} />
      </td>
    </tr>
  );
}

export function ReturnCantCatalogPriceInputsPanel() {
  const summary = buildReturnCantCatalogPriceSummary();

  return (
    <section
      data-testid="product-system-return-cant-catalog-price-inputs"
      className="space-y-4 rounded-xl border border-orange-900/40 bg-orange-950/10 px-4 py-4"
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-sm font-semibold text-orange-100">RETURN-CANT catalog &amp; price inputs</h4>
          <StatusChip
            label="NOT READY FOR PRICING"
            tone="rose"
            testId="product-system-return-cant-catalog-price-global-status"
          />
        </div>
        <p className="mt-1 text-[10px] text-slate-500">
          Catalogurile și prețurile sunt pregătite ca owner workshop · nu există Pricing activation
        </p>
      </div>

      <div
        data-testid="product-system-return-cant-catalog-price-safety"
        className="rounded-lg border border-slate-800/80 bg-slate-950/50 px-3 py-2 text-[10px] text-slate-400"
      >
        <p>
          Catalogurile și prețurile sunt pregătite ca owner workshop. Nu există Pricing activation, Product
          Truth write sau Work Intake exposure.
        </p>
        <p className="mt-1">No Product Truth live write</p>
        <p>No Pricing activation</p>
        <p>No Work Intake exposure</p>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <div
          data-testid="product-system-return-cant-catalog-price-summary-confirmed"
          className="rounded-md border border-emerald-800/30 bg-emerald-950/10 px-2 py-1.5"
        >
          <p className="text-[10px] font-semibold uppercase text-slate-500">Confirmed</p>
          <p className="text-base font-bold tabular-nums text-emerald-200">{summary.ownerConfirmedCount}</p>
        </div>
        <div
          data-testid="product-system-return-cant-catalog-price-summary-partial"
          className="rounded-md border border-cyan-800/30 bg-cyan-950/10 px-2 py-1.5"
        >
          <p className="text-[10px] font-semibold uppercase text-slate-500">Partial</p>
          <p className="text-base font-bold tabular-nums text-cyan-200">{summary.partialConfirmedCount}</p>
        </div>
        <div
          data-testid="product-system-return-cant-catalog-price-summary-owner-input"
          className="rounded-md border border-amber-800/30 bg-amber-950/10 px-2 py-1.5"
        >
          <p className="text-[10px] font-semibold uppercase text-slate-500">Owner input required</p>
          <p className="text-base font-bold tabular-nums text-amber-200">{summary.ownerInputRequiredCount}</p>
        </div>
        <div
          data-testid="product-system-return-cant-catalog-price-summary-pricing-active"
          className="rounded-md border border-slate-800 bg-slate-950/40 px-2 py-1.5"
        >
          <p className="text-[10px] font-semibold uppercase text-slate-500">Pricing active</p>
          <p className="text-base font-bold tabular-nums text-slate-200">{summary.pricingActiveCount}</p>
        </div>
      </div>

      <article
        data-testid="product-system-return-cant-catalog-price-blockers"
        className="rounded-lg border border-rose-800/30 bg-rose-950/10 px-3 py-2.5"
      >
        <p className="text-[10px] font-bold uppercase text-rose-200/90">Blockers before pricing</p>
        <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
          {summary.blockersBeforePricing.map((blocker) => (
            <li key={blocker}>• {blocker}</li>
          ))}
        </ul>
      </article>

      {RETURN_CANT_CATALOG_PRICE_SECTIONS.map((section) => {
        const rows = getReturnCantCatalogPriceInputsByCategory(section.category);
        if (rows.length === 0) return null;
        return (
          <article
            key={section.sectionKey}
            data-testid={`product-system-return-cant-catalog-price-section-${section.sectionKey}`}
            className="rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-3"
          >
            <p className="text-[11px] font-bold uppercase text-slate-200">{section.labelRo}</p>
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full border-collapse text-left">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] font-bold uppercase tracking-wide text-slate-500">
                    <th className="px-2 py-2">Input</th>
                    <th className="px-2 py-2">Status</th>
                    <th className="px-2 py-2">Known so far</th>
                    <th className="px-2 py-2">Still missing</th>
                    <th className="px-2 py-2">Confirmed value</th>
                    <th className="px-2 py-2">Owner question</th>
                    <th className="px-2 py-2">Pricing active</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((input) => (
                    <CatalogPriceInputRow key={input.key} input={input} />
                  ))}
                </tbody>
              </table>
            </div>
          </article>
        );
      })}

      <p
        data-testid="product-system-return-cant-catalog-price-ready-for-pricing"
        className="text-[10px] font-semibold uppercase text-rose-200/90"
      >
        Ready for pricing: NO
      </p>
    </section>
  );
}

export { RETURN_CANT_CATALOG_PRICE_INPUTS };
