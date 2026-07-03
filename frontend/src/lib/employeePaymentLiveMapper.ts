import type {
  EmployeePaymentEmployeeDTO,
  PaymentSituationDTO,
  PaymentSlotSituationDTO,
  ApiPaymentStatus,
} from "@/api/employeePayments";
import type {
  EmployeePaymentSituation,
  MonthPaymentSummary,
  PaymentSlotKey,
  PaymentSlotSituation,
  RecordedPaymentEntry,
  SlotPaymentStatus,
} from "@/lib/employeePaymentSituationDemo";

function mapStatus(status: ApiPaymentStatus): SlotPaymentStatus {
  switch (status) {
    case "paid":
      return "platit";
    case "partial":
      return "partial";
    default:
      return "neplatit";
  }
}

function mapHistory(
  items: PaymentSlotSituationDTO["history"],
  employeeId: string,
  employeeName: string,
  month: string,
  slot: PaymentSlotKey
): RecordedPaymentEntry[] {
  return items.map((h) => ({
    id: String(h.id),
    employeeId,
    employeeName,
    month,
    slot,
    amountPaid: h.amount_paid,
    paymentDate: h.payment_date,
    notes: h.notes ?? undefined,
    status: h.cancelled || h.status === "cancelled" ? "cancelled" : "confirmed",
    createdAt: h.created_at ?? h.payment_date,
  }));
}

function mapSlot(
  slot: PaymentSlotKey,
  data: PaymentSlotSituationDTO,
  employeeId: string,
  employeeName: string,
  month: string
): PaymentSlotSituation {
  const label = slot === "15" ? "Tranșa 15" : "Tranșa 30 / final lună";
  const suggested = data.breakdown.suggested_deduction ?? 0;
  return {
    slot,
    label,
    expectedAmount: data.expected_amount,
    paidAmount: data.paid_amount,
    remainingAmount: data.remaining_amount,
    status: mapStatus(data.status),
    details: {
      bazaCalculata: data.breakdown.base_amount,
      ajustarePontaj: data.breakdown.attendance_adjustment,
      oreSuplimentare: data.breakdown.overtime_amount,
      avansuriDatorii: suggested > 0 ? suggested : data.breakdown.advances_debts_deduction,
    },
    history: mapHistory(data.history, employeeId, employeeName, month, slot),
  };
}

function mapEmployee(row: EmployeePaymentEmployeeDTO, monthKey: string): EmployeePaymentSituation {
  const employeeId = String(row.employee_id);
  const slot15 = mapSlot("15", row.slots["15"], employeeId, row.employee_name, monthKey);
  const slot30 = mapSlot("30", row.slots["30"], employeeId, row.employee_name, monthKey);
  return {
    employeeId,
    employeeName: row.employee_name,
    month: monthKey,
    calculatedMonthly: row.monthly_expected_amount,
    paidSoFar: row.monthly_paid_amount,
    remainingTotal: row.monthly_remaining_amount,
    attendanceSummary: row.attendance_label,
    advancesDebtsSummary: row.advances_debts_label,
    missingBase: row.missing_pay_base,
    slot15,
    slot30,
  };
}

export function mapPaymentSituationResponse(
  data: PaymentSituationDTO,
  monthKey: string
): { situations: EmployeePaymentSituation[]; summary: MonthPaymentSummary } {
  const situations = data.employees.map((e) => mapEmployee(e, monthKey));
  const summary: MonthPaymentSummary = {
    calculated: data.summary.expected_total,
    paid: data.summary.paid_total,
    remaining: data.summary.remaining_total,
    partialOrUnpaidSlots: data.summary.unpaid_count + data.summary.partial_count,
  };
  return { situations, summary };
}
