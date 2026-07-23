import type { ReactNode } from "react";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import {
  TemplateLibraryView,
  type CatalogDensity,
  type ProductSystemCatalogView,
  type TemplateLibraryRowSummary,
} from "@/features/product-system/TemplateLibraryView";
import type { LibraryTab } from "@/features/product-system/productSystemNavigation";
import {
  getDefaultProductSystemPrimaryTab,
  PRODUCT_SYSTEM_PRIMARY_TABS,
  type ProductSystemPrimaryTab,
} from "@/features/product-system/productSystemCatalogShellTypes";
import { CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE } from "@/features/product-system/candidateModuleProdusReadonlyDossierAlignment";

export type ProductSystemCatalogSummary = {
  products: number;
  components: number;
  candidateSets: number;
  dossiers: number | null;
  dossiersLabel: string;
  blocked: number | null;
  archived: number;
};

type ProductSystemCatalogShellProps = {
  primaryTab: ProductSystemPrimaryTab;
  onPrimaryTabChange: (tab: ProductSystemPrimaryTab) => void;
  summary: ProductSystemCatalogSummary;
  catalogOverview: ReactNode;
  candidateSetsPanel: ReactNode | null;
  hasCandidateModuleProdusCandidate: boolean;
  templates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
  libraryTab: LibraryTab;
  onLibraryTabChange: (tab: LibraryTab) => void;
  librarySearch: string;
  onLibrarySearchChange: (value: string) => void;
  catalogView: ProductSystemCatalogView;
  onCatalogViewChange: (view: ProductSystemCatalogView) => void;
  catalogDensity: CatalogDensity;
  onCatalogDensityChange: (density: CatalogDensity) => void;
  summaries: Map<number, TemplateLibraryRowSummary>;
  recommendedTemplateId: number | null;
  activeCount: number;
  archivedCount: number;
  loading: boolean;
  onOpenTemplate: (template: ProductTemplateEntity) => void;
};

function SummaryMetric({
  label,
  value,
  testId,
  muted = false,
}: {
  label: string;
  value: string;
  testId: string;
  muted?: boolean;
}) {
  return (
    <div
      data-testid={testId}
      className={`rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-2 ${muted ? "opacity-80" : ""}`}
    >
      <p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-0.5 text-[15px] font-bold text-slate-100">{value}</p>
    </div>
  );
}

function ReadonlyPlaceholder({
  title,
  testId,
  children,
}: {
  title: string;
  testId: string;
  children: ReactNode;
}) {
  return (
    <section
      data-testid={testId}
      className="rounded-xl border border-slate-800/80 bg-slate-950/30 px-4 py-4"
    >
      <h2 className="text-[15px] font-bold text-slate-100">{title}</h2>
      <div className="mt-2 space-y-2 text-[12px] leading-relaxed text-slate-400">{children}</div>
    </section>
  );
}

function TemplateLibraryPanel({
  shellContextLabel,
  restrictCatalogView,
  ...props
}: Omit<ProductSystemCatalogShellProps, "primaryTab" | "onPrimaryTabChange" | "summary" | "catalogOverview" | "candidateSetsPanel" | "hasCandidateModuleProdusCandidate"> & {
  shellContextLabel: string;
  restrictCatalogView?: ProductSystemCatalogView;
}) {
  return (
    <TemplateLibraryView
      templates={props.templates}
      availabilityItems={props.availabilityItems}
      tab={props.libraryTab}
      onTabChange={props.onLibraryTabChange}
      search={props.librarySearch}
      onSearchChange={props.onLibrarySearchChange}
      catalogView={props.catalogView}
      onCatalogViewChange={props.onCatalogViewChange}
      density={props.catalogDensity}
      onDensityChange={props.onCatalogDensityChange}
      summaries={props.summaries}
      recommendedTemplateId={props.recommendedTemplateId}
      activeCount={props.activeCount}
      archivedCount={props.archivedCount}
      loading={props.loading}
      onOpenTemplate={props.onOpenTemplate}
      shellContextLabel={shellContextLabel}
      restrictCatalogView={restrictCatalogView}
    />
  );
}

export function buildProductSystemCatalogSummary({
  catalogCounts,
  archivedCount,
  hasCandidateModuleProdusCandidate,
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
  hasCandidateModuleProdusCandidate: boolean;
  ownerDecisionRequiredCount: number;
}): ProductSystemCatalogSummary {
  const products = catalogCounts.activeProducts + catalogCounts.candidateProducts;
  const components = catalogCounts.internalModules + catalogCounts.sharedComponents;
  const candidateSets = hasCandidateModuleProdusCandidate ? 1 : 0;
  const dossiers = hasCandidateModuleProdusCandidate ? CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE.length : null;
  const dossiersLabel = hasCandidateModuleProdusCandidate
    ? `${CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE.length} readonly contracts (candidate set)`
    : "Unavailable — open Seturi Module produs when present";
  const blocked = ownerDecisionRequiredCount > 0 ? ownerDecisionRequiredCount : null;
  const archived = catalogCounts.archivedExperimental > 0 ? catalogCounts.archivedExperimental : archivedCount;

  return {
    products,
    components,
    candidateSets,
    dossiers,
    dossiersLabel,
    blocked,
    archived,
  };
}

export function ProductSystemCatalogShell(props: ProductSystemCatalogShellProps) {
  const {
    primaryTab,
    onPrimaryTabChange,
    summary,
    catalogOverview,
    candidateSetsPanel,
    hasCandidateModuleProdusCandidate,
  } = props;

  return (
    <div className="space-y-4" data-testid="product-system-catalog-shell-layout">
      {catalogOverview}

      <section
        data-testid="product-system-summary-bar"
        className="rounded-xl border border-slate-800/80 bg-slate-950/30 px-4 py-3"
      >
        <h2 className="text-[14px] font-bold text-slate-100">Catalog summary</h2>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
          <SummaryMetric
            label="Products"
            value={String(summary.products)}
            testId="product-system-summary-products-count"
          />
          <SummaryMetric
            label="Module produs"
            value={String(summary.components)}
            testId="product-system-summary-components-count"
          />
          <SummaryMetric
            label="Seturi Module produs"
            value={String(summary.candidateSets)}
            testId="product-system-summary-candidate-sets-count"
          />
          <SummaryMetric
            label="Dossiers"
            value={summary.dossiers == null ? "Unavailable" : String(summary.dossiers)}
            testId="product-system-summary-dossiers-count"
            muted={summary.dossiers == null}
          />
          {summary.blocked != null ? (
            <SummaryMetric
              label="Blocked / owner GO"
              value={String(summary.blocked)}
              testId="product-system-summary-blocked-count"
            />
          ) : null}
          <SummaryMetric
            label="Archived"
            value={String(summary.archived)}
            testId="product-system-summary-archived-count"
          />
        </div>
        {summary.dossiers != null ? (
          <p className="mt-2 text-[11px] text-slate-500">{summary.dossiersLabel}</p>
        ) : null}
      </section>

      <div
        className="flex flex-wrap gap-1.5"
        role="tablist"
        aria-label="Product System primary catalog tabs"
        data-testid="product-system-primary-tabs"
      >
        {PRODUCT_SYSTEM_PRIMARY_TABS.map((tab) => {
          const active = primaryTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={active}
              data-testid={tab.testId}
              onClick={() => onPrimaryTabChange(tab.id)}
              className={`rounded-md border px-3 py-1.5 text-[12px] font-bold transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500/40 ${
                active
                  ? "border-purple-500/50 bg-purple-500/10 text-purple-100"
                  : "border-slate-700 bg-slate-900/70 text-slate-300 hover:border-purple-500/30 hover:text-purple-200"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {primaryTab === "products" ? (
        <section
          data-testid="product-system-existing-roots"
          className="rounded-xl border border-purple-900/30 bg-slate-950/20 px-4 py-3"
        >
          <h2 className="text-[15px] font-bold text-slate-100">Active catalog roots / existing templates</h2>
          <p className="mt-1 text-[12px] text-slate-400">
            Offerable and in-preparation product roots including TPL-VOLUMETRIC-LETTERS_v2. Candidate readonly sets
            live in the Seturi Module produs tab.
          </p>
          <div className="mt-3">
            <TemplateLibraryPanel
              {...props}
              shellContextLabel="Active catalog roots / existing templates"
            />
          </div>
        </section>
      ) : null}

      {primaryTab === "components" ? (
        <section data-testid="product-system-components-tab-panel" className="space-y-3">
          <div className="rounded-xl border border-cyan-900/30 bg-slate-950/20 px-4 py-3">
            <h2 className="text-[15px] font-bold text-cyan-100">Module produs / Module partajate</h2>
            <p className="mt-1 text-[12px] text-cyan-200/70">
              Catalog Module produs egale sub Product Template — design-time only. Mini-modulul operațional e separat.
            </p>
          </div>
          <TemplateLibraryPanel
            {...props}
            shellContextLabel="Module produs / Module partajate"
            restrictCatalogView="components"
          />
        </section>
      ) : null}

      {primaryTab === "candidate-sets" ? (
        <section
          data-testid="product-system-candidate-sets"
          className="rounded-xl border border-cyan-900/40 bg-slate-950/20 px-4 py-3"
        >
          <h2 className="text-[15px] font-bold text-cyan-100">Seturi Module produs</h2>
          <p className="mt-1 text-[12px] text-cyan-200/70">
            Readonly parallel sets (Product Template + Module produs egale) — not in Work Intake, not offerable, no activation controls.
          </p>
          <div className="mt-3">
            {candidateSetsPanel ?? (
              <p className="text-[12px] text-slate-500">No readonly candidate sets in the current catalog.</p>
            )}
          </div>
        </section>
      ) : null}

      {primaryTab === "dossiers" ? (
        <ReadonlyPlaceholder title="Dossiers" testId="product-system-dossiers-tab-panel">
          <p>Design-time dossier readiness only — no runtime dossier activation or write path.</p>
          {hasCandidateModuleProdusCandidate ? (
            <>
              <p>
                Candidate Module produs — Litere expune{" "}
                <strong className="text-slate-200">{CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE.length}</strong> contracte
                dossier readonly (Product Template + Module produs).
              </p>
              <p>
                Open <strong className="text-cyan-200">Seturi Module produs</strong> → View candidate readonly → Dossier tab
                for the full readonly workspace.
              </p>
            </>
          ) : (
            <p>Dossier contract counts unavailable until a candidate set is present in catalog.</p>
          )}
        </ReadonlyPlaceholder>
      ) : null}

      {primaryTab === "guards-audit" ? (
        <ReadonlyPlaceholder title="Guards / Audit" testId="product-system-guards-audit-tab-panel">
          <p>Cross-entity guard and audit index — readonly catalog boundary checks only.</p>
          {hasCandidateModuleProdusCandidate ? (
            <p>
              Candidate Module produs — Litere include completeness, drift, Product Compiler readiness și guard-uri
              runtime interzise. Open <strong className="text-cyan-200">Seturi Module produs</strong> → Guards / Audit for
              detail.
            </p>
          ) : (
            <p>No candidate guard bundle loaded in the current catalog view.</p>
          )}
          <p className="text-[11px] text-slate-500">
            No activation, no Work Intake exposure, no Pricing / Quote / Order / Execution wiring from this surface.
          </p>
        </ReadonlyPlaceholder>
      ) : null}

      {primaryTab === "archived" ? (
        <section data-testid="product-system-archived-tab-panel" className="space-y-3">
          <div className="rounded-xl border border-slate-800/80 bg-slate-950/20 px-4 py-3">
            <h2 className="text-[15px] font-bold text-slate-100">Archived / experimental templates</h2>
            <p className="mt-1 text-[12px] text-slate-400">
              Templates removed from active offerable flow — historical and experimental entries only.
            </p>
          </div>
          <TemplateLibraryPanel
            {...props}
            shellContextLabel="Archived / experimental templates"
            restrictCatalogView="archived"
          />
        </section>
      ) : null}
    </div>
  );
}

export { getDefaultProductSystemPrimaryTab };
