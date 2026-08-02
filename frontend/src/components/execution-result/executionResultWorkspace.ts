import type { AlertsResponse, ExecutionStatus, ObservabilityReport } from "@/api/execution";

export type ExecutionResultRole = "operator" | "manager" | "admin" | "other";

const REASONS: Record<string, string> = {
  within_thresholds: "În limitele de execuție",
  minutes_over_warning: "Durata depășește pragul de atenție",
  minutes_over_critical: "Durata depășește pragul critic",
  pct_over_warning: "Abaterea procentuală depășește pragul de atenție",
  pct_over_critical: "Abaterea procentuală depășește pragul critic",
  work_against_zero_plan: "Există lucru înregistrat fără plan",
  order_missing: "Comanda nu este disponibilă",
  plan_missing: "Planul de execuție lipsește",
  reality_missing: "Datele reale de execuție lipsesc",
  data_incomplete: "Datele necesare sunt incomplete",
  config_missing: "Configurația de monitorizare lipsește",
  config_inactive: "Configurația de monitorizare este inactivă",
  unclassified: "Starea nu poate fi clasificată încă",
};

export function executionResultRole(value: string | undefined): ExecutionResultRole {
  switch (value?.toLowerCase()) {
    case "operator":
      return "operator";
    case "manager":
      return "manager";
    case "admin":
      return "admin";
    default:
      return "other";
  }
}

export function isManagementRole(role: ExecutionResultRole): boolean {
  return role === "admin" || role === "manager";
}

export function formatMinutes(value: number | null | undefined): string {
  return value == null ? "—" : `${value.toFixed(1)} min`;
}

export function formatMoney(value: unknown, currency?: unknown): string {
  return typeof value === "number" ? `${value} ${typeof currency === "string" ? currency : ""}`.trim() : "Indisponibil";
}

export function humanReason(code: string): string {
  return REASONS[code] ?? "Este necesară verificarea datelor de execuție";
}

export function statusLabel(status: ExecutionStatus): string {
  switch (status) {
    case "OK":
      return "În limite";
    case "WARNING":
      return "Atenție";
    case "CRITICAL":
      return "Critic";
    case "UNCONFIRMED":
      return "Neconfirmat";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

export function blockersFor(
  observability: ObservabilityReport,
  alerts: AlertsResponse | null,
): string[] {
  const blockers = [...observability.reasons];
  if (!observability.has_plan) blockers.push("plan_missing");
  if (!observability.has_reality) blockers.push("reality_missing");
  if (alerts) blockers.push(...alerts.alerts.map((alert) => alert.reason));
  return [...new Set(blockers)];
}
