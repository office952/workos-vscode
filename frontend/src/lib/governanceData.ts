// ============================================================
// WorkOS Governance Data — Extracted from canonical .md files
// ============================================================

// --- MODULE STATUS FLOWS ---
export interface StatusTransition {
  from: string;
  to: string;
  trigger: string;
}

export interface ModuleStatusFlow {
  id: string;
  name: string;
  shortName: string;
  owner: string;
  statuses: string[];
  transitions: StatusTransition[];
  color: string;
}

export const moduleStatusFlows: ModuleStatusFlow[] = [
  {
    id: "oc",
    name: "Operational Core",
    shortName: "OC",
    owner: "system / admin",
    statuses: ["active", "inactive", "deprecated"],
    transitions: [
      { from: "inactive", to: "active", trigger: "manual admin" },
      { from: "active", to: "inactive", trigger: "manual admin" },
      { from: "active", to: "deprecated", trigger: "manual admin" },
    ],
    color: "text-cyan-400",
  },
  {
    id: "wi",
    name: "Work Intake",
    shortName: "WI",
    owner: "operator / sales",
    statuses: ["new", "in_review", "needs_info", "ready_for_quote", "blocked", "cancelled"],
    transitions: [
      { from: "new", to: "in_review", trigger: "preluare operator" },
      { from: "in_review", to: "needs_info", trigger: "lipsa date" },
      { from: "needs_info", to: "in_review", trigger: "completare client" },
      { from: "in_review", to: "ready_for_quote", trigger: "validare completa" },
      { from: "*", to: "cancelled", trigger: "abandon / invalid" },
    ],
    color: "text-orange-400",
  },
  {
    id: "product_system",
    name: "ProductSystem",
    shortName: "PS",
    owner: "sistem + operator",
    statuses: ["unresolved", "resolving", "resolved", "invalid_configuration"],
    transitions: [
      { from: "unresolved", to: "resolving", trigger: "start configurare" },
      { from: "resolving", to: "resolved", trigger: "configuratie valida" },
      { from: "resolving", to: "invalid_configuration", trigger: "conflict reguli" },
      { from: "invalid_configuration", to: "resolving", trigger: "corectie" },
    ],
    color: "text-pink-400",
  },
  {
    id: "cost_engine",
    name: "CostEngine",
    shortName: "CE",
    owner: "sistem",
    statuses: ["pending", "calculating", "calculated", "failed"],
    transitions: [
      { from: "pending", to: "calculating", trigger: "request calcul" },
      { from: "calculating", to: "calculated", trigger: "succes" },
      { from: "calculating", to: "failed", trigger: "eroare" },
      { from: "failed", to: "calculating", trigger: "retry" },
    ],
    color: "text-cyan-400",
  },
  {
    id: "quotes",
    name: "Quotes",
    shortName: "QT",
    owner: "sales",
    statuses: ["draft", "priced", "sent", "viewed", "negotiating", "accepted", "rejected", "expired"],
    transitions: [
      { from: "draft", to: "priced", trigger: "cost primit" },
      { from: "priced", to: "sent", trigger: "trimis client" },
      { from: "sent", to: "viewed", trigger: "deschidere" },
      { from: "viewed", to: "negotiating", trigger: "interactiune client" },
      { from: "negotiating", to: "priced", trigger: "recalcul comercial" },
      { from: "*", to: "accepted", trigger: "acceptare" },
      { from: "*", to: "rejected", trigger: "refuz" },
      { from: "sent/priced", to: "expired", trigger: "depasire termen" },
    ],
    color: "text-amber-400",
  },
  {
    id: "orders",
    name: "Orders",
    shortName: "OR",
    owner: "sistem + management",
    statuses: ["created", "confirmed", "locked", "in_execution", "completed", "cancelled"],
    transitions: [
      { from: "created", to: "confirmed", trigger: "acceptare oferta" },
      { from: "confirmed", to: "locked", trigger: "snapshot final" },
      { from: "locked", to: "in_execution", trigger: "trimis in WorkOS" },
      { from: "in_execution", to: "completed", trigger: "finalizare" },
      { from: "*", to: "cancelled", trigger: "anulare controlata" },
    ],
    color: "text-blue-400",
  },
  {
    id: "workos",
    name: "WorkOS",
    shortName: "WO",
    owner: "productie",
    statuses: ["pending", "scheduled", "in_progress", "blocked", "partial_done", "done"],
    transitions: [
      { from: "pending", to: "scheduled", trigger: "planificare" },
      { from: "scheduled", to: "in_progress", trigger: "start productie" },
      { from: "in_progress", to: "blocked", trigger: "lipsa resurse" },
      { from: "blocked", to: "in_progress", trigger: "deblocare" },
      { from: "in_progress", to: "partial_done", trigger: "executie partiala" },
      { from: "partial_done", to: "in_progress", trigger: "reluare" },
      { from: "in_progress", to: "done", trigger: "finalizare" },
    ],
    color: "text-emerald-400",
  },
  {
    id: "tasks",
    name: "Tasks",
    shortName: "TK",
    owner: "operator / executant",
    statuses: ["created", "assigned", "in_progress", "blocked", "done", "cancelled"],
    transitions: [
      { from: "created", to: "assigned", trigger: "alocare" },
      { from: "assigned", to: "in_progress", trigger: "start" },
      { from: "in_progress", to: "blocked", trigger: "impediment" },
      { from: "blocked", to: "in_progress", trigger: "rezolvare" },
      { from: "in_progress", to: "done", trigger: "finalizare" },
      { from: "*", to: "cancelled", trigger: "anulare" },
    ],
    color: "text-purple-400",
  },
];

export const systemEvents = [
  { event: "WI_READY_FOR_QUOTE", source: "WI", description: "Cerere pregatita pentru ofertare" },
  { event: "PRODUCT_RESOLVED", source: "ProductSystem", description: "Configuratie produs rezolvata" },
  { event: "COST_CALCULATED", source: "CostEngine", description: "Cost calculat cu succes" },
  { event: "QUOTE_ACCEPTED", source: "Quotes", description: "Oferta acceptata de client" },
  { event: "ORDER_LOCKED", source: "Orders", description: "Snapshot order inghetat" },
  { event: "WORK_STARTED", source: "WorkOS", description: "Executie pornita" },
  { event: "TASK_COMPLETED", source: "Tasks", description: "Task finalizat" },
];

export const invalidPatterns = [
  "Quotes seteaza status in WorkOS",
  "WorkOS modifica status in Orders direct",
  "Tasks devin sursa de adevar pentru productie",
  "WI sare direct in Orders",
];

// --- PRODUCT CATALOG ---
export interface ProductCategory {
  id: string;
  name: string;
  code: string;
  products: { name: string; code: string }[];
}

export const productCatalog: ProductCategory[] = [
  {
    id: "cl", name: "Casete Luminoase", code: "CL",
    products: [
      { name: "Caseta luminoasa simpla", code: "CL-SIMPLU-STD" },
      { name: "Caseta luminoasa dubla fata", code: "CL-DUBLA-STD" },
      { name: "Caseta profil aluminiu + fata plexi", code: "CL-ALU-PLEXI" },
      { name: "Caseta textila backlit", code: "CL-TEXTIL-BACKLIT" },
    ],
  },
  {
    id: "lv", name: "Litere Volumetrice", code: "LV",
    products: [
      { name: "Litere volumetrice neluminoase", code: "LV-NELUM-STD" },
      { name: "Litere volumetrice luminoase fata", code: "LV-FRONTAL-LED" },
      { name: "Litere volumetrice halo (backlit)", code: "LV-HALO-LED" },
      { name: "Litere volumetrice combinate", code: "LV-COMBI-LED" },
      { name: "Litere polistiren", code: "LV-POLI-STD" },
    ],
  },
  {
    id: "totem", name: "Totemuri / Pyloni", code: "TOTEM",
    products: [
      { name: "Totem neluminat", code: "TOTEM-NELUM-STD" },
      { name: "Totem iluminat", code: "TOTEM-ILUMINAT-STD" },
      { name: "Totem structura + placare", code: "TOTEM-STRUCT-PLAC" },
    ],
  },
  {
    id: "semn", name: "Semnalistica Interioara", code: "SEMN",
    products: [
      { name: "Placute semnalizare", code: "SEMN-PLAC-STD" },
      { name: "Placute usi / birouri", code: "SEMN-USI-STD" },
      { name: "Logo 3D interior", code: "SEMN-LOGO3D-STD" },
      { name: "Litere decorative interior", code: "SEMN-LITDEC-STD" },
    ],
  },
  {
    id: "print", name: "Print Flexibil", code: "PRINT",
    products: [
      { name: "Banner frontlit", code: "PRINT-BANNER-FRONT" },
      { name: "Banner backlit", code: "PRINT-BANNER-BACK" },
      { name: "Mesh", code: "PRINT-MESH-STD" },
      { name: "Autocolant simplu", code: "PRINT-AUTO-SIMPLU" },
      { name: "Autocolant laminat", code: "PRINT-AUTO-LAMINAT" },
      { name: "Autocolant perforat", code: "PRINT-AUTO-PERF" },
    ],
  },
  {
    id: "col", name: "Colantari", code: "COL",
    products: [
      { name: "Colantare vitrine", code: "COL-VITRINE-STD" },
      { name: "Colantare auto partiala", code: "COL-AUTO-PARTIAL" },
      { name: "Colantare auto integrala", code: "COL-AUTO-FULL" },
      { name: "Colantare interior", code: "COL-INTERIOR-STD" },
      { name: "Folii sablate", code: "COL-SABLAT-STD" },
    ],
  },
  {
    id: "expo", name: "Sisteme Expozitionale", code: "EXPO",
    products: [
      { name: "Roll-up", code: "EXPO-ROLLUP-STD" },
      { name: "X-banner", code: "EXPO-XBANNER-STD" },
      { name: "Steaguri publicitare", code: "EXPO-STEAG-STD" },
      { name: "Standuri custom", code: "EXPO-STAND-CUSTOM" },
    ],
  },
  {
    id: "metal", name: "Structuri Metalice", code: "METAL",
    products: [
      { name: "Cadre metalice", code: "METAL-CADRU-STD" },
      { name: "Suporturi banner", code: "METAL-SUPORT-BANNER" },
      { name: "Structuri mesh", code: "METAL-STRUCT-MESH" },
      { name: "Console / prinderi", code: "METAL-CONSOLA-STD" },
    ],
  },
  {
    id: "cnc", name: "Productie CNC / Debitare", code: "CNC",
    products: [
      { name: "Debitare PVC", code: "CNC-PVC-DEBITARE" },
      { name: "Debitare plexiglas", code: "CNC-PLEXI-DEBITARE" },
      { name: "Debitare dibond", code: "CNC-DIBOND-DEBITARE" },
      { name: "Debitare lemn", code: "CNC-LEMN-DEBITARE" },
      { name: "Debitare polistiren (HotWire)", code: "CNC-POLI-HOTWIRE" },
    ],
  },
  {
    id: "ext", name: "Externalizari", code: "EXT",
    products: [
      { name: "Print rigid PVC", code: "EXT-PRINT-PVC" },
      { name: "Print rigid plexiglas", code: "EXT-PRINT-PLEXI" },
      { name: "Print rigid dibond", code: "EXT-PRINT-DIBOND" },
      { name: "Alte externalizari", code: "EXT-ALTELE-STD" },
    ],
  },
  {
    id: "elec", name: "Electrice", code: "ELEC",
    products: [
      { name: "Sisteme LED (module + surse)", code: "ELEC-LED-SISTEM" },
      { name: "Cablare", code: "ELEC-CABLU-STD" },
    ],
  },
  {
    id: "serv", name: "Servicii", code: "SERV",
    products: [
      { name: "Design grafic", code: "SERV-DESIGN-STD" },
      { name: "Montaj", code: "SERV-MONTAJ-STD" },
      { name: "Transport", code: "SERV-TRANSPORT-STD" },
      { name: "Mentenanta", code: "SERV-MENTEN-STD" },
    ],
  },
];

// --- BOUNDARY MAP ---
export interface BoundaryLayer {
  id: string;
  name: string;
  shortName: string;
  role: string;
  allowed: string[];
  forbidden: string[];
  hardRule: string;
  color: string;
  borderColor: string;
}

export const boundaryLayers: BoundaryLayer[] = [
  {
    id: "templates",
    name: "Product Templates / Blueprint Studio",
    shortName: "Templates",
    role: "Pregătește contractul calculabil",
    allowed: [
      "Definește structura produsului",
      "Definește componente și build variants",
      "Validează calculation readiness",
      "Livrează verdict Ready for Quotes / Not Ready",
    ],
    forbidden: [
      "Nu calculează prețul final",
      "Nu livrează snapshot de Order",
      "Nu decide context economic",
      "Nu preia rolul Quotes sau OC",
    ],
    hardRule: "Template-ul livrează contractul calculabil. Nu preia rolul Quotes, Orders, WorkOS sau OC.",
    color: "from-pink-500/20 to-pink-900/10",
    borderColor: "border-pink-500",
  },
  {
    id: "quotes",
    name: "Quotes",
    shortName: "Quotes",
    role: "Calculează în contextul firmei",
    allowed: [
      "Calcule de cost și preț",
      "Aplicare formule și reguli comerciale",
      "Compunere quote items",
      "Versionare de quote",
    ],
    forbidden: [
      "Nu repară Template-ul",
      "Nu inventează structura lipsă",
      "Nu completează tacit quantity sources",
      "Nu inventează materialRef lipsă",
      "Nu devine autor de produs",
    ],
    hardRule: "Quotes consumă un Template deja calculabil. Dacă Template-ul nu este pregătit, Quotes nu compensează lipsa.",
    color: "from-amber-500/20 to-amber-900/10",
    borderColor: "border-amber-500",
  },
  {
    id: "orders",
    name: "Orders",
    shortName: "Orders",
    role: "Îngheață snapshot-ul aprobat",
    allowed: [
      "Fixează quote version aprobată",
      "Păstrează snapshot-ul aprobat",
      "Devine input oficial pentru execuție",
      "Transportă configurația aprobată spre WorkOS",
    ],
    forbidden: [
      "Nu recalculează oferta",
      "Nu schimbă structura produsului",
      "Nu devine configurator viu",
      "Nu se comportă ca obiect fluid după aprobare",
    ],
    hardRule: "Orders îngheață snapshot-ul aprobat. Din acel moment, adevărul comercial-tehnic nu mai este reconstruit din mers.",
    color: "from-blue-500/20 to-blue-900/10",
    borderColor: "border-blue-500",
  },
  {
    id: "workos",
    name: "WorkOS",
    shortName: "WorkOS",
    role: "Execută orchestrat",
    allowed: [
      "Citește snapshot-ul Order",
      "Generează și orchestrează execuția",
      "Urmărește progresul real",
      "Colaborează cu OC pentru realism",
    ],
    forbidden: [
      "Nu redefinește produsul",
      "Nu repară structura din amonte",
      "Nu reinventează calculul comercial",
      "Nu decide inventar independent de OC",
      "Nu rescrie snapshot-ul aprobat",
    ],
    hardRule: "WorkOS execută. Nu definește produsul și nu repară lipsurile structurale.",
    color: "from-emerald-500/20 to-emerald-900/10",
    borderColor: "border-emerald-500",
  },
  {
    id: "oc",
    name: "Operational Core (OC)",
    shortName: "OC",
    role: "Păzește adevărul operațional",
    allowed: [
      "Deține adevărul despre resurse și inventar",
      "Actualizează starea operațională reală",
      "Oferă context de capacitate și realism",
      "Confirmă sau expune limitele reale",
    ],
    forbidden: [
      "Nu redefinește oferta",
      "Nu rescrie snapshot-ul Order",
      "Nu preia rolul Quotes",
      "Nu este redus la catalog pasiv",
    ],
    hardRule: "OC rămâne owner pe inventar, resurse și adevăr operațional. WorkOS colaborează cu OC, dar nu îl înlocuiește.",
    color: "from-cyan-500/20 to-cyan-900/10",
    borderColor: "border-cyan-500",
  },
];

// --- AGENT AUTHORITY MAP ---
// Data loaded from canonical registry: docs/canonical/agent_authority_registry.json
// Source of truth: docs/canonical/canonical__agent_authority_map.md
// DO NOT hardcode new agents here. Edit the registry instead.
import agentAuthorityRegistry from "./agentAuthorityRegistry";

export interface Agent {
  id: string;
  name: string;
  shortName: string;
  role: string;
  authority: string[];
  noAuthority: string[];
  escalatesWhen: string[];
  owner: string;
  sourceOfTruth: string;
  color: string;
  icon: string;
}

export const agents: Agent[] = agentAuthorityRegistry;

// --- SOURCE OF TRUTH HIERARCHY ---
export interface TruthSource {
  level: number;
  name: string;
  role: string;
  truthFor: string;
  notTruthFor: string;
  color: string;
}

export const truthHierarchy: TruthSource[] = [
  {
    level: 1,
    name: "Nucleu",
    role: "Agentul Adevărului",
    truthFor: "Adevărul final de sistem, arbitraj conflicte, boundary-uri finale",
    notTruthFor: "Implementare, UI execution layer",
    color: "bg-amber-500",
  },
  {
    level: 2,
    name: "Fișiere .md canonice",
    role: "Forma scrisă oficială",
    truthFor: "Reguli de sistem, boundary-uri, contracte, autoritate, reguli UI/implementare",
    notTruthFor: "Dacă nu există în .md, nu e adevăr canonic",
    color: "bg-blue-500",
  },
  {
    level: 3,
    name: "Contracte validate",
    role: "Validare handoff-uri",
    truthFor: "Handoff-uri, ownership date, shape payload, snapshot, context vs executabil",
    notTruthFor: "Nu inventează lege nouă",
    color: "bg-emerald-500",
  },
  {
    level: 4,
    name: "Codul implementat",
    role: "Execuția specificației",
    truthFor: "Ce există efectiv implementat, forma tehnică reală",
    notTruthFor: "Ce ar trebui să fie sistemul, workaround-uri tacite",
    color: "bg-purple-500",
  },
  {
    level: 5,
    name: "Runtime-ul observat",
    role: "Comportament real",
    truthFor: "Comportamentul real curent, mismatch-uri față de documentație",
    notTruthFor: "Dacă contrazice .md, nu înseamnă automat că .md e greșit",
    color: "bg-cyan-500",
  },
  {
    level: 6,
    name: "Figma",
    role: "Adevăr vizual",
    truthFor: "Layout vizual, ierarhie informație, densitate, design system",
    notTruthFor: "Logica de business, statusuri canonice, contracte funcționale",
    color: "bg-pink-500",
  },
  {
    level: 7,
    name: "Atoms / tool-uri asistate",
    role: "Accelerare execuție",
    truthFor: "Structurare UI, implementare asistată, prototipare controlată",
    notTruthFor: "Legea sistemului, adevărul de business, boundary-uri",
    color: "bg-orange-500",
  },
  {
    level: 8,
    name: "Tool-uri externe",
    role: "Contribuție controlată",
    truthFor: "Nesting, scanare documente, OCR, AI operațional",
    notTruthFor: "Arhitectura de bază, business logic, contracte canonice",
    color: "bg-slate-500",
  },
];

// --- READY FOR QUOTES GATE ---
export interface GateLevel {
  level: string;
  name: string;
  verdicts: string[];
  rule: string;
  color: string;
}

export const gateLevels: GateLevel[] = [
  {
    level: "1",
    name: "Build Variant",
    verdicts: ["Ready", "Warning", "Blocked"],
    rule: "Varianta este calculabilă doar dacă are contract complet: costProfile, costPerUnit > 0, costUnit, consumptionProfile, quantityType, quantitySource recunoscut, wastePercent, materialRef (dacă e cerut).",
    color: "border-pink-500",
  },
  {
    level: "2",
    name: "Component",
    verdicts: ["Ready", "Warning", "Blocked"],
    rule: "Verdictul reflectă varianta relevantă activă. Nu se caută automat altă variantă. Nu se folosește best available variant. Nu se face fallback.",
    color: "border-purple-500",
  },
  {
    level: "3",
    name: "Template",
    verdicts: ["Ready for Quotes", "Not Ready for Quotes"],
    rule: "Un Template este Ready for Quotes doar dacă TOATE componentele required au isCalculable = true. Nu se acceptă procent minim, majoritate, sau aproape gata.",
    color: "border-blue-500",
  },
  {
    level: "4",
    name: "Gate Final",
    verdicts: ["Handoff permis", "Handoff refuzat"],
    rule: "Handoff-ul din Blueprint Studio către Quotes este permis doar dacă gate-ul este trecut. Dacă verdictul este Not Ready, handoff-ul trebuie refuzat.",
    color: "border-emerald-500",
  },
];

// --- IMPLEMENTATION GUARDRAILS ---
export interface Guardrail {
  id: string;
  category: string;
  title: string;
  description: string;
  severity: "critical" | "warning" | "info";
}

export const guardrails: Guardrail[] = [
  { id: "G01", category: "Boundary", title: "Nu amesteca rolurile modulelor", description: "Templates pregătește, Quotes calculează, Orders îngheață, WorkOS execută, OC păzește adevărul operațional.", severity: "critical" },
  { id: "G02", category: "Fallback", title: "Nu accepta fallback-uri ascunse", description: "Nu alege altă variantă 'mai bună' fără regulă canonică. Nu completa tacit quantitySource lipsă.", severity: "critical" },
  { id: "G03", category: "Workaround", title: "Nu accepta workaround-uri arhitecturale", description: "Nu muta logica de business în UI. Nu muta reparații structurale în Quotes. Nu scrie adevăr operațional din WorkOS în locul OC.", severity: "critical" },
  { id: "G04", category: "Clarificare", title: "Cere clarificare obligatorie", description: "Dacă specificația este ambiguă, incompletă sau contradictorie, implementarea trebuie să se oprească și să ceară clarificare.", severity: "warning" },
  { id: "G05", category: "Sursă", title: "Implementarea nu devine sursă de adevăr", description: "Codul spune ce există implementat, nu ce ar trebui să fie sistemul. Dacă codul contrazice .md, conflictul se escaladează.", severity: "critical" },
  { id: "G06", category: "UI", title: "UI reflectă adevărul, nu-l inventează", description: "Nu introduce statusuri canonice noi, stări intermediare false, sau prezentare mai blandă decât verdictul real.", severity: "critical" },
  { id: "G07", category: "Gate", title: "Gate-urile sunt reale, nu decorative", description: "Ready for Quotes este un gate de business, nu badge decorativ. Handoff-ul trebuie refuzat dacă gate-ul nu e trecut.", severity: "critical" },
  { id: "G08", category: "External", title: "Tool-urile externe nu conduc", description: "Pot ajuta, accelera, aduce precizie. Nu conduc arhitectura, nu mută adevărul în afara sistemului.", severity: "warning" },
  { id: "G09", category: "Inventar", title: "Inventarul este teritoriu OC", description: "WorkOS poate colabora cu OC. Nu devine owner pe inventar. Reconstrucție progresivă, nu inventar perfect din prima.", severity: "warning" },
  { id: "G10", category: "Costing", title: "Costing nu este doar pricing", description: "Costing păzește adevărul economic: consum corect, cost corect, formule corecte, relație corectă produs-resurse.", severity: "info" },
  { id: "G11", category: "QA", title: "QA Alignment verifică coerența", description: "Verifică dacă .md, Figma, cod, SQL și runtime spun același lucru. Semnalează mismatch-uri imediat.", severity: "warning" },
  { id: "G12", category: "Escaladare", title: "Escaladare obligatorie la Nucleu", description: "Conflict între reguli, între agenți, între UI și business, între cod și documentație — toate se escaladează la Nucleu.", severity: "info" },
];

// --- UI TRUTH RULES ---
export interface UIRule {
  id: string;
  area: string;
  rule: string;
  correctExamples: string[];
  incorrectExamples: string[];
}

export const uiTruthRules: UIRule[] = [
  {
    id: "UI01",
    area: "Statusuri",
    rule: "Statusurile canonice vin din sistem, nu din UI",
    correctExamples: ["Ready", "Warning", "Blocked", "Ready for Quotes", "Not Ready for Quotes"],
    incorrectExamples: ["Almost Ready", "Soft Blocked", "Nearly Valid", "Smart Ready", "Draft+"],
  },
  {
    id: "UI02",
    area: "Gate-uri",
    rule: "Gate-urile de business se afișează ca gate-uri, nu ca badge-uri decorative",
    correctExamples: ["Verdict clar Ready/Not Ready", "Blocker-e vizibile", "Handoff imposibil dacă gate-ul nu e trecut"],
    incorrectExamples: ["Gate afișat ca sugestie", "Override tacit", "Completare ulterioară în Quotes"],
  },
  {
    id: "UI03",
    area: "Moduri",
    rule: "Operate Mode și Build Mode sunt distincte clar",
    correctExamples: ["Operate: reacție, viteză, monitorizare", "Build: construcție, configurare, claritate"],
    incorrectExamples: ["Ecran de Build care arată ca Operate", "Moduri amestecate"],
  },
  {
    id: "UI04",
    area: "Ierarhie",
    rule: "Prioritatea informației reflectă prioritatea reală",
    correctExamples: ["1. Verdict operațional", "2. Locul problemei", "3. Acțiunea necesară", "4. Context secundar"],
    incorrectExamples: ["Toate elementele par la fel de importante", "Metadate mai vizibile decât verdictul"],
  },
  {
    id: "UI05",
    area: "Probleme",
    rule: "Problemele reale sunt vizibile, localizabile, explicabile, acționabile",
    correctExamples: ["Ce e blocat", "Unde e blocat", "De ce e blocat", "Ce trebuie făcut"],
    incorrectExamples: ["Punct roșu generic", "Eroare fără context", "Problemă ascunsă în spatele UI curat"],
  },
];