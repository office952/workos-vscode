import {
  buildFaceEstimateDraftSummary,
  FACE_CNC_CUTTING_ESTIMATE_DRAFTS,
  FACE_CNC_MINIMUM_POLICY_DRAFT,
  FACE_ESTIMATE_CALCULATION_RULES,
  FACE_ESTIMATE_DRAFT_AUTHORITY,
  FACE_INVENTORY_PRICING_CROSS_REFERENCES,
  FACE_MATERIAL_ESTIMATE_DRAFTS,
  formatFaceEstimateDraftValue,
  type FaceEstimateDraftEntry,
} from "./candidateModuleProdusFaceEstimatedPriceDraft";

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
    tone === "amber"
      ? "border-amber-800/40 bg-amber-950/25 text-amber-200"
      : tone === "cyan"
        ? "border-cyan-800/40 bg-cyan-950/25 text-cyan-200"
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

function DraftRow({ entry }: { entry: FaceEstimateDraftEntry }) {
  return (
    <tr data-testid={`product-system-face-estimate-draft-row-${entry.key}`}>
      <td className="px-2 py-2 align-top text-[10px] text-slate-300">{entry.labelRo}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip
          label="OWNER ESTIMATE DRAFT"
          tone="amber"
          testId={`product-system-face-estimate-draft-status-${entry.key}`}
        />
      </td>
      <td
        data-testid={`product-system-face-estimate-draft-value-${entry.key}`}
        className="px-2 py-2 align-top text-[10px] font-semibold text-slate-200"
      >
        {formatFaceEstimateDraftValue(entry)}
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-500">{entry.notesRo}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip label="NO" tone="slate" testId={`product-system-face-estimate-active-${entry.key}`} />
      </td>
    </tr>
  );
}

export function FaceEstimatedPriceDraftPanel() {
  const summary = buildFaceEstimateDraftSummary();

  return (
    <section
      data-testid="product-system-face-estimate-draft-panel"
      className="space-y-4 rounded-xl border border-orange-900/40 bg-orange-950/10 px-4 py-4"
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-sm font-semibold text-orange-100">FACE estimated prices — owner draft</h4>
          <StatusChip
            label={FACE_ESTIMATE_DRAFT_AUTHORITY.label.replace(/_/g, " ")}
            tone="amber"
            testId="product-system-face-estimate-draft-authority-badge"
          />
          <StatusChip
            label="NOT PRICING REGISTRY"
            tone="slate"
            testId="product-system-face-estimate-not-registry-badge"
          />
        </div>
        <p className="mt-1 text-[10px] text-slate-500">
          Editable by owner · not active pricing · no /inventory/pricing write
        </p>
      </div>

      <div
        data-testid="product-system-face-estimate-draft-safety"
        className="rounded-lg border border-slate-800/80 bg-slate-950/50 px-3 py-2 text-[10px] text-slate-400"
      >
        <p>Not Pricing Registry authority</p>
        <p>Not active pricing</p>
        <p>No Product Truth live write</p>
        <p>No Pricing activation</p>
        <p data-testid="product-system-face-estimate-ready-for-pricing">Ready for pricing: NO</p>
        <p data-testid="product-system-face-estimate-pricing-active-count">
          Pricing active rows: {summary.pricingActiveCount}
        </p>
      </div>

      <article
        data-testid="product-system-face-estimate-calculation-rules"
        className="rounded-lg border border-cyan-900/30 bg-cyan-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-cyan-200">Reguli calcul estimativ</p>
        <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
          {FACE_ESTIMATE_CALCULATION_RULES.map((rule) => (
            <li key={rule}>• {rule}</li>
          ))}
        </ul>
      </article>

      <article data-testid="product-system-face-estimate-material-table">
        <p className="text-[11px] font-bold uppercase text-slate-200">Material FACE — Plexiglas / acrylic</p>
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-800 text-[10px] font-bold uppercase text-slate-500">
                <th className="px-2 py-2">Label</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Estimate</th>
                <th className="px-2 py-2">Notes</th>
                <th className="px-2 py-2">Active</th>
              </tr>
            </thead>
            <tbody>
              {FACE_MATERIAL_ESTIMATE_DRAFTS.map((entry) => (
                <DraftRow key={entry.key} entry={entry} />
              ))}
            </tbody>
          </table>
        </div>
      </article>

      <article data-testid="product-system-face-estimate-cnc-table">
        <p className="text-[11px] font-bold uppercase text-slate-200">Debitare CNC FACE — pe contur</p>
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-800 text-[10px] font-bold uppercase text-slate-500">
                <th className="px-2 py-2">Label</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Estimate</th>
                <th className="px-2 py-2">Notes</th>
                <th className="px-2 py-2">Active</th>
              </tr>
            </thead>
            <tbody>
              {FACE_CNC_CUTTING_ESTIMATE_DRAFTS.map((entry) => (
                <DraftRow key={entry.key} entry={entry} />
              ))}
            </tbody>
          </table>
        </div>
      </article>

      <article
        data-testid="product-system-face-estimate-cnc-minimum"
        className="rounded-lg border border-amber-900/30 bg-amber-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-amber-200">Setup / minim debitare CNC</p>
        <p
          data-testid="product-system-face-estimate-cnc-minimum-value"
          className="mt-2 text-[10px] font-semibold text-slate-200"
        >
          {FACE_CNC_MINIMUM_POLICY_DRAFT.estimateValueLei} lei / lucrare — owner commercial policy (NOT Pricing Registry)
        </p>
        <p className="mt-1 text-[10px] text-slate-400">{FACE_CNC_MINIMUM_POLICY_DRAFT.notesRo}</p>
      </article>

      <article
        data-testid="product-system-face-estimate-inventory-cross-ref"
        className="rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-slate-200">Inventory / Pricing cross-reference (readonly)</p>
        <ul className="mt-2 space-y-2 text-[10px] text-slate-300">
          {FACE_INVENTORY_PRICING_CROSS_REFERENCES.map((ref) => (
            <li
              key={ref.key}
              data-testid={`product-system-face-estimate-cross-ref-${ref.key}`}
            >
              {ref.thicknessMm} mm: {ref.pricingKey ?? "—"} · {ref.registryRoute} · draft ≠ registry authority
              <span className="mt-0.5 block text-slate-500">{ref.notesRo}</span>
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
}
