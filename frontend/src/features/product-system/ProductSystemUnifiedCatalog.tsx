import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ChevronDown, ChevronRight, Search } from "lucide-react";
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

function CatalogRowAction({
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
      className="rounded-md border border-slate-700 bg-slate-900/80 px-2 py-1 text-[11px] font-bold text-cyan-200 hover:border-cyan-600/40 hover:bg-cyan-950/40"
    >
      {label}
    </button>
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
      className={`rounded-lg border px-3 py-2.5 transition-colors ${
        selected
          ? "border-purple-500/50 bg-purple-950/20 ring-1 ring-purple-500/20"
          : "border-slate-800/90 bg-[#111827] hover:border-slate-600/50"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-[15px] font-bold text-slate-100">{entry.name}</p>
          <p className="font-mono text-[11px] text-slate-300">{entry.templateCode}</p>
          <div className="mt-1.5 flex flex-wrap gap-1">
            <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-[11px] font-bold text-slate-300">
              {entry.entityType}
            </span>
            <span
              className={`rounded border px-1.5 py-0.5 text-[11px] font-bold ${
                entry.bucket === "component-first-sets"
                  ? "border-cyan-700/40 bg-cyan-950/40 text-cyan-200"
                  : entry.bucket === "current-products"
                    ? "border-emerald-700/40 bg-emerald-950/30 text-emerald-200"
                    : entry.bucket === "candidate-products"
                      ? "border-amber-700/40 bg-amber-950/30 text-amber-200"
                      : entry.bucket === "legacy-shared-modules"
                        ? "border-slate-600/50 bg-slate-900 text-slate-400"
                        : "border-slate-700 bg-slate-900 text-slate-400"
              }`}
            >
              {entry.lifecycleLabel}
            </span>
            {entry.isBlocked ? (
              <span className="rounded border border-amber-700/40 bg-amber-950/30 px-1.5 py-0.5 text-[11px] font-bold text-amber-200">
                Owner GO
              </span>
            ) : null}
          </div>
          {entry.metadata ? <p className="mt-1.5 line-clamp-2 text-[12px] text-slate-400">{entry.metadata}</p> : null}
        </div>
        <div className="flex flex-wrap items-center justify-end gap-1.5">
          <CatalogRowAction label={actions.open} testId={`${rowTestId}-action-open`} onClick={onOpen} />
          <CatalogRowAction
            label={actions.settings}
            testId={`${rowTestId}-action-settings`}
            onClick={onSettings}
          />
          <CatalogRowAction label={actions.dossier} testId={`${rowTestId}-action-dossier`} onClick={onDossier} />
          {actions.components ? (
            <CatalogRowAction
              label={actions.components}
              testId={`${rowTestId}-action-components`}
              onClick={onComponents}
            />
          ) : null}
          <CatalogRowAction label={actions.guards} testId={`${rowTestId}-action-guards`} onClick={onGuards} />
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
  return (
    <section
      data-testid={group.bucket.testId}
      data-expanded={expanded ? "true" : "false"}
      className="rounded-xl border border-slate-800/80 bg-slate-950/20"
    >
      <button
        type="button"
        data-testid={group.bucket.toggleTestId}
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-left"
      >
        <span className="flex items-center gap-2">
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-slate-400" />
          )}
          <span className="text-[13px] font-bold text-slate-100">{group.bucket.label}</span>
        </span>
        <span className="text-[11px] font-bold text-slate-500">{group.entries.length} entries</span>
      </button>
      {expanded ? (
        <div className="space-y-2 border-t border-slate-800/80 px-2 pb-2 pt-2">
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
  catalogOverview: ReactNode;
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
    <div className="space-y-4" data-testid="product-system-unified-catalog">
      {catalogOverview}

      <section
        data-testid="product-system-summary-bar"
        className="rounded-xl border border-slate-800/80 bg-slate-950/30 px-4 py-2.5"
      >
        <p className="text-[12px] text-slate-400">
          <span className="font-bold text-slate-200">{summary.products}</span> product roots ·{" "}
          <span className="font-bold text-slate-200">{summary.components}</span> legacy modules ·{" "}
          <span className="font-bold text-slate-200">{summary.candidateSets}</span> component-first sets
          {summary.dossiers != null ? (
            <>
              {" "}
              · <span className="font-bold text-slate-200">{summary.dossiers}</span> dossier contracts
            </>
          ) : null}
          {summary.blocked != null ? (
            <>
              {" "}
              · <span className="font-bold text-amber-200">{summary.blocked}</span> blocked / owner GO
            </>
          ) : null}
          {" · "}
          <span className="font-bold text-slate-200">{summary.archived}</span> archived
        </p>
      </section>

      <section
        data-testid="product-system-unified-search-filter"
        className="rounded-xl border border-slate-800/80 bg-slate-950/30 px-4 py-3"
      >
        <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2">
          <Search className="h-4 w-4 shrink-0 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search template code, bucket, lifecycle…"
            data-testid="product-system-unified-search"
            className="w-full bg-transparent text-[13px] text-slate-200 outline-none placeholder:text-slate-600"
          />
        </div>
        <div
          className="mt-3 flex flex-wrap gap-1.5"
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
                className={`rounded-md border px-2.5 py-1 text-[12px] font-bold transition-colors ${
                  active
                    ? "border-purple-500/50 bg-purple-500/10 text-purple-100"
                    : "border-slate-700 bg-slate-900/70 text-slate-300 hover:border-purple-500/30"
                }`}
              >
                {chip.label}
              </button>
            );
          })}
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <section data-testid="product-system-unified-results-list" className="space-y-3" role="list">
          <div className="flex items-center justify-between gap-2 px-1">
            <h2 className="text-[14px] font-bold text-slate-100">Catalog buckets</h2>
            <span className="text-[11px] font-bold text-slate-500">{filteredEntries.length} entries</span>
          </div>
          {loading ? (
            <p className="px-1 text-[12px] text-slate-500">Se încarcă catalogul…</p>
          ) : bucketGroups.length === 0 ? (
            <p className="rounded-lg border border-dashed border-slate-700 px-3 py-4 text-[12px] text-slate-500">
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
          className="min-h-[24rem] rounded-xl border border-slate-800/80 bg-slate-950/20 px-4 py-3"
        >
          {!selectedEntry ? (
            <p className="text-[12px] text-slate-500">Select a catalog entry to view detail, dossier, and guards.</p>
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
            />
          ) : null}
        </section>
      </div>
    </div>
  );
}

export { CANDIDATE_SET_ENTRY_ID };
