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
export const MODULE_PRODUS_SHARED_SINGULAR_LABEL = "Module produs partajat";
export const MODULE_PRODUS_SHARED_VOLUMETRIC_LABEL = "Module produs volumetrice partajate";
export const MODULE_PRODUS_CODE_LABEL = "Module produs code";
export const MODULE_PRODUS_BOUNDARY_LABEL = "Owner boundary: Module produs";
export const MODULE_PRODUS_CANDIDATE_SET_LABEL = "Candidate Module produs — Litere";
export const MODULE_PRODUS_LIST_HEADING = "Module produs";

/** Admin chrome for product_template_module_links (display only — API table name unchanged). */
export const PRODUCT_TEMPLATE_MODULE_LINKS_DISPLAY_LABEL = "Legături Module produs";

/** Soft admin captions for contract patch fields (payload keys stay wire). */
export const USAGE_MODE_DISPLAY_LABEL = "Mod utilizare";
export const INSTANCE_SCHEMA_ID_DISPLAY_LABEL = "Schema instanță";

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
    return MODULE_PRODUS_CODE_LABEL;
  }
  if (normalized === "component_template_code") {
    return MODULE_PRODUS_CODE_LABEL;
  }
  if (normalized === "module_template_id") {
    return "Module produs id";
  }
  if (normalized === "product_template_module_links") {
    return PRODUCT_TEMPLATE_MODULE_LINKS_DISPLAY_LABEL;
  }
  if (normalized === "usage_mode") {
    return USAGE_MODE_DISPLAY_LABEL;
  }
  if (normalized === "instance_schema_id") {
    return INSTANCE_SCHEMA_ID_DISPLAY_LABEL;
  }
  if (normalized.includes("module_template")) {
    return "Module produs (wire)";
  }
  return wireKey;
}

export function equalModulesHintRo(): string {
  return "Față, cant/volum și spate sunt Module produs egale — nu ierarhii nested de template.";
}

/**
 * Operator spine for the Product System workspace — Product System ownership only.
 * Ofertă / Cost / Execution are downstream mentions, never spine steps.
 * Display / IA only; no behavior, API, or formula changes.
 */
export type ProductSystemSpineStep = {
  id: "template" | "modules" | "compiler" | "readiness";
  index: number;
  label: string;
  hint: string;
};

export const PRODUCT_SYSTEM_SPINE_STEPS: ProductSystemSpineStep[] = [
  {
    id: "template",
    index: 1,
    label: PRODUCT_TEMPLATE_LABEL,
    hint: "Produsul vizibil — centrul workspace-ului.",
  },
  {
    id: "modules",
    index: 2,
    label: MODULE_PRODUS_LABEL,
    hint: "Module egale care compun produsul (față, cant/volum, spate, LED, finisaj, montaj).",
  },
  {
    id: "compiler",
    index: 3,
    label: PRODUCT_COMPILER_LABEL,
    hint: "Compilează output-ul tehnic (Definiție + Graf) — fără preț.",
  },
  {
    id: "readiness",
    index: 4,
    label: "Pregătire",
    hint: "Blockere structurale / readiness — nu calculatoare de bani.",
  },
];

export const PRODUCT_SYSTEM_SPINE_TAGLINE =
  "Product Template → Module produs → Product Compiler → Pregătire.";

/** Downstream channels — secondary links only; never Product System spine steps. */
export const OFERTA_CLIENT_CHANNEL_LABEL = "Ofertă client";
export const OFERTA_CLIENT_CHANNEL_HELP =
  "Canal comercial separat (Intake / Oferte). Nu se calculează aici.";
export const COST_INTERN_CHANNEL_LABEL = "Cost intern";
export const COST_INTERN_CHANNEL_HELP =
  "Estimare internă separată — nu preț pentru client.";
export const EXECUTION_CHANNEL_LABEL = "Execution";
export const EXECUTION_CHANNEL_HELP =
  "Plan / execuție după comandă. Nu este flux Product System.";
export const DOWNSTREAM_CHANNELS_STRIP_LABEL = "Alte sisteme (linkuri)";
export const DOWNSTREAM_CHANNELS_STRIP_HELP =
  "Doar legături — nu pași și nu calculatoare în Product System.";
export const REGISTRY_INTERN_CHANNEL_LABEL = "Registry intern";
export const REGISTRY_INTERN_CHANNEL_HELP =
  "Pricing / Utilaje / Pontaj — inputuri admin, pe pagini separate.";

export const PRODUCT_SYSTEM_WORKSPACE_SUBTITLE =
  "Product Template + Module produs · Product Compiler · Pregătire";
export const INTAKE_V6_OPERATOR_PATH = "/intake-v6/operator";
export const QUOTES_DOWNSTREAM_PATH = "/quotes";
export const EXECUTION_DOWNSTREAM_PATH = "/execution";
