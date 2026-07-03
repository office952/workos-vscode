// ============================================================
// WORKSTATION ROUTING CONFIG — v1 Routing Map
// Maps operation types → workstations → skills → operators
// This is a frontend-only routing config (no backend/schema changes)
// ============================================================

// --- WORKSTATION DEFINITIONS ---
export interface Workstation {
  id: string;
  name: string;
  shortName: string;
  icon: string; // emoji for tablet display
  color: string; // tailwind color class
}

export const WORKSTATIONS: Workstation[] = [
  { id: "lacatuserie_sudura", name: "Lăcătușerie / Sudură", shortName: "Lăcătușerie", icon: "🔧", color: "text-orange-400" },
  { id: "asamblare_lipire", name: "Asamblare / Lipire", shortName: "Asamblare", icon: "🔩", color: "text-blue-400" },
  { id: "led_electric", name: "Montaj LED / Electric", shortName: "LED/Electric", icon: "💡", color: "text-yellow-400" },
  { id: "montaj_autocolant", name: "Montaj autocolant", shortName: "Autocolant", icon: "🎨", color: "text-purple-400" },
  { id: "modelare_litere", name: "Modelare litere", shortName: "Litere", icon: "✂️", color: "text-cyan-400" },
  { id: "cnc", name: "CNC", shortName: "CNC", icon: "⚙️", color: "text-emerald-400" },
  { id: "print", name: "Print", shortName: "Print", icon: "🖨️", color: "text-pink-400" },
  { id: "cutter_plotter", name: "Cutter plotter", shortName: "Cutter", icon: "✂️", color: "text-red-400" },
];

export function getWorkstation(id: string): Workstation | undefined {
  return WORKSTATIONS.find((w) => w.id === id);
}

// --- OPERATION TYPE → WORKSTATION MAPPING ---
export type OperationType =
  | "print" | "print_roll" | "print_uv" | "print_banner" | "print_latex"
  | "cutter_plotter" | "contour_cut" | "vinyl_cut" | "transfer_tape"
  | "cnc_cutting" | "routing" | "engraving" | "v_cutting_acm" | "cnc_debitare"
  | "laser_cutting" | "laser_engraving"
  | "letter_return_forming" | "alum_return_forming" | "cant_modelare"
  | "face_bonding" | "letter_face_bonding"
  | "led_installation" | "power_supply" | "wiring" | "montaj_led" | "electrical_test"
  | "metal_frame" | "metal_frame_fabrication" | "welding" | "brackets" | "supports" | "cadru_metalic"
  | "assembly" | "gluing" | "cleaning" | "asamblare_finala"
  | "vinyl_application" | "foil_application" | "print_application" | "colantare"
  | "packing" | "delivery_preparation";

export interface RoutingEntry {
  operationType: string;
  workstationId: string;
  requiredSkill: string;
  skillLabel: string;
}

export const OPERATION_ROUTING: RoutingEntry[] = [
  // Print
  { operationType: "print", workstationId: "print", requiredSkill: "print_operator", skillLabel: "Operator print" },
  { operationType: "print_roll", workstationId: "print", requiredSkill: "print_operator", skillLabel: "Operator print" },
  { operationType: "print_uv", workstationId: "print", requiredSkill: "print_operator", skillLabel: "Operator print" },
  { operationType: "print_banner", workstationId: "print", requiredSkill: "print_operator", skillLabel: "Operator print" },
  { operationType: "print_latex", workstationId: "print", requiredSkill: "print_operator", skillLabel: "Operator print" },
  // Cutter
  { operationType: "cutter_plotter", workstationId: "cutter_plotter", requiredSkill: "cutter_operator", skillLabel: "Operator cutter" },
  { operationType: "contour_cut", workstationId: "cutter_plotter", requiredSkill: "cutter_operator", skillLabel: "Operator cutter" },
  { operationType: "vinyl_cut", workstationId: "cutter_plotter", requiredSkill: "cutter_operator", skillLabel: "Operator cutter" },
  { operationType: "transfer_tape", workstationId: "cutter_plotter", requiredSkill: "cutter_operator", skillLabel: "Operator cutter" },
  // CNC
  { operationType: "cnc_cutting", workstationId: "cnc", requiredSkill: "cnc_operator", skillLabel: "Operator CNC" },
  { operationType: "cnc_debitare", workstationId: "cnc", requiredSkill: "cnc_operator", skillLabel: "Operator CNC" },
  { operationType: "routing", workstationId: "cnc", requiredSkill: "cnc_operator", skillLabel: "Operator CNC" },
  { operationType: "engraving", workstationId: "cnc", requiredSkill: "cnc_operator", skillLabel: "Operator CNC" },
  { operationType: "v_cutting_acm", workstationId: "cnc", requiredSkill: "cnc_operator", skillLabel: "Operator CNC" },
  { operationType: "laser_cutting", workstationId: "cnc", requiredSkill: "cnc_operator", skillLabel: "Operator CNC" },
  { operationType: "laser_engraving", workstationId: "cnc", requiredSkill: "cnc_operator", skillLabel: "Operator CNC" },
  // Modelare litere
  { operationType: "letter_return_forming", workstationId: "modelare_litere", requiredSkill: "litere_modelare", skillLabel: "Modelare litere" },
  { operationType: "alum_return_forming", workstationId: "modelare_litere", requiredSkill: "litere_modelare", skillLabel: "Modelare litere" },
  { operationType: "cant_modelare", workstationId: "modelare_litere", requiredSkill: "litere_modelare", skillLabel: "Modelare litere" },
  { operationType: "face_bonding", workstationId: "modelare_litere", requiredSkill: "litere_modelare", skillLabel: "Modelare litere" },
  { operationType: "letter_face_bonding", workstationId: "modelare_litere", requiredSkill: "litere_modelare", skillLabel: "Modelare litere" },
  // LED / Electric
  { operationType: "led_installation", workstationId: "led_electric", requiredSkill: "electrician_led", skillLabel: "Electrician LED" },
  { operationType: "montaj_led", workstationId: "led_electric", requiredSkill: "electrician_led", skillLabel: "Electrician LED" },
  { operationType: "power_supply", workstationId: "led_electric", requiredSkill: "electrician_led", skillLabel: "Electrician LED" },
  { operationType: "wiring", workstationId: "led_electric", requiredSkill: "electrician_led", skillLabel: "Electrician LED" },
  { operationType: "electrical_test", workstationId: "led_electric", requiredSkill: "electrician_led", skillLabel: "Electrician LED" },
  // Lăcătușerie / Sudură
  { operationType: "metal_frame", workstationId: "lacatuserie_sudura", requiredSkill: "lacatus", skillLabel: "Lăcătuș" },
  { operationType: "metal_frame_fabrication", workstationId: "lacatuserie_sudura", requiredSkill: "lacatus", skillLabel: "Lăcătuș" },
  { operationType: "cadru_metalic", workstationId: "lacatuserie_sudura", requiredSkill: "lacatus", skillLabel: "Lăcătuș" },
  { operationType: "welding", workstationId: "lacatuserie_sudura", requiredSkill: "sudor", skillLabel: "Sudor" },
  { operationType: "brackets", workstationId: "lacatuserie_sudura", requiredSkill: "lacatus", skillLabel: "Lăcătuș" },
  { operationType: "supports", workstationId: "lacatuserie_sudura", requiredSkill: "lacatus", skillLabel: "Lăcătuș" },
  // Asamblare / Lipire
  { operationType: "assembly", workstationId: "asamblare_lipire", requiredSkill: "asamblare", skillLabel: "Asamblare" },
  { operationType: "asamblare_finala", workstationId: "asamblare_lipire", requiredSkill: "asamblare", skillLabel: "Asamblare" },
  { operationType: "gluing", workstationId: "asamblare_lipire", requiredSkill: "asamblare", skillLabel: "Asamblare" },
  { operationType: "cleaning", workstationId: "asamblare_lipire", requiredSkill: "asamblare", skillLabel: "Asamblare" },
  { operationType: "packing", workstationId: "asamblare_lipire", requiredSkill: "ambalare", skillLabel: "Ambalare" },
  { operationType: "delivery_preparation", workstationId: "asamblare_lipire", requiredSkill: "ambalare", skillLabel: "Ambalare" },
  // Montaj autocolant
  { operationType: "vinyl_application", workstationId: "montaj_autocolant", requiredSkill: "colantator", skillLabel: "Colantator" },
  { operationType: "foil_application", workstationId: "montaj_autocolant", requiredSkill: "colantator", skillLabel: "Colantator" },
  { operationType: "print_application", workstationId: "montaj_autocolant", requiredSkill: "colantator", skillLabel: "Colantator" },
  { operationType: "colantare", workstationId: "montaj_autocolant", requiredSkill: "colantator", skillLabel: "Colantator" },
  // Canonical execution task types (backend BLK-08 enum) — compatibility layer
  { operationType: "file_preparation", workstationId: "cutter_plotter", requiredSkill: "cutter_operator", skillLabel: "Pregătire fișier" },
  { operationType: "cnc_routing", workstationId: "cnc", requiredSkill: "cnc_operator", skillLabel: "Operator CNC" },
  { operationType: "edge_bending", workstationId: "modelare_litere", requiredSkill: "litere_modelare", skillLabel: "Modelare litere" },
  { operationType: "plexi_cutting", workstationId: "cnc", requiredSkill: "cnc_operator", skillLabel: "Operator CNC" },
  { operationType: "vinyl_cutting", workstationId: "montaj_autocolant", requiredSkill: "colantator", skillLabel: "Colantator" },
  { operationType: "led_assembly", workstationId: "led_electric", requiredSkill: "electrician_led", skillLabel: "Electrician LED" },
  { operationType: "led_wiring", workstationId: "led_electric", requiredSkill: "electrician_led", skillLabel: "Electrician LED" },
  { operationType: "volumetric_letter_assembly", workstationId: "asamblare_lipire", requiredSkill: "asamblare", skillLabel: "Asamblare litere" },
  { operationType: "quality_control", workstationId: "asamblare_lipire", requiredSkill: "asamblare", skillLabel: "Control calitate" },
  { operationType: "packaging", workstationId: "asamblare_lipire", requiredSkill: "ambalare", skillLabel: "Ambalare" },
  { operationType: "final_assembly", workstationId: "asamblare_lipire", requiredSkill: "asamblare", skillLabel: "Asamblare finală" },
  { operationType: "produce_order", workstationId: "asamblare_lipire", requiredSkill: "asamblare", skillLabel: "Producție comandă" },
];

/** Map stable volumetric process_id keys to routing operation types. */
export const VOLUMETRIC_PROCESS_ID_ROUTING: Record<string, string> = {
  vector_prep: "file_preparation",
  face_cnc_cut: "cnc_routing",
  back_cut: "cnc_routing",
  mounting_template_cnc_cut: "cnc_routing",
  side_forming: "edge_bending",
  return_face_bonding: "welding",
  vinyl_application: "vinyl_cutting",
  led_install_letters: "led_assembly",
  electrical_letters: "led_wiring",
  painting: "volumetric_letter_assembly",
  assembly_letters: "volumetric_letter_assembly",
  qc_letters: "quality_control",
  packaging_letters: "packaging",
};

export function normalizeRoutingOperationType(opType: string, processId?: string): string {
  const normalized = opType.toLowerCase().replace(/[-\s]/g, "_");
  if (getRoutingForOperationDirect(normalized)) {
    return normalized;
  }
  const pid = (processId || "").toLowerCase().replace(/[-\s]/g, "_");
  if (pid && VOLUMETRIC_PROCESS_ID_ROUTING[pid]) {
    return VOLUMETRIC_PROCESS_ID_ROUTING[pid];
  }
  return normalized;
}

function getRoutingForOperationDirect(opType: string): RoutingEntry | undefined {
  return OPERATION_ROUTING.find((r) => r.operationType === opType);
}

export function getRoutingForOperation(opType: string, processId?: string): RoutingEntry | undefined {
  const normalized = normalizeRoutingOperationType(opType, processId);
  return getRoutingForOperationDirect(normalized);
}

export function getWorkstationForOperation(opType: string): Workstation | undefined {
  const routing = getRoutingForOperation(opType);
  if (!routing) return undefined;
  return getWorkstation(routing.workstationId);
}

// --- OPERATOR DEFINITIONS (DEMO ONLY — NOT CANONICAL) ---
// Canonical workforce data lives in /api/v1/operational-registry and employees DB.
// Do NOT add real employee names here; /tablet will consume the registry when wired.
export interface DemoOperator {
  id: string;
  name: string;
  skills: string[]; // workstation IDs
  status: "disponibil" | "ocupat" | "in_ajutor" | "indisponibil";
}

export const DEMO_OPERATORS: DemoOperator[] = [
  { id: "op-1", name: "Ion Popescu", skills: ["lacatuserie_sudura", "montaj_autocolant"], status: "disponibil" },
  { id: "op-2", name: "Mihai Ionescu", skills: ["lacatuserie_sudura", "asamblare_lipire"], status: "disponibil" },
  { id: "op-3", name: "Andrei Vasile", skills: ["cnc", "cutter_plotter"], status: "ocupat" },
  { id: "op-4", name: "Elena Dumitrescu", skills: ["print", "montaj_autocolant"], status: "disponibil" },
  { id: "op-5", name: "Sorin Marin", skills: ["led_electric", "asamblare_lipire"], status: "disponibil" },
  { id: "op-6", name: "Dana Gheorghe", skills: ["modelare_litere", "asamblare_lipire"], status: "disponibil" },
];

export function getEligibleOperators(workstationId: string): DemoOperator[] {
  return DEMO_OPERATORS.filter((op) => op.skills.includes(workstationId));
}

export function isOperatorEligible(operatorId: string, workstationId: string): boolean {
  const op = DEMO_OPERATORS.find((o) => o.id === operatorId);
  return op ? op.skills.includes(workstationId) : false;
}

// --- TASK STATUS ---
export type TabletTaskStatus =
  | "in_coada"
  | "pregatit"
  | "in_lucru"
  | "blocat"
  | "finalizat"
  | "predat"
  | "necesita_clarificare"
  | "ajutor_cerut"
  | "ajutor_preluat";

export const TASK_STATUS_CONFIG: Record<TabletTaskStatus, { label: string; cls: string }> = {
  in_coada: { label: "În coadă", cls: "bg-slate-700/60 text-slate-300 border-slate-600" },
  pregatit: { label: "Pregătit", cls: "bg-blue-900/40 text-blue-300 border-blue-700" },
  in_lucru: { label: "În lucru", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  blocat: { label: "Blocat", cls: "bg-red-900/40 text-red-300 border-red-700" },
  finalizat: { label: "Finalizat", cls: "bg-emerald-900/50 text-emerald-200 border-emerald-600" },
  predat: { label: "Predat", cls: "bg-cyan-900/40 text-cyan-300 border-cyan-700" },
  necesita_clarificare: { label: "Necesită clarificare", cls: "bg-amber-900/40 text-amber-300 border-amber-700" },
  ajutor_cerut: { label: "Ajutor cerut", cls: "bg-purple-900/40 text-purple-300 border-purple-700" },
  ajutor_preluat: { label: "Ajutor preluat", cls: "bg-purple-900/50 text-purple-200 border-purple-600" },
};

// --- HELP REQUEST ---
export type HelpReason =
  | "piesa_grea"
  | "tinere_pozitionare"
  | "sudura_aliniere"
  | "aplicare_folie"
  | "problema_tehnica"
  | "clarificare"
  | "alt_motiv";

export const HELP_REASONS: { value: HelpReason; label: string }[] = [
  { value: "piesa_grea", label: "Piesă grea / ridicare" },
  { value: "tinere_pozitionare", label: "Ținere / poziționare" },
  { value: "sudura_aliniere", label: "Sudură / aliniere" },
  { value: "aplicare_folie", label: "Aplicare folie" },
  { value: "problema_tehnica", label: "Problemă tehnică" },
  { value: "clarificare", label: "Clarificare" },
  { value: "alt_motiv", label: "Alt motiv" },
];

export interface HelpRequest {
  id: string;
  taskId: string;
  stationId: string;
  operatorName: string;
  reason: HelpReason;
  reasonLabel: string;
  observation: string;
  priority: "normal" | "urgent";
  status: "activ" | "preluat" | "rezolvat";
  createdAt: string;
}

// --- TABLET TASK (DEMO) ---
export interface TabletTask {
  id: string;
  orderId: string;
  orderCode: string;
  client: string;
  product: string;
  operationType: string;
  operationName: string;
  workstationId: string;
  requiredSkill: string;
  skillLabel: string;
  status: TabletTaskStatus;
  priority: "normal" | "urgent" | "low";
  deadline: string;
  assignedOperator?: string;
  // Details
  dimensions: string;
  material: string;
  color: string;
  quantity: number;
  observations: string;
  previousStation?: string;
  nextStation?: string;
  // Lăcătușerie special
  metalDetails?: {
    tipStructura: string;
    profilMetalic: string;
    lungimi: string;
    nrBucati: number;
    punctePrindere: string;
    observatiiSudura: string;
  };
  // Attachments
  attachments: { name: string; type: string; status: "aprobat" | "draft" | "vechi" }[];
  // Routing explanation
  routingExplanation: string;
  // Live bridge fields (optional — set when sourced from operator API)
  isLive?: boolean;
  isDemo?: boolean;
  mappingConfirmed?: boolean;
  liveStatus?: string;
  employeeId?: number | null;
  employeeName?: string | null;
  machineName?: string;
  orderIdNum?: number;
  layerId?: string;
  instructions?: string;
}

// --- STATION-SPECIFIC CHECKLISTS ---
export const STATION_CHECKLISTS: Record<string, string[]> = {
  lacatuserie_sudura: [
    "Verifică dimensiunile pe schiță",
    "Verifică profilul metalic",
    "Taie / debitează materialul",
    "Sudează conform specificațiilor",
    "Verifică unghiuri și colțuri",
    "Curăță / șlefuiește",
    "Predă la asamblare",
  ],
  asamblare_lipire: [
    "Verifică componentele primite",
    "Asamblează conform instrucțiunilor",
    "Lipește unde este necesar",
    "Montează LED / sursă dacă este cazul",
    "Testează funcționalitatea",
    "Curăță produsul",
    "Predă mai departe",
  ],
  montaj_autocolant: [
    "Curăță suprafața",
    "Poziționează autocolantul",
    "Aplică fără bule",
    "Verifică alinierea",
    "Finisează marginile",
    "Predă produsul",
  ],
  led_electric: [
    "Verifică schema electrică",
    "Montează LED-urile",
    "Conectează sursa de alimentare",
    "Verifică polaritatea",
    "Testează iluminarea",
    "Izolează conexiunile",
    "Predă la asamblare finală",
  ],
  modelare_litere: [
    "Verifică template-ul literei",
    "Pregătește materialul (aluminiu/plexiglas)",
    "Modelează cantul",
    "Verifică forma și dimensiunile",
    "Lipește fața pe cant",
    "Curăță excesul de adeziv",
    "Predă la LED/Electric",
  ],
  cnc: [
    "Încarcă fișierul în mașină",
    "Verifică materialul pe masă",
    "Setează originea",
    "Rulează programul",
    "Verifică piesa rezultată",
    "Curăță și deburează",
    "Predă piesa",
  ],
  print: [
    "Verifică fișierul de print",
    "Încarcă materialul în printer",
    "Setează profilul de culoare",
    "Lansează printul",
    "Verifică calitatea culorilor",
    "Lasă la uscat dacă este necesar",
    "Predă la cutter sau finisare",
  ],
  cutter_plotter: [
    "Încarcă fișierul vectorial",
    "Poziționează materialul",
    "Setează presiunea lamei",
    "Lansează tăierea",
    "Verifică conturul tăiat",
    "Curăță și sortează piesele",
    "Predă la montaj",
  ],
};

// --- DEMO TASKS ---
export function generateDemoTasks(): TabletTask[] {
  return [
    // Lăcătușerie / Sudură
    {
      id: "TT-001", orderId: "ORD-2024-015", orderCode: "CMD-015", client: "Mega Image", product: "Totem exterior iluminat",
      operationType: "metal_frame", operationName: "Fabricare cadru metalic", workstationId: "lacatuserie_sudura",
      requiredSkill: "lacatus", skillLabel: "Lăcătuș", status: "in_lucru", priority: "urgent", deadline: "2024-12-20",
      dimensions: "2400x600x150 mm", material: "Profil oțel 40x40x2", color: "Grunduit gri", quantity: 1,
      observations: "Atenție la perpendicularitate. Puncte de prindere pe spate pentru fixare perete.",
      previousStation: undefined, nextStation: "Asamblare / Lipire",
      metalDetails: {
        tipStructura: "Cadru suport totem", profilMetalic: "Oțel 40x40x2 mm", lungimi: "2x2400mm, 2x600mm, 3x150mm traverse",
        nrBucati: 1, punctePrindere: "4 puncte M10 pe spate, 2 console laterale",
        observatiiSudura: "Sudură MIG, verifică unghiuri 90°, șlefuiește cordoanele vizibile",
      },
      attachments: [
        { name: "schita_cadru_totem.pdf", type: "Schiță PDF", status: "aprobat" },
        { name: "referinta_totem.jpg", type: "Poză referință", status: "aprobat" },
      ],
      routingExplanation: "Operație: fabricare cadru metalic → Stație: Lăcătușerie / Sudură",
    },
    {
      id: "TT-002", orderId: "ORD-2024-015", orderCode: "CMD-015", client: "Mega Image", product: "Totem exterior iluminat",
      operationType: "welding", operationName: "Sudură console fixare", workstationId: "lacatuserie_sudura",
      requiredSkill: "sudor", skillLabel: "Sudor", status: "in_coada", priority: "urgent", deadline: "2024-12-20",
      dimensions: "Console 200x100 mm", material: "Platbandă oțel 5mm", color: "Grunduit", quantity: 4,
      observations: "Console pentru fixare perete. Sudură completă, nu puncte.",
      previousStation: undefined, nextStation: "Asamblare / Lipire",
      metalDetails: {
        tipStructura: "Console fixare perete", profilMetalic: "Platbandă 100x5 mm", lungimi: "4x200mm",
        nrBucati: 4, punctePrindere: "Găuri Ø12 la 50mm de margine",
        observatiiSudura: "Sudură completă pe ambele laturi, verifică planitatea",
      },
      attachments: [{ name: "detaliu_console.pdf", type: "Schiță PDF", status: "aprobat" }],
      routingExplanation: "Operație: sudură console → Stație: Lăcătușerie / Sudură",
    },
    // CNC
    {
      id: "TT-003", orderId: "ORD-2024-016", orderCode: "CMD-016", client: "Dedeman", product: "Litere volumetrice LED",
      operationType: "cnc_cutting", operationName: "Debitare fețe plexiglas", workstationId: "cnc",
      requiredSkill: "cnc_operator", skillLabel: "Operator CNC", status: "pregatit", priority: "normal", deadline: "2024-12-22",
      dimensions: "Litere H=300mm, grosime 3mm opal", material: "Plexiglas opal 3mm", color: "Opal alb", quantity: 8,
      observations: "8 litere: D-E-D-E-M-A-N + logo. Fișier vectorial confirmat.",
      previousStation: undefined, nextStation: "Modelare litere",
      attachments: [
        { name: "litere_dedeman.ai", type: "Fișier vectorial", status: "aprobat" },
        { name: "bun_de_tipar_litere.pdf", type: "Bun de tipar", status: "aprobat" },
      ],
      routingExplanation: "Operație: debitare CNC plexiglas → Stație: CNC",
    },
    {
      id: "TT-004", orderId: "ORD-2024-017", orderCode: "CMD-017", client: "Kaufland", product: "Panou ACM iluminat",
      operationType: "v_cutting_acm", operationName: "V-cutting panou ACM", workstationId: "cnc",
      requiredSkill: "cnc_operator", skillLabel: "Operator CNC", status: "in_coada", priority: "normal", deadline: "2024-12-23",
      dimensions: "3000x1500 mm, ACM 4mm", material: "ACM alb 4mm", color: "Alb RAL 9003", quantity: 2,
      observations: "V-cut pe 4 laturi pentru îndoire. Atenție la adâncime: 3mm din 4mm.",
      previousStation: undefined, nextStation: "Asamblare / Lipire",
      attachments: [{ name: "desen_panou_acm.pdf", type: "Schiță PDF", status: "aprobat" }],
      routingExplanation: "Operație: V-cutting ACM → Stație: CNC",
    },
    // Print
    {
      id: "TT-005", orderId: "ORD-2024-018", orderCode: "CMD-018", client: "Lidl", product: "Banner promotional",
      operationType: "print_banner", operationName: "Print banner mesh", workstationId: "print",
      requiredSkill: "print_operator", skillLabel: "Operator print", status: "in_coada", priority: "low", deadline: "2024-12-25",
      dimensions: "6000x2000 mm", material: "Mesh 270g", color: "Full color CMYK", quantity: 2,
      observations: "Rezoluție 720dpi. Margini albe 5cm pentru capse.",
      previousStation: undefined, nextStation: "Asamblare / Lipire",
      attachments: [
        { name: "banner_lidl_v3.pdf", type: "Bun de tipar", status: "aprobat" },
        { name: "preview_banner.jpg", type: "Poză referință", status: "aprobat" },
      ],
      routingExplanation: "Operație: print banner → Stație: Print",
    },
    // Cutter
    {
      id: "TT-006", orderId: "ORD-2024-019", orderCode: "CMD-019", client: "Profi", product: "Autocolant vitrine",
      operationType: "contour_cut", operationName: "Tăiere contur autocolant", workstationId: "cutter_plotter",
      requiredSkill: "cutter_operator", skillLabel: "Operator cutter", status: "pregatit", priority: "normal", deadline: "2024-12-21",
      dimensions: "1200x800 mm per bucată", material: "Autocolant Oracal 651", color: "Roșu + alb", quantity: 6,
      observations: "Contur complex cu text. Verifică alinierea la crop marks.",
      previousStation: "Print", nextStation: "Montaj autocolant",
      attachments: [{ name: "contur_profi.ai", type: "Fișier vectorial", status: "aprobat" }],
      routingExplanation: "Operație: tăiere contur → Stație: Cutter plotter",
    },
    // Modelare litere
    {
      id: "TT-007", orderId: "ORD-2024-016", orderCode: "CMD-016", client: "Dedeman", product: "Litere volumetrice LED",
      operationType: "letter_return_forming", operationName: "Modelare cant aluminiu", workstationId: "modelare_litere",
      requiredSkill: "litere_modelare", skillLabel: "Modelare litere", status: "in_coada", priority: "normal", deadline: "2024-12-22",
      dimensions: "Litere H=300mm, adâncime 80mm", material: "Bandă aluminiu 0.5mm, lățime 80mm", color: "Natur aluminiu", quantity: 8,
      observations: "Modelare manuală pe tipar. Lipire cu silicon structural.",
      previousStation: "CNC", nextStation: "LED / Electric",
      attachments: [{ name: "tipar_litere.pdf", type: "Schiță PDF", status: "aprobat" }],
      routingExplanation: "Operație: modelare cant aluminiu → Stație: Modelare litere",
    },
    // LED / Electric
    {
      id: "TT-008", orderId: "ORD-2024-016", orderCode: "CMD-016", client: "Dedeman", product: "Litere volumetrice LED",
      operationType: "led_installation", operationName: "Montaj LED în litere", workstationId: "led_electric",
      requiredSkill: "electrician_led", skillLabel: "Electrician LED", status: "in_coada", priority: "normal", deadline: "2024-12-23",
      dimensions: "Litere H=300mm", material: "Module LED alb 6500K, sursă 12V 150W", color: "Alb rece 6500K", quantity: 8,
      observations: "Distanță între module: 5cm. Conectare serie max 10 module. Sursă separată.",
      previousStation: "Modelare litere", nextStation: "Asamblare / Lipire",
      attachments: [{ name: "schema_led.pdf", type: "Schiță PDF", status: "draft" }],
      routingExplanation: "Operație: montaj LED → Stație: Montaj LED / Electric",
    },
    // Montaj autocolant
    {
      id: "TT-009", orderId: "ORD-2024-019", orderCode: "CMD-019", client: "Profi", product: "Autocolant vitrine",
      operationType: "vinyl_application", operationName: "Aplicare autocolant pe vitrine", workstationId: "montaj_autocolant",
      requiredSkill: "colantator", skillLabel: "Colantator", status: "in_coada", priority: "normal", deadline: "2024-12-22",
      dimensions: "1200x800 mm per bucată", material: "Autocolant Oracal 651 tăiat", color: "Roșu + alb", quantity: 6,
      observations: "Aplicare umedă. Verifică bule. Finisare cu racletă de felt.",
      previousStation: "Cutter plotter", nextStation: undefined,
      attachments: [{ name: "pozitionare_vitrina.jpg", type: "Poză referință", status: "aprobat" }],
      routingExplanation: "Operație: aplicare autocolant → Stație: Montaj autocolant",
    },
    // Asamblare
    {
      id: "TT-010", orderId: "ORD-2024-015", orderCode: "CMD-015", client: "Mega Image", product: "Totem exterior iluminat",
      operationType: "assembly", operationName: "Asamblare finală totem", workstationId: "asamblare_lipire",
      requiredSkill: "asamblare", skillLabel: "Asamblare", status: "in_coada", priority: "urgent", deadline: "2024-12-21",
      dimensions: "2400x600x150 mm", material: "Cadru metalic + panouri ACM + LED", color: "Conform BDT", quantity: 1,
      observations: "Asamblare cadru + panouri. Montaj sursă LED în compartiment. Testare finală.",
      previousStation: "Lăcătușerie / Sudură", nextStation: "Montaj autocolant",
      attachments: [
        { name: "explozie_totem.pdf", type: "Schiță PDF", status: "aprobat" },
        { name: "referinta_totem_final.jpg", type: "Poză referință", status: "aprobat" },
      ],
      routingExplanation: "Operație: asamblare finală → Stație: Asamblare / Lipire",
    },
    // Another Lăcătușerie task - blocat
    {
      id: "TT-011", orderId: "ORD-2024-020", orderCode: "CMD-020", client: "OMV", product: "Structură pylone preț",
      operationType: "metal_frame", operationName: "Fabricare structură pylon", workstationId: "lacatuserie_sudura",
      requiredSkill: "lacatus", skillLabel: "Lăcătuș", status: "blocat", priority: "urgent", deadline: "2024-12-19",
      dimensions: "4000x1200x300 mm", material: "Profil oțel 60x60x3", color: "Grunduit", quantity: 1,
      observations: "BLOCAT: Lipsă profil 60x60x3. Așteptăm livrare furnizor.",
      previousStation: undefined, nextStation: "Asamblare / Lipire",
      metalDetails: {
        tipStructura: "Pylon preț carburanți", profilMetalic: "Oțel 60x60x3 mm", lungimi: "2x4000mm, 4x1200mm, 6x300mm",
        nrBucati: 1, punctePrindere: "Placă bază 400x400x10 cu 4xM16",
        observatiiSudura: "Sudură MAG, cordoane continue pe stâlpi, verifică verticalitatea",
      },
      attachments: [{ name: "desen_pylon.pdf", type: "Schiță PDF", status: "aprobat" }],
      routingExplanation: "Operație: fabricare structură metalică → Stație: Lăcătușerie / Sudură",
    },
    // Finalizat azi
    {
      id: "TT-012", orderId: "ORD-2024-014", orderCode: "CMD-014", client: "Carrefour", product: "Casete luminoase",
      operationType: "print_uv", operationName: "Print UV pe plexiglas", workstationId: "print",
      requiredSkill: "print_operator", skillLabel: "Operator print", status: "finalizat", priority: "normal", deadline: "2024-12-18",
      dimensions: "1000x500 mm", material: "Plexiglas opal 3mm", color: "Full color + alb", quantity: 4,
      observations: "Finalizat. Calitate OK.",
      previousStation: undefined, nextStation: "Asamblare / Lipire",
      attachments: [{ name: "print_casete.pdf", type: "Bun de tipar", status: "aprobat" }],
      routingExplanation: "Operație: print UV → Stație: Print",
    },
  ];
}

// --- DEMO HELP REQUESTS ---
export function generateDemoHelpRequests(): HelpRequest[] {
  return [
    {
      id: "HR-001", taskId: "TT-001", stationId: "lacatuserie_sudura", operatorName: "Ion Popescu",
      reason: "piesa_grea", reasonLabel: "Piesă grea / ridicare", observation: "Cadru 2.4m, necesit ajutor la ridicare pe masa de lucru.",
      priority: "normal", status: "activ", createdAt: "2024-12-18T09:30:00",
    },
    {
      id: "HR-002", taskId: "TT-011", stationId: "lacatuserie_sudura", operatorName: "Mihai Ionescu",
      reason: "problema_tehnica", reasonLabel: "Problemă tehnică", observation: "Profil 60x60 nu corespunde cu schița. Diferență 2mm.",
      priority: "urgent", status: "activ", createdAt: "2024-12-18T10:15:00",
    },
  ];
}

// --- STATION STATS HELPER ---
export interface StationStats {
  queue: number;
  inProgress: number;
  blocked: number;
  completedToday: number;
  activeOperators: number;
  helpRequests: number;
}

export function getStationStats(workstationId: string, tasks: TabletTask[], helpRequests: HelpRequest[]): StationStats {
  const stationTasks = tasks.filter((t) => t.workstationId === workstationId);
  const eligible = getEligibleOperators(workstationId);
  const activeOps = eligible.filter((op) => op.status === "disponibil" || op.status === "ocupat").length;
  const stationHelp = helpRequests.filter((h) => h.stationId === workstationId && h.status === "activ");

  return {
    queue: stationTasks.filter((t) => t.status === "in_coada" || t.status === "pregatit").length,
    inProgress: stationTasks.filter((t) => t.status === "in_lucru").length,
    blocked: stationTasks.filter((t) => t.status === "blocat").length,
    completedToday: stationTasks.filter((t) => t.status === "finalizat" || t.status === "predat").length,
    activeOperators: activeOps,
    helpRequests: stationHelp.length,
  };
}