import { describe, expect, it } from "vitest";
import type { OperationResourceMapping, RegistryEmployee } from "@/api/operationalRegistry";
import type { OperatorTask } from "@/lib/mockData";
import { computeEligibility, listEligibleEmployees } from "@/features/operational-registry/operationEligibility";

const baseEmployee: RegistryEmployee = {
  id: 1,
  name: "Calin Cimpean",
  role: "Operator",
  department: "Atelier",
  status: "active",
  employee_type: "productive",
  user_id: null,
  salary_amount: 8500,
  salary_currency: "RON",
  salary_period: "monthly",
  skill_codes: ["SK_PRINT_OPERATOR"],
  workcenter_codes: ["WC_PRINT"],
  resource_codes: ["MCH-EPSON-60800"],
};

const task: OperatorTask = {
  id: "T-001",
  jobId: "JOB-0001",
  client: "Client",
  product: "Produs",
  operationCode: "print",
  operationName: "Print",
  machineName: "printer_large_format",
  status: "assigned",
  assignee: "—",
  plannedDurationMin: 30,
  actualDurationMin: null,
  startedAt: null,
  targetEndAt: null,
  instructions: "",
  inputDependencies: [],
  expectedOutput: "",
  sequenceIndex: 1,
};

const mapping: OperationResourceMapping = {
  operation_code: "print",
  required_skill_codes: ["SK_PRINT_OPERATOR"],
  allowed_workcenter_codes: ["WC_PRINT"],
  allowed_resource_codes: ["MCH-EPSON-60800"],
  authorization_mode: "hybrid",
  default_resource_code: "MCH-EPSON-60800",
  product_system_aliases: [],
  authorized_employee_ids: [1, 2],
  notes: null,
};

describe("operationEligibility hybrid", () => {
  it("authorizes employee on explicit list even without skill match in explicit mode", () => {
    const other: RegistryEmployee = {
      ...baseEmployee,
      id: 99,
      skill_codes: [],
      workcenter_codes: [],
      resource_codes: [],
    };
    const explicitMapping: OperationResourceMapping = {
      ...mapping,
      authorization_mode: "explicit",
    };
    expect(computeEligibility(baseEmployee, task, explicitMapping)).toBe("authorized");
    expect(computeEligibility(other, task, explicitMapping)).toBe("not_authorized");
  });

  it("hybrid allows skill match or explicit override", () => {
    const octavian: RegistryEmployee = { ...baseEmployee, id: 2, name: "Octavian" };
    expect(computeEligibility(baseEmployee, task, mapping)).toBe("authorized");
    expect(computeEligibility(octavian, task, mapping)).toBe("authorized");
  });

  it("listEligibleEmployees returns multiple authorized employees", () => {
    const pool = listEligibleEmployees(
      [baseEmployee, { ...baseEmployee, id: 2, name: "Octavian" }],
      task,
      mapping
    );
    expect(pool).toHaveLength(2);
  });

  it("listEligibleEmployees excludes inactive even when explicit authorized", () => {
    const inactiveExplicit: RegistryEmployee = {
      ...baseEmployee,
      id: 2,
      name: "Inactive Explicit",
      status: "inactive",
    };
    const pool = listEligibleEmployees([baseEmployee, inactiveExplicit], task, mapping);
    expect(pool.map((e) => e.id)).toEqual([1]);
  });
});
