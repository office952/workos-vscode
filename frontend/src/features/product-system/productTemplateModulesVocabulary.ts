/**
 * Product System UI vocabulary (Nivel 1 + Product Compiler display shell).
 *
 * Labels / IA only — does NOT rename DB columns, API fields (`module_template_*`),
 * formulas, ProductDefinition / ProductAggregate behavior, CPP/EIC, or mini-module registry codes.
 */

export const PRODUCT_TEMPLATE_LABEL = "Product Template";

/** Primary composition slogan for catalog / candidate panels. */
export const PRODUCT_MODULES_SEMANTIC_LABEL = "1 Product Template + N Module produs egale";

export const MODULE_PRODUS_LABEL = "Module produs";
export const MODULE_TEHNIC_LABEL = "Modul tehnic";
export const MODULE_PRODUS_SHARED_LABEL = "Module produs partajate";
export const MODULE_PRODUS_BOUNDARY_LABEL = "Owner boundary: Module produs";
export const MODULE_PRODUS_CANDIDATE_SET_LABEL = "Candidate Module produs — Litere";
export const MODULE_PRODUS_LIST_HEADING = "Module produs";

/** Mini-module registry — operational packaging, not a product module. */
export const MINI_MODULE_OPERATIONAL_LABEL = "Mini-modul operațional";
export const MINI_MODULE_OPERATIONAL_EN_LABEL = "Operational mini-module";

/** Visible unified concept for ProductDefinition + ProductAggregate (display only). */
export const PRODUCT_COMPILER_LABEL = "Product Compiler";
export const PRODUCT_COMPILER_DEFINITION_STAGE_LABEL = "Product Compiler · Definiție";
export const PRODUCT_COMPILER_GRAPH_STAGE_LABEL = "Product Compiler · Graf tehnic";
export const PRODUCT_COMPILER_RELATION_HELP =
  "Product Template → Module produs egale → Product Compiler (output tehnic pentru ofertă / plan).";
export const PRODUCT_COMPILER_NO_PRICE_HELP =
  "Product Compiler nu calculează Ofertă client. Oferta client rămâne pe canal comercial separat.";

/** ExecutionPlan operator-facing states (map to existing preview / draft / materialize). */
export const EXECUTION_PLAN_LABEL = "Execution Plan";
export const EXECUTION_PLAN_PREVIEW_STATE_LABEL = "Preview";
export const EXECUTION_PLAN_DRAFT_STATE_LABEL = "Draft Plan";
export const EXECUTION_PLAN_OPERATIONAL_STATE_LABEL = "Operational Plan";
export const EXECUTION_PLAN_STATES_HELP =
  "Preview (citire) → Draft Plan (salvat) → Operational Plan (materializat — GO owner).";

/** Internal registries — not the operator product spine. */
export const PRICING_REGISTRY_NAV_LABEL = "Pricing (registry)";
export const MACHINES_REGISTRY_NAV_LABEL = "Utilaje (registry)";
export const HR_PONTAJ_REGISTRY_NAV_LABEL = "Pontaj (registry intern)";
export const INTERNAL_REGISTRY_HELPER_HINT =
  "Registry intern / helper — nu este fluxul principal Product Template → Module produs → Compiler.";

export const PRODUCT_TEMPLATE_COMPOSES_HELP =
  "Product Template compune Module produs egale (față, cant/volum, spate, iluminare, structură, finisaj, montaj). Fiecare modul deține adevărul său tehnic. Product Compiler produce output-ul tehnic derivat (fără preț).";

export const PRODUCT_TEMPLATE_COMPOSER_ONLY_HELP =
  "Product Template este nivelul principal (composer). Modulele produsului sunt egale ca valoare structurală; acest panou arată ownership / gaps fără a inventa readiness.";

export const SHARED_FOUNDATION_HELP =
  "Contracte comune ca entități principale; Modulele produsului (rânduri child în product_templates + links) sunt binding-uri de profil. Mini-modulul operațional e separat. No pricing, no runtime activation, no Work Intake exposure change.";

export const CANDIDATE_COMPOSER_HELP =
  "Product Template candidat (readonly) — compune Module produs egale; nu e ofertabil în Work Intake.";

export const RETURN_CANT_MOVE_TRUTH_HELP =
  "Aliniere read-only pentru modulul cant/volum. Arată ce există deja, ce rămâne doar pe aggregate părinte și ce trebuie să fie adevăr pe Module produs — nu pe un sistem separat de template.";

export const MUST_OWN_ON_MODULE_LABEL = "Must own truth on Module produs";

/** Map legacy FE display tokens → Module produs vocabulary (internal keys may still use old wording). */
export function displayModuleSourceTypeLabel(sourceType: string): string {
  switch (sourceType) {
    case "component template / registry":
    case "module / registry":
      return "module / registry";
    case "component template":
    case "module produs":
      return "module produs";
    default:
      return sourceType;
  }
}

/**
 * Display-only adapter for wire field names that still say module_template_*.
 * Does not rename API/DB contracts.
 */
export function displayModuleTemplateWireLabel(wireKey: string): string {
  const normalized = wireKey.trim();
  if (normalized === "module_template_code" || normalized.endsWith("_module_template_code")) {
    return "Module produs code";
  }
  if (normalized.includes("module_template")) {
    return "Module produs (wire)";
  }
  if (normalized === "component_template_code") {
    return "Module produs code";
  }
  return wireKey;
}

export function equalModulesHintRo(): string {
  return "Față, cant/volum și spate sunt Module produs egale — nu ierarhii nested de template.";
}
