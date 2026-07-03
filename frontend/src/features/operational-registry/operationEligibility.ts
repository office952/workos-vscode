/**
 * Hybrid operation eligibility — mirrors backend registry rules.
 */
import type { OperationResourceMapping, RegistryEmployee } from "@/api/operationalRegistry";
import type { OperatorTask } from "@/lib/mockData";

export type EmployeeEligibilityStatus = "authorized" | "not_authorized" | "unverified";

function employeeMatchesSkillRules(
  emp: RegistryEmployee,
  mapping: OperationResourceMapping,
  task: OperatorTask | null
): boolean {
  const requiredSkills = new Set(mapping.required_skill_codes ?? []);
  const allowedWorkcenters = new Set(mapping.allowed_workcenter_codes ?? []);
  const allowedResources = new Set(mapping.allowed_resource_codes ?? []);

  if (requiredSkills.size === 0 && allowedWorkcenters.size === 0 && allowedResources.size === 0) {
    return false;
  }

  const skillOk =
    requiredSkills.size === 0 || emp.skill_codes.some((s) => requiredSkills.has(s));
  const wcOk =
    allowedWorkcenters.size === 0 ||
    emp.workcenter_codes.some((w) => allowedWorkcenters.has(w));
  const machineSlug = (task?.machineName || "").toLowerCase().replace(/\s+/g, "_");
  const resourceOk =
    allowedResources.size === 0 ||
    emp.resource_codes.some(
      (r) =>
        allowedResources.has(r) ||
        r.toLowerCase().includes(machineSlug) ||
        machineSlug.includes(r.toLowerCase())
    );

  return skillOk && wcOk && resourceOk;
}

export function computeEligibility(
  emp: RegistryEmployee,
  task: OperatorTask | null,
  mapping: OperationResourceMapping | null
): EmployeeEligibilityStatus {
  if (!mapping) return "unverified";

  const mode = (mapping.authorization_mode || "hybrid").toLowerCase();
  const explicitIds = new Set(mapping.authorized_employee_ids ?? []);
  const skillMatch = employeeMatchesSkillRules(emp, mapping, task);

  if (mode === "explicit") {
    return explicitIds.has(emp.id) ? "authorized" : "not_authorized";
  }
  if (mode === "skill") {
    return skillMatch ? "authorized" : "not_authorized";
  }

  if (explicitIds.size > 0) {
    return explicitIds.has(emp.id) || skillMatch ? "authorized" : "not_authorized";
  }
  return skillMatch ? "authorized" : "not_authorized";
}

export function listEligibleEmployees(
  employees: RegistryEmployee[],
  task: OperatorTask | null,
  mapping: OperationResourceMapping | null
): RegistryEmployee[] {
  return employees.filter(
    (emp) => emp.status === "active" && computeEligibility(emp, task, mapping) === "authorized"
  );
}
