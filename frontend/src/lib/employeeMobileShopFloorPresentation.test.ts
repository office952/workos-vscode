import { describe, expect, it } from "vitest";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileOrderBlueprintTask } from "@/api/employeeMobileOrderBlueprint";
import {
  buildHomeBriefLines,
  buildRecommendationReason,
  buildWaitingBriefText,
  composeBlockedReason,
  sortTasksOperational,
} from "@/lib/employeeMobileShopFloorPresentation";

const inProgressTask: EmployeeMobileTaskDTO = {
  task_id: "T-004",
  order_id: 1,
  title: "Lipire canturi pe fețele literelor",
  status: "in_progress",
};

const waitingTask: EmployeeMobileTaskDTO = {
  task_id: "T-006",
  order_id: 1,
  title: "Montaj LED",
  status: "assigned",
  readiness_status: "waiting_predecessor",
  blocking_tasks: [{ task_id: "T-005", name: "Debitare spate Forex" }],
};

const upcomingTask: EmployeeMobileTaskDTO = {
  task_id: "T-007",
  order_id: 1,
  title: "Pregătire montaj / bare / șablon",
  status: "assigned",
  is_startable: false,
};

const blueprintTasks: EmployeeMobileOrderBlueprintTask[] = [
  {
    task_id: "T-004",
    name: "Lipire canturi pe fețele literelor",
    status_display: "În lucru",
    is_mine: true,
    is_current: true,
    stage_label: "Asamblare",
    has_documents: true,
    has_instructions: true,
    readiness_status: "in_progress",
  },
  {
    task_id: "T-006",
    name: "Montaj LED",
    status_display: "Alocat",
    is_mine: true,
    is_current: false,
    stage_label: "Asamblare",
    has_documents: false,
    has_instructions: false,
    readiness_status: "waiting_predecessor",
    readiness_label: "Așteaptă task anterior",
    blocking_tasks: [{ task_id: "T-005", name: "Debitare spate Forex" }],
  },
  {
    task_id: "T-007",
    name: "Pregătire montaj / bare / șablon",
    status_display: "Alocat",
    is_mine: true,
    is_current: false,
    stage_label: "Asamblare",
    has_documents: false,
    has_instructions: false,
    readiness_status: "eligible",
  },
];

describe("employeeMobileShopFloorPresentation home brief", () => {
  it("builds continue, waiting and upcoming lines from real task data", () => {
    const lines = buildHomeBriefLines({
      personalTasks: [inProgressTask, waitingTask, upcomingTask],
      blueprintTasks,
      heroTask: inProgressTask,
      primaryOrderId: 1,
      currentTaskId: "T-004",
    });

    expect(lines.map((line) => line.kind)).toEqual(["continue", "waiting", "upcoming"]);
    expect(lines[0]?.text).toContain("Lipire canturi");
    expect(lines[1]?.text).toContain("Montaj LED");
    expect(lines[1]?.text).toContain("Debitare spate Forex");
    expect(lines[2]?.text).toContain("Pregătire montaj");
  });

  it("omits waiting and upcoming lines when no matching tasks exist", () => {
    const lines = buildHomeBriefLines({
      personalTasks: [inProgressTask],
      blueprintTasks: [blueprintTasks[0]!],
      heroTask: inProgressTask,
      primaryOrderId: 1,
      currentTaskId: "T-004",
    });

    expect(lines).toEqual([
      expect.objectContaining({ kind: "continue", label: "Continui" }),
    ]);
  });

  it("builds waiting brief text from blocking task names", () => {
    expect(buildWaitingBriefText(waitingTask)).toContain("Debitare spate Forex");
  });

  it("builds recommendation reason without inventing client names", () => {
    expect(buildRecommendationReason({ personalTask: inProgressTask })).toBe(
      "Taskul tău activ acum.",
    );
  });

  it("sorts operational tasks by execution priority", () => {
    const sorted = sortTasksOperational([upcomingTask, waitingTask, inProgressTask]);
    expect(sorted.map((task) => task.task_id)).toEqual(["T-004", "T-006", "T-007"]);
  });

  it("composes blocked reason with predefined category", () => {
    expect(composeBlockedReason("material", "Lipsește cantul pentru litera R")).toBe(
      "[Material] Lipsește cantul pentru litera R",
    );
  });
});
