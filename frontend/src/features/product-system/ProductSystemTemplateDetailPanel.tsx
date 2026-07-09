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
}: {
  template: ProductTemplateEntity;
  availability: ProductTemplateAvailabilityItem;
  catalogBucket: UnifiedCatalogBucketId;
  section: UnifiedCatalogDetailSection;
  onSectionChange: (section: UnifiedCatalogDetailSection) => void;
  onOpenEditor: () => void;
}) {
  const isProduct =
    catalogBucket === "current-products" || catalogBucket === "candidate-products";
  const sections = isProduct ? PRODUCT_SECTIONS : COMPONENT_SECTIONS;
  const overview = bucketOverviewCopy(template.template_code, catalogBucket, availability);
  const scope = getProductTemplateScopePresentation(availability);

  return (
    <div data-testid="product-system-template-detail-panel" className="space-y-3">
      <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3">
        <div className="flex flex-wrap items-start gap-2">
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold text-slate-100">{template.family_name || template.template_code}</p>
            <p className="mt-0.5 font-mono text-[11px] text-slate-300">{template.template_code}</p>
            <p
              data-testid="product-system-template-detail-bucket-headline"
              className="mt-1 text-[12px] font-bold text-slate-200"
            >
              {overview.headline}
            </p>
          </div>
          <StatusBadge
            domain="productSystem"
            status={catalogBucket === "archived" ? "archived" : scope.isDirectRootAllowed ? "active" : "archived"}
            label={scope.catalogStatusLabel}
            className="shrink-0 text-[11px] uppercase"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Template detail sections">
        {sections.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={section === tab.id}
            data-testid={tab.testId}
            onClick={() => onSectionChange(tab.id)}
            className={`rounded-md border px-2.5 py-1 text-[12px] font-bold transition-colors ${
              section === tab.id
                ? "border-purple-500/50 bg-purple-500/10 text-purple-100"
                : "border-slate-700 bg-slate-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {section === "overview" ? (
        <section
          data-testid="product-system-template-detail-overview"
          className="space-y-2 rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3 text-[12px] text-slate-200"
        >
          <ul className="space-y-1">
            {overview.bullets.map((bullet) => (
              <li key={bullet}>• {bullet}</li>
            ))}
          </ul>
          <p>
            <span className="text-slate-500">Work Intake:</span> {scope.workIntakeLabel}
          </p>
          <p>
            <span className="text-slate-500">Usage:</span> {scope.usageModeLabel}
          </p>
          {availability.owner_decision_required ? (
            <p className="text-amber-200">Owner decision required — not offerable as direct root.</p>
          ) : null}
          {catalogBucket === "legacy-shared-modules" ? (
            <p className="text-slate-400">Legacy shared module contract — not component-first.</p>
          ) : null}
        </section>
      ) : null}

      {section === "composition" && isProduct ? (
        <section
          data-testid="product-system-template-detail-composition"
          className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3 text-[12px] text-slate-200"
        >
          <p className="mb-2 text-slate-400">Legacy shared modules linked to this product root.</p>
          {availability.composition_modules.length === 0 && availability.shared_component_contracts.length === 0 ? (
            <p className="text-slate-400">No composition modules exposed in availability.</p>
          ) : (
            <ul className="space-y-1">
              {availability.composition_modules.map((module) => (
                <li key={`${module.role_key}-${module.module_template_code}`} className="font-mono text-[11px]">
                  {module.role_label}: {module.module_template_code} · {module.status_label}
                </li>
              ))}
              {availability.shared_component_contracts.map((contract) => (
                <li key={contract.component_key} className="font-mono text-[11px]">
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
          className="overflow-hidden rounded-lg border border-slate-800/90"
        >
          <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-2 border-b border-slate-800 bg-slate-950/40 px-2.5 py-1.5 text-[11px] font-bold uppercase text-slate-500">
            <span>Role</span>
            <span>Module code</span>
            <span>Status</span>
          </div>
          {availability.composition_modules.length === 0 && availability.shared_component_contracts.length === 0 ? (
            <p className="px-3 py-3 text-[12px] text-slate-400">No linked components in composition.</p>
          ) : (
            <>
              {availability.composition_modules.map((module) => (
                <div
                  key={`${module.role_key}-${module.module_template_code}`}
                  className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-2 border-b border-slate-800/60 px-2.5 py-2 text-[12px] text-slate-200 last:border-b-0"
                >
                  <span>{module.role_label}</span>
                  <span className="font-mono text-[11px] text-slate-300">{module.module_template_code}</span>
                  <span className="text-[11px] text-slate-400">{module.status_label}</span>
                </div>
              ))}
              {availability.shared_component_contracts.map((contract) => (
                <div
                  key={contract.component_key}
                  className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-2 border-b border-slate-800/60 px-2.5 py-2 text-[12px] text-slate-200 last:border-b-0"
                >
                  <span>{contract.display_name}</span>
                  <span className="font-mono text-[11px] text-slate-300">{contract.module_template_code}</span>
                  <span className="text-[11px] text-slate-400">legacy module</span>
                </div>
              ))}
            </>
          )}
        </section>
      ) : null}

      {section === "dossier" ? (
        <section
          data-testid="product-system-template-detail-dossier"
          className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3 text-[12px] text-slate-300"
        >
          <p>Readonly readiness contract — design-time template dossier lives in the template editor.</p>
          <p className="mt-2 text-slate-400">Not runtime dossier activation from catalog browse.</p>
          <button
            type="button"
            data-testid="product-system-template-detail-open-editor"
            onClick={onOpenEditor}
            className="mt-3 rounded-md border border-purple-700/40 bg-purple-950/30 px-2.5 py-1 text-[12px] font-bold text-purple-200"
          >
            Open template
          </button>
        </section>
      ) : null}

      {section === "fields" && !isProduct ? (
        <section
          data-testid="product-system-template-detail-fields"
          className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3 text-[12px] text-slate-300"
        >
          <p>Legacy module fields and contract metadata are configured in Product System editor.</p>
          <p className="mt-2 font-mono text-[11px] text-slate-400">
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
          className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3 text-[12px] text-slate-300"
        >
          <p>Product Truth paths are owned by the parent product composition and legacy module contract.</p>
          <p className="mt-2 text-slate-400">Readonly catalog view — no Product Truth write from this surface.</p>
        </section>
      ) : null}

      {section === "guards" ? (
        <section
          data-testid="product-system-template-detail-guards"
          className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3 text-[12px] text-slate-300"
        >
          <p>
            <span className="text-slate-500">Status:</span> {availability.status}
          </p>
          <p className="mt-1">
            <span className="text-slate-500">Reason:</span> {availability.status_reason}
          </p>
          <p className="mt-2 text-slate-400">{availability.readiness_reason}</p>
          <p className="mt-2 text-[11px] text-slate-500">
            Readonly readiness contract · Not runtime · No Pricing / Quote / Order / Execution activation.
          </p>
        </section>
      ) : null}
    </div>
  );
}

export function defaultTemplateDetailSection(isProduct: boolean): UnifiedCatalogDetailSection {
  return "overview";
}
