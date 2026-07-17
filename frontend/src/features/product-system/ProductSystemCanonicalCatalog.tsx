import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import { normalizeTemplateCode } from "@/lib/activeTemplateScope";
import {
  buildUnifiedCatalogEntries,
  CANDIDATE_SET_ENTRY_ID,
} from "./buildUnifiedCatalogEntries";
import {
  defaultTemplateDetailSection,
  ProductSystemTemplateDetailPanel,
} from "./ProductSystemTemplateDetailPanel";
import { useProductSystemShell } from "./ProductSystemShellContext";
import {
  CANONICAL_CATALOG_ADVANCED_FILTERS,
  CANONICAL_CATALOG_OPERATOR_FILTERS,
  CANONICAL_READINESS_ROLLUP_LABELS,
  buildCanonicalCatalogProducts,
  filterCanonicalCatalogProducts,
  isOperatorVisibleCatalogProduct,
  sortCanonicalCatalogProducts,
  splitCanonicalCatalogProducts,
  templateEntityForAvailability,
  type CanonicalCatalogFilter,
  type CanonicalCatalogProduct,
} from "./productSystemCanonicalCatalogModel";
import {
  resolveTemplateQuerySelection,
  selectedTemplateCodeFromEntry,
  parseRequestedTemplateCode,
  TEMPLATE_UNAVAILABLE_MESSAGE,
  type TemplateQueryResolution,
} from "./productSystemTemplateQuerySync";
import type {
  UnifiedCatalogDetailSection,
  UnifiedCatalogEntry,
} from "./productSystemUnifiedCatalogTypes";

export type ProductSystemCanonicalCatalogProps = {
  templates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
  loading: boolean;
  search: string;
  onSearchChange: (value: string) => void;
  requestedTemplateCode?: string | null;
  onRequestedTemplateCodeChange?: (code: string | null) => void;
  onOpenTemplate: (template: ProductTemplateEntity) => void;
};

const INTERNAL_TEMPLATE_MESSAGE =
  "Template intern sau indisponibil in catalogul operator.";

function rollupToneClass(rollup: CanonicalCatalogProduct["rollup"]): string {
  switch (rollup) {
    case "READY":
      return "border-emerald-800/50 bg-emerald-950/25 text-emerald-200";
    case "PARTIALLY_READY":
      return "border-amber-800/50 bg-amber-950/25 text-amber-200";
    case "BLOCKED":
      return "border-amber-800/50 bg-amber-950/25 text-amber-200";
    case "INTERNAL":
      return "border-slate-700 bg-slate-900/60 text-slate-300";
    case "DEPRECATED":
      return "border-slate-700 bg-slate-900/60 text-slate-400";
    default:
      return "border-slate-800 bg-slate-900/50 text-slate-300";
  }
}

function resolveCatalogEntryForProduct(
  product: CanonicalCatalogProduct,
  entries: UnifiedCatalogEntry[],
  templates: ProductTemplateEntity[],
): UnifiedCatalogEntry | null {
  const normalized = normalizeTemplateCode(product.templateCode);
  const existing = entries.find(
    (entry) => entry.kind === "template" && normalizeTemplateCode(entry.templateCode) === normalized,
  );
  if (existing) return existing;

  const template = product.template ?? templateEntityForAvailability(product.availability, templates);
  if (!product.availability) return null;

  return {
    id: `template:${template.id}`,
    kind: "template",
    bucket: "current-products",
    name: product.displayName,
    templateCode: product.templateCode,
    entityType: "Canonical product",
    lifecycleLabel: product.availability.ui_label,
    metadata: product.availability.ui_description || "",
    importanceRank: product.availability.importance_rank ?? 50,
    isProduct: true,
    isComponent: false,
    isCandidateReadonly: false,
    isActiveRoot: true,
    isArchived: false,
    isBlocked: product.rollup === "BLOCKED",
    isReadonly: false,
    template,
    availability: product.availability,
  };
}

function isOperatorDeepLinkBlocked(
  entry: UnifiedCatalogEntry,
  canViewAdvanced: boolean,
): boolean {
  if (canViewAdvanced) return false;
  if (entry.availability && isOperatorVisibleCatalogProduct(entry.availability)) return false;
  if (entry.kind === "candidate-set") return true;
  if (entry.bucket === "legacy-shared-modules") return true;
  if (entry.bucket === "archived") return true;
  if (entry.bucket === "candidate-products") return true;
  if (entry.bucket === "component-first-sets") return true;
  if (entry.availability?.readiness?.rollup === "INTERNAL") return true;
  if (entry.availability?.capabilities?.internal_only) return true;
  return false;
}

function CatalogProductCard({
  product,
  selected,
  onSelect,
}: {
  product: CanonicalCatalogProduct;
  selected: boolean;
  onSelect: () => void;
}) {
  const rollupLabel = CANONICAL_READINESS_ROLLUP_LABELS[product.rollup];
  const showBlockerCount =
    product.blockerCount > 0 &&
    (product.rollup === "BLOCKED" || product.rollup === "PARTIALLY_READY");

  return (
    <button
      type="button"
      role="listitem"
      data-testid="product-system-canonical-catalog-card"
      data-template-code={product.templateCode}
      data-readiness-rollup={product.rollup}
      aria-pressed={selected}
      onClick={onSelect}
      className={`w-full rounded-xl border px-3 py-3 text-left transition-colors ${
        selected
          ? "border-purple-600/50 bg-purple-950/20"
          : "border-slate-800/70 bg-slate-950/20 hover:border-slate-700 hover:bg-slate-900/30"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-100">{product.displayName}</p>
          <p className="mt-0.5 truncate text-xs text-slate-500">{product.familyName}</p>
          <p
            className="mt-1 font-mono text-[11px] text-slate-600"
            data-testid="product-system-canonical-card-template-code"
          >
            {product.templateCode}
          </p>
        </div>
        <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-slate-600" aria-hidden />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span
          className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${rollupToneClass(product.rollup)}`}
          data-testid="product-system-canonical-card-commercial-chip"
        >
          {product.commercialChipRo}
        </span>
        <span
          className="rounded-full border border-slate-800 bg-slate-900/60 px-2 py-0.5 text-[11px] font-medium text-slate-400"
          data-testid="product-system-canonical-card-capability"
        >
          {product.capabilityLabel === "Standalone" || product.capabilityLabel === "Both"
            ? "De sine stătător"
            : product.capabilityLabel === "Linked child"
              ? "Copil legat"
              : product.capabilityLabel}
        </span>
        <span
          className="rounded-full border border-slate-800/80 px-2 py-0.5 text-[10px] font-medium text-slate-600"
          data-testid="product-system-canonical-card-readiness-rollup"
          title="Pregătire tehnică — nu înlocuiește chip-ul comercial"
        >
          {rollupLabel}
        </span>
        {showBlockerCount ? (
          <span
            className="rounded-full border border-amber-900/40 bg-amber-950/20 px-2 py-0.5 text-[11px] font-medium text-amber-200"
            data-testid="product-system-canonical-card-blocker-count"
          >
            {product.blockerCount} blocaje
          </span>
        ) : null}
      </div>
    </button>
  );
}

function CatalogListSection({
  title,
  description,
  products,
  selectedTemplateCode,
  onSelectProduct,
  testId,
  emptyMessage,
}: {
  title: string;
  description: string;
  products: CanonicalCatalogProduct[];
  selectedTemplateCode: string | null;
  onSelectProduct: (product: CanonicalCatalogProduct) => void;
  testId: string;
  emptyMessage?: string;
}) {
  if (products.length === 0 && !emptyMessage) return null;

  return (
    <section data-testid={testId} className="space-y-2">
      <div className="px-1">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
        <p className="mt-0.5 text-xs text-slate-600">{description}</p>
      </div>
      {products.length === 0 ? (
        <p className="px-1 text-xs text-slate-500">{emptyMessage}</p>
      ) : (
        <div className="space-y-2" role="list">
          {products.map((product) => (
            <CatalogProductCard
              key={product.id}
              product={product}
              selected={
                selectedTemplateCode != null &&
                normalizeTemplateCode(selectedTemplateCode) ===
                  normalizeTemplateCode(product.templateCode)
              }
              onSelect={() => onSelectProduct(product)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export function ProductSystemCanonicalCatalog({
  templates,
  availabilityItems,
  loading,
  search,
  onSearchChange,
  requestedTemplateCode,
  onRequestedTemplateCodeChange,
  onOpenTemplate,
}: ProductSystemCanonicalCatalogProps) {
  const { canViewAdvanced, operatorReadOnly } = useProductSystemShell();
  const [filter, setFilter] = useState<CanonicalCatalogFilter>("all");
  const [selectedEntry, setSelectedEntry] = useState<UnifiedCatalogEntry | null>(null);
  const [templateDetailSection, setTemplateDetailSection] =
    useState<UnifiedCatalogDetailSection>(defaultTemplateDetailSection);
  const [templateQueryMessage, setTemplateQueryMessage] = useState<string | null>(null);
  const deepLinkHandledRef = useRef<string | null>(null);

  const entries = useMemo(
    () => buildUnifiedCatalogEntries({ templates, availabilityItems }),
    [templates, availabilityItems],
  );

  const entryById = useMemo(() => new Map(entries.map((entry) => [entry.id, entry])), [entries]);

  const allProducts = useMemo(
    () => buildCanonicalCatalogProducts({ templates, availabilityItems }),
    [templates, availabilityItems],
  );

  const filteredProducts = useMemo(
    () =>
      sortCanonicalCatalogProducts(
        filterCanonicalCatalogProducts(allProducts, {
          filter,
          search,
          canViewAdvanced,
        }),
      ),
    [allProducts, filter, search, canViewAdvanced],
  );

  const isAdvancedFilter = CANONICAL_CATALOG_ADVANCED_FILTERS.some((chip) => chip.id === filter);

  const { operator: operatorProducts, advanced: advancedProducts } = useMemo(() => {
    if (isAdvancedFilter) {
      return { operator: [], advanced: filteredProducts };
    }
    if (filter !== "all") {
      return { operator: filteredProducts, advanced: [] };
    }
    return splitCanonicalCatalogProducts(allProducts, search);
  }, [allProducts, filter, filteredProducts, isAdvancedFilter, search]);

  const normalizedRequestedCode = requestedTemplateCode
    ? normalizeTemplateCode(requestedTemplateCode)
    : null;

  const selectEntry = (entry: UnifiedCatalogEntry) => {
    setSelectedEntry(entry);
    setTemplateQueryMessage(null);
    setTemplateDetailSection(defaultTemplateDetailSection);
    const code = selectedTemplateCodeFromEntry(entry);
    onRequestedTemplateCodeChange?.(code);
  };

  const selectProduct = (product: CanonicalCatalogProduct) => {
    const entry = resolveCatalogEntryForProduct(product, entries, templates);
    if (entry) selectEntry(entry);
  };

  useEffect(() => {
    const requested = requestedTemplateCode?.trim() ?? "";
    if (!requested) {
      deepLinkHandledRef.current = null;
      return;
    }
    if (deepLinkHandledRef.current === requested) return;

    const normalized = parseRequestedTemplateCode(requested);
    if (!normalized) return;
    if (loading) return;

    const catalogProduct = buildCanonicalCatalogProducts({ templates, availabilityItems }).find(
      (product) => normalizeTemplateCode(product.templateCode) === normalized,
    );

    const trySelectCatalogProduct = (): boolean => {
      const availability = availabilityItems.find(
        (item) => normalizeTemplateCode(item.template_code) === normalized,
      );
      const product =
        catalogProduct ??
        (availability
          ? buildCanonicalCatalogProducts({ templates, availabilityItems }).find(
              (row) => normalizeTemplateCode(row.templateCode) === normalized,
            )
          : undefined);
      if (!product) return false;
      if (!product.operatorVisible) return false;
      const resolved = resolveCatalogEntryForProduct(product, entries, templates);
      if (!resolved || isOperatorDeepLinkBlocked(resolved, canViewAdvanced)) return false;
      selectEntry(resolved);
      return true;
    };

    const resolution: TemplateQueryResolution = resolveTemplateQuerySelection(
      requested,
      entries,
      availabilityItems,
    );

    deepLinkHandledRef.current = requested;

    if (resolution.kind === "none") {
      trySelectCatalogProduct();
      return;
    }

    if (resolution.kind === "unavailable") {
      if (trySelectCatalogProduct()) return;
      setSelectedEntry(null);
      setTemplateQueryMessage(TEMPLATE_UNAVAILABLE_MESSAGE);
      return;
    }

    const entry =
      entryById.get(resolution.entryId) ??
      (catalogProduct ? resolveCatalogEntryForProduct(catalogProduct, entries, templates) : null);

    if (!entry) {
      if (trySelectCatalogProduct()) return;
      setSelectedEntry(null);
      setTemplateQueryMessage(TEMPLATE_UNAVAILABLE_MESSAGE);
      return;
    }

    if (isOperatorDeepLinkBlocked(entry, canViewAdvanced)) {
      if (trySelectCatalogProduct()) return;
      setSelectedEntry(null);
      setTemplateQueryMessage(INTERNAL_TEMPLATE_MESSAGE);
      return;
    }

    selectEntry(entry);
  }, [
    requestedTemplateCode,
    entries,
    availabilityItems,
    entryById,
    canViewAdvanced,
    onRequestedTemplateCodeChange,
    templates,
    loading,
  ]);

  const visibleCount = operatorProducts.length + (canViewAdvanced ? advancedProducts.length : 0);
  const hasSearchOrFilter = search.trim().length > 0 || filter !== "all";
  const showOperatorEmpty =
    !loading && operatorProducts.length === 0 && !hasSearchOrFilter && filter === "all";
  const showFilteredEmpty = !loading && visibleCount === 0 && hasSearchOrFilter;

  return (
    <div
      className="space-y-4"
      data-testid="product-system-unified-catalog"
      data-catalog-variant="canonical"
      data-layout="comfortable"
    >
      <div
        className="space-y-2 rounded-xl border border-slate-800/70 bg-slate-950/20 px-3 py-2"
        data-testid="product-system-catalog-toolbar"
      >
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Catalog produse</h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Produse operationale canonice — un singur catalog, fara bucket-uri legacy.
            </p>
          </div>
          <span
            className="self-start rounded-full border border-slate-800 bg-slate-950/60 px-2.5 py-1 text-[11px] font-bold tabular-nums text-slate-400"
            data-testid="product-system-canonical-catalog-count"
          >
            {loading ? "…" : visibleCount}
          </span>
        </div>

        <div data-testid="product-system-canonical-search">
          <label className="sr-only" htmlFor="product-system-canonical-search-input">
            Cauta produse
          </label>
          <input
            id="product-system-canonical-search-input"
            type="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Cauta dupa nume, cod template sau familie…"
            data-testid="product-system-canonical-search-input"
            className="w-full rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-purple-700/50 focus:outline-none"
          />
        </div>

        <div
          className="min-w-0 overflow-x-auto xl:overflow-visible"
          data-testid="product-system-canonical-filter-chips-scroll"
        >
          <div
            className="flex w-max flex-nowrap gap-1.5 pr-1 xl:w-auto xl:flex-wrap"
            role="group"
            aria-label="Filtre catalog"
            data-testid="product-system-canonical-filter-chips"
          >
            {CANONICAL_CATALOG_OPERATOR_FILTERS.map((chip) => {
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
            {canViewAdvanced
              ? CANONICAL_CATALOG_ADVANCED_FILTERS.map((chip) => {
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
                          ? "border-slate-600/50 bg-slate-900/70 text-slate-200"
                          : "border-slate-800 bg-slate-900/50 text-slate-500 hover:border-slate-700 hover:text-slate-300"
                      }`}
                    >
                      {chip.label}
                    </button>
                  );
                })
              : null}
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,0.44fr)_minmax(0,0.56fr)] xl:items-start">
        <section data-testid="product-system-canonical-results-list" className="space-y-4">
          {loading ? (
            <p className="px-1 text-sm text-slate-500">Se incarca catalogul…</p>
          ) : showOperatorEmpty ? (
            <div
              className="rounded-xl border border-dashed border-slate-800 px-4 py-8 text-center"
              data-testid="product-system-canonical-empty-operational"
            >
              <p className="text-sm font-medium text-slate-300">Nu exista produse operationale disponibile.</p>
            </div>
          ) : showFilteredEmpty ? (
            <div
              className="rounded-xl border border-dashed border-slate-800 px-4 py-8 text-center"
              data-testid="product-system-canonical-empty-filtered"
            >
              <p className="text-sm font-medium text-slate-300">
                Niciun produs nu corespunde cautarii sau filtrelor selectate.
              </p>
            </div>
          ) : (
            <>
              <CatalogListSection
                title="Produse operationale"
                description="Template-uri active expuse operatorului."
                products={operatorProducts}
                selectedTemplateCode={selectedTemplateCodeFromEntry(selectedEntry)}
                onSelectProduct={selectProduct}
                testId="product-system-canonical-operator-list"
              />
              {canViewAdvanced && filter === "all" && advancedProducts.length > 0 ? (
                <CatalogListSection
                  title="Catalog Advanced"
                  description="Intern, depreciat sau experimental — doar governance."
                  products={advancedProducts}
                  selectedTemplateCode={selectedTemplateCodeFromEntry(selectedEntry)}
                  onSelectProduct={selectProduct}
                  testId="product-system-canonical-advanced-list"
                />
              ) : null}
              {canViewAdvanced && isAdvancedFilter ? (
                <CatalogListSection
                  title="Rezultate Advanced"
                  description="Obiecte non-operator filtrate explicit."
                  products={filteredProducts}
                  selectedTemplateCode={selectedTemplateCodeFromEntry(selectedEntry)}
                  onSelectProduct={selectProduct}
                  testId="product-system-canonical-advanced-filtered-list"
                />
              ) : null}
            </>
          )}
        </section>

        <section
          data-testid="product-system-detail-panel"
          className="min-h-[22rem] rounded-xl border border-slate-800/70 bg-slate-950/20 p-4 xl:sticky xl:top-3 xl:max-h-[calc(100vh-148px)] xl:overflow-y-auto"
        >
          {templateQueryMessage ? (
            <div
              data-testid="product-system-template-query-unavailable"
              className="flex h-full min-h-[18rem] flex-col items-center justify-center px-4 text-center"
            >
              <p className="text-sm font-medium text-amber-200">{templateQueryMessage}</p>
              {normalizedRequestedCode ? (
                <p className="mt-2 font-mono text-xs text-slate-500">{normalizedRequestedCode}</p>
              ) : null}
              <p className="mt-3 max-w-sm text-xs leading-relaxed text-slate-500">
                Selecteaza un produs activ din catalog sau verifica codul template-ului solicitat.
              </p>
            </div>
          ) : !selectedEntry || selectedEntry.kind === "candidate-set" ? (
            <div className="flex h-full min-h-[18rem] flex-col items-center justify-center px-4 text-center">
              <p className="text-sm font-medium text-slate-300">Nicio intrare selectata</p>
              <p className="mt-1 max-w-xs text-xs leading-relaxed text-slate-500">
                Alege un produs din catalog pentru a vedea context, compozitie si garduri.
              </p>
            </div>
          ) : selectedEntry.template && selectedEntry.availability ? (
            <ProductSystemTemplateDetailPanel
              template={selectedEntry.template}
              availability={selectedEntry.availability}
              catalogBucket={selectedEntry.bucket}
              section={templateDetailSection}
              onSectionChange={setTemplateDetailSection}
              onOpenEditor={operatorReadOnly ? undefined : () => onOpenTemplate(selectedEntry.template!)}
              rowMetadata={selectedEntry.metadata}
            />
          ) : null}
        </section>
      </div>
    </div>
  );
}

export { CANDIDATE_SET_ENTRY_ID };
