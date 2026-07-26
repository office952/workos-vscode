import type { EmployeeMobileTaskError } from "@/api/employeeMobileTasks";

const ERROR_MESSAGES: Record<string, string> = {
  employee_link_missing:
    "Contul tău nu este legat de un profil de angajat. Contactează administratorul.",
  MOBILE_V2_TASK_ENVELOPE_MISSING:
    "Planul de execuție V2 nu conține taskuri operaționale. Contactează biroul.",
  MOBILE_V2_TASK_ENVELOPE_CORRUPT:
    "Datele taskurilor sunt corupte. Contactează biroul pentru remediere.",
  MOBILE_V2_TASK_CONTRACT_UNSUPPORTED:
    "Contractul de taskuri mobile nu este suportat pentru această comandă.",
  task_owned_by_other_employee: "Acest task aparține altui coleg.",
  task_not_accessible_to_employee: "Taskul nu este disponibil pentru tine.",
  production_release_blocked: "Producția este blocată — rezolvare pe desktop.",
  task_not_ready: "Taskul nu este încă pregătit.",
  order_not_found: "Comanda nu a fost găsită.",
  task_not_found: "Taskul nu a fost găsit.",
  invalid_task_state: "Starea taskului nu permite această acțiune.",
  network_error: "Nu am putut contacta serverul. Verifică conexiunea.",
};

export function mapMobileTaskErrorMessage(err: unknown): string {
  const error = err as EmployeeMobileTaskError;
  if (isNetworkError(err)) return ERROR_MESSAGES.network_error;
  const code = error?.code?.trim();
  if (code && ERROR_MESSAGES[code]) return ERROR_MESSAGES[code];
  if (error instanceof Error && error.message.trim()) return error.message.trim();
  return "Nu am putut încărca taskurile.";
}

export function isEmployeeLinkError(err: unknown): boolean {
  return (err as EmployeeMobileTaskError)?.code === "employee_link_missing";
}

export function isContractError(err: unknown): boolean {
  const code = (err as EmployeeMobileTaskError)?.code ?? "";
  return code.startsWith("MOBILE_V2_");
}

export function isNetworkError(err: unknown): boolean {
  const message = err instanceof Error ? err.message.toLowerCase() : "";
  return message.includes("failed to fetch") || message.includes("network");
}
