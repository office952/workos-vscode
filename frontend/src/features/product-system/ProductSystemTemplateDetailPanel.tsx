import { Link } from "react-router-dom";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import { StatusBadge } from "@/components/workos/design-system";
import {
  LETTERS_TEMPLATE_CODE,
  LOGO_TEMPLATE_CODE,
  getProductTemplateScopePresentation,
} from "@/lib/productTemplateScopePresentation";
import {
  getProductModularityTruth,
  MODULARITY_LAW_LINES_RO,
  SETTINGS_OWNERSHIP_CONFLICT_RO,
} from "@/lib/productSystemModularityTruth";
import type {
  UnifiedCatalogBucketId,
  UnifiedCatalogDetailSection,
} from "./productSystemUnifiedCatalogTypes";
import { LegacyReplacementReadinessPanel } from "./LegacyReplacementReadinessPanel";
import { FinishMountingOwnershipPanel } from "./FinishMountingOwnershipPanel";
import { TemplateLifecycleReadinessPanel } from "./TemplateLifecycleReadinessPanel";
import { ProductE2EReadinessPanel } from "./ProductE2EReadinessPanel";
import { ProductTemplatePublicationPanel } from "./ProductTemplatePublicationPanel";
import { ArtworkAnalysisReviewPanel } from "./ArtworkAnalysisReviewPanel";

const PRODUCT_SECTIONS: Array<{ id: UnifiedCatalogDetailSection; label: string; testId: string }> = [
  { id: "overview", label: "Prezentare", testId: "product-system-template-detail-tab-overview" },
  { id: "composition", label: "Compoziție", testId: "product-system-template-detail-tab-composition" },
  { id: "components", label: "Componente", testId: "product-system-template-detail-tab-components" },
  { id: "dossier", label: "Dossier", testId: "product-system-template-detail-tab-dossier" },
  { id: "lifecycle", label: "Lifecycle", testId: "product-system-template-detail-tab-lifecycle" },
  { id: "guards", label: "Garduri", testId: "product-system-template-detail-tab-guards" },
];

const COMPONENT_SECTIONS: Array<{ id: UnifiedCatalogDetailSection; label: string; testId: string }> = [
  { id: "overview", label: "Prezentare", testId: "product-system-template-detail-tab-overview" },
  { id: "dossier", label: "Dossier", testId: "product-system-template-detail-tab-dossier" },
  { id: "lifecycle", label: "Lifecycle", testId: "product-system-template-detail-tab-lifecycle" },
  { id: "fields", label: "Câmpuri", testId: "product-system-template-detail-tab-fields" },
  { id: "product-truth-paths", label: "Product Truth", testId: "product-system-template-detail-tab-product-truth-paths" },
  { id: "guards", label: "Garduri", testId: "product-system-template-detail-tab-guards" },
];

function bucketOverviewCopy(
  templateCode: string,
  bucket: UnifiedCatalogBucketId,
  availability: ProductTemplateAvailabilityItem,
): { headline: string; bullets: string[] } {
  const scope = getProductTemplateScopePresentation(availability);
  const modularity = getProductModularityTruth(templateCode);

  if (modularity) {
    return {
      headline: modularity.headlineRo,
      bullets: [
        ...modularity.summaryChipsRo,
        scope.shortDescription,
        "Dossier / BOM / child template ≠ dovadă de modularitate — doar comportament independent.",
      ],
    };
  }

  if (templateCode === LETTERS_TEMPLATE_CODE || bucket === "current-products") {
    return {
      headline: "Rădăcină folosită azi",
      bullets: [
        "Produs ofertabil folosit în Work Intake.",
        "Compoziția folosește module legacy partajate — nu TPL-COMP-* component-first.",
        "Separat de setul candidate component-first Letters.",
      ],
    };
  }

  if (templateCode === LOGO_TEMPLATE_CODE || bucket === "candidate-products") {
    return {
      headline: "Candidat · rădăcină blocată",
      bullets: [
        "Necesită decizie owner înainte de orice cale directă ofertabilă.",
        "Doar compoziție linked / analyzer — fără activare Logo din catalog.",
        "Nu este un Product Composer component-first.",
      ],
    };
  }

  if (bucket === "legacy-shared-modules") {
    return {
      headline: "Modul intern legacy",
      bullets: [
        "Folosit de compoziția produsului părinte — nu e rădăcină ofertabilă standalone.",
        "Nu este template component-first TPL-COMP-*.",
        "Contract readonly de readiness în catalog — nu execuție runtime.",
      ],
    };
  }

  return {
    headline: scope.catalogStatusLabel,
    bullets: [scope.shortDescription, scope.rootDirectLabel],
  };
}

function ModularityHonestySection({ templateCode }: { templateCode: string }) {
  const truth = getProductModularityTruth(templateCode);
  if (!truth) return null;

  return (
    <section
      data-testid="product-system-template-modularity-truth"
      className="space-y-4 rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-200"
    >
      {truth.showModularityLaw ? (
        <div
          data-testid="product-system-modularity-law"
          className="rounded-lg border border-purple-900/40 bg-purple-950/20 px-3 py-2 text-[12px] text-purple-100/90"
        >
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-purple-300/80">
            Legea modularității
          </p>
          <ul className="space-y-0.5">
            {MODULARITY_LAW_LINES_RO.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-1.5" data-testid="product-system-modularity-summary-chips">
        {truth.summaryChipsRo.map((chip) => (
          <span
            key={chip}
            className="rounded-full border border-slate-700/80 bg-slate-900/50 px-2 py-0.5 text-[11px] font-medium text-slate-300"
          >
            {chip}
          </span>
        ))}
      </div>

      <div data-testid="product-system-honesty-axes">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Axe de adevăr (read-only)
        </p>
        <dl className="grid gap-2 sm:grid-cols-2">
          {truth.axes.map((row) => (
            <div
              key={row.axis}
              data-testid={row.testId}
              className="rounded-md border border-slate-800/60 bg-slate-950/30 px-2.5 py-2"
            >
              <dt className="text-[10px] uppercase text-slate-500">{row.axis}</dt>
              <dd className="mt-0.5 text-[12px] text-slate-200">{row.valueRo}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div data-testid="product-system-module-independence">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Independență module
        </p>
        <ul className="space-y-2">
          {truth.modules.map((mod) => (
            <li
              key={mod.moduleKey}
              data-testid={`product-system-module-truth-${mod.moduleKey}`}
              className="rounded-md border border-slate-800/60 px-2.5 py-2"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-medium text-slate-100">{mod.labelRo}</span>
                <span className="text-[11px] text-slate-400">{mod.independenceRo}</span>
              </div>
              {mod.scopeRo ? (
                <p className="mt-1 text-[11px] text-slate-500">Scope: {mod.scopeRo}</p>
              ) : null}
              {mod.noteRo ? <p className="mt-1 text-[11px] text-slate-500">{mod.noteRo}</p> : null}
            </li>
          ))}
        </ul>
      </div>

      {truth.falseGeneric.length > 0 ? (
        <div data-testid="product-system-false-generic-modules">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Module cu nume generic — scope real
          </p>
          <ul className="space-y-2">
            {truth.falseGeneric.map((mod) => (
              <li
                key={mod.moduleKey}
                data-testid={`product-system-false-generic-${mod.moduleKey}`}
                className="rounded-md border border-amber-900/30 bg-amber-950/10 px-2.5 py-2"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-mono text-xs text-amber-100/90">{mod.labelRo}</span>
                  <span className="text-[11px] text-amber-200/80">{mod.independenceRo}</span>
                </div>
                {mod.noteRo ? <p className="mt-1 text-[11px] text-amber-200/70">{mod.noteRo}</p> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {truth.compositionDependencies.length > 0 ? (
        <div data-testid="product-system-composition-dependencies">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Dependențe de compoziție
          </p>
          <ul className="space-y-2">
            {truth.compositionDependencies.map((dep) => (
              <li
                key={`${dep.sourceRo}-${dep.dependencyRo}`}
                data-testid={`product-system-dep-${dep.classId}`}
                className="rounded-md border border-slate-800/60 px-2.5 py-2"
              >
                <p className="text-[12px] text-slate-200">
                  {dep.sourceRo} → {dep.dependencyRo}
                </p>
                <p className="mt-0.5 text-[11px] font-medium text-slate-400">{dep.classLabelRo}</p>
                <p className="mt-1 text-[11px] text-slate-500">{dep.meaningRo}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {truth.settingsConflictVisible ? (
        <p
          data-testid="product-system-settings-conflict"
          className="rounded-lg border border-amber-800/40 bg-amber-950/20 px-3 py-2 text-[12px] text-amber-100/90"
        >
          Ownership setări componente / module = CONFLICTED. {SETTINGS_OWNERSHIP_CONFLICT_RO}.
        </p>
      ) : null}

      {templateCode === LETTERS_TEMPLATE_CODE ? <FinishMountingOwnershipPanel /> : null}

      <div className="flex flex-wrap gap-3 text-[12px]" data-testid="product-system-control-center-links">
        <Link to="/modules" className="text-blue-400 hover:text-blue-300">
          /modules — adevăr sisteme
        </Link>
        <Link to="/governance" className="text-blue-400 hover:text-blue-300">
          /governance — ownership și politici
        </Link>
      </div>
    </section>
  );
}

export function ProductSystemTemplateDetailPanel({
  template,
  availability,
  catalogBucket,
  section,
  onSectionChange,
  onOpenEditor,
  rowMetadata,
}: {
  template: ProductTemplateEntity;
  availability: ProductTemplateAvailabilityItem;
  catalogBucket: UnifiedCatalogBucketId;
  section: UnifiedCatalogDetailSection;
  onSectionChange: (section: UnifiedCatalogDetailSection) => void;
  onOpenEditor?: () => void;
  rowMetadata?: string;
}) {
  const isProduct =
    catalogBucket === "current-products" || catalogBucket === "candidate-products";
  const sections = isProduct ? PRODUCT_SECTIONS : COMPONENT_SECTIONS;
  const overview = bucketOverviewCopy(template.template_code, catalogBucket, availability);
  const scope = getProductTemplateScopePresentation(availability);
  const modularity = getProductModularityTruth(template.template_code);

  return (
    <div data-testid="product-system-template-detail-panel" className="space-y-4">
      <div className="flex flex-wrap items-start gap-3 border-b border-slate-800/70 pb-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <p className="text-base font-semibold text-slate-100">{template.family_name || template.template_code}</p>
            <p className="font-mono text-xs text-slate-500">{template.template_code}</p>
          </div>
          <p
            data-testid="product-system-template-detail-bucket-headline"
            className="mt-1 text-sm text-slate-400"
          >
            {overview.headline}
          </p>
        </div>
        <div
          className="flex flex-col items-end gap-1.5"
          data-testid="product-system-template-detail-commercial-chip"
        >
          <StatusBadge
            domain="productSystem"
            status={catalogBucket === "archived" ? "archived" : scope.isDirectRootAllowed ? "active" : "archived"}
            label={modularity?.commercialChipRo ?? scope.catalogStatusLabel}
            className="shrink-0 text-[10px] uppercase"
          />
          {modularity?.capabilityChipRo ? (
            <span
              data-testid="product-system-template-detail-capability-chip"
              className="rounded-full border border-slate-700/70 px-2 py-0.5 text-[10px] font-medium text-slate-400"
            >
              {modularity.capabilityChipRo}
            </span>
          ) : null}
        </div>
      </div>

      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Secțiuni detaliu șablon">
        {sections.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={section === tab.id}
            data-testid={tab.testId}
            onClick={() => onSectionChange(tab.id)}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
              section === tab.id
                ? "bg-purple-950/40 text-purple-100 ring-1 ring-purple-700/30"
                : "text-slate-500 hover:bg-slate-900/60 hover:text-slate-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {section === "overview" ? (
        <div className="space-y-4">
          <section
            data-testid="product-system-template-detail-overview"
            className="space-y-3 rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-200"
          >
            <div className="grid gap-2 sm:grid-cols-2">
              <p>
                <span className="text-slate-500">Work Intake:</span> {scope.workIntakeLabel}
              </p>
              <p>
                <span className="text-slate-500">Utilizare:</span> {scope.usageModeLabel}
              </p>
            </div>
            {availability.owner_decision_required ? (
              <p className="rounded-lg border border-amber-800/30 bg-amber-950/20 px-3 py-2 text-sm text-amber-200/90">
                Necesită decizie owner — nu e ofertabil ca rădăcină directă.
              </p>
            ) : null}
            {rowMetadata ? (
              <p className="line-clamp-3 text-sm leading-relaxed text-slate-500">{rowMetadata}</p>
            ) : null}
            <details className="text-sm text-slate-400">
              <summary className="cursor-pointer select-none text-slate-500 hover:text-slate-300">Mai mult context</summary>
              <ul className="mt-2 space-y-1.5 pl-4">
                {overview.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
              {catalogBucket === "legacy-shared-modules" ? (
                <p className="mt-2 pl-4">Contract modul legacy partajat — nu component-first.</p>
              ) : null}
            </details>
          </section>
          {isProduct ? <ModularityHonestySection templateCode={template.template_code} /> : null}
        </div>
      ) : null}

      {section === "composition" && isProduct ? (
        <section
          data-testid="product-system-template-detail-composition"
          className="space-y-3 rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-200"
        >
          <p className="text-[11px] text-slate-500">
            Rândurile de compoziție descriu legături — nu dovedesc independență modulară.
          </p>
          {availability.composition_modules.length === 0 && availability.shared_component_contracts.length === 0 ? (
            <p className="text-slate-500">Niciun modul de compoziție expus în availability.</p>
          ) : (
            <ul className="space-y-2">
              {availability.composition_modules.map((module) => (
                <li key={`${module.role_key}-${module.module_template_code}`} className="font-mono text-xs">
                  {module.role_label}: {module.module_template_code} · {module.status_label}
                </li>
              ))}
              {availability.shared_component_contracts.map((contract) => (
                <li key={contract.component_key} className="font-mono text-xs">
                  {contract.display_name}: {contract.module_template_code} · modul legacy partajat
                </li>
              ))}
            </ul>
          )}
          {(availability.svg_bindable_components ?? []).length > 0 ? (
            <div
              className="mt-3 space-y-2 border-t border-slate-800/70 pt-3"
              data-testid="product-system-svg-bindable-components"
            >
              <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                Componente SVG-bindable
              </p>
              <p className="text-[11px] text-slate-500">
                Authority Product System — rol geometric → componentă (Intake consumă ulterior).
              </p>
              <ul className="space-y-2">
                {(availability.svg_bindable_components ?? []).map((bindable) => (
                  <li
                    key={bindable.component_template_code}
                    className="rounded border border-slate-800/80 bg-slate-950/40 px-2 py-1.5 font-mono text-[11px] text-slate-200"
                    data-testid={`product-system-svg-bindable-${bindable.component_template_code}`}
                  >
                    <div className="font-sans text-[12px] font-medium text-slate-100">{bindable.owner_label}</div>
                    <div className="truncate text-slate-400">{bindable.component_template_code}</div>
                    <div className="mt-0.5 text-[10px] text-slate-500">
                      {(bindable.accepted_geometry_roles.length
                        ? bindable.accepted_geometry_roles.join(", ")
                        : "fără rol SVG")}{" "}
                      · {bindable.selection_mode} · {bindable.cardinality}
                      {bindable.required ? " · required" : " · optional"}
                      {bindable.active_by_default ? " · active default" : " · inactive default"}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {modularity ? <ModularityHonestySection templateCode={template.template_code} /> : null}
        </section>
      ) : null}

      {section === "components" && isProduct ? (
        <section
          data-testid="product-system-template-detail-components"
          className="overflow-hidden rounded-xl border border-slate-800/70"
        >
          <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-3 border-b border-slate-800/70 bg-slate-950/30 px-4 py-2.5 text-[11px] font-bold uppercase text-slate-500">
            <span>Rol</span>
            <span>Cod modul</span>
            <span>Status</span>
          </div>
          {availability.composition_modules.length === 0 && availability.shared_component_contracts.length === 0 ? (
            <p className="px-4 py-4 text-sm text-slate-500">Nicio componentă legată în compoziție.</p>
          ) : (
            <>
              {availability.composition_modules.map((module) => (
                <div
                  key={`${module.role_key}-${module.module_template_code}`}
                  className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-3 border-b border-slate-800/50 px-4 py-2.5 text-sm text-slate-200 last:border-b-0"
                >
                  <span>{module.role_label}</span>
                  <span className="font-mono text-xs text-slate-400">{module.module_template_code}</span>
                  <span className="text-xs text-slate-500">{module.status_label}</span>
                </div>
              ))}
              {availability.shared_component_contracts.map((contract) => (
                <div
                  key={contract.component_key}
                  className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-3 border-b border-slate-800/50 px-4 py-2.5 text-sm text-slate-200 last:border-b-0"
                >
                  <span>{contract.display_name}</span>
                  <span className="font-mono text-xs text-slate-400">{contract.module_template_code}</span>
                  <span className="text-xs text-slate-500">modul legacy</span>
                </div>
              ))}
            </>
          )}
        </section>
      ) : null}

      {section === "dossier" ? (
        <section
          data-testid="product-system-template-detail-dossier"
          className="space-y-3 rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-300"
        >
          <p>
            Un singur Dossier canonic. Prezența în Dossier nu dovedește modularitate — distinge rădăcină,
            copil, standalone, composition-only și module captive.
          </p>
          {modularity ? (
            <ul className="space-y-1 text-[12px] text-slate-400" data-testid="product-system-dossier-modularity-hints">
              {modularity.summaryChipsRo.map((chip) => (
                <li key={chip}>· {chip}</li>
              ))}
            </ul>
          ) : null}
          {template.template_code === LETTERS_TEMPLATE_CODE ? (
            <div data-testid="product-system-dossier-ownership-truth">
              <p className="mb-2 text-[12px] text-slate-400">
                Ownership FINISH / MOUNTING — read-only (current vs target). Nu este editor.
              </p>
              <FinishMountingOwnershipPanel />
            </div>
          ) : null}
          <Link
            to="/product-system/blueprint-dossier"
            data-testid="product-system-template-detail-dossier-cta"
            className="inline-flex rounded-md border border-purple-800/40 bg-purple-950/30 px-3 py-1.5 text-xs font-semibold text-purple-200 transition-colors hover:bg-purple-900/30"
          >
            Deschide Dossier canonic
          </Link>
          <div className="flex flex-wrap gap-3 text-[12px]">
            <Link to="/modules" className="text-blue-400 hover:text-blue-300">
              /modules
            </Link>
            <Link to="/governance" className="text-blue-400 hover:text-blue-300">
              /governance
            </Link>
            {onOpenEditor ? (
              <button
                type="button"
                data-testid="product-system-template-detail-open-editor"
                onClick={onOpenEditor}
                className="text-slate-400 underline-offset-2 hover:text-slate-200 hover:underline"
              >
                Editor șablon
              </button>
            ) : null}
          </div>
        </section>
      ) : null}

      {section === "lifecycle" ? (
        <div className="space-y-4" data-testid="product-system-template-detail-lifecycle">
          <TemplateLifecycleReadinessPanel templateCode={template.template_code} />
          {isProduct ? (
            <>
              <ProductTemplatePublicationPanel templateCode={template.template_code} />
              <ProductE2EReadinessPanel templateCode={template.template_code} />
              <ArtworkAnalysisReviewPanel />
            </>
          ) : null}
        </div>
      ) : null}

      {section === "fields" && !isProduct ? (
        <section
          data-testid="product-system-template-detail-fields"
          className="rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-300"
        >
          <p>Câmpurile modulului legacy se configurează în editorul Product System.</p>
          <p className="mt-2 font-mono text-xs text-slate-500">
            Părinți:{" "}
            {(availability.parent_product_codes.length > 0
              ? availability.parent_product_codes
              : availability.parent_codes
            ).join(", ") || "—"}
          </p>
        </section>
      ) : null}

      {section === "product-truth-paths" && !isProduct ? (
        <section
          data-testid="product-system-template-detail-product-truth-paths"
          className="rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-300"
        >
          <p>Căile Product Truth sunt deținute de compoziția produsului părinte.</p>
          <p className="mt-2 text-sm text-slate-500">Vizualizare readonly în catalog — fără scriere Product Truth.</p>
        </section>
      ) : null}

      {section === "guards" ? (
        <div className="space-y-4">
          <section
            data-testid="product-system-template-detail-guards"
            className="rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-300"
          >
            <p>
              <span className="text-slate-500">Status tehnic:</span> {availability.status}
            </p>
            <p className="mt-1">
              <span className="text-slate-500">Motiv:</span> {availability.status_reason}
            </p>
            <details className="mt-3 text-sm text-slate-500">
              <summary className="cursor-pointer select-none hover:text-slate-400">Detaliu readiness</summary>
              <p className="mt-1">{availability.readiness_reason}</p>
              <p className="mt-1">Readonly · Nu runtime · Fără Pricing / Quote / Order / Execution.</p>
            </details>
          </section>
          {catalogBucket === "legacy-shared-modules" ? (
            <LegacyReplacementReadinessPanel highlightLegacyCode={template.template_code} />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function defaultTemplateDetailSection(isProduct: boolean): UnifiedCatalogDetailSection {
  return "overview";
}
