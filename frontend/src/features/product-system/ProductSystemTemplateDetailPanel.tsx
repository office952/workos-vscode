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

const PRODUCT_SECTIONS: Array<{ id: UnifiedCatalogDetailSection; label: string; testId: string }> = [
  { id: "overview", label: "Overview", testId: "product-system-template-detail-tab-overview" },
  { id: "composition", label: "Composition", testId: "product-system-template-detail-tab-composition" },
  { id: "components", label: "Components", testId: "product-system-template-detail-tab-components" },
  { id: "dossier", label: "Dossier", testId: "product-system-template-detail-tab-dossier" },
  { id: "guards", label: "Guards", testId: "product-system-template-detail-tab-guards" },
];

const COMPONENT_SECTIONS: Array<{ id: UnifiedCatalogDetailSection; label: string; testId: string }> = [
  { id: "overview", label: "Overview", testId: "product-system-template-detail-tab-overview" },
  { id: "dossier", label: "Dossier", testId: "product-system-template-detail-tab-dossier" },
  { id: "fields", label: "Fields", testId: "product-system-template-detail-tab-fields" },
  { id: "product-truth-paths", label: "Product Truth paths", testId: "product-system-template-detail-tab-product-truth-paths" },
  { id: "guards", label: "Guards", testId: "product-system-template-detail-tab-guards" },
];

function bucketOverviewCopy(
  templateCode: string,
  bucket: UnifiedCatalogBucketId,
  availability: ProductTemplateAvailabilityItem,
): { headline: string; bullets: string[] } {
  const scope = getProductTemplateScopePresentation(availability);

  if (templateCode === LETTERS_TEMPLATE_CODE || bucket === "current-products") {
    return {
      headline: "Current active root · Used today",
      bullets: [
        "Offerable product root currently used in Work Intake.",
        "Composition uses legacy shared modules — not component-first TPL-COMP-*.",
        "Separate from component-first Letters Candidate set.",
      ],
    };
  }

  if (templateCode === LOGO_TEMPLATE_CODE || bucket === "candidate-products") {
    return {
      headline: "Candidate product · Not Work Intake",
      bullets: [
        "Requires owner GO before any direct root / offerable path.",
        "Linked / analyzer composition only — no Logo activation from catalog.",
        "Not a component-first Product Composer.",
      ],
    };
  }

  if (bucket === "legacy-shared-modules") {
    return {
      headline: "Legacy internal module",
      bullets: [
        "Used by parent product composition — not a standalone quoteable root.",
        "Not a component-first TPL-COMP-* template.",
        "Readonly readiness contract in catalog — not runtime execution.",
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
    <div data-testid="product-system-template-detail-panel" className="space-y-1.5">
      <div className="flex flex-wrap items-start gap-2 border-b border-slate-800/70 pb-1.5">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-1.5 gap-y-0">
            <p className="text-[12px] font-bold text-slate-100">{template.family_name || template.template_code}</p>
            <p className="font-mono text-[9px] text-slate-600">{template.template_code}</p>
          </div>
          <p
            data-testid="product-system-template-detail-bucket-headline"
            className="mt-0.5 text-[10px] font-semibold text-slate-400"
          >
            {overview.headline}
          </p>
        </div>
        <StatusBadge
          domain="productSystem"
          status={catalogBucket === "archived" ? "archived" : scope.isDirectRootAllowed ? "active" : "archived"}
          label={scope.catalogStatusLabel}
          className="shrink-0 text-[9px] uppercase"
        />
      </div>

      <div className="flex flex-wrap gap-0.5" role="tablist" aria-label="Template detail sections">
        {sections.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={section === tab.id}
            data-testid={tab.testId}
            onClick={() => onSectionChange(tab.id)}
            className={`rounded px-2 py-0.5 text-[10px] font-bold transition-colors ${
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
          className="space-y-1.5 rounded border border-slate-800/70 bg-[#0D1321]/50 px-2 py-1.5 text-[11px] text-slate-200"
        >
          <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[10px]">
            <p>
              <span className="text-slate-500">Work Intake:</span> {scope.workIntakeLabel}
            </p>
            <p>
              <span className="text-slate-500">Usage:</span> {scope.usageModeLabel}
            </p>
          </div>
          {availability.owner_decision_required ? (
            <p className="text-[10px] text-amber-200/90">Owner decision required — not offerable as direct root.</p>
          ) : null}
          {rowMetadata ? (
            <p className="line-clamp-2 text-[10px] text-slate-500">{rowMetadata}</p>
          ) : null}
          <details className="text-[10px] text-slate-400">
            <summary className="cursor-pointer select-none text-slate-500 hover:text-slate-300">More context</summary>
            <ul className="mt-1 space-y-0.5 pl-3">
              {overview.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
            {catalogBucket === "legacy-shared-modules" ? (
              <p className="mt-1 pl-3">Legacy shared module contract — not component-first.</p>
            ) : null}
          </details>
        </section>
      ) : null}

      {section === "composition" && isProduct ? (
        <section
          data-testid="product-system-template-detail-composition"
          className="rounded border border-slate-800/70 bg-[#0D1321]/50 px-2 py-1.5 text-[11px] text-slate-200"
        >
          {availability.composition_modules.length === 0 && availability.shared_component_contracts.length === 0 ? (
            <p className="text-slate-500">No composition modules exposed in availability.</p>
          ) : (
            <ul className="space-y-0.5">
              {availability.composition_modules.map((module) => (
                <li key={`${module.role_key}-${module.module_template_code}`} className="font-mono text-[10px]">
                  {module.role_label}: {module.module_template_code} · {module.status_label}
                </li>
              ))}
              {availability.shared_component_contracts.map((contract) => (
                <li key={contract.component_key} className="font-mono text-[10px]">
                  {contract.display_name}: {contract.module_template_code} · legacy shared module
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}

      {section === "components" && isProduct ? (
        <section
          data-testid="product-system-template-detail-components"
          className="overflow-hidden rounded border border-slate-800/70"
        >
          <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-2 border-b border-slate-800/70 bg-slate-950/30 px-2 py-1 text-[9px] font-bold uppercase text-slate-500">
            <span>Role</span>
            <span>Module code</span>
            <span>Status</span>
          </div>
          {availability.composition_modules.length === 0 && availability.shared_component_contracts.length === 0 ? (
            <p className="px-2 py-2 text-[10px] text-slate-500">No linked components in composition.</p>
          ) : (
            <>
              {availability.composition_modules.map((module) => (
                <div
                  key={`${module.role_key}-${module.module_template_code}`}
                  className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-2 border-b border-slate-800/50 px-2 py-1 text-[10px] text-slate-200 last:border-b-0"
                >
                  <span>{module.role_label}</span>
                  <span className="font-mono text-[9px] text-slate-400">{module.module_template_code}</span>
                  <span className="text-[9px] text-slate-500">{module.status_label}</span>
                </div>
              ))}
              {availability.shared_component_contracts.map((contract) => (
                <div
                  key={contract.component_key}
                  className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-2 border-b border-slate-800/50 px-2 py-1 text-[10px] text-slate-200 last:border-b-0"
                >
                  <span>{contract.display_name}</span>
                  <span className="font-mono text-[9px] text-slate-400">{contract.module_template_code}</span>
                  <span className="text-[9px] text-slate-500">legacy module</span>
                </div>
              ))}
            </>
          )}
        </section>
      ) : null}

      {section === "dossier" ? (
        <section
          data-testid="product-system-template-detail-dossier"
          className="rounded border border-slate-800/70 bg-[#0D1321]/50 px-2 py-1.5 text-[11px] text-slate-300"
        >
          <p>Readonly readiness contract — dossier lives in template editor.</p>
          <button
            type="button"
            data-testid="product-system-template-detail-open-editor"
            onClick={onOpenEditor}
            className="mt-1.5 rounded border border-purple-800/40 bg-purple-950/30 px-2 py-0.5 text-[10px] font-bold text-purple-200"
          >
            Open template
          </button>
        </section>
      ) : null}

      {section === "fields" && !isProduct ? (
        <section
          data-testid="product-system-template-detail-fields"
          className="rounded border border-slate-800/70 bg-[#0D1321]/50 px-2 py-1.5 text-[11px] text-slate-300"
        >
          <p>Legacy module fields configured in Product System editor.</p>
          <p className="mt-1 font-mono text-[10px] text-slate-500">
            Parents:{" "}
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
          className="rounded border border-slate-800/70 bg-[#0D1321]/50 px-2 py-1.5 text-[11px] text-slate-300"
        >
          <p>Product Truth paths owned by parent product composition.</p>
          <p className="mt-1 text-[10px] text-slate-500">Readonly catalog view — no Product Truth write.</p>
        </section>
      ) : null}

      {section === "guards" ? (
        <section
          data-testid="product-system-template-detail-guards"
          className="rounded border border-slate-800/70 bg-[#0D1321]/50 px-2 py-1.5 text-[11px] text-slate-300"
        >
          <p>
            <span className="text-slate-500">Status:</span> {availability.status}
          </p>
          <p className="mt-0.5">
            <span className="text-slate-500">Reason:</span> {availability.status_reason}
          </p>
          <details className="mt-1 text-[10px] text-slate-500">
            <summary className="cursor-pointer select-none hover:text-slate-400">Readiness detail</summary>
            <p className="mt-0.5">{availability.readiness_reason}</p>
            <p className="mt-0.5">Readonly · Not runtime · No Pricing / Quote / Order / Execution.</p>
          </details>
        </section>
      ) : null}
    </div>
  );
}

export function defaultTemplateDetailSection(isProduct: boolean): UnifiedCatalogDetailSection {
  return "overview";
}
