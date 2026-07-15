import { describe, expect, it, vi, beforeEach } from "vitest";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  canShowComplete,
  executeEmployeeMobileComplete,
  mapEmployeeMobileRuntimeError,
} from "@/lib/employeeMobileV2RuntimeAction";
import { RUNTIME_FIXTURE_TASKS } from "@/lib/employeeMobileV2RuntimeFixtures";

vi.mock("@/api/employeeMobileTasks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/employeeMobileTasks")>();
  return {
    ...actual,
    completeEmployeeMobileTask: vi.fn(),
  };
});

import { completeEmployeeMobileTask } from "@/api/employeeMobileTasks";

describe("employeeMobileV2RuntimeAction", () => {
  beforeEach(() => {
    vi.mocked(completeEmployeeMobileTask).mockReset();
  });

  it("shows complete only when can_complete is true", () => {
    expect(canShowComplete(RUNTIME_FIXTURE_TASKS.inProgress)).toBe(true);
    expect(canShowComplete({ ...RUNTIME_FIXTURE_TASKS.inProgress, can_complete: false })).toBe(false);
    expect(
      canShowComplete({ ...RUNTIME_FIXTURE_TASKS.inProgress, status: "in_progress", can_complete: undefined }),
    ).toBe(false);
  });

  it("calls complete endpoint with order_id only", async () => {
    vi.mocked(completeEmployeeMobileTask).mockResolvedValue({
      status: "ok",
      action: "complete",
      task_id: "fixture-start-ready",
    });
    await executeEmployeeMobileComplete(RUNTIME_FIXTURE_TASKS.inProgress);
    expect(completeEmployeeMobileTask).toHaveBeenCalledWith("fixture-runtime-in-progress", 23099);
  });

  it("rejects complete when backend capability is false", async () => {
    await expect(executeEmployeeMobileComplete(RUNTIME_FIXTURE_TASKS.noSession)).rejects.toMatchObject({
      code: "task_not_in_progress",
    });
    expect(completeEmployeeMobileTask).not.toHaveBeenCalled();
  });

  it("maps structured runtime errors", () => {
    expect(mapEmployeeMobileRuntimeError({ code: "task_not_started", message: "x" })).toMatch(
      /sesiune activă/i,
    );
    expect(mapEmployeeMobileRuntimeError({ code: "task_already_completed", message: "x" })).toMatch(
      /deja finalizat/i,
    );
  });
});

describe("canShowComplete status independence", () => {
  it("does not infer from status alone", () => {
    const task = {
      ...RUNTIME_FIXTURE_TASKS.inProgress,
      status: "in_progress" as EmployeeMobileTaskDTO["status"],
      can_complete: false,
    };
    expect(canShowComplete(task)).toBe(false);
  });
});
