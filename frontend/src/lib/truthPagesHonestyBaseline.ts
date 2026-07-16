/**
 * W0-B4/B5 honesty baseline — static architecture projection for truth pages.
 * Display labels only. Technical routes/IDs remain unchanged.
 * NOT a parallel source of truth; coverage is intentionally PARTIAL.
 */

export type HonestyCoverage = "baseline" | "partial" | "nevalidat";

export interface HonestyArchitectureNode {
  id: string;
  labelRo: string;
  technicalAlias: string;
  coverage: HonestyCoverage;
  note: string;
}

export interface HonestyHandoff {
  fromId: string;
  toId: string;
  fromLabel: string;
  toLabel: string;
  status: "baseline" | "nevalidat";
  source: string;
  note: string;
}

export interface HonestyOwnershipRow {
  domainRo: string;
  technicalAlias: string;
  owner: string;
  authority: string;
  status: string;
  source: string;
}

export interface HonestyRule {
  ruleRo: string;
  source: string;
  status: string;
}

/** Commercial spine baseline — RO display labels from OD-TERM. */
export const HONESTY_ARCHITECTURE_NODES: HonestyArchitectureNode[] = [
  {
    id: "work_intake",
    labelRo: "Preluare lucrare",
    technicalAlias: "Work Intake",
    coverage: "baseline",
    note: "Intrare comercială / spațiu de lucru",
  },
  {
    id: "product_system",
    labelRo: "Catalog produse",
    technicalAlias: "Product System",
    coverage: "baseline",
    note: "Definiții șablon (nu preț)",
  },
  {
    id: "product_definition",
    labelRo: "Definiție produs",
    technicalAlias: "ProductDefinition",
    coverage: "partial",
    note: "Compile / previzualizare — fără pagină dedicată",
  },
  {
    id: "product_aggregate",
    labelRo: "Structura tehnică a produsului",
    technicalAlias: "ProductAggregate",
    coverage: "partial",
    note: "Agregat tehnic / BOM — panouri, nu SoT comercial",
  },
  {
    id: "quotes",
    labelRo: "Oferte",
    technicalAlias: "Quotes",
    coverage: "baseline",
    note: "Îngheț comercial",
  },
  {
    id: "orders",
    labelRo: "Comenzi",
    technicalAlias: "Orders",
    coverage: "baseline",
    note: "Snapshot aprobat",
  },
  {
    id: "execution_plan",
    labelRo: "Plan de execuție",
    technicalAlias: "ExecutionPlan",
    coverage: "partial",
    note: "Plan din snapshot — materializare controlată",
  },
  {
    id: "execution_reality",
    labelRo: "Execuție",
    technicalAlias: "Execution Reality",
    coverage: "partial",
    note: "Realitate operațională",
  },
];

export const HONESTY_RESOURCE_BOUNDARIES: HonestyArchitectureNode[] = [
  {
    id: "pricing",
    labelRo: "Tarife",
    technicalAlias: "Pricing",
    coverage: "partial",
    note: "Registru tarife — nu SoT ofertă",
  },
  {
    id: "inventory",
    labelRo: "Inventar",
    technicalAlias: "Inventory",
    coverage: "partial",
    note: "Stoc / achiziție",
  },
  {
    id: "machines",
    labelRo: "Utilaje",
    technicalAlias: "Utilaje",
    coverage: "nevalidat",
    note: "Limită resursă — fără hartă Figma dedicată",
  },
  {
    id: "employees",
    labelRo: "Angajați",
    technicalAlias: "Employees",
    coverage: "nevalidat",
    note: "Limită resursă",
  },
  {
    id: "attendance",
    labelRo: "Pontaj",
    technicalAlias: "Attendance",
    coverage: "nevalidat",
    note: "Limită disponibilitate",
  },
];

export const HONESTY_HANDOFFS: HonestyHandoff[] = [
  {
    fromId: "work_intake",
    toId: "product_system",
    fromLabel: "Preluare lucrare",
    toLabel: "Catalog produse",
    status: "baseline",
    source: "Wave 0 plan / Page Completion Foundation",
    note: "Selecție șablon / context produs",
  },
  {
    fromId: "product_system",
    toId: "product_definition",
    fromLabel: "Catalog produse",
    toLabel: "Definiție produs",
    status: "baseline",
    source: "Product truth / PD contracts",
    note: "Compile din șablon + valori spațiu de lucru",
  },
  {
    fromId: "product_definition",
    toId: "product_aggregate",
    fromLabel: "Definiție produs",
    toLabel: "Structura tehnică a produsului",
    status: "baseline",
    source: "ProductAggregate composition",
    note: "Compoziție tehnică",
  },
  {
    fromId: "product_aggregate",
    toId: "quotes",
    fromLabel: "Structura tehnică a produsului",
    toLabel: "Oferte",
    status: "partial",
    source: "Sold-scope / commercial freeze",
    note: "Consum comercial — acoperire validată pe pilot",
  },
  {
    fromId: "quotes",
    toId: "orders",
    fromLabel: "Oferte",
    toLabel: "Comenzi",
    status: "baseline",
    source: "Quote → Order freeze",
    note: "Îngheț snapshot",
  },
  {
    fromId: "orders",
    toId: "execution_plan",
    fromLabel: "Comenzi",
    toLabel: "Plan de execuție",
    status: "partial",
    source: "EP filter / planning readiness",
    note: "Plan din comandă înghețată",
  },
  {
    fromId: "execution_plan",
    toId: "execution_reality",
    fromLabel: "Plan de execuție",
    toLabel: "Execuție",
    status: "partial",
    source: "Execution reality capture",
    note: "Consum plan → realitate",
  },
];

export const HONESTY_OWNERSHIP_ROWS: HonestyOwnershipRow[] = [
  {
    domainRo: "Catalog produse",
    technicalAlias: "Product System",
    owner: "Product System",
    authority: "SUPPORTING / CODE",
    status: "PARTIAL",
    source: "Page Completion Foundation · OD-TERM-01",
  },
  {
    domainRo: "Definiție produs",
    technicalAlias: "ProductDefinition",
    owner: "Product compile path",
    authority: "CODE_CONTRACT",
    status: "PARTIAL",
    source: "Truth Metadata · PD contracts",
  },
  {
    domainRo: "Structura tehnică a produsului",
    technicalAlias: "ProductAggregate",
    owner: "Aggregate composition",
    authority: "CODE_CONTRACT",
    status: "PARTIAL",
    source: "OD-TERM-06 · Aggregate contracts",
  },
  {
    domainRo: "Tarife",
    technicalAlias: "Pricing",
    owner: "Pricing registry",
    authority: "SUPPORTING",
    status: "PARTIAL",
    source: "Commercial preview boundary",
  },
  {
    domainRo: "Oferte / Comenzi",
    technicalAlias: "Quote / Order",
    owner: "Commercial freeze",
    authority: "CODE_CONTRACT",
    status: "PARTIAL",
    source: "Sold-scope / snapshot contracts",
  },
  {
    domainRo: "Execuție",
    technicalAlias: "Execution",
    owner: "Execution path",
    authority: "CODE_CONTRACT",
    status: "PARTIAL",
    source: "EP preview boundary",
  },
  {
    domainRo: "Documentație",
    technicalAlias: "Documentation index",
    owner: "Wave 0 foundation",
    authority: "SUPPORTING_CURRENT",
    status: "INDEXED",
    source: "W0-B2 documentation index (admin)",
  },
  {
    domainRo: "Figma UX",
    technicalAlias: "Figma MASTER",
    owner: "Owner / design review",
    authority: "FIGMA_APPROVED_WITH_NOTES",
    status: "APPROVED_WITH_NOTES",
    source: "Figma MASTER final review",
  },
];

export const HONESTY_SEPARATION_RULES: HonestyRule[] = [
  {
    ruleRo: "UI-ul nu calculează costul comercial.",
    source: "Page Completion Foundation · commercial boundary",
    status: "CURRENT_WITH_GUARDS",
  },
  {
    ruleRo: "Documentația din UI nu devine sursă manuală de adevăr arhitectural.",
    source: "Truth Metadata Contract · Hybrid architecture",
    status: "CURRENT",
  },
  {
    ruleRo: "Runtime (health) confirmă comportament — nu validează automat arhitectura aprobată.",
    source: "Truth Metadata · Wave 0 plan",
    status: "CURRENT",
  },
  {
    ruleRo: "Oferta și comanda îngheață adevărul acceptat; execuția consumă contractul înghețat.",
    source: "Quote/Order freeze · EP boundary",
    status: "CURRENT_WITH_GUARDS",
  },
  {
    ruleRo: "Redenumirea vizibilă (etichetă RO) nu schimbă rutele, ID-urile sau câmpurile API.",
    source: "OD-TERM / W0-B4-B5 safety rule",
    status: "CURRENT",
  },
];

export const HONESTY_OWNER_GATES: string[] = [
  "Modificări schemă DB / migrări",
  "Reguli de pricing / tarife comerciale",
  "Schimbări de contract canonic",
  "Ownership canonic / autoritate document",
  "Redenumire identificatori tehnici (rute, enum, API, DB)",
  "Aprobare Figma ca UX truth",
  "Status canonic document / arhivare / ștergere",
];

export function coverageBadgeClass(coverage: HonestyCoverage): string {
  if (coverage === "baseline") return "bg-emerald-900/30 text-emerald-300 border-emerald-700";
  if (coverage === "partial") return "bg-amber-900/30 text-amber-300 border-amber-700";
  return "bg-slate-700/50 text-slate-300 border-slate-600";
}

export function coverageLabelRo(coverage: HonestyCoverage): string {
  if (coverage === "baseline") return "BASELINE";
  if (coverage === "partial") return "ACOPERIRE PARȚIALĂ";
  return "NEVALIDAT";
}
