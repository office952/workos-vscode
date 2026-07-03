import { describe, expect, it } from "vitest";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  resolveEmployeeMobileV2Task,
  isEmployeeMobileV2TaskPreview,
} from "./resolveEmployeeMobileV2Task";

function task(
  partial: Partial<EmployeeMobileTaskDTO> & Pick<EmployeeMobileTaskDTO, "task_id" | "order_id">,
): EmployeeMobileTaskDTO {
  return {
    status: "assigned",
    ...partial,
  };
}

describe("resolveEmployeeMobileV2Task", () => {
  const myTasks = [
    task({
      task_id: "T-003",
      order_id: 99904,
      order_code: "ORD-99904",
      title: "Colantare fețe litere vechi",
      instructions: "nu pe cant",
    }),
  ];

  const availableTasks = [
    task({
      task_id: "T-003",
      order_id: 99905,
      order_code: "ORD-99905",
      title: "Colantare fețe litere",
      instructions: "Colantezi fețele din plexiglas",
      claimable: true,
      access_mode: "available_preview",
      preview_only: true,
    }),
  ];

  it("resolves exact orderId + taskId from available tasks, not my tasks", () => {
    const resolved = resolveEmployeeMobileV2Task({
      taskId: "T-003",
      orderId: 99905,
      myTasks,
      availableTasks,
    });
    expect(resolved?.order_id).toBe(99905);
    expect(resolved?.instructions).toContain("Colantezi fețele");
  });

  it("does not fall back to another order when orderId is set", () => {
    const resolved = resolveEmployeeMobileV2Task({
      taskId: "T-003",
      orderId: 99905,
      myTasks,
      availableTasks: [],
    });
    expect(resolved).toBeNull();
  });

  it("falls back to first matching taskId when orderId is absent", () => {
    const resolved = resolveEmployeeMobileV2Task({
      taskId: "T-003",
      orderId: null,
      myTasks,
      availableTasks,
    });
    expect(resolved?.order_id).toBe(99904);
  });

  it("detects preview-only available tasks", () => {
    const resolved = resolveEmployeeMobileV2Task({
      taskId: "T-003",
      orderId: 99905,
      myTasks: [],
      availableTasks,
    });
    expect(isEmployeeMobileV2TaskPreview(resolved)).toBe(true);
  });
});
