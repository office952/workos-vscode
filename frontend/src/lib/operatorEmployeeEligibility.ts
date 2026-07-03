/**
 * Operator employee eligibility helpers — no salary exposure.
 */
import type { OperationResourceMapping, RegistryEmployee } from "@/api/operationalRegistry";
import type { OperatorTask } from "@/lib/mockData";
import {
  computeEligibility,
  listEligibleEmployees,
  type EmployeeEligibilityStatus,
} from "@/features/operational-registry/operationEligibility";

export type { EmployeeEligibilityStatus };

export interface OperatorEmployeeOption {
  id: number;
  name: string;
  role: string | null;
  skillCodes: string[];
  workcenterCodes: string[];
  resourceCodes: string[];
  eligibility: EmployeeEligibilityStatus;
  eligibilityLabel: string;
}

const ELIGIBILITY_LABELS: Record<EmployeeEligibilityStatus, string> = {
  authorized: "Autorizat",
  not_authorized: "Neautorizat pentru operație",
  unverified: "Eligibilitate neconfirmată",
};

export function toOperatorEmployeeOption(
  emp: RegistryEmployee,
  task: OperatorTask | null,
  mapping: OperationResourceMapping | null
): OperatorEmployeeOption {
  const eligibility = computeEligibility(emp, task, mapping);
  return {
    id: emp.id,
    name: emp.name,
    role: emp.role,
    skillCodes: emp.skill_codes,
    workcenterCodes: emp.workcenter_codes,
    resourceCodes: emp.resource_codes,
    eligibility,
    eligibilityLabel: ELIGIBILITY_LABELS[eligibility],
  };
}

export { computeEligibility, listEligibleEmployees };

export function listActiveRegistryEmployees(items: RegistryEmployee[]): RegistryEmployee[] {
  return items.filter((e) => e.status === "active");
}
