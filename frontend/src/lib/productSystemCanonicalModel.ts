/**
 * Canonical Product System concept dictionary + stabilization scope.
 * Read-only present truth for Control Center / docs — not a runtime SoT.
 *
 * Owner-approved (2026-07-17): Letters + Logo + ACM only.
 * COMPONENT TEMPLATE STORAGE remains MIXED (no schema migration in this build).
 */

export type ConceptStatus =
  | "CANONICAL"
  | "PARTIAL"
  | "CONCEPT_CANONICAL — STORAGE_MIXED"
  | "SCOPED"
  | "MIXED";

export type MiniModuleScope =
  | "LETTERS_ONLY"
  | "LOGO"
  | "ACM"
  | "SHARED_WITHIN_SIGNAGE"
  | "UNKNOWN";

export type ComponentRepStatus =
  | "CANONICAL_PHYSICAL_COMPONENT"
  | "TEMPORARY_CHILD_TEMPLATE"
  | "LEGACY_CODE"
  | "GHOST"
  | "DUPLICATE"
  | "UNKNOWN";

export type StabilizationProductId = "letters" | "logo" | "acm";

/** Exact canonical operator routes — do not invent alternatives. */
export const CANONICAL_ROUTES = {
  inventory: "/inventory",
  pricing: "/inventory/pricing",
  dossier: "/product-system/blueprint-dossier",
  productSystem: "/product-system",
  intakeV6: "/intake-v6",
  modules: "/modules",
  governance: "/governance",
} as const;

/** Legacy routes that must redirect or leave navigation. */
export const LEGACY_DOSSIER_ROUTE = "/product-system/dossier-completion";
export const LEGACY_PRICING_ROUTE = "/pricing";

export interface CanonicalConcept {
  id: string;
  nameRo: string;
  technicalName: string;
  definitionRo: string;
  ownerRo: string;
  status: ConceptStatus;
  notRo: string;
  verifyRoute: string;
}

/**
 * One definition per concept — Control Center and docs must reuse this list.
 */
export const CANONICAL_CONCEPTS: readonly CanonicalConcept[] = [
  {
    id: "product_family",
    nameRo: "Familie de produs",
    technicalName: "Product Family",
    definitionRo: "Grupare de șabloane de produs înrudite.",
    ownerRo: "Product System (registry)",
    status: "CANONICAL",
    notRo: "Nu este șablon, modul, componentă sau catalog de opțiuni.",
    verifyRoute: CANONICAL_ROUTES.productSystem,
  },
  {
    id: "product_template",
    nameRo: "Șablon de produs",
    technicalName: "Product Template",
    definitionRo: "Composer-ul rădăcină pentru un tip de produs vandabil/definibil.",
    ownerRo: "Product System",
    status: "CANONICAL",
    notRo: "Nu este familie, mini-modul sau Capability UI.",
    verifyRoute: CANONICAL_ROUTES.productSystem,
  },
  {
    id: "component_template",
    nameRo: "Șablon de componentă",
    technicalName: "Component Template",
    definitionRo: "Definiție reutilizabilă a unei părți fizice/tehnice.",
    ownerRo: "Product System (concept)",
    status: "CONCEPT_CANONICAL — STORAGE_MIXED",
    notRo:
      "Nu există tabel first-class component_templates. Nu confunda cu BOM row, child TPL sau mini-modul.",
    verifyRoute: CANONICAL_ROUTES.productSystem,
  },
  {
    id: "mini_module",
    nameRo: "Mini-modul",
    technicalName: "Mini-Module",
    definitionRo: "Pachet operațional cu scope explicit pe familie/șablon.",
    ownerRo: "Product System (registry code)",
    status: "SCOPED",
    notRo: "Nu este Capability UI. Nu este generabil global doar din nume.",
    verifyRoute: CANONICAL_ROUTES.productSystem,
  },
  {
    id: "capability",
    nameRo: "Capability",
    technicalName: "Capability",
    definitionRo: "Tip de interacțiune UI (cum se editează/afișează), nu activare de producție.",
    ownerRo: "Product System declară tipul; Frontend mapează la renderer",
    status: "PARTIAL",
    notRo: "Nu activează module. Nu stochează nume React. Nu este catalog de produse.",
    verifyRoute: CANONICAL_ROUTES.intakeV6,
  },
  {
    id: "intake_contract",
    nameRo: "Contract Intake",
    technicalName: "Intake Contract",
    definitionRo: "Contract formular/compoziție specific produsului.",
    ownerRo: "Product System",
    status: "PARTIAL",
    notRo: "Nu este UI-ul Intake; nu persistă răspunsuri workspace.",
    verifyRoute: CANONICAL_ROUTES.intakeV6,
  },
  {
    id: "product_definition",
    nameRo: "Definiție produs",
    technicalName: "ProductDefinition",
    definitionRo: "Compilerul configurației concrete de produs; autoritate de activare module.",
    ownerRo: "ProductDefinition",
    status: "CANONICAL",
    notRo: "Nu calculează bani. Nu înlocuiește Aggregate.",
    verifyRoute: CANONICAL_ROUTES.intakeV6,
  },
  {
    id: "product_aggregate",
    nameRo: "Agregat produs",
    technicalName: "ProductAggregate",
    definitionRo: "Adevăr tehnic rezolvat + măsurători comerciale non-monetare + minute planificate.",
    ownerRo: "ProductAggregate",
    status: "CANONICAL",
    notRo: "Nu emite prețuri / TVA. Minute ≠ preț.",
    verifyRoute: CANONICAL_ROUTES.productSystem,
  },
  {
    id: "pricing_registry",
    nameRo: "Pricing Registry",
    technicalName: "Pricing Registry",
    definitionRo: "Reguli și tarife comerciale (rate), nu calculatorul monetar final.",
    ownerRo: "Pricing / Inventory rates",
    status: "CANONICAL",
    notRo: "Nu înlocuiește CPP 7G. Nu este inventar stoc.",
    verifyRoute: CANONICAL_ROUTES.pricing,
  },
  {
    id: "cpp_7g",
    nameRo: "CPP 7G",
    technicalName: "CPP 7G",
    definitionRo: "Calculatorul monetar — singura autoritate de bani pe spine.",
    ownerRo: "Commercial Pricing",
    status: "CANONICAL",
    notRo: "Nu deține măsurători tehnice. Nu folosește minute ca bază comercială.",
    verifyRoute: CANONICAL_ROUTES.pricing,
  },
  {
    id: "execution_plan",
    nameRo: "Plan de execuție",
    technicalName: "ExecutionPlan",
    definitionRo: "Plan operațional înghețat pentru producție.",
    ownerRo: "Execution",
    status: "PARTIAL",
    notRo: "Nu rescrie produsul amonte sau oferta.",
    verifyRoute: "/execution",
  },
  {
    id: "dossier",
    nameRo: "Dossier",
    technicalName: "Blueprint Dossier",
    definitionRo: "Documentația tehnică a șablonului (un singur traseu operator).",
    ownerRo: "Product System",
    status: "CANONICAL",
    notRo: "Nu există al doilea Dossier operator. Completion dashboard este legacy.",
    verifyRoute: CANONICAL_ROUTES.dossier,
  },
] as const;

export interface StabilizationProductRow {
  id: StabilizationProductId;
  familyId: string;
  familyLabelRo: string;
  templateCode: string;
  /** Internal maturity token — never show alone as product truth. */
  usageStatus: "ACTIVE" | "PARTIAL" | "OWNERSHIP_GAP";
  /** Operator-facing commercial/root chip (preferred UI label). */
  commercialChipRo: string;
  activeComponentsRo: string;
  activeModulesRo: string;
  intakeRo: string;
  productDefinitionRo: string;
  productAggregateRo: string;
  pricingRo: string;
  executionRo: string;
  limitationRo: string;
}

/** Only Letters, Logo, ACM — no banner/vehicle fill-in. */
export const STABILIZATION_PRODUCTS: readonly StabilizationProductRow[] = [
  {
    id: "letters",
    familyId: "litere_volumetrice",
    familyLabelRo: "Litere volumetrice",
    templateCode: "TPL-VOLUMETRIC-LETTERS_v2",
    usageStatus: "ACTIVE",
    commercialChipRo: "Rădăcină folosită azi",
    activeComponentsRo: "FACE/RETURN-CANT/BACK standalone Slice1; FINISH/MOUNTING captiv",
    activeModulesRo:
      "geometry_svg (LETTERS_ONLY calc); debitare_*; modelare_cant; sistem_led (LETTERS_ONLY); finisaje (captiv); structura_suport (signage-shared)",
    intakeRo: "Intake V6 root offerable + form-contract pilot",
    productDefinitionRo: "PARTIAL — Slice 1 proven; stabilizare generală parțială",
    productAggregateRo: "PARTIAL — selected graph Slice 1; bonding composition-only pe RETURN-CANT",
    pricingRo: "CPP 7G consumă măsurători scoped Slice 1",
    executionRo: "PARTIAL — preview pe frozen sold scope (Letters)",
    limitationRo:
      "Slice 1 stabilizat; FINISH/MOUNTING captive; settings CONFLICTED; form MIXED pe zone rămase.",
  },
  {
    id: "logo",
    familyId: "litere_volumetrice",
    familyLabelRo: "Logo",
    templateCode: "TPL-VOLUMETRIC-LOGO_v1",
    usageStatus: "PARTIAL",
    commercialChipRo: "Candidat · rădăcină blocată",
    activeComponentsRo: "LOGO-* child templates (composition) — nu dovedesc root",
    activeModulesRo: "Module links LOGO — fără independență rădăcină",
    intakeRo: "Candidate / non-offerable root",
    productDefinitionRo: "PARTIAL — preview / fail-closed offerability",
    productAggregateRo: "PARTIAL — linkage existent, nu root comercial",
    pricingRo: "OWNERSHIP GAP — nu ofertabil ca root",
    executionRo: "NEVERIFICAT ca root",
    limitationRo: "Rădăcină blocată; copil legat parțial; independență neprobată — fără activare.",
  },
  {
    id: "acm",
    familyId: "panouri_acp_iluminate",
    familyLabelRo: "Panouri ACM",
    templateCode: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
    usageStatus: "PARTIAL",
    commercialChipRo: "Montaj ACM · parțial",
    activeComponentsRo: "ACM boxed support — nu panou independent",
    activeModulesRo: "Linked optional pe Letters + boxed mounting path",
    intakeRo: "Linked child / mounting path — nu root Letters",
    productDefinitionRo: "PARTIAL — composition mounting chain",
    productAggregateRo: "PARTIAL — linked child resolve",
    pricingRo: "PARTIAL — mounting support lines când activ",
    executionRo: "PARTIAL",
    limitationRo:
      "Montaj ACM · parțial. Panou independent nepregătit. Casetat (TPL-ACM-CASSETTED-PANEL) arhivat.",
  },
] as const;

export interface ComponentRepresentationRow {
  currentRepresentation: string;
  meaningRo: string;
  product: StabilizationProductId | "shared_signage";
  activeConsumerRo: string;
  canonicalConcept: string;
  status: ComponentRepStatus;
}

export const COMPONENT_REPRESENTATION_INVENTORY: readonly ComponentRepresentationRow[] = [
  {
    currentRepresentation: "components_json BOM rows (comp_face_litere, …)",
    meaningRo: "Parte fizică + ops/mats nested în parent template",
    product: "letters",
    activeConsumerRo: "ProductAggregate / Cost paths",
    canonicalConcept: "Component Template (physical) — stored as BOM",
    status: "CANONICAL_PHYSICAL_COMPONENT",
  },
  {
    currentRepresentation: "TPL-VOLUM-ALUMINIU_v1",
    meaningRo: "Child Product Template pentru return/cant",
    product: "letters",
    activeConsumerRo: "module_links + Aggregate",
    canonicalConcept: "Temporary stand-in for Component Template",
    status: "TEMPORARY_CHILD_TEMPLATE",
  },
  {
    currentRepresentation: "TPL-METAL-PREMOUNT-STRUCTURE_v1 / TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
    meaningRo: "Child/root support templates",
    product: "shared_signage",
    activeConsumerRo: "module_links / standalone",
    canonicalConcept: "Temporary child Product Template",
    status: "TEMPORARY_CHILD_TEMPLATE",
  },
  {
    currentRepresentation: "TPL-VOLUMETRIC-FACE_v1 / BACK / LED / FINISH codes",
    meaningRo: "Policy/form backbone codes fără rând DB seed",
    product: "letters",
    activeConsumerRo: "form backbone maps / FE replacement map",
    canonicalConcept: "Component Template (aspirational)",
    status: "GHOST",
  },
  {
    currentRepresentation: "dossier_component_id (comp_*_litere)",
    meaningRo: "Rol dossier legat de mini-module",
    product: "letters",
    activeConsumerRo: "Mini-module registry + PD",
    canonicalConcept: "Physical component role",
    status: "CANONICAL_PHYSICAL_COMPONENT",
  },
  {
    currentRepresentation: "TPL-COMP-LETTER-* / TPL-LETTERS-COMPOSER_v1",
    meaningRo: "Candidate component-first set",
    product: "letters",
    activeConsumerRo: "Read-only FE completeness (inactive)",
    canonicalConcept: "Future Component Template entity",
    status: "LEGACY_CODE",
  },
  {
    currentRepresentation: "ProductAggregate.components[]",
    meaningRo: "Componente rezolvate runtime",
    product: "letters",
    activeConsumerRo: "CPP measurements / Plan",
    canonicalConcept: "Resolved instance of physical component",
    status: "CANONICAL_PHYSICAL_COMPONENT",
  },
  {
    currentRepresentation: "LOGO-* FACE/RETURN/BACK/LIGHTING child TPLs",
    meaningRo: "Composition children pentru Logo",
    product: "logo",
    activeConsumerRo: "Logo seed module links",
    canonicalConcept: "Temporary child Product Template",
    status: "TEMPORARY_CHILD_TEMPLATE",
  },
] as const;

export interface MiniModuleScopeRow {
  moduleCode: string;
  scope: MiniModuleScope;
  noteRo: string;
}

/** Truthful scope — not inferred from generic names alone. */
export const MINI_MODULE_SCOPE_ROWS: readonly MiniModuleScopeRow[] = [
  { moduleCode: "geometry_svg", scope: "LETTERS_ONLY", noteRo: "Registry applies_to Letters v2 only." },
  { moduleCode: "debitare_fata", scope: "LETTERS_ONLY", noteRo: "Dossier face Letters." },
  { moduleCode: "debitare_spate", scope: "LETTERS_ONLY", noteRo: "Dossier back Letters." },
  { moduleCode: "modelare_cant", scope: "LETTERS_ONLY", noteRo: "Linked TPL-VOLUM-ALUMINIU_v1." },
  {
    moduleCode: "sistem_led",
    scope: "LETTERS_ONLY",
    noteRo: "Numele pare generic; runtime = Letters dossier LED.",
  },
  {
    moduleCode: "finisaje",
    scope: "LETTERS_ONLY",
    noteRo: "Include sablon montaj Letters — nu banner finishing.",
  },
  {
    moduleCode: "structura_suport",
    scope: "SHARED_WITHIN_SIGNAGE",
    noteRo: "Maps metal + ACM child templates under Letters parent.",
  },
  {
    moduleCode: "electrica_logo",
    scope: "LOGO",
    noteRo: "FUTURE_RESERVED — nu activ operațional.",
  },
] as const;

/** UI interaction types — not production modules. */
export const CAPABILITY_TYPES = [
  {
    id: "grouped_finish_editor",
    labelRo: "Editor finisaje pe grup",
    activatesModule: false,
  },
  {
    id: "lighting_configuration",
    labelRo: "Configurare iluminare",
    activatesModule: false,
  },
  {
    id: "mounting_solution_editor",
    labelRo: "Editor soluție montaj",
    activatesModule: false,
  },
  {
    id: "geometry_viewer",
    labelRo: "Vizualizare geometrie / analyzer",
    activatesModule: false,
  },
  {
    id: "simple_fields",
    labelRo: "Câmpuri simple (contract renderer)",
    activatesModule: false,
  },
  {
    id: "material_selector",
    labelRo: "Selector material",
    activatesModule: false,
  },
] as const;

export type SettingCategory =
  | "platform"
  | "company"
  | "family"
  | "template"
  | "component"
  | "module"
  | "workspace"
  | "derived"
  | "commercial"
  | "execution";

export interface SettingsOwnershipRow {
  setting: string;
  category: SettingCategory;
  currentOwnerRo: string;
  runtimeSourceRo: string;
  consumerRo: string;
  statusRo: string;
}

export const SETTINGS_OWNERSHIP_ROWS: readonly SettingsOwnershipRow[] = [
  {
    setting: "Component settings catalogs",
    category: "template",
    currentOwnerRo: "MULTIPLE — unresolved",
    runtimeSourceRo: "Form contract + FE catalogs + template JSON",
    consumerRo: "Intake / PD",
    statusRo: "CONFLICTED — Cataloage de opțiuni multiple — conflict nerezolvat",
  },
  {
    setting: "Module settings catalogs",
    category: "module",
    currentOwnerRo: "MULTIPLE — unresolved",
    runtimeSourceRo: "Form contract + FE catalogs + module defaults",
    consumerRo: "Intake / PD",
    statusRo: "CONFLICTED — Cataloage de opțiuni multiple — conflict nerezolvat",
  },
  {
    setting: "VAT %",
    category: "company",
    currentOwnerRo: "Company commercial settings",
    runtimeSourceRo: "company_commercial_settings",
    consumerRo: "Dry-run / offer",
    statusRo: "CODE_ENFORCED (workspace VAT not authority)",
  },
  {
    setting: "Markup / discount operator",
    category: "workspace",
    currentOwnerRo: "Intake finish_setup.commercial_inputs",
    runtimeSourceRo: "Workspace",
    consumerRo: "Dry-run cost-plus",
    statusRo: "CONFLICT — dual vs commercial_markup_policies",
  },
  {
    setting: "Material markup policies",
    category: "commercial",
    currentOwnerRo: "commercial_markup_policies",
    runtimeSourceRo: "Admin policies",
    consumerRo: "PS pricing preview",
    statusRo: "CONFLICT — second markup concept",
  },
  {
    setting: "Material / finish options",
    category: "template",
    currentOwnerRo: "MIXED — form contract + FE option maps",
    runtimeSourceRo: "Contract bindings + FE catalogs",
    consumerRo: "Intake",
    statusRo: "CONFLICT — triple finish catalogs",
  },
  {
    setting: "Return depths",
    category: "module",
    currentOwnerRo: "Letters return module / API depths",
    runtimeSourceRo: "finish_setup.return_depth_mm",
    consumerRo: "PD / Aggregate",
    statusRo: "PARTIAL",
  },
  {
    setting: "Lighting / PSU options",
    category: "module",
    currentOwnerRo: "Form contract pilot + FE remnants",
    runtimeSourceRo: "finish_setup.lighting_* / selected_psu_watts",
    consumerRo: "PD sistem_led",
    statusRo: "PARTIAL — pilot contract-driven",
  },
  {
    setting: "Mounting options",
    category: "workspace",
    currentOwnerRo: "Intake FE (scope/solution) + links",
    runtimeSourceRo: "finish_setup.mounting_*",
    consumerRo: "PD activation",
    statusRo: "MIXED — FE visibility ≠ activation",
  },
  {
    setting: "Workspace selections",
    category: "workspace",
    currentOwnerRo: "Intake V6",
    runtimeSourceRo: "Workspace payload",
    consumerRo: "PD → Aggregate → CPP",
    statusRo: "CODE_ENFORCED",
  },
  {
    setting: "Derived geometry",
    category: "derived",
    currentOwnerRo: "SVG Analyzer / PD",
    runtimeSourceRo: "Analyzer + quote_geometry",
    consumerRo: "Aggregate",
    statusRo: "CODE_ENFORCED",
  },
  {
    setting: "Planned minutes",
    category: "derived",
    currentOwnerRo: "ProductAggregate (+ planning_duration_contract)",
    runtimeSourceRo: "Aggregate operations",
    consumerRo: "ExecutionPlan",
    statusRo: "CODE_ENFORCED — not commercial",
  },
  {
    setting: "Pricing rates",
    category: "commercial",
    currentOwnerRo: "Pricing Registry → inventory/workcenter",
    runtimeSourceRo: CANONICAL_ROUTES.pricing,
    consumerRo: "CPP 7G",
    statusRo: "CODE_ENFORCED",
  },
  {
    setting: "Live product_templates JSON",
    category: "template",
    currentOwnerRo: "Product System Products editor",
    runtimeSourceRo: "DB product_templates",
    consumerRo: "Open workspaces (mutable risk)",
    statusRo: "CONFLICT — mutable vs snapshots",
  },
] as const;

export function assertUniqueConceptIds(concepts: readonly CanonicalConcept[] = CANONICAL_CONCEPTS): void {
  const ids = concepts.map((c) => c.id);
  if (new Set(ids).size !== ids.length) {
    throw new Error("Duplicate canonical concept ids");
  }
  const names = concepts.map((c) => c.technicalName);
  if (new Set(names).size !== names.length) {
    throw new Error("Duplicate canonical concept technical names");
  }
}

export function isStabilizationTemplateCode(templateCode: string | null | undefined): boolean {
  const code = (templateCode || "").trim();
  return STABILIZATION_PRODUCTS.some((p) => p.templateCode === code);
}

export function stabilizationClaimsBannerOrVehicle(text: string): boolean {
  return /\bbanner\b/i.test(text) || /\bvehicle\b/i.test(text) || /colant[aă]ri auto/i.test(text);
}
