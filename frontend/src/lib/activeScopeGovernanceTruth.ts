/**
 * Active-scope modularity + documentation governance — official Control Center truth.
 * Consumed by /modules and /governance only as Level-1 present truth.
 * Audits/worklogs are Level-3/4 evidence — they do not override this file.
 *
 * RUNTIME IMPLEMENTATION = STOP until separate owner GO
 * (ACTIVE_SCOPE_MODULE_INDEPENDENCE_V1).
 */

import { CANONICAL_ROUTES } from "@/lib/productSystemCanonicalModel";

/** Local status union — avoid circular import with currentTruthControlCenter. */
type RegistrationRuntimeStatus =
  | "CONFIRMAT"
  | "PARTIAL"
  | "BLOCAT"
  | "INACTIV"
  | "NEVERIFICAT"
  | "CONFLICTED"
  | "FAILED";

/** Level-1 official current-truth surfaces. */
export const OFFICIAL_CURRENT_TRUTH_ROUTES = {
  modules: "/modules",
  governance: "/governance",
} as const;

export const DOCUMENTATION_HIERARCHY = [
  {
    level: 1,
    id: "official_current_truth",
    labelRo: "Adevăr curent oficial",
    surfacesRo: "/modules · /governance",
    mayDeclareRo:
      "status curent; sisteme oficiale; ownership; rute active; usage permis; owner gates; handoff-uri canonice",
    ruleRo: "Singura sursă oficială pentru adevăr operațional și arhitectural curent.",
  },
  {
    level: 2,
    id: "canonical_contracts",
    labelRo: "Contracte detaliate canonice",
    surfacesRo: "docs/architecture · boundary · contract docs",
    mayDeclareRo: "Explică Level 1 — nu îl contrazice",
    ruleRo: "Detaliu tehnic subordonat Control Center.",
  },
  {
    level: 3,
    id: "evidence",
    labelRo: "Dovezi",
    surfacesRo: "audits · tests · runtime captures · API · screenshots",
    mayDeclareRo: "Dovedesc sau contestă adevărul curent",
    ruleRo: "Nu definesc status oficial singure.",
  },
  {
    level: 4,
    id: "history",
    labelRo: "Istoric",
    surfacesRo: "worklogs · old plans · archived audits · superseded reports",
    mayDeclareRo: "Context istoric",
    ruleRo: "Nu definesc adevărul curent.",
  },
] as const;

export const DOCUMENTATION_AUTHORITY_RULE_RO =
  "Runtime și codul dovedesc ce există. /modules definește ce este oficial. /governance definește ce este permis.";

export const UNREGISTERED_SYSTEM_POLICY = {
  id: "UNREGISTERED_SYSTEM",
  labelRo: "Sistem neregistrat",
  definitionRo:
    "Orice sistem arhitectural, motor, registry, flux, modul, capability, rută publică sau autoritate de contract care nu este înregistrat în /modules + /governance.",
  mayRo: [
    "poate fi auditat",
    "poate fi clasificat",
    "poate fi legacy",
  ],
  mayNotRo: [
    "nu poate fi extins ca oficial",
    "nu poate deveni sursă de adevăr",
    "nu poate fi conectat în calea E2E canonică",
    "nu poate fi declarat production-ready",
  ],
  appliesToRo:
    "sisteme arhitecturale, engines, registries, flows, modules, capabilities, rute publice, contract authorities — nu fiecare helper/utilitar",
  status: "ACTIVE" as const,
};

/** Required registration fields for an official system. */
export const SYSTEM_REGISTRATION_REQUIRED_FIELDS = [
  "canonicalSystemId",
  "canonicalName",
  "roleRo",
  "owner",
  "ownedDataContractsRo",
  "exclusionsRo",
  "inputsRo",
  "outputsRo",
  "consumersRo",
  "sourceOfTruthRo",
  "runtimeStatus",
  "boundariesRo",
  "ownerGatesRo",
  "uiApiLinks",
  "supportingEvidence",
  "lastVerificationStatus",
] as const;

export type OfficialSystemRegistration = {
  canonicalSystemId: string;
  canonicalName: string;
  roleRo: string;
  owner: string;
  ownedDataContractsRo: string;
  exclusionsRo: string;
  inputsRo: string;
  outputsRo: string;
  consumersRo: string;
  sourceOfTruthRo: string;
  runtimeStatus: RegistrationRuntimeStatus;
  boundariesRo: string;
  ownerGatesRo: string;
  uiApiLinks: readonly string[];
  supportingEvidence: readonly string[];
  lastVerificationStatus: string;
};

export const ACTIVE_SCOPE_SYSTEM: OfficialSystemRegistration = {
  canonicalSystemId: "active_scope_sold_scope",
  canonicalName: "Active Scope / Sold Scope",
  roleRo:
    "Rezolvă setul exact de module/componente cerut de client (sold scope) și îl compilează în scope runtime activ.",
  owner: "ProductDefinition (compiled active scope) — țintă; runtime încă REWORK",
  ownedDataContractsRo:
    "offer_scope.mode · sold_modules · runtime active/inactive sets · calc prerequisites · commercial scope · execution scope",
  exclusionsRo:
    "Nu deține tarife; nu materializează task-uri live; nu inventează template Return-only; FINISH/MOUNTING deferred Slice1",
  inputsRo:
    "product template · offer_scope.mode · sold_modules · hard technical prerequisites · conditional dependencies",
  outputsRo:
    "active runtime module set · inactive module set · calc prerequisites · commercial scope · execution scope",
  consumersRo: "ProductAggregate · CPP 7G · Quote Snapshot · Order Snapshot · ExecutionPlan",
  sourceOfTruthRo:
    "/modules (oficial) · offer_scope contract · ProductDefinition (țintă pentru compiled set)",
  runtimeStatus: "PARTIAL",
  boundariesRo:
    "PARTIAL — FE visibility / BOM / Execution paths exist; ProductDefinition și Aggregate nu sunt unificate pe offer_scope",
  ownerGatesRo:
    "RUNTIME IMPLEMENTATION = STOP până la GO separat ACTIVE_SCOPE_MODULE_INDEPENDENCE_V1",
  uiApiLinks: [
    OFFICIAL_CURRENT_TRUTH_ROUTES.modules,
    OFFICIAL_CURRENT_TRUTH_ROUTES.governance,
    "/intake-v6",
    CANONICAL_ROUTES.dossier,
  ],
  supportingEvidence: [
    "docs/audits/2026-07-17_product_system_module_independence_e2e_audit.md",
    "docs/worklog/realignment/2026-07-17_product_system_module_independence_e2e_audit.md",
    "backend/tests/test_offer_scope_bom_eic_cpp_filter.py",
    "backend/tests/test_intake_v6_live_calc_offer_scope.py",
    "backend/services/product_definition_builder_service.py#_resolve_module_state",
    "backend/services/execution_sold_scope_reader_service.py",
  ],
  lastVerificationStatus: "PARTIAL / CONFLICTED — audit HEAD b0306d4; registration build post-56053fd",
};

export const ACTIVE_SCOPE_KNOWN_DEFECTS_RO = [
  "PD always-on Letters modules (face/back/return/finisaje)",
  "Aggregate parent graph unscoped",
  "live-calc commercial pollution",
  "FACE-only BOM filter defect",
  "execution depends on frozen sold_scope",
] as const;

export type ActiveScopeHandoffStatus =
  | "CONFIRMED"
  | "PARTIAL"
  | "CONFLICTED"
  | "FAILED / NOT CONSUMED"
  | "CONFIRMED_WITH_GUARDS";

export const ACTIVE_SCOPE_HANDOFFS: readonly {
  id: string;
  fromRo: string;
  toRo: string;
  status: ActiveScopeHandoffStatus;
  noteRo: string;
}[] = [
  {
    id: "as.intake_offer_scope",
    fromRo: "Intake V6",
    toRo: "offer_scope contract",
    status: "CONFIRMED",
    noteRo: "component_subset + sold_modules persistate în workspace",
  },
  {
    id: "as.offer_scope_fe",
    fromRo: "offer_scope",
    toRo: "FE visibility",
    status: "CONFIRMED",
    noteRo: "intakeV6SoldScopeVisibility ascunde modulele nesold",
  },
  {
    id: "as.offer_scope_pd",
    fromRo: "offer_scope",
    toRo: "ProductDefinition active scope",
    status: "FAILED / NOT CONSUMED",
    noteRo: "_resolve_module_state ignoră offer_scope; always_on face/back/return",
  },
  {
    id: "as.pd_aggregate",
    fromRo: "ProductDefinition",
    toRo: "Aggregate active graph",
    status: "PARTIAL",
    noteRo: "Aggregate merge parent+dossier; fără sold_scope în builder",
  },
  {
    id: "as.aggregate_cpp",
    fromRo: "Aggregate",
    toRo: "CPP scoped measurements",
    status: "CONFLICTED",
    noteRo: "BOM return-only PASS; live-calc unscoped FAIL; measurements attach unscoped",
  },
  {
    id: "as.scope_snapshot",
    fromRo: "scope",
    toRo: "frozen Quote/Order snapshot",
    status: "PARTIAL",
    noteRo: "sold_scope pe snapshot încă parțial pe căi",
  },
  {
    id: "as.frozen_exec",
    fromRo: "frozen sold_scope",
    toRo: "Execution filter",
    status: "CONFIRMED_WITH_GUARDS",
    noteRo: "execution_sold_scope_reader filtrează când scope e înghețat",
  },
];

export const ACTIVE_SCOPE_TARGET_HANDOFF_RO = [
  "Intake V6",
  "Offer Scope Contract",
  "ProductDefinition Active Scope",
  "ProductAggregate Selected Graph",
  "Commercial Measurements → CPP 7G",
  "Active Operations → ExecutionPlan",
] as const;

export const ACTIVE_SCOPE_TARGET_NOTE_RO =
  "Țintă — nu implementat. Nu afișa acest lanț ca comportament curent.";

export const ACTIVE_SCOPE_READINESS_LAW = {
  id: "active_scope_readiness_law",
  titleRo: "Legea readiness pe scope activ",
  bindingRo:
    "Readiness se evaluează numai pentru modulele active. Un modul neales nu este o problemă.",
  inactiveMustNotRo: [
    "nu cere setări",
    "nu generează missing fields",
    "nu creează warnings",
    "nu creează linii comerciale",
    "nu creează operații sau task-uri",
  ],
  ownerLawRo: [
    "UN MODUL NEALES NU ESTE O PROBLEMA.",
    "UN MODUL ALES TREBUIE SA SE SUSTINA SINGUR.",
    "TEMPLATE-UL COMBINA MODULE — NU LE TINE CAPTIVE.",
  ],
  status: "DOCUMENTED — RUNTIME REWORK" as const,
};

export const ACTIVE_SCOPE_OWNERSHIP = [
  {
    systemId: "intake_v6",
    ownsRo: "selecție sold-scope operator · UI visibility · persistență workspace",
    doesNotOwnRo: "activare finală module · Aggregate graph · pricing scope · execution scope",
  },
  {
    systemId: "product_definition",
    ownsRo:
      "compiled active module set · hard dependencies · conditional dependencies · active-scope readiness",
    doesNotOwnRo: "bani · task materialization · tarife",
  },
  {
    systemId: "product_aggregate",
    ownsRo:
      "selected technical graph · active components · active materials · active operations · active commercial measurements",
    doesNotOwnRo: "prețuri · TVA · scope sold din Intake UI",
  },
  {
    systemId: "pricing_commercial",
    ownsRo: "bani numai pentru măsurători comerciale active",
    doesNotOwnRo: "măsurători tehnice · minute ca preț",
  },
  {
    systemId: "execution_plan",
    ownsRo: "operații active numai din frozen sold_scope",
    doesNotOwnRo: "reactivare module inactive · rewrite ofertă",
  },
] as const;

export const DEPENDENCY_CLASSES = [
  {
    id: "hard_technical",
    labelRo: "Hard technical",
    definitionRo: "Modulul nu poate exista fără aceasta.",
    exampleRo: "perimeter pentru modeled return",
  },
  {
    id: "conditional",
    labelRo: "Conditional",
    definitionRo: "Necesară doar pentru o variantă aleasă.",
    exampleRo: "culoare/vopsea pentru return vopsit",
  },
  {
    id: "composition_only",
    labelRo: "Composition-only",
    definitionRo: "Necesară doar pentru un produs complet anume — nu universal pentru modul.",
    exampleRo: "lipire față–cant pentru litere complete, nu pentru return vândut singur",
  },
  {
    id: "commercial",
    labelRo: "Commercial",
    definitionRo: "Necesară doar pentru linia comercială selectată.",
    exampleRo: "regula comercială modelare_cant",
  },
  {
    id: "execution",
    labelRo: "Execution",
    definitionRo: "Necesară doar la producție / asignare operație.",
    exampleRo: "workcenter forming return",
  },
] as const;

export const DEPENDENCY_BINDING_RULE_RO =
  "Dependențele de compoziție nu trebuie să devină dependențe universale de modul.";

export const HYBRID_INTAKE_MODEL = {
  id: "hybrid_intake_entry",
  approvedModel: "HYBRID" as const,
  productFirstRo: "Selectezi produsul Letters complet și configurezi modulele active.",
  moduleFirstRo:
    "Selectezi un subset component/service prin component_subset existent (ex. RETURN-CANT).",
  compileRuleRo: "Ambele compilează în aceleași contracte de modul — fără template Return-only nou.",
  uiStatus: "PARTIAL" as const,
  downstreamStatus: "NOT YET PROVEN" as const,
  noteRo: "HYBRID UI ENTRY = PARTIAL · HYBRID DOWNSTREAM COMPILATION = NOT YET PROVEN",
};

export const MODULE_INDEPENDENCE_PRODUCT_STATUS = [
  {
    id: "letters",
    labelRo: "Litere volumetrice",
    composedProduct: "ACTIVE",
    moduleIndependence: "PARTIAL",
    modeledReturn: {
      intakeSelection: "AVAILABLE",
      pdActiveScope: "FAILED",
      aggregateActiveScope: "PARTIAL",
      cpp: "CONFLICTED",
      execution: "GUARDED",
      final: "PARTIAL",
    },
  },
  {
    id: "logo",
    labelRo: "Logo",
    componentIndependence: "BLOCKED",
    rootOfferability: "BLOCKED",
  },
  {
    id: "acm",
    labelRo: "ACM",
    componentIndependence: "PARTIAL",
  },
] as const;

export const FULL_TEMPLATE_COUPLING_DEFECT = {
  id: "FULL_TEMPLATE_COUPLING",
  titleRo: "Cuplare pe template complet",
  severityRo: "CRITICAL — grouped defect",
  includesRo: [
    "PD always-on face/back/return/finisaje",
    "pending modules blocking readiness",
    "Aggregate full parent/dossier merge",
    "live-calc unscoped lines",
    "BOM FACE-only empty result",
    "path-dependent pricing",
    "execution scope dependency on frozen sold_scope",
  ],
  doNotRo: "Nu deschide micro-defecte per warning — repară autoritatea de activare/filtrare.",
  runtimeImplementation: "STOP",
  nextBuildRo: "ACTIVE_SCOPE_MODULE_INDEPENDENCE_V1 — numai după GO owner",
} as const;

export const ACTIVE_SCOPE_EVIDENCE = [
  {
    id: "ev.module_independence_audit",
    title: "Module independence E2E audit (approved)",
    category: "Decizie owner" as const,
    evidenceType: "acceptance",
    date: "2026-07-17",
    provesRo:
      "FULL_TEMPLATE_COUPLING_FOUND; HYBRID entry; PD/Aggregate unscoped; CPP CONFLICTED; return-only PARTIAL",
    stillCurrentRuntime: true,
    source: "docs/audits/2026-07-17_product_system_module_independence_e2e_audit.md",
  },
  {
    id: "ev.module_independence_worklog",
    title: "Module independence audit worklog",
    category: "Dovadă istorică" as const,
    evidenceType: "worklog",
    date: "2026-07-17",
    provesRo: "Handoff Level-4 — nu overridează /modules+/governance",
    stillCurrentRuntime: false,
    source: "docs/worklog/realignment/2026-07-17_product_system_module_independence_e2e_audit.md",
  },
] as const;
