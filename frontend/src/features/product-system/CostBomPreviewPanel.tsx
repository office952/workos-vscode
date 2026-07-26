import { AlertTriangle, Calculator, Eye, Layers, ShieldAlert } from "lucide-react";
import type { CostBomPreview } from "@/api/costBomPreview";
import {
  deriveAggregateCostSource,
  deriveCostPreviewSource,
  deriveParityStatus,
  isVolumetricAggregateTemplate,
} from "@/api/costBomPreview";
import { useCostBomPreviewData } from "@/features/product-system/useCostBomPreviewData";

function bomStatusClass(status: string): string {
  switch (status) {
    case "ready":
      return "bg-emerald-900/20 text-emerald-300 border-emerald-700/40";
    case "blocked":
      return "bg-red-900/20 text-red-300 border-red-700/40";
    default:
      return "bg-amber-900/20 text-amber-300 border-amber-700/40";
  }
}

function parityClass(status: string): string {
  switch (status) {
    case "aligned":
      return "text-emerald-300";
    case "blocked":
      return "text-red-300";
    default:
      return "text-amber-300";
  }
}

function CostPreviewTruthBanner({ preview }: { preview: CostBomPreview }) {
  const source = deriveCostPreviewSource(preview.template_code);
  const aggregateSource = deriveAggregateCostSource(preview);
  const parity = deriveParityStatus(preview);

  return (
    <div
      className="flex items-start gap-2 rounded-lg border border-violet-800/40 bg-violet-900/15 px-3 py-2.5 text-[11px] text-violet-100"
      data-testid="cost-bom-read-only-banner"
    >
      <Eye className="w-4 h-4 shrink-0 mt-0.5" />
      <div className="space-y-1">
        <p className="font-semibold">Cost preview read-only (Step 7D)</p>
        <p className="text-violet-200/80">
          Nu este quote priced · nu creează comandă · nu creează taskuri · fără salvare DB · fără reprice automat
        </p>
        <p className="font-mono text-[10px] text-violet-300/90" data-testid="cost-bom-source-line">
          source: {source} · aggregate_cost_source: {aggregateSource ? "true" : "false"} · parity_status:{" "}
          <span className={parityClass(parity)}>{parity}</span>
        </p>
        {isVolumetricAggregateTemplate(preview.template_code) ? (
          <p className="text-[10px] text-violet-300/80" data-testid="cost-bom-reprice-guard">
            quote_reprice_allowed: false · requires_owner_approval: true (inclusiv quote 4)
          </p>
        ) : null}
      </div>
    </div>
  );
}

function ActiveModulesSummary({ preview }: { preview: CostBomPreview }) {
  const active = preview.active_modules.filter((m) => m.included_in_cost_bom);
  return (
    <div className="space-y-2" data-testid="cost-bom-active-modules">
      <div className="flex items-center gap-2">
        <Layers className="w-4 h-4 text-sky-400" />
        <h4 className="text-[13px] font-bold text-wo-text-primary">Active modules (cost BOM)</h4>
      </div>
      <div className="space-y-1">
        {active.map((mod) => (
          <div
            key={mod.module_code}
            className="rounded-lg border border-wo-border-subtle bg-wo-surface-inset px-3 py-1.5 text-[10px] text-wo-text-secondary font-mono"
          >
            {mod.module_code}
            <span className="text-wo-text-muted"> · </span>
            <span className="text-emerald-300">{mod.state}</span>
          </div>
        ))}
        {active.length === 0 ? (
          <p className="text-[10px] text-wo-text-muted">Niciun modul activ în cost BOM.</p>
        ) : null}
      </div>
    </div>
  );
}

function BlockersSection({ preview }: { preview: CostBomPreview }) {
  const hasBlockers =
    preview.pricing_blockers.length > 0 ||
    preview.missing_pricing.length > 0 ||
    preview.missing_geometry.length > 0 ||
    preview.missing_inventory_materials.length > 0;

  if (!hasBlockers) {
    return (
      <div className="rounded-lg border border-emerald-700/30 bg-emerald-900/10 px-3 py-2 text-[11px] text-emerald-200">
        Fără blockers critice de pricing/geometry/inventory în acest preview.
      </div>
    );
  }

  return (
    <div className="space-y-2" data-testid="cost-bom-blockers">
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-400" />
        <h4 className="text-[13px] font-bold text-wo-text-primary">Blockers & missing data</h4>
      </div>
      {preview.pricing_blockers.map((b) => (
        <div
          key={`${b.blocker_code}:${b.code}`}
          className="rounded border border-red-700/30 bg-red-900/10 px-2 py-1 text-[10px] text-red-200 font-mono"
        >
          {b.blocker_code} · {b.code} — {b.reason}
        </div>
      ))}
      {preview.missing_pricing.map((m) => (
        <div
          key={`mp:${m.code}:${m.reason}`}
          className="rounded border border-amber-700/30 bg-amber-900/10 px-2 py-1 text-[10px] text-amber-200 font-mono"
        >
          missing_pricing · {m.code} — {m.reason}
        </div>
      ))}
      {preview.missing_geometry.map((g) => (
        <div
          key={`mg:${g}`}
          className="rounded border border-amber-700/30 bg-amber-900/10 px-2 py-1 text-[10px] text-amber-200 font-mono"
        >
          missing_geometry · {g}
        </div>
      ))}
      {preview.missing_inventory_materials.map((code) => (
        <div
          key={`mi:${code}`}
          className="rounded border border-amber-700/30 bg-amber-900/10 px-2 py-1 text-[10px] text-amber-200 font-mono"
        >
          missing_inventory · {code}
        </div>
      ))}
    </div>
  );
}

function ExternalizationMetadata({ preview }: { preview: CostBomPreview }) {
  const futureHooks = preview.externalization_requirements.filter((r) => !r.selected_now);
  if (futureHooks.length === 0 && preview.reseller_requirements.length === 0) return null;

  return (
    <div className="space-y-2" data-testid="cost-bom-externalization-metadata">
      <p className="text-[10px] font-bold uppercase text-wo-text-muted">HUB boundary (metadata only)</p>
      <p className="text-[10px] text-wo-text-muted">
        Hooks viitor — nu activează WorkOS externalizare, furnizori, taskuri externe sau reseller pricing.
      </p>
      {futureHooks.slice(0, 4).map((hook) => (
        <div key={hook.code} className="text-[10px] text-wo-text-muted font-mono">
          {hook.code} · {hook.production_mode} · selected_now=false
        </div>
      ))}
    </div>
  );
}

function SkippedSummary({ preview }: { preview: CostBomPreview }) {
  if (!preview.skipped_items.length) return null;
  const summary = preview.skipped_items.slice(0, 6);
  return (
    <details className="rounded-lg border border-wo-border-subtle bg-wo-surface-inset">
      <summary className="cursor-pointer px-3 py-2 text-[11px] font-semibold text-wo-text-secondary">
        Skipped items ({preview.skipped_items.length})
      </summary>
      <ul className="px-3 pb-3 space-y-1 text-[10px] text-wo-text-muted font-mono">
        {summary.map((item) => (
          <li key={`${item.item_type}:${item.item_key}`}>
            {item.item_type}/{item.item_key} — {item.reason}
          </li>
        ))}
      </ul>
    </details>
  );
}

export function CostBomPreviewPanel({ templateCode }: { templateCode: string }) {
  const { preview, status, error, isLoading } = useCostBomPreviewData(templateCode);

  if (isLoading) {
    return <div className="text-[11px] text-wo-text-muted">Se încarcă Cost BOM preview…</div>;
  }

  if (status === "unavailable" || !preview) {
    return (
      <div className="space-y-3" data-testid="cost-bom-preview-panel">
        <div className="rounded-lg border border-amber-700/40 bg-amber-900/10 px-3 py-2 text-[11px] text-amber-200">
          <AlertTriangle className="w-4 h-4 inline mr-1.5" />
          {error ?? "Cost BOM preview indisponibil."}
        </div>
      </div>
    );
  }

  const activeModuleCount = preview.active_modules.filter((m) => m.included_in_cost_bom).length;

  return (
    <div className="space-y-4 border-t border-wo-border-subtle pt-4 mt-4" data-testid="cost-bom-preview-panel">
      <div className="flex items-center gap-2">
        <Calculator className="w-4 h-4 text-violet-400" />
        <h3 className="text-[14px] font-bold text-wo-text-primary">Cost BOM / Pricing readiness</h3>
        <span
          className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${bomStatusClass(preview.bom_status)}`}
          data-testid="cost-bom-status"
        >
          {preview.bom_status}
        </span>
      </div>

      <CostPreviewTruthBanner preview={preview} />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]" data-testid="cost-bom-counts">
        <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2">
          <p className="text-[9px] uppercase text-wo-text-muted font-bold">Modules active</p>
          <p className="text-[14px] font-bold text-wo-text-primary">{activeModuleCount}</p>
        </div>
        <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2">
          <p className="text-[9px] uppercase text-wo-text-muted font-bold">Costable materials</p>
          <p className="text-[14px] font-bold text-wo-text-primary">{preview.costable_materials.length}</p>
        </div>
        <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2">
          <p className="text-[9px] uppercase text-wo-text-muted font-bold">Costable operations</p>
          <p className="text-[14px] font-bold text-wo-text-primary">{preview.costable_operations.length}</p>
        </div>
        <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2">
          <p className="text-[9px] uppercase text-wo-text-muted font-bold">Missing pricing</p>
          <p className="text-[14px] font-bold text-amber-300">{preview.missing_pricing.length}</p>
        </div>
      </div>

      <ActiveModulesSummary preview={preview} />
      <BlockersSection preview={preview} />
      <ExternalizationMetadata preview={preview} />
      <SkippedSummary preview={preview} />

      {preview.warnings.length > 0 ? (
        <div className="space-y-1">
          <p className="text-[10px] font-bold uppercase text-wo-text-muted">Warnings</p>
          {preview.warnings.slice(0, 5).map((w) => (
            <div key={w} className="text-[10px] text-amber-200 rounded border border-amber-700/20 px-2 py-1">
              {w}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
