import { describe, expect, it, vi } from "vitest";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  canShowAssignedStart,
  canShowAvailableStart,
  executeEmployeeMobileStart,
  mapEmployeeMobileStartError,
  resolveEmployeeMobileStartMode,
} from "@/lib/employeeMobileV2StartAction";
import { START_FIXTURE_TASKS } from "@/lib/employeeMobileV2StartFixtures";

vi.mock("@/api/employeeMobileTasks", () => ({
  startEmployeeMobileTask: vi.fn(async () => ({ status: "ok", action: "start" })),
  startEmployeeMobileTaskFromAvailable: vi.fn(async () => ({
    status: "ok",
    action: "start_from_available",
  })),
}));

import {
  startEmployeeMobileTask,
  startEmployeeMobileTaskFromAvailable,
} from "@/api/employeeMobileTasks";

describe("employeeMobileV2StartAction", () => {
  it("selects assigned mode from backend can_start", () => {
    expect(resolveEmployeeMobileStartMode(START_FIXTURE_TASKS.readyAssigned)).toBe("assigned");
    expect(canShowAssignedStart(START_FIXTURE_TASKS.readyAssigned)).toBe(true);
  });

  it("selects available mode from can_start_from_available", () => {
    expect(resolveEmployeeMobileStartMode(START_FIXTURE_TASKS.availableStartable)).toBe("available");
    expect(canShowAvailableStart(START_FIXTURE_TASKS.availableStartable)).toBe(true);
  });

  it("does not show start when backend says blocked", () => {
    expect(canShowAssignedStart(START_FIXTURE_TASKS.productionBlocked)).toBe(false);
    expect(canShowAssignedStart(START_FIXTURE_TASKS.readinessBlocked)).toBe(false);
    expect(resolveEmployeeMobileStartMode(START_FIXTURE_TASKS.productionBlocked)).toBe("none");
  });

  it("calls assigned endpoint for owned startable task", async () => {
    await executeEmployeeMobileStart(START_FIXTURE_TASKS.readyAssigned);
    expect(startEmployeeMobileTask).toHaveBeenCalledWith("fixture-start-ready", 23099);
    expect(startEmployeeMobileTaskFromAvailable).not.toHaveBeenCalled();
  });

  it("calls atomic start-from-available for available task", async () => {
    vi.mocked(startEmployeeMobileTask).mockClear();
    vi.mocked(startEmployeeMobileTaskFromAvailable).mockClear();
    await executeEmployeeMobileStart(START_FIXTURE_TASKS.availableStartable);
    expect(startEmployeeMobileTaskFromAvailable).toHaveBeenCalledWith("fixture-start-available", 23099);
    expect(startEmployeeMobileTask).not.toHaveBeenCalled();
  });

  it("maps production and readiness errors distinctly", () => {
    expect(
      mapEmployeeMobileStartError({ code: "production_release_blocked", message: "x" }),
    ).toContain("Producția este blocată");
    expect(mapEmployeeMobileStartError({ code: "task_not_ready", message: "x" })).toContain(
      "pregătit",
    );
    expect(
      mapEmployeeMobileStartError({ code: "task_already_assigned", message: "x" }),
    ).toContain("alt coleg");
  });

  it("does not send employee_id in client payload", async () => {
    const task = START_FIXTURE_TASKS.readyAssigned;
    await executeEmployeeMobileStart(task);
    const args = vi.mocked(startEmployeeMobileTask).mock.calls.at(-1);
    expect(args).toEqual([task.task_id, task.order_id]);
  });

  it("hides start for in-progress task", () => {
    const task = START_FIXTURE_TASKS.inProgress as EmployeeMobileTaskDTO;
    expect(canShowAssignedStart(task)).toBe(false);
    expect(resolveEmployeeMobileStartMode(task)).toBe("none");
  });
});
