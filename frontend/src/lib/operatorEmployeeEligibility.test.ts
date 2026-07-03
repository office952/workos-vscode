import { describe, expect, it } from "vitest";
import type { RegistryEmployee } from "@/api/operationalRegistry";
import type { OperatorTask } from "@/lib/mockData";
import {
  computeEligibility,
  listActiveRegistryEmployees,
  toOperatorEmployeeOption,
} from "@/lib/operatorEmployeeEligibility";

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

describe("operatorEmployeeEligibility", () => {
  it("marks employee authorized when skills match mapping", () => {
    const status = computeEligibility(baseEmployee, task, {
      operation_code: "print",
      required_skill_codes: ["SK_PRINT_OPERATOR"],
      allowed_workcenter_codes: ["WC_PRINT"],
      allowed_resource_codes: ["MCH-EPSON-60800"],
      authorization_mode: "hybrid",
      default_resource_code: null,
      product_system_aliases: [],
      authorized_employee_ids: [],
      notes: null,
    });
    expect(status).toBe("authorized");
  });

  it("returns unverified when mapping missing", () => {
    expect(computeEligibility(baseEmployee, task, null)).toBe("unverified");
  });

  it("toOperatorEmployeeOption never exposes salary fields", () => {
    const option = toOperatorEmployeeOption(baseEmployee, task, null);
    expect(option.name).toBe("Calin Cimpean");
    expect(option).not.toHaveProperty("salary_amount");
    expect(option).not.toHaveProperty("salary_currency");
  });

  it("listActiveRegistryEmployees filters inactive", () => {
    const items = listActiveRegistryEmployees([
      baseEmployee,
      { ...baseEmployee, id: 2, name: "Inactiv", status: "inactive" },
    ]);
    expect(items).toHaveLength(1);
    expect(items[0].name).toBe("Calin Cimpean");
  });
});
