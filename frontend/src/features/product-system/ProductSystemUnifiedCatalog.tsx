import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ChevronDown, ChevronRight, MoreHorizontal, Search } from "lucide-react";
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
  dossiers: number | null;
  blocked: number | null;
  archived: number;
};

export function buildUnifiedCatalogSummary({
  catalogCounts,
  archivedCount,
  hasComponentFirstCandidate,
  ownerDecisionRequiredCount,
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
}): UnifiedCatalogSummary {
  return {
    products: catalogCounts.activeProducts + catalogCounts.candidateProducts,
    components: catalogCounts.internalModules + catalogCounts.sharedComponents,
    candidateSets: hasComponentFirstCandidate ? 1 : 0,
    dossiers: hasComponentFirstCandidate ? COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE.length : null,
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
      open: "Open readonly",
      settings: "Settings readonly",
      dossier: "Dossier",
      components: "Components",
      guards: "Guards",
    };
  }
  if (entry.bucket === "legacy-shared-modules") {
    return {
      open: "Open module",
      settings: "View parent usage",
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

function SummaryStrip({ summary }: { summary: UnifiedCatalogSummary }) {
  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-slate-500">
      <span>
        <span className="font-bold tabular-nums text-slate-300">{summary.products}</span> roots
      </span>
      <span className="text-slate-700" aria-hidden="true">
        ·
      </span>
      <span>
        <span className="font-bold tabular-nums text-slate-300">{summary.components}</span> modules
      </span>
      <span className="text-slate-700" aria-hidden="true">
        ·
      </span>
      <span>
        <span className="font-bold tabular-nums text-slate-300">{summary.candidateSets}</span> comp-first
      </span>
      {summary.dossiers != null ? (
        <>
          <span className="text-slate-700" aria-hidden="true">
            ·
          </span>
          <span>
            <span className="font-bold tabular-nums text-slate-300">{summary.dossiers}</span> dossiers
          </span>
        </>
      ) : null}
      {summary.blocked != null ? (
        <>
          <span className="text-slate-700" aria-hidden="true">
            ·
          </span>
          <span className="text-amber-300/90">
            <span className="font-bold tabular-nums">{summary.blocked}</span> blocked
          </span>
        </>
      ) : null}
      <span className="text-slate-700" aria-hidden="true">
        ·
      </span>
      <span>
        <span className="font-bold tabular-nums text-slate-300">{summary.archived}</span> archived
      </span>
    </p>
  );
}

function CatalogRowPrimaryAction({
  label,
  testId,
  onClick,
}: {
  label: string;
  testId: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      data-testid={testId}
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}
      className="shrink-0 rounded border border-purple-700/50 bg-purple-950/40 px-1.5 py-0.5 text-[10px] font-bold text-purple-100 hover:bg-purple-900/50"
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
        className="shrink-0 rounded border border-slate-800 bg-slate-900/60 p-0.5 text-slate-500 hover:text-slate-300"
        aria-label="More row actions"
        aria-expanded={open}
      >
        <MoreHorizontal className="h-3.5 w-3.5" />
      </button>
      {open ? (
        <div
          className="absolute right-0 top-full z-20 mt-0.5 min-w-[9rem] rounded border border-slate-800 bg-[#0f172a] p-1 shadow-lg"
          onClick={(event) => event.stopPropagation()}
        >
          <button
            type="button"
            data-testid={`${rowTestId}-action-settings`}
            className="block w-full rounded px-2 py-1 text-left text-[11px] text-slate-200 hover:bg-slate-800"
            onClick={() => {
              onSettings();
              setOpen(false);
            }}
          >
            {actions.settings}
          </button>
          <button
            type="button"
            data-testid={`${rowTestId}-action-dossier`}
            className="block w-full rounded px-2 py-1 text-left text-[11px] text-slate-200 hover:bg-slate-800"
            onClick={() => {
              onDossier();
              setOpen(false);
            }}
          >
            {actions.dossier}
          </button>
          {actions.components ? (
            <button
              type="button"
              data-testid={`${rowTestId}-action-components`}
              className="block w-full rounded px-2 py-1 text-left text-[11px] text-slate-200 hover:bg-slate-800"
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
            className="block w-full rounded px-2 py-1 text-left text-[11px] text-slate-200 hover:bg-slate-800"
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
      className={`cursor-pointer rounded-md border px-2 py-1 transition-colors ${
        selected
          ? "border-slate-600/80 bg-slate-900/70 ring-1 ring-purple-500/15"
          : "border-slate-800/70 bg-[#111827]/60 hover:border-slate-700 hover:bg-slate-900/40"
      }`}
    >
      <div className="flex items-center gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-1.5 gap-y-0">
            <p className="text-[12px] font-bold leading-tight text-slate-100">{entry.name}</p>
            <p className="font-mono text-[9px] text-slate-600">{entry.templateCode}</p>
          </div>
          <div className="mt-0.5 flex flex-wrap gap-0.5">
            <span className="rounded border border-slate-800 bg-slate-950/80 px-1 py-px text-[9px] font-bold uppercase text-slate-500">
              {entry.entityType}
            </span>
            <span className={`rounded border px-1 py-px text-[9px] font-bold ${theme.badge}`}>{entry.lifecycleLabel}</span>
            {entry.isBlocked ? (
              <span className="rounded border border-amber-800/40 bg-amber-950/25 px-1 py-px text-[9px] font-bold text-amber-200/90">
                Owner GO
              </span>
            ) : null}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1" onClick={(event) => event.stopPropagation()}>
          <CatalogRowPrimaryAction label={actions.open} testId={`${rowTestId}-action-open`} onClick={onOpen} />
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
}) {
  const theme = UNIFIED_CATALOG_BUCKET_THEMES[group.bucket.id];

  return (
    <section
      data-testid={group.bucket.testId}
      data-expanded={expanded ? "true" : "false"}
      className="overflow-hidden rounded-md border border-slate-800/70 bg-slate-950/10"
    >
      <button
        type="button"
        data-testid={group.bucket.toggleTestId}
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-2 px-2 py-1 text-left hover:bg-slate-900/35"
      >
        <span className="flex min-w-0 items-center gap-1.5">
          {expanded ? (
            <ChevronDown className="h-3 w-3 shrink-0 text-slate-500" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0 text-slate-500" />
          )}
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${theme.dot}`} aria-hidden="true" />
          <span className="truncate text-[11px] font-bold text-slate-200">{group.bucket.label}</span>
        </span>
        <span className="shrink-0 text-[9px] font-bold tabular-nums text-slate-500">{group.entries.length}</span>
      </button>
      {expanded ? (
        <div className="space-y-1 border-t border-slate-800/60 px-1.5 py-1">
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
  onOpenTemplate: (template: ProductTemplateEntity) => void;
};

export function ProductSystemUnifiedCatalog({
  catalogOverview,
  templates,
  availabilityItems,
  summary,
  loading,
  onOpenTemplate,
}: ProductSystemUnifiedCatalogProps) {
  const [filter, setFilter] = useState<UnifiedCatalogFilter>("all");
  const [search, setSearch] = useState("");
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
    }
  }, [entries, loading, selectedEntryId]);

  const selectEntry = (entry: UnifiedCatalogEntry) => {
    setSelectedEntryId(entry.id);
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

  return (
    <div className="space-y-2" data-testid="product-system-unified-catalog" data-layout="compact">
      {catalogOverview ?? null}

      <section
        data-testid="product-system-compact-toolbar"
        className="rounded-md border border-slate-800/70 bg-slate-950/15 px-2 py-1.5"
      >
        <div data-testid="product-system-summary-bar">
          <SummaryStrip summary={summary} />
        </div>
        <div
          data-testid="product-system-unified-search-filter"
          className="mt-1 flex min-w-0 items-center gap-2"
        >
          <div className="flex w-44 shrink-0 items-center gap-1.5 rounded border border-slate-800/80 bg-[#0a0f18]/80 px-2 py-1 sm:w-52">
            <Search className="h-3 w-3 shrink-0 text-slate-600" />
            <input
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search…"
              data-testid="product-system-unified-search"
              className="w-full bg-transparent text-[11px] text-slate-200 outline-none placeholder:text-slate-600"
            />
          </div>
          <div
            className="min-w-0 flex-1 overflow-x-auto scrollbar-thin"
            data-testid="product-system-unified-filter-chips-scroll"
          >
            <div
              className="flex w-max flex-nowrap gap-1 pr-1"
              role="group"
              aria-label="Catalog filters"
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
                    className={`shrink-0 rounded border px-2 py-0.5 text-[10px] font-bold transition-colors ${
                      active
                        ? "border-purple-600/50 bg-purple-950/30 text-purple-100"
                        : "border-slate-800 bg-slate-900/50 text-slate-500 hover:text-slate-300"
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

      <div className="grid gap-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.92fr)] xl:items-start">
        <section data-testid="product-system-unified-results-list" className="space-y-1" role="list">
          <div className="flex items-center justify-between gap-2 px-0.5">
            <h2 className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Catalog buckets</h2>
            <span className="text-[9px] font-bold tabular-nums text-slate-600">{filteredEntries.length}</span>
          </div>
          {loading ? (
            <p className="px-0.5 text-[10px] text-slate-600">Se încarcă catalogul…</p>
          ) : bucketGroups.length === 0 ? (
            <p className="rounded-md border border-dashed border-slate-800 px-2 py-3 text-[11px] text-slate-500">
              Niciun rezultat pentru filtrele curente.
            </p>
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
              />
            ))
          )}
        </section>

        <section
          data-testid="product-system-detail-panel"
          className="min-h-[14rem] rounded-md border border-slate-800/70 bg-slate-950/15 px-2 py-1.5 xl:sticky xl:top-2 xl:max-h-[calc(100vh-140px)] xl:overflow-y-auto"
        >
          {!selectedEntry ? (
            <p className="py-6 text-center text-[11px] text-slate-600">Selectează o intrare pentru detail.</p>
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
