/**
 * Current Truth Control Center V1 — shared present-truth projection.
 * Consumed by /modules and /governance. Present truth only; history is evidence.
 * Read-only UI projection — not a control plane and not a second SoT.
 */

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
    id: "intake_v6",
    labelRo: "Intake V6",
    technicalName: "Intake V6 / Work Intake",
    owner: "Operator comercial / Sales",
    purposeRo: "Preluare cerere și spațiu de lucru cu selecție șablon activ.",
    status: "CONFIRMAT",
    inputRo: "Intent client, canal, familie produs",
    outputRo: "Workspace + selecție șablon / context cerere",
    consumerRo: "ProductDefinition, Catalog produse (Product System)",
    limitationRo: "UX Step2 și acoperirea șabloanelor rămân parțiale (nu doar Letters).",
    verifyRoute: "/intake-v6",
    spineOrder: 1,
  },
  {
    id: "product_definition",
    labelRo: "Definiție produs",
    technicalName: "ProductDefinition",
    owner: "Product compile path",
    purposeRo: "Compilează / previzualizează definiția produsului din compoziție.",
    status: "PARTIAL",
    inputRo: "Compoziție + selecție șablon din Intake",
    outputRo: "Graf / definiție compilată",
    consumerRo: "ProductAggregate",
    limitationRo: "Fără pagină operator dedicată — verificare prin API / flux embedded.",
    verifyRoute: "/intake-v6",
    spineOrder: 2,
  },
  {
    id: "product_aggregate",
    labelRo: "Structura tehnică a produsului",
    technicalName: "ProductAggregate",
    owner: "Aggregate composition",
    purposeRo: "Produce agregatul tehnic (BOM / task_contract) pentru plan și comercial.",
    status: "PARTIAL",
    inputRo: "ProductDefinition / graf compilat",
    outputRo: "Aggregate + task_contract",
    consumerRo: "ExecutionPlan, Pricing / Commercial",
    limitationRo: "Probat pe Letters; nu este universal pentru toate șabloanele.",
    verifyRoute: "/product-system",
    spineOrder: 3,
  },
  {
    id: "pricing_commercial",
    labelRo: "Pricing / Commercial",
    technicalName: "Commercial Pricing",
    owner: "Commercial Pricing",
    purposeRo: "Deține calculul comercial autoritar (nu UI-ul).",
    status: "PARTIAL",
    inputRo: "Aggregate / context comercial",
    outputRo: "Valori comerciale pentru îngheț ofertă",
    consumerRo: "Quote Snapshot",
    limitationRo: "Tarifele de registru nu sunt SoT pentru oferta acceptată; orele/minutele nu sunt autoritate comercială.",
    verifyRoute: "/pricing",
    spineOrder: 4,
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
    spineOrder: 5,
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
    spineOrder: 6,
  },
  {
    id: "execution_plan",
    labelRo: "Plan de execuție",
    technicalName: "ExecutionPlan",
    owner: "Execution path",
    purposeRo: "Deține adevărul operațional planificat înghețat.",
    status: "PARTIAL",
    inputRo: "Order Snapshot + task_contract",
    outputRo: "Plan / task-uri planificate",
    consumerRo: "Execution Reality",
    limitationRo: "Materializare completă nu e universală pe toate șabloanele.",
    verifyRoute: "/execution",
    spineOrder: 7,
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
    spineOrder: 8,
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
    limitationRo: "Fără write-back comercial; TE2E-028 rămâne deschis ca residual.",
    verifyRoute: "/execution",
    spineOrder: 9,
  },
];

/** Supporting systems — not spine nodes, but present ownership surfaces. */
export const PRESENT_SUPPORT_SYSTEMS: PresentSystem[] = [
  {
    id: "product_system",
    labelRo: "Catalog produse",
    technicalName: "Product System",
    owner: "Product System",
    purposeRo: "Deține contracte reutilizabile de produs / șablon / modul.",
    status: "CONFIRMAT",
    inputRo: "Coduri șablon / definiții modul",
    outputRo: "Contracte șablon consumabile",
    consumerRo: "Intake V6, ProductDefinition",
    limitationRo: "Nu deține selecții workspace, pricing, inventar real sau actuals.",
    verifyRoute: "/product-system",
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
    limitationRo: "Nu este sursă de preț pentru oferte.",
    verifyRoute: "/inventory",
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
    id: "h.intake_pd",
    producerId: "intake_v6",
    producerRo: "Intake V6",
    consumerId: "product_definition",
    consumerRo: "ProductDefinition",
    outputContractRo: "Workspace + selecție șablon / intent produs",
    enforcementRo: "Intake V6 workspace + compile path",
    status: "CONFIRMAT",
    verificationRo: "UI /intake-v6 · compile pe workspace activ",
  },
  {
    id: "h.pd_pa",
    producerId: "product_definition",
    producerRo: "ProductDefinition",
    consumerId: "product_aggregate",
    consumerRo: "ProductAggregate",
    outputContractRo: "Definiție / graf compilat",
    enforcementRo: "Product compile → aggregate composition",
    status: "PARTIAL",
    verificationRo: "API / flux embedded (fără pagină dedicată PD)",
  },
  {
    id: "h.pa_plan",
    producerId: "product_aggregate",
    producerRo: "ProductAggregate",
    consumerId: "execution_plan",
    consumerRo: "ExecutionPlan",
    outputContractRo: "task_contract / reguli task",
    enforcementRo: "Plan V2 materializare din aggregate",
    status: "PARTIAL",
    verificationRo: "UI /execution · plan generat din contract",
  },
  {
    id: "h.pricing_quote",
    producerId: "pricing_commercial",
    producerRo: "Pricing / Commercial",
    consumerId: "quote_snapshot",
    consumerRo: "Quote Snapshot",
    outputContractRo: "Valori comerciale pentru îngheț",
    enforcementRo: "Commercial pricing services (nu UI)",
    status: "PARTIAL",
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
    systemId: "intake_v6",
    domainRo: "Intake V6 / Preluare lucrare",
    technicalAlias: "Intake V6 / Work Intake",
    owner: "Operator comercial / Sales",
    semanticOwnershipRo: "Cerere și spațiu de lucru",
    writeAuthorityRo: "Workspace intake (operator)",
    readOnlyRo: "Catalog șabloane (Product System)",
    enforcementRo: "Rute Intake V6 + contracte workspace",
    status: "CONFIRMAT",
  },
  {
    systemId: "product_system",
    domainRo: "Catalog produse",
    technicalAlias: "Product System",
    owner: "Product System",
    semanticOwnershipRo: "Contracte șablon / modul reutilizabile",
    writeAuthorityRo: "Product System admin / builder",
    readOnlyRo: "Intake, PD (consum)",
    enforcementRo: "Product System registry + availability",
    status: "CONFIRMAT",
  },
  {
    systemId: "product_definition",
    domainRo: "Definiție produs",
    technicalAlias: "ProductDefinition",
    owner: "Product compile path",
    semanticOwnershipRo: "Definiție compilată",
    writeAuthorityRo: "Compile path (sistem)",
    readOnlyRo: "Aggregate (consum)",
    enforcementRo: "Contracte PD / compile services",
    status: "PARTIAL",
  },
  {
    systemId: "product_aggregate",
    domainRo: "Structura tehnică a produsului",
    technicalAlias: "ProductAggregate",
    owner: "Aggregate composition",
    semanticOwnershipRo: "BOM / task_contract",
    writeAuthorityRo: "Aggregate composition (sistem)",
    readOnlyRo: "Plan, comercial (consum)",
    enforcementRo: "Aggregate + task_contract compile",
    status: "PARTIAL",
  },
  {
    systemId: "pricing_commercial",
    domainRo: "Pricing / Commercial",
    technicalAlias: "Commercial Pricing",
    owner: "Commercial Pricing",
    semanticOwnershipRo: "Calcul comercial autoritar",
    writeAuthorityRo: "Servicii pricing (backend)",
    readOnlyRo: "UI Quotes (afișare)",
    enforcementRo: "Commercial preview / pricing services",
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
    semanticOwnershipRo: "Adevăr planificat înghețat",
    writeAuthorityRo: "Generare plan din snapshot/contract",
    readOnlyRo: "Execution Reality (consum plan)",
    enforcementRo: "Plan V2 / task materialization",
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
    systemId: "inventory",
    domainRo: "Inventar",
    technicalAlias: "Inventory",
    owner: "Inventory",
    semanticOwnershipRo: "Stoc / achiziție",
    writeAuthorityRo: "Inventory services",
    readOnlyRo: "Producție (citire)",
    enforcementRo: "Inventory routers",
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
      "Inventarul nu este sursă de preț ofertă",
    ],
    enforcementRo: "Servicii commercial pricing / preview boundary",
    ownerGateRo: "Schimbări de autoritate pricing = GO owner",
    verificationRo: "/pricing · /quotes · contracte commercial preview",
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
    truthControlledRo: "Contracte produs/șablon/modul reutilizabile",
    allowedRo: ["Definește șabloane și module", "Availability / activation scope"],
    forbiddenRo: [
      "Nu deține selecții workspace",
      "Nu deține pricing",
      "Nu deține angajați / pontaj",
      "Nu deține inventar real",
      "Nu deține actuals de execuție",
    ],
    enforcementRo: "Product System registry + activation scope",
    ownerGateRo: "Activare root product = GO owner",
    verificationRo: "/product-system",
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
];

export const PRESENT_GUARDRAILS: PresentGuardrail[] = [
  {
    id: "G01",
    titleRo: "Nu amesteca rolurile sistemelor",
    requirementRo:
      "Intake preia cererea; Product System deține șabloanele; ProductDefinition compilează; ProductAggregate structurează; Pricing calculează comercial; Quote/Order îngheață; ExecutionPlan planifică; Execution Reality înregistrează actuals; Post-Job reconciliază read-only.",
    enforcementRo: "Politică arhitecturală + contracte de boundary (nu RBAC)",
    status: "POLITICA OWNER",
    ownerGateRo: "Schimbare de rol sistem = GO owner",
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
