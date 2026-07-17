/**
 * Current Truth Control Center V1 — shared present-truth projection.
 * Consumed by /modules and /governance — the ONLY official Level-1 current-truth source.
 * Present truth only; audits/worklogs are Level-3/4 evidence and must not override this file.
 * Read-only UI projection — not a control plane and not a second SoT.
 *
 * Concept dictionary + stabilization scope live in productSystemCanonicalModel.ts
 * (owner-approved Letters + Logo + ACM only).
 * Active-scope modularity law lives in activeScopeGovernanceTruth.ts.
 */

export {
  CANONICAL_CONCEPTS,
  CANONICAL_ROUTES,
  CAPABILITY_TYPES,
  COMPONENT_REPRESENTATION_INVENTORY,
  LEGACY_DOSSIER_ROUTE,
  MINI_MODULE_SCOPE_ROWS,
  SETTINGS_OWNERSHIP_ROWS,
  STABILIZATION_PRODUCTS,
} from "@/lib/productSystemCanonicalModel";

export {
  ACTIVE_SCOPE_EVIDENCE,
  ACTIVE_SCOPE_HANDOFFS,
  ACTIVE_SCOPE_KNOWN_DEFECTS_RO,
  ACTIVE_SCOPE_OWNERSHIP,
  ACTIVE_SCOPE_READINESS_LAW,
  ACTIVE_SCOPE_SYSTEM,
  ACTIVE_SCOPE_TARGET_HANDOFF_RO,
  ACTIVE_SCOPE_TARGET_NOTE_RO,
  DEPENDENCY_BINDING_RULE_RO,
  DEPENDENCY_CLASSES,
  DOCUMENTATION_AUTHORITY_RULE_RO,
  DOCUMENTATION_HIERARCHY,
  FULL_TEMPLATE_COUPLING_DEFECT,
  HYBRID_INTAKE_MODEL,
  MODULE_INDEPENDENCE_PRODUCT_STATUS,
  OFFICIAL_CURRENT_TRUTH_ROUTES,
  SYSTEM_REGISTRATION_REQUIRED_FIELDS,
  UNREGISTERED_SYSTEM_POLICY,
} from "@/lib/activeScopeGovernanceTruth";

export type PresentStatus =
  | "CONFIRMAT"
  | "PARTIAL"
  | "BLOCAT"
  | "INACTIV"
  | "NEVERIFICAT";

export type GovernanceEnforcementStatus =
  | "APLICAT"
  | "PARTIAL APLICAT"
  | "POLITICA OWNER"
  | "NEAPLICAT"
  | "NEVERIFICAT";

export type EvidenceCategory =
  | "Dovadă curentă"
  | "Dovadă istorică"
  | "Decizie owner"
  | "Referință arhitecturală";

export interface PresentSystem {
  id: string;
  labelRo: string;
  technicalName: string;
  owner: string;
  purposeRo: string;
  status: PresentStatus;
  inputRo: string;
  outputRo: string;
  consumerRo: string;
  limitationRo: string;
  verifyRoute: string;
  verifyEndpoint?: string;
  spineOrder: number;
}

export interface PresentHandoff {
  id: string;
  producerId: string;
  producerRo: string;
  consumerId: string;
  consumerRo: string;
  outputContractRo: string;
  enforcementRo: string;
  status: PresentStatus;
  verificationRo: string;
}

export interface PresentOwnershipRow {
  systemId: string;
  domainRo: string;
  technicalAlias: string;
  owner: string;
  semanticOwnershipRo: string;
  writeAuthorityRo: string;
  readOnlyRo: string;
  enforcementRo: string;
  status: PresentStatus;
}

export interface PresentBoundary {
  id: string;
  nameRo: string;
  technicalAlias: string;
  owner: string;
  truthControlledRo: string;
  allowedRo: string[];
  forbiddenRo: string[];
  enforcementRo: string;
  ownerGateRo: string;
  verificationRo: string;
  status: GovernanceEnforcementStatus;
}

export interface PresentGate {
  id: string;
  nameRo: string;
  blocksRo: string;
  approverRo: string;
  enforcementRo: string;
  verificationRo: string;
  withoutApprovalRo: string;
  status: GovernanceEnforcementStatus;
}

export interface PresentGuardrail {
  id: string;
  titleRo: string;
  requirementRo: string;
  enforcementRo: string;
  status: GovernanceEnforcementStatus;
  ownerGateRo: string;
}

export interface PresentEvidenceItem {
  id: string;
  title: string;
  category: EvidenceCategory;
  evidenceType: string;
  date: string;
  provesRo: string;
  stillCurrentRuntime: boolean;
  source: string;
}

/** Canonical primary WorkOS spine — only active spine in primary Modules view. */
export const CANONICAL_SPINE_LABELS_RO = [
  "Catalog produse",
  "Intake V6",
  "ProductDefinition",
  "ProductAggregate",
  "Pricing / Commercial",
  "Quote Snapshot",
  "Order Snapshot",
  "ExecutionPlan",
  "Execution Reality",
  "Post-Job",
] as const;

export const PRESENT_SYSTEMS: PresentSystem[] = [
  {
    id: "product_system",
    labelRo: "Catalog produse",
    technicalName: "Product System",
    owner: "Product System",
    purposeRo:
      "Deține limba de produs reutilizabilă: contract formular, module, dependențe, formule tehnice și definiții de măsurători comerciale (non-monetare).",
    status: "PARTIAL",
    inputRo: "Coduri șablon / definiții modul / registry",
    outputRo: "Contract formular + module consumabile de Intake / PD / Aggregate",
    consumerRo: "Intake V6, ProductDefinition, ProductAggregate",
    limitationRo:
      "Scope stabilizare: Litere + Logo + ACM. Familie ≠ Șablon ≠ Componentă ≠ Mini-modul ≠ Capability. Component storage = MIXED. Mini-module reuse global = NOT PROVEN. Renderer pilot Letters = PARTIAL. Nu deține tarife. Fără produse tip print textil sau colantări auto ca scope implementare.",
    verifyRoute: "/product-system",
    spineOrder: 1,
  },
  {
    id: "intake_v6",
    labelRo: "Intake V6",
    technicalName: "Intake V6 / Work Intake",
    owner: "Operator comercial / Sales",
    purposeRo: "Randează UI-ul de intake și capturează răspunsurile concrete din workspace.",
    status: "CONFIRMAT",
    inputRo: "Contract Product System (metadate/etichete Review) + intent client",
    outputRo: "Workspace + răspunsuri operator / selecție șablon",
    consumerRo: "ProductDefinition",
    limitationRo:
      "Letters: renderer generic (fără logică de produs) pentru secțiuni pilot; etichete/opțiuni/required din contract. Owns sold-scope selection + UI visibility — NU owns activare PD / Aggregate / pricing / execution scope. Hybrid entry PARTIAL. Layout grup + analyzer MIXED. Nu calculează total comercial autoritar.",
    verifyRoute: "/intake-v6",
    spineOrder: 2,
  },
  {
    id: "product_definition",
    labelRo: "Definiție produs",
    technicalName: "ProductDefinition",
    owner: "Product compile path",
    purposeRo:
      "Validează, normalizează și compilează configurația concretă; țintă: compiled active module set + active-scope readiness.",
    status: "PARTIAL",
    inputRo: "Răspunsuri Intake + contract Product System + offer_scope (Letters Slice 1)",
    outputRo: "Fapte ProductDefinition (geometrie, finisaje, module, readiness pe active scope)",
    consumerRo: "ProductAggregate",
    limitationRo:
      "ACTIVE-SCOPE READINESS = PROVEN FOR LETTERS SLICE 1. offer_scope → PD compile_active_scope. Nu calculează bani. Logo/ACM out of slice.",
    verifyRoute: "/intake-v6",
    spineOrder: 3,
  },
  {
    id: "product_aggregate",
    labelRo: "Structura tehnică a produsului",
    technicalName: "ProductAggregate",
    owner: "Aggregate composition",
    purposeRo:
      "Rezolvă adevărul tehnic (componente, cantități, operații, minute planificate) și emite măsurători comerciale non-monetare pentru CPP 7G — selected graph pe scope activ.",
    status: "PARTIAL",
    inputRo: "ProductDefinition / graf compilat + ActiveScopeResult",
    outputRo: "Aggregate tehnic + măsurători comerciale (fără preț) + task_contract",
    consumerRo: "CPP 7G (măsurători), ExecutionPlan (operații / minute)",
    limitationRo:
      "ACTIVE GRAPH = PROVEN FOR LETTERS SLICE 1. filter_aggregate_by_active_scope înainte de consumers. Nu emite prețuri. Logo/ACM out of slice.",
    verifyRoute: "/product-system",
    spineOrder: 4,
  },
  {
    id: "pricing_commercial",
    labelRo: "Pricing / Commercial",
    technicalName: "Commercial Pricing / CPP 7G",
    owner: "Commercial Pricing",
    purposeRo: "Singura autoritate monetară: transformă măsurători + reguli Pricing Registry în linii și total.",
    status: "PARTIAL",
    inputRo: "Măsurători Aggregate + Pricing Registry / reguli comerciale",
    outputRo: "Linii comerciale, prețuri, TVA, total pentru îngheț ofertă",
    consumerRo: "Quote Snapshot",
    limitationRo:
      "CPP 7G rămâne autoritate bani. Letters Slice 1 commercial_scope proven (live-calc/BOM/CPP unify). Legacy /entities/quotes/price (orar) retras (HTTP 410). Minutele nu sunt autoritate comercială. Rută canonică Pricing: /inventory/pricing.",
    verifyRoute: "/inventory/pricing",
    spineOrder: 5,
  },
  {
    id: "quote_snapshot",
    labelRo: "Quote Snapshot",
    technicalName: "Quotes / Quote Snapshot",
    owner: "Commercial freeze",
    purposeRo: "Îngheață propunerea comercială acceptată.",
    status: "CONFIRMAT",
    inputRo: "Rezultat comercial + context ofertă",
    outputRo: "Snapshot ofertă înghețat",
    consumerRo: "Order Snapshot",
    limitationRo: "Nu recalculează autoritar în UI; dual-cost debt rămâne cunoscut.",
    verifyRoute: "/quotes",
    spineOrder: 6,
  },
  {
    id: "order_snapshot",
    labelRo: "Order Snapshot",
    technicalName: "Orders / Order Snapshot",
    owner: "Commercial freeze / Orders",
    purposeRo: "Îngheață adevărul de comandă derivat din propunerea acceptată.",
    status: "CONFIRMAT",
    inputRo: "Quote Snapshot acceptat",
    outputRo: "Snapshot comandă înghețat",
    consumerRo: "ExecutionPlan",
    limitationRo: "Gate-ul de imutabilitate completă rămâne deschis pe unele căi.",
    verifyRoute: "/orders",
    spineOrder: 7,
  },
  {
    id: "execution_plan",
    labelRo: "Plan de execuție",
    technicalName: "ExecutionPlan",
    owner: "Execution path",
    purposeRo: "Deține adevărul operațional planificat înghețat.",
    status: "PARTIAL",
    inputRo: "Order Snapshot + Aggregate (operații / minute planificate)",
    outputRo: "Plan / task-uri planificate",
    consumerRo: "Execution Reality",
    limitationRo:
      "ACTIVE_OPERATIONS_ONLY când frozen sold_scope e prezent (CONFIRMED_WITH_GUARDS); CONFLICTED dacă Aggregate/snapshot nescopat. Minute Aggregate (TE2E-028A/B Letters); fără câmpuri comerciale pe plan.",
    verifyRoute: "/execution",
    spineOrder: 8,
  },
  {
    id: "execution_reality",
    labelRo: "Execuție reală",
    technicalName: "Execution Reality",
    owner: "Execution path",
    purposeRo: "Deține adevărul execuției reale (sesiuni / actuals).",
    status: "PARTIAL",
    inputRo: "ExecutionPlan",
    outputRo: "Actuals / sesiuni închise",
    consumerRo: "Post-Job",
    limitationRo: "Nu rescrie Quote, Order sau planul înghețat; acoperire actuals parțială.",
    verifyRoute: "/execution",
    spineOrder: 9,
  },
  {
    id: "post_job",
    labelRo: "Post-Job",
    technicalName: "PostJobTruth",
    owner: "Post-Job reconciliation (read-only)",
    purposeRo: "Reconciliere și învățare derivată din plan vs realitate.",
    status: "PARTIAL",
    inputRo: "ExecutionPlan + Execution Reality",
    outputRo: "Reconciliere matched / missing / variance (read-only)",
    consumerRo: "Operator review / învățare",
    limitationRo:
      "Fără write-back comercial; TE2E-028A static + TE2E-028B formula Letters PROVEN; TE2E-028 rămâne deschis (stoc G3 / labor $ / fixture / Letters breadth).",
    verifyRoute: "/execution",
    spineOrder: 10,
  },
];

/** Supporting systems — not spine nodes, but present ownership surfaces. */
export const PRESENT_SUPPORT_SYSTEMS: PresentSystem[] = [
  {
    id: "active_scope_sold_scope",
    labelRo: "Active Scope / Sold Scope",
    technicalName: "Active Scope / Sold Scope",
    owner: "ProductDefinition (compiled active scope) — Letters Slice 1 proven",
    purposeRo:
      "Rezolvă setul exact de module/componente cerut de client. Regula: modul neales ≠ problemă; modul ales trebuie să se susțină singur.",
    status: "PARTIAL",
    inputRo: "product template · offer_scope.mode · sold_modules · hard/conditional deps",
    outputRo: "active/inactive runtime sets · calc prerequisites · commercial + execution scope",
    consumerRo: "ProductAggregate · CPP 7G · Snapshots · ExecutionPlan",
    limitationRo:
      "PROVEN FOR LETTERS SLICE 1 — RETURN-CANT ONLY ready. Nu independență globală; Logo BLOCKED; ACM PARTIAL.",
    verifyRoute: "/modules",
    spineOrder: 0,
  },
  {
    id: "inventory",
    labelRo: "Inventar",
    technicalName: "Inventory",
    owner: "Inventory / Operational resources",
    purposeRo: "Stoc și achiziție — adevăr de resursă, nu preț ofertă.",
    status: "PARTIAL",
    inputRo: "Mișcări stoc / fișe",
    outputRo: "Stare inventar",
    consumerRo: "Operator / producție (citire)",
    limitationRo: "Nu este sursă de preț pentru oferte. Rută canonică: /inventory. Pricing Registry UI: /inventory/pricing.",
    verifyRoute: "/inventory",
    spineOrder: 0,
  },
  {
    id: "dossier",
    labelRo: "Dossier",
    technicalName: "Blueprint Dossier",
    owner: "Product System",
    purposeRo: "Documentație tehnică a șablonului — un singur traseu operator.",
    status: "CONFIRMAT",
    inputRo: "product-blueprint-dossiers + template",
    outputRo: "Dossier sections / completion metadata",
    consumerRo: "Product System / operator tehnic",
    limitationRo:
      "Canonic: /product-system/blueprint-dossier. /product-system/dossier-completion = legacy redirect. Fără al doilea Dossier operator.",
    verifyRoute: "/product-system/blueprint-dossier",
    spineOrder: 0,
  },
  {
    id: "attendance",
    labelRo: "Pontaj",
    technicalName: "Attendance / HR",
    owner: "HR / Pontaj",
    purposeRo: "Disponibilitate și pontaj unde e activ în runtime.",
    status: "NEVERIFICAT",
    inputRo: "Înregistrări prezență",
    outputRo: "Disponibilitate operatori",
    consumerRo: "Planificare (citire)",
    limitationRo: "Hartă Figma / control-center coverage nevalidată pe această pagină.",
    verifyRoute: "/attendance",
    spineOrder: 0,
  },
];

export const PRESENT_HANDOFFS: PresentHandoff[] = [
  {
    id: "h.ps_intake",
    producerId: "product_system",
    producerRo: "Catalog produse",
    consumerId: "intake_v6",
    consumerRo: "Intake V6",
    outputContractRo:
      "render_sections + field metadata (tip/opțiuni/required/visibility) pentru pilot Letters; writable_workspace_paths allowlist",
    enforcementRo: "GET form-contract + isContractRendererEnabled + IntakeContractSectionRenderer",
    status: "PARTIAL",
    verificationRo:
      "UI /intake-v6 · runtime_authority_scope=selected_sections:finisaje_fields,iluminare,montaj_template",
  },
  {
    id: "h.intake_pd",
    producerId: "intake_v6",
    producerRo: "Intake V6",
    consumerId: "product_definition",
    consumerRo: "ProductDefinition",
    outputContractRo:
      "Răspunsuri workspace + offer_scope (selecție) — PD consumă via compile_active_scope (Slice 1)",
    enforcementRo: "Intake V6 workspace + ProductDefinition compile path",
    status: "PARTIAL",
    verificationRo: "UI /intake-v6 · test_product_definition_active_scope · Active Scope handoff PROVEN",
  },
  {
    id: "h.pd_pa",
    producerId: "product_definition",
    producerRo: "ProductDefinition",
    consumerId: "product_aggregate",
    consumerRo: "ProductAggregate",
    outputContractRo: "Fapte canonice + module — Aggregate selected graph pe active scope (Slice 1)",
    enforcementRo: "Product compile → filter_aggregate_by_active_scope",
    status: "PARTIAL",
    verificationRo: "test_product_aggregate_active_scope_filter · workspace compose",
  },
  {
    id: "h.pa_cpp",
    producerId: "product_aggregate",
    producerRo: "ProductAggregate",
    consumerId: "pricing_commercial",
    consumerRo: "CPP 7G",
    outputContractRo:
      "Măsurători non-monetare scoped — commercial_scope_modules (Letters Slice 1 proven)",
    enforcementRo: "commercial_measurements → CPP 7G; linked-logo suppressed in component_subset",
    status: "PARTIAL",
    verificationRo: "test_intake_v6_live_calc_offer_scope · test_offer_scope_bom_*",
  },
  {
    id: "h.pa_plan",
    producerId: "product_aggregate",
    producerRo: "ProductAggregate",
    consumerId: "execution_plan",
    consumerRo: "ExecutionPlan",
    outputContractRo: "Componente, operații, task_contract, minute planificate (static + formula), proveniență",
    enforcementRo: "Plan V2 materializare din aggregate",
    status: "CONFIRMAT",
    verificationRo: "UI /execution · TE2E-028A/B",
  },
  {
    id: "h.pricing_quote",
    producerId: "pricing_commercial",
    producerRo: "Pricing / Commercial",
    consumerId: "quote_snapshot",
    consumerRo: "Quote Snapshot",
    outputContractRo: "Valori comerciale pentru îngheț",
    enforcementRo: "CPP 7G (nu UI)",
    status: "CONFIRMAT",
    verificationRo: "UI /quotes · snapshot comercial",
  },
  {
    id: "h.quote_order",
    producerId: "quote_snapshot",
    producerRo: "Quote Snapshot",
    consumerId: "order_snapshot",
    consumerRo: "Order Snapshot",
    outputContractRo: "Propunere comercială înghețată",
    enforcementRo: "Acceptare ofertă → freeze order",
    status: "CONFIRMAT",
    verificationRo: "UI /quotes → /orders",
  },
  {
    id: "h.order_plan",
    producerId: "order_snapshot",
    producerRo: "Order Snapshot",
    consumerId: "execution_plan",
    consumerRo: "ExecutionPlan",
    outputContractRo: "Snapshot comandă înghețat",
    enforcementRo: "Order lock → plan generation",
    status: "CONFIRMAT",
    verificationRo: "UI /orders → /execution",
  },
  {
    id: "h.plan_reality",
    producerId: "execution_plan",
    producerRo: "ExecutionPlan",
    consumerId: "execution_reality",
    consumerRo: "Execution Reality",
    outputContractRo: "Task-uri planificate",
    enforcementRo: "Execution sessions against plan",
    status: "PARTIAL",
    verificationRo: "UI /execution — plan vs sesiuni",
  },
  {
    id: "h.reality_postjob",
    producerId: "execution_reality",
    producerRo: "Execution Reality",
    consumerId: "post_job",
    consumerRo: "Post-Job",
    outputContractRo: "Actuals / sesiuni",
    enforcementRo: "PostJobTruth read-only reconciliation",
    status: "PARTIAL",
    verificationRo: "UI /execution — panou Post-Job",
  },
];

export const PRESENT_OWNERSHIP_ROWS: PresentOwnershipRow[] = [
  {
    systemId: "product_family",
    domainRo: "Familie de produs",
    technicalAlias: "Product Family",
    owner: "Product System",
    semanticOwnershipRo: "Grupare șabloane înrudite",
    writeAuthorityRo: "Registry product_families",
    readOnlyRo: "Intake / catalog",
    enforcementRo: "Nu deține module, opțiuni sau tarife",
    status: "CONFIRMAT",
  },
  {
    systemId: "product_template",
    domainRo: "Șablon de produs",
    technicalAlias: "Product Template",
    owner: "Product System",
    semanticOwnershipRo: "Composer rădăcină produs",
    writeAuthorityRo: "product_templates (+ module links)",
    readOnlyRo: "Intake / PD / Aggregate",
    enforcementRo: "Root offerable Letters; Logo/ACM PARTIAL",
    status: "PARTIAL",
  },
  {
    systemId: "component_template",
    domainRo: "Șablon de componentă",
    technicalAlias: "Component Template",
    owner: "Product System (concept)",
    semanticOwnershipRo: "Parte fizică reutilizabilă",
    writeAuthorityRo: "STORAGE_MIXED — BOM / child TPL / dossier (fără tabel first-class)",
    readOnlyRo: "Aggregate components",
    enforcementRo: "CONCEPT_CANONICAL — STORAGE_MIXED; migrare tabel = GO owner",
    status: "PARTIAL",
  },
  {
    systemId: "mini_module",
    domainRo: "Mini-modul",
    technicalAlias: "Mini-Module",
    owner: "Product System",
    semanticOwnershipRo: "Pachet operațional cu scope explicit",
    writeAuthorityRo: "Registry code (Letters-scoped)",
    readOnlyRo: "Form contract / PD / Aggregate",
    enforcementRo: "Scope LETTERS_ONLY / SHARED_WITHIN_SIGNAGE — nu generic global",
    status: "PARTIAL",
  },
  {
    systemId: "capability",
    domainRo: "Capability",
    technicalAlias: "Capability (UI)",
    owner: "PS declară tipul · FE mapează renderer",
    semanticOwnershipRo: "Tip interacțiune UI",
    writeAuthorityRo: "Nu stochează nume React; nu activează module producție",
    readOnlyRo: "Intake renderer mapping",
    enforcementRo: "Separate de mini-module / offerability catalog",
    status: "PARTIAL",
  },
  {
    systemId: "intake_v6",
    domainRo: "Intake V6 / Preluare lucrare",
    technicalAlias: "Intake V6 / Work Intake",
    owner: "Operator comercial / Sales",
    semanticOwnershipRo: "Selecție sold-scope · UI visibility · persistență workspace",
    writeAuthorityRo: "Workspace intake (operator)",
    readOnlyRo: "Catalog / contract Product System",
    enforcementRo: "NU owns activare PD · Aggregate graph · pricing scope · execution scope",
    status: "CONFIRMAT",
  },
  {
    systemId: "product_system",
    domainRo: "Catalog produse",
    technicalAlias: "Product System",
    owner: "Product System",
    semanticOwnershipRo:
      "Limbă produs + contract formular + module + formule tehnice + definiții măsurători (non-monetare)",
    writeAuthorityRo: "Product System admin / builder",
    readOnlyRo: "Intake, PD, Aggregate (consum)",
    enforcementRo: "Scope Litere+Logo+ACM; form full MIXED; fără banner/vehicle",
    status: "PARTIAL",
  },
  {
    systemId: "product_definition",
    domainRo: "Definiție produs",
    technicalAlias: "ProductDefinition",
    owner: "Product compile path",
    semanticOwnershipRo:
      "Compiled active module set · hard/conditional deps · active-scope readiness",
    writeAuthorityRo: "Compile path (sistem) — autoritate activare",
    readOnlyRo: "Aggregate (consum)",
    enforcementRo: "PROVEN Letters Slice 1 — compile_active_scope + readiness pe module active",
    status: "PARTIAL",
  },
  {
    systemId: "active_scope_sold_scope",
    domainRo: "Active Scope / Sold Scope",
    technicalAlias: "Active Scope / Sold Scope",
    owner: "ProductDefinition (compiled) — Slice 1 proven",
    semanticOwnershipRo: "Set runtime activ/inactiv din offer_scope + hard deps",
    writeAuthorityRo: "PD compile via active_scope_resolver_service",
    readOnlyRo: "Intake selecție · Aggregate/CPP/Exec consum",
    enforcementRo: "PROVEN FOR LETTERS SLICE 1 — FULL_TEMPLATE_COUPLING remediat pe slice",
    status: "PARTIAL",
  },
  {
    systemId: "product_aggregate",
    domainRo: "Structura tehnică a produsului",
    technicalAlias: "ProductAggregate",
    owner: "Aggregate composition",
    semanticOwnershipRo:
      "Selected technical graph · active components/materials/ops · active commercial measurements",
    writeAuthorityRo: "Aggregate composition (sistem)",
    readOnlyRo: "CPP 7G (măsurători), ExecutionPlan (operații/minute)",
    enforcementRo: "PROVEN Letters Slice 1 — selected graph înainte de consumers",
    status: "PARTIAL",
  },
  {
    systemId: "pricing_commercial",
    domainRo: "Pricing / Commercial",
    technicalAlias: "CPP 7G / Pricing Registry",
    owner: "Commercial Pricing",
    semanticOwnershipRo: "Bani numai pentru măsurători comerciale active",
    writeAuthorityRo: "CPP 7G + Pricing Registry (backend)",
    readOnlyRo: "UI Quotes (afișare)",
    enforcementRo: "STANDALONE PRICING = CONFLICTED (path-dependent); fără minute ca preț",
    status: "PARTIAL",
  },
  {
    systemId: "quote_snapshot",
    domainRo: "Quote Snapshot",
    technicalAlias: "Quotes",
    owner: "Commercial freeze",
    semanticOwnershipRo: "Propunere comercială înghețată",
    writeAuthorityRo: "Freeze la acceptare",
    readOnlyRo: "Orders (consum snapshot)",
    enforcementRo: "Quote snapshot freeze",
    status: "CONFIRMAT",
  },
  {
    systemId: "order_snapshot",
    domainRo: "Order Snapshot",
    technicalAlias: "Orders",
    owner: "Orders / Commercial freeze",
    semanticOwnershipRo: "Comandă înghețată",
    writeAuthorityRo: "Order lock din quote acceptat",
    readOnlyRo: "ExecutionPlan (consum)",
    enforcementRo: "Order snapshot freeze",
    status: "CONFIRMAT",
  },
  {
    systemId: "execution_plan",
    domainRo: "Plan de execuție",
    technicalAlias: "ExecutionPlan",
    owner: "Execution path",
    semanticOwnershipRo: "Operații active numai din frozen sold_scope",
    writeAuthorityRo: "Generare plan din snapshot/contract",
    readOnlyRo: "Execution Reality (consum plan)",
    enforcementRo: "ACTIVE_OPERATIONS_ONLY / CONFLICTED fără frozen scope",
    status: "PARTIAL",
  },
  {
    systemId: "execution_reality",
    domainRo: "Execuție reală",
    technicalAlias: "Execution Reality",
    owner: "Execution path",
    semanticOwnershipRo: "Actuals / sesiuni",
    writeAuthorityRo: "Sesiuni execuție",
    readOnlyRo: "Post-Job (citire)",
    enforcementRo: "Execution session APIs",
    status: "PARTIAL",
  },
  {
    systemId: "post_job",
    domainRo: "Post-Job",
    technicalAlias: "PostJobTruth",
    owner: "Post-Job (read-only)",
    semanticOwnershipRo: "Reconciliere derivată",
    writeAuthorityRo: "Nicio scriere comercială",
    readOnlyRo: "Operator review",
    enforcementRo: "PostJobTruth projection",
    status: "PARTIAL",
  },
  {
    systemId: "dossier",
    domainRo: "Dossier",
    technicalAlias: "Blueprint Dossier",
    owner: "Product System",
    semanticOwnershipRo: "Documentație tehnică șablon — un traseu",
    writeAuthorityRo: "Blueprint Dossier Studio",
    readOnlyRo: "Completion metrics (legacy redirect)",
    enforcementRo: "Canonic /product-system/blueprint-dossier",
    status: "CONFIRMAT",
  },
  {
    systemId: "inventory",
    domainRo: "Inventar",
    technicalAlias: "Inventory",
    owner: "Inventory",
    semanticOwnershipRo: "Stoc / achiziție",
    writeAuthorityRo: "Inventory services",
    readOnlyRo: "Producție (citire)",
    enforcementRo: "/inventory · pricing UI /inventory/pricing",
    status: "PARTIAL",
  },
  {
    systemId: "attendance",
    domainRo: "Pontaj / HR",
    technicalAlias: "Attendance",
    owner: "HR / Pontaj",
    semanticOwnershipRo: "Disponibilitate",
    writeAuthorityRo: "Attendance where active",
    readOnlyRo: "Planificare",
    enforcementRo: "Attendance routes (unde active)",
    status: "NEVERIFICAT",
  },
];

export const PRESENT_BOUNDARIES: PresentBoundary[] = [
  {
    id: "b.pricing",
    nameRo: "Pricing comercial",
    technicalAlias: "Commercial Pricing",
    owner: "Commercial Pricing",
    truthControlledRo: "Calcul comercial autoritar",
    allowedRo: [
      "Calculează valori comerciale în backend",
      "Livrează input pentru îngheț ofertă",
    ],
    forbiddenRo: [
      "UI-ul nu calculează valori comerciale autoritare",
      "Orele/minutele nu sunt autoritate de pricing comercial",
      "Legacy POST /entities/quotes/price retras — nu mai este autoritate comercială",
      "Inventarul nu este sursă de preț ofertă",
    ],
    enforcementRo: "Servicii commercial pricing / preview boundary",
    ownerGateRo: "Schimbări de autoritate pricing = GO owner",
    verificationRo: "/inventory/pricing · /quotes · contracte commercial preview",
    status: "PARTIAL APLICAT",
  },
  {
    id: "b.quote",
    nameRo: "Quote Snapshot",
    technicalAlias: "Quotes",
    owner: "Commercial freeze",
    truthControlledRo: "Propunere comercială acceptată înghețată",
    allowedRo: ["Îngheață oferta acceptată", "Versionare snapshot ofertă"],
    forbiddenRo: [
      "Nu recalculează autoritar structura produsului",
      "Nu inventează costuri lipsă în UI",
    ],
    enforcementRo: "Quote snapshot freeze path",
    ownerGateRo: "Mutare adevăr înghețat = GO owner",
    verificationRo: "/quotes",
    status: "APLICAT",
  },
  {
    id: "b.order",
    nameRo: "Order Snapshot",
    technicalAlias: "Orders",
    owner: "Orders",
    truthControlledRo: "Adevăr comandă derivat din propunerea acceptată",
    allowedRo: ["Îngheață comanda din quote acceptat", "Input oficial pentru plan"],
    forbiddenRo: ["Nu recalculează oferta", "Nu reconfigurează produsul după lock"],
    enforcementRo: "Order snapshot freeze",
    ownerGateRo: "Mutare snapshot comandă = GO owner",
    verificationRo: "/orders",
    status: "APLICAT",
  },
  {
    id: "b.plan",
    nameRo: "ExecutionPlan",
    technicalAlias: "ExecutionPlan",
    owner: "Execution path",
    truthControlledRo: "Adevăr operațional planificat înghețat",
    allowedRo: ["Materializează task-uri din contract/snapshot", "Citește Order Snapshot"],
    forbiddenRo: ["Nu rescrie Quote/Order", "Nu inventează produsul amonte"],
    enforcementRo: "Plan V2 generation",
    ownerGateRo: "Schimbare contract plan = GO owner",
    verificationRo: "/execution",
    status: "PARTIAL APLICAT",
  },
  {
    id: "b.reality",
    nameRo: "Execution Reality",
    technicalAlias: "Execution Reality",
    owner: "Execution path",
    truthControlledRo: "Adevăr execuție reală",
    allowedRo: ["Înregistrează actuals / sesiuni", "Consumă planul"],
    forbiddenRo: [
      "Nu rescrie Quote Snapshot",
      "Nu rescrie Order Snapshot",
      "Nu rescrie adevărul planificat ca și cum ar fi actual",
    ],
    enforcementRo: "Execution session APIs",
    ownerGateRo: "Mutare actuals înghețate = GO owner",
    verificationRo: "/execution",
    status: "PARTIAL APLICAT",
  },
  {
    id: "b.postjob",
    nameRo: "Post-Job",
    technicalAlias: "PostJobTruth",
    owner: "Post-Job",
    truthControlledRo: "Reconciliere / învățare derivată",
    allowedRo: ["Compară plan vs realitate (read-only)", "Expune matched/missing/variance"],
    forbiddenRo: ["Fără write-back comercial", "Nu mută autoritatea de pricing"],
    enforcementRo: "PostJobTruth projection",
    ownerGateRo: "Orice write-back = STOP / GO owner",
    verificationRo: "/execution — Post-Job",
    status: "PARTIAL APLICAT",
  },
  {
    id: "b.product_system",
    nameRo: "Product System",
    technicalAlias: "Product System",
    owner: "Product System",
    truthControlledRo: "Limbă produs, contract formular, module, formule tehnice, definiții măsurători",
    allowedRo: [
      "Definește șabloane și module",
      "Metadate câmp + etichete Review Letters (scope=review_labels)",
      "Availability / activation scope",
    ],
    forbiddenRo: [
      "Nu deține tarife / prețuri",
      "Nu deține selecții workspace concrete",
      "Nu calculează total comercial",
      "Nu pretinde generare completă de formular din contract Letters",
      "Nu deține inventar real / actuals",
      "Nu promovează suport global din dovadă Letters-only",
    ],
    enforcementRo: "Registry + modular form contract + Control Center scope (PARTIAL code for labels)",
    ownerGateRo: "Activare root product / extindere șablon = GO owner",
    verificationRo: "/product-system · /modules · /governance",
    status: "PARTIAL APLICAT",
  },
  {
    id: "b.product_aggregate",
    nameRo: "ProductAggregate",
    technicalAlias: "ProductAggregate",
    owner: "Aggregate composition",
    truthControlledRo: "Adevăr tehnic + măsurători comerciale non-monetare + minute planificate",
    allowedRo: [
      "Emite componente, cantități, operații",
      "Emite măsurători comerciale (cantitate/unitate/cheie)",
      "Emite minute planificate operaționale",
    ],
    forbiddenRo: [
      "Nu emite unit_price / total / TVA / discount",
      "Nu pune planned_minutes sau actual_minutes în măsurători comerciale",
      "Nu calculează preț orar comercial",
    ],
    enforcementRo: "commercial_measurement_contract + teste Letters",
    ownerGateRo: "Schimbare contract măsurători = GO owner",
    verificationRo: "tests/test_letters_commercial_measurement_contract.py",
    status: "APLICAT",
  },
];

export const PRESENT_GATES: PresentGate[] = [
  {
    id: "g.owner_business",
    nameRo: "GO owner — comportament business",
    blocksRo: "Schimbări de comportament business fără aprobare",
    approverRo: "Owner",
    enforcementRo: "Politică owner (proces) — nu motor RBAC în UI",
    verificationRo: "Worklog / master status + review owner",
    withoutApprovalRo: "Schimbarea rămâne neautorizată",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_schema",
    nameRo: "GO owner — schemă / migrare",
    blocksRo: "Schema DB / migrări",
    approverRo: "Owner",
    enforcementRo: "Politică owner + review PR",
    verificationRo: "Absența migrărilor neaprobate în scope",
    withoutApprovalRo: "STOP implementare",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_seed",
    nameRo: "GO owner — seed permanent",
    blocksRo: "Seed permanent / date de referință permanente",
    approverRo: "Owner",
    enforcementRo: "Politică owner",
    verificationRo: "Scripturi seed + review",
    withoutApprovalRo: "STOP",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_frozen",
    nameRo: "GO owner — adevăr înghețat",
    blocksRo: "Mutarea Quote/Order/plan înghețat",
    approverRo: "Owner",
    enforcementRo: "Freeze paths + politică owner",
    verificationRo: "/quotes · /orders · /execution",
    withoutApprovalRo: "Mutarea este interzisă",
    status: "PARTIAL APLICAT",
  },
  {
    id: "g.owner_activation",
    nameRo: "GO owner — activare produs root",
    blocksRo: "Activare root product / șablon nou în flux operator",
    approverRo: "Owner",
    enforcementRo: "Politică owner + Product System scope",
    verificationRo: "/product-system availability",
    withoutApprovalRo: "Activarea rămâne în afara scope",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_pricing",
    nameRo: "GO owner — autoritate pricing",
    blocksRo: "Schimbări de autoritate / semantică pricing",
    approverRo: "Owner",
    enforcementRo: "Politică owner (CostEngine/Pricing protected)",
    verificationRo: "Review dedicat + teste pricing",
    withoutApprovalRo: "STOP",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_boundary",
    nameRo: "GO owner — limite de sistem",
    blocksRo: "Schimbări de boundary între sisteme",
    approverRo: "Owner",
    enforcementRo: "Politică owner + documente master",
    verificationRo: "/governance · /modules",
    withoutApprovalRo: "STOP",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_new_template",
    nameRo: "GO owner — produs / șablon nou",
    blocksRo: "Familie nouă, șablon nou, ieșire din Litere+Logo+ACM",
    approverRo: "Owner",
    enforcementRo: "Scope stabilizare + politică owner",
    verificationRo: "/product-system · STABILIZATION_PRODUCTS",
    withoutApprovalRo: "STOP — nu inventăm banner/vehicle",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_component_migration",
    nameRo: "GO owner — migrare model componentă",
    blocksRo: "Tabel component_templates / migrare storage",
    approverRo: "Owner",
    enforcementRo: "Schema gate — STORAGE_MIXED până la GO",
    verificationRo: "Absența migrării component_templates",
    withoutApprovalRo: "STOP schema",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_module_scope",
    nameRo: "GO owner — scope mini-modul",
    blocksRo: "Extindere mini-modul cross-family / claim generic",
    approverRo: "Owner",
    enforcementRo: "MINI_MODULE_SCOPE_ROWS + registry applies_to",
    verificationRo: "/modules vocabular",
    withoutApprovalRo: "Rămâne scoped Letters/signage",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_capability",
    nameRo: "GO owner — capability nouă",
    blocksRo: "Tip capability UI nou / mapare renderer",
    approverRo: "Owner",
    enforcementRo: "Capability ≠ mini-module; fără nume React în PS",
    verificationRo: "CAPABILITY_TYPES",
    withoutApprovalRo: "Nu se adaugă în catalog produse",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_option_authority",
    nameRo: "GO owner — autoritate opțiuni",
    blocksRo: "Mutare cataloage opțiuni / dual authority FE",
    approverRo: "Owner",
    enforcementRo: "SETTINGS_OWNERSHIP_ROWS conflicts",
    verificationRo: "Triple finish catalogs / dual markup",
    withoutApprovalRo: "Conflict rămâne vizibil; fără silent rewrite",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_dossier_route",
    nameRo: "GO owner — rută Dossier",
    blocksRo: "Al doilea Dossier operator / schimbare canonică",
    approverRo: "Owner",
    enforcementRo: "Un singur canonic: /product-system/blueprint-dossier",
    verificationRo: "Redirect legacy dossier-completion",
    withoutApprovalRo: "STOP dual Dossier",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_inventory_pricing_route",
    nameRo: "GO owner — rute Inventory/Pricing",
    blocksRo: "Rute alternative Inventory/Pricing",
    approverRo: "Owner",
    enforcementRo: "/inventory · /inventory/pricing only",
    verificationRo: "CANONICAL_ROUTES + Control Center links",
    withoutApprovalRo: "Link greșit = defect adevăr prezent",
    status: "POLITICA OWNER",
  },
  {
    id: "g.owner_active_scope_runtime",
    nameRo: "GO owner — Active Scope runtime (PD/Aggregate/CPP)",
    blocksRo:
      "Extindere dincolo de Letters Slice 1 (Logo/ACM independence, FINISH/MOUNTING sold, task materialization)",
    approverRo: "Owner",
    enforcementRo: "Letters Slice 1 proven sub GO ACTIVE_SCOPE_MODULE_INDEPENDENCE_V1 — nu overclaim global",
    verificationRo: "/modules Active Scope · /governance G14 · worklog active_scope_module_independence_v1",
    withoutApprovalRo: "STOP — nu activa Logo/ACM ca independență de modul",
    status: "POLITICA OWNER",
  },
];

export const PRESENT_GUARDRAILS: PresentGuardrail[] = [
  {
    id: "G01",
    titleRo: "Nu amesteca rolurile sistemelor",
    requirementRo:
      "Product System definește contractul; Intake capturează răspunsuri; ProductDefinition compilează; ProductAggregate rezolvă tehnic + măsurători non-monetare; CPP 7G calculează banii; ExecutionPlan consumă minute operaționale; Execution Reality deține actuals; Post-Job rămâne read-only.",
    enforcementRo: "Politică arhitecturală + contracte de boundary (nu RBAC)",
    status: "POLITICA OWNER",
    ownerGateRo: "Schimbare de rol sistem = GO owner",
  },
  {
    id: "G14",
    titleRo: "Readiness numai pe module active",
    requirementRo:
      "Readiness se evaluează numai pentru modulele active. Modulele inactive: nu cer setări, nu generează missing fields, nu creează warnings, linii comerciale, operații sau task-uri. Un modul neales nu este o problemă; un modul ales trebuie să se susțină singur.",
    enforcementRo: "PROVEN FOR LETTERS SLICE 1 — compile_active_scope + PD readiness scoped",
    status: "PARTIAL APLICAT",
    ownerGateRo: "Extindere Logo/ACM = GO owner separat",
  },
  {
    id: "G15",
    titleRo: "Control Center = singura documentație curentă oficială",
    requirementRo:
      "/modules și /governance sunt Level 1 — adevăr curent oficial. Audits/worklogs = dovezi (Level 3/4). Runtime dovedește ce există; Modules ce e oficial; Governance ce e permis.",
    enforcementRo: "DOCUMENTATION_HIERARCHY + OFFICIAL_CURRENT_TRUTH_ROUTES",
    status: "APLICAT",
    ownerGateRo: "Schimbare ierarhie docs = GO owner",
  },
  {
    id: "G16",
    titleRo: "Sistem neregistrat (UNREGISTERED_SYSTEM)",
    requirementRo:
      "Un sistem arhitectural/motor/registry/flux/modul/capability/rută publică/autoritate contract este oficial doar dacă e înregistrat cu câmpurile obligatorii. UNREGISTERED_SYSTEM: poate fi auditat; nu poate fi SoT, E2E canonic sau production-ready.",
    enforcementRo: "SYSTEM_REGISTRATION_REQUIRED_FIELDS + UNREGISTERED_SYSTEM_POLICY",
    status: "APLICAT",
    ownerGateRo: "Înregistrare sistem nou = GO owner",
  },
  {
    id: "G17",
    titleRo: "Dependențe de compoziție ≠ universale",
    requirementRo:
      "Clase: hard technical · conditional · composition-only · commercial · execution. Dependențele composition-only nu trebuie să devină dependențe universale de modul (ex. lipire față–cant ≠ obligatoriu pentru return singur).",
    enforcementRo: "DEPENDENCY_CLASSES — politică; runtime încă REWORK",
    status: "POLITICA OWNER",
    ownerGateRo: "Encoding composition deps as universal = defect",
  },
  {
    id: "G03",
    titleRo: "UI-ul nu mută logica de business",
    requirementRo: "Nu muta calculul comercial autoritar în frontend. UI afișează și orchestrează.",
    enforcementRo: "Commercial preview boundary + review",
    status: "PARTIAL APLICAT",
    ownerGateRo: "Orice mutare de autoritate = GO owner",
  },
  {
    id: "G05",
    titleRo: "Implementarea nu devine SoT arhitectural",
    requirementRo: "Codul arată ce există; conflictele cu documentele master se escaladează.",
    enforcementRo: "Politică owner",
    status: "POLITICA OWNER",
    ownerGateRo: "Arbitraj owner",
  },
  {
    id: "G06",
    titleRo: "UI reflectă adevărul, nu-l inventează",
    requirementRo: "Nu inventa statusuri LIVE/COMPLETE fără dovadă runtime.",
    enforcementRo: "UI-TRUTH-01B banner + acest Control Center",
    status: "PARTIAL APLICAT",
    ownerGateRo: "UI-TRUTH-01C rămâne PAUSED pentru drill-down",
  },
  {
    id: "G13",
    titleRo: "UTF-8 end-to-end pentru textul operator",
    requirementRo:
      "Textul uman vizibil și persistat folosește UTF-8 pe tot lanțul (sursă → DB → API → UI). Niciun sistem nu convertește tacit Unicode prin Latin-1/Windows-1252.",
    enforcementRo: "Seed/tests/helpers + politică G13 (aplicare parțială pe tot lanțul)",
    status: "PARTIAL APLICAT",
    ownerGateRo: "Regresie encoding = reopen controlat",
  },
];

export const PRESENT_EVIDENCE: PresentEvidenceItem[] = [
  {
    id: "ev.health_api",
    title: "Runtime health API",
    category: "Dovadă curentă",
    evidenceType: "api",
    date: "2026-07-17",
    provesRo: "Aggregate health status citit live; checks publice pot fi goale",
    stillCurrentRuntime: true,
    source: "GET /api/v1/system/health",
  },
  {
    id: "ev.ui_truth_01b",
    title: "UI-TRUTH-01B — banner runtime real",
    category: "Dovadă curentă",
    evidenceType: "acceptance",
    date: "2026-07-17",
    provesRo: "EnvironmentBanner folosește useRuntimeHealth (nu auth-derived LIVE/DB)",
    stillCurrentRuntime: true,
    source: "docs/plans/2026-07-17_ui_truth_01b_unpause_plan.md",
  },
  {
    id: "ev.same_scenario",
    title: "Same-scenario E2E PROVEN_V1 (Build 1)",
    category: "Dovadă istorică",
    evidenceType: "qa",
    date: "2026-07-16",
    provesRo: "Spine Letters request→post-job pe scenariu determinist local",
    stillCurrentRuntime: false,
    source: "docs/qa/BUILD_SAME_SCENARIO_REQUEST_TO_POST_JOB_E2E_V1.md",
  },
  {
    id: "ev.w7_t02",
    title: "W7-T02 Post-Job reconciliation breadth",
    category: "Dovadă istorică",
    evidenceType: "qa",
    date: "2026-07-17",
    provesRo: "Reconciliere matched/missing/variance pe orders de referință",
    stillCurrentRuntime: false,
    source: "docs/qa/w7-t02-reconciliation-2026-07-17/",
  },
  {
    id: "ev.w7_owner",
    title: "Wave 7 OWNER_ACCEPTED",
    category: "Decizie owner",
    evidenceType: "acceptance",
    date: "2026-07-17",
    provesRo: "Wave 7 semnat; TE2E-028 rămâne residual deschis",
    stillCurrentRuntime: false,
    source: "docs/plans/2026-07-17_w7_t03_owner_signoff_checklist.md",
  },
  {
    id: "ev.te2e_028a",
    title: "TE2E-028A Planning-minute source integrity",
    category: "Dovadă curentă",
    evidenceType: "qa",
    date: "2026-07-17",
    provesRo:
      "Minute planificate statice (ex. Control calitate=15 min) supraviețuiesc aggregate→preview→plan→Post-Job; UI /execution/972901 verificat (Plan vs execuție); missing actual rămâne explicit; fără write-back; TE2E-028 rămâne deschis",
    stillCurrentRuntime: true,
    source: "docs/qa/te2e-028a-planning-minutes-2026-07-17/",
  },
  {
    id: "ev.te2e_028b",
    title: "TE2E-028B Formula planning-duration authority",
    category: "Dovadă curentă",
    evidenceType: "qa",
    date: "2026-07-17",
    provesRo:
      "Letters vector_prep: count_based_time rezolvat în ProductAggregate (5 litere → 10 min); Plan/Post-Job consumă proveniența formula; UI /execution/972910 Plan vs execuție; comercial 1888 neschimbat; CostEngine/EIC nu sunt autoritate Plan; TE2E-028 rămâne deschis pe residuals",
    stillCurrentRuntime: true,
    source: "docs/worklog/realignment/2026-07-17_te2e_028b_formula_planning_duration_authority_audit.md",
  },
  {
    id: "ev.letters_canonical_slice",
    title: "LETTERS_CANONICAL_PRODUCT_SLICE_V1",
    category: "Dovadă curentă",
    evidenceType: "qa",
    date: "2026-07-17",
    provesRo:
      "PARTIAL + renderer pilot: render_sections Iluminare/Montaj șablon (+ Finisaje fără layout grup) din Product System; Aggregate măsurători → CPP cu fallback; baseline freeze 3549.1286/4294.45; layout grup/analyzer MIXED; Quote→Order→Plan nou NOT PROVEN",
    stillCurrentRuntime: true,
    source: "docs/worklog/realignment/2026-07-17_intake_v6_generic_contract_renderer_letters_pilot.md",
  },
  {
    id: "ev.e2e_truth_audit",
    title: "E2E Product System → Intake → Commercial truth audit",
    category: "Decizie owner",
    evidenceType: "acceptance",
    date: "2026-07-17",
    provesRo:
      "Audit aprobat + closure verification: Intake form source rămâne MIXED; Aggregate→CPP handoff proven cu fallback; owner status PARTIAL — CONTRACT AND PRICING HANDOFF PROVEN",
    stillCurrentRuntime: true,
    source: "docs/audits/2026-07-17_product_system_intake_commercial_e2e_truth_audit.md",
  },
  {
    id: "ev.legacy_quote_price_isolated",
    title: "Legacy hourly quote /price isolated",
    category: "Dovadă curentă",
    evidenceType: "qa",
    date: "2026-07-17",
    provesRo:
      "POST /entities/quotes/price retras (410, absent OpenAPI); QuoteWizard nu mai apelează legacy; autoritate comercială activă rămâne Intake V6 → 7G",
    stillCurrentRuntime: true,
    source: "docs/worklog/realignment/2026-07-17_commercial_pricing_time_isolation_audit.md",
  },
  {
    id: "ev.legacy_oc_tk",
    title: "Lanț istoric OC→TK (referință)",
    category: "Referință arhitecturală",
    evidenceType: "architecture",
    date: "pre-2026-07",
    provesRo: "Model vechi de handoff OC→WI→PS→CE→QT→OR→WO→TK — nu fluxul activ",
    stillCurrentRuntime: false,
    source: "useModuleChainData CONTRACT_HANDOFFS (istoric)",
  },
  {
    id: "ev.page_completion",
    title: "Page Completion Foundation",
    category: "Referință arhitecturală",
    evidenceType: "document",
    date: "2026-07",
    provesRo: "Contract de completare pagină / DoD",
    stillCurrentRuntime: true,
    source: "docs/architecture/WORKOS_PAGE_COMPLETION_FOUNDATION.md",
  },
  {
    id: "ev.ui_truth_01c_paused",
    title: "UI-TRUTH-01C PAUSED",
    category: "Decizie owner",
    evidenceType: "decision",
    date: "2026-07-17",
    provesRo: "Failure/stale/retry/drill-down rămâne pauzat până după Control Center",
    stillCurrentRuntime: true,
    source: "docs/plans/2026-07-17_ui_truth_01c_scope_plan.md",
  },
  {
    id: "ev.module_independence_audit",
    title: "Module independence E2E audit (approved)",
    category: "Decizie owner",
    evidenceType: "acceptance",
    date: "2026-07-17",
    provesRo:
      "FULL_TEMPLATE_COUPLING_FOUND baseline — Level-3 evidence, nu override Control Center",
    stillCurrentRuntime: false,
    source: "docs/audits/2026-07-17_product_system_module_independence_e2e_audit.md",
  },
  {
    id: "ev.module_independence_worklog",
    title: "Module independence audit worklog",
    category: "Dovadă istorică",
    evidenceType: "worklog",
    date: "2026-07-17",
    provesRo: "Level-4 history — nu definește adevărul curent oficial",
    stillCurrentRuntime: false,
    source: "docs/worklog/realignment/2026-07-17_product_system_module_independence_e2e_audit.md",
  },
  {
    id: "ev.active_scope_v1_worklog",
    title: "Active scope module independence V1",
    category: "Runtime proof",
    evidenceType: "acceptance",
    date: "2026-07-17",
    provesRo:
      "Letters Slice 1 proven — RETURN-CANT ONLY ready; Level-3 evidence under /modules+/governance",
    stillCurrentRuntime: true,
    source: "docs/worklog/realignment/2026-07-17_active_scope_module_independence_v1.md",
  },
];

export const MODULE_CHAIN_TABS = [
  { id: "system_map" as const, labelRo: "Harta sistemelor" },
  { id: "handoffs" as const, labelRo: "Contracte și transferuri" },
  { id: "runtime" as const, labelRo: "Stare runtime" },
  { id: "evidence" as const, labelRo: "Surse și dovezi" },
];

export type ModuleChainTabId = (typeof MODULE_CHAIN_TABS)[number]["id"];

export function presentStatusBadgeClass(status: PresentStatus): string {
  if (status === "CONFIRMAT") return "bg-emerald-900/30 text-emerald-300 border-emerald-700";
  if (status === "PARTIAL") return "bg-amber-900/30 text-amber-300 border-amber-700";
  if (status === "BLOCAT") return "bg-red-900/30 text-red-300 border-red-700";
  if (status === "INACTIV") return "bg-slate-700/50 text-slate-400 border-slate-600";
  return "bg-slate-700/60 text-slate-300 border-slate-600";
}

export function governanceStatusBadgeClass(status: GovernanceEnforcementStatus): string {
  if (status === "APLICAT") return "bg-emerald-900/30 text-emerald-300 border-emerald-700";
  if (status === "PARTIAL APLICAT") return "bg-amber-900/30 text-amber-300 border-amber-700";
  if (status === "POLITICA OWNER") return "bg-blue-900/30 text-blue-300 border-blue-700";
  if (status === "NEAPLICAT") return "bg-red-900/30 text-red-300 border-red-700";
  return "bg-slate-700/60 text-slate-300 border-slate-600";
}

/** Cross-page helpers — same names/owners for Modules + Governance. */
export function getSystemById(id: string): PresentSystem | undefined {
  return [...PRESENT_SYSTEMS, ...PRESENT_SUPPORT_SYSTEMS].find((s) => s.id === id);
}

export function ownershipForSystem(systemId: string): PresentOwnershipRow | undefined {
  return PRESENT_OWNERSHIP_ROWS.find((r) => r.systemId === systemId);
}

export function assertNoMojibake(text: string): boolean {
  // Reject common UTF-8 mojibake markers in operator-visible strings.
  return !text.includes("\uFFFD") && !/Ã.|Â.|â€/.test(text);
}
