/**
 * Employee Internal Records — Demo Data Layer
 *
 * EVIDENȚĂ INTERNĂ — NU este document fiscal/contabil.
 * Toate datele sunt demonstrative.
 */

// ============================================================
// TYPES
// ============================================================

export type EmployeeStatus = "activ" | "inactiv" | "plecat";

export type DocumentType =
  | "contract_munca"
  | "act_aditional"
  | "fisa_post"
  | "medicina_muncii"
  | "ssm_psi"
  | "alt_document";

export type DocumentStatus = "valid" | "expira_curand" | "expirat" | "lipsa";

export type AttendanceType =
  | "prezent"
  | "absent"
  | "liber"
  | "medical"
  | "nemotivat"
  | "concediu";

export type PaymentStatus =
  | "de_calculat"
  | "verificat"
  | "pregatit_plata"
  | "platit"
  | "blocat";

export type AdvanceStatus = "activ" | "retinut" | "anulat";
export type LoanStatus = "activ" | "achitat" | "blocat";

export type AlertType =
  | "medicina_muncii_expira"
  | "contract_lipsa"
  | "document_lipsa"
  | "pontaj_incomplet"
  | "datorie_activa"
  | "data_plata_aproape"
  | "plata_neconfirmata"
  | "absenta_nejustificata";

export interface EmployeeStation {
  id: string;
  name: string;
}

export interface EmployeeRecord {
  id: string;
  name: string;
  functie: string;
  departament: string;
  statiePrincipala: string;
  status: EmployeeStatus;
  dataAngajarii: string;
  telefon: string;
  email: string;
  observatii: string;
  sumaLunaraInterna: number;
  skills: string[];
}

export interface EmployeeDocument {
  id: string;
  employeeId: string;
  tip: DocumentType;
  tipLabel: string;
  dataEmitere: string;
  dataExpirare: string | null;
  status: DocumentStatus;
  observatii: string;
}

export interface AttendanceDay {
  date: string; // YYYY-MM-DD
  type: AttendanceType;
  oreLucrate: number;
  oreSuplimentare: number;
  observatii: string;
}

export interface MonthlyAttendance {
  employeeId: string;
  month: string; // YYYY-MM
  zileLucratoare: number;
  zilePrezente: number;
  zileLipsa: number;
  oreNormale: number;
  oreSuplimentare: number;
  zileConcediu: number;
  zileLiber: number;
  zileMedical: number;
  zileNemotivat: number;
  days: AttendanceDay[];
}

export interface PaymentRun {
  id: string;
  employeeId: string;
  employeeName: string;
  month: string; // YYYY-MM
  dataPlata: "15" | "30";
  sumaLunaraInterna: number;
  transaTeorica: number; // 50%
  zileLipsa: number;
  deducereZileLipsa: number;
  oreSuplimentare: number;
  valorOreSuplimentare: number;
  bonusuri: number;
  avansuri: number;
  rateDatorii: number;
  alteRetineri: number;
  totalDeDat: number;
  status: PaymentStatus;
}

export interface Advance {
  id: string;
  employeeId: string;
  employeeName: string;
  tip: "avans" | "imprumut" | "retinere";
  suma: number;
  dataAcordare: string;
  // For imprumut
  nrRate?: number;
  rataLunara?: number;
  soldRamas?: number;
  dataInceput?: string;
  // For retinere
  motiv?: string;
  lunaAplicare?: string;
  // Common
  status: AdvanceStatus | LoanStatus;
  observatii: string;
}

export interface InternalAlert {
  id: string;
  employeeId: string;
  employeeName: string;
  type: AlertType;
  message: string;
  severity: "warning" | "error" | "info";
  date: string;
}

// ============================================================
// DOCUMENT TYPE LABELS
// ============================================================

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  contract_munca: "Contract de muncă",
  act_aditional: "Act adițional",
  fisa_post: "Fișă post",
  medicina_muncii: "Medicina muncii",
  ssm_psi: "SSM / PSI",
  alt_document: "Alt document",
};

export const DOCUMENT_STATUS_CONFIG: Record<DocumentStatus, { label: string; cls: string }> = {
  valid: { label: "Valid", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  expira_curand: { label: "Expiră curând", cls: "bg-amber-900/40 text-amber-300 border-amber-700" },
  expirat: { label: "Expirat", cls: "bg-red-900/40 text-red-300 border-red-700" },
  lipsa: { label: "Lipsă", cls: "bg-slate-700/60 text-slate-400 border-slate-600" },
};

export const ATTENDANCE_TYPE_CONFIG: Record<AttendanceType, { label: string; cls: string; short: string }> = {
  prezent: { label: "Prezent", cls: "bg-emerald-900/40 text-emerald-300", short: "P" },
  absent: { label: "Absent", cls: "bg-red-900/40 text-red-300", short: "A" },
  liber: { label: "Liber", cls: "bg-blue-900/40 text-blue-300", short: "L" },
  medical: { label: "Medical", cls: "bg-amber-900/40 text-amber-300", short: "M" },
  nemotivat: { label: "Nemotivat", cls: "bg-red-900/60 text-red-200", short: "N" },
  concediu: { label: "Concediu", cls: "bg-cyan-900/40 text-cyan-300", short: "CO" },
};

export const PAYMENT_STATUS_CONFIG: Record<PaymentStatus, { label: string; cls: string }> = {
  de_calculat: { label: "De calculat", cls: "bg-slate-700/60 text-slate-300 border-slate-600" },
  verificat: { label: "Verificat", cls: "bg-blue-900/40 text-blue-300 border-blue-700" },
  pregatit_plata: { label: "Pregătit de plată", cls: "bg-amber-900/40 text-amber-300 border-amber-700" },
  platit: { label: "Plătit", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  blocat: { label: "Blocat", cls: "bg-red-900/40 text-red-300 border-red-700" },
};

export const ALERT_TYPE_LABELS: Record<AlertType, string> = {
  medicina_muncii_expira: "Medicina muncii expiră",
  contract_lipsa: "Contract lipsă",
  document_lipsa: "Document lipsă",
  pontaj_incomplet: "Pontaj incomplet",
  datorie_activa: "Datorie activă",
  data_plata_aproape: "Data de plată se apropie",
  plata_neconfirmata: "Plată pregătită nemarcată",
  absenta_nejustificata: "Absență nejustificată",
};

// Employee population for HR demo modules comes from live operational employees
// via `operationalEmployeeRecords.ts` — no static demo person list here.

// ============================================================
// DEMO ATTENDANCE (deterministic per employee id)
// ============================================================

function generateMonthDays(employeeId: string, month: string): AttendanceDay[] {
  const year = parseInt(month.split("-")[0]);
  const mo = parseInt(month.split("-")[1]) - 1;
  const daysInMonth = new Date(year, mo + 1, 0).getDate();
  const days: AttendanceDay[] = [];

  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(year, mo, d);
    const dayOfWeek = date.getDay(); // 0=Sun, 6=Sat
    const dateStr = `${month}-${String(d).padStart(2, "0")}`;

    if (dayOfWeek === 0 || dayOfWeek === 6) continue; // skip weekends

    // Default: present
    let type: AttendanceType = "prezent";
    let oreLucrate = 8;
    let oreSuplimentare = 0;
    let observatii = "";

    let idHash = 0;
    for (let i = 0; i < employeeId.length; i++) {
      idHash += employeeId.charCodeAt(i);
    }
    const seed = (idHash + d) % 20;
    if (seed === 0 && d > 5) {
      type = "medical";
      oreLucrate = 0;
      observatii = "Certificat medical";
    } else if (seed === 3 && d > 10) {
      type = "concediu";
      oreLucrate = 0;
      observatii = "Concediu odihnă";
    } else if (seed === 7 && d > 15 && idHash % 4 === 1) {
      type = "nemotivat";
      oreLucrate = 0;
      observatii = "Absență nejustificată";
    } else if (seed === 5 && d > 8) {
      oreSuplimentare = 2;
      observatii = "Ore suplimentare — comandă urgentă";
    }

    days.push({ date: dateStr, type, oreLucrate, oreSuplimentare, observatii });
  }
  return days;
}

export function getMonthlyAttendance(employeeId: string, month: string): MonthlyAttendance {
  const days = generateMonthDays(employeeId, month);
  const zileLucratoare = days.length;
  const zilePrezente = days.filter((d) => d.type === "prezent").length;
  const zileLipsa = days.filter((d) => d.type === "absent" || d.type === "nemotivat").length;
  const oreNormale = days.reduce((s, d) => s + d.oreLucrate, 0);
  const oreSuplimentare = days.reduce((s, d) => s + d.oreSuplimentare, 0);
  const zileConcediu = days.filter((d) => d.type === "concediu").length;
  const zileLiber = days.filter((d) => d.type === "liber").length;
  const zileMedical = days.filter((d) => d.type === "medical").length;
  const zileNemotivat = days.filter((d) => d.type === "nemotivat").length;

  return {
    employeeId,
    month,
    zileLucratoare,
    zilePrezente,
    zileLipsa,
    oreNormale,
    oreSuplimentare,
    zileConcediu,
    zileLiber,
    zileMedical,
    zileNemotivat,
    days,
  };
}

// ============================================================
// HELPER FUNCTIONS (require caller-provided demo collections)
// ============================================================

export function getEmployeeById(
  id: string,
  employees: EmployeeRecord[]
): EmployeeRecord | undefined {
  return employees.find((e) => e.id === id);
}

export function getDocumentsForEmployee(
  employeeId: string,
  documents: EmployeeDocument[]
): EmployeeDocument[] {
  return documents.filter((d) => d.employeeId === employeeId);
}

export function getAdvancesForEmployee(employeeId: string, advances: Advance[]): Advance[] {
  return advances.filter((a) => a.employeeId === employeeId);
}

export function getAlertsForEmployee(employeeId: string, alerts: InternalAlert[]): InternalAlert[] {
  return alerts.filter((a) => a.employeeId === employeeId);
}

export function getAllActiveAdvances(advances: Advance[]): Advance[] {
  return advances.filter((a) => a.status === "activ");
}