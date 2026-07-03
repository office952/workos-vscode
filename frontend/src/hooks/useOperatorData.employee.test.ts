import { describe, expect, it } from "vitest";

describe("useOperatorData performAction payload", () => {
  it("includes employee_id and operator_name when provided", () => {
    const payload: Record<string, unknown> = {
      order_id: 1,
      task_id: "T-001",
      action: "start",
    };
    const employeeId = 3;
    const operatorName = "Calin Cimpean";
    if (employeeId != null) payload.employee_id = employeeId;
    if (operatorName) payload.operator_name = operatorName;

    expect(payload).toEqual({
      order_id: 1,
      task_id: "T-001",
      action: "start",
      employee_id: 3,
      operator_name: "Calin Cimpean",
    });
    expect(payload).not.toHaveProperty("salary_amount");
  });
});
