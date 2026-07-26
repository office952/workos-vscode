import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  completeEmployeeMobileTask,
  type EmployeeMobileTaskError,
} from "@/api/employeeMobileTasks";
import { mapMobileTaskErrorMessage } from "@/lib/employeeMobileV2TaskErrors";
import { employeeMobileStartTaskKey } from "@/lib/employeeMobileV2StartAction";

export interface EmployeeMobileCompleteResponse {
  status?: string;
  action?: string;
  task_id?: string;
  order_id?: number;
  timestamp?: string;
  already_completed?: boolean;
}

const RUNTIME_ERROR_MESSAGES: Record<string, string> = {
  task_not_started: "Taskul nu este pornit — nu există sesiune activă.",
  task_not_in_progress: "Taskul nu este în lucru.",
  active_session_missing: "Nu există sesiune activă pentru acest task.",
  task_is_blocked: "Taskul este blocat — deblochează înainte de finalizare.",
  task_is_paused: "Taskul este întrerupt — reia lucrul înainte de finalizare.",
  task_already_completed: "Taskul este deja finalizat.",
  task_not_assigned_to_employee: "Taskul nu îți este atribuit.",
  task_owned_by_other_employee: "Acest task aparține altui coleg.",
  task_not_found: "Taskul nu a fost găsit.",
  order_not_found: "Comanda nu a fost găsită.",
  employee_link_missing: "Contul tău nu este legat de un profil de angajat.",
  invalid_task_state: "Starea taskului nu permite această acțiune.",
  network_error: "Nu am putut contacta serverul. Verifică conexiunea.",
};

export function employeeMobileRuntimeTaskKey(
  task: Pick<EmployeeMobileTaskDTO, "order_id" | "task_id">,
): string {
  return employeeMobileStartTaskKey(task);
}

/** Backend capability only — not status string alone. */
export function canShowComplete(task: EmployeeMobileTaskDTO): boolean {
  return task.can_complete === true;
}

export function mapEmployeeMobileRuntimeError(err: unknown): string {
  const error = err as EmployeeMobileTaskError;
  const code = String(error?.code ?? "").trim();
  if (code && RUNTIME_ERROR_MESSAGES[code]) {
    return RUNTIME_ERROR_MESSAGES[code];
  }
  if (error instanceof TypeError && error.message.toLowerCase().includes("failed to fetch")) {
    return RUNTIME_ERROR_MESSAGES.network_error;
  }
  const mapped = mapMobileTaskErrorMessage(err);
  if (mapped && mapped !== "Nu am putut încărca taskurile.") {
    return mapped;
  }
  return error instanceof Error && error.message.trim()
    ? error.message.trim()
    : "Nu am putut finaliza taskul.";
}

export async function executeEmployeeMobileComplete(
  task: EmployeeMobileTaskDTO,
): Promise<EmployeeMobileCompleteResponse> {
  if (!canShowComplete(task)) {
    throw Object.assign(new Error("Taskul nu poate fi finalizat acum."), {
      code: "task_not_in_progress",
    });
  }
  return (await completeEmployeeMobileTask(
    task.task_id,
    task.order_id,
  )) as EmployeeMobileCompleteResponse;
}

export const COMPLETE_LABEL = "Finalizez";
export const COMPLETE_PENDING_LABEL = "Se finalizează…";
