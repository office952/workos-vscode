import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import { StatusBadge } from "@/components/workos/design-system";
import {
  LETTERS_TEMPLATE_CODE,
  LOGO_TEMPLATE_CODE,
  getProductTemplateScopePresentation,
} from "@/lib/productTemplateScopePresentation";
import type {
  UnifiedCatalogBucketId,
  UnifiedCatalogDetailSection,
} from "./productSystemUnifiedCatalogTypes";
import { LegacyReplacementReadinessPanel } from "./LegacyReplacementReadinessPanel";

const PRODUCT_SECTIONS: Array<{ id: UnifiedCatalogDetailSection; label: string; testId: string }> = [
  { id: "overview", label: "Prezentare", testId: "product-system-template-detail-tab-overview" },
  { id: "composition", label: "Compoziție", testId: "product-system-template-detail-tab-composition" },
  { id: "components", label: "Componente", testId: "product-system-template-detail-tab-components" },
  { id: "dossier", label: "Dossier", testId: "product-system-template-detail-tab-dossier" },
  { id: "guards", label: "Garduri", testId: "product-system-template-detail-tab-guards" },
];

const COMPONENT_SECTIONS: Array<{ id: UnifiedCatalogDetailSection; label: string; testId: string }> = [
  { id: "overview", label: "Prezentare", testId: "product-system-template-detail-tab-overview" },
  { id: "dossier", label: "Dossier", testId: "product-system-template-detail-tab-dossier" },
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

  if (templateCode === LETTERS_TEMPLATE_CODE || bucket === "current-products") {
    return {
      headline: "Rădăcină activă · folosită azi",
      bullets: [
        "Produs ofertabil folosit în Work Intake.",
        "Compoziția folosește module legacy partajate — nu TPL-COMP-* component-first.",
        "Separat de setul candidate component-first Letters.",
      ],
    };
  }

  if (templateCode === LOGO_TEMPLATE_CODE || bucket === "candidate-products") {
    return {
      headline: "Produs candidate · fără Work Intake",
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
  onOpenEditor: () => void;
  rowMetadata?: string;
}) {
  const isProduct =
    catalogBucket === "current-products" || catalogBucket === "candidate-products";
  const sections = isProduct ? PRODUCT_SECTIONS : COMPONENT_SECTIONS;
  const overview = bucketOverviewCopy(template.template_code, catalogBucket, availability);
  const scope = getProductTemplateScopePresentation(availability);

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
        <StatusBadge
          domain="productSystem"
          status={catalogBucket === "archived" ? "archived" : scope.isDirectRootAllowed ? "active" : "archived"}
          label={scope.catalogStatusLabel}
          className="shrink-0 text-[10px] uppercase"
        />
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
      ) : null}

      {section === "composition" && isProduct ? (
        <section
          data-testid="product-system-template-detail-composition"
          className="rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-200"
        >
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
          className="rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-300"
        >
          <p>Contract readonly de readiness — dossier-ul complet trăiește în editorul de șablon.</p>
          <button
            type="button"
            data-testid="product-system-template-detail-open-editor"
            onClick={onOpenEditor}
            className="mt-3 rounded-md border border-purple-800/40 bg-purple-950/30 px-3 py-1.5 text-xs font-semibold text-purple-200 transition-colors hover:bg-purple-900/30"
          >
            Deschide șablonul
          </button>
        </section>
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
              <span className="text-slate-500">Status:</span> {availability.status}
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
