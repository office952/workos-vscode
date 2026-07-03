import type { EmployeeRequestStatus, EmployeeRequestType } from "@/api/employeeMobileRequests";
import type { AttendanceEventStatus, AttendanceEventType } from "@/api/employeeAttendance";

export const REQUEST_TYPE_LABELS: Record<EmployeeRequestType, string> = {
  leave: "Concediu",
  day_off: "Zi liberă",
  time_off: "Învoire",
  advance: "Avans",
  attendance_correction: "Corecție pontaj",
  equipment: "Echipament",
  issue_report: "Raport problemă",
  other: "Altele",
};

export const REQUEST_STATUS_LABELS: Record<EmployeeRequestStatus, string> = {
  draft: "Ciornă",
  submitted: "În așteptare",
  approved: "Aprobată",
  rejected: "Respinsă",
  cancelled: "Anulată",
};

export type EmployeeMobileStatusBadgeVariant =
  | "live"
  | "readonly"
  | "review"
  | "neutral"
  | "warning";

export function requestStatusBadgeVariant(
  status: EmployeeRequestStatus,
): EmployeeMobileStatusBadgeVariant {
  if (status === "submitted" || status === "draft") return "warning";
  if (status === "approved") return "live";
  if (status === "rejected") return "neutral";
  return "neutral";
}

export function formatDisplayDate(value?: string | null): string | null {
  if (!value) return null;
  const datePart = value.slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(datePart)) return value;
  const [y, m, d] = datePart.split("-");
  return `${d}.${m}.${y}`;
}

export function formatDateTime(value?: string | null): string | null {
  if (!value) return null;
  const date = formatDisplayDate(value);
  const timePart = value.length > 11 ? value.slice(11, 16) : null;
  return timePart ? `${date} ${timePart}` : date;
}

export const ATTENDANCE_EVENT_TYPE_LABELS: Record<AttendanceEventType, string> = {
  absent: "Absent",
  leave: "Concediu",
  sick: "Medical",
  partial: "Parțial",
  overtime: "Suplimentar",
  correction: "Corecție",
};

export const ATTENDANCE_EVENT_STATUS_LABELS: Record<AttendanceEventStatus, string> = {
  planned: "Planificat",
  approved: "Aprobat",
  confirmed: "Confirmat",
  cancelled: "Anulat",
};

export const ROMANIAN_MONTH_NAMES = [
  "Ianuarie",
  "Februarie",
  "Martie",
  "Aprilie",
  "Mai",
  "Iunie",
  "Iulie",
  "August",
  "Septembrie",
  "Octombrie",
  "Noiembrie",
  "Decembrie",
] as const;

export function formatMonthYearLabel(year: number, month: number): string {
  const name = ROMANIAN_MONTH_NAMES[month - 1] ?? String(month);
  return `${name} ${year}`;
}

function formatCompactDateLabel(date: Date): string {
  const weekday = new Intl.DateTimeFormat("ro-RO", { weekday: "long" }).format(date);
  const day = date.getDate();
  const monthShort = ROMANIAN_MONTH_NAMES[date.getMonth()]?.slice(0, 3) ?? "";
  const capitalizedWeekday = weekday.charAt(0).toUpperCase() + weekday.slice(1);
  return `${capitalizedWeekday}, ${day} ${monthShort}`;
}

/** Short work zone label for Employee Mobile shell — falls back to „Producție”. */
export function employeeMobileWorkZoneLabel(role: string | null | undefined): string {
  if (!role || role === "employee" || role === "employee_mobile") return "Producție";
  if (role === "admin") return "Administrator";
  if (role === "manager") return "Manager";
  return role;
}

/** Employee Mobile header subtitle — e.g. „Producție · Vineri, 12 Iun”. */
export function formatOperationalPanelSubtitle(
  date = new Date(),
  role?: string | null,
): string {
  return `${employeeMobileWorkZoneLabel(role)} · ${formatCompactDateLabel(date)}`;
}
