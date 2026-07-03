import { describe, expect, it } from "vitest";
import type { EmployeeMobileOrderBlueprintTask } from "@/api/employeeMobileOrderBlueprint";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  buildPipelineTaskPresentation,
  buildPersonalTasksById,
  resolvePipelineCurrentTaskId,
} from "@/lib/employeeMobilePipelineEligibility";

function blueprintTask(
  partial: Partial<EmployeeMobileOrderBlueprintTask> &
    Pick<EmployeeMobileOrderBlueprintTask, "task_id" | "is_mine">,
): EmployeeMobileOrderBlueprintTask {
  return {
    name: partial.task_id,
    status_display: "Neatribuit",
    is_current: false,
    stage_label: "Execuție",
    has_documents: false,
    has_instructions: false,
    readiness_status: "",
    readiness_label: "",
    is_startable: false,
    ...partial,
  };
}

function personalTask(
  partial: Partial<EmployeeMobileTaskDTO> &
    Pick<EmployeeMobileTaskDTO, "task_id" | "order_id" | "status">,
): EmployeeMobileTaskDTO {
  return { title: partial.task_id, ...partial };
}

describe("employeeMobilePipelineEligibility", () => {
  it("marks in_progress mine task as current", () => {
    const tasks = [
      blueprintTask({
        task_id: "T-004",
        is_mine: true,
        readiness_status: "in_progress",
      }),
      blueprintTask({ task_id: "T-006", is_mine: true }),
    ];
    const personal = buildPersonalTasksById([
      personalTask({ task_id: "T-004", order_id: 1, status: "in_progress" }),
    ]);
    expect(resolvePipelineCurrentTaskId(tasks, personal)).toBe("T-004");
  });

  it("shows waiting predecessor instead of Acum for blocked deps", () => {
    const tasks = [
      blueprintTask({
        task_id: "T-006",
        is_mine: true,
        readiness_status: "waiting_predecessor",
        readiness_label: "Așteaptă task anterior",
        is_startable: false,
        blocking_tasks: [{ task_id: "T-005", name: "Debitare spate Forex" }],
      }),
    ];
    const personal = buildPersonalTasksById([
      personalTask({ task_id: "T-006", order_id: 1, status: "assigned" }),
    ]);
    const currentId = resolvePipelineCurrentTaskId(tasks, personal);
    expect(currentId).toBeNull();
    const presentation = buildPipelineTaskPresentation(tasks[0], 0, currentId, personal);
    expect(presentation.markerLabel).toBe("Așteaptă task anterior");
    expect(presentation.blockingTasks[0]?.name).toContain("Forex");
    expect(presentation.showStartButton).toBe(false);
  });

  it("marks first startable mine task as current when none in progress", () => {
    const tasks = [
      blueprintTask({
        task_id: "T-008",
        is_mine: true,
        readiness_status: "eligible",
        is_startable: true,
      }),
      blueprintTask({
        task_id: "T-006",
        is_mine: true,
        readiness_status: "waiting_predecessor",
        is_startable: false,
      }),
    ];
    const personal = buildPersonalTasksById([
      personalTask({ task_id: "T-008", order_id: 1, status: "assigned" }),
      personalTask({ task_id: "T-006", order_id: 1, status: "assigned" }),
    ]);
    const currentId = resolvePipelineCurrentTaskId(tasks, personal);
    expect(currentId).toBe("T-008");
  });

  it("shows dependency warning on in_progress task with missing predecessor", () => {
    const tasks = [
      blueprintTask({
        task_id: "T-004",
        is_mine: true,
        readiness_status: "in_progress",
        dependency_warning: "A pornit înainte de finalizarea dependențelor",
        blocking_tasks: [{ task_id: "T-003", name: "Modelare canturi litere volumetrice" }],
      }),
    ];
    const personal = buildPersonalTasksById([
      personalTask({ task_id: "T-004", order_id: 1, status: "in_progress" }),
    ]);
    const presentation = buildPipelineTaskPresentation(tasks[0], 3, "T-004", personal);
    expect(presentation.markerLabel).toBe("Acum");
    expect(presentation.dependencyWarning).toContain("dependențelor");
    expect(presentation.blockingTasks[0]?.task_id).toBe("T-003");
  });

  it("shows non-mine contextual labels without employee names", () => {
    const tasks = [blueprintTask({ task_id: "T-003", is_mine: false, status_display: "Neatribuit" })];
    const personal = buildPersonalTasksById([]);
    const presentation = buildPipelineTaskPresentation(tasks[0], 0, null, personal);
    expect(presentation.markerLabel).toBe("Alt post");
    expect(presentation.mineLabel).toBeNull();
  });
});
