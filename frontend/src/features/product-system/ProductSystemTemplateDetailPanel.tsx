import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import { getProductTemplatePublication } from "@/api/productTemplatePublication";
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
} from "./productSystemCatalogEntries";
import { LegacyReplacementReadinessPanel } from "./LegacyReplacementReadinessPanel";
import { FinishMountingOwnershipPanel } from "./FinishMountingOwnershipPanel";
import { TemplateLifecycleReadinessPanel } from "./TemplateLifecycleReadinessPanel";
import { ProductE2EReadinessPanel } from "./ProductE2EReadinessPanel";
import { ProductTemplatePublicationPanel } from "./ProductTemplatePublicationPanel";
import { ArtworkAnalysisReviewPanel } from "./ArtworkAnalysisReviewPanel";
import { ComponentContractUsedByPanel } from "./ComponentContractUsedByPanel";
import { AcmBoxedAppliedContentPanel } from "./AcmBoxedAppliedContentPanel";
import { AcmBoxedFaceTreatmentPanel } from "./AcmBoxedFaceTreatmentPanel";
import { TemplateCompositionAuthoringPanel } from "./TemplateCompositionAuthoringPanel";
import { ProductSystemReferenceFinishLinePanel } from "./ProductSystemReferenceFinishLinePanel";
import { ProductSystemReferenceCompletePanel } from "./ProductSystemReferenceCompletePanel";
import { TemplateRuntimePreviewPanel } from "./TemplateRuntimePreviewPanel";
import { TemplateDualStatusChips } from "./TemplateDualStatusChips";
import { TemplatePricingStudioPanel } from "./TemplatePricingStudioPanel";
import { showTemplatePricingStudio } from "./templatePricingStudioEligibility";
import { humanTemplateName } from "./productSystemAdminDisplay";
import { PS_SURFACE_INSET, PS_SURFACE_PANEL } from "./productSystemSurfaces";

const ACM_BOXED_TEMPLATE_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";

/** Primary authoring flow — identity → composition → dossier → readiness → publication → preview. */
const PRODUCT_PRIMARY_SECTIONS: Array<{
  id: UnifiedCatalogDetailSection;
  label: string;
  testId: string;
}> = [
  { id: "overview", label: "Prezentare", testId: "product-system-template-detail-tab-overview" },
  { id: "composition", label: "Compoziție", testId: "product-system-template-detail-tab-composition" },
  { id: "contracts", label: "Contracte", testId: "product-system-template-detail-tab-contracts" },
  { id: "pricing", label: "Prețuri template", testId: "product-system-template-detail-tab-pricing" },
  { id: "dossier", label: "Dosar tehnic", testId: "product-system-template-detail-tab-dossier" },
  { id: "readiness", label: "Pregătire E2E", testId: "product-system-template-detail-tab-readiness" },
  { id: "publication", label: "Publicare", testId: "product-system-template-detail-tab-publication" },
  { id: "runtime-preview", label: "Previzualizare runtime", testId: "product-system-template-detail-tab-runtime-preview" },
];

/** Secondary / diagnostic — available, not dominant. */
const PRODUCT_DIAGNOSTIC_SECTIONS: Array<{
  id: UnifiedCatalogDetailSection;
  label: string;
  testId: string;
}> = [
  { id: "components", label: "Componente", testId: "product-system-template-detail-tab-components" },
  { id: "relationships", label: "Relații", testId: "product-system-template-detail-tab-relationships" },
  { id: "materials", label: "Materiale", testId: "product-system-template-detail-tab-materials" },
  { id: "guards", label: "Diagnostic", testId: "product-system-template-detail-tab-guards" },
];

const PRODUCT_SECTIONS = [...PRODUCT_PRIMARY_SECTIONS, ...PRODUCT_DIAGNOSTIC_SECTIONS];

const COMPONENT_SECTIONS: Array<{ id: UnifiedCatalogDetailSection; label: string; testId: string }> = [
  { id: "overview", label: "Prezentare", testId: "product-system-template-detail-tab-overview" },
  { id: "dossier", label: "Dossier", testId: "product-system-template-detail-tab-dossier" },
  { id: "lifecycle", label: "Lifecycle", testId: "product-system-template-detail-tab-lifecycle" },
  { id: "fields", label: "Câmpuri", testId: "product-system-template-detail-tab-fields" },
  { id: "product-truth-paths", label: "Product Truth", testId: "product-system-template-detail-tab-product-truth-paths" },
  { id: "guards", label: "Garduri", testId: "product-system-template-detail-tab-guards" },
];

const COMPONENT_PRICING_TAB = {
  id: "pricing" as const,
  label: "Prețuri template",
  testId: "product-system-template-detail-tab-pricing",
};

function componentSectionsWithOptionalPricing(
  includePricing: boolean,
): Array<{ id: UnifiedCatalogDetailSection; label: string; testId: string }> {
  if (!includePricing) return COMPONENT_SECTIONS;
  const [overview, ...rest] = COMPONENT_SECTIONS;
  return [overview, COMPONENT_PRICING_TAB, ...rest];
}

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
        "Dossier / BOM / Module produs ≠ dovadă de modularitate — doar comportament independent.",
      ],
    };
  }

  if (templateCode === LETTERS_TEMPLATE_CODE || bucket === "current-products") {
    return {
      headline: "Rădăcină folosită azi",
      bullets: [
        "Produs ofertabil folosit în Work Intake.",
        "Compoziția folosește Module produs partajate (legacy links) — nu setul TPL-COMP-* candidat.",
        "Separat de setul candidate Module produs Letters.",
      ],
    };
  }

  if (templateCode === LOGO_TEMPLATE_CODE || bucket === "candidate-products") {
    return {
      headline: "Candidat · rădăcină blocată",
      bullets: [
        "Necesită decizie owner înainte de orice cale directă ofertabilă.",
        "Doar compoziție linked / analyzer — fără activare Logo din catalog.",
        "Nu este un Product Template ofertabil standalone.",
      ],
    };
  }

  if (bucket === "legacy-shared-modules") {
    return {
      headline: "Modul intern legacy",
      bullets: [
        "Folosit de compoziția produsului părinte — nu e rădăcină ofertabilă standalone.",
        "Nu este set candidat Module produs TPL-COMP-*.",
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
      className={`${PS_SURFACE_PANEL} space-y-4 px-4 py-4 text-sm text-slate-200`}
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
            className="rounded border border-[#2A3548]/55 bg-transparent px-2 py-0.5 text-[11px] font-medium text-slate-300"
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
  const pricingStudioVisible = showTemplatePricingStudio({
    isProduct,
    templateCode: template.template_code,
  });
  const sections = isProduct
    ? PRODUCT_SECTIONS
    : componentSectionsWithOptionalPricing(pricingStudioVisible);
  const overview = bucketOverviewCopy(template.template_code, catalogBucket, availability);
  const scope = getProductTemplateScopePresentation(availability);
  const modularity = getProductModularityTruth(template.template_code);

  const displayName =
    template.family_name || humanTemplateName(template.template_code);
  const primarySections = isProduct ? PRODUCT_PRIMARY_SECTIONS : sections;
  const diagnosticSections = isProduct ? PRODUCT_DIAGNOSTIC_SECTIONS : [];
  const showDiagnosticTabs = diagnosticSections.length > 0;
  const [publicationStatus, setPublicationStatus] = useState<string | null>(null);

  useEffect(() => {
    if (!isProduct) {
      setPublicationStatus(null);
      return;
    }
    let cancelled = false;
    void getProductTemplatePublication(template.template_code)
      .then((state) => {
        if (!cancelled) setPublicationStatus(state.publication_status);
      })
      .catch(() => {
        if (!cancelled) setPublicationStatus(null);
      });
    return () => {
      cancelled = true;
    };
  }, [isProduct, template.template_code]);

  return (
    <div data-testid="product-system-template-detail-panel" className="space-y-4">
      <header className="flex flex-wrap items-start gap-3 border-b border-slate-800/70 pb-4">
        <div className="min-w-0 flex-1">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Șablon produs
          </p>
          <div className="mt-0.5 flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <h2 className="text-lg font-semibold text-slate-100">{displayName}</h2>
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
          <TemplateDualStatusChips
            templateCode={template.template_code}
            dbActive={Boolean(template.active ?? availability.status === "available")}
          />
          <details className="text-right">
            <summary className="cursor-pointer select-none text-[10px] text-slate-500 hover:text-slate-400">
              Status catalog
            </summary>
            <div className="mt-1 flex justify-end">
              <StatusBadge
                domain="productSystem"
                status={
                  catalogBucket === "archived"
                    ? "archived"
                    : scope.isDirectRootAllowed
                      ? "active"
                      : "archived"
                }
                label={modularity?.commercialChipRo ?? scope.catalogStatusLabel}
                className="shrink-0 text-[10px] uppercase"
              />
            </div>
          </details>
        </div>
      </header>

      {isProduct ? (
        <div
          className={`${PS_SURFACE_INSET} flex flex-wrap items-center justify-between gap-2 px-3 py-2`}
          data-testid="product-system-template-next-action-strip"
        >
          <p className="text-[12px] text-slate-300">
            <span className="font-semibold text-slate-100">Următorul pas:</span>{" "}
            {publicationStatus === "PUBLISHED" ? (
              <>
                șablonul este <span className="text-emerald-200">PUBLISHED</span>. Verifică
                Prețuri template / AI defaults și snapshot-urile înainte de ofertă nouă.
              </>
            ) : (
              <>
                verifică Pregătire E2E înainte de publicare. Copiii obligatorii inactivi și
                blockerele structurale blochează publicarea (nu default-urile AI).
              </>
            )}
          </p>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              className="rounded border border-slate-600/70 px-2.5 py-1 text-[11px] font-medium text-slate-200 hover:bg-slate-800/60"
              data-testid="product-system-template-next-action-readiness"
              onClick={() => onSectionChange("readiness")}
            >
              Verifică traseul
            </button>
            <button
              type="button"
              className="rounded border border-slate-700/60 px-2.5 py-1 text-[11px] font-medium text-slate-400 hover:bg-slate-900/40"
              data-testid="product-system-template-next-action-publication"
              onClick={() => onSectionChange("publication")}
            >
              Publicare
            </button>
          </div>
        </div>
      ) : null}

      <div className="space-y-1.5">
        <div
          className="flex flex-wrap gap-1 border-b border-slate-800/80"
          role="tablist"
          aria-label="Flux authoring șablon"
        >
          {primarySections.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={section === tab.id}
              data-testid={tab.testId}
              onClick={() => onSectionChange(tab.id)}
              className={`border-b-2 px-3 py-2 text-xs font-semibold transition-colors ${
                section === tab.id
                  ? "border-sky-500 text-slate-100"
                  : "border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        {showDiagnosticTabs && diagnosticSections.length > 0 ? (
          <details
            className="group"
            data-testid="product-system-template-diagnostic-tabs"
            open={diagnosticSections.some((tab) => tab.id === section)}
          >
            <summary className="cursor-pointer select-none py-1 text-[11px] font-medium text-slate-600 hover:text-slate-400">
              Diagnostic și liste secundare
            </summary>
            <div
              className="mt-1 flex flex-wrap gap-1"
              role="tablist"
              aria-label="Diagnostic și liste secundare"
            >
              {diagnosticSections.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={section === tab.id}
                  data-testid={tab.testId}
                  onClick={() => onSectionChange(tab.id)}
                  className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                    section === tab.id
                      ? "bg-slate-800/80 text-slate-200 ring-1 ring-slate-600/50"
                      : "text-slate-600 hover:bg-slate-900/50 hover:text-slate-400"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </details>
        ) : null}
      </div>

      {section === "overview" ? (
        <div className="space-y-4">
          <section
            data-testid="product-system-template-detail-overview"
            className={`${PS_SURFACE_PANEL} space-y-3 px-4 py-4 text-sm text-slate-200`}
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
                <p className="mt-2 pl-4">Contract modul legacy partajat — nu set candidat Module produs.</p>
              ) : null}
            </details>
          </section>
          {isProduct ? (
            <>
              <ProductSystemReferenceCompletePanel />
              <ProductSystemReferenceFinishLinePanel />
              <details className={`${PS_SURFACE_PANEL} px-4 py-3`}>
                <summary className="cursor-pointer select-none text-[12px] font-medium text-slate-400 hover:text-slate-300">
                  Axe de adevăr / modularitate (read-only)
                </summary>
                <div className="mt-3">
                  <ModularityHonestySection templateCode={template.template_code} />
                </div>
              </details>
            </>
          ) : null}
        </div>
      ) : null}

      {section === "composition" && isProduct ? (
        <div className="space-y-4" data-testid="product-system-template-detail-composition">
          {template.template_code === ACM_BOXED_TEMPLATE_CODE ? (
            <>
              <AcmBoxedAppliedContentPanel templateCode={template.template_code} />
              <AcmBoxedFaceTreatmentPanel templateCode={template.template_code} />
            </>
          ) : null}
          <TemplateCompositionAuthoringPanel
            parentTemplateCode={template.template_code}
            parentTemplateId={template.id}
          />
          <section className={`${PS_SURFACE_PANEL} space-y-3 px-4 py-4 text-sm text-slate-200`}>
            <p className="text-[11px] text-slate-500">
              Availability read-model (nu dovedește independență modulară).
            </p>
            {availability.composition_modules.length === 0 &&
            availability.shared_component_contracts.length === 0 ? (
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
          </section>
        </div>
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

      {section === "contracts" && isProduct ? (
        <div data-testid="product-system-template-detail-contracts">
          <ComponentContractUsedByPanel templateCode={template.template_code} />
        </div>
      ) : null}

      {section === "pricing" && pricingStudioVisible ? (
        <div data-testid="product-system-template-detail-pricing">
          {!isProduct ? (
            <p
              data-testid="product-system-template-pricing-module-note"
              className="mb-3 text-[12px] text-slate-400"
            >
              Modul component / legacy — bucket neschimbat. Prețuri template reutilizează
              același Studio și API; nu transformă entitatea în produs root.
            </p>
          ) : null}
          <TemplatePricingStudioPanel templateCode={template.template_code} />
        </div>
      ) : null}

      {section === "relationships" && isProduct ? (
        <section
          data-testid="product-system-template-detail-relationships"
          className={`${PS_SURFACE_PANEL} space-y-3 px-4 py-4 text-sm text-slate-300`}
        >
          <p className="text-[11px] text-slate-500">
            Hartă relații parent↔child din availability — validare vizuală, fără auto-activare.
          </p>
          <ul className="space-y-2 font-mono text-xs">
            {availability.composition_modules.map((module) => (
              <li key={`rel-${module.role_key}-${module.module_template_code}`}>
                {template.template_code} → {module.module_template_code} · {module.role_label} ·{" "}
                {module.status_label}
              </li>
            ))}
            {(availability.parent_product_codes?.length
              ? availability.parent_product_codes
              : availability.parent_codes
            ).map((parentCode) => (
              <li key={`parent-${parentCode}`}>
                {parentCode} → {template.template_code} (părinte)
              </li>
            ))}
          </ul>
          {availability.composition_modules.length === 0 &&
          (availability.parent_product_codes?.length ?? availability.parent_codes?.length ?? 0) ===
            0 ? (
            <p className="text-slate-500">Nicio relație expusă.</p>
          ) : null}
        </section>
      ) : null}

      {section === "materials" && isProduct ? (
        <div data-testid="product-system-template-detail-materials">
          <TemplateRuntimePreviewPanel templateCode={template.template_code} />
          <p className="mt-2 text-[11px] text-slate-500">
            Materiale din ProductDefinition preview (read-only). Nu e Pricing / Inventory SoT.
          </p>
        </div>
      ) : null}

      {section === "dossier" ? (
        <section
          data-testid="product-system-template-detail-dossier"
          className={`${PS_SURFACE_PANEL} space-y-3 px-4 py-4 text-sm text-slate-300`}
        >
          <p>
            Un singur Dossier canonic. Prezența în Dossier nu dovedește modularitate — distinge rădăcină,
            copil, standalone, composition-only și module captive.
          </p>
          <p className="text-[11px] text-slate-500">
            Clasificare: Documentation / Review / Decisions / Approved bridges. Runtime-owned rămâne în
            Intake / PD / Order — nu în Dossier.
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
            to={`/product-system/blueprint-dossier?template=${encodeURIComponent(template.template_code)}`}
            data-testid="product-system-template-detail-dossier-cta"
            className="inline-flex rounded-md border border-sky-800/40 bg-sky-950/30 px-3 py-1.5 text-xs font-semibold text-sky-100 transition-colors hover:bg-sky-900/30"
          >
            Deschide Dossier Studio
          </Link>
          <p className="text-[11px] text-slate-500">
            În Studio: Salvează → Validează → Verifică → Publică (sticky). Publicarea rămâne pe
            autoritatea șablonului, nu pe Dossier.
          </p>
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

      {section === "runtime-preview" && isProduct ? (
        <div data-testid="product-system-template-detail-runtime-preview">
          <TemplateRuntimePreviewPanel templateCode={template.template_code} />
        </div>
      ) : null}

      {section === "readiness" && isProduct ? (
        <div className="space-y-4" data-testid="product-system-template-detail-readiness">
          <ProductE2EReadinessPanel templateCode={template.template_code} />
          <ArtworkAnalysisReviewPanel />
        </div>
      ) : null}

      {section === "publication" && isProduct ? (
        <div className="space-y-4" data-testid="product-system-template-detail-publication">
          <ProductTemplatePublicationPanel templateCode={template.template_code} />
          <p className="text-[11px] text-slate-500">
            Fail-closed publish · fără auto-publish · fără SVG geometry checks în poarta de publicare.
          </p>
        </div>
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
          className={`${PS_SURFACE_PANEL} px-4 py-4 text-sm text-slate-300`}
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
          className={`${PS_SURFACE_PANEL} px-4 py-4 text-sm text-slate-300`}
        >
          <p>Căile Product Truth sunt deținute de compoziția produsului părinte.</p>
          <p className="mt-2 text-sm text-slate-500">Vizualizare readonly în catalog — fără scriere Product Truth.</p>
        </section>
      ) : null}

      {section === "guards" ? (
        <div className="space-y-4">
          <section
            data-testid="product-system-template-detail-guards"
            className={`${PS_SURFACE_PANEL} px-4 py-4 text-sm text-slate-300`}
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
