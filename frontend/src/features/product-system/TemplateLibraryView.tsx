import { Search, Package, ChevronRight, Star, SquarePen, Eye } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { StatusBadge } from "@/components/workos/design-system";
import type { ProductTemplateEntity } from "@/lib/api";
import { isActiveTemplateForQuote } from "@/lib/activeTemplateScope";
import {
  filterLibraryTemplates,
  formatTemplateListDate,
  type LibraryTab,
} from "@/features/product-system/productSystemNavigation";

export interface TemplateLibraryRowSummary {
  components: number;
  operations: number;
  materials: number;
  validationPassed: number;
  validationTotal: number;
  aggregateCounts?: { components: number; operations: number; materials: number } | null;
  showDualCounts?: boolean;
  parentDirectCounts?: { components: number; operations: number; materials: number };
}

function TemplateLibraryRow({
  template,
  summary,
  recommended,
  onOpen,
}: {
  template: ProductTemplateEntity;
  summary: TemplateLibraryRowSummary;
  recommended: boolean;
  onOpen: () => void;
}) {
  const quoteActive = isActiveTemplateForQuote(template);
  const updated = formatTemplateListDate(template.updated_at);
  const created = formatTemplateListDate(template.created_at);
  const metricsLine = summary.showDualCounts && summary.aggregateCounts && summary.parentDirectCounts
    ? [
        quoteActive ? "Activ" : "Arhivat",
        `Parent direct: ${summary.parentDirectCounts.components}/${summary.parentDirectCounts.operations}/${summary.parentDirectCounts.materials}`,
        `Aggregate: ${summary.aggregateCounts.components}/${summary.aggregateCounts.operations}/${summary.aggregateCounts.materials}`,
        `Validare ${summary.validationPassed}/${summary.validationTotal}`,
      ].join(" · ")
    : [
        quoteActive ? "Activ" : "Arhivat",
        `${summary.components} componente`,
        `${summary.operations} operații`,
        `${summary.materials} materiale`,
        `Validare ${summary.validationPassed}/${summary.validationTotal}`,
      ].join(" · ");

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onOpen();
        }
      }}
      className={`bg-[#111827] border rounded-lg p-4 cursor-pointer transition-all group ${
        quoteActive
          ? "border-[#1E293B] hover:border-purple-600/40 hover:bg-[#131B2E]"
          : "border-slate-800/80 hover:border-slate-600/50 hover:bg-[#131B2E]/80 opacity-90"
      } ${recommended ? "ring-1 ring-purple-500/30 border-purple-500/40" : ""}`}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
              quoteActive ? "bg-purple-500/10" : "bg-slate-800/60"
            }`}
          >
            <Package
              className={`w-4 h-4 ${quoteActive ? "text-purple-400" : "text-slate-500"}`}
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[14px] font-mono font-bold text-slate-100 truncate">
                {template.template_code}
              </span>
              {recommended ? (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-semibold rounded bg-purple-900/30 text-purple-300 border border-purple-700/40">
                  <Star className="w-2.5 h-2.5" />
                  Recomandat
                </span>
              ) : null}
              <StatusBadge
                domain="productSystem"
                status={quoteActive ? "active" : "archived"}
                label={quoteActive ? "Activ" : "Arhivat"}
                className="text-[9px] uppercase"
              />
            </div>
            <p className="text-[12px] text-slate-400 truncate mt-0.5">
              {template.family_name || "—"}
            </p>
            <p className="text-[11px] text-slate-500 mt-1">{metricsLine}</p>
            {(updated || created) && (
              <p className="text-[10px] text-slate-600 mt-1">
                {updated ? `Actualizat: ${updated}` : null}
                {updated && created ? " · " : null}
                {created ? `Creat: ${created}` : null}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Tooltip>
            <TooltipTrigger asChild>
              <span
                aria-label={quoteActive ? "Deschide editor" : "Vezi arhivă"}
                className={`w-8 h-8 rounded-md flex items-center justify-center border transition-colors ${
                  quoteActive
                    ? "bg-purple-500/10 border-purple-500/25 text-purple-300 group-hover:bg-purple-500/20 group-hover:border-purple-500/40"
                    : "bg-slate-800/50 border-slate-700/60 text-slate-400 group-hover:bg-slate-800 group-hover:text-slate-300"
                }`}
              >
                {quoteActive ? (
                  <SquarePen className="w-3.5 h-3.5" />
                ) : (
                  <Eye className="w-3.5 h-3.5" />
                )}
              </span>
            </TooltipTrigger>
            <TooltipContent side="left" className="text-[11px]">
              {quoteActive ? "Deschide editor" : "Vezi arhivă"}
            </TooltipContent>
          </Tooltip>
          <ChevronRight
            className={`w-4 h-4 transition-transform group-hover:translate-x-0.5 ${
              quoteActive ? "text-purple-400" : "text-slate-600"
            }`}
          />
        </div>
      </div>
    </div>
  );
}

export function TemplateLibraryView({
  templates,
  tab,
  onTabChange,
  search,
  onSearchChange,
  summaries,
  recommendedTemplateId,
  activeCount,
  archivedCount,
  loading,
  onOpenTemplate,
}: {
  templates: ProductTemplateEntity[];
  tab: LibraryTab;
  onTabChange: (tab: LibraryTab) => void;
  search: string;
  onSearchChange: (value: string) => void;
  summaries: Map<number, TemplateLibraryRowSummary>;
  recommendedTemplateId: number | null;
  activeCount: number;
  archivedCount: number;
  loading: boolean;
  onOpenTemplate: (template: ProductTemplateEntity) => void;
}) {
  const filtered = filterLibraryTemplates(templates, tab, search);

  const tabs: { id: LibraryTab; label: string; count: number }[] = [
    { id: "active", label: "Active", count: activeCount },
    { id: "archived", label: "Arhivate", count: archivedCount },
    { id: "all", label: "Toate", count: templates.length },
  ];

  const emptyFallback =
    tab === "active"
      ? "Nu există șabloane active pentru ofertă."
      : tab === "archived"
        ? "Nu există șabloane arhivate."
        : "Nu există șabloane în registru.";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onTabChange(t.id)}
            className={`px-3 py-1.5 rounded-lg text-[11px] font-bold border transition-colors ${
              tab === t.id
                ? t.id === "archived"
                  ? "bg-amber-900/25 text-amber-300 border-amber-700/50"
                  : "bg-emerald-900/25 text-emerald-300 border-emerald-700/50"
                : "bg-slate-800/40 text-slate-500 border-slate-700 hover:text-slate-300"
            }`}
          >
            {t.label} ({t.count})
          </button>
        ))}
      </div>

      {tab === "archived" ? (
        <p className="text-[11px] text-amber-400/90 px-0.5">
          Șabloane arhivate — nu sunt active pentru ofertă sau Pricing. Deschiderea este doar pentru
          consultare.
        </p>
      ) : null}

      <div className="flex items-center gap-2 bg-[#111827] rounded-lg px-3 py-2 border border-[#1E293B] w-full max-w-lg">
        <Search className="w-4 h-4 text-slate-500 shrink-0" />
        <input
          type="text"
          placeholder="Caută cod șablon, familie…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
        />
      </div>

      {loading ? (
        <div className="text-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-2" />
          <p className="text-[12px] text-slate-500">Se încarcă șabloanele…</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-slate-500 text-[13px]">
          {search.trim() ? "Niciun șablon pentru căutarea curentă." : emptyFallback}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((t) => {
            const summary = summaries.get(t.id) ?? {
              components: 0,
              operations: 0,
              materials: 0,
              validationPassed: 0,
              validationTotal: 6,
            };
            return (
              <TemplateLibraryRow
                key={t.id}
                template={t}
                summary={summary}
                recommended={recommendedTemplateId === t.id}
                onOpen={() => onOpenTemplate(t)}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
