import {
  buildFinishEstimateDraftSummary,
  FINISH_DRAFT_EXCLUDED_KEYS,
  FINISH_ESTIMATE_CALCULATION_RULES,
  FINISH_ESTIMATE_DRAFT_AUTHORITY,
  FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES,
  FINISH_LEGACY_RUNTIME_EVIDENCE,
  FINISH_OWNER_PRICE_VALUES_DECISION,
  type FinishEstimateDraftEntry,
  type FinishDraftValueStatus,
} from "./componentFirstFinishEstimatedPriceDraft";

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
        : tone === "emerald"
          ? "border-emerald-800/40 bg-emerald-950/25 text-emerald-200"
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

function draftStatusTone(status: FinishDraftValueStatus) {
  if (status === "evidence_only" || status === "owner_confirmed_quantity_basis") return "cyan" as const;
  if (status === "source_inventory_audit_required" || status === "owner_price_required") return "amber" as const;
  if (status === "not_applicable") return "slate" as const;
  return "rose" as const;
}

function draftStatusLabel(status: FinishDraftValueStatus) {
  return status.replace(/_/g, " ").toUpperCase();
}

function DraftRow({ entry }: { entry: FinishEstimateDraftEntry }) {
  const evidenceKeys = [
    ...entry.materialEvidenceKeys,
    ...entry.laborEvidenceKeys,
    ...entry.serviceEvidenceKeys,
  ].join(" · ");

  return (
    <tr data-testid={`product-system-finish-estimate-draft-row-${entry.key}`}>
      <td className="px-2 py-2 align-top text-[10px] text-slate-300">{entry.labelRo}</td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">{entry.surfaceTarget}</td>
      <td className="px-2 py-2 align-top font-mono text-[9px] text-cyan-200/80">{entry.quantityBasis}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip
          label={draftStatusLabel(entry.draftValueStatus)}
          tone={draftStatusTone(entry.draftValueStatus)}
          testId={`product-system-finish-estimate-draft-status-${entry.key}`}
        />
      </td>
      <td
        data-testid={`product-system-finish-estimate-draft-value-${entry.key}`}
        className="px-2 py-2 align-top text-[10px] font-semibold text-slate-200"
      >
        {entry.displayValueRo}
      </td>
      <td className="px-2 py-2 align-top font-mono text-[9px] text-slate-500">{evidenceKeys || "—"}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip label="BLOCKED" tone="slate" testId={`product-system-finish-estimate-active-${entry.key}`} />
      </td>
    </tr>
  );
}

export function FinishEstimatedPriceDraftPanel() {
  const summary = buildFinishEstimateDraftSummary();

  return (
    <section
      data-testid="product-system-finish-estimate-draft-panel"
      className="space-y-4 rounded-xl border border-pink-900/40 bg-pink-950/10 px-4 py-4"
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-sm font-semibold text-pink-100">
            FINISH Estimated Price Draft — readonly / inactive
          </h4>
          <StatusChip
            label={FINISH_ESTIMATE_DRAFT_AUTHORITY.label.replace(/_/g, " ")}
            tone="cyan"
            testId="product-system-finish-estimate-draft-authority-badge"
          />
          <StatusChip
            label="NOT PRICING REGISTRY"
            tone="slate"
            testId="product-system-finish-estimate-not-registry-badge"
          />
          <StatusChip
            label="OWNER PRICE VALUES APPLIED"
            tone="emerald"
            testId="product-system-finish-estimate-owner-price-values-badge"
          />
        </div>
        <p className="mt-1 text-[10px] text-slate-500">
          {FINISH_OWNER_PRICE_VALUES_DECISION.signedDoc} — seeds evidence_only, activation blocked
        </p>
      </div>

      <div
        data-testid="product-system-finish-estimate-draft-safety"
        className="rounded-lg border border-slate-800/80 bg-slate-950/50 px-3 py-2 text-[10px] text-slate-400"
      >
        <p>Not Pricing Registry authority</p>
        <p>Not active pricing</p>
        <p>No Product Truth live write</p>
        <p>No ProductDefinition bridge</p>
        <p>No Pricing activation</p>
        <p data-testid="product-system-finish-estimate-ready-for-pricing">Ready for pricing: NO</p>
        <p data-testid="product-system-finish-estimate-pricing-active-count">
          Pricing active rows: {summary.pricingActiveCount}
        </p>
        <p data-testid="product-system-finish-estimate-product-definition-bridge">
          ProductDefinition bridge: NO
        </p>
      </div>

      <article
        data-testid="product-system-finish-estimate-calculation-rules"
        className="rounded-lg border border-cyan-900/30 bg-cyan-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-cyan-200">Reguli calcul estimativ (readonly)</p>
        <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
          {FINISH_ESTIMATE_CALCULATION_RULES.map((rule) => (
            <li key={rule}>• {rule}</li>
          ))}
        </ul>
      </article>

      <article
        data-testid="product-system-finish-estimate-labor-evidence"
        className="rounded-lg border border-amber-900/30 bg-amber-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-amber-200">Labor evidence — owner decision</p>
        <ul className="mt-2 space-y-2 text-[10px] text-slate-300">
          <li data-testid="product-system-finish-estimate-face-labor-key">
            <span className="font-mono text-cyan-200/80">FACE_VINYL_APPLICATION_LABOR</span>
            {" · evidence_only · FINISH draft authority (face + artwork)"}
          </li>
          <li data-testid="product-system-finish-estimate-legacy-wc-labor">
            <span className="font-mono text-amber-200/80">{FINISH_LEGACY_RUNTIME_EVIDENCE.key}</span>
            {" · legacy_runtime_evidence · Intake V4 artwork path only"}
          </li>
        </ul>
      </article>

      <article data-testid="product-system-finish-estimate-draft-table">
        <p className="text-[11px] font-bold uppercase text-slate-200">Draft rows — evidence / audit</p>
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-800 text-[10px] font-bold uppercase text-slate-500">
                <th className="px-2 py-2">Variant / group</th>
                <th className="px-2 py-2">Surface</th>
                <th className="px-2 py-2">Qty basis</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Evidence values</th>
                <th className="px-2 py-2">Keys</th>
                <th className="px-2 py-2">Active</th>
              </tr>
            </thead>
            <tbody>
              {FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES.map((entry) => (
                <DraftRow key={entry.key} entry={entry} />
              ))}
            </tbody>
          </table>
        </div>
      </article>

      <article
        data-testid="product-system-finish-estimate-excluded-keys"
        className="rounded-lg border border-rose-900/30 bg-rose-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-rose-200">Excluded from FINISH draft</p>
        <ul className="mt-2 space-y-2 text-[10px] text-slate-300">
          {FINISH_DRAFT_EXCLUDED_KEYS.map((ref) => (
            <li
              key={ref.key}
              data-testid={`product-system-finish-estimate-excluded-${ref.key}`}
            >
              <span className="font-mono text-rose-200/80">{ref.pricingKey}</span>
              {" · "}
              {ref.ownerComponent} — {ref.notesRo}
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
}
