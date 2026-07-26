/**
 * Pricing Registry V2 — spacious template-first layout.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Search,
  RefreshCw,
  AlertTriangle,
  Loader2,
  TrendingUp,
  Info,
  Pencil,
  Star,
  X,
  ChevronDown,
  ExternalLink,
  Settings2,
} from "lucide-react";
import type { PricingRegistryItem, PricingRegistryResponse } from "@/api/pricingRegistry";
import type { CommercialMarkupPolicy } from "@/api/commercialMarkupPoliciesAdmin";
import type { PriceHistoryEntryDTO } from "@/api/inventoryMaterialsAdmin";
import { MaterialMarketPriceRegistryPanel } from "@/features/pricing/MaterialMarketPriceRegistryPanel";
import {
  buildDetailPanelModel,
  buildProblemQueue,
  buildTemplateList,
  computeTemplateStats,
  filterTemplatesForPicker,
  formatProblemBanner,
  groupItemsForCoverageStack,
  itemsForTemplate,
  templateHumanLabel,
  type PricingMainView,
  type ProblemQueueEntry,
  type StatusSeverity,
  type TemplateListEntry,
} from "@/lib/pricingRegistry";
import { PricingEntryRow } from "./PricingEntryRow";
import { SourceBadge, PreviewOfficialBanner, CapacityNotice, BoundaryBadge } from "@/components/workos/design-system";
import { PRICING_VIEW_TAB_META } from "./pricingRegistryUi";
import {
  filterByTypedCatalogView,
  type TypedCatalogView,
} from "@/lib/pricing/pricingTypedCatalog";

function fmtCost(n: number | null | undefined, currency?: string | null): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "Lipsă";
  const formatted = n.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
  return currency ? `${formatted} ${currency}` : `${formatted}`;
}

function severityClass(sev: StatusSeverity): string {
  switch (sev) {
    case "ok":
      return "text-emerald-700 dark:text-emerald-400";
    case "warn":
      return "text-amber-700 dark:text-amber-400";
    case "bad":
      return "text-red-700 dark:text-red-400";
    default:
      return "text-muted-foreground";
  }
}

function readinessClass(readiness: string): string {
  switch (readiness) {
    case "available":
      return "text-emerald-700 dark:text-emerald-400";
    case "partial":
      return "text-amber-700 dark:text-amber-400";
    case "blocked":
      return "text-red-700 dark:text-red-400";
    default:
      return "text-muted-foreground";
  }
}

function technicalSourceLabel(source: string): string {
  switch (source) {
    case "inventory_materials":
      return "inventory_materials";
    case "workcenter_rates":
      return "workcenter_rates";
    case "commercial_markup_policies":
      return "commercial_markup_policies";
    default:
      return source;
  }
}

interface PricingRegistrySpaciousViewProps {
  registry: PricingRegistryResponse;
  policies: CommercialMarkupPolicy[];
  loading: boolean;
  error: string | null;
  source: "db" | "loading" | "error";
  selectedTemplate: string;
  recentTemplates: string[];
  favoriteTemplates: string[];
  mainView: PricingMainView;
  selectedItem: PricingRegistryItem | null;
  stackSearch: string;
  priceHistory: PriceHistoryEntryDTO[];
  loadingHistory: boolean;
  loadingRate: boolean;
  onRefresh: () => void;
  onSelectTemplate: (code: string) => void;
  onToggleFavoriteTemplate: (code: string) => void;
  onMainViewChange: (view: PricingMainView) => void;
  onSelectItem: (item: PricingRegistryItem) => void;
  onStackSearchChange: (q: string) => void;
  onEditMaterial: (item: PricingRegistryItem) => void;
  onEditRate: (item: PricingRegistryItem) => void;
  onOpenMarkupDrawer: () => void;
  onGoToProblem: (item: PricingRegistryItem) => void;
  baseCurrency?: string | null;
}

export function PricingRegistrySpaciousView({
  registry,
  policies,
  loading,
  error,
  source,
  selectedTemplate,
  recentTemplates,
  favoriteTemplates,
  mainView,
  selectedItem,
  stackSearch,
  priceHistory,
  loadingHistory,
  loadingRate,
  onRefresh,
  onSelectTemplate,
  onToggleFavoriteTemplate,
  onMainViewChange,
  onSelectItem,
  onStackSearchChange,
  onEditMaterial,
  onEditRate,
  onOpenMarkupDrawer,
  onGoToProblem,
  baseCurrency,
}: PricingRegistrySpaciousViewProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [typedCatalogView, setTypedCatalogView] = useState<TypedCatalogView>("all");
  const [pickerSearch, setPickerSearch] = useState("");
  const [pickerFamily, setPickerFamily] = useState("all");
  const pickerRef = useRef<HTMLDivElement>(null);

  const allTemplates = useMemo(
    () => buildTemplateList(registry.template_usage),
    [registry.template_usage]
  );

  const templateFamilies = useMemo(() => {
    const set = new Set(allTemplates.map((t) => t.family));
    return ["all", ...Array.from(set).sort()];
  }, [allTemplates]);

  const pickerTemplates = useMemo(
    () =>
      filterTemplatesForPicker(allTemplates, {
        search: pickerSearch,
        family: pickerFamily,
      }),
    [allTemplates, pickerSearch, pickerFamily]
  );

  const templateItems = useMemo(
    () => itemsForTemplate(registry.items, selectedTemplate),
    [registry.items, selectedTemplate]
  );

  const templateStats = useMemo(
    () => computeTemplateStats(templateItems),
    [templateItems]
  );

  const problemQueue = useMemo(
    () => buildProblemQueue(templateItems),
    [templateItems]
  );

  const problemBanner = formatProblemBanner(problemQueue);

  const filteredStackItems = useMemo(() => {
    const typed = filterByTypedCatalogView(templateItems, typedCatalogView);
    if (!stackSearch.trim()) return typed;
    const q = stackSearch.trim().toLowerCase();
    return typed.filter(
      (i) =>
        i.pricing_code.toLowerCase().includes(q) ||
        i.display_name.toLowerCase().includes(q) ||
        i.registry_category.toLowerCase().includes(q)
    );
  }, [templateItems, stackSearch, typedCatalogView]);

  const coverageSections = useMemo(
    () =>
      groupItemsForCoverageStack(
        filteredStackItems,
        mainView === "coverage" && typedCatalogView === "all"
          ? registry.markup_policies
          : [],
        { includeVerification: false }
      ),
    [filteredStackItems, registry.markup_policies, mainView, typedCatalogView]
  );

  const allEntriesFiltered = useMemo(() => {
    const typed = filterByTypedCatalogView(registry.items, typedCatalogView);
    if (!stackSearch.trim()) return typed;
    const q = stackSearch.trim().toLowerCase();
    return typed.filter(
      (i) =>
        i.pricing_code.toLowerCase().includes(q) ||
        i.display_name.toLowerCase().includes(q)
    );
  }, [registry.items, stackSearch, typedCatalogView]);

  const verifyItems = useMemo(() => {
    const base = filterByTypedCatalogView(registry.items, typedCatalogView).filter(
      (i) =>
        i.status === "missing_price" ||
        i.status === "needs_review" ||
        i.confidence === "estimated" ||
        i.confidence === "missing" ||
        (i.data_quality_flags ?? []).includes("rate_basis_column_mismatch")
    );
    if (!stackSearch.trim()) return base;
    const q = stackSearch.trim().toLowerCase();
    return base.filter(
      (i) =>
        i.pricing_code.toLowerCase().includes(q) ||
        i.display_name.toLowerCase().includes(q)
    );
  }, [registry.items, stackSearch, typedCatalogView]);

  useEffect(() => {
    if (!pickerOpen) return;
    const handler = (e: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        setPickerOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [pickerOpen]);

  const activePoliciesCount = policies.filter((p) => p.status === "active").length;

  const tabMeta = PRICING_VIEW_TAB_META[mainView];
  const verifyCount = buildProblemQueue(templateItems).length;

  return (
    <div className="flex flex-col min-h-0 space-y-2">
      {/* Stage Banner */}
      <PreviewOfficialBanner
        stage="internal"
        label="Registry intern de referință"
        detail="Material / Reguli comerciale / Cost intern / Capacitate / Analytics. Nu este hub unic de ofertare. Oferta oficială = Snapshot V2."
        compact={false}
      />
      <div className="flex flex-wrap items-center gap-2">
        <BoundaryBadge domain="pricing" label="Pricing Registry" />
        <CapacityNotice
          message="Efort intern / oră = capacitate — NU tarif client. Nu deblochează oferta."
          compact
        />
      </div>

      {/* Header — compact */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <TrendingUp className="w-5 h-5 text-blue-400 shrink-0" />
            <h1 className="text-[18px] font-bold text-foreground">Pricing Registry</h1>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Registry intern de referință — nu este fluxul operator Product Template → Structură produs → Product
              Compiler.
            </p>
            <SourceBadge
              source={source === "db" ? "db" : source === "loading" ? "loading" : "error"}
            />
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            <span className="text-muted-foreground">Pricing</span> = registry intern (materiale / utilaje / manoperă) ·{" "}
            <span className="text-muted-foreground">Inventory</span> = stoc și cost achiziție · Oferta client rămâne pe canal CPP
            {baseCurrency ? (
              <>
                {" "}
                · Monedă de bază (Settings):{" "}
                <span className="text-muted-foreground font-semibold">{baseCurrency}</span>
              </>
            ) : null}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={onOpenMarkupDrawer}
            className="inline-flex items-center gap-1.5 rounded border border-purple-200 bg-purple-50 px-2.5 py-1.5 text-[11px] font-medium text-purple-700 transition-colors hover:bg-purple-100 dark:border-purple-700/50 dark:bg-purple-900/30 dark:text-purple-300 dark:hover:bg-purple-900/50"
          >
            <Settings2 className="w-3 h-3" />
            Adaos
            <span className="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] text-purple-800 dark:bg-purple-800/50 dark:text-purple-200">
              {activePoliciesCount}
            </span>
          </button>
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded border border-border bg-wo-surface-raised px-2.5 py-1.5 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
            Actualizează
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 dark:border-red-800/40 dark:bg-red-900/20">
          <AlertTriangle className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
          <p className="text-[12px] text-red-800 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* View tabs */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {(Object.keys(PRICING_VIEW_TAB_META) as PricingMainView[]).map((key) => {
          const meta = PRICING_VIEW_TAB_META[key];
          const countBadge =
            key === "verify" && verifyCount > 0 ? (
              <span className="ml-1 rounded-full bg-amber-100 px-1.5 py-0.5 text-[9px] text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
                {verifyCount}
              </span>
            ) : null;
          return (
            <button
              key={key}
              type="button"
              onClick={() => onMainViewChange(key)}
              className={`px-3 py-1.5 text-[12px] font-medium rounded-full border transition-all ${
                mainView === key
                  ? "bg-blue-600/20 text-blue-300 border-blue-600/50"
                  : "bg-transparent text-muted-foreground border-wo-border-strong hover:border-slate-500 hover:text-muted-foreground"
              }`}
            >
              {meta.label}
              {countBadge}
            </button>
          );
        })}
      </div>

      {/* Typed catalog views — Pricing Foundation V1 */}
      {(mainView === "coverage" || mainView === "all" || mainView === "verify") && (
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground mr-1">Catalog:</span>
          {(
            [
              { key: "all" as const, label: "Toate tipurile" },
              { key: "material" as const, label: "Preturi materiale" },
              { key: "machine_operation" as const, label: "Operații utilaje" },
              { key: "labor_service" as const, label: "Manoperă și servicii" },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setTypedCatalogView(tab.key)}
              className={`px-2.5 py-1 text-[11px] font-medium rounded-md border transition-all ${
                typedCatalogView === tab.key
                  ? "bg-cyan-900/30 text-cyan-200 border-cyan-700/50"
                  : "bg-transparent text-muted-foreground border-wo-border-strong hover:border-slate-500 hover:text-muted-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {typedCatalogView === "material" &&
      (mainView === "coverage" || mainView === "all" || mainView === "verify") ? (
        <MaterialMarketPriceRegistryPanel />
      ) : null}

      {/* Template zone — coverage + verify share template context */}
      {(mainView === "coverage" || mainView === "verify") && (
        <TemplateZone
          selectedTemplate={selectedTemplate}
          recentTemplates={recentTemplates}
          templateStats={templateStats}
          allTemplates={allTemplates}
          pickerOpen={pickerOpen}
          pickerSearch={pickerSearch}
          pickerFamily={pickerFamily}
          pickerFamilies={templateFamilies}
          pickerTemplates={pickerTemplates}
          pickerRef={pickerRef}
          problemBanner={problemBanner}
          problemQueue={problemQueue}
          onOpenPicker={() => setPickerOpen(true)}
          onClosePicker={() => setPickerOpen(false)}
          onPickerSearchChange={setPickerSearch}
          onPickerFamilyChange={setPickerFamily}
          favoriteTemplates={favoriteTemplates}
          onSelectTemplate={(code) => {
            onSelectTemplate(code);
            setPickerOpen(false);
          }}
          onToggleFavoriteTemplate={onToggleFavoriteTemplate}
          onGoToProblem={onGoToProblem}
        />
      )}

      {/* Main workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-3 min-h-[480px]">
        <div className="flex flex-col min-h-0 bg-wo-surface-inset border border-border rounded-lg overflow-hidden">
          <div className="px-4 py-2.5 bg-card border-b border-border">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <h2 className="text-[13px] font-semibold text-foreground">{tabMeta.title}</h2>
              {mainView !== "audit" && (
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Caută cod, nume…"
                    value={stackSearch}
                    onChange={(e) => onStackSearchChange(e.target.value)}
                    className="pl-8 pr-3 py-1.5 text-[12px] bg-wo-surface-inset border border-wo-border-strong rounded-lg text-foreground w-[200px] focus:outline-none focus:border-blue-600/50"
                  />
                </div>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {mainView === "coverage" && (
              <CoverageStack
                sections={coverageSections}
                selectedItem={selectedItem}
                onSelectItem={onSelectItem}
                onEditMaterial={onEditMaterial}
                onEditRate={onEditRate}
                loadingRate={loadingRate}
              />
            )}
            {mainView === "all" && (
              <FlatEntryList
                items={allEntriesFiltered}
                selectedItem={selectedItem}
                onSelectItem={onSelectItem}
                onEditMaterial={onEditMaterial}
                onEditRate={onEditRate}
                loadingRate={loadingRate}
              />
            )}
            {mainView === "verify" && (
              <FlatEntryList
                items={verifyItems}
                selectedItem={selectedItem}
                onSelectItem={onSelectItem}
                onEditMaterial={onEditMaterial}
                onEditRate={onEditRate}
                loadingRate={loadingRate}
              />
            )}
            {mainView === "markup" && (
              <MarkupView policies={registry.markup_policies} onSelectItem={onSelectItem} selectedItem={selectedItem} />
            )}
            {mainView === "audit" && (
              <AuditPlaceholder selectedItem={selectedItem} priceHistory={priceHistory} loadingHistory={loadingHistory} />
            )}
          </div>
        </div>

        <div className="bg-wo-surface-inset border border-border rounded-lg overflow-hidden min-h-[320px] lg:min-h-0">
          <DetailPanel
            item={selectedItem}
            priceHistory={priceHistory}
            loadingHistory={loadingHistory}
            onEditMaterial={onEditMaterial}
            onEditRate={onEditRate}
            loadingRate={loadingRate}
            baseCurrency={baseCurrency}
          />
        </div>
      </div>
    </div>
  );
}

function TemplateZone({
  selectedTemplate,
  recentTemplates,
  favoriteTemplates,
  templateStats,
  allTemplates,
  pickerOpen,
  pickerSearch,
  pickerFamily,
  pickerFamilies,
  pickerTemplates,
  pickerRef,
  problemBanner,
  problemQueue,
  onOpenPicker,
  onClosePicker,
  onPickerSearchChange,
  onPickerFamilyChange,
  onSelectTemplate,
  onToggleFavoriteTemplate,
  onGoToProblem,
}: {
  selectedTemplate: string;
  recentTemplates: string[];
  favoriteTemplates: string[];
  templateStats: ReturnType<typeof computeTemplateStats>;
  allTemplates: TemplateListEntry[];
  pickerOpen: boolean;
  pickerSearch: string;
  pickerFamily: string;
  pickerFamilies: string[];
  pickerTemplates: TemplateListEntry[];
  pickerRef: React.RefObject<HTMLDivElement | null>;
  problemBanner: string | null;
  problemQueue: ProblemQueueEntry[];
  onOpenPicker: () => void;
  onClosePicker: () => void;
  onPickerSearchChange: (q: string) => void;
  onPickerFamilyChange: (f: string) => void;
  onSelectTemplate: (code: string) => void;
  onToggleFavoriteTemplate: (code: string) => void;
  onGoToProblem: (item: PricingRegistryItem) => void;
}) {
  const firstProblem = problemQueue[0]?.item;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between gap-3 flex-wrap px-3 py-2.5 bg-card border border-border rounded-lg">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-mono text-[12px] font-semibold text-blue-400">{selectedTemplate}</p>
            <span className={`text-[10px] font-semibold ${readinessClass(templateStats.readiness)}`}>
              {templateStats.readinessLabel}
            </span>
          </div>
          <p className="text-[12px] text-muted-foreground mt-0.5 truncate">{templateHumanLabel(selectedTemplate)}</p>
          <p className="text-[10px] text-muted-foreground mt-1">
            {templateStats.ownerConfirmed} confirmate ·{" "}
            <span className="text-amber-700 dark:text-amber-400">
              {templateStats.estimated + templateStats.needsReview} review
            </span>{" "}
            ·{" "}
            <span className="text-red-700 dark:text-red-400">
              {templateStats.missingPrice} lipsă
            </span>
          </p>
        </div>
        <button
          type="button"
          onClick={onOpenPicker}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg border border-wo-border-strong bg-wo-surface-inset text-foreground hover:border-blue-600/40 hover:text-blue-300 transition-colors whitespace-nowrap"
        >
          Schimbă template…
          <ChevronDown className="w-3.5 h-3.5" />
        </button>
      </div>

      {(favoriteTemplates.length > 0 || recentTemplates.length > 0) && (
        <div className="flex items-center gap-2 flex-wrap px-1">
          {favoriteTemplates.map((code) => (
            <button
              key={`fav-${code}`}
              type="button"
              onClick={() => onSelectTemplate(code)}
              title="Favorite"
              className={`px-2 py-0.5 rounded-full text-[10px] border transition-colors ${
                code === selectedTemplate
                  ? "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-700/40 dark:bg-amber-900/20 dark:text-amber-300"
                  : "border-wo-border-strong text-muted-foreground hover:text-amber-700 dark:hover:text-amber-300"
              }`}
            >
              ★ {code}
            </button>
          ))}
          {recentTemplates
            .filter((code) => !favoriteTemplates.includes(code))
            .map((code) => (
              <button
                key={code}
                type="button"
                onClick={() => onSelectTemplate(code)}
                title="Recent"
                className={`px-2 py-0.5 rounded-full text-[10px] border transition-colors ${
                  code === selectedTemplate
                    ? "text-blue-300 border-blue-700/40 bg-blue-900/25"
                    : "text-muted-foreground border-wo-border-strong hover:text-blue-300"
                }`}
              >
                {code}
              </button>
            ))}
        </div>
      )}

      {problemBanner && (
        <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-lg bg-red-900/15 border border-red-800/30 text-[12px] text-red-200">
          <span>{problemBanner}.</span>
          {firstProblem && (
            <button
              type="button"
              onClick={() => onGoToProblem(firstProblem)}
              className="text-blue-400 font-semibold hover:underline whitespace-nowrap"
            >
              Mergi la problemă
            </button>
          )}
        </div>
      )}

      {pickerOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-6 bg-black/55">
          <div
            ref={pickerRef}
            className="w-full max-w-lg max-h-[70vh] flex flex-col bg-wo-surface-inset border border-border rounded-xl shadow-2xl overflow-hidden"
          >
            <div className="px-4 py-3 border-b border-border">
              <div className="flex items-center justify-between">
                <h3 className="text-[14px] font-semibold text-foreground">Selectează template</h3>
                <button type="button" onClick={onClosePicker} className="p-1 rounded hover:bg-muted">
                  <X className="w-4 h-4 text-muted-foreground" />
                </button>
              </div>
              <input
                type="text"
                placeholder="Caută template_code, nume, familie…"
                value={pickerSearch}
                onChange={(e) => onPickerSearchChange(e.target.value)}
                className="w-full mt-2 px-3 py-2 text-[13px] bg-card border border-wo-border-strong rounded-lg text-foreground focus:outline-none focus:border-blue-600/50"
                autoFocus
              />
            </div>
            <div className="flex gap-2 flex-wrap px-4 py-2 border-b border-border items-center">
              <select
                value={pickerFamily}
                onChange={(e) => onPickerFamilyChange(e.target.value)}
                className="px-2 py-1 text-[11px] bg-card border border-wo-border-strong rounded text-muted-foreground"
              >
                {pickerFamilies.map((f) => (
                  <option key={f} value={f}>
                    {f === "all" ? "Toate familiile" : f}
                  </option>
                ))}
              </select>
              <span className="text-[10px] text-muted-foreground ml-auto">
                {allTemplates.length} template-uri active
              </span>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {pickerTemplates.length === 0 ? (
                <p className="text-center text-[12px] text-muted-foreground py-8">Niciun template găsit.</p>
              ) : (
                pickerTemplates.map((t) => {
                  const isFav = favoriteTemplates.includes(t.template_code);
                  return (
                    <div
                      key={t.template_code}
                      className={`flex items-start gap-1 rounded-lg mb-1 ${
                        t.template_code === selectedTemplate ? "bg-blue-900/20" : "hover:bg-wo-surface-raised/60"
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => onSelectTemplate(t.template_code)}
                        className="flex-1 text-left px-3 py-2.5"
                      >
                        <p className="font-mono text-[11px] font-semibold text-blue-400">{t.template_code}</p>
                        <p className="text-[13px] text-foreground mt-0.5">{t.label}</p>
                        <p className="text-[10px] text-muted-foreground mt-1">
                          {t.family} · {t.materialCount} materiale · {t.workcenterCount} operații
                        </p>
                      </button>
                      <button
                        type="button"
                        onClick={() => onToggleFavoriteTemplate(t.template_code)}
                        className="p-2 mt-1 text-muted-foreground hover:text-amber-400"
                        title={isFav ? "Elimină din favorite" : "Adaugă la favorite"}
                      >
                        <Star
                          className={`w-4 h-4 ${isFav ? "fill-amber-400 text-amber-400" : ""}`}
                        />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
            <div className="px-4 py-2 border-t border-border text-[10px] text-muted-foreground">
              Căutare scalabilă — nu afișăm toate template-urile ca chip-uri.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function GroupHeader({ label, count }: { label: string; count: number }) {
  return (
    <div className="flex items-center gap-2 mt-5 mb-2 first:mt-0">
      <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground shrink-0">{label}</h4>
      <div className="flex-1 h-px bg-muted" />
      <span className="text-[10px] text-wo-text-dim">{count}</span>
    </div>
  );
}

function SectionHeader({ title }: { title: string }) {
  return (
    <h3 className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mb-2 mt-3 first:mt-0">
      {title}
    </h3>
  );
}

function CoverageStack({
  sections,
  selectedItem,
  onSelectItem,
  onEditMaterial,
  onEditRate,
  loadingRate,
}: {
  sections: ReturnType<typeof groupItemsForCoverageStack>;
  selectedItem: PricingRegistryItem | null;
  onSelectItem: (item: PricingRegistryItem) => void;
  onEditMaterial: (item: PricingRegistryItem) => void;
  onEditRate: (item: PricingRegistryItem) => void;
  loadingRate: boolean;
}) {
  if (sections.length === 0) {
    return (
      <p className="text-center text-[12px] text-muted-foreground py-12">
        Niciun rând pentru template-ul selectat.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {sections.map((section) => (
        <div key={section.key}>
          <SectionHeader title={section.title} />
          {section.subgroups.map((sg) => (
            <div key={sg.label}>
              <GroupHeader label={sg.label} count={sg.items.length} />
              <div className="space-y-2">
                {sg.items.map((item) => (
                  <PricingEntryRow
                    key={item.pricing_code}
                    item={item}
                    selected={selectedItem?.pricing_code === item.pricing_code}
                    onSelect={() => onSelectItem(item)}
                    onEditMaterial={onEditMaterial}
                    onEditRate={onEditRate}
                    loadingRate={loadingRate}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function FlatEntryList({
  items,
  selectedItem,
  onSelectItem,
  onEditMaterial,
  onEditRate,
  loadingRate,
}: {
  items: PricingRegistryItem[];
  selectedItem: PricingRegistryItem | null;
  onSelectItem: (item: PricingRegistryItem) => void;
  onEditMaterial: (item: PricingRegistryItem) => void;
  onEditRate: (item: PricingRegistryItem) => void;
  loadingRate: boolean;
}) {
  if (items.length === 0) {
    return <p className="text-center text-[12px] text-muted-foreground py-12">Niciun rând.</p>;
  }
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <PricingEntryRow
          key={item.pricing_code}
          item={item}
          selected={selectedItem?.pricing_code === item.pricing_code}
          onSelect={() => onSelectItem(item)}
          onEditMaterial={onEditMaterial}
          onEditRate={onEditRate}
          loadingRate={loadingRate}
          showTemplates={true}
        />
      ))}
    </div>
  );
}

function MarkupView({
  policies,
  selectedItem,
  onSelectItem,
}: {
  policies: PricingRegistryItem[];
  selectedItem: PricingRegistryItem | null;
  onSelectItem: (item: PricingRegistryItem) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-700/40 dark:bg-amber-900/20">
        <p className="text-[11px] leading-relaxed text-amber-900 dark:text-amber-200">
          <Info className="mr-1 inline h-3 w-3" />
          Editare reguli adaos — build separat. Regulile sunt vizibile aici, dar modificarea se face într-un flux dedicat.
        </p>
      </div>
      {policies.length === 0 ? (
        <p className="text-[12px] text-muted-foreground text-center py-8">Nu există reguli de adaos.</p>
      ) : (
        <div className="space-y-2">
          {policies.map((item) => (
            <PricingEntryRow
              key={item.pricing_code}
              item={item}
              selected={selectedItem?.pricing_code === item.pricing_code}
              onSelect={() => onSelectItem(item)}
              showCategory={false}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function AuditPlaceholder({
  selectedItem,
  priceHistory,
  loadingHistory,
}: {
  selectedItem: PricingRegistryItem | null;
  priceHistory: PriceHistoryEntryDTO[];
  loadingHistory: boolean;
}) {
  if (!selectedItem) {
    return (
      <p className="text-center text-[12px] text-muted-foreground py-12 px-4">
        Selectează un material sau o rată din acoperire pentru a vedea istoricul de preț disponibil.
      </p>
    );
  }
  if (selectedItem.pricing_kind !== "material") {
    return (
      <p className="text-center text-[12px] text-muted-foreground py-12 px-4">
        Istoricul detaliat este disponibil pentru materiale. Selectează un material din listă.
      </p>
    );
  }
  if (loadingHistory) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
      </div>
    );
  }
  if (priceHistory.length === 0) {
    return (
      <p className="text-center text-[12px] text-muted-foreground py-12">
        Nu există intrări în istoricul de preț pentru {selectedItem.pricing_code}.
      </p>
    );
  }
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold text-muted-foreground">
        Istoric — {selectedItem.pricing_code}
      </p>
      {priceHistory.map((h, idx) => (
        <div
          key={idx}
          className="bg-card border border-border rounded-lg p-4 text-[11px] hover:border-slate-500 transition-colors"
        >
          <p className="text-[14px] text-foreground font-bold">
            {h.unit_cost != null ? fmtCost(h.unit_cost, h.currency) : "—"}
            <span className="text-[11px] font-normal text-muted-foreground ml-1">/ buc</span>
          </p>
          <p className="text-muted-foreground mt-1">
            {h.valid_from ? new Date(h.valid_from).toLocaleDateString("ro-RO") : "—"}
            {h.change_reason ? ` · ${h.change_reason}` : ""}
          </p>
        </div>
      ))}
    </div>
  );
}

function DetailPanel({
  item,
  priceHistory,
  loadingHistory,
  onEditMaterial,
  onEditRate,
  loadingRate,
  baseCurrency,
}: {
  item: PricingRegistryItem | null;
  priceHistory: PriceHistoryEntryDTO[];
  loadingHistory: boolean;
  onEditMaterial: (item: PricingRegistryItem) => void;
  onEditRate: (item: PricingRegistryItem) => void;
  loadingRate: boolean;
  baseCurrency?: string | null;
}) {
  const model = buildDetailPanelModel(item, { baseCurrency });

  if (!model || !item) {
    return (
      <div className="flex flex-col items-center justify-center p-6 text-center min-h-[280px]">
        <Info className="w-7 h-7 text-wo-text-dim mb-2" />
        <p className="text-[12px] text-muted-foreground max-w-[240px]">
          Selectează o intrare pentru impact ofertă, sursă tehnică și acțiuni.
        </p>
      </div>
    );
  }

  const costDisplay =
    item.base_cost != null && !Number.isNaN(item.base_cost)
      ? fmtCost(item.base_cost, item.currency)
      : "Lipsă";

  return (
    <div className="flex flex-col min-h-0 overflow-y-auto p-4 space-y-3">
      <div className="border-b border-border pb-3">
        <h2 className="text-[15px] font-bold text-foreground">{model.name}</h2>
        <p className="font-mono text-[11px] text-blue-400 mt-0.5">{model.code}</p>
        <p className="text-[10px] text-muted-foreground mt-1">
          {model.typeLabel} · {model.category}
        </p>
      </div>

      <div className="bg-card border border-border rounded-lg p-3">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">{model.costLabelRo}</p>
        <p className="text-[20px] font-bold text-foreground">{costDisplay}</p>
        <p className="text-[11px] text-muted-foreground">{model.unit}</p>
        {model.machineFamilyLabel && (
          <p className="text-[11px] text-cyan-300/80 mt-1">{model.machineFamilyLabel}</p>
        )}
        <p className={`text-[11px] font-semibold mt-2 ${severityClass(model.status.severity)}`}>
          {model.status.text}
        </p>
        {model.currencyMismatchWarning && (
          <p className="text-[10px] text-amber-300 mt-2 leading-relaxed flex items-start gap-1">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            {model.currencyMismatchWarning}
          </p>
        )}
        {model.dataQualityWarningRo && (
          <p className="text-[10px] text-amber-300 mt-2 leading-relaxed flex items-start gap-1">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            {model.dataQualityWarningRo}
          </p>
        )}
      </div>

      <div className="text-[11px] text-muted-foreground space-y-1">
        <p>
          <span className="text-muted-foreground">Impact ofertă:</span>{" "}
          <span className="text-foreground">{model.impact}</span>
        </p>
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          Modifică valoarea folosită în calculul de ofertă. Nu modifică stocul, loturile sau ultimul preț de achiziție.
        </p>
      </div>

      <div className="space-y-1.5 text-[11px] border-t border-border pt-3">
        <div className="flex justify-between gap-2">
          <span className="text-muted-foreground shrink-0">Sursă tehnică</span>
          <span className="text-muted-foreground font-mono text-right">{technicalSourceLabel(model.technicalSource)}</span>
        </div>
        {model.templates.length > 0 && (
          <div>
            <span className="text-muted-foreground">Template-uri</span>
            <p className="text-muted-foreground mt-0.5 font-mono text-[10px] break-all">{model.templates.join(", ")}</p>
          </div>
        )}
        {model.sourceNotes && (
          <div>
            <span className="text-muted-foreground">Note sursă</span>
            <p className="text-muted-foreground mt-0.5 italic">{model.sourceNotes}</p>
          </div>
        )}
        {model.costEngineRate != null && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">CostEngine</span>
            <span className={model.costEngineRateMatch ? "text-emerald-400" : "text-amber-400"}>
              {model.costEngineRate} {model.costEngineRateMatch ? "✓" : "≠"}
            </span>
          </div>
        )}
      </div>

      {model.isMaterial && (
        <Link
          to="/inventory"
          className="inline-flex items-center gap-1.5 text-[11px] text-blue-400 hover:underline"
        >
          <ExternalLink className="w-3 h-3" />
          Referință operațională în Inventory
        </Link>
      )}

      {model.isMaterial && (
        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1.5">Istoric recent</p>
          {loadingHistory ? (
            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          ) : priceHistory.length > 0 ? (
            <div className="space-y-1">
              {priceHistory.slice(0, 3).map((h, idx) => (
                <p key={idx} className="text-[10px] text-muted-foreground">
                  {h.unit_cost != null ? fmtCost(h.unit_cost, h.currency) : "—"} —{" "}
                  {h.valid_from ? new Date(h.valid_from).toLocaleDateString("ro-RO") : "—"}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-[10px] text-wo-text-dim">Nu există istoric disponibil.</p>
          )}
        </div>
      )}

      <div className="flex gap-2 pt-1">
        {model.isMaterial && model.editable && (
          <button
            type="button"
            onClick={() => onEditMaterial(item)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded bg-blue-600 text-white hover:bg-blue-500"
          >
            <Pencil className="w-3 h-3" />
            Editare preț
          </button>
        )}
        {model.isRate && model.editable && (
          <button
            type="button"
            onClick={() => onEditRate(item)}
            disabled={loadingRate}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50"
          >
            <Pencil className="w-3 h-3" />
            Editare rată
          </button>
        )}
        {model.isMarkup && (
          <span className="text-[10px] text-amber-400/90 self-center">Editare reguli adaos — build separat</span>
        )}
        {!model.isMaterial && !model.isRate && !model.isMarkup && (
          <span className="text-[10px] text-muted-foreground self-center">Vizualizare read-only</span>
        )}
      </div>
    </div>
  );
}
