import { describe, expect, it } from "vitest";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  buildEmployeeMobileTaskDetailPath,
  buildEmployeeMobileTasksPath,
  filterTasksForView,
  filterTodayActionableTasks,
  parseEmployeeMobileTaskView,
  summarizeEmployeeMobileTaskCounts,
} from "@/lib/employeeMobileTaskViews";

function task(partial: Partial<EmployeeMobileTaskDTO> & Pick<EmployeeMobileTaskDTO, "task_id" | "order_id" | "status">): EmployeeMobileTaskDTO {
  return { title: partial.task_id, ...partial };
}

describe("employeeMobileTaskViews", () => {
  it("parses known views and falls back to today", () => {
    expect(parseEmployeeMobileTaskView("blocked")).toBe("blocked");
    expect(parseEmployeeMobileTaskView("unknown")).toBe("today");
    expect(parseEmployeeMobileTaskView(null)).toBe("today");
  });

  it("builds task paths with view and order filters", () => {
    expect(buildEmployeeMobileTasksPath("today")).toBe("/employee-app/tasks");
    expect(buildEmployeeMobileTasksPath("pipeline")).toBe("/employee-app/tasks?view=pipeline");
    expect(buildEmployeeMobileTasksPath("all")).toBe("/employee-app/tasks?view=all");
    expect(buildEmployeeMobileTasksPath("orders")).toBe("/employee-app/tasks?view=orders");
    expect(buildEmployeeMobileTasksPath("orders", 1)).toBe(
      "/employee-app/tasks?view=orders&orderId=1",
    );
  });

  it("summarizes task counts", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "assigned" }),
      task({ task_id: "T-2", order_id: 1, status: "in_progress" }),
      task({ task_id: "T-3", order_id: 1, status: "blocked" }),
      task({ task_id: "T-4", order_id: 1, status: "done" }),
    ];
    expect(summarizeEmployeeMobileTaskCounts(tasks)).toEqual({
      active: 3,
      assigned: 1,
      inProgress: 1,
      blocked: 1,
      done: 1,
      total: 4,
    });
  });

  it("filters blocked and upcoming views", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "assigned" }),
      task({ task_id: "T-2", order_id: 1, status: "blocked" }),
    ];
    expect(filterTasksForView(tasks, "blocked")).toEqual([tasks[1]]);
    expect(filterTasksForView(tasks, "upcoming")).toEqual([tasks[0]]);
  });

  it("filters tasks by order when orderId is set", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "assigned" }),
      task({ task_id: "T-2", order_id: 2, status: "assigned" }),
    ];
    expect(filterTasksForView(tasks, "orders", 1)).toEqual([tasks[0]]);
  });

  it("filters today actionable tasks without waiting predecessors", () => {
    const tasks = [
      task({ task_id: "T-1", order_id: 1, status: "in_progress" }),
      task({ task_id: "T-2", order_id: 1, status: "assigned", is_startable: true }),
      task({ task_id: "T-3", order_id: 1, status: "assigned", is_startable: false }),
      task({ task_id: "T-4", order_id: 1, status: "blocked" }),
      task({ task_id: "T-5", order_id: 1, status: "done" }),
    ];
    expect(filterTodayActionableTasks(tasks).map((row) => row.task_id)).toEqual([
      "T-1",
      "T-2",
      "T-4",
    ]);
  });

  it("builds task detail deep link", () => {
    expect(
      buildEmployeeMobileTaskDetailPath({ task_id: "T-1", order_id: 9 }, "today"),
    ).toBe("/employee-app/tasks?taskId=T-1&orderId=9");
  });
});
