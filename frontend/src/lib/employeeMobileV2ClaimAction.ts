import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  claimEmployeeMobileTask,
  type EmployeeMobileClaimResult,
  type EmployeeMobileTaskError,
} from "@/api/employeeMobileTasks";
import { mapMobileTaskErrorMessage } from "@/lib/employeeMobileV2TaskErrors";
import { canShowAvailableStart } from "@/lib/employeeMobileV2StartAction";

const CLAIM_ERROR_MESSAGES: Record<string, string> = {
  task_already_assigned: "Taskul este deja preluat de alt coleg.",
  assignment_conflict: "Taskul a fost preluat de alt coleg.",
  task_not_claimable: "Taskul nu poate fi preluat acum.",
  employee_not_eligible: "Nu ești eligibil pentru acest task.",
  task_has_active_session: "Un coleg lucrează deja la acest task.",
  network_error: "Nu am putut contacta serverul. Verifică conexiunea.",
};

export const CLAIM_ONLY_LABEL = "Preiau sarcina";
export const CLAIM_PENDING_LABEL = "Se preia…";

export function employeeMobileClaimTaskKey(
  task: Pick<EmployeeMobileTaskDTO, "order_id" | "task_id">,
): string {
  return `${task.order_id}:${task.task_id}`;
}

/** Secondary claim-only — primary start-from-available takes precedence when both are allowed. */
export function canShowClaimOnly(task: EmployeeMobileTaskDTO): boolean {
  return (
    task.is_available_for_claim === true &&
    Boolean(task.can_claim ?? task.claimable) &&
    !canShowAvailableStart(task)
  );
}

export function mapEmployeeMobileClaimError(err: unknown): string {
  const error = err as EmployeeMobileTaskError;
  const code = String(error?.code ?? "").trim();
  if (code && CLAIM_ERROR_MESSAGES[code]) {
    return CLAIM_ERROR_MESSAGES[code];
  }
  if (error instanceof TypeError && error.message.toLowerCase().includes("failed to fetch")) {
    return CLAIM_ERROR_MESSAGES.network_error;
  }
  const mapped = mapMobileTaskErrorMessage(err);
  if (mapped && mapped !== "Nu am putut încărca taskurile.") {
    return mapped;
  }
  return "Nu am putut prelua taskul.";
}

export async function executeEmployeeMobileClaim(
  task: EmployeeMobileTaskDTO,
): Promise<EmployeeMobileClaimResult> {
  return claimEmployeeMobileTask(task.task_id, task.order_id);
}
