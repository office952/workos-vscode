import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import { StatusBadge } from "@/components/workos/design-system";
import type { UnifiedCatalogDetailSection } from "./productSystemUnifiedCatalogTypes";

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

export function ProductSystemTemplateDetailPanel({
  template,
  availability,
  section,
  onSectionChange,
  onOpenEditor,
}: {
  template: ProductTemplateEntity;
  availability: ProductTemplateAvailabilityItem;
  section: UnifiedCatalogDetailSection;
  onSectionChange: (section: UnifiedCatalogDetailSection) => void;
  onOpenEditor: () => void;
}) {
  const isProduct =
    availability.product_system_role === "offerable_product" ||
    availability.product_system_role === "candidate_product";
  const sections = isProduct ? PRODUCT_SECTIONS : COMPONENT_SECTIONS;

  return (
    <div data-testid="product-system-template-detail-panel" className="space-y-3">
      <div className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3">
        <div className="flex flex-wrap items-start gap-2">
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold text-slate-100">{template.family_name || template.template_code}</p>
            <p className="mt-0.5 font-mono text-[11px] text-slate-300">{template.template_code}</p>
            <p className="mt-1 text-[12px] text-slate-400">{availability.ui_label}</p>
          </div>
          <StatusBadge
            domain="productSystem"
            status={availability.display_group === "archived_experimental" ? "archived" : "active"}
            label={availability.ui_label}
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
        <section className="space-y-2 rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3 text-[12px] text-slate-200">
          <p>
            <span className="text-slate-500">Type:</span> {isProduct ? "Product template" : "Component template"}
          </p>
          <p>
            <span className="text-slate-500">Lifecycle:</span> {availability.ui_label}
          </p>
          <p>
            <span className="text-slate-500">Work Intake:</span>{" "}
            {availability.quote_offerable ? "visible for offerable roots" : "not exposed"}
          </p>
          <p>
            <span className="text-slate-500">Readiness:</span> {availability.readiness_reason || "—"}
          </p>
          {availability.owner_decision_required ? (
            <p className="text-amber-200">Owner decision required before activation paths.</p>
          ) : null}
        </section>
      ) : null}

      {section === "composition" && isProduct ? (
        <section
          data-testid="product-system-template-detail-composition"
          className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3 text-[12px] text-slate-200"
        >
          {availability.composition_modules.length === 0 ? (
            <p className="text-slate-400">No composition modules exposed in availability.</p>
          ) : (
            <ul className="space-y-1">
              {availability.composition_modules.map((module) => (
                <li key={`${module.role_key}-${module.module_template_code}`} className="font-mono text-[11px]">
                  {module.role_label}: {module.module_template_code} · {module.status_label}
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
          {availability.composition_modules.length === 0 ? (
            <p className="px-3 py-3 text-[12px] text-slate-400">No linked components in composition.</p>
          ) : (
            availability.composition_modules.map((module) => (
              <div
                key={`${module.role_key}-${module.module_template_code}`}
                className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] gap-2 border-b border-slate-800/60 px-2.5 py-2 text-[12px] text-slate-200 last:border-b-0"
              >
                <span>{module.role_label}</span>
                <span className="font-mono text-[11px] text-slate-300">{module.module_template_code}</span>
                <span className="text-[11px] text-slate-400">{module.status_label}</span>
              </div>
            ))
          )}
        </section>
      ) : null}

      {section === "dossier" ? (
        <section
          data-testid="product-system-template-detail-dossier"
          className="rounded-lg border border-slate-800/90 bg-[#0D1321]/70 px-3 py-3 text-[12px] text-slate-300"
        >
          <p>Design-time template dossier lives in the template editor configuration.</p>
          <p className="mt-2 text-slate-400">
            Open the template to inspect materials, operations, and notes. No runtime dossier activation from catalog.
          </p>
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
          <p>Component template fields and contract metadata are configured in Product System editor.</p>
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
          <p>Product Truth paths are owned by the parent product composition and component contract.</p>
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
            No Pricing / Quote / Order / Execution activation from catalog browse.
          </p>
        </section>
      ) : null}
    </div>
  );
}

export function defaultTemplateDetailSection(isProduct: boolean): UnifiedCatalogDetailSection {
  return "overview";
}
