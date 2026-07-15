import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  startEmployeeMobileTask,
  startEmployeeMobileTaskFromAvailable,
  type EmployeeMobileTaskError,
} from "@/api/employeeMobileTasks";
import { mapMobileTaskErrorMessage } from "@/lib/employeeMobileV2TaskErrors";

export type EmployeeMobileStartMode = "assigned" | "available" | "none";

export interface EmployeeMobileStartResponse {
  status?: string;
  action?: string;
  task_id?: string;
  order_id?: number;
  timestamp?: string;
  already_started?: boolean;
}

const START_ERROR_MESSAGES: Record<string, string> = {
  production_release_blocked: "Producția este blocată — rezolvare pe desktop.",
  task_not_ready: "Taskul nu este încă pregătit.",
  task_owned_by_other_employee: "Acest task aparține altui coleg.",
  task_not_assigned_to_employee: "Taskul nu îți este atribuit.",
  task_already_started: "Taskul este deja în lucru.",
  task_already_completed: "Taskul este deja finalizat.",
  task_is_blocked: "Taskul este blocat manual.",
  task_has_active_session: "Un coleg lucrează deja la acest task.",
  task_already_assigned: "Taskul este deja preluat de alt coleg.",
  assignment_conflict: "Taskul a fost preluat de alt coleg.",
  employee_not_eligible: "Nu ești eligibil pentru acest task.",
  employee_link_missing: "Contul tău nu este legat de un profil de angajat.",
  order_not_found: "Comanda nu a fost găsită.",
  task_not_found: "Taskul nu a fost găsit.",
  invalid_task_state: "Starea taskului nu permite această acțiune.",
  task_not_claimable: "Taskul nu poate fi preluat acum.",
  network_error: "Nu am putut contacta serverul. Verifică conexiunea.",
};

export function employeeMobileStartTaskKey(task: Pick<EmployeeMobileTaskDTO, "order_id" | "task_id">): string {
  return `${task.order_id}:${task.task_id}`;
}

/** Backend capability only — no local readiness calculation. */
export function resolveEmployeeMobileStartMode(task: EmployeeMobileTaskDTO): EmployeeMobileStartMode {
  if (task.is_assigned_to_current_employee && task.can_start === true) {
    return "assigned";
  }
  if (task.is_available_for_claim && task.can_start_from_available === true) {
    return "available";
  }
  if (task.is_available_for_claim && task.can_start === true) {
    return "available";
  }
  return "none";
}

export function canShowAssignedStart(task: EmployeeMobileTaskDTO): boolean {
  return task.is_assigned_to_current_employee === true && task.can_start === true;
}

export function canShowAvailableStart(task: EmployeeMobileTaskDTO): boolean {
  return (
    task.is_available_for_claim === true &&
    (task.can_start_from_available === true || task.can_start === true)
  );
}

export function mapEmployeeMobileStartError(err: unknown): string {
  const error = err as EmployeeMobileTaskError;
  const code = String(error?.code ?? "").trim();
  if (code && START_ERROR_MESSAGES[code]) {
    return START_ERROR_MESSAGES[code];
  }
  if (error instanceof TypeError && error.message.toLowerCase().includes("failed to fetch")) {
    return START_ERROR_MESSAGES.network_error;
  }
  const mapped = mapMobileTaskErrorMessage(err);
  if (mapped && mapped !== "Nu am putut încărca taskurile.") {
    return mapped;
  }
  return error instanceof Error && error.message.trim()
    ? error.message.trim()
    : "Nu am putut porni taskul.";
}

export async function executeEmployeeMobileStart(
  task: EmployeeMobileTaskDTO,
): Promise<EmployeeMobileStartResponse> {
  const mode = resolveEmployeeMobileStartMode(task);
  if (mode === "none") {
    throw Object.assign(new Error("Taskul nu poate fi pornit."), { code: "task_not_ready" });
  }
  if (mode === "available") {
    return (await startEmployeeMobileTaskFromAvailable(
      task.task_id,
      task.order_id,
    )) as EmployeeMobileStartResponse;
  }
  return (await startEmployeeMobileTask(task.task_id, task.order_id)) as EmployeeMobileStartResponse;
}

export const ASSIGNED_START_LABEL = "Încep task";
export const AVAILABLE_START_LABEL = "Preia și pornește";
export const START_PENDING_LABEL = "Se pornește…";
