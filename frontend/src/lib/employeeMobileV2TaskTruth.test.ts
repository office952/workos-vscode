import { describe, expect, it } from "vitest";
import {
  buildEmployeeMobileV2TaskTruthView,
  resolveTaskComponentLine,
  resolveTaskDisplayTitle,
  truthTaskToDto,
} from "@/lib/employeeMobileV2TaskTruth";
import { flatTaskToTruthNested } from "@/components/workos/employee-mobile-v2/EmployeeMobileV2TaskTruthPanels";

describe("employeeMobileV2TaskTruth", () => {
  it("partitions assigned and available from backend flags only", () => {
    const assigned = flatTaskToTruthNested({
      task_id: "node:root:op1",
      order_id: 23099,
      status: "assigned",
      display_label: "Vector Prep",
      component_label: "Produs principal",
      component_role: "root_product",
      is_assigned_to_current_employee: true,
      is_available_for_claim: false,
    });
    const available = flatTaskToTruthNested({
      task_id: "node:mounting:op2",
      order_id: 23099,
      status: "assigned",
      display_label: "Montaj panou",
      component_label: "Panou montaj",
      component_role: "mounting_panel",
      is_assigned_to_current_employee: false,
      is_available_for_claim: true,
      can_claim: true,
    });
    const view = buildEmployeeMobileV2TaskTruthView({
      contract_version: "employee_mobile_task_truth/v1",
      employee_id: 4,
      generated_at: "2026-07-15T00:00:00Z",
      tasks: [assigned, available],
      summary: {
        total_tasks: 2,
        assigned_count: 1,
        available_count: 1,
        startable_count: 0,
        blocked_count: 0,
      },
    });
    expect(view.assignedTasks).toHaveLength(1);
    expect(view.availableTasks).toHaveLength(1);
    expect(view.assignedTasks[0].task_id).toBe("node:root:op1");
    expect(view.availableTasks[0].task_id).toBe("node:mounting:op2");
  });

  it("renders root and logo identity from backend labels", () => {
    const root = truthTaskToDto(
      flatTaskToTruthNested({
        task_id: "node:root_product:TPL:vector_prep",
        order_id: 1,
        status: "assigned",
        display_label: "Vector Prep",
        component_label: "Produs principal",
        component_role: "root_product",
      }),
      "employee_mobile_task_truth/v1",
    );
    expect(resolveTaskDisplayTitle(root)).toBe("Vector Prep");
    expect(resolveTaskComponentLine(root)).toBe("Produs principal");

    const logo = truthTaskToDto(
      flatTaskToTruthNested({
        task_id: "node:logo:logo_instance_001:cut",
        order_id: 1,
        status: "assigned",
        display_label: "Tăiere logo",
        component_label: "Logo",
        component_role: "logo_segment",
        logo_segment_label: "Logo segment (logo_instance_001)",
      }),
      "employee_mobile_task_truth/v1",
    );
    expect(resolveTaskDisplayTitle(logo)).toBe("Tăiere logo");
    expect(resolveTaskComponentLine(logo)).toBe("Logo segment (logo_instance_001)");
    expect(resolveTaskDisplayTitle(logo)).not.toContain("logo_instance_001");
  });
});
