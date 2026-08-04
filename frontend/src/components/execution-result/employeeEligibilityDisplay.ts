/**
 * Wave 4 — display-only mapping for Employee Eligibility Read Model (DEC-015).
 * Backend owns eligibility_status; this module only labels tones in Romanian.
 */
export type EligibilityTone = "success" | "warning" | "danger" | "neutral";

const STATUS_LABELS: Record<string, string> = {
  ready: "Candidat eligibil",
  ready_with_warnings: "Eligibil (cu atenționări)",
  blocked_no_matching_employee: "Niciun candidat eligibil",
  blocked_missing_requirements: "Regulă neconfigurată",
  blocked_missing_workcenter: "Workcenter înghețat lipsă",
  blocked_ambiguous_workcenter: "Workcenter ambiguu",
  blocked_not_materialized: "Taskuri operaționale lipsă",
  not_required: "Neaplicabil",
};

export function eligibilityStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

export function eligibilityStatusTone(status: string): EligibilityTone {
  if (status === "ready") return "success";
  if (status === "ready_with_warnings" || status === "not_required") return "warning";
  if (status.startsWith("blocked_")) return "danger";
  return "neutral";
}
