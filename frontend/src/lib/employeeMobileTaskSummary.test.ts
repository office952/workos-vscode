import { describe, expect, it } from "vitest";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  formatOrderLabel,
  groupTasksByOrder,
  isInstallationTask,
  pickBlockedTasks,
  pickHeroTask,
  pickInstallationTasks,
  pickTodayTasks,
  pickUpcomingTasks,
} from "@/lib/employeeMobileTaskSummary";

function task(partial: Partial<EmployeeMobileTaskDTO> & Pick<EmployeeMobileTaskDTO, "task_id" | "order_id" | "status">): EmployeeMobileTaskDTO {
  return {
    title: partial.title ?? partial.task_id,
    ...partial,
  };
}

describe("employeeMobileTaskSummary", () => {
  it("prioritizes in_progress over blocked and assigned for hero", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "assigned" }),
      task({ task_id: "T-2", order_id: 1, status: "blocked" }),
      task({ task_id: "T-3", order_id: 1, status: "in_progress" }),
    ];

    expect(pickHeroTask(tasks)).toEqual({
      task: tasks[2],
      mode: "working",
    });
  });

  it("prioritizes blocked over assigned when nothing is in progress", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "assigned" }),
      task({ task_id: "T-2", order_id: 1, status: "blocked", blocked_reason: "Material lipsă" }),
    ];

    expect(pickHeroTask(tasks)).toEqual({
      task: tasks[1],
      mode: "blocked",
    });
  });

  it("falls back to first assigned task as next", () => {
    const tasks = [task({ task_id: "T-001", order_id: 1, status: "assigned" })];

    expect(pickHeroTask(tasks)).toEqual({
      task: tasks[0],
      mode: "next",
    });
  });

  it("returns empty hero when no active tasks exist", () => {
    expect(pickHeroTask([task({ task_id: "T-1", order_id: 1, status: "done" })])).toEqual({
      task: null,
      mode: "empty",
    });
  });

  it("limits today tasks to active statuses", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "assigned" }),
      task({ task_id: "T-2", order_id: 1, status: "in_progress" }),
      task({ task_id: "T-3", order_id: 1, status: "done" }),
      task({ task_id: "T-4", order_id: 2, status: "blocked" }),
    ];

    expect(pickTodayTasks(tasks, 3).map((row) => row.task_id)).toEqual(["T-1", "T-2", "T-4"]);
  });

  it("collects blocked tasks separately", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "blocked" }),
      task({ task_id: "T-2", order_id: 1, status: "assigned" }),
    ];

    expect(pickBlockedTasks(tasks)).toEqual([tasks[0]]);
  });

  it("excludes hero assigned task from upcoming list", () => {
    const hero = task({ task_id: "T-001", order_id: 1, status: "assigned" });
    const tasks = [
      hero,
      task({ task_id: "T-002", order_id: 1, status: "assigned" }),
    ];

    expect(pickUpcomingTasks(tasks, hero)).toEqual([tasks[1]]);
  });

  it("groups active tasks by order without inventing client names", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "assigned", order_code: "ORD-1" }),
      task({ task_id: "T-2", order_id: 1, status: "done" }),
      task({ task_id: "T-3", order_id: 2, status: "in_progress" }),
    ];

    const grouped = groupTasksByOrder(tasks);
    expect(grouped).toHaveLength(2);
    expect(grouped[0].orderId).toBe(1);
    expect(grouped[0].activeCount).toBe(1);
    expect(grouped[0].doneCount).toBe(1);
    expect(formatOrderLabel(grouped[0])).toBe("ORD-1");
    expect(formatOrderLabel(grouped[1])).toBe("Comandă #2");
  });

  it("detects installation tasks conservatively from known keywords", () => {
    expect(
      isInstallationTask(
        task({
          task_id: "T-M",
          order_id: 1,
          status: "assigned",
          process_type: "field_installation",
        }),
      ),
    ).toBe(true);

    expect(
      isInstallationTask(
        task({
          task_id: "T-C",
          order_id: 1,
          status: "assigned",
          title: "Tăiere CNC",
        }),
      ),
    ).toBe(false);
  });

  it("returns only active installation tasks for scheduled section", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "assigned", title: "Montaj fațadă" }),
      task({ task_id: "T-2", order_id: 1, status: "done", title: "Montaj vechi" }),
    ];

    expect(pickInstallationTasks(tasks)).toEqual([tasks[0]]);
  });
});
