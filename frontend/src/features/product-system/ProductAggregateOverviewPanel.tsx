import type { ProductAggregate, ProductAggregateComponent, ProductAggregateConflict } from "@/api/productAggregate";
import {
  hasParentComponentsEmptyWarning,
  PROVENANCE_LABELS,
  provenanceBadgeClass,
} from "@/features/product-system/productAggregateDisplay";
import { ProductCompilerDisplayShell } from "@/features/product-system/ProductCompilerDisplayShell";
import { PRODUCT_COMPILER_GRAPH_STAGE_LABEL } from "@/features/product-system/productTemplateModulesVocabulary";
import { AlertTriangle, Layers, Link2, Package, Cog } from "lucide-react";

function ConflictList({
  title,
  items,
}: {
  title: string;
  items: ProductAggregateConflict[];
}) {
  if (!items.length) return null;
  return (
    <div className="space-y-1.5">
      <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{title}</p>
      {items.map((item) => (
        <div
          key={`${item.code}-${item.message}`}
          className={`rounded-lg border px-3 py-2 text-[11px] ${
            item.severity === "error"
              ? "border-red-700/40 bg-red-900/15 text-red-200"
              : item.severity === "warning"
                ? "border-amber-700/40 bg-amber-900/15 text-amber-200"
                : "border-slate-700/40 bg-slate-900/30 text-slate-300"
          }`}
          data-testid={`aggregate-${title.toLowerCase()}-${item.code}`}
        >
          <span className="font-mono font-bold">{item.code}</span>
          <span className="mx-1.5 text-slate-500">·</span>
          {item.message}
        </div>
      ))}
    </div>
  );
}

function ProvenanceBadge({ provenance }: { provenance: string }) {
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded border text-[9px] font-bold uppercase tracking-wide ${provenanceBadgeClass(provenance)}`}
      data-testid={`provenance-${provenance}`}
    >
      {PROVENANCE_LABELS[provenance] ?? provenance}
    </span>
  );
}

function AggregateComponentRow({ component }: { component: ProductAggregateComponent }) {
  return (
    <div
      className="rounded-lg border border-[#1E293B] bg-[#0D1321]/80 px-3 py-2.5"
      data-testid={`aggregate-component-${component.component_id}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[12px] font-semibold text-slate-100 truncate">
            {component.label_ro || component.component_id}
          </p>
          <p className="text-[10px] font-mono text-slate-500 truncate">{component.component_id}</p>
          {component.role ? (
            <p className="text-[10px] text-slate-400 mt-0.5">{component.role}</p>
          ) : null}
          {component.mini_module_code ? (
            <p className="text-[10px] text-purple-300/80 mt-0.5">modul: {component.mini_module_code}</p>
          ) : null}
        </div>
        <ProvenanceBadge provenance={component.provenance} />
      </div>
    </div>
  );
}

export function ProductAggregateOverviewPanel({
  aggregate,
  fallbackMessage,
  showLegacyFallbackNote = false,
}: {
  aggregate?: ProductAggregate | null;
  fallbackMessage?: string | null;
  showLegacyFallbackNote?: boolean;
}) {
  if (fallbackMessage) {
    return (
      <div
        className="rounded-xl border border-amber-700/40 bg-amber-900/15 px-4 py-3 text-[11px] text-amber-200"
        data-testid="product-aggregate-fallback-banner"
      >
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-bold">{fallbackMessage}</p>
            {showLegacyFallbackNote ? (
              <p className="text-[10px] text-amber-300/80 mt-1">
                Legacy parser may still synthesize comp_auto_1 for edit compatibility — not authoritative.
              </p>
            ) : null}
          </div>
        </div>
      </div>
    );
  }

  if (!aggregate) {
    return null;
  }

  const parentCounts = aggregate.provenance_summary?.parent ?? {};
  const dossierCounts = aggregate.provenance_summary?.dossier ?? {};
  const linkedCounts = aggregate.provenance_summary?.linked_modules ?? {};
  const showParentEmptyMessage = hasParentComponentsEmptyWarning(aggregate);

  return (
    <div className="space-y-4" data-testid="product-aggregate-overview">
      <ProductCompilerDisplayShell stage="graph" compact />
      <div className="rounded-xl border border-purple-700/30 bg-purple-900/10 px-4 py-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-wide font-bold text-purple-300/90">
              {PRODUCT_COMPILER_GRAPH_STAGE_LABEL}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Output tehnic derivat (read model intern: ProductAggregate)
            </p>
            <p className="text-[13px] font-bold text-slate-100 mt-0.5">
              {aggregate.business_name_ro || aggregate.template_code}
            </p>
            <p className="text-[10px] font-mono text-slate-500">{aggregate.template_code}</p>
          </div>
          <span className="text-[9px] font-mono text-slate-500">v{aggregate.aggregate_version}</span>
        </div>

        {showParentEmptyMessage ? (
          <p
            className="mt-3 text-[11px] text-amber-200 bg-amber-900/20 border border-amber-700/30 rounded-lg px-3 py-2"
            data-testid="aggregate-parent-empty-message"
          >
            Parent template has no direct components. Showing Product Compiler graph from dossier and linked Module
            produs.
          </p>
        ) : null}

        <div className="grid grid-cols-3 gap-2 mt-3 text-[10px]">
          <div className="rounded-lg bg-[#0D1321]/60 border border-[#1E293B] px-2 py-1.5">
            <span className="text-slate-500 block">Parent</span>
            <span className="font-mono text-slate-300">
              C:{parentCounts.components ?? 0} O:{parentCounts.operations ?? 0} M:{parentCounts.materials ?? 0}
            </span>
          </div>
          <div className="rounded-lg bg-[#0D1321]/60 border border-[#1E293B] px-2 py-1.5">
            <span className="text-slate-500 block">Dossier</span>
            <span className="font-mono text-slate-300">
              C:{dossierCounts.components ?? 0} keys O:{dossierCounts.operation_keys ?? 0}
            </span>
          </div>
          <div className="rounded-lg bg-[#0D1321]/60 border border-[#1E293B] px-2 py-1.5">
            <span className="text-slate-500 block">Modules</span>
            <span className="font-mono text-slate-300">
              req:{linkedCounts.required ?? 0} opt:{linkedCounts.optional ?? 0}
            </span>
          </div>
        </div>
      </div>

      <ConflictList title="Conflicts" items={aggregate.conflicts} />
      <ConflictList title="Warnings" items={aggregate.warnings} />

      <div>
        <div className="flex items-center gap-2 mb-2">
          <Layers className="w-4 h-4 text-emerald-400" />
            <h4 className="text-[11px] font-bold text-slate-200 uppercase tracking-wide">
            Module / componente în Compiler ({aggregate.components.length})
          </h4>
        </div>
        <div className="space-y-2">
          {aggregate.components.map((component) => (
            <AggregateComponentRow key={component.component_id} component={component} />
          ))}
        </div>
      </div>

      {(aggregate.modules.required.length > 0 || aggregate.modules.optional.length > 0) && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Link2 className="w-4 h-4 text-blue-400" />
            <h4 className="text-[11px] font-bold text-slate-200 uppercase tracking-wide">Linked Module produs</h4>
          </div>
          <div className="space-y-2">
            {aggregate.modules.required.map((mod) => (
              <div
                key={`req-${mod.child_template_code}`}
                className="rounded-lg border border-blue-700/30 bg-blue-900/10 px-3 py-2"
                data-testid={`aggregate-module-required-${mod.child_template_code}`}
              >
                <p className="text-[10px] font-bold text-blue-300 uppercase">Required</p>
                <p className="text-[12px] font-mono text-slate-100">{mod.child_template_code}</p>
                <p className="text-[10px] text-slate-500">{mod.module_code}</p>
              </div>
            ))}
            {aggregate.modules.optional.map((mod) => (
              <div
                key={`opt-${mod.child_template_code}`}
                className="rounded-lg border border-slate-700/40 bg-slate-900/20 px-3 py-2"
                data-testid={`aggregate-module-optional-${mod.child_template_code}`}
              >
                <p className="text-[10px] font-bold text-slate-400 uppercase">Optional</p>
                <p className="text-[12px] font-mono text-slate-100">{mod.child_template_code}</p>
                <p className="text-[10px] text-slate-500">{mod.module_code}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Package className="w-3.5 h-3.5 text-slate-400" />
            <h4 className="text-[10px] font-bold text-slate-400 uppercase">Materiale ({aggregate.materials.length})</h4>
          </div>
          <div className="max-h-32 overflow-y-auto space-y-1 text-[10px] font-mono text-slate-400">
            {aggregate.materials.slice(0, 12).map((mat) => (
              <div key={`${mat.material_code}-${mat.provenance}-${mat.source_template_code}`} className="flex items-center justify-between gap-2">
                <span className="truncate">{mat.material_code}</span>
                <ProvenanceBadge provenance={mat.provenance} />
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Cog className="w-3.5 h-3.5 text-slate-400" />
            <h4 className="text-[10px] font-bold text-slate-400 uppercase">Operații ({aggregate.operations.length})</h4>
          </div>
          <div className="max-h-32 overflow-y-auto space-y-1 text-[10px] font-mono text-slate-400">
            {aggregate.operations.slice(0, 12).map((op) => (
              <div key={`${op.operation_code}-${op.provenance}-${op.source_template_code}`} className="flex items-center justify-between gap-2">
                <span className="truncate">{op.operation_code}</span>
                <ProvenanceBadge provenance={op.provenance} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function ProductAggregateStructureList({
  aggregate,
}: {
  aggregate: ProductAggregate;
}) {
  return (
    <div className="space-y-2" data-testid="product-aggregate-structure-list">
      {aggregate.components.map((component) => (
        <AggregateComponentRow key={component.component_id} component={component} />
      ))}
    </div>
  );
}
