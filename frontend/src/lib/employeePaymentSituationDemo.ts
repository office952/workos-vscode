/**
 * Demo payment situation builder — UI contract only, no backend persistence.
 */
import type { Advance, EmployeeRecord } from "@/lib/employeeRecordsData";
import { getMonthlyAttendance } from "@/lib/employeeRecordsData";
import { generatePaymentRunForEmployees } from "@/lib/operationalEmployeeRecords";

export type PaymentSlotKey = "15" | "30";
export type SlotPaymentStatus = "neplatit" | "partial" | "platit";
export type RecordedPaymentStatus = "draft" | "confirmed" | "cancelled";

export interface RecordedPaymentEntry {
  id: string;
  employeeId: string;
  employeeName: string;
  month: string;
  slot: PaymentSlotKey;
  amountPaid: number;
  paymentDate: string;
  notes?: string;
  status: RecordedPaymentStatus;
  createdAt: string;
}

export interface PaymentSlotDetails {
  bazaCalculata: number;
  ajustarePontaj: number;
  oreSuplimentare: number;
  avansuriDatorii: number;
}

export interface PaymentSlotSituation {
  slot: PaymentSlotKey;
  label: string;
  expectedAmount: number;
  paidAmount: number;
  remainingAmount: number;
  status: SlotPaymentStatus;
  details: PaymentSlotDetails;
  history?: RecordedPaymentEntry[];
}

export interface EmployeePaymentSituation {
  employeeId: string;
  employeeName: string;
  month: string;
  calculatedMonthly: number;
  paidSoFar: number;
  remainingTotal: number;
  attendanceSummary: string;
  advancesDebtsSummary: string;
  missingBase: boolean;
  slot15: PaymentSlotSituation;
  slot30: PaymentSlotSituation;
}

export interface MonthPaymentSummary {
  calculated: number;
  paid: number;
  remaining: number;
  partialOrUnpaidSlots: number;
}

export function formatMonthKey(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, "0")}`;
}

export function parseMonthKey(key: string): { year: number; month: number } {
  const [y, m] = key.split("-").map(Number);
  return { year: y, month: m };
}

export function shiftMonthKey(key: string, delta: number): string {
  const { year, month } = parseMonthKey(key);
  const d = new Date(year, month - 1 + delta, 1);
  return formatMonthKey(d.getFullYear(), d.getMonth() + 1);
}

export function slotStatusLabel(status: SlotPaymentStatus): string {
  switch (status) {
    case "platit":
      return "Plătit";
    case "partial":
      return "Parțial";
    default:
      return "Neplătit";
  }
}

function activePaidForSlot(
  recorded: RecordedPaymentEntry[],
  employeeId: string,
  month: string,
  slot: PaymentSlotKey
): number {
  return recorded
    .filter(
      (r) =>
        r.employeeId === employeeId &&
        r.month === month &&
        r.slot === slot &&
        r.status !== "cancelled"
    )
    .reduce((sum, r) => sum + r.amountPaid, 0);
}

function buildSlotSituation(
  expectedAmount: number,
  paidAmount: number,
  slot: PaymentSlotKey,
  label: string,
  details: PaymentSlotDetails = {
    bazaCalculata: 0,
    ajustarePontaj: 0,
    oreSuplimentare: 0,
    avansuriDatorii: 0,
  }
): PaymentSlotSituation {
  const remainingAmount = Math.max(0, expectedAmount - paidAmount);
  let status: SlotPaymentStatus = "neplatit";
  if (expectedAmount <= 0) {
    status = "neplatit";
  } else if (paidAmount >= expectedAmount) {
    status = "platit";
  } else if (paidAmount > 0) {
    status = "partial";
  }
  return {
    slot,
    label,
    expectedAmount,
    paidAmount,
    remainingAmount,
    status,
    details,
  };
}

function slotDetailsFromRun(run: {
  transaTeorica: number;
  deducereZileLipsa: number;
  valorOreSuplimentare: number;
  avansuri: number;
  rateDatorii: number;
  alteRetineri: number;
}): PaymentSlotDetails {
  return {
    bazaCalculata: run.transaTeorica,
    ajustarePontaj: run.deducereZileLipsa,
    oreSuplimentare: run.valorOreSuplimentare,
    avansuriDatorii: run.avansuri + run.rateDatorii + run.alteRetineri,
  };
}

function attendanceSummaryText(employeeId: string, month: string): string {
  const att = getMonthlyAttendance(employeeId, month);
  if (att.zileLipsa > 0 || att.zileNemotivat > 0) {
    return `Incomplet — ${att.zileLipsa + att.zileNemotivat} zile lipsă`;
  }
  return `OK — ${att.zilePrezente}/${att.zileLucratoare} zile`;
}

function advancesDebtsSummaryText(employeeId: string, advances: Advance[]): string {
  const active = advances.filter((a) => a.employeeId === employeeId && a.status === "activ");
  if (active.length === 0) return "Sold 0 RON";
  const total = active.reduce((s, a) => s + (a.soldRamas ?? a.suma), 0);
  return `Sold activ ${total.toLocaleString("ro-RO")} RON (${active.length} poz.)`;
}

export function buildEmployeePaymentSituations(
  employees: EmployeeRecord[],
  advances: Advance[],
  month: string,
  recorded: RecordedPaymentEntry[]
): EmployeePaymentSituation[] {
  const runs15 = generatePaymentRunForEmployees(employees, advances, month, "15");
  const runs30 = generatePaymentRunForEmployees(employees, advances, month, "30");

  return runs15.map((run15) => {
    const run30 = runs30.find((r) => r.employeeId === run15.employeeId);
    const expected15 = run15.totalDeDat;
    const expected30 = run30?.totalDeDat ?? 0;
    const paid15 = activePaidForSlot(recorded, run15.employeeId, month, "15");
    const paid30 = activePaidForSlot(recorded, run15.employeeId, month, "30");
    const slot15 = buildSlotSituation(
      expected15,
      paid15,
      "15",
      "Tranșa 15",
      run15 ? slotDetailsFromRun(run15) : undefined
    );
    const slot30 = buildSlotSituation(
      expected30,
      paid30,
      "30",
      "Tranșa 30",
      run30 ? slotDetailsFromRun(run30) : undefined
    );
    const calculatedMonthly = expected15 + expected30;
    const paidSoFar = paid15 + paid30;

    return {
      employeeId: run15.employeeId,
      employeeName: run15.employeeName,
      month,
      calculatedMonthly,
      paidSoFar,
      remainingTotal: Math.max(0, calculatedMonthly - paidSoFar),
      attendanceSummary: attendanceSummaryText(run15.employeeId, month),
      advancesDebtsSummary: advancesDebtsSummaryText(run15.employeeId, advances),
      missingBase: run15.sumaLunaraInterna <= 0,
      slot15,
      slot30,
    };
  });
}

export function computeMonthPaymentSummary(
  situations: EmployeePaymentSituation[]
): MonthPaymentSummary {
  let calculated = 0;
  let paid = 0;
  let partialOrUnpaidSlots = 0;

  for (const s of situations) {
    calculated += s.calculatedMonthly;
    paid += s.paidSoFar;
    if (s.slot15.status !== "platit") partialOrUnpaidSlots += 1;
    if (s.slot30.status !== "platit") partialOrUnpaidSlots += 1;
  }

  return {
    calculated,
    paid,
    remaining: Math.max(0, calculated - paid),
    partialOrUnpaidSlots,
  };
}

export function createRecordedPayment(
  employeeId: string,
  employeeName: string,
  month: string,
  slot: PaymentSlotKey,
  amountPaid: number,
  paymentDate: string,
  notes?: string,
  status: RecordedPaymentStatus = "confirmed"
): RecordedPaymentEntry {
  return {
    id: `rec-${employeeId}-${month}-${slot}-${Date.now()}`,
    employeeId,
    employeeName,
    month,
    slot,
    amountPaid,
    paymentDate,
    notes,
    status,
    createdAt: new Date().toISOString(),
  };
}
