/**
 * Active-scope modularity + documentation governance — official Control Center truth.
 * Consumed by /modules and /governance only as Level-1 present truth.
 * Audits/worklogs are Level-3/4 evidence — they do not override this file.
 *
 * Letters Slice 1 runtime proof: ACTIVE_SCOPE_MODULE_INDEPENDENCE_V1 (owner GO).
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
  owner: "ProductDefinition (compiled active scope) — Letters Slice 1 proven",
  ownedDataContractsRo:
    "offer_scope.mode · sold_modules · ActiveScopeResult · runtime active/inactive · calc prerequisites · commercial/execution scope",
  exclusionsRo:
    "Nu deține tarife; nu materializează task-uri live; nu inventează template Return-only; FINISH/MOUNTING deferred Slice1; Logo/ACM out of slice",
  inputsRo:
    "product template · offer_scope.mode · sold_modules · workspace facts · hard/conditional/composition dependencies",
  outputsRo:
    "active runtime module set · inactive module set · calc prerequisites · commercial scope · execution scope · composition exclusions",
  consumersRo: "ProductAggregate · CPP 7G · live-calc · BOM · Quote Snapshot · Order Snapshot · ExecutionPlan preview",
  sourceOfTruthRo:
    "/modules (oficial) · active_scope_resolver_service · ProductDefinition compile",
  runtimeStatus: "PARTIAL",
  boundariesRo:
    "PROVEN FOR LETTERS SLICE 1 — canonical resolver + PD/Aggregate/CPP/execution preview; not global module independence",
  ownerGatesRo:
    "Nu declara independență globală; Logo BLOCKED; ACM PARTIAL; fără task materialization; fără template/schema nou",
  uiApiLinks: [
    OFFICIAL_CURRENT_TRUTH_ROUTES.modules,
    OFFICIAL_CURRENT_TRUTH_ROUTES.governance,
    "/intake-v6",
    CANONICAL_ROUTES.dossier,
  ],
  supportingEvidence: [
    "docs/audits/2026-07-17_product_system_module_independence_e2e_audit.md",
    "docs/worklog/realignment/2026-07-17_active_scope_module_independence_v1.md",
    "backend/services/active_scope_resolver_service.py",
    "backend/tests/test_active_scope_resolver_service.py",
    "backend/tests/test_product_definition_active_scope.py",
    "backend/tests/test_product_aggregate_active_scope_filter.py",
    "backend/tests/test_intake_v6_live_calc_offer_scope.py",
    "backend/services/execution_sold_scope_reader_service.py",
  ],
  lastVerificationStatus:
    "PROVEN FOR LETTERS SLICE 1 — ACTIVE_SCOPE_MODULE_INDEPENDENCE_V1; RETURN-CANT ONLY acceptance",
};

export const ACTIVE_SCOPE_KNOWN_DEFECTS_RO = [
  "FULL_TEMPLATE_COUPLING — remediat pe Letters Slice 1 (PD/Aggregate/CPP/exec preview)",
  "Logo commercial/component independence rămâne BLOCKED",
  "ACM cassette activation rămâne PARTIAL / out of slice",
  "FINISH/MOUNTING sold codes deferred Slice1",
] as const;

export type ActiveScopeHandoffStatus =
  | "CONFIRMED"
  | "PARTIAL"
  | "CONFLICTED"
  | "FAILED / NOT CONSUMED"
  | "CONFIRMED_WITH_GUARDS"
  | "PROVEN";

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
    status: "PROVEN",
    noteRo: "compile_active_scope → _resolve_module_state; inactive outside sold set",
  },
  {
    id: "as.pd_aggregate",
    fromRo: "ProductDefinition",
    toRo: "Aggregate active graph",
    status: "PROVEN",
    noteRo: "filter_aggregate_by_active_scope + identity enrich; bonding composition-only for RETURN-CANT",
  },
  {
    id: "as.aggregate_cpp",
    fromRo: "Aggregate",
    toRo: "CPP scoped measurements",
    status: "PROVEN",
    noteRo: "commercial_scope_modules + measurement module_gate; linked-logo suppressed in subset",
  },
  {
    id: "as.scope_snapshot",
    fromRo: "scope",
    toRo: "frozen Quote/Order snapshot",
    status: "PARTIAL",
    noteRo: "offer_scope_snapshot freeze existent; official V6 snapshot path still has fixture dry-run debt",
  },
  {
    id: "as.frozen_exec",
    fromRo: "frozen sold_scope",
    toRo: "Execution filter",
    status: "PROVEN",
    noteRo: "RETURN-CANT excludes return_face_bonding; preview-only, no materialization",
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
  "Lanțul țintă este proven pe Letters Slice 1. Nu declara independență globală pentru Logo/ACM.";

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
  status: "PROVEN FOR LETTERS SLICE 1" as const,
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
  downstreamStatus: "PROVEN FOR LETTERS SLICE 1" as const,
  noteRo: "HYBRID UI ENTRY = PARTIAL · HYBRID DOWNSTREAM COMPILATION = PROVEN SLICE 1",
};

export const MODULE_INDEPENDENCE_PRODUCT_STATUS = [
  {
    id: "letters",
    labelRo: "Litere volumetrice",
    composedProduct: "ACTIVE",
    moduleIndependence: "PARTIAL / PROVEN FOR SLICE 1",
    modeledReturn: {
      intakeSelection: "AVAILABLE",
      pdActiveScope: "READY",
      aggregateActiveScope: "READY",
      cpp: "READY",
      execution: "READY",
      final: "READY",
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
  severityRo: "REMEDIATED ON LETTERS SLICE 1 — still historical defect id",
  includesRo: [
    "PD always-on face/back/return/finisaje — fixed via active_scope",
    "Aggregate full parent merge — filtered selected graph",
    "live-calc unscoped lines — unified commercial_scope",
    "BOM FACE-only empty — identity components + sold authority",
    "return_face_bonding composition-only for RETURN-CANT alone",
  ],
  doNotRo: "Nu redeschide micro-defecte pe Letters Slice 1 fără regresie dovedită.",
  runtimeImplementation: "PROVEN FOR LETTERS SLICE 1",
  nextBuildRo: "Logo independence / ACM expansion — separate owner GO only",
} as const;

export const ACTIVE_SCOPE_EVIDENCE = [
  {
    id: "ev.module_independence_audit",
    title: "Module independence E2E audit (approved)",
    category: "Decizie owner" as const,
    evidenceType: "acceptance",
    date: "2026-07-17",
    provesRo:
      "FULL_TEMPLATE_COUPLING_FOUND baseline; HYBRID entry; registered before runtime GO",
    stillCurrentRuntime: false,
    source: "docs/audits/2026-07-17_product_system_module_independence_e2e_audit.md",
  },
  {
    id: "ev.active_scope_v1_worklog",
    title: "Active scope module independence V1 worklog",
    category: "Runtime proof" as const,
    evidenceType: "acceptance",
    date: "2026-07-17",
    provesRo:
      "Letters Slice 1 resolver + PD/Aggregate/CPP/exec; RETURN-CANT ONLY ready",
    stillCurrentRuntime: true,
    source: "docs/worklog/realignment/2026-07-17_active_scope_module_independence_v1.md",
  },
] as const;
