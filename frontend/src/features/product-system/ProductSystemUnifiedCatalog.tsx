import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ChevronDown, ChevronRight, MoreHorizontal } from "lucide-react";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import { LETTERS_TEMPLATE_CODE } from "@/lib/productTemplateScopePresentation";
import { COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE } from "./componentFirstReadonlyCompleteness";
import { ComponentFirstReadonlyCandidatePanel } from "./ComponentFirstReadonlyCandidatePanel";
import {
  buildUnifiedCatalogEntries,
  CANDIDATE_SET_ENTRY_ID,
  filterUnifiedCatalogEntries,
  groupUnifiedCatalogEntriesByBucket,
} from "./buildUnifiedCatalogEntries";
import { COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE } from "./componentFirstReadonlyDossierAlignment";
import {
  defaultTemplateDetailSection,
  ProductSystemTemplateDetailPanel,
} from "./ProductSystemTemplateDetailPanel";
import {
  UNIFIED_CATALOG_BUCKETS,
  UNIFIED_CATALOG_BUCKET_THEMES,
  UNIFIED_CATALOG_FILTERS,
  type UnifiedCatalogBucketGroup,
  type UnifiedCatalogBucketId,
  type UnifiedCatalogDetailSection,
  type UnifiedCatalogEntry,
  type UnifiedCatalogFilter,
} from "./productSystemUnifiedCatalogTypes";

export type UnifiedCatalogSummary = {
  products: number;
  components: number;
  candidateSets: number;
  dossierContractCount: number | null;
  componentFirstLiveRows: number | null;
  componentFirstExpectedRows: number | null;
  blocked: number | null;
  archived: number;
};

export function buildUnifiedCatalogSummary({
  catalogCounts,
  archivedCount,
  hasComponentFirstCandidate,
  ownerDecisionRequiredCount,
  componentFirstLiveRows = null,
  componentFirstExpectedRows = null,
}: {
  catalogCounts: {
    activeProducts: number;
    candidateProducts: number;
    internalModules: number;
    sharedComponents: number;
    archivedExperimental: number;
  };
  archivedCount: number;
  hasComponentFirstCandidate: boolean;
  ownerDecisionRequiredCount: number;
  componentFirstLiveRows?: number | null;
  componentFirstExpectedRows?: number | null;
}): UnifiedCatalogSummary {
  return {
    products: catalogCounts.activeProducts + catalogCounts.candidateProducts,
    components: catalogCounts.internalModules + catalogCounts.sharedComponents,
    candidateSets: hasComponentFirstCandidate ? 1 : 0,
    dossierContractCount: hasComponentFirstCandidate ? COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE.length : null,
    componentFirstLiveRows: hasComponentFirstCandidate ? componentFirstLiveRows : null,
    componentFirstExpectedRows: hasComponentFirstCandidate ? componentFirstExpectedRows : null,
    blocked: ownerDecisionRequiredCount > 0 ? ownerDecisionRequiredCount : null,
    archived: catalogCounts.archivedExperimental > 0 ? catalogCounts.archivedExperimental : archivedCount,
  };
}

function initialBucketExpandedState(): Record<UnifiedCatalogBucketId, boolean> {
  return UNIFIED_CATALOG_BUCKETS.reduce(
    (acc, bucket) => {
      acc[bucket.id] = bucket.defaultExpanded;
      return acc;
    },
    {} as Record<UnifiedCatalogBucketId, boolean>,
  );
}

function rowActionLabels(entry: UnifiedCatalogEntry): {
  open: string;
  settings: string;
  dossier: string;
  components: string | null;
  guards: string;
} {
  if (entry.kind === "candidate-set") {
    return {
      open: "Open",
      settings: "Settings",
      dossier: "Dossier",
      components: "Components",
      guards: "Guards",
    };
  }
  if (entry.bucket === "legacy-shared-modules") {
    return {
      open: "Open",
      settings: "Settings",
      dossier: "Dossier",
      components: null,
      guards: "Guards",
    };
  }
  return {
    open: "Open",
    settings: "Settings",
    dossier: "Dossier",
    components: entry.isProduct ? "Components" : null,
    guards: "Guards",
  };
}

const SUMMARY_METRICS: Array<{
  key: keyof UnifiedCatalogSummary;
  label: string;
  testId: string;
  tone?: "default" | "warning";
}> = [
  { key: "products", label: "Rădăcini produs", testId: "product-system-summary-products" },
  { key: "components", label: "Module", testId: "product-system-summary-components" },
  { key: "candidateSets", label: "Seturi comp-first", testId: "product-system-summary-candidate-sets" },
  { key: "dossierContractCount", label: "Dosare contract", testId: "product-system-summary-dossier-contract" },
  {
    key: "componentFirstLiveRows",
    label: "Randuri live comp-first",
    testId: "product-system-summary-component-first-live-rows",
  },
  { key: "blocked", label: "Blocate", testId: "product-system-summary-blocked", tone: "warning" },
  { key: "archived", label: "Arhivate", testId: "product-system-summary-archived" },
];

function buildSummaryCompactLine(summary: UnifiedCatalogSummary): string {
  const parts = [
    `${summary.products} rădăcini`,
    `${summary.components} module`,
    `${summary.candidateSets} comp-first`,
  ];
  if (summary.dossierContractCount != null) parts.push(`${summary.dossierContractCount} dosare contract`);
  if (summary.componentFirstLiveRows != null && summary.componentFirstExpectedRows != null) {
    parts.push(`${summary.componentFirstLiveRows}/${summary.componentFirstExpectedRows} randuri live`);
  }
  if (summary.blocked != null) parts.push(`${summary.blocked} blocate`);
  parts.push(`${summary.archived} arhivate`);
  return parts.join(" · ");
}

function filterToExpandedBuckets(filter: UnifiedCatalogFilter): UnifiedCatalogBucketId[] {
  switch (filter) {
    case "current-products":
      return ["current-products"];
    case "candidate-products":
      return ["candidate-products"];
    case "component-first-sets":
      return ["component-first-sets"];
    case "legacy-modules":
      return ["legacy-shared-modules"];
    case "archived":
      return ["archived"];
    case "blocked":
      return UNIFIED_CATALOG_BUCKETS.map((bucket) => bucket.id);
    default:
      return [];
  }
}

function SummaryMetrics({ summary }: { summary: UnifiedCatalogSummary }) {
  return (
    <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
      {SUMMARY_METRICS.map((metric) => {
        const rawValue = summary[metric.key];
        if (metric.key === "dossierContractCount" && rawValue == null) return null;
        if (metric.key === "componentFirstLiveRows" && summary.componentFirstExpectedRows == null) return null;
        if (metric.key === "blocked" && rawValue == null) return null;

        const value =
          metric.key === "componentFirstLiveRows" && summary.componentFirstExpectedRows != null
            ? `${summary.componentFirstLiveRows ?? 0}/${summary.componentFirstExpectedRows}`
            : rawValue ?? 0;
        const isWarning = metric.tone === "warning" && value > 0;

        return (
          <div
            key={metric.key}
            data-testid={metric.testId}
            className={`rounded-md border px-2 py-1.5 ${
              isWarning
                ? "border-amber-800/40 bg-amber-950/15"
                : "border-slate-800/80 bg-slate-950/40"
            }`}
          >
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">{metric.label}</p>
            <p
              className={`mt-0.5 text-base font-bold tabular-nums leading-none ${
                isWarning ? "text-amber-200" : "text-slate-100"
              }`}
            >
              {value}
            </p>
          </div>
        );
      })}
    </div>
  );
}

function CollapsibleSummaryBar({ summary }: { summary: UnifiedCatalogSummary }) {
  const [expanded, setExpanded] = useState(false);
  const compactLine = buildSummaryCompactLine(summary);

  return (
    <div data-testid="product-system-summary-bar" data-expanded={expanded ? "true" : "false"}>
      <button
        type="button"
        data-testid="product-system-summary-toggle"
        onClick={() => setExpanded((current) => !current)}
        className="flex w-full items-center gap-2 rounded-md border border-slate-800/70 bg-slate-950/30 px-2.5 py-1.5 text-left transition-colors hover:bg-slate-900/40"
        aria-expanded={expanded}
      >
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-500" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-500" />
        )}
        <span className="text-[11px] font-semibold text-slate-400">Statistici catalog</span>
        {!expanded ? (
          <span className="min-w-0 flex-1 truncate text-xs text-slate-500">{compactLine}</span>
        ) : null}
      </button>
      {expanded ? <div className="mt-2"><SummaryMetrics summary={summary} /></div> : null}
    </div>
  );
}

function CatalogRowAction({
  label,
  testId,
  onClick,
  variant = "secondary",
}: {
  label: string;
  testId: string;
  onClick: () => void;
  variant?: "primary" | "secondary" | "ghost";
}) {
  const className =
    variant === "primary"
      ? "border-purple-700/50 bg-purple-950/40 text-purple-100 hover:bg-purple-900/50"
      : variant === "ghost"
        ? "border-transparent bg-transparent text-slate-400 hover:border-slate-700 hover:bg-slate-900/60 hover:text-slate-200"
        : "border-slate-700/80 bg-slate-900/50 text-slate-300 hover:border-slate-600 hover:bg-slate-800/80";

  return (
    <button
      type="button"
      data-testid={testId}
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}
      className={`shrink-0 rounded-md border px-2.5 py-1 text-xs font-semibold transition-colors ${className}`}
    >
      {label}
    </button>
  );
}

function CatalogRowActionsMenu({
  rowTestId,
  actions,
  onSettings,
  onDossier,
  onComponents,
  onGuards,
}: {
  rowTestId: string;
  actions: ReturnType<typeof rowActionLabels>;
  onSettings: () => void;
  onDossier: () => void;
  onComponents: () => void;
  onGuards: () => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        type="button"
        data-testid={`${rowTestId}-action-more`}
        onClick={(event) => {
          event.stopPropagation();
          setOpen((current) => !current);
        }}
        className="shrink-0 rounded-md border border-slate-800 bg-slate-900/60 p-1.5 text-slate-500 transition-colors hover:border-slate-700 hover:text-slate-300"
        aria-label="Mai multe acțiuni"
        aria-expanded={open}
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>
      {open ? (
        <div
          className="absolute right-0 top-full z-20 mt-1 min-w-[10rem] rounded-lg border border-slate-800 bg-[#0f172a] p-1.5 shadow-xl"
          onClick={(event) => event.stopPropagation()}
        >
          <button
            type="button"
            data-testid={`${rowTestId}-action-settings`}
            className="block w-full rounded-md px-2.5 py-1.5 text-left text-xs text-slate-200 hover:bg-slate-800"
            onClick={() => {
              onSettings();
              setOpen(false);
            }}
          >
            {actions.settings}
          </button>
          {actions.components ? (
            <button
              type="button"
              data-testid={`${rowTestId}-action-components`}
              className="block w-full rounded-md px-2.5 py-1.5 text-left text-xs text-slate-200 hover:bg-slate-800"
              onClick={() => {
                onComponents();
                setOpen(false);
              }}
            >
              {actions.components}
            </button>
          ) : null}
          <button
            type="button"
            data-testid={`${rowTestId}-action-guards`}
            className="block w-full rounded-md px-2.5 py-1.5 text-left text-xs text-slate-200 hover:bg-slate-800"
            onClick={() => {
              onGuards();
              setOpen(false);
            }}
          >
            {actions.guards}
          </button>
        </div>
      ) : null}
    </div>
  );
}

function UnifiedCatalogRow({
  entry,
  selected,
  onSelect,
  onOpen,
  onSettings,
  onDossier,
  onComponents,
  onGuards,
}: {
  entry: UnifiedCatalogEntry;
  selected: boolean;
  onSelect: () => void;
  onOpen: () => void;
  onSettings: () => void;
  onDossier: () => void;
  onComponents: () => void;
  onGuards: () => void;
}) {
  const rowTestId =
    entry.kind === "candidate-set"
      ? "product-system-unified-row-candidate-set"
      : `product-system-unified-row-${entry.templateCode}`;
  const actions = rowActionLabels(entry);
  const theme = UNIFIED_CATALOG_BUCKET_THEMES[entry.bucket];

  return (
    <article
      data-testid={rowTestId}
      data-bucket={entry.bucket}
      data-selected={selected ? "true" : "false"}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }}
      role="listitem"
      tabIndex={0}
      className={`cursor-pointer rounded-xl border px-3 py-3 transition-all ${
        selected
          ? "border-purple-500/40 bg-slate-900/80 shadow-[0_0_0_1px_rgba(168,85,247,0.12)]"
          : "border-slate-800/70 bg-[#111827]/50 hover:border-slate-700 hover:bg-slate-900/50"
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1 space-y-2">
          <div>
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
              <p className="text-sm font-semibold leading-snug text-slate-100">{entry.name}</p>
              <p className="font-mono text-[11px] text-slate-500">{entry.templateCode}</p>
            </div>
            {entry.metadata ? (
              <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-500">{entry.metadata}</p>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-1.5">
            <span className="rounded-md border border-slate-800 bg-slate-950/80 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-500">
              {entry.entityType}
            </span>
            <span className={`rounded-md border px-2 py-0.5 text-[10px] font-bold ${theme.badge}`}>
              {entry.lifecycleLabel}
            </span>
            {entry.isBlocked ? (
              <span className="rounded-md border border-amber-800/40 bg-amber-950/25 px-2 py-0.5 text-[10px] font-bold text-amber-200/90">
                Owner GO
              </span>
            ) : null}
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1.5 sm:flex-row sm:items-center" onClick={(event) => event.stopPropagation()}>
          <div className="flex items-center gap-1.5">
            <CatalogRowAction
              label={actions.open}
              testId={`${rowTestId}-action-open`}
              onClick={onOpen}
              variant="primary"
            />
            <CatalogRowAction
              label={actions.dossier}
              testId={`${rowTestId}-action-dossier`}
              onClick={onDossier}
              variant="ghost"
            />
          </div>
          <CatalogRowActionsMenu
            rowTestId={rowTestId}
            actions={actions}
            onSettings={onSettings}
            onDossier={onDossier}
            onComponents={onComponents}
            onGuards={onGuards}
          />
        </div>
      </div>
    </article>
  );
}

function CatalogBucketSection({
  group,
  expanded,
  onToggle,
  selectedEntryId,
  onSelectEntry,
  onOpenEntry,
  onSettingsEntry,
  onOpenSection,
  onViewReplacementMap,
}: {
  group: UnifiedCatalogBucketGroup;
  expanded: boolean;
  onToggle: () => void;
  selectedEntryId: string | null;
  onSelectEntry: (entry: UnifiedCatalogEntry) => void;
  onOpenEntry: (entry: UnifiedCatalogEntry) => void;
  onSettingsEntry: (entry: UnifiedCatalogEntry) => void;
  onOpenSection: (
    entry: UnifiedCatalogEntry,
    section: UnifiedCatalogDetailSection | "components" | "dossier" | "guards-audit" | "guards",
  ) => void;
  onViewReplacementMap?: () => void;
}) {
  const theme = UNIFIED_CATALOG_BUCKET_THEMES[group.bucket.id];
  const isLegacyBucket = group.bucket.id === "legacy-shared-modules";
  const legacyCount = group.entries.length;

  return (
    <section
      data-testid={group.bucket.testId}
      data-expanded={expanded ? "true" : "false"}
      className={`overflow-hidden rounded-xl border ${theme.header}`}
    >
      <button
        type="button"
        data-testid={group.bucket.toggleTestId}
        onClick={onToggle}
        className="flex w-full items-start justify-between gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-900/25"
      >
        <span className="flex min-w-0 items-start gap-2.5">
          {expanded ? (
            <ChevronDown className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
          ) : (
            <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
          )}
          <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${theme.dot}`} aria-hidden="true" />
          <span className="min-w-0">
            <span className="block text-sm font-semibold text-slate-100">{group.bucket.label}</span>
            <span className="mt-0.5 block text-xs leading-relaxed text-slate-500">{group.bucket.description}</span>
          </span>
        </span>
        <span className="shrink-0 rounded-full border border-slate-800 bg-slate-950/60 px-2 py-0.5 text-[11px] font-bold tabular-nums text-slate-400">
          {group.entries.length}
        </span>
      </button>
      {expanded ? (
        <div className="space-y-2 border-t border-slate-800/60 px-3 py-3">
          {isLegacyBucket ? (
            <div
              data-testid="product-system-legacy-bucket-support-banner"
              className="rounded-lg border border-amber-800/30 bg-amber-950/15 px-3 py-2.5"
            >
              <p
                data-testid="product-system-legacy-bucket-support-copy"
                className="text-xs font-semibold text-amber-200/90"
              >
                Legacy support only — used by parent product, not new component-first.
              </p>
              <p className="mt-1 text-[10px] text-slate-400">
                Replacement path proposed · readonly mapping · no delete now · future deprecation candidate.
              </p>
              {legacyCount > 20 ? (
                <p
                  data-testid="product-system-legacy-bucket-scale-hint"
                  className="mt-2 text-[10px] font-medium text-slate-500"
                >
                  Use search/filter before expanding full legacy list ({legacyCount} modules).
                </p>
              ) : null}
              {onViewReplacementMap ? (
                <button
                  type="button"
                  data-testid="product-system-legacy-bucket-view-replacement-map"
                  onClick={(event) => {
                    event.stopPropagation();
                    onViewReplacementMap();
                  }}
                  className="mt-2 rounded-md border border-purple-800/40 bg-purple-950/30 px-2.5 py-1 text-[10px] font-semibold text-purple-200 transition-colors hover:bg-purple-900/30"
                >
                  View replacement map
                </button>
              ) : null}
            </div>
          ) : null}
          {group.entries.map((entry) => (
            <UnifiedCatalogRow
              key={entry.id}
              entry={entry}
              selected={selectedEntryId === entry.id}
              onSelect={() => onSelectEntry(entry)}
              onOpen={() => onOpenEntry(entry)}
              onSettings={() => onSettingsEntry(entry)}
              onDossier={() => onOpenSection(entry, "dossier")}
              onComponents={() => onOpenSection(entry, "components")}
              onGuards={() => onOpenSection(entry, "guards")}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

type ProductSystemUnifiedCatalogProps = {
  catalogOverview?: ReactNode;
  templates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
  summary: UnifiedCatalogSummary;
  loading: boolean;
  search?: string;
  onSearchChange?: (value: string) => void;
  onOpenTemplate: (template: ProductTemplateEntity) => void;
};

export function ProductSystemUnifiedCatalog({
  catalogOverview,
  templates,
  availabilityItems,
  summary,
  loading,
  search: searchProp,
  onSearchChange,
  onOpenTemplate,
}: ProductSystemUnifiedCatalogProps) {
  const [internalSearch, setInternalSearch] = useState("");
  const search = searchProp ?? internalSearch;
  const setSearch = onSearchChange ?? setInternalSearch;
  const [filter, setFilter] = useState<UnifiedCatalogFilter>("all");
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null);
  const [templateDetailSection, setTemplateDetailSection] = useState<UnifiedCatalogDetailSection>("overview");
  const [candidateDetailSection, setCandidateDetailSection] = useState<
    "overview" | "components" | "dossier" | "guards-audit"
  >("overview");
  const [bucketExpanded, setBucketExpanded] = useState(initialBucketExpandedState);

  const entries = useMemo(
    () => buildUnifiedCatalogEntries({ templates, availabilityItems }),
    [templates, availabilityItems],
  );

  const filteredEntries = useMemo(
    () => filterUnifiedCatalogEntries({ entries, filter, search }),
    [entries, filter, search],
  );

  const bucketGroups = useMemo(
    () => groupUnifiedCatalogEntriesByBucket(filteredEntries),
    [filteredEntries],
  );

  const selectedEntry =
    filteredEntries.find((entry) => entry.id === selectedEntryId) ??
    entries.find((entry) => entry.id === selectedEntryId) ??
    null;

  useEffect(() => {
    if (selectedEntryId || loading || entries.length === 0) return;
    const lettersEntry = entries.find(
      (entry) => entry.templateCode === LETTERS_TEMPLATE_CODE && entry.bucket === "current-products",
    );
    if (lettersEntry) {
      setSelectedEntryId(lettersEntry.id);
      setTemplateDetailSection("overview");
      setBucketExpanded((current) => ({ ...current, "current-products": true }));
    }
  }, [entries, loading, selectedEntryId]);

  useEffect(() => {
    const bucketsForFilter = filterToExpandedBuckets(filter);
    if (bucketsForFilter.length === 0) return;
    setBucketExpanded((current) => {
      const next = { ...current };
      for (const bucketId of bucketsForFilter) {
        next[bucketId] = true;
      }
      return next;
    });
  }, [filter]);

  useEffect(() => {
    if (!search.trim()) return;
    const bucketsWithMatches = new Set(filteredEntries.map((entry) => entry.bucket));
    if (bucketsWithMatches.size === 0) return;
    setBucketExpanded((current) => {
      const next = { ...current };
      bucketsWithMatches.forEach((bucketId) => {
        next[bucketId] = true;
      });
      return next;
    });
  }, [search, filteredEntries]);

  const selectEntry = (entry: UnifiedCatalogEntry) => {
    setSelectedEntryId(entry.id);
    setBucketExpanded((current) => ({ ...current, [entry.bucket]: true }));
    if (entry.kind === "template" && entry.template && entry.availability) {
      setTemplateDetailSection(defaultTemplateDetailSection(entry.isProduct));
    } else if (entry.kind === "candidate-set") {
      setCandidateDetailSection("overview");
    }
  };

  const openEntry = (entry: UnifiedCatalogEntry) => {
    selectEntry(entry);
    if (entry.kind === "template" && entry.template) {
      onOpenTemplate(entry.template);
    }
  };

  const openSettings = (entry: UnifiedCatalogEntry) => {
    selectEntry(entry);
    if (entry.kind === "template" && entry.template) {
      onOpenTemplate(entry.template);
    }
  };

  const openSection = (
    entry: UnifiedCatalogEntry,
    section: UnifiedCatalogDetailSection | "components" | "dossier" | "guards-audit" | "guards",
  ) => {
    selectEntry(entry);
    if (entry.kind === "candidate-set") {
      if (section === "components") setCandidateDetailSection("components");
      else if (section === "dossier") setCandidateDetailSection("dossier");
      else if (section === "guards" || section === "guards-audit") setCandidateDetailSection("guards-audit");
      else setCandidateDetailSection("overview");
      return;
    }
    if (section === "guards-audit") {
      setTemplateDetailSection("guards");
      return;
    }
    setTemplateDetailSection(section as UnifiedCatalogDetailSection);
  };

  const toggleBucket = (bucketId: UnifiedCatalogBucketId) => {
    setBucketExpanded((current) => ({ ...current, [bucketId]: !current[bucketId] }));
  };

  const viewLegacyReplacementMap = () => {
    const legacyEntries = entries.filter((entry) => entry.bucket === "legacy-shared-modules" && entry.kind === "template");
    const faceEntry =
      legacyEntries.find((entry) => entry.templateCode === "TPL-VOLUMETRIC-FACE_v1") ?? legacyEntries[0];
    if (!faceEntry) return;
    setSelectedEntryId(faceEntry.id);
    setBucketExpanded((current) => ({ ...current, "legacy-shared-modules": true }));
    setTemplateDetailSection("guards");
  };

  return (
    <div className="space-y-4" data-testid="product-system-unified-catalog" data-layout="comfortable">
      {catalogOverview ?? null}

      <section
        data-testid="product-system-catalog-toolbar"
        className="space-y-2 rounded-xl border border-slate-800/70 bg-slate-950/20 px-3 py-2"
      >
        <CollapsibleSummaryBar summary={summary} />

        <div
          className="min-w-0 overflow-x-auto xl:overflow-visible"
          data-testid="product-system-unified-search-filter"
        >
          <div
            className="min-w-0 overflow-x-auto xl:overflow-visible"
            data-testid="product-system-unified-filter-chips-scroll"
          >
            <div
              className="flex w-max flex-nowrap gap-1.5 pr-1 xl:w-auto xl:flex-wrap"
              role="group"
              aria-label="Filtre catalog"
              data-testid="product-system-unified-filter-chips"
            >
              {UNIFIED_CATALOG_FILTERS.map((chip) => {
                const active = filter === chip.id;
                return (
                  <button
                    key={chip.id}
                    type="button"
                    data-testid={chip.testId}
                    aria-pressed={active}
                    onClick={() => setFilter(chip.id)}
                    className={`shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold transition-colors ${
                      active
                        ? "border-purple-600/50 bg-purple-950/30 text-purple-100"
                        : "border-slate-800 bg-slate-900/50 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                    }`}
                  >
                    {chip.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,0.44fr)_minmax(0,0.56fr)] xl:items-start">
        <section data-testid="product-system-unified-results-list" className="space-y-3" role="list">
          <div className="flex items-end justify-between gap-3 px-1">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Catalog pe categorii</h2>
              <p className="mt-0.5 text-xs text-slate-500">Selectează o intrare pentru detalii în panoul din dreapta.</p>
            </div>
            <span className="rounded-full border border-slate-800 bg-slate-950/60 px-2.5 py-1 text-[11px] font-bold tabular-nums text-slate-400">
              {filteredEntries.length}
            </span>
          </div>
          {loading ? (
            <p className="px-1 text-sm text-slate-500">Se încarcă catalogul…</p>
          ) : bucketGroups.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-800 px-4 py-8 text-center">
              <p className="text-sm font-medium text-slate-300">Niciun rezultat</p>
              <p className="mt-1 text-xs text-slate-500">Încearcă alt filtru sau șterge textul din căutare.</p>
            </div>
          ) : (
            bucketGroups.map((group) => (
              <CatalogBucketSection
                key={group.bucket.id}
                group={group}
                expanded={bucketExpanded[group.bucket.id] ?? group.bucket.defaultExpanded}
                onToggle={() => toggleBucket(group.bucket.id)}
                selectedEntryId={selectedEntryId}
                onSelectEntry={selectEntry}
                onOpenEntry={openEntry}
                onSettingsEntry={openSettings}
                onOpenSection={openSection}
                onViewReplacementMap={
                  group.bucket.id === "legacy-shared-modules" ? viewLegacyReplacementMap : undefined
                }
              />
            ))
          )}
        </section>

        <section
          data-testid="product-system-detail-panel"
          className="min-h-[22rem] rounded-xl border border-slate-800/70 bg-slate-950/20 p-4 xl:sticky xl:top-3 xl:max-h-[calc(100vh-148px)] xl:overflow-y-auto"
        >
          {!selectedEntry ? (
            <div className="flex h-full min-h-[18rem] flex-col items-center justify-center px-4 text-center">
              <p className="text-sm font-medium text-slate-300">Nicio intrare selectată</p>
              <p className="mt-1 max-w-xs text-xs leading-relaxed text-slate-500">
                Alege un produs, modul sau set component-first din listă pentru a vedea context, compoziție și garduri.
              </p>
            </div>
          ) : selectedEntry.kind === "candidate-set" ? (
            <div data-testid="product-system-candidate-sets">
              <ComponentFirstReadonlyCandidatePanel
                templates={templates}
                availabilityItems={availabilityItems}
                selectedTemplateCode={COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE}
                variant="detail-panel"
                detailSection={candidateDetailSection}
                onDetailSectionChange={setCandidateDetailSection}
              />
            </div>
          ) : selectedEntry.template && selectedEntry.availability ? (
            <ProductSystemTemplateDetailPanel
              template={selectedEntry.template}
              availability={selectedEntry.availability}
              catalogBucket={selectedEntry.bucket}
              section={templateDetailSection}
              onSectionChange={setTemplateDetailSection}
              onOpenEditor={() => onOpenTemplate(selectedEntry.template!)}
              rowMetadata={selectedEntry.metadata}
            />
          ) : null}
        </section>
      </div>
    </div>
  );
}

export { CANDIDATE_SET_ENTRY_ID };
